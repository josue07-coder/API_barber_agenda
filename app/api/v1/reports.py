from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from fastapi.responses import StreamingResponse

from app.utils.export_utils import export_to_csv, export_to_excel
from app.database.session import get_db
from app.core.dependecies import require_role
from app.services.metrics_service import (
     get_dashboard_metrics, 
     get_income_by_barber,
     get_income_by_service,
     get_frequent_clients,
     get_clients_with_no_show,
     get_demand_by_hour, get_demand_by_weekday
)

router = APIRouter(
        prefix="/reports",
        tags=["Reports"]
)

@router.get("/dashboard", response_model=dict)
def dashboard(
    *,
    start_date: date = Query(..., description="Fecha inicio YYYY-MM-DD"),
    end_date: date = Query(..., description="Fecha fin YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="Rango de fechas inválido"
        )

    return get_dashboard_metrics(db, start_date, end_date)

@router.get("/financial/by-barber", response_model=list[dict])
def income_by_barber_report(
    *,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="Rango de fechas inválido"
        )

    return get_income_by_barber(db, start_date, end_date)

@router.get("/financial/by-service", response_model=list[dict])
def income_by_service_report(
    *,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="Rango de fechas inválido"
        )

    return get_income_by_service(db, start_date, end_date)

@router.get("/clients/frequent", response_model=list[dict])
def frequent_clients_report(
    *,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="Rango de fechas inválido"
        )

    return get_frequent_clients(db, start_date, end_date)

@router.get("/clients/no-show", response_model=list[dict])
def clients_no_show_report(
    *,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="Rango de fechas inválido"
        )

    return get_clients_with_no_show(db, start_date, end_date)

@router.get("/operations/hours", response_model=list[dict])
def demand_hours_report(
    *,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    if start_date > end_date:
        raise HTTPException(400, "Rango de fechas inválido")
    return get_demand_by_hour(db, start_date, end_date)


@router.get("/operations/days", response_model=list[dict])
def demand_days_report(
    *,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    if start_date > end_date:
        raise HTTPException(400, "Rango de fechas inválido")
    return get_demand_by_weekday(db, start_date, end_date)

@router.get("/financial/by-barber/export/csv")
def export_income_by_barber_csv(
    *,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    data = get_income_by_barber(db, start_date, end_date)

    csv_file = export_to_csv(data)

    return StreamingResponse(
        csv_file,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=ingresos_por_barbero.csv"
        }
    )

@router.get("/financial/by-barber/export/excel")
def export_income_by_barber_excel(
    *,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    data = get_income_by_barber(db, start_date, end_date)

    excel_file = export_to_excel(data)

    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=ingresos_por_barbero.xlsx"
        }
    )
