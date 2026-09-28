# IT Helpdesk RAG

A lightweight Retrieval-Augmented Generation (RAG) application for answering employee IT questions using internal documentation such as password policies, VPN guidance, and software installation procedures.

This project combines:
- a Streamlit web app for user interaction,
- a local vector database for document retrieval,
- sentence-transformer embeddings for semantic search,
- an Ollama-hosted LLM for answer generation.

The goal is to help users quickly find answers from policy documents without manually searching through multiple files.

---

## Why this project exists

Many IT teams store policies in plain text or documentation files. This project turns those documents into a searchable knowledge base that can answer natural-language questions like:

- "What is the password reset policy?"
- "How do I install required software on my device?"
- "What steps do I follow to connect to the VPN?"

Instead of relying on a static FAQ, the app retrieves the most relevant passages from the knowledge base and uses a language model to generate a grounded answer.

---

## Features

- Semantic search across IT policy documents
- Local vector storage with Chroma
- Hugging Face embeddings for document retrieval
- Ollama-powered LLM response generation
- Simple, user-friendly Streamlit interface
- Source tracking so users can see which documents were used
- Easy extension with more policy files or new departments

---

## Project structure

```text
IT_Helpdesk_RAG/
├── app.py                 # Streamlit web interface
├── ingest.py              # Ingests documents and builds the vector store
├── rag.py                 # RAG logic: retrieval + LLM answer generation
├── retrieval.py           # Simple CLI retrieval test utility
├── documents/             # IT documentation files used as knowledge base
│   ├── password_policy.txt
│   ├── software_installation_policy.txt
│   └── vpn_guide.txt
├── vectorstore/           # Local Chroma vector database files
├── .env                   # Optional local environment variables
├── .gitignore
├── test_langsmith.py      # LangSmith and Ollama validation script
├── README.md
└── requirements.txt       # If added later for dependency management
```

---

## Technology stack

- Python
- Streamlit
- LangChain
- ChromaDB
- Hugging Face sentence-transformers
- Ollama
- LangSmith (optional tracing and monitoring)

---

## How it works

1. The documents in the `documents/` folder are loaded.
2. Each file is split into smaller text chunks.
3. The chunks are converted into embeddings using `sentence-transformers/all-MiniLM-L6-v2`.
4. The embeddings are stored in a local Chroma vector database.
5. When a user asks a question:
   - the app retrieves the most relevant document chunks,
   - those chunks are passed as context to the LLM,
   - the model answers using only the information available in the retrieved context.

---

## Prerequisites

Before running the project, make sure you have:

- Python 3.10+ installed
- Ollama installed and running locally
- An Ollama model available, such as `llama3.2`
- A virtual environment (recommended)

Install Ollama from: https://ollama.com

After installing Ollama, pull the model:

```bash
ollama pull llama3.2
```

---

## Setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd IT_Helpdesk_RAG
```

### 2. Create and activate a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install streamlit python-dotenv langchain langchain-community langchain-chroma langchain-huggingface langchain-ollama sentence-transformers
```

If you prefer a pinned requirements file, you can generate one later with:

```bash
pip freeze > requirements.txt
```

### 4. Add environment variables (optional)

Create a `.env` file in the project root if you want to enable LangSmith tracing:

```env
LANGSMITH_API_KEY=your_api_key_here
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=it-helpdesk-rag
```

These settings are not required for the app to run locally, but they help with observability and tracing.

---

## Build the knowledge base

Run the ingestion step to load the documents and create the Chroma vector store:

```bash
python ingest.py
```

This will read the files in `documents/` and populate the `vectorstore/` folder.

---

## Run the app

Start the Streamlit interface:

```bash
streamlit run app.py
```

Then open the local URL shown in the terminal, typically:

```text
http://localhost:8501
```

---

## Example usage

In the app, ask questions such as:

- How do I reset my password?
- What is the VPN setup process?
- What software can I install on my machine?
- What do I need to know about company IT policy?

The app will return:
- the generated answer,
- a short list of likely source documents used for retrieval.

---

## Important files

### `app.py`
This file contains the Streamlit UI. It loads environment variables, sets the page title, listens for user input, and displays the generated answer and relevant sources.

### `ingest.py`
This script loads all `.txt` files from `documents/`, chunks them, creates embeddings, and stores them in Chroma.

### `rag.py`
This is the heart of the application. It:
- initializes the retriever,
- fetches relevant chunks from the vector database,
- builds the prompt,
- calls the Ollama model,
- returns the answer and sources.

### `retrieval.py`
A lightweight CLI utility for testing retrieval behavior directly from the terminal.

### `test_langsmith.py`
A simple script to confirm that LangSmith environment settings and the Ollama model are available.

---

## Project notes

- The application is designed for local, private use and works well for internal policy/document lookup.
- It is intentionally simple and easy to extend.
- The system is grounded in retrieved documents, which reduces hallucination risk when the answer is present in the knowledge base.
- If a question is not covered by the available documents, the app is configured to respond with a safe fallback message instead of inventing policy.

---

## Customization ideas

You can extend the project by:

- adding more department policy documents,
- changing the embedding model,
- switching from Ollama to a hosted provider,
- adding a better UI with conversation history,
- supporting PDF/Word document ingestion,
- adding authentication for internal users.

---

## Troubleshooting

### The app cannot find the Ollama model
Run:

```bash
ollama pull llama3.2
```

### No answers are returned
Make sure the vectorstore was built successfully:

```bash
python ingest.py
```

### Document retrieval is poor
Improve the quality by:
- adding more relevant documents,
- refining chunk size and overlap in `ingest.py`,
- adjusting the number of retrieved documents in `rag.py`.

### Dependencies are missing
Reinstall project packages in the active virtual environment:

```bash
pip install streamlit python-dotenv langchain langchain-community langchain-chroma langchain-huggingface langchain-ollama sentence-transformers
```

---

## License

This project is intended for internal or educational use unless a separate license is added by the repository owner.

---

## Summary

This project demonstrates a practical enterprise RAG workflow for IT support documentation. It is a strong starting point for building a company knowledge assistant that can answer policy-based questions using local documents and open-source AI tools.
