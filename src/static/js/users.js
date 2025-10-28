document.addEventListener('DOMContentLoaded', () => {
    const usersTableBody = document.getElementById('users-tbody');
    const modal = document.getElementById('user-modal');
    const closeModalBtn = modal.querySelector('.close-btn');
    const form = document.getElementById('user-form');

    const userIdInput = document.getElementById('user-id');
    const firstNameInput = document.getElementById('first_name');
    const lastNameInput = document.getElementById('last_name');
    const emailInput = document.getElementById('email');
    const phoneInput = document.getElementById('phone');
    const passwordInput = document.getElementById('password');
    const roleInput = document.getElementById('role');

    const createBtn = document.querySelector('button.btn-success');

    window.openUserModal = function(title) {
        modal.classList.add('show');
        document.getElementById('modal-title').innerText = title;
    }

    window.closeUserModal = function() {
        modal.classList.remove('show');
        setTimeout(() => {
            form.reset();
            userIdInput.value = '';
            passwordInput.required = false;
        }, 300);
    }

    window.openCreateUserModal = function() {
        form.reset();
        userIdInput.value = '';
        passwordInput.value = '';
        passwordInput.required = true;
        window.openUserModal('Додати користувача');
    }

    if (createBtn) {
        createBtn.addEventListener('click', () => {
            window.openCreateUserModal();
        });
    }

    closeModalBtn.addEventListener('click', window.closeUserModal);
    
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            window.closeUserModal();
        }
    });

    async function fetchUsers() {
        try {
            const response = await authManager.makeAuthenticatedRequest('/api/v1/users/');
            const users = await response.json();
            usersTableBody.innerHTML = '';

            if (!users || users.length === 0) {
                usersTableBody.innerHTML = `<tr><td colspan="8" class="loading">Користувачів не знайдено</td></tr>`;
                return;
            }

            users.forEach(user => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${user.id}</td>
                    <td>${user.first_name}</td>
                    <td>${user.last_name}</td>
                    <td>${user.email}</td>
                    <td>${user.phone || ''}</td>
                    <td><span class="role-badge role-${user.role}">${user.role}</span></td>
                    <td>${user.created_at ? new Date(user.created_at).toLocaleDateString() : ''}</td>
                    <td>
                        <button class="edit-btn btn btn-edit" data-id="${user.id}">Редагувати</button>
                        <button class="delete-btn btn btn-delete" data-id="${user.id}">Видалити</button>
                    </td>
                `;
                usersTableBody.appendChild(tr);
            });

            addTableEventListeners();
        } catch (error) {
            console.error("Error fetching users:", error);
            usersTableBody.innerHTML = `<tr><td colspan="8" class="loading">Помилка завантаження користувачів</td></tr>`;
        }
    }

    function addTableEventListeners() {
        document.querySelectorAll('.edit-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const userId = btn.dataset.id;
                try {
                    const response = await authManager.makeAuthenticatedRequest(`/api/v1/users/${userId}`);
                    const user = await response.json();

                    userIdInput.value = user.id;
                    firstNameInput.value = user.first_name;
                    lastNameInput.value = user.last_name;
                    emailInput.value = user.email;
                    phoneInput.value = user.phone || '';
                    roleInput.value = user.role;
                    passwordInput.value = '';
                    passwordInput.required = false;

                    window.openUserModal('Редагувати користувача');
                } catch (err) {
                    alert('Помилка завантаження користувача');
                    console.error(err);
                }
            });
        });

        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                if (confirm('Видалити користувача?')) {
                    const userId = btn.dataset.id;
                    try {
                        await authManager.makeAuthenticatedRequest(`/api/v1/users/${userId}`, {
                            method: 'DELETE'
                        });
                        fetchUsers();
                    } catch (err) {
                        alert('Помилка при видаленні користувача');
                        console.error(err);
                    }
                }
            });
        });
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        e.stopPropagation();
        
        const userData = {
            first_name: firstNameInput.value.trim(),
            last_name: lastNameInput.value.trim(),
            email: emailInput.value.trim(),
            phone: phoneInput.value.trim(),
            role: roleInput.value
        };

        if (passwordInput.value.trim()) {
            userData.password = passwordInput.value;
        }

        const userId = userIdInput.value;

        try {
            if (userId) {
                // Update user (PATCH)
                console.log('Оновлення користувача ID:', userId);
                const response = await authManager.makeAuthenticatedRequest(`/api/v1/users/${userId}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(userData)
                });
                
                if (!response.ok) {
                    throw new Error('Помилка оновлення користувача');
                }
                
                console.log('Користувач успішно оновлений');
            } else {
                // Create user (POST)
                console.log('Створення нового користувача');
                if (!userData.password) {
                    alert('Пароль є обов\'язковим при створенні користувача');
                    return;
                }
                const response = await authManager.makeAuthenticatedRequest('/api/v1/users/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(userData)
                });
                
                if (!response.ok) {
                    throw new Error('Помилка створення користувача');
                }
                
                console.log('Користувач успішно створений');
            }
            
            window.closeUserModal();
            await fetchUsers();
            
        } catch (err) {
            console.error('Помилка при збереженні:', err);
            alert('Помилка при збереженні користувача. Перевірте консоль для деталей.');
        }
    });

    fetchUsers();
});