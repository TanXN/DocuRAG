# DocuRAG

DocuRAG is a lightweight RAG project built with FastAPI, ChromaDB, local embedding models, and DeepSeek API.

It supports uploading TXT / Markdown documents, splitting documents into chunks, generating embeddings locally, storing vectors in ChromaDB, retrieving relevant chunks by user questions, and generating answers with an LLM.

## Features

- Upload TXT and Markdown files
- Parse document text
- Split long text into chunks
- Generate local embeddings with BGE model
- Store vectors in ChromaDB
- Retrieve relevant document chunks
- Generate answers with DeepSeek API
- Simple FastAPI backend
- Suitable for learning RAG basics

## Tech Stack

- Python
- FastAPI
- ChromaDB
- SentenceTransformers
- BAAI/bge-small-zh-v1.5
- DeepSeek API
- Uvicorn

## Project Structure

```text
docurag/
├── app.py
├── rag_service.py
├── requirements.txt
├── .env
├── .gitignore
├── uploads/
├── chroma_db/
└── README.md
```

## Installation

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the virtual environment.

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Windows CMD:

```cmd
.\.venv\Scripts\activate.bat
```

Install dependencies:

```bash
pip install -r requirements.txt
```

If you do not have `requirements.txt`, install manually:

```bash
pip install fastapi uvicorn python-multipart python-dotenv openai chromadb sentence-transformers
```

## Environment Variables

Create a `.env` file in the project root directory:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
```

Do not upload `.env` to GitHub.

## Run the Project

Start the FastAPI server:

```bash
uvicorn app:app --reload --port 8000
```

Open API docs:

```text
http://127.0.0.1:8000/docs
```

## API Usage

### 1. Upload Document

Endpoint:

```http
POST /api/rag/upload
```

Supported file types:

```text
.txt
.md
```

Example response:

```json
{
  "code": 200,
  "msg": "文档上传并入库成功",
  "data": {
    "filename": "test.md",
    "chunk_count": 10
  }
}
```

### 2. Ask Question

Endpoint:

```http
POST /api/rag/chat
```

Request body:

```json
{
  "question": "Nginx 配置文件在哪里？"
}
```

Example response:

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "question": "Nginx 配置文件在哪里？",
    "answer": "根据文档，Nginx 配置文件路径是 /etc/nginx/conf.d/web.conf。",
    "chunks": [
      "Nginx 配置文件路径为：/etc/nginx/conf.d/web.conf"
    ]
  }
}
```

## How It Works

DocuRAG follows a basic RAG pipeline:

```text
Upload document
      ↓
Read text
      ↓
Split text into chunks
      ↓
Generate embeddings
      ↓
Store embeddings in ChromaDB
      ↓
User asks a question
      ↓
Convert question to embedding
      ↓
Retrieve relevant chunks
      ↓
Send chunks and question to LLM
      ↓
Generate final answer
```

## Core Concepts

### Document Chunk

A chunk is a small piece of a document.

Long documents are split into chunks because sending the whole document to an LLM is inefficient and expensive.

### Embedding

An embedding is a vector representation of text.

Texts with similar meanings usually have similar vectors.

Example:

```text
How to restart backend service?
How to restart ccu.service?
```

These two questions have similar meanings, so their embeddings should be close.

### Vector Database

ChromaDB stores document chunks and their embeddings.

When a user asks a question, ChromaDB searches for chunks with similar embeddings.

### LLM Generation

After retrieving relevant chunks, the project sends the chunks and user question to DeepSeek API.

The LLM generates an answer based on the retrieved document content.

## Notes

If you change the embedding model, delete the old ChromaDB data before uploading documents again.

For example, delete:

```text
chroma_db/
```

Different embedding models may generate vectors with different dimensions. Mixing vectors with different dimensions in the same collection can cause errors.

## Recommended `.gitignore`

```gitignore
.env
.venv/
__pycache__/
*.pyc

uploads/
chroma_db/

.idea/
.vscode/
```

## Roadmap

- Support PDF parsing
- Support Word document parsing
- Support document deletion
- Support multiple knowledge bases
- Add streaming output
- Add frontend UI
- Add reranking
- Add hybrid search
- Add user authentication

## License

This project is licensed under the MIT License.
