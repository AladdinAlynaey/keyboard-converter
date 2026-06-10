/**
 * Smart Keyboard Converter AI - API Client Wrapper
 * Handles auto CSRF cookie header parsing and JWT automatic refresh retries.
 */

const API = {
    // Read a browser cookie by name
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    },

    // Perform a fetch request injecting headers
    async request(url, options = {}) {
        options.headers = options.headers || {};
        options.credentials = 'include'; // Include cookies

        // Add JSON content type if payload present
        if (options.body && !(options.body instanceof FormData) && typeof options.body === 'object') {
            options.body = JSON.stringify(options.body);
            options.headers['Content-Type'] = 'application/json';
        }

        // CSRF Protection
        // Read the csrf_access_token (or csrf_refresh_token for refresh requests)
        const isRefresh = url.endsWith('/auth/refresh');
        const csrfToken = this.getCookie(isRefresh ? 'csrf_refresh_token' : 'csrf_access_token');
        if (csrfToken) {
            options.headers['X-CSRF-Token'] = csrfToken;
        }

        let targetUrl = url;
        if (url.startsWith('/api') && window.location.port === '5173') {
            targetUrl = `${window.location.protocol}//${window.location.hostname}:5454${url}`;
        }

        try {
            let response = await fetch(targetUrl, options);
            
            // Auto-refresh token if access token expired (returns 401)
            if (response.status === 401 && !isRefresh && !url.endsWith('/auth/login') && !url.endsWith('/auth/register')) {
                const refreshSuccess = await this.refreshTokens();
                if (refreshSuccess) {
                    // Retry original request with new cookies
                    const newCsrf = this.getCookie('csrf_access_token');
                    if (newCsrf) {
                        options.headers['X-CSRF-Token'] = newCsrf;
                    }
                    response = await fetch(targetUrl, options);
                } else {
                    // Refresh failed, user needs to login
                    localStorage.removeItem('user');
                    window.dispatchEvent(new Event('unauthorized'));
                }
            }
            
            return response;
        } catch (err) {
            console.error(`API Request Error [${targetUrl}]:`, err);
            throw err;
        }
    },

    async refreshTokens() {
        try {
            const res = await this.request('/api/auth/refresh', { method: 'POST' });
            return res.ok;
        } catch (e) {
            return false;
        }
    },

    // REST methods shortcut helpers
    async get(url) {
        return this.request(url, { method: 'GET' });
    },

    async post(url, body) {
        return this.request(url, { method: 'POST', body });
    },

    async put(url, body) {
        return this.request(url, { method: 'PUT', body });
    },

    async delete(url) {
        return this.request(url, { method: 'DELETE' });
    }
};
