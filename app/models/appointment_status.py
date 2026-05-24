from enum import Enum

class AppointmentStatus (str, Enum):
    agendada = "agendada"
    confirmada = "confirmada"
    completada = "completada"
    cancelada = "cancelada"
    no_show = "no_show"
