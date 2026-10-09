"""FastAPI REST API. Run with:  uvicorn app.main:app --reload
Interactive docs are served at http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app import service
from app.lifecycle import InvalidTransition

app = FastAPI(title="AI Ticket Automation API", version="1.0.0")


class TicketIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=5)


class TransitionIn(BaseModel):
    status: str
    note: str = ""


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/tickets", status_code=201)
def create_ticket(body: TicketIn):
    return service.create_ticket(body.title, body.description)


@app.get("/tickets")
def list_tickets(status: str | None = Query(None), category: str | None = Query(None)):
    return service.list_tickets(status, category)


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: int):
    try:
        return service.get_ticket(ticket_id)
    except service.TicketNotFound as exc:
        raise HTTPException(404, str(exc))


@app.post("/tickets/{ticket_id}/transition")
def transition(ticket_id: int, body: TransitionIn):
    try:
        return service.transition(ticket_id, body.status.upper(), body.note)
    except service.TicketNotFound as exc:
        raise HTTPException(404, str(exc))
    except InvalidTransition as exc:
        raise HTTPException(409, str(exc))


@app.get("/tickets/{ticket_id}/history")
def ticket_history(ticket_id: int):
    try:
        return service.history(ticket_id)
    except service.TicketNotFound as exc:
        raise HTTPException(404, str(exc))


@app.get("/stats")
def stats():
    return service.stats()
