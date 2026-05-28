# RAG 为什么会答错，以及我如何优化

## 一、项目背景

我最近实现了一个文档问答系统 DocuRAG。项目的目标是让用户上传自己的文档，然后可以基于文档内容进行问答。

最开始的 RAG v1 版本主要实现了基础链路：

```text
文档上传
  ↓
文档解析
  ↓
文本切块
  ↓
生成 embedding
  ↓
写入向量数据库 ChromaDB
  ↓
根据用户问题进行向量检索
  ↓
把检索到的 chunk 交给大模型生成答案
```

这个版本可以跑通完整流程，但在测试中很快发现一个问题：**文档里明明有答案，系统却回答“文档中没有找到相关信息”**。

这也是很多 RAG 项目从 demo 走向实际可用时都会遇到的问题。大模型本身不一定不会回答，真正的问题经常出在检索阶段：正确的文档片段没有被召回，或者召回顺序不理想，导致大模型根本没有看到正确上下文。

因此，我对项目做了 RAG v2 优化，目标是把它从一个玩具 demo 升级成一个更接近真实工程的面试项目。

---

## 二、RAG v1 的基本实现

RAG v1 的核心流程比较简单。

用户上传 TXT、Markdown 或 PDF 文档后，后端会解析文档内容，然后按照固定长度进行切块。每个 chunk 会通过本地 BGE embedding 模型转成向量，并写入 ChromaDB。

用户提问时，系统会把问题也转成向量，然后在 ChromaDB 中检索相似度最高的 chunks。最后把这些 chunks 拼接成上下文，交给大模型生成答案。

简化后的流程如下：

```text
用户问题
  ↓
embedding
  ↓
ChromaDB 向量检索
  ↓
top_k chunks
  ↓
DeepSeek 生成答案
```

这个版本的优点是实现简单，能够快速理解 RAG 的核心链路。

但它的问题也很明显：**只靠向量检索并不稳定**。

---

## 三、RAG 为什么会答错？

在测试过程中，我发现 RAG 答错主要有几类原因。

---

### 1. 检索没有召回正确 chunk

RAG 的回答依赖检索结果。如果检索阶段没有把正确 chunk 找出来，大模型后面就不可能回答正确。

比如文档中有这样一段：

```text
14. 运维检查清单

每日检查内容：
- Nginx 服务是否正常。
- 后端 API 服务是否正常。
- MySQL 是否可以连接。
- Redis 是否可以连接。
- MQTT Broker 是否正常运行。
- 是否存在大量离线设备。
- 最近一小时是否有传感器数据上报。
- 报警记录是否正常生成。
- 磁盘空间是否充足。
```

如果用户问：

```text
智能温室监控平台每日检查内容
```

向量检索有时会被“智能温室监控平台”这些范围词带偏，召回系统介绍、架构说明等片段，而不是“每日检查内容”所在的片段。

这时大模型看到的上下文里没有答案，就只能回答：

```text
文档中没有找到相关信息。
```

这不是大模型生成错了，而是检索错了。

---

### 2. 用户表达和文档表达不一致

用户提问时使用的表达，和文档里的正式表达不一定完全相同。

例如用户可能问：

```text
温控平台每日检查内容
```

但文档里写的是：

```text
智能温室监控平台
运维检查清单
每日检查内容
```

向量检索虽然能处理一定程度的语义相似，但并不能保证每次都准确命中。尤其是在业务词、简称、别名、口语表达较多的场景下，检索结果容易不稳定。

---

### 3. 精确字符串不适合只靠向量检索

很多企业文档里有大量精确字符串，例如：

```text
18081
6379
1883
greenhouse-api.service
/etc/nginx/conf.d/greenhouse.conf
t_sensor_data
systemctl restart nginx
```

这些内容不适合只靠 embedding 检索。

比如用户问：

```text
greenhouse-api.service 怎么重启？
```

最重要的是找到包含 `greenhouse-api.service` 和 `systemctl restart greenhouse-api.service` 的片段。

这种场景下，关键词检索比向量检索更稳定。

---

### 4. 召回结果相关，但排序不一定最优

即使正确 chunk 已经进入候选集，它也不一定排在第一位。

比如用户问：

```text
智能温室监控平台每日检查内容
```

Elasticsearch BM25 可能会召回：

```text
第 1 条：智能温室监控平台文档说明
第 2 条：RAG 测试问题
第 3 条：每日检查内容
```

从 BM25 的角度看，第一页文档说明命中了“智能、温室、监控、平台”等多个词，分数可能更高。但从问答角度看，真正能回答问题的是第三条“每日检查内容”。

所以 RAG 不能只做召回，还需要 rerank 进行重排序。

---

### 5. 缺少引用来源，无法判断答案依据

RAG v1 只返回答案，不返回来源。

这会带来两个问题：

第一，用户不知道答案来自哪里。
第二，开发者无法排查错误答案到底是检索问题，还是大模型生成问题。

所以 RAG v2 需要返回来源信息，例如：

```json
{
  "source_id": "S0",
  "file_name": "智能温室监控平台部署与运维手册.pdf",
  "page": 3,
  "chunk_index": 4
}
```

这样可以明确知道答案基于哪些文档片段生成。

---

## 四、优化一：支持 PDF 并保留页码

RAG v1 只处理 TXT 和 Markdown。为了更接近真实知识库场景，我加入了 PDF 支持。

PDF 解析时，我没有把整份 PDF 简单拼成一个大字符串，而是按页解析：

```text
PDF 第 1 页 -> text + page=1
PDF 第 2 页 -> text + page=2
PDF 第 3 页 -> text + page=3
```

这样每个 chunk 都能保留页码信息。

写入数据库时，每个 chunk 的 metadata 里会保存：

```json
{
  "file_name": "智能温室监控平台部署与运维手册.pdf",
  "file_type": ".pdf",
  "page": 15,
  "chunk_index": 27
}
```

这样后续回答时可以返回：

```text
来源：智能温室监控平台部署与运维手册.pdf，第 15 页，chunk 27
```

这个改动解决了 RAG 系统的一个重要问题：**答案可追溯**。

---

## 五、优化二：加入 Elasticsearch + IK + BM25 关键词检索

只靠向量检索不稳定，所以我引入了 Elasticsearch 作为关键词检索引擎。

文档切块后，每个 chunk 会同时写入两套存储：

```text
ChromaDB：
存 embedding、document、metadata，用于向量检索

Elasticsearch：
存 content、file_name、page、chunk_index，用于关键词检索
```

Elasticsearch 的 content 字段使用 IK 中文分词器：

```json
{
  "content": {
    "type": "text",
    "analyzer": "ik_max_word",
    "search_analyzer": "ik_smart"
  }
}
```

其中：

```text
ik_max_word：写入文档时尽量细粒度切词，提高召回率
ik_smart：查询时使用较粗粒度切词，减少噪音
```

加入 Elasticsearch 后，像下面这些问题就能更稳定地召回正确片段：

```text
greenhouse-api.service 怎么重启？
Nginx 配置文件路径是什么？
MySQL 备份目录在哪里？
后端服务端口是多少？
```

关键词检索主要解决的是：

```text
路径
端口
命令
服务名
表名
字段名
配置项
```

这些内容是向量检索不太稳定，但 BM25 很擅长的场景。

---

## 六、优化三：混合召回

RAG v2 中，我没有用 Elasticsearch 替代 ChromaDB，而是让两者各自发挥优势。

```text
ChromaDB 向量检索：
负责语义相似，适合用户换一种说法提问

Elasticsearch BM25：
负责关键词命中，适合路径、端口、命令、服务名等精确内容
```

查询时，系统会同时执行两路召回：

```text
用户问题
  ↓
ChromaDB vector_search top_k
  ↓
Elasticsearch keyword_search top_k
  ↓
合并去重
```

合并时使用 `chunk_id` 作为唯一标识。

同一个 chunk 如果同时被向量检索和关键词检索命中，只保留一份，避免重复塞进 prompt。

混合召回解决了一个关键问题：**不再依赖单一检索方式**。

只要正确 chunk 被其中一路召回，后面就还有 rerank 和大模型回答的机会。

---

## 七、优化四：加入 rerank 重排序

混合召回解决的是“找得到”的问题，但还不能保证“排得准”。

所以我加入了 CrossEncoder reranker。

向量检索和关键词检索都是召回阶段，它们负责快速找出一批可能相关的 chunks。而 rerank 是精排阶段，它会对：

```text
用户问题 + 候选 chunk
```

进行相关性打分。

流程如下：

```text
vector_search top 20
keyword_search top 20
  ↓
合并去重
  ↓
CrossEncoder rerank
  ↓
取 top 5
```

reranker 和 embedding 模型不同：

```text
embedding 模型：
单独把问题和文档转成向量，再计算相似度，速度快，适合大规模召回

reranker 模型：
直接输入 question 和 chunk，输出相关性分数，速度慢，但排序更准
```

在项目中，rerank 后每个 chunk 会带上：

```json
{
  "rerank_score": 0.9765
}
```

最终进入大模型上下文的是 rerank 后的 top chunks。

这样可以减少无关 chunk 进入 prompt，提高回答准确率。

---

## 八、优化五：加入引用来源

RAG 里的“引用来源”不是从大模型内部自动推断出来的，而是在检索阶段设计出来的。

我的做法是：

```text
1. 每个 chunk 入库时保存 file_name、page、chunk_index
2. 检索和 rerank 后，给最终 chunks 编号：S0、S1、S2
3. 把 source_id 和 chunk 内容一起放进 prompt
4. 要求大模型回答时在关键结论后标注 [S0]、[S1]
5. 接口返回 chunks，里面包含 source_id 和 metadata
```

例如：

```json
{
  "source_id": "S0",
  "document": "后端服务使用 FastAPI 开发，运行端口为：18081 ...",
  "metadata": {
    "file_name": "智能温室监控平台部署与运维手册.pdf",
    "page": 3,
    "chunk_index": 4
  },
  "retrieval_type": "vector",
  "rerank_score": 0.9765
}
```

回答示例：

```text
后端服务运行端口为 18081 [S0]。
```

需要注意的是，这种引用表示：

```text
这些 chunks 是系统提供给大模型生成答案的证据来源
```

它不等于系统数学上证明了每一个字都来自某个 chunk。

如果要做到更严格的逐句溯源，还需要在答案生成后进行句子级别的证据校验。这属于更进一步的优化。

---

## 九、优化六：加入问答历史

为了方便用户查看历史记录，也为了方便开发者复盘 RAG 错误案例，我加入了问答历史模块。

当前使用 SQLite 保存：

```text
question
answer
chunks_json
created_at
```

每次用户提问后，系统会保存：

```text
用户问题
大模型回答
检索到的 chunks
来源信息
rerank 分数
创建时间
```

这样可以方便地查看：

```text
这个问题当时召回了哪些 chunk？
rerank 后哪些 chunk 进入了 prompt？
答案引用了哪些 source？
错误答案是检索问题，还是生成问题？
```

这对 RAG 项目非常重要。因为 RAG 的优化不是一次完成的，而是需要不断观察错误案例，然后针对性优化检索、切块、rerank 和 prompt。

---

## 十、优化后的整体架构

RAG v2 的整体流程如下：

```text
文档上传
  ↓
解析 TXT / Markdown / PDF
  ↓
按页读取 PDF，保留 page 信息
  ↓
文本切块
  ↓
生成 chunk_id
  ↓
写入 ChromaDB：embedding + document + metadata
  ↓
写入 Elasticsearch：content + metadata
```

用户提问时：

```text
用户问题
  ↓
ChromaDB 向量检索
  ↓
Elasticsearch BM25 关键词检索
  ↓
按 chunk_id 合并去重
  ↓
CrossEncoder rerank 重排序
  ↓
取 top chunks
  ↓
构造带 source_id 的 prompt
  ↓
DeepSeek 生成答案
  ↓
保存问答历史
  ↓
返回 answer + chunks
```

最终技术栈包括：

```text
FastAPI
Pydantic
PyMuPDF
BGE embedding
ChromaDB
Elasticsearch
IK Analyzer
BM25
BGE reranker
DeepSeek API
SQLite
Docker
```

---

## 十一、优化效果

优化前，只靠向量检索时，系统容易出现：

```text
文档里有答案，但回答“文档中没有找到相关信息”
```

尤其是当用户问题包含系统名、项目名、范围词时，向量检索可能被带偏。

优化后，Elasticsearch BM25 可以把包含关键词的 chunk 召回进候选集。即使它不是第一条，只要进入 top_k，后续 rerank 仍然可以把真正能回答问题的 chunk 排到前面。

例如问题：

```text
智能温室监控平台每日检查内容
```

关键词检索可以召回包含“每日检查内容”的 chunk，reranker 再判断该 chunk 与问题最相关，最终大模型能够正确回答：

```text
每日检查内容包括检查 Nginx 服务、后端 API 服务、MySQL、Redis、MQTT Broker、离线设备、最近一小时数据上报、报警记录和磁盘空间。
```

再比如：

```text
greenhouse-api.service 怎么重启？
```

系统可以召回包含命令的 chunk，并回答：

```text
可以使用 systemctl restart greenhouse-api.service 重启服务。
```

对于路径、端口、服务名、配置项等问题，关键词检索的加入明显提高了稳定性。

---

## 十二、项目总结

通过这次优化，我对 RAG 的理解从“把文档塞进向量数据库，然后让大模型回答”变成了更工程化的认识。

RAG 答错通常不是单一原因，而是多个环节共同影响：

```text
文档解析质量
chunk 切分方式
embedding 表达能力
向量检索召回率
关键词检索能力
候选结果排序
prompt 构造
来源引用
历史记录和错误复盘
```

RAG v1 能跑通流程，但还只是 demo。

RAG v2 加入 PDF 支持、Elasticsearch + IK + BM25、混合召回、rerank、引用来源和问答历史后，系统才更接近一个可展示、可调试、可解释的工程项目。

最终我认为，一个更可靠的 RAG 系统不应该只依赖向量检索，而应该采用：

```text
向量检索负责语义召回
关键词检索负责精确召回
rerank 负责精排
引用来源负责可解释性
问答历史负责错误复盘
```

这也是我这次 RAG v2 优化的核心思路。
