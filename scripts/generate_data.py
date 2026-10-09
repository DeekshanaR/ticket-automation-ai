"""Generate a synthetic IT-ticket dataset (no real/company data is used).

Usage:  python -m scripts.generate_data
"""
import csv
import random
from pathlib import Path

from app.config import DATA_PATH

# category -> list of (symptom, details)
TEMPLATES = {
    "Network": [
        ("VPN not connecting", "VPN client shows timeout error when connecting from home"),
        ("Wi-Fi keeps dropping", "Wireless connection disconnects every few minutes in meeting room"),
        ("No internet access", "Cannot browse any website, ping to gateway fails"),
        ("Slow network speed", "File downloads and shared drive are extremely slow since morning"),
        ("Cannot reach intranet portal", "DNS resolution fails for internal sites, external sites work"),
        ("Network outage in building", "Entire floor lost connectivity, switch lights are off"),
    ],
    "Access": [
        ("Password reset needed", "I forgot my password and the self service portal is not accepting my answers"),
        ("Account locked", "My account got locked after several failed login attempts"),
        ("Need access to shared folder", "Please add me to the finance shared drive group, approved by manager"),
        ("Active Directory group request", "Require membership in the project AD group for new joiner"),
        ("Unable to login to application", "Login says user not authorized although I had access yesterday"),
        ("MFA token not working", "Authenticator codes are rejected during sign in"),
    ],
    "Hardware": [
        ("Laptop will not power on", "Laptop does not turn on even when charger is connected"),
        ("Monitor flickering", "External monitor flickers and goes black randomly"),
        ("Keyboard keys not working", "Several keys on my laptop keyboard stopped responding"),
        ("Printer not printing", "Office printer shows offline and jobs are stuck in queue"),
        ("Battery drains quickly", "Laptop battery lasts only twenty minutes after full charge"),
        ("Broken laptop screen", "Screen is cracked after the device fell from the desk"),
    ],
    "Software": [
        ("Application crashes on startup", "The reporting application closes immediately after opening"),
        ("Need software installation", "Please install the latest version of the design tool on my machine"),
        ("Excel freezing", "Spreadsheet application hangs when opening large workbook"),
        ("Error code during update", "Software update fails with error code 0x80070005"),
        ("Browser extension issue", "Web application page does not load properly in the browser"),
        ("License expired message", "Application shows license expired banner and is read only"),
    ],
    "Email": [
        ("Cannot send emails", "Outlook shows stuck in outbox and messages are not delivered"),
        ("Mailbox full", "Received a warning that my mailbox quota is exceeded"),
        ("Not receiving external emails", "Emails from customers are not arriving in my inbox"),
        ("Calendar not syncing", "Meeting invites are missing from the calendar on my phone"),
        ("Shared mailbox access", "Need access to the support shared mailbox with send as rights"),
        ("Outlook keeps asking for password", "Credential prompt appears repeatedly in the mail client"),
    ],
    "Security": [
        ("Suspicious phishing email", "Received an email asking to verify credentials through a link"),
        ("Possible malware infection", "Antivirus flagged a trojan and the laptop is behaving strangely"),
        ("Unauthorized login attempt", "Alert shows sign in from an unknown country on my account"),
        ("Lost company laptop", "Laptop was stolen from my car, contains confidential data"),
        ("Data leak suspected", "Sensitive document was shared with an external address by mistake"),
        ("Ransomware message on screen", "Files are encrypted and a ransom note appeared on the desktop"),
    ],
}

HIGH_WORDS = ["outage", "ransomware", "stolen", "leak", "malware", "entire", "not power", "unauthorized", "cannot send"]
LOW_WORDS = ["install", "slow", "flicker", "calendar", "extension", "latest version", "quota", "shared folder", "group"]
PREFIX = ["", "Hi team, ", "Urgent help: ", "Hello, ", "Please assist. ", "Request: "]
SUFFIX = ["", " Please help.", " Thanks in advance.", " This started today.", " Happening since yesterday.", " Need a fix soon."]


def _priority(text: str, rng: random.Random) -> str:
    t = text.lower()
    if any(w in t for w in HIGH_WORDS):
        label = "High"
    elif any(w in t for w in LOW_WORDS):
        label = "Low"
    else:
        label = "Medium"
    if rng.random() < 0.05:  # a little label noise, like real data
        label = rng.choice(["Low", "Medium", "High"])
    return label


def generate(path: Path = DATA_PATH, n: int = 600, seed: int = 42) -> Path:
    rng = random.Random(seed)
    rows = []
    for _ in range(n):
        category = rng.choice(list(TEMPLATES))
        title, desc = rng.choice(TEMPLATES[category])
        full_desc = rng.choice(PREFIX) + desc + rng.choice(SUFFIX)
        rows.append({
            "title": title,
            "description": full_desc,
            "category": category,
            "priority": _priority(title + " " + desc, rng),
        })
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "description", "category", "priority"])
        writer.writeheader()
        writer.writerows(rows)
    return path


if __name__ == "__main__":
    print(f"Wrote {generate()}")
