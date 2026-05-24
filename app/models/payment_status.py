from enum import Enum


class PaymentStatus(str, Enum):
    pending = "pending"
    paid = "paid"
    partially_paid = "partially_paid"
    refunded = "refunded"
    failed = "failed"
    cancelled = "cancelled"
