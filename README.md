# IT Helpdesk RAG

A lightweight Retrieval-Augmented Generation (RAG) application for answering employee IT questions using internal documentation such as password policies, VPN guidance, and software installation procedures.

This project combines:
- a Streamlit web app for user interaction,
- a local vector database for document retrieval,
- sentence-transformer embeddings for semantic search,
- an Ollama-hosted LLM for answer generation,
- **comprehensive guardrails for safe and accurate responses**.

The goal is to help users quickly find answers from policy documents without manually searching through multiple files.

---

## System Workflow & Orchestration

### High-Level Architecture

```
User Question
     |
     v
[Input Guardrails] --> Block if unsafe/off-topic
     |
     v
[Vector Database] --> Retrieve relevant documents (k=3)
     |
     v
[Retrieval Guardrails] --> Validate documents found
     |
     v
[Build Context] --> Combine retrieved document chunks
     |
     v
[LLM (Llama 3.2)] --> Generate answer from context
     |
     v
[Output Guardrails] --> Block if credentials/PII leaked
     |
     v
[Confidence Scoring] --> Calculate answer confidence (0-1)
     |
     v
[Quality Evaluation] --> Assess groundedness & relevance
     |
     v
Final Answer + Sources --> Display to user
```

### Detailed Processing Pipeline

#### 1. User Input (Streamlit UI)
- User submits question via web interface
- `app.py` calls `ask_question(question)`

#### 2. Input Guardrails (First Safety Layer)
**Function**: `input_guardrail(question)`
- Checks minimum length (3+ characters)
- Detects gibberish/keyboard mashing
- Scans for PII: SSN, credit cards, phone numbers, emails
- Blocks security keywords: "hack", "exploit", "bypass security"
- Validates IT-related topic using keyword matching
- **Result**: PASS → continue | FAIL → return error message

#### 3. Document Retrieval (Vector Search)
**Function**: `retriever.invoke(question)`
- Converts question to embedding using `sentence-transformers/all-MiniLM-L6-v2`
- Searches ChromaDB vector store
- Retrieves top k=3 most similar document chunks
- **Returns**: List of Document objects with content and metadata

#### 4. Retrieval Guardrails (Second Safety Layer)
**Function**: `retrieval_guardrail(question, documents)`
- Verifies documents were found (not empty)
- Validates minimum quality threshold
- **Result**: PASS → continue | FAIL → return "no documentation found"

#### 5. Context Building
```python
context = "\n\n".join(document.page_content for document in documents)
```
- Combines retrieved document chunks into single context string
- Separates chunks with double newlines for clarity

#### 6. LLM Generation (Answer Synthesis)
**Function**: `chain.invoke({"context": context, "question": question})`

**Prompt Template**:
```
You are an IT Helpdesk Assistant.

Answer the employee's question using only the provided context.

If the answer is not available in the context, say:
"I could not find this information in the available IT documentation."

Do not invent company policies or procedures.

Context:
{retrieved document chunks}

Employee Question:
{user's question}

Answer:
```

- LLM (Llama 3.2) processes the prompt
- Generates natural language answer based ONLY on provided context
- **Important**: LLM synthesizes an answer - it doesn't just return raw documents
- **Returns**: Generated answer string

#### 7. Output Guardrails (Third Safety Layer)
**Function**: `output_guardrail(answer, sources)`
- Validates answer length (10+ characters)
- Scans for PII leakage: SSN, emails, phone numbers
- Detects credential exposure: usernames, passwords
- Flags unsupported claims: "guaranteed", "100% secure", legal advice
- Verifies sources are present (prevents hallucination)
- **Result**: PASS → continue | FAIL → return safety error

#### 8. Confidence Scoring
**Function**: `calculate_confidence(answer, sources, documents)`

**Factors**:
- Number of sources (more sources = higher confidence)
- Hedge phrases ("might", "possibly", "unclear" = lower confidence)
- Answer length (very short = lower confidence)
- Explicit uncertainty ("I don't know" = very low confidence)
- Generic fallback ("contact IT helpdesk" = lower confidence)

**Returns**: Float between 0.0 and 1.0

#### 9. Quality Evaluation
**Function**: `evaluate_answer(question, answer, sources, documents, confidence)`

**Metrics**:
- **Groundedness**: Is answer supported by retrieved context?
- **Relevance**: Does answer address the question?
- **Hallucination Risk**: Low, medium, or high
- **Verdict**: 
  - `confidence < 0.5` → FAIL
  - `confidence < 0.7` → NEEDS_REVIEW
  - `confidence >= 0.7` → PASS

**Returns**: AnswerEvaluation object

#### 10. Final Response Assembly
```python
if verdict == "fail":
    return "Not confident, contact IT directly", []
elif verdict == "needs_review":
    return answer + "\n\nNote: Moderate confidence. Verify for critical issues.", sources
else:
    return answer, sources
```

### Example Complete Trace

**User Input**: "How do I reset my password?"

1. **Input Guardrail**: ✓ PASS (valid IT question, no PII, contains "password" keyword)

2. **Document Retrieval**: Retrieved 3 chunks:
   - `documents/password_policy.txt` (chunk 0): "Company Password Policy..."
   - `documents/password_policy.txt` (chunk 1): "If an employee forgets..."
   - `documents/vpn_guide.txt` (chunk 2): "Employees must connect..."

3. **Retrieval Guardrail**: ✓ PASS (3 documents found)

4. **Context Built**:
   ```
   Company Password Policy
   
   Employees must use their company credentials to access company systems.
   
   If an employee forgets their password:
   1. Open the company password management portal.
   2. Select Forgot Password.
   3. Enter the registered company email address.
   4. Complete identity verification.
   5. Create a new password.
   ```

5. **LLM Generation** (Llama 3.2):
   ```
   To reset your password, follow these steps:
   
   1. Open the company password management portal
   2. Select "Forgot Password"
   3. Enter your registered company email address
   4. Complete the identity verification process
   5. Create a new password
   
   If password recovery fails, contact the IT Helpdesk for assistance.
   ```

6. **Output Guardrail**: ✓ PASS (no PII leaked, no credentials exposed, answer has sources)

7. **Confidence Score**: 0.92 (high - 3 sources, clear answer, no hedge phrases)

8. **Quality Evaluation**:
   - Groundedness: 1.0 (fully supported by context)
   - Relevance: 0.85 (directly addresses password reset)
   - Hallucination Risk: Low
   - Verdict: PASS

9. **Final Response**:
   - Answer: [LLM-generated answer above]
   - Sources: [`documents/password_policy.txt`]

---

## Key Points About the LLM

### What the LLM Does

✓ **Synthesizes answers** from retrieved context  
✓ **Reformats** information in natural language  
✓ **Combines** multiple document chunks coherently  
✓ **Adds structure** (e.g., numbered steps, clear explanations)  
✓ **Handles edge cases** (e.g., "contact IT if this fails")  

### What the LLM Does NOT Do

✗ Does NOT just return raw document text  
✗ Does NOT invent policies not in the context  
✗ Does NOT use outside knowledge (constrained to context)  
✗ Does NOT access the internet or other data sources  

### LLM vs Retrieval-Only

| Approach | Output |
|----------|--------|
| **Retrieval Only** | Raw chunks: "Company Password Policy. Employees must use... If an employee forgets..." |
| **LLM + Retrieval (RAG)** | Natural answer: "To reset your password, follow these steps: 1. Open the portal, 2. Select Forgot Password..." |

The LLM **transforms** retrieved context into a **conversational, helpful answer**.

---

## Guardrails System

This application includes **production-grade safety measures** at multiple layers:

### 1. Input Guardrails
- Validates question length and format
- Detects and blocks PII (SSN, credit cards, phone numbers, emails)
- Filters gibberish and keyboard mashing
- Blocks security threats ("hack", "bypass security")
- Ensures questions are IT-related

### 2. Retrieval Guardrails
- Validates that relevant documents were found
- Ensures minimum quality thresholds

### 3. Output Guardrails
- Prevents credential leakage in responses
- Blocks unsupported claims (guarantees, legal advice)
- Detects sensitive information in generated answers
- Ensures responses are grounded in source documents

### 4. Confidence Scoring & Evaluation
- Calculates confidence based on sources, answer quality, and uncertainty
- Evaluates groundedness and relevance
- Assigns verdicts: pass, needs_review, or fail
- Flags low-confidence answers for user awareness

### Testing Guardrails

Run the comprehensive test suite:

```bash
python test_guardrails.py
```

Expected output:
```
37 tests passing (100% success rate)
- Input validation: 17 tests
- Retrieval validation: 3 tests
- Output validation: 10 tests
- Confidence calculation: 4 tests
- Answer evaluation: 3 tests
```

For detailed documentation, see **[GUARDRAILS.md](GUARDRAILS.md)**.

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
- Multi-layer guardrails for safety and quality

---

## Project structure

```text
IT_Helpdesk_RAG/
├── app.py                           # Streamlit web interface
├── ingest.py                        # Ingests documents and builds the vector store
├── rag.py                           # RAG logic: retrieval + LLM answer generation (with guardrails)
├── retrieval.py                     # Simple CLI retrieval test utility
├── guardrail.py                     # Multi-layer guardrail system
├── test_guardrails.py               # Comprehensive guardrail test suite
├── reference_guardrail.py           # Reference implementation for inspiration
├── guardrail_config_example.py      # Configuration template
├── GUARDRAILS.md                    # Complete guardrail documentation
├── QUICKSTART_GUARDRAILS.md         # Quick start guide
├── IMPLEMENTATION_SUMMARY.md        # Implementation details
├── GUARDRAILS_INDEX.md              # File navigation
├── documents/                       # IT documentation files used as knowledge base
│   ├── password_policy.txt
│   ├── software_installation_policy.txt
│   └── vpn_guide.txt
├── vectorstore/                     # Local Chroma vector database files
├── .env                             # Optional local environment variables
├── .gitignore
├── test_langsmith.py                # LangSmith and Ollama validation script
└── README.md
```

---

## Technology stack

- Python 3.10+
- Streamlit
- LangChain
- ChromaDB
- Hugging Face sentence-transformers
- Ollama (Llama 3.2)
- LangSmith (optional tracing and monitoring)

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
- the generated answer (synthesized by LLM from retrieved context),
- a short list of source documents used for retrieval.

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
- builds the prompt with context,
- calls the Ollama model (Llama 3.2),
- applies guardrails at each step,
- returns the answer and sources.

### `guardrail.py`
Multi-layer safety system that validates inputs, retrieval, outputs, and calculates confidence scores.

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
- The LLM synthesizes answers from context - it does not just return raw document text.

---

## Customization ideas

You can extend the project by:

- adding more department policy documents,
- changing the embedding model,
- switching from Ollama to a hosted provider,
- adding a better UI with conversation history,
- supporting PDF/Word document ingestion,
- adding authentication for internal users,
- adjusting guardrail thresholds in `guardrail_config_example.py`.

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
- adjusting the number of retrieved documents in `rag.py` (k parameter).

### Dependencies are missing
Reinstall project packages in the active virtual environment:

```bash
pip install streamlit python-dotenv langchain langchain-community langchain-chroma langchain-huggingface langchain-ollama sentence-transformers
```

### Guardrails blocking legitimate questions
See `GUARDRAILS.md` troubleshooting section or customize keywords in `guardrail_config_example.py`.

---

## License

This project is intended for internal or educational use unless a separate license is added by the repository owner.

---

## Summary

This project demonstrates a practical enterprise RAG workflow for IT support documentation. It is a strong starting point for building a company knowledge assistant that can answer policy-based questions using local documents and open-source AI tools.

The guardrail system ensures safe, accurate, and high-quality responses while the LLM provides natural, conversational answers based on your company's actual policies.
