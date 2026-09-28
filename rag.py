from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

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
    documents = retriever.invoke(question)

    context = "\n\n".join(
        document.page_content
        for document in documents
    )

    answer = chain.invoke({
        "context": context,
        "question": question
    })

    sources = []

    for document in documents:
        source = document.metadata.get("source")

        if source and source not in sources:
            sources.append(source)

    return answer, sources