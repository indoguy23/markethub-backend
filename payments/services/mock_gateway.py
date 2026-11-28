import uuid
from decimal import Decimal, InvalidOperation


class MockPaymentGateway:

    @staticmethod
    def process_payment(amount, outcome="success"):

        try:
            amount = Decimal(str(amount))
        except(InvalidOperation, TypeError, ValueError):
            raise ValueError("Invalid payment amount.")

        if not amount.is_finite() or amount <= Decimal("0.00"):
            raise ValueError("Payment amount must be greater than zero.")
        
        if outcome not in ("success", "failure"):
            raise ValueError("Invalid payment outcome.")
        
        transaction_id = f"MOCK_{uuid.uuid4().hex.upper()}"

        if outcome == "success":
            return {
                "transaction_id": transaction_id,
                "status": "successful",
                "message": "Mock payment completed successfully.",
                "amount": amount,
                "currency": "INR",
            }
        return {
            "transaction_id": transaction_id,
            "status": "failed",
            "message": "Mock payment failed.",
            "amount": amount,
            "currency": "INR",
        }