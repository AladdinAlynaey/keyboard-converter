/**
 * Smart Keyboard Converter AI - Marketplace UI Handler
 * Implements public layout search, rating star selectors, and community comments.
 */

const MarketplaceUI = {
    selectedLayoutId: null,
    languages: [],
    
    setupDone: false,

    onLoad() {
        this.setupUI();
        this.fetchLanguages();
        this.searchMarketplace();
    },

    setupUI() {
        if (this.setupDone) return;

        // Search inputs
        const searchInput = document.getElementById('marketplace-search-input');
        if (searchInput) {
            // Debounce search
            let timer;
            searchInput.addEventListener('input', () => {
                clearTimeout(timer);
                timer = setTimeout(() => this.searchMarketplace(), 400);
            });
        }

        // Filters switch
        const langFilter = document.getElementById('marketplace-filter-lang');
        if (langFilter) {
            langFilter.addEventListener('change', () => this.searchMarketplace());
        }

        const sortSelect = document.getElementById('marketplace-sort-select');
        if (sortSelect) {
            sortSelect.addEventListener('change', () => this.searchMarketplace());
        }

        // Close details modal
        const closeBtn = document.getElementById('marketplace-detail-close-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                document.getElementById('marketplace-detail-modal').classList.add('hidden');
            });
        }

        // Post comment click
        const commentBtn = document.getElementById('btn-md-post-comment');
        if (commentBtn) {
            commentBtn.addEventListener('click', () => this.postComment());
        }

        // Favorite click details
        const favBtn = document.getElementById('btn-md-favorite');
        if (favBtn) {
            favBtn.addEventListener('click', () => this.toggleFavoriteInDetails());
        }

        // Download layout details
        const dlBtn = document.getElementById('btn-md-download');
        if (dlBtn) {
            dlBtn.addEventListener('click', () => this.downloadLayoutFromDetails());
        }

        // Stars rating selector with hover effects
        const stars = document.querySelectorAll('#stars-rating-selector .star-item');
        stars.forEach(star => {
            star.addEventListener('click', (e) => {
                const rating = parseInt(e.target.dataset.rating);
                this.submitRating(rating);
            });
            star.addEventListener('mouseenter', (e) => {
                const currentRating = parseInt(e.target.dataset.rating);
                stars.forEach(s => {
                    if (parseInt(s.dataset.rating) <= currentRating) {
                        s.classList.add('hovered');
                    } else {
                        s.classList.remove('hovered');
                    }
                });
            });
        });

        const starSelector = document.getElementById('stars-rating-selector');
        if (starSelector) {
            starSelector.addEventListener('mouseleave', () => {
                stars.forEach(s => s.classList.remove('hovered'));
            });
        }

        this.setupDone = true;
    },

    async fetchLanguages() {
        // Build language filters list dynamically by scanning database
        try {
            const res = await API.get('/api/marketplace');
            if (res.ok) {
                const layouts = await res.json();
                const langSet = new Set();
                layouts.forEach(l => {
                    if (l.language) langSet.add(l.language);
                });
                
                const langFilter = document.getElementById('marketplace-filter-lang');
                if (langFilter) {
                    // Save first element (All)
                    const firstOpt = langFilter.options[0];
                    langFilter.replaceChildren();
                    langFilter.appendChild(firstOpt);
                    
                    langSet.forEach(lang => {
                        const opt = document.createElement('option');
                        opt.value = lang;
                        opt.textContent = lang;
                        langFilter.appendChild(opt);
                    });
                }
            }
        } catch (e) {}
    },

    async searchMarketplace() {
        const container = document.getElementById('marketplace-cards-container');
        if (!container) return;

        container.replaceChildren();

        // Show skeleton loader placeholders while loading
        for (let i = 0; i < 3; i++) {
            const skel = document.createElement('div');
            skel.className = 'skeleton skeleton-card';
            container.appendChild(skel);
        }

        const query = document.getElementById('marketplace-search-input').value;
        const language = document.getElementById('marketplace-filter-lang').value;
        const sortBy = document.getElementById('marketplace-sort-select').value;

        try {
            const url = `/api/marketplace?q=${encodeURIComponent(query)}&language=${encodeURIComponent(language)}&sort_by=${sortBy}`;
            const res = await API.get(url);
            const layouts = await res.json();
            
            // Clear skeletons
            container.replaceChildren();

            if (!res.ok) {
                app.toast("Failed to load marketplace layouts", "error");
                return;
            }

            if (layouts.length === 0) {
                const emptyState = document.createElement('div');
                emptyState.className = 'empty-state';
                emptyState.style.gridColumn = '1 / -1';

                const icon = document.createElement('div');
                icon.className = 'empty-state-icon';
                icon.innerHTML = '<i data-lucide="search" style="width: 48px; height: 48px;"></i>';

                const title = document.createElement('div');
                title.className = 'empty-state-title';
                title.textContent = 'No layouts found';

                const desc = document.createElement('div');
                desc.className = 'empty-state-description';
                desc.textContent = 'Try adjusting your search terms or filters to find what you\'re looking for.';

                emptyState.appendChild(icon);
                emptyState.appendChild(title);
                emptyState.appendChild(desc);
                container.appendChild(emptyState);
                return;
            }

            layouts.forEach(layout => {
                const card = this.createMarketplaceCard(layout);
                container.appendChild(card);
            });
            if (window.lucide) { window.lucide.createIcons(); }
        } catch (err) {
            container.replaceChildren();
            app.toast("Marketplace connection error", "error");
        }
    },

    createMarketplaceCard(layout) {
        const card = document.createElement('div');
        card.className = 'layout-card';

        const title = document.createElement('h3');
        title.textContent = layout.name;
        card.appendChild(title);

        // Subtitle with creator name and avatar
        const creatorLine = document.createElement('div');
        creatorLine.className = 'card-creator-line';
        
        const avatarSpan = document.createElement('div');
        avatarSpan.className = 'card-creator-avatar';
        if (layout.creator_avatar) {
            const avatarImg = document.createElement('img');
            avatarImg.src = layout.creator_avatar;
            avatarImg.alt = layout.creator_name || 'Creator';
            avatarSpan.appendChild(avatarImg);
        } else {
            avatarSpan.textContent = (layout.creator_name || 'A').substring(0, 1).toUpperCase();
        }
        
        creatorLine.appendChild(avatarSpan);
        
        const nameText = document.createTextNode(` by ${layout.creator_name || 'Anonymous'}`);
        creatorLine.appendChild(nameText);
        
        card.appendChild(creatorLine);

        const metaLine = document.createElement('div');
        metaLine.className = 'card-meta-line';
        
        const langBadge = document.createElement('span');
        langBadge.className = 'badge badge-lang';
        langBadge.textContent = layout.language;
        
        const downloads = document.createElement('span');
        downloads.className = 'badge badge-dl';
        downloads.innerHTML = `<i data-lucide="download" style="width: 12px; height: 12px; display: inline-block; vertical-align: middle; margin-right: 3px;"></i> ${layout.downloads || 0}`;

        const likes = document.createElement('span');
        likes.className = 'badge badge-likes';
        likes.innerHTML = `<i data-lucide="heart" style="width: 12px; height: 12px; display: inline-block; vertical-align: middle; margin-right: 3px; fill: var(--error-text);"></i> ${layout.likes || 0}`;

        const rating = document.createElement('span');
        rating.className = 'badge badge-rating';
        rating.innerHTML = `<i data-lucide="star" style="width: 12px; height: 12px; display: inline-block; vertical-align: middle; margin-right: 3px; fill: var(--warning-text); stroke: var(--warning-text);"></i> ${layout.average_rating || '0.0'} (${layout.ratings_count || 0})`;

        metaLine.appendChild(langBadge);
        metaLine.appendChild(downloads);
        metaLine.appendChild(likes);
        metaLine.appendChild(rating);
        card.appendChild(metaLine);

        if (layout.description) {
            const desc = document.createElement('p');
            desc.textContent = layout.description;
            card.appendChild(desc);
        }

        const footer = document.createElement('div');
        footer.className = 'card-footer-actions';
        
        const viewBtn = document.createElement('button');
        viewBtn.className = 'btn btn-primary btn-sm';
        viewBtn.textContent = 'View Details';
        viewBtn.addEventListener('click', () => this.showLayoutDetails(layout.layout_id));
        
        footer.appendChild(viewBtn);
        card.appendChild(footer);

        return card;
    },

    async showLayoutDetails(layoutId) {
        this.selectedLayoutId = layoutId;
        
        try {
            const res = await API.get(`/api/marketplace/${layoutId}`);
            if (!res.ok) {
                app.toast("Failed to load layout details", "error");
                return;
            }
            const layout = await res.json();
            
            document.getElementById('md-layout-name').textContent = layout.name;
            document.getElementById('md-layout-desc').textContent = layout.description || 'No description provided.';
            document.getElementById('md-layout-lang').textContent = layout.language;
            document.getElementById('md-layout-downloads').textContent = layout.downloads || 0;
            document.getElementById('md-layout-likes').textContent = layout.likes || 0;
            document.getElementById('md-layout-rating').textContent = `${layout.average_rating || '0.0'}/5 (${layout.ratings_count || 0})`;
            document.getElementById('md-layout-creator').textContent = layout.creator_name || 'Anonymous';

            // Populate publisher avatar
            const creatorFallback = document.getElementById('md-creator-fallback');
            const creatorImg = document.getElementById('md-creator-img');
            if (creatorFallback && creatorImg) {
                if (layout.creator_avatar) {
                    creatorImg.src = layout.creator_avatar;
                    creatorImg.classList.remove('hidden');
                    creatorFallback.classList.add('hidden');
                } else {
                    creatorImg.classList.add('hidden');
                    creatorFallback.classList.remove('hidden');
                    creatorFallback.textContent = (layout.creator_name || 'A').substring(0, 1).toUpperCase();
                }
            }

            // Update rating star display if logged in
            this.resetStarDisplay();
            if (app.user) {
                try {
                    const ratingRes = await API.get(`/api/marketplace/${layout.layout_id}/my-rating`);
                    if (ratingRes.ok) {
                        const ratingData = await ratingRes.json();
                        this.setStarDisplay(ratingData.rating);
                    }
                } catch (e) {}
            }

            // Load comments feed
            await this.loadComments();

            // Update details favorite button text
            const favBtn = document.getElementById('btn-md-favorite');
            if (favBtn) {
                if (layout.is_favorite) {
                    favBtn.innerHTML = '<i data-lucide="star" style="width: 16px; height: 16px; fill: currentColor;"></i> Favorited';
                } else {
                    favBtn.innerHTML = '<i data-lucide="star" style="width: 16px; height: 16px;"></i> Favorite';
                }
            }

            document.getElementById('marketplace-detail-modal').classList.remove('hidden');
            if (window.lucide) { window.lucide.createIcons(); }
        } catch (err) {
            app.toast("Failed to load layout details", "error");
        }
    },

    async loadComments() {
        const feed = document.getElementById('md-comments-feed');
        const countSpan = document.getElementById('md-comments-count');
        if (!feed) return;

        feed.replaceChildren();

        try {
            const res = await API.get(`/api/marketplace/${this.selectedLayoutId}/comments`);
            if (res.ok) {
                const comments = await res.json();
                countSpan.textContent = comments.length;

                if (comments.length === 0) {
                    const emptyState = document.createElement('div');
                    emptyState.className = 'empty-state';
                    emptyState.style.padding = 'var(--space-7) var(--space-4)';

                    const icon = document.createElement('div');
                    icon.className = 'empty-state-icon';
                    icon.innerHTML = '<i data-lucide="message-square" style="width: 48px; height: 48px;"></i>';

                    const title = document.createElement('div');
                    title.className = 'empty-state-title';
                    title.textContent = 'No comments yet';

                    const desc = document.createElement('div');
                    desc.className = 'empty-state-description';
                    desc.textContent = 'Be the first to share your thoughts about this layout.';

                    emptyState.appendChild(icon);
                    emptyState.appendChild(title);
                    emptyState.appendChild(desc);
                    feed.appendChild(emptyState);
                    return;
                }

                comments.forEach((comment, index) => {
                    const item = document.createElement('div');
                    item.className = 'comment-item';
                    
                    if (index >= 3) {
                        item.classList.add('collapsed-comment', 'hidden');
                    }

                    // Create comment avatar block on the left
                    const avatarSpan = document.createElement('div');
                    avatarSpan.className = 'comment-avatar';
                    if (comment.creator_avatar) {
                        const avatarImg = document.createElement('img');
                        avatarImg.src = comment.creator_avatar;
                        avatarImg.alt = comment.creator_name || 'Commenter';
                        avatarSpan.appendChild(avatarImg);
                    } else {
                        avatarSpan.textContent = (comment.creator_name || 'A').substring(0, 1).toUpperCase();
                    }
                    item.appendChild(avatarSpan);

                    // Create details container on the right
                    const details = document.createElement('div');
                    details.className = 'comment-details';

                    const meta = document.createElement('div');
                    meta.className = 'comment-meta';

                    const author = document.createElement('span');
                    author.className = 'comment-author';
                    author.textContent = comment.creator_name;

                    const date = document.createElement('span');
                    date.textContent = new Date(comment.timestamp).toLocaleDateString();

                    meta.appendChild(author);
                    meta.appendChild(date);
                    details.appendChild(meta);

                    const content = document.createElement('div');
                    content.className = 'comment-content';
                    content.textContent = comment.content;
                    details.appendChild(content);

                    // If comment is own, allow delete
                    if (app.user && app.user.id === comment.user_id) {
                        const delBtn = document.createElement('button');
                        delBtn.className = 'btn-logout-sidebar';
                        delBtn.textContent = 'Delete';
                        delBtn.style.float = 'right';
                        delBtn.addEventListener('click', async () => {
                            const delRes = await API.delete(`/api/marketplace/comments/${comment.id}`);
                            if (delRes.ok) {
                                app.toast("Comment deleted", "info");
                                this.loadComments();
                            }
                        });
                        meta.appendChild(delBtn);
                    }

                    item.appendChild(details);
                    feed.appendChild(item);
                });

                // Add toggle button if more than 3 comments
                if (comments.length > 3) {
                    const toggleBtn = document.createElement('button');
                    toggleBtn.className = 'btn btn-secondary btn-sm btn-full margin-top-sm';
                    toggleBtn.textContent = `Show More (${comments.length - 3} more)`;
                    toggleBtn.style.width = '100%';
                    toggleBtn.style.justifyContent = 'center';
                    toggleBtn.addEventListener('click', () => {
                        const hiddenComments = feed.querySelectorAll('.collapsed-comment');
                        const isExpanded = toggleBtn.dataset.expanded === 'true';
                        if (isExpanded) {
                            hiddenComments.forEach(c => c.classList.add('hidden'));
                            toggleBtn.textContent = `Show More (${comments.length - 3} more)`;
                            toggleBtn.dataset.expanded = 'false';
                        } else {
                            hiddenComments.forEach(c => c.classList.remove('hidden'));
                            toggleBtn.textContent = 'Show Less';
                            toggleBtn.dataset.expanded = 'true';
                        }
                    });
                    feed.appendChild(toggleBtn);
                }
            }
            if (window.lucide) { window.lucide.createIcons(); }
        } catch (e) {}
    },

    async postComment() {
        if (!app.user) {
            app.toast("Please log in to write comments", "error");
            return;
        }

        // Email verification check
        if (!app.user.is_verified) {
            app.toast("You must verify your email address to post comments.", "error");
            return;
        }

        const input = document.getElementById('marketplace-comment-input');
        const content = input.value.trim();
        
        if (!content) return;

        try {
            const res = await API.post(`/api/marketplace/${this.selectedLayoutId}/comments`, { content });
            if (res.ok) {
                input.value = '';
                app.toast("Comment posted!", "success");
                await this.loadComments();
            } else {
                const data = await res.json();
                app.toast(data.error || "Failed to post comment", "error");
            }
        } catch (err) {
            app.toast("Connection failed", "error");
        }
    },

    async toggleFavoriteInDetails() {
        if (!app.user) {
            app.toast("Please log in to favorite layouts", "error");
            return;
        }

        try {
            const res = await API.post(`/api/marketplace/${this.selectedLayoutId}/favorite`);
            const data = await res.json();
            
            if (res.ok) {
                app.toast(data.status === 'added' ? "Added to favorites" : "Removed from favorites", "info");
                await this.showLayoutDetails(this.selectedLayoutId); // Refresh details modal dynamically
                this.searchMarketplace(); // Refresh marketplace view
            }
        } catch (e) {
            app.toast("Connection failed", "error");
        }
    },

    async downloadLayoutFromDetails() {
        if (!app.user) {
            app.toast("Please log in to import layouts", "error");
            return;
        }

        try {
            // Increment download count first
            await API.post(`/api/marketplace/${this.selectedLayoutId}/download`);

            // Fetch detail mapping json to save in user private lists
            const res = await API.get(`/api/layouts/${this.selectedLayoutId}/export`);
            const layoutData = await res.json();

            if (res.ok) {
                // Import to user layouts database
                const importRes = await API.post('/api/layouts/import', { layout_json: layoutData });
                const importData = await importRes.json();
                
                if (importRes.ok) {
                    app.toast(`Layout imported successfully as "${importData.name}"!`, "success");
                    this.searchMarketplace(); // Refresh download counter in details modal
                    
                    // Close details modal
                    document.getElementById('marketplace-detail-modal').classList.add('hidden');
                    
                    // Redirect to editor
                    app.navigateTo('editor', { id: importData.id });
                } else {
                    app.toast(importData.error || "Failed to save imported layout", "error");
                }
            }
        } catch (e) {
            app.toast("Import process failed", "error");
        }
    },

    async submitRating(rating) {
        if (!app.user) {
            app.toast("Please sign in to rate layouts.", "info");
            app.showAuthModal('login');
            return;
        }

        // Email verification check
        if (!app.user.is_verified) {
            app.toast("You must verify your email address to submit ratings.", "warning");
            app.navigateTo('profile');
            return;
        }

        try {
            const res = await API.post(`/api/marketplace/${this.selectedLayoutId}/rate`, { rating });
            
            if (res.ok) {
                app.toast("Rating submitted successfully!", "success");
                await this.showLayoutDetails(this.selectedLayoutId); // Refresh details modal dynamically
                this.searchMarketplace(); // Refresh cards view
            } else {
                const data = await res.json();
                app.toast(data.error || "Rating submission failed", "error");
            }
        } catch (err) {
            app.toast("Connection failed", "error");
        }
    },

    resetStarDisplay() {
        document.querySelectorAll('#stars-rating-selector .star-item').forEach(star => {
            star.classList.remove('active');
        });
    },

    setStarDisplay(rating) {
        this.resetStarDisplay();
        document.querySelectorAll('#stars-rating-selector .star-item').forEach(star => {
            if (parseInt(star.dataset.rating) <= rating) {
                star.classList.add('active');
            }
        });
    }
};
