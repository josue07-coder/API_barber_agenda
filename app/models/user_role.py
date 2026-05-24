from enum import Enum


class UserRole(str, Enum):
    admin = "admin"
    barber = "barber"
    client = "client"
