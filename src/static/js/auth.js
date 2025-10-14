// Authentication management JavaScript

class AuthManager {
    constructor() {
        this.token = localStorage.getItem('authToken');
        this.user = JSON.parse(localStorage.getItem('user') || 'null');
        this.init();
    }

    init() {
        // Update navigation based on auth status
        this.updateNavigation();
        
        // Check token validity on page load
        if (this.token) {
            this.validateToken();
        }
    }

    // Check if user is authenticated
    isAuthenticated() {
        return !!this.token && !!this.user;
    }

    // Check if user is admin
    isAdmin() {
        return this.user && this.user.is_admin;
    }

    // Update navigation based on auth status
    updateNavigation() {
        const loginBtn = document.querySelector('.login-btn');
        const navList = document.querySelector('.nav-list');
        
        if (this.isAuthenticated()) {
            // Hide login button and show user menu
            if (loginBtn) {
                loginBtn.style.display = 'none';
            }
            
            // Add user menu to navigation
            this.addUserMenu(navList);
        } else {
            // Show login button
            if (loginBtn) {
                loginBtn.style.display = 'flex';
            }
            
            // Remove user menu if exists
            this.removeUserMenu(navList);
        }
    }

    // Add user menu to navigation
    addUserMenu(navList) {
        // Remove existing user menu
        this.removeUserMenu(navList);
        
        if (!navList) return;
        
        const userMenu = document.createElement('li');
        userMenu.className = 'dropdown';
        userMenu.innerHTML = `
            <a href="#" class="nav-link">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                </svg>
                ${this.user.first_name} ${this.user.last_name}
            </a>
            <ul class="dropdown-menu">
                <li><a href="/profile">Мій профіль</a></li>
                <li><a href="/bookings">Мої бронювання</a></li>
                ${this.isAdmin() ? '<li><a href="/admin">Адмін панель</a></li>' : ''}
                <li><a href="#" onclick="authManager.logout()">Вийти</a></li>
            </ul>
        `;
        
        navList.appendChild(userMenu);
    }

    // Remove user menu from navigation
    removeUserMenu(navList) {
        if (!navList) return;
        
        const userMenu = navList.querySelector('.dropdown');
        if (userMenu) {
            userMenu.remove();
        }
    }

    // Validate token with server
    async validateToken() {
        try {
            const response = await fetch('/api/v1/auth/me', {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });
            
            if (response.ok) {
                const userData = await response.json();
                this.user = userData;
                localStorage.setItem('user', JSON.stringify(userData));
                this.updateNavigation();
            } else {
                this.logout();
            }
        } catch (error) {
            console.error('Token validation failed:', error);
            this.logout();
        }
    }

    // Login user
    async login(email, password) {
        try {
            const response = await fetch('/api/v1/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.token = data.token;
                this.user = data.user;
                localStorage.setItem('authToken', this.token);
                localStorage.setItem('user', JSON.stringify(this.user));
                this.updateNavigation();
                return { success: true, data };
            } else {
                return { success: false, message: data.message };
            }
        } catch (error) {
            return { success: false, message: 'Помилка з\'єднання з сервером' };
        }
    }

    // Register user
    async register(userData) {
        try {
            const response = await fetch('/api/v1/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.token = data.token;
                this.user = data.user;
                localStorage.setItem('authToken', this.token);
                localStorage.setItem('user', JSON.stringify(this.user));
                this.updateNavigation();
                return { success: true, data };
            } else {
                return { success: false, message: data.message };
            }
        } catch (error) {
            return { success: false, message: 'Помилка з\'єднання з сервером' };
        }
    }

    // Logout user
    logout() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
        this.updateNavigation();
        
        // Redirect to home page if not already there
        if (window.location.pathname !== '/') {
            window.location.href = '/';
        }
    }

    // Get auth headers for API requests
    getAuthHeaders() {
        if (this.token) {
            return {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            };
        }
        return {
            'Content-Type': 'application/json'
        };
    }

    // Make authenticated API request
    async makeAuthenticatedRequest(url, options = {}) {
        const headers = {
            ...this.getAuthHeaders(),
            ...options.headers
        };
        
        const response = await fetch(url, {
            ...options,
            headers
        });
        
        // If unauthorized, logout user
        if (response.status === 401) {
            this.logout();
        }
        
        return response;
    }
}

// Initialize auth manager
const authManager = new AuthManager();

// Export for use in other scripts
window.authManager = authManager;
