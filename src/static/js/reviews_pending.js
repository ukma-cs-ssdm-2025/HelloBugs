// Модерація відгуків (STAFF/ADMIN)
document.addEventListener('DOMContentLoaded', async () => {
  const container = document.getElementById('pending-reviews');
  const empty = document.getElementById('no-pending');

  const token = localStorage.getItem('access_token');
  if (!token) {
    container.innerHTML = '<div class="error">Потрібна авторизація</div>';
    return;
  }

  try {
    const res = await fetch('/api/v1/auth/me', { headers: { Authorization: `Bearer ${token}` } });
    if (!res.ok) throw new Error('auth');
    const me = await res.json();
    if (!(me.role === 'STAFF' || me.role === 'ADMIN')) {
      container.innerHTML = '<div class="error">Доступ лише для персоналу</div>';
      return;
    }
  } catch (_) {
    container.innerHTML = '<div class="error">Помилка авторизації</div>';
    return;
  }

  await loadPending();

  async function loadPending() {
    container.innerHTML = '<div class="loading">Завантаження...</div>';
    try {
      const resp = await fetch('/api/v1/reviews/pending', { headers: { Authorization: `Bearer ${token}` } });
      if (!resp.ok) throw new Error('load');
      const reviews = await resp.json();

      if (!reviews.length) {
        container.style.display = 'none';
        empty.style.display = 'flex';
        return;
      }

      container.style.display = 'grid';
      empty.style.display = 'none';
      container.innerHTML = '';

      reviews.forEach(r => container.appendChild(renderCard(r)));
    } catch (e) {
      container.innerHTML = '<div class="error">Не вдалося завантажити</div>';
    }
  }

  function renderCard(r) {
    const card = document.createElement('div');
    card.className = 'review-card';
    card.innerHTML = `
      <div class="review-header">
        <div class="review-user">${r.user?.first_name || ''} ${r.user?.last_name || ''}</div>
        <div class="review-rating">${'★'.repeat(r.rating)}${'☆'.repeat(5-r.rating)}</div>
      </div>
      <div class="review-room">Номер: ${r.room?.room_number || r.room_id}</div>
      <div class="review-comment">${r.comment || ''}</div>
      <div class="review-actions">
        <button class="btn btn-primary" data-id="${r.review_id}">Підтвердити</button>
        <button class="btn btn-secondary" data-id="${r.review_id}" data-action="reject">Скасувати</button>
      </div>
    `;

    const approveBtn = card.querySelector('button.btn.btn-primary');
    const rejectBtn = card.querySelector('button[data-action="reject"]');

    approveBtn.addEventListener('click', async (e) => {
      const id = e.currentTarget.getAttribute('data-id');
      approveBtn.disabled = true;
      rejectBtn.disabled = true;
      try {
        const resp = await fetch(`/api/v1/reviews/${id}/approve`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` }
        });
        if (resp.ok) {
          card.remove();
          if (!container.children.length) {
            container.style.display = 'none';
            empty.style.display = 'flex';
          }
        } else {
          const err = await resp.json().catch(() => ({}));
          alert(err.message || 'Не вдалося підтвердити відгук');
          approveBtn.disabled = false;
          rejectBtn.disabled = false;
        }
      } catch (networkErr) {
        console.error('Network error approving review', networkErr);
        approveBtn.disabled = false;
        rejectBtn.disabled = false;
      }
    });

    rejectBtn.addEventListener('click', async (e) => {
      const id = e.currentTarget.getAttribute('data-id');
      approveBtn.disabled = true;
      rejectBtn.disabled = true;
      try {
        const resp = await fetch(`/api/v1/reviews/${id}`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${token}` }
        });
        if (resp.status === 204 || resp.ok) {
          card.remove();
          if (!container.children.length) {
            container.style.display = 'none';
            empty.style.display = 'flex';
          }
        } else {
          const err = await resp.json().catch(() => ({}));
          alert(err.message || 'Не вдалося скасувати відгук');
          approveBtn.disabled = false;
          rejectBtn.disabled = false;
        }
      } catch (networkErr) {
        console.error('Network error rejecting review', networkErr);
        approveBtn.disabled = false;
        rejectBtn.disabled = false;
      }
    });

    return card;
  }
});
