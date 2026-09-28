from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vectorstore = Chroma(
    persist_directory="vectorstore",
    embedding_function=embeddings
)

retriever = vectorstore.as_retriever(
    search_kwargs={"k": 2}
)

question = input("Ask your IT question: ")
documents = retriever.invoke(question)
print("\nRetrieved Documents:\n")

for i, document in enumerate(documents):
    print(f"--- Result {i} ---")
    print(document.page_content)
    print("Source:", document.metadata.get("source"))
    print()