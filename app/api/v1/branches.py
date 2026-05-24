from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.database.session import get_db
from app.schema.branch import BranchCreate, BranchResponse, BranchUpdate
from app.schema.branch_settings import BranchSettingsResponse, BranchSettingsUpdate
from app.services.branch_service import (
    create_new_branch,
    deactivate_branch,
    get_branch_or_404,
    list_branches,
    get_settings_for_user,
    update_branch_settings,
    update_existing_branch,
)


router = APIRouter()


@router.get("/", response_model=list[BranchResponse])
def list_branches_api(
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return list_branches(db, search)


@router.get("/{branch_id}", response_model=BranchResponse)
def get_branch_api(
    branch_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return get_branch_or_404(db, branch_id)


@router.get("/{branch_id}/settings", response_model=BranchSettingsResponse)
def get_branch_settings_api(
    branch_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_settings_for_user(db, branch_id, current_user)


@router.put("/{branch_id}/settings", response_model=BranchSettingsResponse)
def update_branch_settings_api(
    branch_id: int,
    data: BranchSettingsUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return update_branch_settings(db, branch_id, data, current_user)


@router.post("/", response_model=BranchResponse)
def create_branch_api(
    data: BranchCreate,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin")),
):
    return create_new_branch(db, data)


@router.put("/{branch_id}", response_model=BranchResponse)
def update_branch_api(
    branch_id: int,
    data: BranchUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin")),
):
    return update_existing_branch(db, branch_id, data)


@router.delete("/{branch_id}", response_model=BranchResponse)
def deactivate_branch_api(
    branch_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin")),
):
    return deactivate_branch(db, branch_id)
