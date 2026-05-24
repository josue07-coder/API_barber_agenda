from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.database.session import get_db
from app.services.metrics_service import (
    get_clients_with_no_show,
    get_dashboard_metrics,
    get_demand_by_hour,
    get_demand_by_weekday,
    get_frequent_clients,
    get_income_by_barber,
    get_income_by_day,
    get_income_by_month,
    get_income_by_payment_method,
    get_income_by_branch,
    get_income_by_service,
    get_payment_export_data,
    get_pending_balances,
    validate_date_range,
)
from app.services.client_penalty_service import get_penalty_report
from app.services.inventory_service import product_report
from app.utils.export_utils import export_to_csv, export_to_excel


router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)

FINANCIAL_EXPORT_COLUMNS = [
    "fecha",
    "cita",
    "cliente",
    "barbero",
    "servicio",
    "metodo_pago",
    "monto_pagado",
    "monto_reembolsado",
    "balance_neto",
    "estado_pago",
]


@router.get("/dashboard", response_model=dict)
def dashboard(
    *,
    start_date: date = Query(..., description="Fecha inicio YYYY-MM-DD"),
    end_date: date = Query(..., description="Fecha fin YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    validate_date_range(start_date, end_date)
    return get_dashboard_metrics(db, start_date, end_date)


@router.get(
    "/financial/by-barber",
    response_model=list[dict],
    summary="Ingresos por barbero",
    description="Calcula ingresos desde pagos cobrados reales. Admin ve todos; barbero solo sus propias citas.",
)
def income_by_barber_report(
    *,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "barber")),
):
    validate_date_range(start_date, end_date)
    return get_income_by_barber(db, start_date, end_date, current_user)


@router.get(
    "/financial/by-service",
    response_model=list[dict],
    summary="Ingresos por servicio",
    description="Agrupa pagos cobrados reales por servicio. Excluye pagos pendientes, fallidos y cancelados.",
)
def income_by_service_report(
    *,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    validate_date_range(start_date, end_date)
    return get_income_by_service(db, start_date, end_date)


@router.get(
    "/financial/by-branch",
    response_model=list[dict],
    summary="Ingresos por sucursal",
    description="Agrupa pagos cobrados reales por sucursal.",
)
def income_by_branch_report(
    *,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    validate_date_range(start_date, end_date)
    return get_income_by_branch(db, start_date, end_date)


@router.get(
    "/financial/by-method",
    response_model=list[dict],
    summary="Ingresos por metodo de pago",
    description="Agrupa pagos cobrados por cash, card, transfer, online u other.",
)
def income_by_payment_method_report(
    *,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    validate_date_range(start_date, end_date)
    return get_income_by_payment_method(db, start_date, end_date)


@router.get(
    "/financial/daily",
    response_model=list[dict],
    summary="Ingresos diarios",
    description="Devuelve ingresos, reembolsos y balance neto por dia.",
)
def income_daily_report(
    *,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    validate_date_range(start_date, end_date)
    return get_income_by_day(db, start_date, end_date)


@router.get(
    "/financial/monthly",
    response_model=list[dict],
    summary="Ingresos mensuales",
    description="Devuelve ingresos, reembolsos y balance neto por mes.",
)
def income_monthly_report(
    *,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    validate_date_range(start_date, end_date)
    return get_income_by_month(db, start_date, end_date)


@router.get(
    "/financial/pending-balances",
    response_model=list[dict],
    summary="Citas con saldo pendiente",
    description="Lista citas activas cuyo total pagado real no cubre el precio del servicio.",
)
def pending_balances_report(
    *,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "barber")),
):
    validate_date_range(start_date, end_date)
    return get_pending_balances(db, start_date, end_date, current_user)


@router.get("/clients/frequent", response_model=list[dict])
def frequent_clients_report(
    *,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    validate_date_range(start_date, end_date)
    return get_frequent_clients(db, start_date, end_date)


@router.get("/clients/no-show", response_model=list[dict])
def clients_no_show_report(
    *,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    validate_date_range(start_date, end_date)
    return get_clients_with_no_show(db, start_date, end_date)


@router.get(
    "/clients/penalties",
    response_model=dict,
    summary="Reporte de penalizaciones",
    description="Resume no-shows, penalizaciones activas/cobradas y penalizaciones por sucursal.",
)
def client_penalties_report(
    *,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    validate_date_range(start_date, end_date)
    return get_penalty_report(db, current_user, start_date, end_date)


@router.get(
    "/products",
    response_model=dict,
    summary="Reporte de productos",
    description="Resume productos mas vendidos, ingresos por productos, ventas por sucursal y margen aproximado.",
)
def products_report(
    *,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    validate_date_range(start_date, end_date)
    return product_report(db, current_user, start_date, end_date)


@router.get("/operations/hours", response_model=list[dict])
def demand_hours_report(
    *,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    validate_date_range(start_date, end_date)
    return get_demand_by_hour(db, start_date, end_date)


@router.get("/operations/days", response_model=list[dict])
def demand_days_report(
    *,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    validate_date_range(start_date, end_date)
    return get_demand_by_weekday(db, start_date, end_date)


@router.get("/financial/by-barber/export/csv")
def export_income_by_barber_csv(
    *,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "barber")),
):
    validate_date_range(start_date, end_date)
    data = get_payment_export_data(db, start_date, end_date, current_user)
    csv_file = export_to_csv(data, FINANCIAL_EXPORT_COLUMNS)

    return StreamingResponse(
        csv_file,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=ingresos_pagos.csv"
        },
    )


@router.get("/financial/by-barber/export/excel")
def export_income_by_barber_excel(
    *,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "barber")),
):
    validate_date_range(start_date, end_date)
    data = get_payment_export_data(db, start_date, end_date, current_user)
    excel_file = export_to_excel(data, FINANCIAL_EXPORT_COLUMNS)

    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=ingresos_pagos.xlsx"
        },
    )
