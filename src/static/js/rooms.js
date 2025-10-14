document.addEventListener('DOMContentLoaded', () => {
    const roomsContainer = document.getElementById('rooms-container');

    fetch('/api/v1/rooms/')
        .then(res => res.json())
        .then(data => {
            roomsContainer.innerHTML = ''; 
            data.forEach(room => {
                const card = document.createElement('div');
                card.classList.add('room-card');

                card.innerHTML = `
                    <div class="room-image">
                        <img src="${room.main_photo_url}" alt="Room ${room.room_number}">
                    </div>
                    <div class="room-info">
                        <h3>Номер ${room.room_number} - ${room.room_type}</h3>
                        <p class="room-description">${room.description}</p>
                        <div class="room-details">
                            <span class="max-guest">Макс. гостей: ${room.max_guest}</span>
                            <span class="price">Ціна: ${room.base_price} грн/ніч</span>
                        </div>
                        <div class="room-details">
                            <span>Поверх: ${room.floor}</span>
                            <span>Площа: ${room.size_sqm} м²</span>
                        </div>
                        <button class="btn btn-primary" onclick="bookRoom(${room.id})">Забронювати</button>
                    </div>
                `;
                roomsContainer.appendChild(card);
            });
        })
        .catch(err => {
            roomsContainer.innerHTML = '<p>Помилка завантаження кімнат.</p>';
            console.error(err);
        });

    const applyBtn = document.getElementById('apply-filters');
    if (applyBtn) {
        applyBtn.addEventListener('click', applyFilters);
    }
});

function bookRoom(roomId) {
    localStorage.setItem('selected_room_id', roomId);
    
    window.location.href = `/booking/create?room_id=${roomId}`;
}

function applyFilters() {
    const capacity = document.getElementById('filter-capacity').value;
    const price = document.getElementById('filter-price').value;
    const roomsContainer = document.getElementById('rooms-container');

    const cards = document.querySelectorAll('.room-card');
    let visibleCount = 0;

    cards.forEach(card => {
        let show = true;

        if (capacity) {
            const maxGuests = parseInt(card.querySelector('.max-guest').textContent.match(/\d+/)[0]);
            if (maxGuests < parseInt(capacity)) show = false;
        }

        if (price && show) {
            const roomPrice = parseFloat(card.querySelector('.price').textContent.match(/\d+/)[0]);
            if (price.includes('+')) {
                const minPrice = parseInt(price);
                if (roomPrice < minPrice) show = false;
            } else {
                const [minPrice, maxPrice] = price.split('-').map(Number);
                if (roomPrice < minPrice || roomPrice > maxPrice) show = false;
            }
        }

        card.style.display = show ? 'block' : 'none';
        if (show) visibleCount++;
    });

    const existingMessage = document.getElementById('no-results-message');
    if (visibleCount === 0) {
        if (!existingMessage) {
            const message = document.createElement('p');
            message.id = 'no-results-message';
            message.textContent = 'Немає кімнат за обраними параметрами.';
            message.style.textAlign = 'center';
            message.style.marginTop = '20px';
            message.style.color = '#B8963E';
            roomsContainer.appendChild(message);
        }
    } else if (existingMessage) {
        existingMessage.remove();
    }
}

window.bookRoom = bookRoom;