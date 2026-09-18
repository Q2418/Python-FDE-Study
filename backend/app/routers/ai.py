import json
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import MAX_UPLOAD_SIZE, UPLOAD_DIR
from ..core.deps import get_current_user, require_admin
from ..core.llm import chat_completion, extract_answer, is_mock_mode
from ..core.logger import log_operation
from ..core.prompts import QA_ANSWER_TEMPERATURE, SYSTEM_PROMPT_QA, SYSTEM_PROMPT_TOOL, TOOL_ANSWER_TEMPERATURE
from ..core.rag import parse_document, retrieve, split_text
from ..core.response import success
from ..core.tools import TOOL_DEFINITIONS, execute_tool
from ..database import get_db
from ..models.ai import AiChunk, AiDocument
from ..models.user import User
from ..schemas.ai import AskRequest, ChatRequest, DocumentOut

logger = logging.getLogger("asset_admin")

router = APIRouter(prefix="/api/ai", tags=["AI 助手"], dependencies=[Depends(get_current_user)])

AI_DOC_DIR = UPLOAD_DIR / "ai_docs"
AI_DOC_EXTENSIONS = {".txt", ".md", ".docx"}

TOOL_LABELS = {"query_employees": "员工", "query_assets": "资产", "query_records": "领用记录"}


@router.post("/document", summary="上传知识库文档（txt/md/docx）")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    filename = file.filename or "未命名文档"
    extension = Path(filename).suffix.lower()
    if extension not in AI_DOC_EXTENSIONS:
        raise HTTPException(status_code=400, detail="知识库仅支持 txt / md / docx 格式")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="文件内容为空")
    if len(data) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过 5MB")
    text = parse_document(filename, data)
    chunks = split_text(text)
    if not chunks:
        raise HTTPException(status_code=400, detail="文档解析后没有有效内容")
    AI_DOC_DIR.mkdir(parents=True, exist_ok=True)
    stored_path = AI_DOC_DIR / f"{uuid.uuid4().hex}{extension}"
    stored_path.write_bytes(data)
    document = AiDocument(
        filename=filename,
        file_path=str(stored_path),
        file_size=len(data),
        chunk_count=len(chunks),
        uploader_id=admin.id,
    )
    db.add(document)
    db.flush()
    db.add_all([AiChunk(document_id=document.id, seq=index, content=content) for index, content in enumerate(chunks)])
    db.commit()
    db.refresh(document)
    log_operation(admin, "上传知识库文档", f"{filename}（{len(chunks)} 个切片）")
    return success(DocumentOut.model_validate(document), msg="文档上传成功")


@router.get("/document/list", summary="知识库文档列表")
def list_documents(db: Session = Depends(get_db)):
    documents = db.query(AiDocument).order_by(AiDocument.id.desc()).all()
    return success([DocumentOut.model_validate(item) for item in documents])


@router.delete("/document/{doc_id}", summary="删除知识库文档")
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    document = db.get(AiDocument, doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    db.query(AiChunk).filter(AiChunk.document_id == doc_id).delete()
    try:
        Path(document.file_path).unlink(missing_ok=True)
    except OSError:
        logger.warning("删除知识库文件失败: %s", document.file_path)
    filename = document.filename
    db.delete(document)
    db.commit()
    log_operation(admin, "删除知识库文档", filename)
    return success(msg="删除成功")


@router.post("/ask", summary="知识库问答（RAG）")
def ask(
    data: AskRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    hits = retrieve(db, data.question, top_k=data.top_k)
    sources = [
        {"document": filename, "score": round(score, 3), "snippet": chunk.content[:120]}
        for score, chunk, filename in hits
    ]
    if not hits:
        answer = "知识库中没有找到相关信息，请先上传业务文档，或换一种问法。"
    elif is_mock_mode():
        lines = ["【模拟模式】根据知识库检索到以下相关内容："]
        lines.extend(f"- {chunk.content[:150]}" for _, chunk, _ in hits)
        lines.append("（在 config.py 中配置 AI_API_KEY 后可切换为真实大模型总结回答）")
        answer = "\n".join(lines)
    else:
        context = "\n\n".join(f"【来源：{filename}】{chunk.content}" for _, chunk, filename in hits)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_QA},
            {"role": "user", "content": f"参考资料：\n{context}\n\n问题：{data.question}"},
        ]
        answer = extract_answer(chat_completion(messages, temperature=QA_ANSWER_TEMPERATURE))
    log_operation(user, "知识库问答", data.question)
    return success({"answer": answer, "sources": sources, "mode": "mock" if is_mock_mode() else "real"})


def _mock_tool_call(message: str):
    if any(keyword in message for keyword in ["记录", "领用记录", "归还记录"]):
        arguments = {}
        if "领用" in message:
            arguments["action"] = "领用"
        if "归还" in message:
            arguments["action"] = "归还"
        return "query_records", arguments
    if "资产" in message or "设备" in message:
        arguments = {}
        for status in ["空闲", "已领用", "维修", "报废"]:
            if status in message:
                arguments["status"] = status
                break
        for category in ["电脑设备", "网络设备", "办公用品"]:
            if category in message:
                arguments["category"] = category
                break
        return "query_assets", arguments
    arguments = {}
    for department in ["技术部", "人事部", "财务部", "市场部", "行政部"]:
        if department in message:
            arguments["department"] = department
            break
    if "在职" in message:
        arguments["status"] = "在职"
    if "离职" in message:
        arguments["status"] = "离职"
    return "query_employees", arguments


def _format_mock_answer(tool_name: str, result: dict) -> str:
    label = TOOL_LABELS.get(tool_name, "数据")
    if not result.get("count"):
        return f"【模拟模式】没有查询到符合条件的{label}数据。"
    lines = [f"【模拟模式】共查询到 {result['count']} 条{label}数据："]
    for item in result["items"][:5]:
        lines.append("、".join(f"{key}：{value}" for key, value in item.items() if value is not None))
    lines.append("（在 config.py 中配置 AI_API_KEY 后可切换为真实大模型智能回答）")
    return "\n".join(lines)


@router.post("/chat", summary="数据助手（大模型工具调用）")
def chat(
    data: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tool_info = None
    result = None
    if is_mock_mode():
        tool_name, arguments = _mock_tool_call(data.message)
        result = execute_tool(db, tool_name, arguments)
        answer = _format_mock_answer(tool_name, result)
        tool_info = {"name": tool_name, "arguments": arguments}
    else:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_TOOL},
            {"role": "user", "content": data.message},
        ]
        response = chat_completion(messages, tools=TOOL_DEFINITIONS, temperature=TOOL_ANSWER_TEMPERATURE)
        try:
            message = response["choices"][0]["message"]
        except (KeyError, IndexError, TypeError):
            logger.error("AI 返回格式异常: %s", str(response)[:300])
            raise HTTPException(status_code=502, detail="AI 返回格式异常，请稍后重试")
        tool_calls = message.get("tool_calls") or []
        if tool_calls:
            call = tool_calls[0]
            tool_name = call["function"]["name"]
            try:
                arguments = json.loads(call["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                arguments = {}
            result = execute_tool(db, tool_name, arguments)
            tool_info = {"name": tool_name, "arguments": arguments}
            messages.append({"role": "assistant", "content": message.get("content"), "tool_calls": tool_calls})
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.get("id", "call_1"),
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )
            answer = extract_answer(chat_completion(messages, temperature=TOOL_ANSWER_TEMPERATURE))
        else:
            answer = message.get("content") or ""
    log_operation(user, "AI 数据助手", data.message)
    return success({"answer": answer, "tool": tool_info, "data": result, "mode": "mock" if is_mock_mode() else "real"})
