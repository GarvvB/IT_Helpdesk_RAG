from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Import guardrail functions
from guardrail import (
    input_guardrail,
    retrieval_guardrail,
    output_guardrail,
    calculate_confidence,
    evaluate_answer
)

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vectorstore = Chroma(
    persist_directory="vectorstore",
    embedding_function=embeddings
)

retriever = vectorstore.as_retriever(
    search_kwargs={"k": 3}
)

llm = OllamaLLM(model="llama3.2")

prompt = ChatPromptTemplate.from_template("""
You are an IT Helpdesk Assistant.

Answer the employee's question using only the provided context.

If the answer is not available in the context, say:
"I could not find this information in the available IT documentation."

Do not invent company policies or procedures.

Context:
{context}

Employee Question:
{question}

Answer:
""")

chain = prompt | llm | StrOutputParser()


def ask_question(question):
    """
    Process a user question through the RAG pipeline with guardrails.
    
    Args:
        question: User's input question
        
    Returns:
        Tuple of (answer: str, sources: list[str])
        If guardrails fail, returns error message and empty sources
    """
    # GUARDRAIL 1: Input validation
    input_check = input_guardrail(question)
    if not input_check.passed:
        return input_check.reason, []
    
    # Retrieve relevant documents
    documents = retriever.invoke(question)
    
    # GUARDRAIL 2: Retrieval validation
    retrieval_check = retrieval_guardrail(question, documents)
    if not retrieval_check.passed:
        return retrieval_check.reason, []
    
    # Build context from retrieved documents
    context = "\n\n".join(
        document.page_content
        for document in documents
    )

    # Generate answer using LLM
    answer = chain.invoke({
        "context": context,
        "question": question
    })

    # Extract sources
    sources = []
    for document in documents:
        source = document.metadata.get("source")
        if source and source not in sources:
            sources.append(source)
    
    # GUARDRAIL 3: Output validation
    output_check = output_guardrail(answer, sources)
    if not output_check.passed:
        return output_check.reason, []
    
    # GUARDRAIL 4: Confidence calculation and evaluation
    confidence = calculate_confidence(answer, sources, documents)
    evaluation = evaluate_answer(question, answer, sources, documents, confidence)
    
    # If answer needs review or fails, add a warning
    if evaluation.verdict == "fail":
        return (
            "I'm not confident in my answer to this question. "
            "Please contact the IT Helpdesk directly for accurate information."
        ), []
    elif evaluation.verdict == "needs_review":
        answer = f"{answer}\n\nNote: This answer has moderate confidence ({confidence:.0%}). "
        answer += "Please verify with IT Helpdesk if this is for a critical issue."

    return answer, sources


def ask_question_with_details(question):
    """
    Extended version that returns detailed guardrail evaluation.
    
    Useful for debugging, logging, or advanced UI features.
    
    Args:
        question: User's input question
        
    Returns:
        Dict with answer, sources, confidence, evaluation, and guardrail results
    """
    result = {
        "question": question,
        "answer": None,
        "sources": [],
        "confidence": 0.0,
        "evaluation": None,
        "guardrail_checks": {
            "input": None,
            "retrieval": None,
            "output": None
        }
    }
    
    # Input guardrail
    input_check = input_guardrail(question)
    result["guardrail_checks"]["input"] = input_check
    if not input_check.passed:
        result["answer"] = input_check.reason
        return result
    
    # Retrieval
    documents = retriever.invoke(question)
    retrieval_check = retrieval_guardrail(question, documents)
    result["guardrail_checks"]["retrieval"] = retrieval_check
    if not retrieval_check.passed:
        result["answer"] = retrieval_check.reason
        return result
    
    # Build context and generate
    context = "\n\n".join(doc.page_content for doc in documents)
    answer = chain.invoke({"context": context, "question": question})
    
    # Extract sources
    sources = []
    for doc in documents:
        source = doc.metadata.get("source")
        if source and source not in sources:
            sources.append(source)
    
    # Output guardrail
    output_check = output_guardrail(answer, sources)
    result["guardrail_checks"]["output"] = output_check
    if not output_check.passed:
        result["answer"] = output_check.reason
        return result
    
    # Evaluation
    confidence = calculate_confidence(answer, sources, documents)
    evaluation = evaluate_answer(question, answer, sources, documents, confidence)
    
    result["answer"] = answer
    result["sources"] = sources
    result["confidence"] = confidence
    result["evaluation"] = evaluation
    
    return result