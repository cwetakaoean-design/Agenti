"""CRUD for agency clients."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Client, ClientCreate

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.post("", response_model=Client, status_code=201)
def create_client(payload: ClientCreate, session: Session = Depends(get_session)) -> Client:
    client = Client(**payload.model_dump())
    session.add(client)
    session.commit()
    session.refresh(client)
    return client


@router.get("", response_model=list[Client])
def list_clients(session: Session = Depends(get_session)) -> list[Client]:
    return list(session.exec(select(Client).order_by(Client.id.desc())).all())


@router.get("/{client_id}", response_model=Client)
def get_client(client_id: int, session: Session = Depends(get_session)) -> Client:
    client = session.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client
