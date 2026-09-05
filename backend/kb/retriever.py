# -*- coding: utf-8 -*-
"""电智学伴 Phase 2 - 检索器：向量检索 + 页码级引用"""
from pathlib import Path
from typing import Optional

import chromadb

import kb.config as cfg
from kb.embeddings import BGEEmbeddingFunction, encode_query


class Retriever:
    """对 Chroma 中教材知识库的检索封装。"""

    def __init__(self) -> None:
        self._client = chromadb.PersistentClient(path=str(cfg.CHROMA_DIR))
        self._col = self._client.get_or_create_collection(
            name=cfg.COLLECTION_NAME,
            embedding_function=BGEEmbeddingFunction(),
            metadata={"hnsw:space": "cosine"},  # 与 build_kb 一致：余弦距离，score=1-dist 才正确
        )

    # ---- 状态 ----
    @property
    def collection(self):
        return self._col

    def count(self) -> int:
        return self._col.count()

    def sources(self) -> list[str]:
        if self.count() == 0:
            return []
        res = self._col.get(include=["metadatas"], limit=100000)
        srcs = {}
        for m in res.get("metadatas", []):
            if m:
                srcs.setdefault(m["title"], {"chunks": 0, "pages": set()})
                srcs[m["title"]]["chunks"] += 1
                srcs[m["title"]]["pages"].add(m["pdf_page"])
        out = []
        for t, info in srcs.items():
            out.append({"title": t, "chunks": info["chunks"], "pages": len(info["pages"])})
        return out

    # ---- 检索 ----
    def retrieve(self, query: str, top_k: Optional[int] = None) -> list[dict]:
        """返回按相关度排序的片段，含来源与页码信息。"""
        if self.count() == 0:
            return []
        k = top_k or cfg.TOP_K
        res = self._col.query(
            query_embeddings=encode_query(query),
            n_results=min(k, self.count()),
            include=["documents", "metadatas", "distances"],
        )
        hits = []
        for doc, meta, dist in zip(
            res["documents"][0], res["metadatas"][0], res["distances"][0]
        ):
            m = meta or {}
            hits.append(
                {
                    "text": doc,
                    "title": m.get("title", ""),
                    "source": m.get("source", ""),
                    "pdf_page": m.get("pdf_page"),
                    "printed_page": m.get("printed_page"),
                    "score": round(1 - float(dist), 4),  # cosine 距离 → 相似度
                }
            )
        return hits

    # ---- 组装供 LLM 使用的引用上下文 ----
    def format_context(self, hits: list[dict]) -> str:
        """把检索结果转成带页码标注的 prompt 上下文。

        片段头固定格式：
            [片段N｜来源《标题》第 X 页｜PDF页 P｜相关度 S]
        其中 X 优先取印刷页码（printed_page），无则取 PDF 物理页序。
        LLM 被要求只能引用此处标注的页码（见 main.py 的引用规则）。
        """
        lines = []
        for i, h in enumerate(hits, 1):
            printed = h.get("printed_page")
            pdf = h.get("pdf_page")
            page = printed if printed is not None else pdf
            loc = f"第 {page} 页" if page is not None else "页码未知"
            pdf_note = f"｜PDF页 {pdf}" if (pdf is not None and printed is not None) else ""
            lines.append(
                f"[片段{i}｜来源《{h['title']}》{loc}{pdf_note}｜相关度 {h['score']}]\n{h['text']}"
            )
        return "\n\n".join(lines)

    def format_citations(self, hits: list[dict]) -> list[dict]:
        """返回给前端的引用列表（用于展示来源）。"""
        out = []
        for h in hits:
            page = h["printed_page"] if h["printed_page"] is not None else h["pdf_page"]
            out.append(
                {
                    "source": h["title"],
                    "page": page,
                    "pdf_page": h.get("pdf_page"),
                    "score": h["score"],
                    "snippet": (h["text"] or "")[:160],
                }
            )
        return out


# 进程内单例（懒加载，避免重复开库）
_retriever: Optional[Retriever] = None


def get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever
