from sqlalchemy.orm import Session

from app.models.branch_settings import BranchSettings


def get_branch_settings(db: Session, branch_id: int) -> BranchSettings | None:
    return db.query(BranchSettings).filter(BranchSettings.branch_id == branch_id).first()


def save_branch_settings(db: Session, settings: BranchSettings) -> BranchSettings:
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings
