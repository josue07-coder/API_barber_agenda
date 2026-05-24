from sqlalchemy.orm import Session
from app.models.service import Service

def get_service_by_id(db: Session, service_id: int) -> Service | None:
    return db.query(Service).filter(Service.id == service_id).first()

def get_active_service_by_id(db: Session, service_id: int) -> Service | None:
    return db.query(Service).filter(
        Service.id == service_id,
        Service.is_active == True
    ).first()

def get_services(db: Session, search: str | None = None, branch_id: int | None = None):
    query = db.query(Service).filter(Service.is_active == True)

    if search:
        query = query.filter(Service.name.ilike(f"%{search}%"))

    if branch_id is not None:
        query = query.filter(Service.branch_id == branch_id)

    return query.order_by(Service.name).all()

def create_service(db: Session, service: Service) -> Service:
    db.add(service)
    db.commit()
    db.refresh(service)
    return service

def update_service(db: Session, service: Service) -> Service:
    db.add(service)
    db.commit()
    db.refresh(service)
    return service

def deactivate_service(db: Session, service: Service) -> Service:
    service.is_active = False
    db.commit()
    db.refresh(service)
    return service
