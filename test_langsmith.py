import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM

load_dotenv()

print("API:", bool(os.getenv("LANGSMITH_API_KEY")))
print("TRACING:", os.getenv("LANGSMITH_TRACING"))
print("PROJECT:", os.getenv("LANGSMITH_PROJECT"))

prompt = ChatPromptTemplate.from_template(
    "Answer this question briefly: {question}"
)

llm = OllamaLLM(model="llama3.2")

chain = prompt | llm

answer = chain.invoke(
    {"question": "What is RAG?"}
)

print("\nAnswer:")
print(answer)