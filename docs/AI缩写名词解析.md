# AI 英文缩写名词解析（新手友好版）

> 分类原则：按"你在哪会遇到"排，不是按字母排。每类先说最常见，再说进阶。
> 使用建议：先通读一遍有印象，以后遇到不认识回来查。

---

## 一、你天天在用的"基础设施"缩写

| 缩写 | 全称 | 中文 | 一句话解释 | 你会哪遇到 |
|---|---|---|---|---|
| API | Application Programming Interface | 应用程序接口 | 程序之间对话的"窗口/服务员"——你点菜（请求），它上菜（返回） | 电智学伴调 Kimi、OpenClaw 的一切 |
| URL | Uniform Resource Locator | 统一资源定位符 | 网址，网上每个东西的"门牌号" | http://localhost:8000 |
| HTTP | HyperText Transfer Protocol | 超文本传输协议 | 浏览器和服务器之间传文字的"规矩" | 接口路径 /chat、/kb/status |
| JSON | JavaScript Object Notation | JS对象表示法 | 人和程序都能读的数据文本格式，前后端传数据全靠它 | API 返回的 {reply:...} |
| DOM | Document Object Model | 文档对象模型 | 网页在程序眼里的"树"，节点=标签 | getElementById |
| CSS | Cascading Style Sheets | 层叠样式表 | 网页的美容师（颜色/布局） | index.html 的 <style> |
| HTML | HyperText Markup Language | 超文本标记语言 | 网页的骨架结构 | index.html 的标签 |
| IDE | Integrated Development Environment | 集成开发环境 | 写代码的"办公室"（编辑器全家桶） | VS Code 之类 |
| CLI | Command-Line Interface | 命令行界面 | 用打字操作电脑（相对图形界面 GUI） | git 命令、python 命令 |
| GUI | Graphical User Interface | 图形用户界面 | 用鼠标点的界面 | GitHub Desktop |

## 二、AI 核心缩写（最重要的一类）

| 缩写 | 全称 | 中文 | 一句话解释 |
|---|---|---|---|
| AI | Artificial Intelligence | 人工智能 | 机器模拟人的智能（总称） |
| ML | Machine Learning | 机器学习 | AI 的一个分支：让程序从数据里自己学规律，而不是人写死规则 |
| DL | Deep Learning | 深度学习 | ML 的分支：用"神经网络"学，当前 AI 的主力 |
| LLM | Large Language Model | 大语言模型 | 用海量文字训练出来的"超强接话机器"——Kimi、DeepSeek 都是 LLM |
| GPT | Generative Pre-trained Transformer | 生成式预训练变换器 | OpenAI 的 LLM 系列名，现在常被当作"AI 聊天模型"代称 |
| AGI | Artificial General Intelligence | 通用人工智能 | 和人类一样全能搞定的 AI（还没实现，是终极目标） |
| NLP | Natural Language Processing | 自然语言处理 | 让电脑理解/生成人类语言的技术（LLM 属于 NLP） |
| CV | Computer Vision | 计算机视觉 | 让电脑"看懂"图片视频（人脸识别等） |
| ASR / TTS | Speech Recognition / Text-to-Speech | 语音识别/语音合成 | 听懂说话 / 把文字读出来（语音助手） |
| RAG | Retrieval-Augmented Generation | 检索增强生成 | **先查资料再回答**——电智学伴的核心！解决 LLM 瞎编和知识过时 |
| Token | （无中文直译） | 词元 | LLM 计数的"字块"单位，1 个汉字约 1-2 token；API 按它收费 |
| Prompt | （沿用英文） | 提示词 | 你给 AI 的指令/问题——你的 system_prompt.py 就是"人设+规则" |
| Embedding | （沿用英文） | 向量化/嵌入 | 把文字变成一串数字（向量），让电脑能算"哪两句话意思近"——bge 模型干这个 |
| Vector DB | Vector Database | 向量数据库 | 存向量并快速找相似的库——Chroma 就是 |
| Fine-tune | Fine-tuning | 微调 | 拿现成模型+自己的数据再练一练，让它变"专科" |
| Inference | （沿用） | 推理 | 模型"回答问题"这个动作（相对训练） |
| Hallucination | — | 幻觉 | AI 一本正经地胡说八道（编造内容）——电智学伴的页码核查就是防它 |
| Context Window | — | 上下文窗口 | AI 一次能"记住"多少内容（Kimi 很大，DeepSeek 号称 1M） |
| Benchmark | — | 基准测试 | 给模型打分排名的标准考题集 |

## 三、电智学伴 / OpenClaw 里你用到的具体技术缩写

| 缩写 | 全称 | 它是什么 | 在你项目里的角色 |
|---|---|---|---|
| FastAPI | Fast + API | Python 写后端接口的框架 | main.py 的骨架，提供 /chat 等接口 |
| uvicorn | — | 运行 FastAPI 的"服务器发动机" | python main.py 启动的就是它 |
| Chroma | ChromaDB | 开源向量数据库 | 存教材片段向量，检索用 |
| bge | BAAI General Embedding | 智源研究院的中文向量模型 | 把你的问题变成向量（本地运行） |
| OpenAI SDK | Software Development Kit | 官方给的"调 API 的工具包" | 用它连 Moonshot 的 Kimi |
| CORS | Cross-Origin Resource Sharing | 跨域资源共享 | 允许前端页面调后端接口的开关 |
| OCR | Optical Character Recognition | 光学字符识别 | 把扫描图片里的字变成可编辑文字（扫描版 PDF 需要它） |
| PDF | Portable Document Format | 便携文档格式 | 教材文件格式（文字版可直接解析，扫描版需 OCR） |
| SQLite | — | 轻量数据库文件 | Chroma 底层存数据用 |
| .env | environment | 环境变量文件 | 存 API Key 等配置（**已 gitignore，不入库**） |

## 四、模型/平台名（你知道它们是啥就行）

| 名字 | 是什么 | 谁家的 |
|---|---|---|
| Kimi / Moonshot | LLM（长文本强） | 月之暗面（国内）——电智学伴用的 |
| DeepSeek | LLM（便宜强大） | 深度求索（国内）——OpenClaw 主力模型 |
| OpenAI / ChatGPT | LLM 开山鼻祖 | 美国 |
| Claude | LLM（长文/写作强） | Anthropic，美国 |
| Gemini | LLM | Google |
| Hugging Face | AI 模型"应用商店" | 下载 bge 等开源模型的地方 |
| Ollama | 本地跑开源模型的工具 | 把 Llama 等跑在自己电脑上 |
| Llama | 开源 LLM 系列 | Meta |

## 五、硬件缩写（聊 AI 常提到）

| 缩写 | 全称 | 一句话 |
|---|---|---|
| CPU | Central Processing Unit | 电脑大脑，通用计算（你跑 bge 用的） |
| GPU | Graphics Processing Unit | 显卡芯片，并行算力强，训练/跑大模型必需 |
| TPU / NPU | Tensor/Nerual Processing Unit | 谷歌/手机厂商的专用 AI 芯片 |
| RAM / VRAM | 内存 / 显存 | 临时存放数据；跑大模型吃显存 |
| TFLOPS | Tera Floating-point Ops | 每秒万亿次计算，衡量算力 |

---

## 记忆小技巧

1. **别背缩写，记"一句话本质"**：知道 LLM=接话机器、RAG=先查再答、Embedding=文字变数字，比记住全称有用。
2. **缩写会"分层"**：AI ⊃ ML ⊃ DL ⊃ LLM，是包含关系不是并列。
3. **你已经在用了**：RAG、Embedding、Chroma、LLM、Prompt——你天天操作的，只是不知道它们叫这名字。
4. **遇到新缩写三连问**：全称？一句话本质？我在哪遇到它？答得上就过了。
