from sqlalchemy.orm import Session
from app.models.user import User

def get_user_by_id (db: Session, user_id: int) -> User | None:
        return db.query(User).filter(User.id == user_id).first()

def get_active_user_by_id(db: Session, user_id: int):
            return (
        db.query(User)
        .filter(
            User.id == user_id,
            User.is_active == True
        )
        .first()
    )


def get_user_by_email (db: Session, email) -> User | None:
        return db.query(User).filter(User.email == email, User.is_active == True).first()

def create_user(db: Session, user:User) -> User:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
def get_all_users(db: Session):
        return db.query(User).filter(User.is_active == True).all()

def update_user(db: Session, user: User) -> User:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

def deactivate_user(db:Session, user: User):
        user.is_active = False
        db.commit()
        