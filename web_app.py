"""Minimal local web interface for the tuition RAG system.

Run:
    .\.venv\Scripts\python.exe web_app.py
Then open http://127.0.0.1:8000.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from scripts.run_individual_evaluation import (
    HashingWordEmbedder,
    corpus_chunks,
    extractive_llm,
)
from src import EmbeddingStore, KnowledgeBaseAgent


ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"
STATIC_FILES = {
    "/": WEB_DIR / "index.html",
    "/index.html": WEB_DIR / "index.html",
    "/styles.css": WEB_DIR / "styles.css",
    "/app.js": WEB_DIR / "app.js",
}


class TuitionRAG:
    def __init__(self) -> None:
        self.embedder = HashingWordEmbedder()
        self.documents = corpus_chunks()
        self.store = EmbeddingStore(
            collection_name="tuition_web_interface",
            embedding_fn=self.embedder,
        )
        self.store.add_documents(self.documents)
        self.agent = KnowledgeBaseAgent(self.store, extractive_llm)

    def ask(
        self,
        question: str,
        institution: str | None = None,
        top_k: int = 3,
    ) -> dict:
        metadata_filter = {"institution": institution} if institution else None
        results = self.store.search_with_filter(
            question,
            top_k=top_k,
            metadata_filter=metadata_filter,
        )
        answer = self.agent.answer(
            question,
            top_k=top_k,
            metadata_filter=metadata_filter,
        )
        sources = []
        for result in results:
            metadata = result["metadata"]
            excerpt = re.sub(r"\s+", " ", result["content"]).strip()
            sources.append(
                {
                    "title": metadata.get("title", "Tài liệu học phí"),
                    "url": metadata.get("source_url", ""),
                    "institution": metadata.get("institution", ""),
                    "document_id": metadata.get("source_doc_id", metadata.get("doc_id", "")),
                    "chunk_index": metadata.get("chunk_index"),
                    "score": round(float(result["score"]), 4),
                    "excerpt": excerpt[:420] + ("…" if len(excerpt) > 420 else ""),
                }
            )
        return {
            "question": question,
            "answer": answer,
            "filter": institution or "ALL",
            "sources": sources,
            "stats": {
                "documents": 6,
                "chunks": self.store.get_collection_size(),
                "backend": self.embedder._backend_name,
            },
        }


APP = TuitionRAG()


class RequestHandler(BaseHTTPRequestHandler):
    server_version = "TuitionRAG/1.0"

    def log_message(self, format: str, *args: object) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/health":
            self._send_json(
                {
                    "status": "ok",
                    "documents": 6,
                    "chunks": APP.store.get_collection_size(),
                }
            )
            return

        file_path = STATIC_FILES.get(path)
        if file_path is None or not file_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "Không tìm thấy tài nguyên")
            return

        body = file_path.read_bytes()
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/api/ask":
            self.send_error(HTTPStatus.NOT_FOUND, "Không tìm thấy API")
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0 or content_length > 20_000:
                raise ValueError("Dữ liệu gửi lên không hợp lệ.")
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            question = str(payload.get("question", "")).strip()
            institution = str(payload.get("institution", "")).strip().upper() or None
            top_k = int(payload.get("top_k", 3))

            if len(question) < 3:
                raise ValueError("Câu hỏi cần có ít nhất 3 ký tự.")
            if len(question) > 500:
                raise ValueError("Câu hỏi không được dài quá 500 ký tự.")
            if institution not in {None, "HVTC", "UTT", "USSH", "PTIT", "NTU", "PNT"}:
                raise ValueError("Bộ lọc trường không hợp lệ.")
            if top_k not in {1, 3, 5}:
                raise ValueError("Số kết quả chỉ có thể là 1, 3 hoặc 5.")

            self._send_json(APP.ask(question, institution=institution, top_k=top_k))
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception:
            self._send_json(
                {"error": "Không thể xử lý câu hỏi lúc này. Vui lòng thử lại."},
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Giao diện hỏi đáp học phí cục bộ")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), RequestHandler)
    print(f"Tuition RAG UI: http://{args.host}:{args.port}")
    print("Nhấn Ctrl+C để dừng máy chủ.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
