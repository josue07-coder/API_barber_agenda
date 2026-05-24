from enum import Enum


class PaymentMethod(str, Enum):
    cash = "cash"
    card = "card"
    transfer = "transfer"
    online = "online"
    other = "other"
