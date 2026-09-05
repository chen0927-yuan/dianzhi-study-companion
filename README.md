# 电智学伴 · Phase 2（本地 bge-small-zh RAG · 精准页码引用）

> 电智学伴 = 电气工程考研复试 AI 学习伴侣。
> **Phase 2 已闭环**：本地 `bge-small-zh-v1.5` 向量检索 + Chroma 分页索引 + Kimi 生成，
> 回答按（《教材名》第 X 页）格式标注精确页码，前端展示引用卡片并做**页码幻觉核查**。

## 目录结构

```
电智学伴-Phase1/
├── 启动服务.bat          # 一键启动（自动选 py -3.12，装依赖 + 开浏览器 + 起服务）
├── textbooks/            # ← 把教材 PDF 放这里（邱关源《电路》第五版文字版等）
├── frontend/
│   └── index.html        # 网页聊天界面（Phase2：RAG 开关 + 引用页码卡片）
└── backend/
    ├── main.py           # FastAPI 后端（/chat 普通模式、/chat-rag 检索模式、/kb/status）
    ├── system_prompt.py  # System Prompt（可整体替换为你优化版）
    ├── requirements.txt  # Phase1 + Phase2 依赖
    ├── .env.example      # 环境变量模板（复制为 .env 填 Key）
    └── kb/               # Phase 2 知识库
        ├── config.py     # 路径 / 分块参数 / 检索参数 / 页码偏移
        ├── embeddings.py # 本地 bge-small-zh（chromadb EmbeddingFunction + 查询指令前缀）
        ├── build_kb.py   # 逐页解析 PDF → 页内切块 → Chroma 索引（页码元数据精确）
        ├── retriever.py  # 向量检索 + 引用上下文组装 + 引用列表
        └── make_test_pdf.py  # 生成 6 页测试教材（验证用，非交付物）
```

## 运行步骤

1. **Python 3.10~3.12**（本机实测 3.12；默认 `python` 若是 3.13+/3.14 请用 `py -3.12`）
2. 依赖已在 Python 3.12 装好；换机时执行：
   `py -3.12 -m pip install -r backend\requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`
3. 确认 `backend/.env` 存在且含 `KIMI_API_KEY`（Moonshot Kimi，见 .env.example）
4. **构建教材索引**（textbooks/ 下放入教材 PDF 后执行）：
   ```
   cd backend
   py -3.12 -m kb.build_kb --dir ..\textbooks --offset 0
   ```
5. 启动：双击 `启动服务.bat`，或 `cd backend && py -3.12 main.py`
6. 浏览器打开 `http://localhost:8000` → 勾选「📚 基于教材检索回答」→ 提问

自检：`http://localhost:8000/health` 返回 `{"status":"ok","version":"Phase-2-RAG",...}`；
`http://localhost:8000/kb/status` 返回片段总数与来源。

## 精准页码引用的实现要点

1. **逐页切块、绝不跨页**（`build_kb.py`）：每页文本独立切块，每块元数据同时记录
   `pdf_page`（PDF 物理页序）与 `printed_page`（印刷页码）→ 页码零歧义。
2. **印刷页码校准**：`printed_page = pdf_page + offset`。
   PDF 第 1 页印着"第 N 页"则 `offset = N-1`。构建后可用测试教材验证：
   ```
   py -3.12 -m kb.make_test_pdf ..\..\textbooks\test_textbook.pdf   # 页脚印刷页 10~15，物理页 1~6
   py -3.12 -m kb.build_kb --pdf ..\..\textbooks\test_textbook.pdf --offset 9 --force
   ```
   问"戴维南定理"应引用到印刷第 14 页（物理第 5 页）。
3. **本地 bge-small-zh 编码规范**（`embeddings.py`）：文档侧不加指令，查询侧加
   `为这个句子生成表示以用于检索相关文章：` 前缀（bge 官方要求，相关性更准）；
   向量余弦归一化；模型只下载一次（约 100MB，国内可设 `HF_ENDPOINT=https://hf-mirror.com`）。
4. **引用约束进 Prompt**（`main.py`）：强制 LLM 只引用片段头标注的页码、
   禁止编造页码、片段不足时明说"教材未检索到该内容"。
5. **页码幻觉核查**（`main.py _check_reply_pages`）：回答返回后自动提取其中所有"第 X 页"，
   与本次检索命中的页码集合比对，不一致的页码在 `citation_check.unmatched_pages` 中标出并提示前端。
6. **前端引用卡片**：/chat-rag 返回的 `citations`（来源/页码/相关度/片段摘要）直接展示在回答下方。

## API

| 接口 | 说明 |
|---|---|
| `POST /chat` | 普通问答（不带知识库） |
| `POST /chat-rag` | 检索模式：本地 bge 检索 → 带页码上下文生成；返回 `reply/citations/citation_check/contexts_used` |
| `GET /kb/status` | 知识库状态：片段数、来源清单 |
| `GET /health` | 健康检查 |

## 常见问题

- **首次提问慢（10~30s）**：CPU 加载 bge 模型并编码，属正常；之后查询为秒级。
- **报"模型不存在"**：Moonshot 平台模型名会更新，改 `.env` 的 `KIMI_MODEL`。
- **扫描版 PDF 无法建索引**：需先 OCR（如 PaddleOCR）转文字版 PDF。
- **页码总差几页**：用 `--offset` 校准重建（公式见上）。
- **环境变量优先级**：代码先读 `.env`，也兼容系统环境变量同名覆盖。
