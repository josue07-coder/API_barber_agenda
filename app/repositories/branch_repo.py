from sqlalchemy.orm import Session

from app.models.branch import Branch


def get_branch_by_id(db: Session, branch_id: int) -> Branch | None:
    return db.query(Branch).filter(Branch.id == branch_id).first()


def get_active_branch_by_id(db: Session, branch_id: int) -> Branch | None:
    return (
        db.query(Branch)
        .filter(Branch.id == branch_id, Branch.is_active == True)
        .first()
    )


def get_branch_by_name(db: Session, name: str) -> Branch | None:
    return db.query(Branch).filter(Branch.name == name).first()


def get_branches(db: Session, search: str | None = None) -> list[Branch]:
    query = db.query(Branch).filter(Branch.is_active == True)
    if search:
        query = query.filter(Branch.name.ilike(f"%{search}%"))
    return query.order_by(Branch.name).all()


def create_branch(db: Session, branch: Branch) -> Branch:
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


def update_branch(db: Session, branch: Branch) -> Branch:
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch
