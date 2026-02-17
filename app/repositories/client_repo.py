from sqlalchemy.orm import Session
from app.models.client import Client
from app.schema.client import ClientCreate

def get_client_by_id(db: Session, client_id: int) -> Client | None:
    return db.query(Client).filter(Client.id == client_id, Client.is_active == True).first()

def get_clients(
    db: Session,
    search: str | None = None
):
    query = db.query(Client).filter(Client.is_active == True)

    if search:
        query = query.filter(
            Client.name.ilike(f"%{search}%")
        )

    return query.order_by(Client.name).all()

def create_client(db: Session, data: ClientCreate) -> Client:
        client = Client(
        name=data.name,
        phone=data.phone,
        notes= data.notes,
        is_active=True
    )

        db.add(client)
        db.commit()
        db.refresh(client)

        return client

def update_client(db: Session, client: Client) -> Client:
    db.add(client)
    db.commit()
    db.refresh(client)
    return client

def deactivate_client(db: Session, client: Client):
    client.is_active = False
    db.commit()
