function loadRoomInfo() {
    const urlParams = new URLSearchParams(window.location.search);
    const roomId = urlParams.get('room_id');

    if (!roomId) {
        const savedRoomId = localStorage.getItem('selected_room_id');
        if (savedRoomId) {
            fetchRoomDetails(savedRoomId);
        } else {
            showNoRoomSelected();
        }
    } else {
        fetchRoomDetails(roomId);
    }
}

async function fetchRoomDetails(roomId) {
    try {
        const response = await fetch(`/api/v1/rooms/${roomId}`);
        if (!response.ok) throw new Error('Room not found');

        const room = await response.json();
        displayRoomInfo(room);
        document.getElementById('room_id').value = room.id;
        localStorage.setItem('selected_room_id', room.id); 
        initAvailabilityCalendar(room.id);
    } catch (error) {
        console.error('Error loading room:', error);
        showNoRoomSelected();
    }
}

function displayRoomInfo(room) {
    const roomDisplay = document.getElementById('selected-room-display');
    const roomInfo = document.getElementById('room-info');

    roomDisplay.textContent = `Номер ${room.room_number} - ${room.room_type}`;
    roomDisplay.classList.add('selected');

    roomInfo.innerHTML = `
        <div class="room-detail"><strong>Номер:</strong> ${room.room_number}</div>
        <div class="room-detail"><strong>Тип:</strong> ${room.room_type}</div>
        <div class="room-detail"><strong>Ціна:</strong> ${room.base_price} грн/ніч</div>
        <div class="room-detail"><strong>Макс. гостей:</strong> ${room.max_guest}</div>
        <div class="room-detail"><strong>Поверх:</strong> ${room.floor}</div>
        <div class="room-detail"><strong>Площа:</strong> ${room.size_sqm} м²</div>
    `;
}

function showNoRoomSelected() {
    const roomInfo = document.getElementById('room-info');
    roomInfo.innerHTML = `
        <p style="color: var(--gray); text-align: center; padding: 20px;">
            Номер не обрано
        </p>
    `;
}

function autofillGuestData() {
    if (window.authManager && authManager.isAuthenticated()) {
        const user = authManager.user;
        document.getElementById('user_id').value = user.id || '';
        document.getElementById('guest_email').value = user.email || '';
        document.getElementById('guest_first_name').value = user.first_name || '';
        document.getElementById('guest_last_name').value = user.last_name || '';
        document.getElementById('guest_phone').value = user.phone || '';
    } else {
        const userId = localStorage.getItem('user_id');
        if (!userId) return;

        document.getElementById('user_id').value = userId;
        const email = localStorage.getItem('user_email');
        const firstName = localStorage.getItem('user_first_name');
        const lastName = localStorage.getItem('user_last_name');
        const phone = localStorage.getItem('user_phone');

        if (email) document.getElementById('guest_email').value = email;
        if (firstName) document.getElementById('guest_first_name').value = firstName;
        if (lastName) document.getElementById('guest_last_name').value = lastName;
        if (phone) document.getElementById('guest_phone').value = phone;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadRoomInfo();
    autofillGuestData();
    attachDateInputSync();
    const params = new URLSearchParams(window.location.search);
    const initialRoomId = params.get('room_id') || localStorage.getItem('selected_room_id');
    initAvailabilityCalendar(initialRoomId ? parseInt(initialRoomId) : null);

    const form = document.getElementById('create-booking-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        const data = {
            room_id: parseInt(formData.get('room_id')),
            check_in_date: formData.get('check_in_date'),
            check_out_date: formData.get('check_out_date'),
            special_requests: formData.get('special_requests') || null,
            email: formData.get('email') || null,
            first_name: formData.get('first_name') || null,
            last_name: formData.get('last_name') || null,
            phone: formData.get('phone') || null
        };

        if (window.authManager && authManager.isAuthenticated()) {
            data.user_id = authManager.user.id;
        } else {
            const userId = localStorage.getItem('user_id');
            if (userId) data.user_id = parseInt(userId);
        }

        try {
            const res = await fetch('/api/v1/bookings/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (res.ok) {
                alert('Бронювання створено успішно!');
                form.reset();
                window.location.href = '/bookings';
            } else {
                const error = await res.json();
                alert('Помилка створення: ' + (error.message || 'невідома помилка'));
            }
        } catch (err) {
            console.error(err);
            alert('Помилка зʼєднання з сервером');
        }
    });
});

let calState = {
    roomId: null,
    startMonth: new Date(),
    monthsToShow: 2,
    bookedRanges: [],
    selectedStart: null,
    selectedEnd: null,
};

function attachDateInputSync() {
    const inEl = document.getElementById('check_in_date');
    const outEl = document.getElementById('check_out_date');
    const nightsEl = document.getElementById('nights-count');

    function diffNights() {
        if (inEl.value && outEl.value) {
            const n = (new Date(outEl.value) - new Date(inEl.value)) / (1000*60*60*24);
            nightsEl.textContent = n > 0 ? n : 0;
        } else {
            nightsEl.textContent = 0;
        }
    }

    inEl.addEventListener('change', () => {
        calState.selectedStart = inEl.value || null;
        if (calState.selectedEnd && calState.selectedStart && calState.selectedEnd <= calState.selectedStart) {
            calState.selectedEnd = null;
            outEl.value = '';
        }
        renderCalendar();
        diffNights();
    });
    outEl.addEventListener('change', () => {
        calState.selectedEnd = outEl.value || null;
        renderCalendar();
        diffNights();
    });

    diffNights();
}

async function initAvailabilityCalendar(roomId) {
    calState.roomId = roomId;
    const container = document.getElementById('availability-calendar');
    if (!container) return;

    container.innerHTML = `
      <div class="cal-nav">
        <button class="cal-btn cal-prev" aria-label="Попередній місяць">‹</button>
        <div class="cal-months"></div>
        <button class="cal-btn cal-next" aria-label="Наступний місяць">›</button>
      </div>
      <div class="cal-grid-wrapper"></div>
      <div class="cal-legend">
        <span class="dot booked"></span> Зайнято
        <span class="dot selected"></span> Обрано
      </div>
    `;

    container.querySelector('.cal-prev').addEventListener('click', async () => {
        calState.startMonth = addMonths(calState.startMonth, -1);
        await loadAvailability();
        renderCalendar();
    });
    container.querySelector('.cal-next').addEventListener('click', async () => {
        calState.startMonth = addMonths(calState.startMonth, 1);
        await loadAvailability();
        renderCalendar();
    });

    await loadAvailability();
    renderCalendar();
}

async function loadAvailability() {
    if (!calState.roomId) return;
    const start = firstDayOfMonth(calState.startMonth);
    const end = addMonths(start, calState.monthsToShow);
    const startStr = toISODate(start);
    const endStr = toISODate(end);
    const res = await fetch(`/api/v1/rooms/${calState.roomId}/availability?start=${startStr}&end=${endStr}`);
    const data = await res.json();
    calState.bookedRanges = data.booked || [];
}

function renderCalendar() {
    const wrapper = document.querySelector('#availability-calendar .cal-grid-wrapper');
    const monthsTitle = document.querySelector('#availability-calendar .cal-months');
    if (!wrapper) return;
    wrapper.innerHTML = '';
    monthsTitle.innerHTML = '';

    let m = new Date(calState.startMonth);
    for (let i = 0; i < calState.monthsToShow; i++) {
        const monthEl = buildMonth(m);
        wrapper.appendChild(monthEl);
        const title = document.createElement('div');
        title.className = 'cal-month-title';
        title.textContent = monthLabel(m);
        monthsTitle.appendChild(title);
        m = addMonths(m, 1);
    }
}

function buildMonth(dateObj) {
    const monthStart = new Date(dateObj.getFullYear(), dateObj.getMonth(), 1);
    const monthEnd = new Date(dateObj.getFullYear(), dateObj.getMonth()+1, 0);
    const grid = document.createElement('div');
    grid.className = 'cal-month';

    const weekdays = ['Пн','Вт','Ср','Чт','Пт','Сб','Нд'];
    const head = document.createElement('div');
    head.className = 'cal-weekdays';
    weekdays.forEach(d => { const s=document.createElement('span'); s.textContent=d; head.appendChild(s); });
    grid.appendChild(head);

    const firstWeekday = (monthStart.getDay()+6)%7; // Monday=0
    const daysGrid = document.createElement('div');
    daysGrid.className = 'cal-days';
    for (let i=0; i<firstWeekday; i++) {
        const blank = document.createElement('button');
        blank.className = 'cal-day blank';
        blank.tabIndex = -1;
        blank.disabled = true;
        daysGrid.appendChild(blank);
    }

    const today = new Date(); today.setHours(0,0,0,0);
    for (let d=1; d<=monthEnd.getDate(); d++) {
        const curr = new Date(dateObj.getFullYear(), dateObj.getMonth(), d);
        const currStr = toISODate(curr);
        const btn = document.createElement('button');
        btn.className = 'cal-day';
        btn.textContent = String(d);

        const isPast = curr < today;
        const isBooked = isDateBooked(currStr);
        const isSelectedStart = calState.selectedStart === currStr;
        const inRange = calState.selectedStart && calState.selectedEnd && currStr > calState.selectedStart && currStr < calState.selectedEnd;

        if (isBooked || isPast) {
            btn.classList.add('booked');
            btn.disabled = true;
        } else {
            btn.classList.add('available');
            btn.addEventListener('click', () => onDayClick(currStr));
        }

        if (isSelectedStart) btn.classList.add('selected');
        if (inRange) btn.classList.add('in-range');

        daysGrid.appendChild(btn);
    }

    grid.appendChild(daysGrid);
    return grid;
}

function onDayClick(dateStr) {
    const inEl = document.getElementById('check_in_date');
    const outEl = document.getElementById('check_out_date');

    if (!calState.selectedStart || (calState.selectedStart && calState.selectedEnd)) {
        calState.selectedStart = dateStr;
        calState.selectedEnd = null;
        inEl.value = dateStr;
        outEl.value = '';
    } else {
        if (dateStr <= calState.selectedStart) return;
        if (!isRangeFree(calState.selectedStart, dateStr)) return;
        calState.selectedEnd = dateStr;
        outEl.value = dateStr;
    }
    renderCalendar();
    const evt = new Event('change'); inEl.dispatchEvent(evt); outEl.dispatchEvent(evt);
}

function isDateBooked(dateStr) {
    const d = dateStr;
    return calState.bookedRanges.some(r => d >= r.start && d < r.end);
}

function isRangeFree(startStr, endStr) {
    let curr = new Date(startStr);
    const end = new Date(endStr);
    while (curr < end) {
        const currStr = toISODate(curr);
        if (isDateBooked(currStr)) return false;
        curr.setDate(curr.getDate()+1);
    }
    return true;
}

// Helpers
function toISODate(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth()+1).padStart(2,'0');
  const day = String(d.getDate()).padStart(2,'0');
  return `${y}-${m}-${day}`;
}
function firstDayOfMonth(d) { return new Date(d.getFullYear(), d.getMonth(), 1); }
function addMonths(d, n) { return new Date(d.getFullYear(), d.getMonth()+n, 1); }
function monthLabel(d) {
    const months = ['Січень','Лютий','Березень','Квітень','Травень','Червень','Липень','Серпень','Вересень','Жовтень','Листопад','Грудень'];
    return `${months[d.getMonth()]} ${d.getFullYear()}`;
}
