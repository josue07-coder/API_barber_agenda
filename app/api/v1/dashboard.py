from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.services.dashboard_service import (
    appointments,
    barbers,
    branches,
    clients,
    financial,
    overview,
)


router = APIRouter()


def dashboard_filters(
    start_date: date = Query(...),
    end_date: date = Query(...),
    branch_id: int | None = Query(default=None),
    barber_id: int | None = Query(default=None),
):
    return {
        "start_date": start_date,
        "end_date": end_date,
        "branch_id": branch_id,
        "barber_id": barber_id,
    }


@router.get("/overview", response_model=dict, summary="Dashboard general")
def dashboard_overview_api(
    filters: dict = Depends(dashboard_filters),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return overview(db, current_user, **filters)


@router.get("/financial", response_model=dict, summary="Dashboard financiero")
def dashboard_financial_api(
    filters: dict = Depends(dashboard_filters),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return financial(db, current_user, **filters)


@router.get("/appointments", response_model=dict, summary="Dashboard de citas")
def dashboard_appointments_api(
    filters: dict = Depends(dashboard_filters),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return appointments(db, current_user, **filters)


@router.get("/barbers", response_model=dict, summary="Dashboard de barberos")
def dashboard_barbers_api(
    filters: dict = Depends(dashboard_filters),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return barbers(db, current_user, **filters)


@router.get("/clients", response_model=dict, summary="Dashboard de clientes")
def dashboard_clients_api(
    filters: dict = Depends(dashboard_filters),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return clients(db, current_user, **filters)


@router.get("/branches", response_model=dict, summary="Dashboard de sucursales")
def dashboard_branches_api(
    filters: dict = Depends(dashboard_filters),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return branches(db, current_user, **filters)
