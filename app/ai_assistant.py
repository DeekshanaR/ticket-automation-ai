"""AI component 2: resolution suggestions.

If ANTHROPIC_API_KEY is set, a Claude model drafts the suggestion.
Otherwise (or on any error) a built-in knowledge base is used, so the
project always works offline and in CI without secrets.
"""
import logging
import os

from app.config import ANTHROPIC_MODEL

log = logging.getLogger(__name__)

KNOWLEDGE_BASE = {
    "Network": "Check cable/Wi-Fi connection, restart the adapter, run ping/traceroute to the gateway, then escalate to the network team if multiple users are affected.",
    "Access": "Verify the user identity, check account lock/expiry status in the directory, reset the password or update group membership as per the access policy.",
    "Hardware": "Run basic hardware diagnostics, check cables and power, and arrange a replacement device if diagnostics fail.",
    "Software": "Collect application logs and version, try a repair or clean reinstall, and check for known issues in the latest release notes.",
    "Email": "Check mailbox quota and sync status, rebuild the mail profile, and review the mail flow logs for delivery failures.",
    "Security": "Isolate the affected system, preserve logs, reset exposed credentials and notify the security team immediately.",
}


def _fallback(category: str) -> str:
    return KNOWLEDGE_BASE.get(category, "Collect more details from the requester and triage manually.")


def suggest_resolution(title: str, description: str, category: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback(category)
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": (
                    "You are an IT service-desk assistant. Give 3 short, numbered "
                    f"troubleshooting steps for this {category} ticket.\n"
                    f"Title: {title}\nDescription: {description}"
                ),
            }],
        )
        return msg.content[0].text.strip()
    except Exception as exc:  # network, auth, quota... never break ticket creation
        log.warning("LLM call failed (%s); using knowledge base.", exc)
        return _fallback(category)
