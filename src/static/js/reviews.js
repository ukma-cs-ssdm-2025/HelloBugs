// Завантаження та відображення відгуків
document.addEventListener('DOMContentLoaded', async () => {
    await loadReviews();
    await loadAverageRating();
    setupEditModal();
});

async function loadReviews() {
    const container = document.getElementById('reviews-container');
    const emptyState = document.getElementById('empty-state');
    
    try {
        const response = await fetch('/api/v1/reviews/');
        
        if (!response.ok) {
            throw new Error('Помилка завантаження відгуків');
        }
        
        const reviews = await response.json();
        
        if (reviews.length === 0) {
            container.style.display = 'none';
            emptyState.style.display = 'flex';
            
            // Показуємо кнопку "Залишити відгук" для авторизованих користувачів
            const token = localStorage.getItem('access_token');
            if (token) {
                const authOnlyElements = emptyState.querySelectorAll('.auth-only');
                authOnlyElements.forEach(el => el.style.display = 'inline-block');
            }
        } else {
            container.innerHTML = '';
            emptyState.style.display = 'none';
            
            reviews.forEach(review => {
                container.appendChild(createReviewCard(review));
            });
            
            document.getElementById('total-reviews').textContent = reviews.length;

            // обчислення середнього за рейтингом
            const sum = reviews.reduce((acc, r) => acc + (Number(r.rating) || 0), 0);
            const avg = reviews.length ? (sum / reviews.length) : 0;
            const avgEl = document.getElementById('average-rating');
            if (avgEl) {
                avgEl.textContent = avg.toFixed(1);
            }
        }
    } catch (error) {
        console.error('Помилка:', error);
        container.innerHTML = '<p class="error-message">Не вдалося завантажити відгуки</p>';
    }
}

async function loadAverageRating() {
    try {
        const response = await fetch('/api/v1/reviews/average-rating');
        
        if (response.ok) {
            const data = await response.json();
            const value = Number(data && data.average_rating);
            if (!Number.isNaN(value)) {
                document.getElementById('average-rating').textContent = value.toFixed(1);
            }
        }
    } catch (error) {
        console.error('Помилка завантаження середнього рейтингу:', error);
    }
}

function createReviewCard(review) {
    const card = document.createElement('div');
    card.className = 'review-card';
    
    const stars = '★'.repeat(review.rating) + '☆'.repeat(5 - review.rating);
    const date = new Date(review.created_at).toLocaleDateString('uk-UA', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
    
    const userName = review.user 
        ? `${review.user.first_name} ${review.user.last_name}`
        : 'Анонімний користувач';
    
    const roomInfo = review.room 
        ? `<span class="review-room">Номер ${review.room.room_number} - ${review.room.room_type}</span>`
        : '<span class="review-room">Номер не вказано</span>';
    
    card.innerHTML = `
        <div class="review-header">
            <div class="review-author">
                <div class="author-avatar">${userName.charAt(0)}</div>
                <div class="author-info">
                    <h3 class="author-name">${userName}</h3>
                    <span class="review-date">${date}</span>
                    ${roomInfo}
                </div>
            </div>
            <div class="review-rating">${stars}</div>
        </div>
        ${review.comment ? `<p class="review-comment">${escapeHtml(review.comment)}</p>` : ''}
        <div class="review-actions" id="review-actions-${review.review_id}" style="display: none;">
            <button class="btn-icon edit-review" data-review-id="${review.review_id}" title="Редагувати">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                </svg>
            </button>
            <button class="btn-icon delete-review" data-review-id="${review.review_id}" title="Видалити">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
            </button>
        </div>
    `;
    
    // Показуємо кнопки редагування/видалення для власника відгуку
    checkReviewOwnership(review);
    
    return card;
}

async function checkReviewOwnership(review) {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    
    try {
        const response = await fetch('/api/v1/auth/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const user = await response.json();
            const isOwner = user.user_id === review.user_id;
            const isAdmin = user.role === 'ADMIN';

            const actionsDiv = document.getElementById(`review-actions-${review.review_id}`);
            if (!actionsDiv) return;

            const editBtn = actionsDiv.querySelector('.edit-review');
            const deleteBtn = actionsDiv.querySelector('.delete-review');

            if (editBtn) {
                if (isOwner) {
                    editBtn.style.display = 'inline-flex';
                    editBtn.addEventListener('click', () => openEditModal(review));
                } else {
                    editBtn.style.display = 'none';
                }
            }

            if (deleteBtn) {
                if (isOwner || isAdmin) {
                    deleteBtn.style.display = 'inline-flex';
                    deleteBtn.addEventListener('click', () => deleteReview(review.review_id));
                } else {
                    deleteBtn.style.display = 'none';
                }
            }

            if ((isOwner && editBtn) || (isOwner || isAdmin) && deleteBtn) {
                actionsDiv.style.display = 'flex';
            }
        }
    } catch (error) {
        console.error('Помилка перевірки власника відгуку:', error);
    }
}

function setupEditModal() {
    const modal = document.getElementById('edit-review-modal');
    const closeBtn = document.getElementById('edit-close-modal');
    const cancelBtn = document.getElementById('edit-cancel-modal-btn');
    const form = document.getElementById('edit-review-form');
    
    // Закриття модалки
    closeBtn.onclick = () => modal.style.display = 'none';
    cancelBtn.onclick = () => modal.style.display = 'none';
    
    window.onclick = (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    };
    
    // Рейтинг зірками
    setupStarRating('edit-star-rating', 'edit-rating');
    
    // Відправка форми
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await updateReview();
    });
}

function openEditModal(review) {
    const modal = document.getElementById('edit-review-modal');
    
    document.getElementById('edit_review_id').value = review.review_id;
    document.getElementById('edit-rating').value = review.rating;
    document.getElementById('edit-comment').value = review.comment || '';
    
    // Встановлюємо зірки
    const stars = document.querySelectorAll('#edit-star-rating .star');
    stars.forEach((star, index) => {
        if (index < review.rating) {
            star.classList.add('active');
        } else {
            star.classList.remove('active');
        }
    });
    
    modal.style.display = 'block';
}

async function updateReview() {
    const reviewId = document.getElementById('edit_review_id').value;
    const rating = parseInt(document.getElementById('edit-rating').value);
    const comment = document.getElementById('edit-comment').value;
    
    if (!rating) {
        alert('Будь ласка, оберіть рейтинг');
        return;
    }
    
    const token = localStorage.getItem('access_token');
    if (!token) {
        alert('Необхідна авторизація');
        window.location.href = '/login';
        return;
    }
    
    try {
        const response = await fetch(`/api/v1/reviews/${reviewId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ rating, comment })
        });
        
        if (response.ok) {
            alert('Відгук успішно оновлено!');
            document.getElementById('edit-review-modal').style.display = 'none';
            await loadReviews();
        } else {
            const error = await response.json();
            alert(error.message || 'Помилка оновлення відгуку');
        }
    } catch (error) {
        console.error('Помилка:', error);
        alert('Не вдалося оновити відгук');
    }
}

async function deleteReview(reviewId) {
    if (!confirm('Ви впевнені, що хочете видалити цей відгук?')) {
        return;
    }
    
    const token = localStorage.getItem('access_token');
    if (!token) {
        alert('Необхідна авторизація');
        window.location.href = '/login';
        return;
    }
    
    try {
        const response = await fetch(`/api/v1/reviews/${reviewId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            alert('Відгук успішно видалено');
            await loadReviews();
            await loadAverageRating();
        } else {
            const error = await response.json();
            alert(error.message || 'Помилка видалення відгуку');
        }
    } catch (error) {
        console.error('Помилка:', error);
        alert('Не вдалося видалити відгук');
    }
}

function setupStarRating(containerId, inputId) {
    const stars = document.querySelectorAll(`#${containerId} .star`);
    const ratingInput = document.getElementById(inputId);
    
    stars.forEach(star => {
        star.addEventListener('click', () => {
            const rating = parseInt(star.dataset.rating);
            ratingInput.value = rating;
            
            stars.forEach((s, index) => {
                if (index < rating) {
                    s.classList.add('active');
                } else {
                    s.classList.remove('active');
                }
            });
        });
        
        star.addEventListener('mouseenter', () => {
            const rating = parseInt(star.dataset.rating);
            stars.forEach((s, index) => {
                if (index < rating) {
                    s.classList.add('hover');
                } else {
                    s.classList.remove('hover');
                }
            });
        });
    });
    
    const container = document.getElementById(containerId);
    container.addEventListener('mouseleave', () => {
        stars.forEach(s => s.classList.remove('hover'));
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
