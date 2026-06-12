/**
 * Smart Keyboard Converter AI - SPA Router & App Controller
 */

class AppController {
    constructor() {
        this.user = null;
        this.aiConfig = { ai_enabled: false, available_models: [] };
        
        // Bind events
        window.addEventListener('hashchange', () => this.handleRouting());
        window.addEventListener('load', () => this.init());
        window.addEventListener('unauthorized', () => this.handleUnauthorized());
    }

    async init() {
        this.initTheme();
        this.setupEventListeners();
        
        // Check for Google OAuth callback in URL pathname
        if (window.location.pathname === '/auth/google/callback') {
            const urlParams = new URLSearchParams(window.location.search);
            const code = urlParams.get('code');
            if (code) {
                window.history.replaceState({}, document.title, "/");
                this.toast("Authenticating with Google...", "info");
                
                try {
                    const res = await API.post('/api/auth/google', { code });
                    const resData = await res.json();
                    if (res.ok) {
                        this.user = resData.user;
                        localStorage.setItem('user', JSON.stringify(this.user));
                        this.toast("Logged in with Google successfully!", "success");
                        this.updateAuthStateUI();
                    } else {
                        this.toast(resData.error || "Google sign in failed.", "error");
                    }
                } catch (err) {
                    this.toast("Failed to authenticate via Google OAuth.", "error");
                }
                window.location.hash = '#converter';
            }
        }

        // Restore user state from localStorage
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            try {
                this.user = JSON.parse(storedUser);
            } catch (e) {
                localStorage.removeItem('user');
            }
        }

        // Fetch platform capabilities configurations (AI toggles, models)
        await this.fetchPlatformConfig();
        
        // Check session profile on start if user was logged in
        if (this.user) {
            await this.refreshUserProfile();
        }

        this.updateAuthStateUI();
        this.handleRouting();
    }

    initTheme() {
        const themeToggle = document.getElementById('theme-toggle');
        const storedTheme = localStorage.getItem('theme') || 'dark';
        
        if (storedTheme === 'light') {
            document.body.classList.remove('dark-theme');
            document.body.classList.add('light-theme');
            if (themeToggle) themeToggle.checked = false;
        } else {
            document.body.classList.remove('light-theme');
            document.body.classList.add('dark-theme');
            if (themeToggle) themeToggle.checked = true;
        }
    }

    setupEventListeners() {
        // Theme switch checkbox
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('change', (e) => {
                if (e.target.checked) {
                    document.body.classList.remove('light-theme');
                    document.body.classList.add('dark-theme');
                    localStorage.setItem('theme', 'dark');
                } else {
                    document.body.classList.remove('dark-theme');
                    document.body.classList.add('light-theme');
                    localStorage.setItem('theme', 'light');
                }
            });
        }

        // Auth switches
        const switchLink = document.getElementById('auth-switch-link');
        if (switchLink) {
            switchLink.addEventListener('click', (e) => {
                e.preventDefault();
                const title = document.getElementById('auth-modal-title');
                const loginForm = document.getElementById('login-form');
                const regForm = document.getElementById('register-form');
                const forgotForm = document.getElementById('forgot-form');
                const switchText = document.getElementById('auth-switch-text');
                
                if (loginForm.classList.contains('hidden')) {
                    // Switch to Login
                    title.textContent = "Sign In";
                    loginForm.classList.remove('hidden');
                    regForm.classList.add('hidden');
                    forgotForm.classList.add('hidden');
                    switchText.textContent = "New user? ";
                    switchLink.textContent = "Create an account";
                } else {
                    // Switch to Register
                    title.textContent = "Register";
                    loginForm.classList.add('hidden');
                    regForm.classList.remove('hidden');
                    forgotForm.classList.add('hidden');
                    switchText.textContent = "Already have an account? ";
                    switchLink.textContent = "Log In";
                }
            });
        }

        // Login Handler
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const email = document.getElementById('login-email').value;
                const password = document.getElementById('login-password').value;
                const rememberMe = document.getElementById('login-remember').checked;
                
                try {
                    const res = await API.post('/api/auth/login', { email, password, remember_me: rememberMe });
                    const resData = await res.json();
                    
                    if (!res.ok) {
                        this.toast(resData.error || "Login failed", "error");
                        return;
                    }
                    
                    this.user = resData.user;
                    localStorage.setItem('user', JSON.stringify(this.user));
                    this.toast("Logged in successfully!", "success");
                    this.hideAuthModal();
                    this.updateAuthStateUI();
                    
                    // Reload current view
                    this.handleRouting();
                } catch (err) {
                    this.toast("An error occurred during login. Please try again.", "error");
                }
            });
        }

        // Registration Handler
        const registerForm = document.getElementById('register-form');
        if (registerForm) {
            registerForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const email = document.getElementById('register-email').value;
                const password = document.getElementById('register-password').value;
                
                try {
                    const res = await API.post('/api/auth/register', { email, password });
                    const resData = await res.json();
                    
                    if (!res.ok) {
                        this.toast(resData.error || "Registration failed", "error");
                        return;
                    }
                    
                    this.toast(resData.message || "Registration completed. Check email for validation.", "success");
                    // Switch back to Login view
                    document.getElementById('auth-switch-link').click();
                } catch (err) {
                    this.toast("An error occurred during registration.", "error");
                }
            });
        }

        // Forgot password Handler
        const forgotForm = document.getElementById('forgot-form');
        if (forgotForm) {
            forgotForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const email = document.getElementById('forgot-email').value;
                try {
                    const res = await API.post('/api/auth/reset-password/request', { email });
                    const resData = await res.json();
                    this.toast(resData.message || "Reset link dispatched.", "success");
                    this.hideAuthModal();
                } catch (err) {
                    this.toast("Failed to request password reset.", "error");
                }
            });
        }

        // Google OAuth handler
        const googleBtn = document.getElementById('btn-google-oauth');
        if (googleBtn) {
            googleBtn.addEventListener('click', () => {
                const clientId = this.aiConfig.google_client_id || "392585962294-l1pg0ktt9apep0eun27mj79emrf29opl.apps.googleusercontent.com";
                const redirectUri = encodeURIComponent(this.aiConfig.google_redirect_uri || "https://keboard.alaadin-alynaey.site/auth/google/callback");
                const oauthUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${clientId}&redirect_uri=${redirectUri}&response_type=code&scope=openid%20email%20profile`;
                window.location.href = oauthUrl;
            });
        }

        // Reset password confirm Handler
        const resetConfirmForm = document.getElementById('reset-confirm-form');
        if (resetConfirmForm) {
            resetConfirmForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const token = document.getElementById('reset-confirm-token').value;
                const newPassword = document.getElementById('reset-confirm-password').value;
                try {
                    const res = await API.post('/api/auth/reset-password/confirm', { token, new_password: newPassword });
                    const resData = await res.json();
                    if (res.ok) {
                        this.toast(resData.message || "Password reset successful.", "success");
                        this.showAuthModal('login');
                    } else {
                        this.toast(resData.error || "Failed to reset password.", "error");
                    }
                } catch (err) {
                    this.toast("Failed to reset password.", "error");
                }
            });
        }

        // Mobile responsive aside menu toggle trigger
        const mobileMenuBtn = document.getElementById('mobile-menu-btn');
        if (mobileMenuBtn) {
            mobileMenuBtn.addEventListener('click', () => {
                this.toggleMobileSidebar();
            });
        }

        // Sidebar backdrop click to close
        const backdrop = document.getElementById('sidebar-backdrop');
        if (backdrop) {
            backdrop.addEventListener('click', () => {
                this.closeMobileSidebar();
            });
        }
    }

    async fetchPlatformConfig() {
        try {
            const res = await API.get('/api/converter/config');
            if (res.ok) {
                this.aiConfig = await res.json();
            }
        } catch (e) {
            console.error("Failed to query platform configurations:", e);
        }
    }

    async refreshUserProfile() {
        try {
            const res = await API.get('/api/auth/profile');
            if (res.ok) {
                const resData = await res.json();
                this.user = resData.user;
                localStorage.setItem('user', JSON.stringify(this.user));
            } else if (res.status === 401) {
                this.handleUnauthorized();
            }
        } catch (e) {
            // Offline/Local fail
        }
    }

    handleRouting() {
        const hash = window.location.hash || '#converter';
        const viewName = hash.split('?')[0].replace('#', '');

        // Intercept verify-email hash route
        if (viewName === 'verify-email') {
            const queryParams = {};
            if (hash.includes('?')) {
                const queryStr = hash.split('?')[1];
                const pairs = queryStr.split('&');
                for (const pair of pairs) {
                    const [key, val] = pair.split('=');
                    queryParams[decodeURIComponent(key)] = decodeURIComponent(val || '');
                }
            }
            const token = queryParams.token;
            if (token) {
                this.toast("Verifying your email...", "info");
                API.get(`/api/auth/verify-email?token=${encodeURIComponent(token)}`)
                    .then(async res => {
                        const data = await res.json();
                        if (res.ok) {
                            this.toast(data.message || "Email verified successfully!", "success");
                            if (this.user) {
                                this.user.is_verified = true;
                                localStorage.setItem('user', JSON.stringify(this.user));
                                this.updateAuthStateUI();
                            }
                        } else {
                            this.toast(data.error || "Email verification failed.", "error");
                        }
                        window.location.hash = this.user ? '#profile' : '#converter';
                    })
                    .catch(() => {
                        this.toast("Connection error during email verification.", "error");
                        window.location.hash = '#converter';
                    });
            } else {
                this.toast("Missing verification token.", "error");
                window.location.hash = '#converter';
            }
            return;
        }

        // Intercept reset-password hash route
        if (viewName === 'reset-password') {
            const queryParams = {};
            if (hash.includes('?')) {
                const queryStr = hash.split('?')[1];
                const pairs = queryStr.split('&');
                for (const pair of pairs) {
                    const [key, val] = pair.split('=');
                    queryParams[decodeURIComponent(key)] = decodeURIComponent(val || '');
                }
            }
            const token = queryParams.token;
            if (token) {
                window.location.hash = '#converter';
                this.showAuthModal('reset', token);
            } else {
                this.toast("Missing password reset token.", "error");
                window.location.hash = '#converter';
            }
            return;
        }
        
        // Guards: require login for profile, history, my layouts, marketplace
        const securedViews = ['layouts', 'history', 'profile', 'editor', 'marketplace'];
        if (securedViews.includes(viewName)) {
            if (!this.user) {
                this.toast("Please sign in to access this page.", "info");
                window.location.hash = '#converter';
                this.showAuthModal('login');
                return;
            }
            if (viewName === 'marketplace' && !this.user.is_verified) {
                this.toast("You must verify your email address to browse the marketplace.", "warning");
                window.location.hash = '#profile';
                return;
            }
        }

        // Close mobile menu if open
        this.closeMobileSidebar();

        // Remove active state from all sidebar items
        document.querySelectorAll('.sidebar-nav .nav-item').forEach(item => {
            item.classList.remove('active');
        });

        // Hide all views
        document.querySelectorAll('.app-view').forEach(view => {
            view.classList.add('hidden');
        });

        // Activate matching view
        const activeView = document.getElementById(`view-${viewName}`);
        if (activeView) {
            activeView.classList.remove('hidden');
            
            // Highlight sidebar item
            const navItem = document.getElementById(`nav-${viewName}`);
            if (navItem) navItem.classList.add('active');
            
            // Set header title
            const headerTitle = document.getElementById('current-view-title');
            if (headerTitle) {
                const titles = {
                    'converter': 'Layout Converter',
                    'layouts': 'My Keyboard Layouts',
                    'editor': 'Layout Editor',
                    'marketplace': 'Layout Marketplace',
                    'history': 'Conversion History',
                    'profile': 'Profile & Statistics'
                };
                headerTitle.textContent = titles[viewName] || 'Smart Converter';
            }

            // Trigger view callbacks
            this.triggerViewCallback(viewName, hash);
        } else {
            // View not found, fallback
            document.getElementById('view-landing').classList.remove('hidden');
        }
        if (window.lucide) { window.lucide.createIcons(); }
    }

    triggerViewCallback(viewName, hash) {
        // Parse queries if any
        const queryParams = {};
        if (hash.includes('?')) {
            const queryStr = hash.split('?')[1];
            const pairs = queryStr.split('&');
            for (const pair of pairs) {
                const [key, val] = pair.split('=');
                queryParams[decodeURIComponent(key)] = decodeURIComponent(val || '');
            }
        }

        if (viewName === 'converter') {
            ConverterUI.onLoad(queryParams);
        } else if (viewName === 'layouts') {
            LayoutsManagerUI.loadUserLayouts();
        } else if (viewName === 'editor') {
            LayoutEditorUI.onLoad(queryParams);
        } else if (viewName === 'marketplace') {
            MarketplaceUI.onLoad();
        } else if (viewName === 'history') {
            HistoryUI.loadHistory();
        } else if (viewName === 'profile') {
            ProfileUI.onLoad();
        }
    }

    navigateTo(viewName, queries = null) {
        let path = `#${viewName}`;
        if (queries) {
            const queryStr = Object.keys(queries)
                .map(k => `${encodeURIComponent(k)}=${encodeURIComponent(queries[k])}`)
                .join('&');
            path += `?${queryStr}`;
        }
        window.location.hash = path;
    }

    toggleMobileSidebar() {
        const sidebar = document.querySelector('.app-sidebar');
        const backdrop = document.getElementById('sidebar-backdrop');
        if (sidebar.classList.contains('open')) {
            this.closeMobileSidebar();
        } else {
            sidebar.classList.add('open');
            if (backdrop) backdrop.classList.add('visible');
        }
    }

    closeMobileSidebar() {
        const sidebar = document.querySelector('.app-sidebar');
        const backdrop = document.getElementById('sidebar-backdrop');
        if (sidebar) sidebar.classList.remove('open');
        if (backdrop) backdrop.classList.remove('visible');
    }

    updateAuthStateUI() {
        const userBlock = document.getElementById('sidebar-user-block');
        const headerActions = document.getElementById('header-user-actions');
        
        user_repo_cleanup_elements(userBlock);
        user_repo_cleanup_elements(headerActions);

        if (this.user) {
            // RENDER USER BLOCK IN SIDEBAR SECURELY
            const avatar = document.createElement('div');
            avatar.className = 'user-avatar';
            if (this.user.profile_picture) {
                const img = document.createElement('img');
                img.src = this.user.profile_picture;
                img.alt = this.user.name || 'User Avatar';
                avatar.appendChild(img);
            } else {
                avatar.textContent = (this.user.name || this.user.email).substring(0, 2).toUpperCase();
            }
            
            const details = document.createElement('div');
            details.className = 'user-details';
            
            const nameSpan = document.createElement('span');
            nameSpan.className = 'user-name';
            nameSpan.textContent = this.user.name || 'User';
            
            const emailSpan = document.createElement('span');
            emailSpan.className = 'user-email';
            emailSpan.textContent = this.user.email;
            
            const logoutBtn = document.createElement('button');
            logoutBtn.className = 'btn-logout-sidebar';
            logoutBtn.textContent = 'Logout';
            logoutBtn.addEventListener('click', () => this.handleLogout());

            details.appendChild(nameSpan);
            details.appendChild(emailSpan);
            details.appendChild(logoutBtn);
            
            userBlock.appendChild(avatar);
            userBlock.appendChild(details);

            // Hide Landing View Link or customize
            document.getElementById('view-landing').classList.add('hidden');
        } else {
            // RENDER SIGN IN BUTTONS SECURELY
            const loginBtn = document.createElement('button');
            loginBtn.className = 'btn btn-secondary';
            loginBtn.textContent = 'Sign In';
            loginBtn.addEventListener('click', () => this.showAuthModal('login'));

            const registerBtn = document.createElement('button');
            registerBtn.className = 'btn btn-primary';
            registerBtn.textContent = 'Register';
            registerBtn.addEventListener('click', () => this.showAuthModal('register'));

            headerActions.appendChild(loginBtn);
            headerActions.appendChild(registerBtn);
            
            // Show inline guest message in sidebar
            const guestText = document.createElement('span');
            guestText.className = 'user-email';
            guestText.textContent = 'Guest Mode';
            userBlock.appendChild(guestText);
        }
        if (window.lucide) { window.lucide.createIcons(); }
    }

    async handleLogout() {
        try {
            await API.post('/api/auth/logout');
        } catch (e) {}
        
        localStorage.removeItem('user');
        this.user = null;
        this.toast("Logged out successfully.", "info");
        this.updateAuthStateUI();
        this.navigateTo('converter');
        
        // Full page reload on logout to clear local memory cache
        window.location.reload();
    }

    handleUnauthorized() {
        if (this.user) {
            this.user = null;
            localStorage.removeItem('user');
            this.toast("Session expired. Please log in again.", "error");
            this.updateAuthStateUI();
            this.navigateTo('converter');
        }
    }

    showAuthModal(mode = 'login', token = '') {
        const modal = document.getElementById('auth-modal');
        const title = document.getElementById('auth-modal-title');
        const loginForm = document.getElementById('login-form');
        const regForm = document.getElementById('register-form');
        const forgotForm = document.getElementById('forgot-form');
        const resetConfirmForm = document.getElementById('reset-confirm-form');
        const switchText = document.getElementById('auth-switch-text');
        const switchLink = document.getElementById('auth-switch-link');
        
        modal.classList.remove('hidden');
        
        if (mode === 'login') {
            title.textContent = "Sign In";
            loginForm.classList.remove('hidden');
            regForm.classList.add('hidden');
            forgotForm.classList.add('hidden');
            if (resetConfirmForm) resetConfirmForm.classList.add('hidden');
            switchText.textContent = "New user? ";
            switchLink.textContent = "Create an account";
        } else if (mode === 'register') {
            title.textContent = "Register";
            loginForm.classList.add('hidden');
            regForm.classList.remove('hidden');
            forgotForm.classList.add('hidden');
            if (resetConfirmForm) resetConfirmForm.classList.add('hidden');
            switchText.textContent = "Already have an account? ";
            switchLink.textContent = "Log In";
        } else if (mode === 'forgot') {
            title.textContent = "Forgot Password";
            loginForm.classList.add('hidden');
            regForm.classList.add('hidden');
            forgotForm.classList.remove('hidden');
            if (resetConfirmForm) resetConfirmForm.classList.add('hidden');
            switchText.textContent = "Remember password? ";
            switchLink.textContent = "Log In";
        } else if (mode === 'reset') {
            title.textContent = "Reset Password";
            loginForm.classList.add('hidden');
            regForm.classList.add('hidden');
            forgotForm.classList.add('hidden');
            if (resetConfirmForm) {
                resetConfirmForm.classList.remove('hidden');
                document.getElementById('reset-confirm-token').value = token;
                document.getElementById('reset-confirm-password').value = '';
            }
            switchText.textContent = "Want to try signing in? ";
            switchLink.textContent = "Log In";
        }
    }

    hideAuthModal() {
        document.getElementById('auth-modal').classList.add('hidden');
    }

    toast(message, type = 'info') {
        const container = document.getElementById('toast-holder');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = document.createElement('span');
        icon.className = 'toast-icon';
        const lucideName = type === 'success' ? 'check-circle' : type === 'error' ? 'x-circle' : 'info';
        icon.innerHTML = `<i data-lucide="${lucideName}" style="width: 16px; height: 16px;"></i>`;
        
        const textSpan = document.createElement('span');
        textSpan.textContent = message;

        toast.appendChild(icon);
        toast.appendChild(textSpan);
        container.appendChild(toast);
        if (window.lucide) { window.lucide.createIcons(); }

        // Remove toast after 4 seconds
        setTimeout(() => {
            toast.remove();
        }, 4000);
    }
}

// --- History View UI Manager ---
const HistoryUI = {
    async loadHistory() {
        const container = document.getElementById('history-rows-container');
        if (!container) return;

        container.replaceChildren();

        try {
            const res = await API.get('/api/history');
            const logs = await res.json();
            
            if (!res.ok) {
                app.toast(logs.error || "Failed to load conversion history", "error");
                return;
            }

            if (logs.length === 0) {
                const tr = document.createElement('tr');
                const td = document.createElement('td');
                td.setAttribute('colspan', '6');
                td.style.padding = '0';
                
                const emptyState = document.createElement('div');
                emptyState.className = 'empty-state';

                const icon = document.createElement('div');
                icon.className = 'empty-state-icon';
                icon.innerHTML = '<i data-lucide="clipboard-list" style="width: 48px; height: 48px;"></i>';

                const title = document.createElement('div');
                title.className = 'empty-state-title';
                title.textContent = 'No conversions yet';

                const desc = document.createElement('div');
                desc.className = 'empty-state-description';
                desc.textContent = 'Your conversion history will appear here once you start using the converter.';

                const cta = document.createElement('button');
                cta.className = 'btn btn-primary';
                cta.textContent = 'Go to Converter';
                cta.addEventListener('click', () => app.navigateTo('converter'));

                emptyState.appendChild(icon);
                emptyState.appendChild(title);
                emptyState.appendChild(desc);
                emptyState.appendChild(cta);
                td.appendChild(emptyState);
                tr.appendChild(td);
                container.appendChild(tr);
                return;
            }

            logs.forEach(log => {
                const tr = document.createElement('tr');

                const tdTime = document.createElement('td');
                tdTime.textContent = new Date(log.timestamp).toLocaleString();

                const tdLayout = document.createElement('td');
                tdLayout.textContent = log.layout_name || "Unknown Layout";

                const tdOrig = document.createElement('td');
                tdOrig.textContent = log.original_text.substring(0, 50) + (log.original_text.length > 50 ? '...' : '');

                const tdConv = document.createElement('td');
                tdConv.textContent = log.converted_text.substring(0, 50) + (log.converted_text.length > 50 ? '...' : '');

                const tdAi = document.createElement('td');
                tdAi.textContent = log.ai_enhanced_text ? (log.ai_enhanced_text.substring(0, 50) + (log.ai_enhanced_text.length > 50 ? '...' : '')) : '-';

                const tdActions = document.createElement('td');
                
                const btnCopy = document.createElement('button');
                btnCopy.className = 'btn btn-secondary btn-sm';
                btnCopy.textContent = 'Copy';
                btnCopy.addEventListener('click', () => {
                    navigator.clipboard.writeText(log.converted_text);
                    app.toast("Converted text copied!", "success");
                });

                const btnDel = document.createElement('button');
                btnDel.className = 'btn btn-danger btn-sm';
                btnDel.textContent = '×';
                btnDel.addEventListener('click', async () => {
                    const delRes = await API.delete(`/api/history/${log.id}`);
                    if (delRes.ok) {
                        app.toast("Entry removed", "info");
                        this.loadHistory();
                    }
                });

                tdActions.appendChild(btnCopy);
                tdActions.appendChild(document.createTextNode(" "));
                tdActions.appendChild(btnDel);

                tr.appendChild(tdTime);
                tr.appendChild(tdLayout);
                tr.appendChild(tdOrig);
                tr.appendChild(tdConv);
                tr.appendChild(tdAi);
                tr.appendChild(tdActions);

                container.appendChild(tr);
            });
            if (window.lucide) { window.lucide.createIcons(); }
        } catch (e) {
            app.toast("Failed to load history list.", "error");
        }
    },

    setupDone: false,
    setup() {
        if (this.setupDone) return;
        
        const clearBtn = document.getElementById('btn-clear-history-all');
        if (clearBtn) {
            clearBtn.addEventListener('click', async () => {
                const res = await API.delete('/api/history/clear');
                if (res.ok) {
                    app.toast("History cleared successfully.", "success");
                    this.loadHistory();
                } else {
                    app.toast("Failed to clear history", "error");
                }
            });
        }
        this.setupDone = true;
    }
};

// --- Profile & Stats UI Manager ---
const ProfileUI = {
    setupDone: false,

    onLoad() {
        this.setupUI();
        this.loadProfileDetails();
        this.loadStatsAndFavorites();
    },

    setupUI() {
        // Run setup events once
        if (this.setupDone) return;
        HistoryUI.setup();

        const profileForm = document.getElementById('profile-update-form');
        if (profileForm) {
            profileForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const name = document.getElementById('profile-name').value.trim();
                const currPass = document.getElementById('profile-curr-pass').value;
                const newPass = document.getElementById('profile-new-pass').value;

                const payload = { name };
                if (newPass) {
                    payload.current_password = currPass;
                    payload.new_password = newPass;
                }

                try {
                    const res = await API.put('/api/auth/profile', payload);
                    const data = await res.json();
                    
                    if (res.ok) {
                        app.toast("Account details updated successfully!", "success");
                        // Refresh profile state
                        await app.refreshUserProfile();
                        app.updateAuthStateUI();
                        
                        // Clear password inputs
                        document.getElementById('profile-curr-pass').value = '';
                        document.getElementById('profile-new-pass').value = '';
                    } else {
                        app.toast(data.error || "Failed to update profile", "error");
                    }
                } catch (err) {
                    app.toast("Failed to save changes", "error");
                }
            });
        }

        const aiForm = document.getElementById('profile-ai-settings-form');
        if (aiForm) {
            aiForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const payload = {
                    preferred_model: document.getElementById('profile-ai-model').value,
                    temperature: parseFloat(document.getElementById('profile-ai-temp').value),
                    prompt_prefix: document.getElementById('profile-ai-prompt').value.trim()
                };

                try {
                    const res = await API.put('/api/auth/ai-settings', payload);
                    if (res.ok) {
                        app.toast("AI preferences saved successfully!", "success");
                        await app.refreshUserProfile();
                    } else {
                        app.toast("Failed to update AI settings", "error");
                    }
                } catch (err) {
                    app.toast("Connection failed", "error");
                }
            });
        }

        // AI Temp slider profile
        const range = document.getElementById('profile-ai-temp');
        const display = document.getElementById('profile-temp-val');
        if (range && display) {
            range.addEventListener('input', (e) => {
                display.textContent = e.target.value;
            });
        }

        // Resend Verification Email handler
        const resendBtn = document.getElementById('btn-profile-resend-verification');
        if (resendBtn) {
            resendBtn.addEventListener('click', async () => {
                resendBtn.disabled = true;
                resendBtn.textContent = 'Sending...';
                try {
                    const res = await API.post('/api/auth/resend-verification');
                    const data = await res.json();
                    if (res.ok) {
                        app.toast(data.message || "Verification email sent!", "success");
                    } else {
                        app.toast(data.error || "Failed to resend verification email.", "error");
                    }
                } catch (e) {
                    app.toast("Failed to resend verification email due to connection error.", "error");
                } finally {
                    resendBtn.disabled = false;
                    resendBtn.textContent = 'Resend Email';
                }
            });
        }

        // Avatar Upload Handler
        const avatarInput = document.getElementById('avatar-input');
        if (avatarInput) {
            avatarInput.addEventListener('change', async (e) => {
                const file = e.target.files[0];
                if (!file) return;

                if (file.size > 2 * 1024 * 1024) {
                    app.toast("File size exceeds the 2MB limit.", "error");
                    avatarInput.value = '';
                    return;
                }

                const formData = new FormData();
                formData.append('avatar', file);

                try {
                    app.toast("Uploading profile picture...", "info");
                    const res = await API.post('/api/auth/profile/avatar', formData);
                    const data = await res.json();
                    
                    if (res.ok) {
                        app.toast("Profile picture updated successfully!", "success");
                        await app.refreshUserProfile();
                        app.updateAuthStateUI();
                        this.loadProfileDetails();
                    } else {
                        app.toast(data.error || "Failed to upload profile picture.", "error");
                    }
                } catch (err) {
                    app.toast("Failed to upload profile picture due to connection error.", "error");
                } finally {
                    avatarInput.value = '';
                }
            });
        }

        this.setupDone = true;
    },

    loadProfileDetails() {
        if (!app.user) return;
        document.getElementById('profile-email').value = app.user.email;
        document.getElementById('profile-name').value = app.user.name || '';

        // Render profile page avatar preview
        const avatarPreview = document.getElementById('profile-avatar-preview');
        const avatarFallback = document.getElementById('profile-avatar-fallback');
        const avatarImg = document.getElementById('profile-avatar-img');
        
        if (avatarPreview && avatarFallback && avatarImg) {
            if (app.user.profile_picture) {
                avatarImg.src = app.user.profile_picture;
                avatarImg.classList.remove('hidden');
                avatarFallback.classList.add('hidden');
            } else {
                avatarImg.classList.add('hidden');
                avatarFallback.classList.remove('hidden');
                avatarFallback.textContent = (app.user.name || app.user.email).substring(0, 2).toUpperCase();
            }
        }

        // Render account verification status
        const isVerified = app.user.is_verified;
        const badge = document.getElementById('profile-verification-badge');
        const resendBtn = document.getElementById('btn-profile-resend-verification');
        if (badge) {
            badge.replaceChildren();
            if (isVerified) {
                badge.innerHTML = '<i data-lucide="check-circle" style="width: 14px; height: 14px; display: inline-block; vertical-align: middle; margin-right: 4px;"></i> Verified';
                badge.className = "badge success";
                if (resendBtn) resendBtn.classList.add('hidden');
            } else {
                badge.innerHTML = '<i data-lucide="x-circle" style="width: 14px; height: 14px; display: inline-block; vertical-align: middle; margin-right: 4px;"></i> Not Verified';
                badge.className = "badge danger";
                if (resendBtn) resendBtn.classList.remove('hidden');
            }
        }
        if (window.lucide) { window.lucide.createIcons(); }

        // Disable or load AI Settings options based on global enablement
        const aiEnabled = app.aiConfig.ai_enabled;
        const aiCard = document.getElementById('profile-ai-settings-card');
        
        if (!aiEnabled) {
            if (aiCard) aiCard.classList.add('hidden');
            return;
        }
        
        if (aiCard) aiCard.classList.remove('hidden');

        // Populate model select in profile
        const modelSelect = document.getElementById('profile-ai-model');
        if (modelSelect) {
            modelSelect.replaceChildren();
            app.aiConfig.available_models.forEach(model => {
                const opt = document.createElement('option');
                opt.value = model.id;
                opt.textContent = model.name;
                modelSelect.appendChild(opt);
            });
        }

        // Set user current settings
        const settings = app.user.ai_settings || {};
        if (settings.preferred_model) {
            document.getElementById('profile-ai-model').value = settings.preferred_model;
        }
        if (settings.temperature !== undefined) {
            document.getElementById('profile-ai-temp').value = settings.temperature;
            document.getElementById('profile-temp-val').textContent = settings.temperature;
        }
        if (settings.prompt_prefix) {
            document.getElementById('profile-ai-prompt').value = settings.prompt_prefix;
        }
    },

    async loadStatsAndFavorites() {
        // Load stats counters
        try {
            const res = await API.get('/api/auth/stats');
            if (res.ok) {
                const stats = await res.json();
                document.getElementById('stat-total-conversions').textContent = stats.total_conversions || 0;
                document.getElementById('stat-total-chars').textContent = stats.total_chars_converted || 0;
                document.getElementById('stat-layouts-count').textContent = stats.layouts_count || 0;
            }
        } catch (e) {}

        // Load favorites list
        const favContainer = document.getElementById('profile-favorites-container');
        if (!favContainer) return;

        favContainer.replaceChildren();

        try {
            const favRes = await API.get('/api/marketplace/favorites');
            if (favRes.ok) {
                const favs = await favRes.json();
                if (favs.length === 0) {
                    const emptyState = document.createElement('div');
                    emptyState.className = 'empty-state';
                    emptyState.style.padding = 'var(--space-7) var(--space-4)';

                    const icon = document.createElement('div');
                    icon.className = 'empty-state-icon';
                    icon.innerHTML = '<i data-lucide="star" style="width: 48px; height: 48px;"></i>';

                    const title = document.createElement('div');
                    title.className = 'empty-state-title';
                    title.textContent = 'No favorites yet';

                    const desc = document.createElement('div');
                    desc.className = 'empty-state-description';
                    desc.textContent = 'Browse the marketplace and favorite layouts you love.';

                    emptyState.appendChild(icon);
                    emptyState.appendChild(title);
                    emptyState.appendChild(desc);
                    favContainer.appendChild(emptyState);
                    return;
                }

                favs.forEach(layout => {
                    const item = document.createElement('div');
                    item.className = 'card-meta-line';
                    item.style.padding = '8px 0';
                    item.style.borderBottom = '1px dashed var(--border-secondary)';
                    item.style.justifyContent = 'space-between';

                    const nameSpan = document.createElement('span');
                    nameSpan.textContent = layout.name;
                    nameSpan.style.cursor = 'pointer';
                    nameSpan.style.fontWeight = '600';
                    nameSpan.addEventListener('click', () => {
                        app.navigateTo('converter', { layout: layout.layout_id || layout.id });
                    });

                    const lang = document.createElement('span');
                    lang.className = 'badge';
                    lang.textContent = layout.language;

                    item.appendChild(nameSpan);
                    item.appendChild(lang);
                    favContainer.appendChild(item);
                });
            }
            if (window.lucide) { window.lucide.createIcons(); }
        } catch (err) {}
    }
};

// Security cleanups
function user_repo_cleanup_elements(el) {
    if (el) {
        while (el.firstChild) {
            el.removeChild(el.firstChild);
        }
    }
}

// Instantiate Global Controller
const app = new AppController();
