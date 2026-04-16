class PaymentNotFoundError(Exception):
    def __init__(self, payment_id: str) -> None:
        super().__init__(f"Payment {payment_id} was not found")
