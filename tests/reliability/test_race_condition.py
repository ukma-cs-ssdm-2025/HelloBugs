import pytest
import threading
from datetime import date, timedelta
import uuid

from src.api.models.room_model import Room, RoomType, RoomStatus
from src.api.models.booking_model import Booking

@pytest.fixture(scope="function")
def race_room(db_session):
    """
    Створює одну кімнату, за яку будуть "змагатися" потоки
    (користувачі натискати на кнопку "забронювати")
    """
    room = Room(
        room_number=f"{uuid.uuid4().hex[:6]}",
        room_type=RoomType.STANDARD,
        max_guest=2,
        base_price=1000.0,
        status=RoomStatus.AVAILABLE,
        floor=1,
        size_sqm=25.0,
        description="Room for concurrency test"
    )
    db_session.add(room)
    db_session.commit()
    yield room

    db_session.query(Booking).filter_by(room_id=room.room_id).delete()
    db_session.query(Room).filter_by(room_id=room.room_id).delete()
    db_session.commit()


def book_room_task(client, room_id, check_in, check_out, results_list):
    """
    Імітує одного користувача, що намагається забронювати номер.
    """
    payload = {
        "room_id": room_id,
        "check_in_date": check_in.isoformat(),
        "check_out_date": check_out.isoformat(),
        "email": f"g{uuid.uuid4().hex[:10]}@gmail.com",
        "first_name": "Race",
        "last_name": "Testenko",
        "phone": f"+38099{uuid.uuid4().int % 10000000:07d}"
    }

    try:
        # `client` (з pytest-flask) є потоко-безпечним.
        response = client.post("/api/v1/bookings/", json=payload)
        results_list.append(response.status_code)
    except Exception as e:
        results_list.append(str(e))


def test_booking_race_condition(client, db_session, race_room):
    """
    Перевіряє race condition при бронюванні.
    Запускає 5 одночасних запитів на бронювання однієї кімнати.
    """
    num_threads = 5
    threads = []
    results = []

    check_in = date.today() + timedelta(days=20)
    check_out = date.today() + timedelta(days=25)

    for _ in range(num_threads):
        t = threading.Thread(
            target=book_room_task,
            args=(client, race_room.room_id, check_in, check_out, results)
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    success_count = results.count(201)
    conflict_count = results.count(409)

    final_bookings_in_db = db_session.query(Booking).filter_by(
        room_id=race_room.room_id,
        check_in_date=check_in
    ).count()

    assert success_count == 1
    assert conflict_count == num_threads - 1
    assert final_bookings_in_db == 1