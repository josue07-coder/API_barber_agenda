from enum import Enum


class NotificationChannel(str, Enum):
    email = "email"
    sms = "sms"
    whatsapp = "whatsapp"
    in_app = "in_app"
