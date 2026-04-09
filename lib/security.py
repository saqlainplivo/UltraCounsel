"""
lib/security.py
Phone number hashing and prompt injection detection for UltraCounsel.
"""

import hashlib
import os
import re
from typing import Optional


# ─── Phone Number Security ──────────────────────────────────────────────────

def hash_phone_number(phone: str) -> str:
    """
    One-way SHA-256 hash of a phone number using SALT from env.
    The raw number is NEVER stored in the database.
    """
    salt = os.getenv("SECRET_HASH_SALT", "apex-default-salt-change-in-prod")
    combined = f"{salt}:{phone}"
    return hashlib.sha256(combined.encode()).hexdigest()


def mask_phone(phone: str) -> str:
    """Return a masked version for safe logging: +91XXXXX6789."""
    if len(phone) <= 4:
        return "XXXXXXX"
    return phone[:3] + "X" * (len(phone) - 7) + phone[-4:]


# ─── Prompt Injection Detection ─────────────────────────────────────────────

_INJECTION_PATTERNS = [
    r"ignore (previous|all|above|prior) instructions",
    r"disregard (your|the) (system |)prompt",
    r"you are now",
    r"pretend (to be|you are|you're)",
    r"act as (a |an |)(different|new|another|unrestricted|jailbreak)",
    r"forget (everything|your training|your instructions)",
    r"(reveal|show|print|output|display) (your |the )?(system prompt|instructions|prompt)",
    r"developer mode",
    r"jailbreak",
    r"do anything now",
    r"bypass (your |)(safety|restrictions|guidelines|filters)",
    r"override (your |)(instructions|prompt|training)",
]

_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]


def is_prompt_injection(text: str) -> bool:
    """Return True if the text appears to be a prompt injection attempt."""
    return any(p.search(text) for p in _COMPILED_PATTERNS)


# ─── Query Classification ────────────────────────────────────────────────────

_QUERY_CATEGORIES = {
    "prompt_injection": _INJECTION_PATTERNS,
    "fee_question": [
        r"\bfee\b", r"\bcost\b", r"\bprice\b", r"\brupee", r"\bhow much\b",
        r"\bpayment\b", r"\binstallment\b",
    ],
    "scholarship_question": [
        r"\bscholarship\b", r"\bdiscount\b", r"\bconcession\b",
        r"\bfinancial (aid|support|help)\b", r"\bwaiver\b",
    ],
    "batch_question": [
        r"\bbatch\b", r"\btiming\b", r"\bschedule\b", r"\bseat\b",
        r"\bavailable\b", r"\bmorning\b", r"\bevening\b", r"\bweekend\b",
    ],
    "course_question": [
        r"\bcourse\b", r"\bsyllabus\b", r"\bclass\b", r"\bjee\b",
        r"\bneet\b", r"\bcbse\b", r"\bicse\b", r"\bfoundation\b",
    ],
    "demo_question": [
        r"\bdemo\b", r"\btrial\b", r"\bfree class\b", r"\bsample (class|lecture)\b",
    ],
    "angry": [
        r"\b(terrible|horrible|useless|fraud|scam|cheated|refund|complaint)\b",
        r"\bwaste (of )?money\b",
    ],
    "normal": [],
}


def classify_query_type(text: str) -> str:
    """Classify a user query into one of the defined categories."""
    for category, patterns in _QUERY_CATEGORIES.items():
        if category == "normal":
            continue
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return category
    return "normal"
