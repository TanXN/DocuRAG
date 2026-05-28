# DocuRAG - 企业知识库问答系统 RAG v2

DocuRAG 是一个面向企业知识库问答场景的轻量级 RAG 项目。项目基于 FastAPI、ChromaDB、Elasticsearch、SentenceTransformers 和 DeepSeek API，实现了从文档上传、解析、切块、向量化、混合召回、rerank 到带来源引用回答的完整链路。

相比 v1 版本，v2 不再只是“能跑通 RAG 流程”的 demo，而是重点解决真实问答中常见的检索不准、关键词丢失、答案无来源、结果不可追溯等问题。



## 项目目标

第 6 周 RAG 优化 v2 的目标：

- 支持 PDF 文档解析。
- 增加 Elasticsearch 关键词检索。
- 增加向量检索 + 关键词检索的混合召回。
- 增加 CrossEncoder rerank 重排序。
- 生成答案时返回引用来源。
- 保存问答历史，方便追踪每次问答使用了哪些片段。

## 系统架构

DocuRAG v2 的整体架构如下：

<p align="center">
  <img src="docsmages/rag-v2-architecture.png" alt="DocuRAG RAG v2 系统架构图" width="900">
</p>

整体流程分为四个部分：

1. **文档入库**：上传 TXT、Markdown、PDF 文档，解析后切块，并同时写入 ChromaDB 和 Elasticsearch。
2. **用户提问与检索**：用户问题会同时经过向量检索和关键词检索，再进行混合召回、去重和 rerank。
3. **答案生成**：系统将最终筛选出的 chunks 构造成 Prompt，交给 DeepSeek 生成带来源引用的答案。
4. **历史与追溯**：每次问答都会保存 question、answer、chunks 和 created_at，方便后续复盘。

## 核心功能

- 文档上传：支持 `.txt`、`.md`、`.pdf`。
- 文档解析：TXT / Markdown 直接读取，PDF 使用 PyMuPDF 按页抽取文本。
- 文本切块：长文本按固定窗口切分，并保留 overlap。
- 向量检索：使用本地 BGE embedding 模型生成向量，写入 ChromaDB。
- 关键词检索：使用 Elasticsearch BM25 做全文关键词匹配。
- 混合召回：合并向量召回和关键词召回结果，并去重。
- Rerank：使用本地 BGE reranker 对候选片段重新排序。
- 来源引用：回答中使用 `[S0]`、`[S1]` 等来源编号标注依据。
- 问答历史：使用 SQLite 保存 question、answer、chunks 和 created_at。
- FastAPI 接口：提供上传、问答、向量检索、关键词检索、混合检索、rerank 检索和历史查询接口。

## 技术栈

- Python
- FastAPI
- Uvicorn
- ChromaDB
- Elasticsearch
- SQLite
- PyMuPDF
- SentenceTransformers
- BAAI/bge-small-zh-v1.5
- BAAI/bge-reranker-base
- DeepSeek API

## 项目结构

```text
rag/
├── app.py                # FastAPI 接口入口
├── rag_service.py        # RAG 核心流程：解析、切块、向量化、召回、生成
├── es_store.py           # Elasticsearch 索引创建、写入和关键词检索
├── reranker.py           # CrossEncoder rerank 逻辑
├── history_service.py    # SQLite 问答历史
├── requirement.txt       # Python 依赖
├── docs/
│   └── images/
│       └── rag-v2-architecture.png # RAG v2 架构图
├── uploads/              # 上传文件目录
├── chroma_db/            # ChromaDB 持久化目录
├── rag_history.db        # 问答历史数据库，运行后生成
├── .env                  # 环境变量，本地创建，不提交
└── README.md
```

## 安装依赖

创建虚拟环境：

```bash
python -m venv .venv
```

Windows PowerShell 激活虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

安装依赖：

```bash
pip install -r requirement.txt
```

如果本地依赖文件还没有包含 Elasticsearch 客户端，需要额外安装：

```bash
pip install elasticsearch
```

## 环境变量

在项目根目录创建 `.env` 文件：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
```

`.env` 不要提交到 GitHub。

## 本地模型

当前代码使用本地模型路径：

```text
D:\Models\bge-small-zh-v1.5
D:\Models\bge-reranker-base
```

如果你的模型路径不同，需要修改 `rag_service.py` 和 `reranker.py` 中的模型路径。

## 启动 Elasticsearch

项目 v2 使用 Elasticsearch 做关键词检索，并且 `es_store.py` 中配置了 `ik_max_word` 和 `ik_smart` 分词器。

先使用项目里的 `Dockerfile.elasticsearch` 构建一个自动安装 IK 插件的 Elasticsearch 镜像：

```powershell
docker build `
  -f Dockerfile.elasticsearch `
  --build-arg ELASTIC_VERSION=9.4.1 `
  -t docurag-elasticsearch-ik:9.4.1 `
  .
```

然后启动单节点 ES：

```powershell
docker run --name docurag-es `
  -p 9200:9200 `
  -e "discovery.type=single-node" `
  -e "xpack.security.enabled=false" `
  -e "ES_JAVA_OPTS=-Xms1g -Xmx1g" `
  docurag-elasticsearch-ik:9.4.1
```

`Dockerfile.elasticsearch` 会在构建阶段执行：

```dockerfile
RUN elasticsearch-plugin install --batch \
    https://get.infini.cloud/elasticsearch/analysis-ik/${ELASTIC_VERSION}
```

IK 插件版本必须和 Elasticsearch 版本一致。如果你修改了 Elasticsearch 版本，也要同步修改 `ELASTIC_VERSION`。

当前 `es_store.py` 使用的地址：

```text
http://localhost:9200
```

索引名：

```text
docurag_chunks
```

## 启动项目

```bash
uvicorn app:app --reload --port 8000
```

打开接口文档：

```text
http://127.0.0.1:8000/docs
```

服务启动时会自动：

- 创建 Elasticsearch 索引。
- 初始化 SQLite 问答历史表。

## API 接口

### 1. 上传文档

```http
POST /api/rag/upload
```

支持文件类型：

```text
.txt
.md
.pdf
```

示例响应：

```json
{
  "code": 200,
  "msg": "文档上传并入库成功",
  "data": {
    "filename": "ops.pdf",
    "chunk_count": 12
  }
}
```

上传后会同时写入：

- ChromaDB：用于向量检索。
- Elasticsearch：用于关键词检索。

### 2. RAG 问答

```http
POST /api/reg/chat
```

请求体：

```json
{
  "question": "智能温室监控平台每日检查哪些内容？"
}
```

示例响应：

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "question": "智能温室监控平台每日检查哪些内容？",
    "answer": "每日需要检查设备在线状态、传感器数据和告警记录等内容。[S0]",
    "chunks": [
      {
        "document": "每日检查内容包括设备在线状态、传感器数据、告警记录...",
        "metadata": {
          "file_name": "ops.pdf",
          "file_type": ".pdf",
          "page": 3,
          "chunk_index": 8
        },
        "retrieval_type": "keyword",
        "rerank_score": 0.87,
        "source_id": "S0"
      }
    ]
  }
}
```

### 3. 向量检索

```http
POST /api/reg/vector-search
```

只使用 ChromaDB 向量相似度检索，适合语义相近但关键词不完全一致的问题。

### 4. 关键词检索

```http
POST /api/reg/key-word-search
```

只使用 Elasticsearch BM25 检索，适合专有名词、系统名称、配置项、路径、编号等精确关键词。

### 5. 混合召回

```http
POST /api/reg/hybrid-search
```

同时使用：

- ChromaDB 向量检索。
- Elasticsearch 关键词检索。

然后合并结果并按照 `chunk_index` 去重。

### 6. Rerank 检索

```http
POST /api/reg/rerank-search
```

先做混合召回，再使用 CrossEncoder reranker 重新计算“问题-片段”的相关性分数，返回最终 Top N。

### 7. 问答历史

```http
GET /api/reg/rag-history?limit=50
```

返回最近的问答记录，包括问题、答案、引用片段和创建时间。

## RAG v2 工作流程

```text
上传文档
  -> 解析 TXT / Markdown / PDF
  -> 文本切块
  -> 生成 embedding
  -> 写入 ChromaDB
  -> 写入 Elasticsearch

用户提问
  -> 向量检索召回候选片段
  -> 关键词检索召回候选片段
  -> 混合召回并去重
  -> rerank 重排序
  -> 给片段添加来源编号
  -> 拼接 prompt
  -> 调用 DeepSeek 生成答案
  -> 保存问答历史
  -> 返回答案、引用来源和命中的 chunks
```

## 为什么要从 v1 优化到 v2

v1 版本只做向量检索，能跑通 RAG 全链路，但在真实企业知识库里容易出现几个问题：

- 用户问题和文档表达不一致时，向量检索可能召回不稳定。
- 专有名词、配置项、设备名称、路径、编号等信息更依赖关键词匹配。
- 只看 Top K 向量结果时，真正相关的片段可能排在后面。
- LLM 生成答案时如果没有来源约束，容易产生看似合理但文档中不存在的内容。
- 没有历史记录时，不方便复盘某次问答为什么答错。

v2 的优化思路是：

- 用 PDF 解析扩大知识库文档类型。
- 用 Elasticsearch 弥补向量检索对精确关键词不敏感的问题。
- 用混合召回提高候选片段覆盖率。
- 用 rerank 在候选片段中挑出更相关的内容。
- 用来源编号让答案可追溯。
- 用 SQLite 保存问答历史，方便调试和复盘。

## RAG 为什么会答错，以及我如何优化

RAG 答错通常不是单一原因，而是检索、排序、上下文和生成共同造成的。

第一类问题是“没有召回正确片段”。例如用户问“温室平台每日检查内容”，但文档中写的是“智能温室监控平台运维检查内容”。这两个表达在语义上相关，但如果 embedding 模型理解不稳定，或者文档里包含大量相似内容，向量检索可能把真正的答案排到后面。

第二类问题是“关键词信息被语义检索弱化”。企业文档里有很多专有名词、接口路径、配置文件、设备编号、告警码。这些内容不一定需要复杂语义理解，反而需要精确匹配。只用向量检索时，模型可能认为几个相似段落都差不多，导致召回结果不够准。

第三类问题是“召回了相关内容，但排序不对”。向量检索和 BM25 都是第一阶段召回，更关注快速找候选结果。它们不一定能精细判断“这个片段是否真正回答了当前问题”。因此 v2 增加 CrossEncoder reranker，让模型重新阅读“问题 + 文档片段”组合，并给候选片段重新打分。

第四类问题是“生成阶段没有约束”。如果 prompt 没有要求模型只基于文档回答，LLM 可能会补充自己的常识，产生幻觉。v2 在 prompt 中明确要求：文档中没有答案就回答没有找到相关信息，并且关键结论尽量标注来源编号。

第五类问题是“答错后无法复盘”。v1 只返回答案，很难判断问题出在召回、排序还是生成。v2 保存问答历史，并返回命中的 chunks、metadata、retrieval_type、rerank_score 和 source_id，这样可以看到答案到底依据了哪些片段。

最终优化后的链路是：先扩大候选召回范围，再用 rerank 精排，最后用带引用约束的 prompt 生成答案。这样既提高了召回覆盖率，也提高了答案可信度。

## v1 与 v2 对比

| 能力 | RAG v1 | RAG v2 |
| --- | --- | --- |
| 文档类型 | TXT / Markdown | TXT / Markdown / PDF |
| 检索方式 | 向量检索 | 向量检索 + BM25 关键词检索 |
| 召回策略 | 单路召回 | 混合召回 |
| 排序方式 | 向量相似度 Top K | CrossEncoder rerank |
| 来源引用 | 不完整 | 使用 source_id 标注 |
| 问答历史 | 无 | SQLite 持久化保存 |
| 可调试性 | 较弱 | 可查看 chunks、分数、来源和历史 |

## 注意事项

- 如果更换 embedding 模型，建议删除旧的 `chroma_db/` 后重新上传文档。
- 不同 embedding 模型的向量维度可能不同，混用会导致 ChromaDB 查询或写入异常。
- 当前 PDF 解析适合文本型 PDF；扫描版或图片型 PDF 可能无法抽取文本。
- 如果 Elasticsearch 没有启动，上传文档或关键词检索会失败。
- 当前代码中 API 前缀同时存在 `/api/rag` 和 `/api/reg`，README 按现有代码接口记录。

## 后续优化方向

- 支持 Word / Excel 等更多企业文档格式。
- 增加文档删除和重新入库。
- 支持多知识库隔离。
- 增加用户登录和权限控制。
- 增加流式输出。
- 增加前端页面。
- 引入更细粒度的 chunk 元数据和引用展示。
- 对 PDF 扫描件增加 OCR。

## License

This project is licensed under the MIT License.
