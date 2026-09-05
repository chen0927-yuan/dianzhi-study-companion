# =============================================================
# 电智学伴 Phase 1 - FastAPI 后端 (修正版)
# 相对路线图原稿的修正：
#   1) API Key 不再硬编码 -> 读环境变量 / .env 文件
#   2) 模型名可配置（Moonshot 平台模型名可能更新，以平台为准）
#   3) 同端口托管前端静态页，浏览器访问 http://localhost:8000 即可
#   4) 启动时校验 API Key，缺失给出明确指引而非静默失败
# =============================================================
import os
from pathlib import Path

# --- 基础路径：backend/ 上一级为项目根，前端目录在其下 ---
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

# --- .env 加载（若安装了 python-dotenv）---
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

API_KEY = os.getenv("KIMI_API_KEY", "").strip()
BASE_URL = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
MODEL = os.getenv("KIMI_MODEL", "kimi-k2.6")  # 以 Moonshot 平台最新模型名为准（2026-09-03 实测为 kimi-k2.6）
# kimi-k2.x 系列强制 temperature=1（API 拒绝其他值），默认即 1
TEMPERATURE = float(os.getenv("KIMI_TEMPERATURE", "1.0"))
PORT = int(os.getenv("PORT", "8000"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import openai

# 允许前端跨域访问（本地调试 / 小程序 / 内网穿透均可）
app = FastAPI(title="电智学伴 API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- System Prompt：独立文件 system_prompt.py，便于替换为你优化后的完整版 ---
from system_prompt import SYSTEM_PROMPT

# --- Kimi (Moonshot) 客户端：懒初始化，Key 缺失时服务仍可启动 ---
_client = None

def get_client():
    global _client
    if _client is None:
        _client = openai.OpenAI(api_key=API_KEY, base_url=BASE_URL)
    return _client

MODE_PREFIX = {
    "刷题模式": "用户给出了一道具体题目，请直接输出完整解答过程。",
    "答疑模式": "用户对某个概念有疑问，请先给结论再分层解释。",
    "复试模式": "用户正在准备考研复试，请输出书面精解+面试口述版（3分钟内）。",
}


class ChatRequest(BaseModel):
    message: str
    mode: str = "刷题模式"  # 刷题模式/答疑模式/复试模式


class ChatRagRequest(ChatRequest):
    pass  # Phase 2 扩展：携带检索上下文


# ---- Phase 2: RAG（本地 bge-small-zh + Chroma 分页索引） ----
RAG_ENABLED = True

# 引用上下文 system 追加指令：强制 LLM 只引用检索片段、标注页码、不编造
def _make_rag_messages(req, contexts: str):
    prefix = MODE_PREFIX.get(req.mode, "")
    rag_rule = (
        "\n\n【知识库引用规则（必须严格遵守）】\n"
        "1. 优先基于教材片段作答。引用教材内容时，必须在相应句子后标注来源页码，格式：\n"
        "   （《教材名》第 X 页）\n"
        "2. 页码只能取自片段开头标注的页码（[片段N｜来源《书名》第 X 页]）。\n"
        "   禁止编造片段标注之外的页码；不确定时宁可不写页码。\n"
        "3. 同一知识点若多个片段都涉及，可并列标注多个页码，如（《电路》第 62、74 页）。\n"
        "4. 片段不足以回答时，可结合自己的知识补充，但必须明说\"教材未检索到该内容，以下为常识补充\"，\n"
        "   且补充部分不得伪造页码引用。\n"
        "5. 若没有任何教材片段，按普通模式回答即可。\n"
        "6. 回答中出现的每个页码都应当能在上面的片段标注中找到依据。"
    )
    system = SYSTEM_PROMPT + rag_rule
    user = f"[当前模式：{req.mode}]{prefix}\n\n用户问题：{req.message}\n\n---教材片段（片段头标注了精确页码）---\n{contexts}\n---片段结束---\n\n请回答，并按要求在引用处标注（《教材名》第 X 页）。"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _extract_cited_pages(text: str) -> list[int]:
    """从回答文本中提取所有『第 X 页 / 第X- Y页』引用页码（去重、保序）。"""
    import re

    pages: list[int] = []
    seen: set[int] = set()
    # 兼容：第 14 页 / 第14页 / 第 14~15 页 / 第 14、74 页
    for m in re.finditer(r"第\s*(\d+(?:\s*[~至到]\s*\d+)?)\s*页", text):
        seg = m.group(1).replace(" ", "")
        for num in re.split(r"[~至到]", seg):
            n = int(num)
            if n not in seen:
                seen.add(n)
                pages.append(n)
    return pages


def _check_reply_pages(reply: str, hits: list[dict]) -> dict:
    """页码幻觉核查：回答中提到的页码必须存在于本次检索返回的片段页码集合中。"""
    available = []
    for h in hits:
        for key in ("printed_page", "pdf_page"):
            p = h.get(key)
            if isinstance(p, int) and p not in available:
                available.append(p)
    available.sort()
    cited = _extract_cited_pages(reply)
    unmatched = [p for p in cited if p not in available]
    return {
        "cited_pages": cited,
        "available_pages": available,
        "unmatched_pages": unmatched,
    }


@app.post("/chat-rag")
async def chat_rag(req: ChatRagRequest):
    if not API_KEY:
        return {
            "reply": "后端未配置 KIMI_API_KEY。请先填入 backend/.env（参照 .env.example），重启服务。",
            "mode": req.mode,
            "tokens_used": 0,
            "citations": [],
        }
    from kb.retriever import get_retriever

    retriever = get_retriever()
    hits = retriever.retrieve(req.message)
    if not hits:
        return {
            "reply": "知识库为空：请先构建教材索引（python -m kb.build_kb --pdf <教材.pdf>），或扫描版 PDF 需先 OCR。",
            "mode": req.mode,
            "tokens_used": 0,
            "citations": [],
            "kb_empty": True,
        }
    contexts = retriever.format_context(hits)
    messages = _make_rag_messages(req, contexts)
    try:
        response = get_client().chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=TEMPERATURE,
            max_tokens=4000,
        )
        reply = response.choices[0].message.content
        return {
            "reply": reply,
            "mode": req.mode,
            "tokens_used": response.usage.total_tokens,
            "citations": retriever.format_citations(hits),
            "contexts_used": len(hits),
            "citation_check": _check_reply_pages(reply, hits),
        }
    except Exception as e:
        return {
            "reply": f"调用失败：{e}",
            "mode": req.mode,
            "tokens_used": 0,
            "citations": retriever.format_citations(hits),
            "contexts_used": len(hits),
            "citation_check": None,
        }


@app.get("/kb/status")
async def kb_status():
    from kb.retriever import get_retriever

    r = get_retriever()
    return {"enabled": RAG_ENABLED, "total_chunks": r.count(), "sources": r.sources()}


@app.post("/chat")
async def chat(req: ChatRequest):
    if not API_KEY:
        return {
            "reply": "后端未配置 KIMI_API_KEY。请到 https://platform.moonshot.cn 注册获取 Key，"
                     "然后填入 backend/.env（参照 .env.example），重启服务。",
            "mode": req.mode,
            "tokens_used": 0,
        }
    prefix = MODE_PREFIX.get(req.mode, "")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"[当前模式：{req.mode}]{prefix}\n\n用户问题：{req.message}"},
    ]
    try:
        response = get_client().chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=TEMPERATURE,
            max_tokens=4000,
        )
        return {
            "reply": response.choices[0].message.content,
            "mode": req.mode,
            "tokens_used": response.usage.total_tokens,
        }
    except Exception as e:
        return {"reply": f"调用失败：{e}", "mode": req.mode, "tokens_used": 0}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model": MODEL,
        "api_key_configured": bool(API_KEY),
        "version": "Phase-2-RAG",
    }


# --- 托管前端（放在最后注册，避免遮蔽 /chat /health 等 API）---
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    if not API_KEY:
        print("[警告] 未检测到 KIMI_API_KEY，/chat 将返回配置提示。")
        print("       获取方式: https://platform.moonshot.cn -> API Key 管理")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
