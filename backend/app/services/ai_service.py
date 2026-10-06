import json
import os
from urllib.error import URLError
from urllib.request import Request, urlopen


KEYWORDS = {
    "Network": {"vpn", "wifi", "internet", "network", "dns", "proxy", "lan"},
    "Hardware": {"laptop", "keyboard", "mouse", "screen", "monitor", "printer", "battery"},
    "Access": {"password", "login", "access", "permission", "account", "locked"},
    "Software": {"install", "software", "application", "app", "crash", "update"},
}

TROUBLESHOOTING = {
    "Network": ["Check DNS and proxy settings", "Restart the network adapter", "Confirm VPN gateway availability"],
    "Hardware": ["Check power and cable connections", "Restart the device", "Capture an error light or screen message"],
    "Access": ["Confirm the account is not locked", "Try the password reset flow", "Verify the requested permission with the manager"],
    "Software": ["Capture the exact error message", "Restart and retry the application", "Check whether the latest approved version is installed"],
    "Other": ["Add the exact steps that reproduce the issue", "Include screenshots or error messages", "Mention when the issue first started"],
}


def _rule_suggestion(title: str, description: str, requested_priority: str | None = None) -> dict:
    text = f"{title} {description}".lower()
    scores = {category: sum(word in text for word in words) for category, words in KEYWORDS.items()}
    category = max(scores, key=scores.get) if max(scores.values(), default=0) else "Other"
    priority = requested_priority if requested_priority in {"low", "medium", "high", "critical"} else "medium"
    if any(word in text for word in {"down", "breach", "all users", "urgent", "blocked"}):
        priority = "high" if priority == "medium" else priority
    if any(word in text for word in {"outage", "production", "everyone", "security"}):
        priority = "critical"
    return {
        "category": category,
        "priority": priority,
        "confidence": round(min(0.55 + scores.get(category, 0) * 0.12, 0.96), 2),
        "troubleshooting": TROUBLESHOOTING[category],
        "disclaimer": "Rule-based suggestion only. An engineer must confirm the final category and priority.",
    }


def _gemini_suggestion(title: str, description: str, fallback: dict) -> dict | None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    model = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")
    prompt = (
        "Classify this IT support ticket. Return JSON only with keys category, priority, "
        "confidence, troubleshooting. Category: Network, Hardware, Access, Software, "
        "or Other. Priority: low, medium, high, or critical. Give safe diagnostic steps. "
        f"Title: {title}. Description: {description}."
    )
    request = Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
        data=json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"},
        }).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode())
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(text.replace("```json", "").replace("```", "").strip())
        if parsed.get("category") not in TROUBLESHOOTING or parsed.get("priority") not in {"low", "medium", "high", "critical"}:
            return None
        steps = parsed.get("troubleshooting")
        if not isinstance(steps, list) or not steps:
            return None
        return {
            "category": parsed["category"],
            "priority": parsed["priority"],
            "confidence": float(parsed.get("confidence", fallback["confidence"])),
            "troubleshooting": [str(step) for step in steps[:5]],
            "disclaimer": "Gemini suggestion only. An engineer must confirm the final category and priority.",
        }
    except (KeyError, TypeError, ValueError, URLError, TimeoutError, OSError):
        return None


def suggest_issue(title: str, description: str, requested_priority: str | None = None) -> dict:
    fallback = _rule_suggestion(title, description, requested_priority)
    return _gemini_suggestion(title, description, fallback) or fallback