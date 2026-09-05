# -*- coding: utf-8 -*-
"""电智学伴 Phase 2 - 知识库配置"""
import os
from pathlib import Path

# Chroma 遥测 / 联网检查一律关闭（本地离线运行，避免无谓超时）
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
os.environ.setdefault("CHROMA_TELEMETRY", "False")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

# backend/ 目录（kb 包的上级）
BACKEND_DIR = Path(__file__).resolve().parent.parent

# 教材 PDF 目录：把教材 PDF 放进这里
PDF_DIR = BACKEND_DIR.parent / "textbooks"

# Chroma 持久化目录（自动创建）
CHROMA_DIR = BACKEND_DIR / "chroma_db"
COLLECTION_NAME = "textbooks"

# ---- 本地 Embedding：bge-small-zh-v1.5 ----
# 首次运行会自动从 HuggingFace 下载模型（约 100MB）。
# 国内网络慢时设置环境变量：HF_ENDPOINT=https://hf-mirror.com
EMBED_MODEL = "BAAI/bge-small-zh-v1.5"
EMBED_DEVICE = "cpu"
# bge 系列检索规范：查询侧加指令前缀，文档侧不加
QUERY_INSTRUCTION = "为这个句子生成表示以用于检索相关文章："

# ---- 分块参数（按页切块，保证页码元数据精确） ----
CHUNK_SIZE = 450        # 每块目标字符数（中文）
CHUNK_OVERLAP = 80      # 块间重叠字符数
MIN_PAGE_CHARS = 20     # 少于该字符数的页视为图片/空页，跳过
MAX_PAGE_CHARS = 12000  # 单页超过该字符数视为解析异常，跳过

# ---- 检索 ----
TOP_K = 5               # 默认返回片段数

# 页码偏移：教材印刷页码与 PDF 物理页序的差值。
# 例如 PDF 第 1 页印着"第 5 页"，则 PAGE_OFFSET = 4。
# 构建时可用 --offset 覆盖。见 README「页码校准」一节。
PAGE_OFFSET = 0
