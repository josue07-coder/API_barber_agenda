from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.branch import Branch
from app.models.branch_settings import BranchSettings
from app.repositories.branch_repo import (
    create_branch,
    get_active_branch_by_id,
    get_branch_by_id,
    get_branch_by_name,
    get_branches,
    update_branch,
)
from app.repositories.branch_settings_repo import (
    get_branch_settings,
    save_branch_settings,
)
from app.schema.branch import BranchCreate, BranchUpdate
from app.schema.branch_settings import BranchSettingsUpdate
from app.core.config import settings as global_settings


def create_new_branch(db: Session, data: BranchCreate) -> Branch:
    if get_branch_by_name(db, data.name):
        raise HTTPException(409, "Sucursal ya existe")

    try:
        return create_branch(
            db,
            Branch(
                name=data.name,
                address=data.address,
                phone=data.phone,
                is_active=True,
            ),
        )
    except IntegrityError:
        raise HTTPException(409, "Sucursal ya existe")


def list_branches(db: Session, search: str | None = None) -> list[Branch]:
    return get_branches(db, search)


def get_branch_or_404(db: Session, branch_id: int) -> Branch:
    branch = get_branch_by_id(db, branch_id)
    if not branch:
        raise HTTPException(404, "Sucursal no encontrada")
    return branch


def get_active_branch_or_404(db: Session, branch_id: int) -> Branch:
    branch = get_active_branch_by_id(db, branch_id)
    if not branch:
        raise HTTPException(404, "Sucursal no encontrada")
    return branch


def update_existing_branch(db: Session, branch_id: int, data: BranchUpdate) -> Branch:
    branch = get_branch_or_404(db, branch_id)

    if data.name is not None and data.name != branch.name:
        if get_branch_by_name(db, data.name):
            raise HTTPException(409, "Sucursal ya existe")
        branch.name = data.name

    if data.address is not None:
        branch.address = data.address

    if data.phone is not None:
        branch.phone = data.phone

    if data.is_active is not None:
        branch.is_active = data.is_active

    try:
        return update_branch(db, branch)
    except IntegrityError:
        raise HTTPException(409, "Sucursal ya existe")


def deactivate_branch(db: Session, branch_id: int) -> Branch:
    branch = get_branch_or_404(db, branch_id)
    branch.is_active = False
    return update_branch(db, branch)


def default_branch_settings(branch_id: int) -> BranchSettings:
    return BranchSettings(
        branch_id=branch_id,
        timezone="America/Santo_Domingo",
        currency="DOP",
        default_cancel_cutoff_hours=global_settings.CLIENT_CANCEL_CUTOFF_HOURS,
        default_reschedule_cutoff_hours=global_settings.CLIENT_RESCHEDULE_CUTOFF_HOURS,
        deposit_required=False,
        default_deposit_amount=None,
        default_deposit_percentage=None,
        reminder_24h_enabled=True,
        reminder_2h_enabled=True,
        no_show_penalty_points=global_settings.CLIENT_NO_SHOW_PENALTY_POINTS,
        no_show_penalty_amount=(
            global_settings.CLIENT_NO_SHOW_PENALTY_AMOUNT
            if global_settings.CLIENT_NO_SHOW_PENALTY_AMOUNT > 0
            else None
        ),
        late_cancel_penalty_points=global_settings.CLIENT_LATE_CANCEL_PENALTY_POINTS,
        late_cancel_penalty_amount=(
            global_settings.CLIENT_LATE_CANCEL_PENALTY_AMOUNT
            if global_settings.CLIENT_LATE_CANCEL_PENALTY_AMOUNT > 0
            else None
        ),
    )


def get_or_create_branch_settings(db: Session, branch_id: int) -> BranchSettings:
    get_active_branch_or_404(db, branch_id)
    existing = get_branch_settings(db, branch_id)
    if existing:
        return existing
    return save_branch_settings(db, default_branch_settings(branch_id))


def can_read_branch_settings(current_user, branch_id: int) -> bool:
    if current_user.role == "admin":
        return True
    return current_user.role == "barber" and current_user.branch_id == branch_id


def get_settings_for_user(db: Session, branch_id: int, current_user) -> BranchSettings:
    if not can_read_branch_settings(current_user, branch_id):
        raise HTTPException(403, "No tienes permiso")
    return get_or_create_branch_settings(db, branch_id)


def update_branch_settings(
    db: Session,
    branch_id: int,
    data: BranchSettingsUpdate,
    current_user,
) -> BranchSettings:
    if current_user.role != "admin":
        raise HTTPException(403, "No tienes permiso")

    settings = get_or_create_branch_settings(db, branch_id)
    settings.timezone = data.timezone
    settings.currency = data.currency.upper()
    settings.default_cancel_cutoff_hours = data.default_cancel_cutoff_hours
    settings.default_reschedule_cutoff_hours = data.default_reschedule_cutoff_hours
    settings.deposit_required = data.deposit_required
    settings.default_deposit_amount = data.default_deposit_amount
    settings.default_deposit_percentage = data.default_deposit_percentage
    settings.reminder_24h_enabled = data.reminder_24h_enabled
    settings.reminder_2h_enabled = data.reminder_2h_enabled
    settings.no_show_penalty_points = data.no_show_penalty_points
    settings.no_show_penalty_amount = data.no_show_penalty_amount
    settings.late_cancel_penalty_points = data.late_cancel_penalty_points
    settings.late_cancel_penalty_amount = data.late_cancel_penalty_amount
    return save_branch_settings(db, settings)


def get_effective_branch_settings(db: Session, branch_id: int | None) -> BranchSettings | None:
    if branch_id is None:
        return None
    return get_branch_settings(db, branch_id)
