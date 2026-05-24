from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schema.appointment import AppointmentResponse
from app.schema.client import ClientProfileUpdate, ClientResponse
from app.schema.client_penalty import ClientPenaltyResponse
from app.schema.notification import NotificationResponse
from app.schema.payment import PaymentResponse
from app.schema.user import UserResponse
from app.services.appointment_service import list_my_appointments
from app.services.client_service import update_my_client_profile
from app.services.client_penalty_service import list_my_penalties
from app.services.notification_service import list_notifications
from app.services.payment_service import list_my_payments


router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Perfil autenticado",
    description="Devuelve el usuario autenticado, incluyendo client_id cuando el rol es client.",
)
def get_me_api(current_user: User = Depends(get_current_user)):
    return current_user


@router.get(
    "/me/appointments",
    response_model=list[AppointmentResponse],
    summary="Mis citas",
    description="Para clientes autenticados, lista solo sus propias citas.",
)
def get_my_appointments_api(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_my_appointments(db, current_user)


@router.get(
    "/me/payments",
    response_model=list[PaymentResponse],
    summary="Mis pagos",
    description="Para clientes autenticados, lista solo pagos asociados a sus citas.",
)
def get_my_payments_api(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_my_payments(db, current_user)


@router.get(
    "/me/notifications",
    response_model=list[NotificationResponse],
    summary="Mis notificaciones",
    description="Para clientes autenticados, lista solo sus notificaciones propias.",
)
def get_my_notifications_api(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_notifications(db, current_user)


@router.get(
    "/me/penalties",
    response_model=list[ClientPenaltyResponse],
    summary="Mis penalizaciones",
    description="Para clientes autenticados, lista solo sus penalizaciones propias.",
)
def get_my_penalties_api(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_my_penalties(db, current_user)


@router.patch(
    "/me/client-profile",
    response_model=ClientResponse,
    summary="Actualizar mi perfil de cliente",
    description="Permite a un usuario client actualizar name, phone y notes de su propio Client.",
)
def update_my_client_profile_api(
    data: ClientProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_my_client_profile(db, current_user, data)
