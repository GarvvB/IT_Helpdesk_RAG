import streamlit as st
from rag import ask_question, ask_question_with_details
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

# Add a sidebar with guardrail info
with st.sidebar:
    st.header("Safety Features")
    st.write(
        "This assistant uses multiple guardrails to ensure safe and accurate responses:"
    )
    st.write("- Input validation")
    st.write("- PII detection")
    st.write("- Topic relevance filtering")
    st.write("- Output safety checks")
    st.write("- Confidence scoring")
    
    show_details = st.checkbox("Show detailed analysis", value=False)

st.write("---")

question = st.text_input("Ask your IT question:", placeholder="e.g., How do I reset my password?")

if st.button("Ask", type="primary"):
    if question:
        with st.spinner("Searching IT documentation..."):
            if show_details:
                # Use detailed version for debugging
                result = ask_question_with_details(question)
                
                st.subheader("Answer")
                st.write(result["answer"])
                
                if result["sources"]:
                    st.subheader("Sources")
                    for source in result["sources"]:
                        st.write(f"- {source}")
                
                # Show detailed analysis
                with st.expander("Detailed Analysis"):
                    st.write("**Confidence Score:**", f"{result['confidence']:.0%}")
                    
                    if result["evaluation"]:
                        st.write("**Evaluation:**")
                        st.write(f"- Groundedness: {result['evaluation'].groundedness_score:.0%}")
                        st.write(f"- Relevance: {result['evaluation'].relevance_score:.0%}")
                        st.write(f"- Hallucination Risk: {result['evaluation'].hallucination_risk}")
                        st.write(f"- Verdict: {result['evaluation'].verdict}")
                        st.write(f"- Reasoning: {result['evaluation'].reasoning}")
                    
                    st.write("**Guardrail Checks:**")
                    for check_name, check_result in result["guardrail_checks"].items():
                        if check_result:
                            status = "PASSED" if check_result.passed else "FAILED"
                            st.write(f"- {check_name.title()}: {status}")
                            if not check_result.passed:
                                st.write(f"  Reason: {check_result.reason}")
            else:
                # Standard user-friendly version
                answer, sources = ask_question(question)

                st.subheader("Answer")
                st.write(answer)

                if sources:
                    st.subheader("Sources")
                    for source in sources:
                        st.write(f"- {source}")

    else:
        st.warning("Please enter a question.")

# Footer
st.write("---")
st.caption("Note: This assistant only answers based on company IT documentation. For urgent issues, contact IT Helpdesk directly.")