from __future__ import annotations

SENSITIVE_KEYWORDS = [
    "harass", "discrimination", "bullying", "retaliation", "pay dispute",
    "salary dispute", "legal complaint", "workplace complaint", "medical condition",
    "disability accommodation", "pregnancy", "personal medical",
]

KEYWORDS = {
    "IT": ["laptop", "password", "vpn", "it setup", "email", "software", "device"],
    "Finance": ["expense", "reimbursement", "receipt", "invoice", "travel cost"],
    "Facilities": ["office", "parking", "desk", "building", "facilities", "meeting room"],
    "HR": ["leave", "holiday", "parental", "attendance", "onboarding", "benefits"],
}

ESCALATION_MESSAGE = (
    "This question requires human HR assistance. Please contact the HR Conduct Team "
    "(hr-conduct@northwindretail.example)."
)

def is_sensitive(question: str) -> bool:
    text = question.lower()
    return any(keyword in text for keyword in SENSITIVE_KEYWORDS)

def classify(question: str) -> str:
    if is_sensitive(question):
        return "Sensitive"
    text = question.lower()
    for department, words in KEYWORDS.items():
        if any(word in text for word in words):
            return department
    return "General"
