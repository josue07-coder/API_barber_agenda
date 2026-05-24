from enum import Enum


class NotificationStatus(str, Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"
    cancelled = "cancelled"
