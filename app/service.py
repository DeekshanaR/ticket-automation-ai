"""Business logic shared by the REST API and the batch runner."""
import logging

from app import ai_assistant
from app.classifier import get_classifier
from app.config import ASSIGNMENT_RULES, CONFIDENCE_THRESHOLD
from app.database import get_conn
from app.lifecycle import validate_transition

log = logging.getLogger(__name__)


class TicketNotFound(LookupError):
    pass


def _record(conn, ticket_id, from_status, to_status, note):
    conn.execute(
        "INSERT INTO ticket_history (ticket_id, from_status, to_status, note) VALUES (?,?,?,?)",
        (ticket_id, from_status, to_status, note),
    )


def get_ticket(ticket_id: int) -> dict:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if not row:
        raise TicketNotFound(f"Ticket {ticket_id} not found")
    return dict(row)


def list_tickets(status: str | None = None, category: str | None = None) -> list[dict]:
    query, params = "SELECT * FROM tickets WHERE 1=1", []
    if status:
        query += " AND status = ?"
        params.append(status)
    if category:
        query += " AND category = ?"
        params.append(category)
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(query + " ORDER BY id DESC", params)]


def history(ticket_id: int) -> list[dict]:
    get_ticket(ticket_id)
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM ticket_history WHERE ticket_id = ? ORDER BY id", (ticket_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def transition(ticket_id: int, new_status: str, note: str = "") -> dict:
    ticket = get_ticket(ticket_id)
    validate_transition(ticket["status"], new_status)
    with get_conn() as conn:
        conn.execute(
            "UPDATE tickets SET status = ?, updated_at = datetime('now') WHERE id = ?",
            (new_status, ticket_id),
        )
        _record(conn, ticket_id, ticket["status"], new_status, note)
    return get_ticket(ticket_id)


def create_ticket(title: str, description: str) -> dict:
    """Create a ticket, classify it with AI, triage and auto-assign it."""
    prediction = get_classifier().predict(title, description)
    needs_review = prediction["confidence"] < CONFIDENCE_THRESHOLD
    suggestion = ai_assistant.suggest_resolution(title, description, prediction["category"])

    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO tickets (title, description, category, priority, confidence,
                                    needs_review, ai_suggestion)
               VALUES (?,?,?,?,?,?,?)""",
            (title, description, prediction["category"], prediction["priority"],
             prediction["confidence"], int(needs_review), suggestion),
        )
        ticket_id = cur.lastrowid
        _record(conn, ticket_id, None, "NEW", "Ticket created")
    transition(ticket_id, "TRIAGED",
               f"AI classified as {prediction['category']} ({prediction['confidence']:.0%} confidence)")
    if needs_review:
        log.warning("Ticket %s has low confidence; left in TRIAGED for manual review", ticket_id)
        return get_ticket(ticket_id)

    team = ASSIGNMENT_RULES.get(prediction["category"], "service-desk")
    with get_conn() as conn:
        conn.execute("UPDATE tickets SET assignee = ? WHERE id = ?", (team, ticket_id))
    return transition(ticket_id, "ASSIGNED", f"Auto-assigned to {team}")


def stats() -> dict:
    with get_conn() as conn:
        by_status = conn.execute("SELECT status, COUNT(*) FROM tickets GROUP BY status").fetchall()
        by_cat = conn.execute("SELECT category, COUNT(*) FROM tickets GROUP BY category").fetchall()
        by_pri = conn.execute("SELECT priority, COUNT(*) FROM tickets GROUP BY priority").fetchall()
        review = conn.execute("SELECT COUNT(*) FROM tickets WHERE needs_review = 1").fetchone()[0]
    return {
        "by_status": {r[0]: r[1] for r in by_status},
        "by_category": {r[0]: r[1] for r in by_cat},
        "by_priority": {r[0]: r[1] for r in by_pri},
        "needs_manual_review": review,
    }
