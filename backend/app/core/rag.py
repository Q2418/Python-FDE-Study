import io
import re


def parse_document(filename: str, data: bytes) -> str:
    """解析知识库文档：支持 txt / md / docx"""
    lower = filename.lower()
    if lower.endswith(".docx"):
        from docx import Document

        document = Document(io.BytesIO(data))
        return "\n".join(p.text for p in document.paragraphs if p.text.strip())
    return data.decode("utf-8", errors="ignore")


def split_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list:
    """按固定长度切片，带重叠避免上下文断裂"""
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    chunks = []
    start = 0
    while start < len(normalized):
        end = start + chunk_size
        chunks.append(normalized[start:end])
        if end >= len(normalized):
            break
        start = end - overlap
    return chunks


def _bigrams(text: str) -> set:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff]", "", text.lower())
    if len(cleaned) < 2:
        return {cleaned} if cleaned else set()
    return {cleaned[i:i + 2] for i in range(len(cleaned) - 1)}


def score_chunk(query: str, chunk: str) -> float:
    """简易相似度：查询与切片的字符二元组重合率（无需外部向量库）"""
    query_grams = _bigrams(query)
    if not query_grams:
        return 0.0
    chunk_grams = _bigrams(chunk)
    if not chunk_grams:
        return 0.0
    return len(query_grams & chunk_grams) / len(query_grams)


def retrieve(db, query: str, top_k: int = 3, min_score: float = 0.05) -> list:
    from ..models.ai import AiChunk, AiDocument

    rows = (
        db.query(AiChunk, AiDocument.filename)
        .join(AiDocument, AiChunk.document_id == AiDocument.id)
        .all()
    )
    scored = [(score_chunk(query, chunk.content), chunk, filename) for chunk, filename in rows]
    scored.sort(key=lambda item: item[0], reverse=True)
    return [item for item in scored[:top_k] if item[0] >= min_score]
