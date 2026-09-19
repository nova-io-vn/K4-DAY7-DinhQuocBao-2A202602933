from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(
        self,
        question: str,
        top_k: int = 3,
        metadata_filter: dict | None = None,
    ) -> str:
        results = (
            self.store.search_with_filter(
                question, top_k=top_k, metadata_filter=metadata_filter
            )
            if metadata_filter
            else self.store.search(question, top_k=top_k)
        )
        if results:
            context = "\n\n".join(
                f"[Nguồn {index} | doc_id={result['metadata'].get('doc_id', 'unknown')}]\n"
                f"{result['content']}"
                for index, result in enumerate(results, start=1)
            )
        else:
            context = "Không tìm thấy ngữ cảnh phù hợp trong cơ sở tri thức."

        prompt = (
            "Bạn là trợ lý hỏi đáp dựa trên cơ sở tri thức. "
            "Chỉ trả lời bằng thông tin có trong ngữ cảnh; nếu ngữ cảnh không đủ, "
            "hãy nói rõ rằng không đủ thông tin.\n\n"
            f"NGỮ CẢNH:\n{context}\n\n"
            f"CÂU HỎI:\n{question}\n\n"
            "TRẢ LỜI:"
        )
        return self.llm_fn(prompt)
