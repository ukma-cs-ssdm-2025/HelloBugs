"""Tests for refund calculation service"""

from src.api.services.refund_service import calculate_refund_amount

def test_full_refund_when_cancelled_7_or_more_days_before():
    result = calculate_refund_amount(
        booking_date='2025-11-01',
        cancel_date='2025-10-20',
        total_price=1000
    )
    assert result == 1000


def test_half_refund_when_cancelled_3_to_6_days_before():
    result = calculate_refund_amount(
        booking_date='2025-11-01',
        cancel_date='2025-10-27',  
        total_price=1000
    )
    assert result == 500


def test_no_refund_when_cancelled_less_than_3_days():
    result = calculate_refund_amount(
        booking_date='2025-11-01',
        total_price=1000
    )
    assert result == 0