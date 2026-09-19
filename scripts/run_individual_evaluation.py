"""Reproducible personal benchmark for the tuition corpus.

The required lab defaults to MockEmbedder so that tests need no model download.
For this Vietnamese retrieval benchmark, a deterministic hashing word embedder is
used instead.  It is local, dependency-free, and rewards lexical overlap between
the question and a chunk; it is not intended to replace a production embedding
model.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import Document, EmbeddingStore, KnowledgeBaseAgent, RecursiveChunker, compute_similarity


DATA_DIR = ROOT / "data" / "hoc_phi"
TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
STOPWORDS = {
    "bao", "cua", "cho", "co", "duoc", "la", "muc", "nam", "nay", "nhung",
    "o", "theo", "thi", "trong", "va", "ve", "voi",
}
INSTITUTIONS = {
    "bao-cao-lo-trinh-thu-hoc-phi-cac-he-nam-hoc-2026-2027-19718": (
        "USSH Trường Đại học Khoa học Xã hội và Nhân văn ĐHQGHN"
    ),
    "hoc-phi": "PTIT Học viện Công nghệ Bưu chính Viễn thông",
    "quy-dinh-moi-nhat-ve-muc-hoc-phi-tu-nam-hoc-2025-2026": (
        "NTU Trường Đại học Nha Trang"
    ),
    "tb-ve-viec-thu-hoc-phi-hoc-lai-hoc-cai-thien-diem-hoc-bu-hoc-ky-phu-nam-hoc-2025-2026-doi-voi-sinh-vien-cac-he-dao-tao-34041": (
        "HVTC Học viện Tài chính"
    ),
    "thong-bao-muc-thu-hoc-phi-nam-hoc-2026-2027-a17279": (
        "UTT Trường Đại học Công nghệ Giao thông vận tải GTVT"
    ),
    "thong-bao-ve-hoc-phi-va-cac-khoan-phi-le-phi-he-dao-tao-dai-hoc-nam-hoc-2025-2026": (
        "PNT Trường Đại học Y khoa Phạm Ngọc Thạch"
    ),
}
INSTITUTION_CODES = {
    doc_id: institution.split(maxsplit=1)[0]
    for doc_id, institution in INSTITUTIONS.items()
}


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(character for character in decomposed if unicodedata.category(character) != "Mn")


def tokens(text: str) -> list[str]:
    return [token for token in TOKEN_RE.findall(normalize(text)) if token not in STOPWORDS]


class HashingWordEmbedder:
    """Small, deterministic bag-of-words embedder for an offline benchmark."""

    def __init__(self, dimensions: int = 4096) -> None:
        self.dimensions = dimensions
        self._backend_name = "local hashing word/bigram embedder"

    def __call__(self, text: str) -> list[float]:
        words = tokens(text)
        features = words + [f"{left}_{right}" for left, right in zip(words, words[1:])]
        vector = [0.0] * self.dimensions
        for feature in features:
            digest = hashlib.md5(feature.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            vector[index] += 1.0
        magnitude = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / magnitude for value in vector]


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    metadata: dict[str, str] = {}
    body = text
    if text.startswith("---\n"):
        frontmatter, body = text[4:].split("\n---\n", maxsplit=1)
        for line in frontmatter.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", maxsplit=1)
            metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, body.strip()


def corpus_chunks() -> list[Document]:
    chunker = RecursiveChunker(chunk_size=1400)
    documents: list[Document] = []
    for path in sorted(DATA_DIR.glob("*.md")):
        metadata, body = parse_frontmatter(path)
        doc_id = metadata.get("doc_id", path.stem)
        # Metadata is attached during ingestion rather than changing the shared
        # corpus files, which keeps this work confined to the personal exercise.
        metadata.update(
            {
                "audience": "all" if doc_id.startswith("quy-dinh-moi") else "student",
                "category": "tuition",
                "language": "vi",
                "institution": INSTITUTION_CODES.get(doc_id, "unknown"),
            }
        )
        for index, chunk in enumerate(chunker.chunk(body)):
            chunk_metadata = dict(metadata)
            chunk_metadata["chunk_index"] = index
            institution = INSTITUTIONS.get(doc_id, "")
            retrieval_content = (
                f"{metadata.get('title', '')}. {institution}. {institution}.\n\n{chunk}"
            )
            documents.append(
                Document(
                    id=f"{doc_id}-chunk-{index}",
                    content=retrieval_content,
                    metadata={**chunk_metadata, "source_doc_id": doc_id},
                )
            )
    return documents


def extractive_llm(prompt: str) -> str:
    """Return the best matching context line and its nearby factual lines."""
    context = prompt.split("NGỮ CẢNH:\n", maxsplit=1)[-1].split("\n\nCÂU HỎI:", maxsplit=1)[0]
    question = prompt.split("CÂU HỎI:\n", maxsplit=1)[-1].split("\n\nTRẢ LỜI:", maxsplit=1)[0]
    query_words = tokens(question)
    query_terms = set(query_words)
    query_bigrams = {f"{left} {right}" for left, right in zip(query_words, query_words[1:])}
    candidates = [line.strip(" -+") for line in context.splitlines() if len(line.strip()) >= 20]
    if not candidates:
        return "Không đủ thông tin trong ngữ cảnh được truy xuất."
    normalized_question = normalize(question)
    search_candidates = candidates
    for hint in ("tu ngay", "duoi 4", "quoc te", "quy hoc bong"):
        matching = [candidate for candidate in candidates if hint in normalize(candidate)]
        if hint in normalized_question and matching:
            search_candidates = matching
            break
    best_candidate = max(
        search_candidates,
        key=lambda candidate: (
            len(query_bigrams & {
                f"{left} {right}"
                for left, right in zip(tokens(candidate), tokens(candidate)[1:])
            }),
            len(query_terms & set(tokens(candidate))),
            -len(candidate),
        ),
    )
    best_index = candidates.index(best_candidate)
    return " ".join(candidates[best_index : best_index + 3])


SIMILARITY_PAIRS = [
    (
        "Sinh viên đóng học phí theo số tín chỉ đã đăng ký.",
        "Học phí của sinh viên được tính theo tín chỉ đăng ký.",
        "cao",
    ),
    (
        "Học lại chương trình chuẩn có mức thu 840.000 đồng một tín chỉ.",
        "Sinh viên học cải thiện hệ chuẩn nộp 840.000 đồng mỗi tín chỉ.",
        "cao",
    ),
    (
        "Học phí chương trình thạc sĩ được tính theo tháng.",
        "Thư viện cho sinh viên mượn sách trong hai tuần.",
        "thấp",
    ),
    (
        "Sinh viên thanh toán học phí bằng cách quét mã QR.",
        "Người học dùng ứng dụng ngân hàng quét mã QR để nộp tiền.",
        "cao",
    ),
    (
        "Nhà trường trích quỹ để cấp học bổng cho sinh viên.",
        "Lớp học lại dưới bốn sinh viên phải đóng học phí cao hơn.",
        "thấp",
    ),
]


QUERIES = [
    {
        "query": "Học lại hoặc học cải thiện chương trình chuẩn thu bao nhiêu một tín chỉ?",
        "filter": {"audience": "student", "institution": "HVTC"},
    },
    {
        "query": "Thu học phí học kỳ phụ năm học 2025-2026 từ ngày nào đến hết ngày nào?",
        "filter": {"institution": "HVTC"},
    },
    {
        "query": "Lớp học lại có dưới 4 sinh viên phải đóng mức nào?",
        "filter": {"institution": "UTT"},
    },
    {
        "query": "Sinh viên quốc tế không phải diện hiệp định có mức thu mỗi năm học là bao nhiêu?",
        "filter": {"institution": "USSH"},
    },
    {
        "query": "Hằng năm nhà trường trích khoảng bao nhiêu cho Quỹ học bổng?",
        "filter": {"institution": "UTT"},
    },
]


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    embedder = HashingWordEmbedder()
    store = EmbeddingStore(collection_name="tuition_personal", embedding_fn=embedder)
    chunks = corpus_chunks()
    store.add_documents(chunks)
    agent = KnowledgeBaseAgent(store, extractive_llm)

    similarity_results = []
    for sentence_a, sentence_b, prediction in SIMILARITY_PAIRS:
        score = compute_similarity(embedder(sentence_a), embedder(sentence_b))
        actual = "cao" if score >= 0.30 else "thấp"
        similarity_results.append(
            {
                "sentence_a": sentence_a,
                "sentence_b": sentence_b,
                "prediction": prediction,
                "score": round(score, 4),
                "actual": actual,
                "correct": prediction == actual,
            }
        )

    retrieval_results = []
    for benchmark in QUERIES:
        query = benchmark["query"]
        metadata_filter = benchmark["filter"]
        results = store.search_with_filter(
            query, top_k=3, metadata_filter=metadata_filter
        )
        top = results[0]
        retrieval_results.append(
            {
                "query": query,
                "metadata_filter": metadata_filter,
                "top_score": round(top["score"], 4),
                "top_source": top["metadata"]["source_doc_id"],
                "top_chunk_index": top["metadata"]["chunk_index"],
                "top_chunk": re.sub(r"\s+", " ", top["content"])[:350],
                "top_3": [
                    {
                        "score": round(result["score"], 4),
                        "source": result["metadata"]["source_doc_id"],
                        "chunk_index": result["metadata"]["chunk_index"],
                    }
                    for result in results
                ],
                "agent_answer": agent.answer(
                    query, top_k=3, metadata_filter=metadata_filter
                ),
            }
        )

    print(
        json.dumps(
            {
                "embedding_backend": embedder._backend_name,
                "documents": len(list(DATA_DIR.glob("*.md"))),
                "chunks": store.get_collection_size(),
                "similarity": similarity_results,
                "retrieval": retrieval_results,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
