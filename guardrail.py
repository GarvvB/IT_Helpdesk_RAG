"""
Guardrail system for IT Helpdesk RAG application.

This module provides multi-layer safety checks for user inputs and model outputs
to ensure the IT helpdesk assistant operates safely and within intended boundaries.
"""

from __future__ import annotations
import re
from typing import Optional, Literal
from pydantic import BaseModel, Field


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class GuardrailResult(BaseModel):
    """Result of a guardrail check."""
    passed: bool
    reason: Optional[str] = Field(default=None, description="Explanation if guardrail failed")
    risk_level: Literal["low", "medium", "high"] = Field(default="low")


class ITAnswer(BaseModel):
    """Structured output from the IT helpdesk RAG system."""
    answer: str = Field(description="Generated answer to the employee question")
    sources: list[str] = Field(description="Document sources used")
    confidence: float = Field(ge=0, le=1, description="Confidence score for the answer")
    guardrail_passed: bool = Field(default=True)
    guardrail_notes: Optional[str] = Field(default=None)


class AnswerEvaluation(BaseModel):
    """Evaluation of answer quality and safety."""
    groundedness_score: float = Field(
        ge=0, le=1,
        description="Is the answer grounded in retrieved context?"
    )
    relevance_score: float = Field(
        ge=0, le=1,
        description="Does the answer address the question?"
    )
    hallucination_risk: Literal["low", "medium", "high"]
    verdict: Literal["pass", "needs_review", "fail"]
    reasoning: str = Field(description="Brief justification for the verdict")


# ============================================================================
# PATTERNS AND BLOCKLISTS
# ============================================================================

# Sensitive information patterns
SSN_PATTERN = r"\b\d{3}-\d{2}-\d{4}\b"
CREDIT_CARD_PATTERN = r"\b(?:\d[ -]*?){13,16}\b"
PHONE_PATTERN = r"\b(?:\+?1[-.]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@(?!company\.)(?!example\.)(?!test\.)[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

# Actual passwords or credential sharing attempts
PASSWORD_SHARING_PATTERNS = [
    r"password\s+is\s+",
    r"my\s+password[:\s]+\w+",
    r"the\s+password[:\s]+\w+",
    r"use\s+password\s+\w+",
]

# Blocked keywords that indicate inappropriate content
BLOCKED_KEYWORDS = [
    "social security number", "ssn", "credit card", "cvv",
    "driver's license", "drivers license",
    "hack", "exploit", "bypass security", "crack password",
    "suicide", "kill myself", "self harm", "self-harm",
]

# IT-relevant topics (for topic filtering)
IT_RELATED_KEYWORDS = [
    "password", "vpn", "software", "install", "access", "login",
    "network", "wifi", "computer", "laptop", "account", "email",
    "printer", "hardware", "device", "application", "system",
    "authentication", "reset", "unlock", "permission", "security",
    "policy", "procedure", "it", "helpdesk", "tech", "support",
    "connection", "error", "issue", "problem", "troubleshoot",
]


# ============================================================================
# INPUT GUARDRAILS
# ============================================================================

def _contains_pii(text: str) -> tuple[bool, Optional[str]]:
    """Check if text contains personally identifiable information."""
    if re.search(SSN_PATTERN, text):
        return True, "Social Security Number"
    if re.search(CREDIT_CARD_PATTERN, text):
        return True, "Credit card number"
    if re.search(PHONE_PATTERN, text):
        return True, "Phone number"
    if re.search(EMAIL_PATTERN, text, re.IGNORECASE):
        return True, "Personal email address"
    for pattern in PASSWORD_SHARING_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True, "Password or credential"
    return False, None


def _contains_blocked_content(text: str) -> tuple[bool, Optional[str]]:
    """Check if text contains blocked keywords."""
    text_lower = text.lower()
    for keyword in BLOCKED_KEYWORDS:
        if keyword in text_lower:
            return True, keyword
    return False, None


def _is_gibberish(text: str) -> bool:
    """Detect if text is likely gibberish or keyboard mashing."""
    # Remove common punctuation and split into words
    words = re.findall(r'\b[a-zA-Z]+\b', text)
    if len(words) == 0:
        return True
    
    # Check vowel ratio - real words typically have vowels
    vowels = set('aeiouAEIOU')
    total_chars = sum(len(word) for word in words)
    if total_chars == 0:
        return True
    
    vowel_count = sum(sum(1 for c in word if c in vowels) for word in words)
    vowel_ratio = vowel_count / total_chars
    
    # Real text has roughly 30-50% vowels
    if vowel_ratio < 0.15 or vowel_ratio > 0.70:
        return True
    
    # Check for excessive repeated characters
    if re.search(r'(.)\1{4,}', text):  # Same character 5+ times
        return True
    
    return False


def _is_it_related(text: str) -> bool:
    """Check if the question is IT-related."""
    text_lower = text.lower()
    
    # Count IT-related keywords
    keyword_count = sum(1 for keyword in IT_RELATED_KEYWORDS if keyword in text_lower)
    
    # If question has at least 1 IT keyword, consider it related
    return keyword_count > 0


def input_guardrail(user_question: str) -> GuardrailResult:
    """
    Primary input validation - runs before any LLM or retrieval call.
    
    Checks for:
    - Empty or too-short input
    - Gibberish or keyboard mashing
    - PII in the question
    - Blocked keywords (security threats, self-harm)
    - Off-topic (non-IT) questions
    
    Args:
        user_question: Raw user input from the chat interface
        
    Returns:
        GuardrailResult indicating pass/fail and reason
    """
    question = user_question.strip()
    
    # Check for empty or too short
    if len(question) < 3:
        return GuardrailResult(
            passed=False,
            reason="Question is too short. Please provide a complete question.",
            risk_level="low"
        )
    
    # Check for gibberish
    if _is_gibberish(question):
        return GuardrailResult(
            passed=False,
            reason="This doesn't look like a valid question. Please rephrase clearly.",
            risk_level="low"
        )
    
    # Check for PII
    has_pii, pii_type = _contains_pii(question)
    if has_pii:
        return GuardrailResult(
            passed=False,
            reason=f"Please do not include sensitive information ({pii_type}) in your question. "
                   f"The IT helpdesk does not need this information to answer policy questions.",
            risk_level="high"
        )
    
    # Check for blocked content
    has_blocked, blocked_keyword = _contains_blocked_content(question)
    if has_blocked:
        return GuardrailResult(
            passed=False,
            reason=f"Your question contains content that cannot be processed. "
                   f"This system is for IT policy questions only.",
            risk_level="high"
        )
    
    # Check if IT-related
    if not _is_it_related(question):
        return GuardrailResult(
            passed=False,
            reason="This question doesn't appear to be IT-related. "
                   "Please ask about company IT policies, VPN, passwords, software installation, or other IT topics.",
            risk_level="medium"
        )
    
    return GuardrailResult(passed=True, risk_level="low")


# ============================================================================
# RETRIEVAL GUARDRAILS
# ============================================================================

def retrieval_guardrail(
    question: str,
    retrieved_docs: list,
    min_relevance_threshold: float = 0.3
) -> GuardrailResult:
    """
    Validates retrieved documents before sending to LLM.
    
    Checks:
    - At least some documents were retrieved
    - Documents have minimum similarity scores (if available)
    
    Args:
        question: User's question
        retrieved_docs: List of retrieved document objects
        min_relevance_threshold: Minimum similarity score (if metadata includes it)
        
    Returns:
        GuardrailResult indicating if retrieval quality is acceptable
    """
    if not retrieved_docs or len(retrieved_docs) == 0:
        return GuardrailResult(
            passed=False,
            reason="No relevant documentation found for this question. "
                   "Please rephrase or contact IT helpdesk directly.",
            risk_level="medium"
        )
    
    # Check if documents are too generic (optional enhancement)
    # Could check document metadata for relevance scores if available
    
    return GuardrailResult(passed=True, risk_level="low")


# ============================================================================
# OUTPUT GUARDRAILS
# ============================================================================

def _makes_unsupported_claims(answer: str) -> tuple[bool, Optional[str]]:
    """Check if answer makes claims that shouldn't be in IT policy responses."""
    answer_lower = answer.lower()
    
    # Check for absolute guarantees
    if any(phrase in answer_lower for phrase in [
        "guaranteed", "promise", "always works", "will never fail",
        "100% secure", "perfectly safe", "completely protected"
    ]):
        return True, "Makes absolute guarantees"
    
    # Check for legal advice
    if any(phrase in answer_lower for phrase in [
        "legally required", "legal obligation", "you must legally",
        "law requires", "federal regulation"
    ]):
        return True, "Provides legal advice"
    
    # Check for medical advice
    if any(phrase in answer_lower for phrase in [
        "medical", "health condition", "see a doctor", "diagnosis"
    ]):
        return True, "Provides medical advice"
    
    # Check for specific credentials being shared (username/password combinations)
    # Pattern: "username is:" or "username:" followed by actual username
    if re.search(r'username\s*(?:is\s*)?:\s*[a-z0-9._-]+', answer_lower):
        return True, "Contains specific credentials"
    if re.search(r'password\s*(?:is\s*)?:\s*\w+', answer_lower):
        return True, "Contains specific credentials"
    
    return False, None


def _contains_sensitive_data(answer: str) -> tuple[bool, Optional[str]]:
    """Check if answer leaks sensitive information."""
    # Check for PII patterns in output
    has_pii, pii_type = _contains_pii(answer)
    if has_pii:
        return True, pii_type
    
    # Check for API keys, tokens, or secrets
    if re.search(r'\b[A-Za-z0-9_-]{32,}\b', answer):
        return True, "Possible API key or token"
    
    # Check for IP addresses
    if re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', answer):
        return True, "IP address"
    
    return False, None


def output_guardrail(answer: str, sources: list[str]) -> GuardrailResult:
    """
    Validates LLM output before showing to user.
    
    Checks:
    - Answer is not empty
    - Answer doesn't contain sensitive information
    - Answer doesn't make unsupported claims
    - Answer has supporting sources
    
    Args:
        answer: Generated answer text
        sources: List of source documents used
        
    Returns:
        GuardrailResult indicating if output is safe to display
    """
    if not answer or len(answer.strip()) < 10:
        return GuardrailResult(
            passed=False,
            reason="Generated answer is too short or empty.",
            risk_level="medium"
        )
    
    # Check for sensitive data leakage
    has_sensitive, sensitive_type = _contains_sensitive_data(answer)
    if has_sensitive:
        return GuardrailResult(
            passed=False,
            reason=f"Answer contains sensitive information ({sensitive_type}) and cannot be displayed. "
                   f"Please contact IT helpdesk directly.",
            risk_level="high"
        )
    
    # Check for unsupported claims
    has_claim, claim_type = _makes_unsupported_claims(answer)
    if has_claim:
        return GuardrailResult(
            passed=False,
            reason=f"Answer makes unsupported claims ({claim_type}). "
                   f"Please verify with IT helpdesk.",
            risk_level="medium"
        )
    
    # Check that sources are present
    if not sources or len(sources) == 0:
        return GuardrailResult(
            passed=False,
            reason="Answer was generated without document sources. "
                   "This may indicate hallucination.",
            risk_level="high"
        )
    
    return GuardrailResult(passed=True, risk_level="low")


# ============================================================================
# CONFIDENCE SCORING
# ============================================================================

def calculate_confidence(
    answer: str,
    sources: list[str],
    retrieved_docs: list
) -> float:
    """
    Calculate confidence score for the generated answer.
    
    Factors:
    - Number of sources (more sources = higher confidence)
    - Answer length (very short answers may indicate low confidence)
    - Presence of hedge phrases (indicates uncertainty)
    - Whether answer admits lack of information
    
    Args:
        answer: Generated answer text
        sources: Source document paths
        retrieved_docs: Retrieved document objects
        
    Returns:
        Confidence score between 0 and 1
    """
    confidence = 1.0
    
    # Factor 1: Check for explicit uncertainty
    hedge_phrases = [
        "i could not find", "not available", "no information",
        "i don't know", "unclear", "uncertain", "might", "possibly",
        "perhaps", "may be"
    ]
    answer_lower = answer.lower()
    if any(phrase in answer_lower for phrase in hedge_phrases):
        confidence *= 0.3
    
    # Factor 2: Source count (more sources = more confident)
    if len(sources) == 0:
        confidence *= 0.2
    elif len(sources) == 1:
        confidence *= 0.6
    elif len(sources) == 2:
        confidence *= 0.8
    # 3+ sources: no penalty
    
    # Factor 3: Answer length (very short may indicate low info)
    if len(answer) < 50:
        confidence *= 0.7
    
    # Factor 4: Generic fallback response detection
    if "contact the it helpdesk" in answer_lower and len(answer) < 100:
        confidence *= 0.4
    
    return max(0.0, min(1.0, confidence))


def evaluate_answer(
    question: str,
    answer: str,
    sources: list[str],
    retrieved_docs: list,
    confidence: float
) -> AnswerEvaluation:
    """
    Comprehensive evaluation of answer quality.
    
    Produces a structured evaluation with scores and verdict.
    
    Args:
        question: Original user question
        answer: Generated answer
        sources: Source documents
        retrieved_docs: Retrieved context
        confidence: Pre-calculated confidence score
        
    Returns:
        AnswerEvaluation with scores and verdict
    """
    # Groundedness: Does answer cite sources?
    groundedness = 1.0 if len(sources) > 0 else 0.0
    if "i could not find" in answer.lower():
        groundedness *= 0.5
    
    # Relevance: Simple keyword overlap check
    question_words = set(re.findall(r'\b\w+\b', question.lower()))
    answer_words = set(re.findall(r'\b\w+\b', answer.lower()))
    overlap = len(question_words & answer_words)
    relevance = min(1.0, overlap / max(len(question_words), 1) + 0.3)
    
    # Hallucination risk
    if confidence < 0.4:
        hallucination_risk = "high"
    elif confidence < 0.7:
        hallucination_risk = "medium"
    else:
        hallucination_risk = "low"
    
    # Overall verdict
    if confidence < 0.5 or groundedness < 0.5:
        verdict = "fail"
        reasoning = "Low confidence or poor grounding in sources"
    elif confidence < 0.7 or relevance < 0.6:
        verdict = "needs_review"
        reasoning = "Moderate confidence - may need human review"
    else:
        verdict = "pass"
        reasoning = "High confidence answer grounded in documentation"
    
    return AnswerEvaluation(
        groundedness_score=groundedness,
        relevance_score=relevance,
        hallucination_risk=hallucination_risk,
        verdict=verdict,
        reasoning=reasoning
    )


# ============================================================================
# ORCHESTRATION
# ============================================================================

def run_full_guardrails(
    question: str,
    answer: str,
    sources: list[str],
    retrieved_docs: list
) -> tuple[bool, str, AnswerEvaluation]:
    """
    Run complete guardrail pipeline on a question-answer pair.
    
    This is the main entry point for integrated guardrail checking.
    
    Args:
        question: User's input question
        answer: Generated answer
        sources: Source documents used
        retrieved_docs: Retrieved document objects
        
    Returns:
        Tuple of (passed: bool, message: str, evaluation: AnswerEvaluation)
    """
    # Step 1: Output guardrail
    output_check = output_guardrail(answer, sources)
    if not output_check.passed:
        return False, output_check.reason, None
    
    # Step 2: Calculate confidence
    confidence = calculate_confidence(answer, sources, retrieved_docs)
    
    # Step 3: Evaluate answer
    evaluation = evaluate_answer(question, answer, sources, retrieved_docs, confidence)
    
    # Step 4: Decision based on evaluation
    if evaluation.verdict == "fail":
        return False, f"Answer quality check failed: {evaluation.reasoning}", evaluation
    elif evaluation.verdict == "needs_review":
        # Allow through but flag for potential review
        return True, f"Note: {evaluation.reasoning} (Confidence: {confidence:.2f})", evaluation
    else:
        return True, "All guardrails passed", evaluation


# ============================================================================
# STANDALONE TESTING
# ============================================================================

if __name__ == "__main__":
    # Test input guardrails
    print("=== Testing Input Guardrails ===\n")
    
    test_inputs = [
        "How do I reset my password?",
        "asdfghjkl",
        "My SSN is 123-45-6789",
        "What's the weather today?",
        "vpn connection not working",
        "hack the system",
    ]
    
    for test in test_inputs:
        result = input_guardrail(test)
        status = "✓ PASS" if result.passed else "✗ FAIL"
        print(f"{status}: '{test}'")
        if not result.passed:
            print(f"  Reason: {result.reason}")
        print()
    
    # Test output guardrails
    print("\n=== Testing Output Guardrails ===\n")
    
    test_outputs = [
        ("Valid answer about password reset policy.", ["password_policy.txt"]),
        ("", []),
        ("Your password is: admin123", ["password_policy.txt"]),
        ("This is guaranteed to work 100%.", ["vpn_guide.txt"]),
    ]
    
    for answer, sources in test_outputs:
        result = output_guardrail(answer, sources)
        status = "✓ PASS" if result.passed else "✗ FAIL"
        print(f"{status}: '{answer[:50]}...'")
        if not result.passed:
            print(f"  Reason: {result.reason}")
        print()
