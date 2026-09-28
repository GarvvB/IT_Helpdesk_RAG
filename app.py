import streamlit as st
from rag import ask_question
import os
from dotenv import load_dotenv

load_dotenv()


print("LangSmith API key loaded:", bool(os.getenv("LANGSMITH_API_KEY")))
print("LangSmith tracing:", os.getenv("LANGSMITH_TRACING"))
print("LangSmith project:", os.getenv("LANGSMITH_PROJECT"))


st.set_page_config(
    page_title="IT Helpdesk Assistant"
)

st.title("IT Helpdesk Assistant")
st.write(
    "Ask questions about company IT policies, procedures, "
    "VPN, passwords, software installation and other IT topics."
)

question = st.text_input("Ask your IT question:")

if st.button("Ask"):
    if question:
        with st.spinner("Searching IT documentation..."):
            answer, sources = ask_question(question)

        st.subheader("Answer")
        st.write(answer)

        st.subheader("Sources")

        for source in sources:
            st.write(f"- {source}")

    else:
        st.warning("Please enter a question.")