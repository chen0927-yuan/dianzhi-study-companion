# -*- coding: utf-8 -*-
"""电智学伴 Phase 2 - 构建教材向量知识库（分页索引，页码级精确）

用法（在 backend 目录下）：
    python -m kb.build_kb --pdf ..\..\textbooks\邱关源电路第五版.pdf
    python -m kb.build_kb --pdf <file> --offset 4     # 印刷页码 = PDF页序 + offset
    python -m kb.build_kb --dir ..\..\textbooks        # 批量构建目录下全部 PDF

页码精准的关键：
  1) 逐页提取文本（pypdf），每页独立切块，绝不跨页 → 每块页码无歧义
  2) chunk 元数据同时记录 pdf_page（PDF 物理页序，1 起）与 printed_page（印刷页码）
  3) printed_page = pdf_page + offset；offset 通过抽查 PDF 中"印刷页码 vs 页序"校准
"""
import argparse
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import chromadb
from pypdf import PdfReader

import kb.config as cfg
from kb.embeddings import BGEEmbeddingFunction


# ---------------- 文本切分 ----------------

_SENT_BOUND = re.compile(r"(?<=[。！？；])\s*")
_LINE_BOUND = re.compile(r"\s*\n\s*")


def split_page_text(text: str) -> list[str]:
    """页内切块：优先段落 → 句子 → 行，超长硬切。保证不跨页。"""
    text = re.sub(r"[ \t]+", " ", text).strip()
    if not text:
        return []

    # 1) 先按空行分段落
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    buffer = ""

    def flush():
        nonlocal buffer
        if buffer.strip():
            chunks.append(buffer.strip())
        buffer = ""

    for para in paragraphs:
        # 段落很长时再按句子拆
        sentences = [s.strip() for s in _SENT_BOUND.split(para) if s.strip()]
        for sent in sentences:
            if len(sent) <= cfg.CHUNK_SIZE:
                if len(buffer) + len(sent) + 1 > cfg.CHUNK_SIZE and buffer:
                    flush()
                buffer = (buffer + "\n" + sent).strip()
            else:
                flush()
                # 超长句（多为公式/表格粘连）：按换行拆
                lines = [l.strip() for l in _LINE_BOUND.split(sent) if l.strip()]
                piece = ""
                for ln in lines:
                    if len(piece) + len(ln) + 1 > cfg.CHUNK_SIZE and piece:
                        chunks.append(piece.strip())
                        piece = ""
                    piece = (piece + "\n" + ln).strip()
                if piece:
                    chunks.append(piece.strip())
    flush()
    return chunks


# ---------------- PDF 解析（逐页） ----------------

def extract_pages(pdf_path: Path) -> list[tuple[int, str]]:
    """返回 [(pdf_page_1based, text), ...]，过滤空页/异常页。"""
    reader = PdfReader(str(pdf_path))
    pages: list[tuple[int, str]] = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as e:  # 个别页解析失败不中断整体
            print(f"  [warn] page {i} extract failed: {e}")
            continue
        text = text.strip()
        if len(text) < cfg.MIN_PAGE_CHARS:
            continue  # 图片页/空白页
        if len(text) > cfg.MAX_PAGE_CHARS:
            print(f"  [warn] page {i} suspiciously large ({len(text)} chars), skipped")
            continue
        pages.append((i, text))
    return pages


# ---------------- 构建 ----------------

def build_pdf(pdf_path: Path, offset: int, force: bool = False) -> dict:
    print(f"== 构建: {pdf_path.name} (offset={offset}) ==")
    pages = extract_pages(pdf_path)
    if not pages:
        raise RuntimeError(f"未从 {pdf_path.name} 提取到文本——可能是扫描版图片 PDF，需先 OCR")

    client = chromadb.PersistentClient(path=str(cfg.CHROMA_DIR))
    col = client.get_or_create_collection(
        name=cfg.COLLECTION_NAME,
        embedding_function=BGEEmbeddingFunction(),
        metadata={"hnsw:space": "cosine"},
    )
    source = pdf_path.name
    title = pdf_path.stem

    # 同源重建：先删旧
    if force:
        existing = col.get(where={"source": source}, include=[])
        if existing["ids"]:
            col.delete(ids=existing["ids"])
            print(f"  已删除旧索引 {len(existing['ids'])} 块（force）")

    ids, docs, metas = [], [], []
    total_chunks = 0
    t0 = time.time()
    for pdf_page, text in pages:
        printed_page = pdf_page + offset
        for ci, chunk in enumerate(split_page_text(text)):
            if len(chunk) < 15:
                continue
            ids.append(f"{pdf_path.stem}-p{pdf_page}-c{ci}")
            docs.append(chunk)
            metas.append(
                {
                    "source": source,
                    "title": title,
                    "pdf_page": pdf_page,
                    "printed_page": printed_page,
                    "chunk": ci,
                }
            )
            total_chunks += 1

    if not ids:
        raise RuntimeError("切分后无有效文本块")

    # 分批写入，避免单次过大
    B = 200
    for i in range(0, len(ids), B):
        col.add(
            ids=ids[i : i + B],
            documents=docs[i : i + B],
            metadatas=metas[i : i + B],
        )
    elapsed = time.time() - t0
    print(f"  完成: {total_chunks} 块 / {len(pages)} 页, 耗时 {elapsed:.1f}s")
    return {"source": source, "pages": len(pages), "chunks": total_chunks}


def main():
    ap = argparse.ArgumentParser(description="构建教材向量知识库")
    ap.add_argument("--pdf", type=str, default=None, help="单个 PDF 路径")
    ap.add_argument("--dir", type=str, default=None, help="批量构建目录内全部 PDF")
    ap.add_argument("--offset", type=int, default=cfg.PAGE_OFFSET, help="印刷页码偏移")
    ap.add_argument("--force", action="store_true", help="同源重建（先删旧块）")
    args = ap.parse_args()

    if args.pdf:
        p = Path(args.pdf)
        if not p.exists():
            print(f"[error] 文件不存在: {p}")
            sys.exit(1)
        print(build_pdf(p, args.offset, args.force))
    elif args.dir:
        d = Path(args.dir)
        pdfs = sorted(d.glob("*.pdf"))
        if not pdfs:
            print(f"[error] {d} 下没有 PDF")
            sys.exit(1)
        for p in pdfs:
            try:
                build_pdf(p, args.offset, args.force)
            except Exception as e:
                print(f"  [error] {p.name}: {e}")
    else:
        ap.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
