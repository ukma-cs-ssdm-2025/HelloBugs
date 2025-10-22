"""Service for calculating booking refunds based on cancellation policy.

   Policy:
    - ≥7 days before: 100% refund
    - 3-6 days before: 50% refund
    - <3 days before: 0% refund
"""

from datetime import datetime

def calculate_refund_amount(booking_date, cancel_date, total_price):
    booking_dt = datetime.fromisoformat(booking_date)
    cancel_dt = datetime.fromisoformat(cancel_date)
    days_before_booking = (booking_dt - cancel_dt).days

    if days_before_booking >= 7:
        return total_price     
    elif days_before_booking >= 3:
        return total_price * 0.5 
    else:
        return 0.0
