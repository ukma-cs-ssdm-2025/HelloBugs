"""Service for calculating booking refunds"""

from datetime import datetime

def calculate_refund_amount(booking_date, cancel_date, total_price):
    booking_dt = datetime.fromisoformat(booking_date)
    cancel_dt = datetime.fromisoformat(cancel_date)
    days_before_booking = (booking_dt - cancel_dt).days
    
    if days_before_booking >= 7:
        return total_price
    else:
        return total_price * 0.5
