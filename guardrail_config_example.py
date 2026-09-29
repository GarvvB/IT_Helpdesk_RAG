"""
Guardrail Configuration Example

Copy and modify this file to customize guardrail behavior for your specific use case.
After modifying, import from this config file instead of using defaults.
"""

# ============================================================================
# KEYWORD LISTS
# ============================================================================

# Add your company-specific IT terms here
CUSTOM_IT_KEYWORDS = [
    # Infrastructure & Cloud
    "aws", "azure", "gcp", "kubernetes", "docker", "terraform",
    
    # Tools & Platforms
    "jira", "confluence", "slack", "teams", "zoom",
    "github", "gitlab", "bitbucket",
    
    # Processes
    "onboarding", "offboarding", "provisioning",
    "incident", "ticket", "request",
    
    # Your specific terms
    # "your_tool", "your_process", "your_platform",
]

# Add terms that should never be processed
CUSTOM_BLOCKED_KEYWORDS = [
    # Company-specific security terms
    # "internal_secret_project", "classified_system",
    
    # Add any other terms you want to block
]

# ============================================================================
# CONFIDENCE THRESHOLDS
# ============================================================================

# Minimum confidence to show answer (0.0 to 1.0)
# Lower = more permissive, Higher = more strict
CONFIDENCE_THRESHOLD_FAIL = 0.5      # Below this = fail (don't show answer)
CONFIDENCE_THRESHOLD_REVIEW = 0.7    # Below this = needs review warning

# Adjust these if you find too many/too few warnings
# Examples:
#   - Too many false warnings? Lower thresholds (0.4, 0.6)
#   - Want stricter quality? Raise thresholds (0.6, 0.8)

# ============================================================================
# PII PATTERNS (Advanced)
# ============================================================================

# Add company-specific PII patterns if needed
# Example: Employee ID format
EMPLOYEE_ID_PATTERN = r"\b(?:EMP|EMPLOYEE)-\d{5}\b"  # EMP-12345

# Example: Internal account number format
INTERNAL_ACCOUNT_PATTERN = r"\bACC-\d{8}\b"  # ACC-12345678

# Example: Badge/access card number
BADGE_NUMBER_PATTERN = r"\b(?:BADGE|CARD)-\d{6}\b"  # BADGE-123456

# To use these patterns, add them to the _contains_pii() function in guardrail.py

# ============================================================================
# RETRIEVAL SETTINGS
# ============================================================================

# Minimum number of documents that should be retrieved
MIN_DOCUMENTS_REQUIRED = 1  # Increase if you want stricter retrieval

# Similarity threshold (if using scored retrieval)
MIN_SIMILARITY_THRESHOLD = 0.3  # 0.0 to 1.0

# ============================================================================
# OUTPUT VALIDATION SETTINGS
# ============================================================================

# Minimum answer length (in characters)
MIN_ANSWER_LENGTH = 10

# Maximum answer length (to detect potential errors)
MAX_ANSWER_LENGTH = 5000

# Words that indicate uncertainty (affects confidence)
UNCERTAINTY_INDICATORS = [
    "might", "maybe", "perhaps", "possibly", "could be",
    "i'm not sure", "unclear", "uncertain", "i don't know",
    "i could not find", "not available", "no information",
]

# ============================================================================
# TOPIC FILTERING SETTINGS
# ============================================================================

# Require at least this many IT keywords to consider question relevant
MIN_IT_KEYWORD_MATCHES = 1  # Increase to 2 for stricter filtering

# Allow questions about these general topics even without IT keywords
ALLOWED_GENERAL_TOPICS = [
    "help", "support", "assistance", "question", "issue", "problem"
]

# ============================================================================
# EXAMPLE: HOW TO USE THIS CONFIG
# ============================================================================

"""
In guardrail.py, at the top, add:

try:
    from guardrail_config import (
        CUSTOM_IT_KEYWORDS,
        CUSTOM_BLOCKED_KEYWORDS,
        CONFIDENCE_THRESHOLD_FAIL,
        CONFIDENCE_THRESHOLD_REVIEW,
    )
    
    # Merge with defaults
    IT_RELATED_KEYWORDS.extend(CUSTOM_IT_KEYWORDS)
    BLOCKED_KEYWORDS.extend(CUSTOM_BLOCKED_KEYWORDS)
    
except ImportError:
    # Use defaults if config file doesn't exist
    pass

Then in your evaluation logic:

if confidence < CONFIDENCE_THRESHOLD_FAIL:
    verdict = "fail"
elif confidence < CONFIDENCE_THRESHOLD_REVIEW:
    verdict = "needs_review"
else:
    verdict = "pass"
"""

# ============================================================================
# MONITORING & LOGGING CONFIG
# ============================================================================

# Log levels for different guardrail events
LOGGING_CONFIG = {
    "input_blocked": "WARNING",        # User input was blocked
    "output_blocked": "ERROR",         # Generated output was blocked
    "low_confidence": "INFO",          # Answer has low confidence
    "pii_detected": "WARNING",         # PII found in input/output
    "off_topic": "INFO",               # Off-topic question attempted
    "security_threat": "ERROR",        # Security-related keyword detected
}

# Whether to log full question text (may contain PII)
LOG_FULL_QUESTIONS = False  # Set to False in production for privacy

# Whether to log generated answers
LOG_ANSWERS = True

# Sample rate for logging (1.0 = log everything, 0.1 = log 10%)
LOGGING_SAMPLE_RATE = 1.0

# ============================================================================
# FEATURE FLAGS
# ============================================================================

# Enable/disable specific guardrails
ENABLE_INPUT_GUARDRAIL = True
ENABLE_RETRIEVAL_GUARDRAIL = True
ENABLE_OUTPUT_GUARDRAIL = True
ENABLE_CONFIDENCE_SCORING = True
ENABLE_ANSWER_EVALUATION = True

# Enable/disable specific checks within input guardrail
CHECK_PII_IN_INPUT = True
CHECK_TOPIC_RELEVANCE = True
CHECK_BLOCKED_KEYWORDS = True
CHECK_GIBBERISH = True

# Enable/disable specific checks within output guardrail
CHECK_PII_IN_OUTPUT = True
CHECK_CREDENTIALS_IN_OUTPUT = True
CHECK_UNSUPPORTED_CLAIMS = True
CHECK_SOURCE_VALIDATION = True

# ============================================================================
# ENVIRONMENT-SPECIFIC SETTINGS
# ============================================================================

import os

# Different settings for different environments
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

if ENVIRONMENT == "production":
    # Production: stricter settings
    CONFIDENCE_THRESHOLD_FAIL = 0.6
    CONFIDENCE_THRESHOLD_REVIEW = 0.75
    MIN_DOCUMENTS_REQUIRED = 2
    LOG_FULL_QUESTIONS = False
    
elif ENVIRONMENT == "development":
    # Development: more permissive for testing
    CONFIDENCE_THRESHOLD_FAIL = 0.4
    CONFIDENCE_THRESHOLD_REVIEW = 0.6
    MIN_DOCUMENTS_REQUIRED = 1
    LOG_FULL_QUESTIONS = True
    
elif ENVIRONMENT == "staging":
    # Staging: balanced settings
    CONFIDENCE_THRESHOLD_FAIL = 0.5
    CONFIDENCE_THRESHOLD_REVIEW = 0.7
    MIN_DOCUMENTS_REQUIRED = 1
    LOG_FULL_QUESTIONS = False

# ============================================================================
# CUSTOMIZATION EXAMPLES
# ============================================================================

# Example 1: Company allows personal emails in questions
ALLOW_COMPANY_EMAIL_DOMAIN = "yourcompany.com"
EMAIL_PATTERN_OVERRIDE = (
    r"\b[A-Za-z0-9._%+-]+@(?!" + ALLOW_COMPANY_EMAIL_DOMAIN + r")[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
)

# Example 2: Specific username formats that ARE allowed (not blocked)
ALLOWED_USERNAME_PATTERNS = [
    r"@[a-zA-Z0-9_-]+",  # Slack-style usernames
    r"#[a-zA-Z0-9_-]+",  # Channel names
]

# Example 3: Department-specific keyword lists
DEPARTMENT_KEYWORDS = {
    "engineering": ["deployment", "build", "ci/cd", "repository", "docker"],
    "hr": ["onboarding", "benefits", "leave", "timesheet"],
    "finance": ["expense", "invoice", "procurement", "budget"],
}

# To use: Combine all department keywords into IT_RELATED_KEYWORDS
ALL_DEPARTMENT_KEYWORDS = [kw for dept_kws in DEPARTMENT_KEYWORDS.values() for kw in dept_kws]

# ============================================================================
# VALIDATION
# ============================================================================

def validate_config():
    """Validate configuration values are sensible."""
    assert 0.0 <= CONFIDENCE_THRESHOLD_FAIL <= 1.0, "Invalid confidence threshold"
    assert 0.0 <= CONFIDENCE_THRESHOLD_REVIEW <= 1.0, "Invalid review threshold"
    assert CONFIDENCE_THRESHOLD_FAIL < CONFIDENCE_THRESHOLD_REVIEW, "Thresholds out of order"
    assert MIN_DOCUMENTS_REQUIRED >= 0, "Invalid minimum documents"
    assert MIN_ANSWER_LENGTH > 0, "Invalid minimum answer length"
    assert 0.0 <= LOGGING_SAMPLE_RATE <= 1.0, "Invalid logging sample rate"
    print("✅ Configuration validation passed")

if __name__ == "__main__":
    validate_config()
    print(f"\nCurrent Environment: {ENVIRONMENT}")
    print(f"Confidence Thresholds: Fail<{CONFIDENCE_THRESHOLD_FAIL}, Review<{CONFIDENCE_THRESHOLD_REVIEW}")
    print(f"Min Documents: {MIN_DOCUMENTS_REQUIRED}")
    print(f"Custom IT Keywords: {len(CUSTOM_IT_KEYWORDS)}")
    print(f"Custom Blocked Keywords: {len(CUSTOM_BLOCKED_KEYWORDS)}")
