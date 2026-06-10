/**
 * Smart Keyboard Converter AI - Keyboard Layout Builder UI Handler
 * Implements CRUD, duplication, JSON import/export, and verified email checks.
 */

const LayoutsManagerUI = {
    async loadUserLayouts() {
        const container = document.getElementById('layouts-cards-container');
        if (!container) return;

        // Clear container securely
        container.replaceChildren();

        try {
            const res = await API.get('/api/layouts');
            const layouts = await res.json();
            
            if (!res.ok) {
                app.toast(layouts.error || "Failed to load layouts", "error");
                return;
            }

            if (layouts.length === 0) {
                const emptyMsg = document.createElement('div');
                emptyMsg.className = 'card placeholder-text';
                emptyMsg.textContent = "You don't have any custom keyboard layouts yet. Click Add New Layout to create one!";
                container.appendChild(emptyMsg);
            } else {
                layouts.forEach(layout => {
                    const card = this.createLayoutCard(layout);
                    container.appendChild(card);
                });
            }
            
            // Draw default system templates
            this.renderSystemTemplates();
        } catch (err) {
            app.toast("Error contacting database", "error");
        }
    },

    renderSystemTemplates() {
        const container = document.getElementById('system-templates-container');
        if (!container) return;

        container.replaceChildren();

        const templates = [
            {
                id: 'default_en_ar',
                name: 'English to Arabic (PC Default)',
                language: 'Arabic',
                direction: 'rtl',
                description: 'Standard English to Arabic layout PC mapping template.',
                mapping: typeof LOCAL_DEFAULT_EN_AR_MAPPING !== 'undefined' ? LOCAL_DEFAULT_EN_AR_MAPPING : {}
            },
            {
                id: 'default_ar_en',
                name: 'Arabic to English (PC Default)',
                language: 'English',
                direction: 'ltr',
                description: 'Standard Arabic to English layout PC mapping template.',
                mapping: typeof LOCAL_DEFAULT_AR_EN_MAPPING !== 'undefined' ? LOCAL_DEFAULT_AR_EN_MAPPING : {}
            }
        ];

        templates.forEach(tpl => {
            const card = document.createElement('div');
            card.className = 'layout-card';

            const title = document.createElement('h3');
            title.textContent = tpl.name;
            card.appendChild(title);

            const metaLine = document.createElement('div');
            metaLine.className = 'card-meta-line';

            const langBadge = document.createElement('span');
            langBadge.className = 'badge';
            langBadge.textContent = tpl.language;

            const charsBadge = document.createElement('span');
            charsBadge.className = 'badge';
            charsBadge.textContent = `${Object.keys(tpl.mapping).length} characters`;

            const sysBadge = document.createElement('span');
            sysBadge.className = 'badge';
            sysBadge.textContent = '⚙️ System Preset';

            metaLine.appendChild(langBadge);
            metaLine.appendChild(charsBadge);
            metaLine.appendChild(sysBadge);
            card.appendChild(metaLine);

            const desc = document.createElement('p');
            desc.textContent = tpl.description;
            card.appendChild(desc);

            const footer = document.createElement('div');
            footer.className = 'card-footer-actions';

            const btnImport = document.createElement('button');
            btnImport.className = 'btn btn-primary btn-sm';
            btnImport.textContent = '📥 Import Template';
            btnImport.addEventListener('click', () => this.importSystemTemplate(tpl));

            footer.appendChild(btnImport);
            card.appendChild(footer);

            container.appendChild(card);
        });
    },

    async importSystemTemplate(tpl) {
        try {
            const payload = {
                name: tpl.name,
                language: tpl.language,
                description: tpl.description,
                direction: tpl.direction,
                mapping: tpl.mapping
            };

            const res = await API.post('/api/layouts/import', { layout_json: payload });
            const data = await res.json();

            if (res.ok) {
                app.toast(`Template imported successfully as "${data.name}"!`, "success");
                app.navigateTo('editor', { id: data.id });
            } else {
                app.toast(data.error || "Failed to import template layout", "error");
            }
        } catch (err) {
            app.toast("Failed to import template mapping.", "error");
        }
    },

    createLayoutCard(layout) {
        const card = document.createElement('div');
        card.className = 'layout-card';

        const title = document.createElement('h3');
        title.textContent = layout.name;
        card.appendChild(title);

        const metaLine = document.createElement('div');
        metaLine.className = 'card-meta-line';
        
        const langBadge = document.createElement('span');
        langBadge.className = 'badge';
        langBadge.textContent = layout.language;
        
        const charsBadge = document.createElement('span');
        charsBadge.className = 'badge';
        charsBadge.textContent = `${Object.keys(layout.mapping).length} characters`;

        const publicBadge = document.createElement('span');
        publicBadge.className = `badge ${layout.is_public ? 'success' : ''}`;
        publicBadge.textContent = layout.is_public ? '🌐 Public' : '🔒 Private';
        
        metaLine.appendChild(langBadge);
        metaLine.appendChild(charsBadge);
        metaLine.appendChild(publicBadge);
        card.appendChild(metaLine);

        if (layout.description) {
            const desc = document.createElement('p');
            desc.textContent = layout.description;
            card.appendChild(desc);
        }

        // Action panel
        const footer = document.createElement('div');
        footer.className = 'card-footer-actions';

        const btnEdit = document.createElement('button');
        btnEdit.className = 'btn btn-secondary btn-sm';
        btnEdit.textContent = '✏️ Edit';
        btnEdit.addEventListener('click', () => {
            app.navigateTo('editor', { id: layout.id });
        });

        const btnDup = document.createElement('button');
        btnDup.className = 'btn btn-secondary btn-sm';
        btnDup.textContent = '📋 Clone';
        btnDup.addEventListener('click', () => this.duplicateLayout(layout.id, layout.name));

        const btnExport = document.createElement('button');
        btnExport.className = 'btn btn-secondary btn-sm';
        btnExport.textContent = '📤 Export';
        btnExport.addEventListener('click', () => this.exportLayout(layout));

        const btnPub = document.createElement('button');
        btnPub.className = `btn ${layout.is_public ? 'btn-danger' : 'btn-primary'} btn-sm`;
        btnPub.textContent = layout.is_public ? '🔒 Unpublish' : '🌐 Publish';
        btnPub.addEventListener('click', () => this.togglePublish(layout));

        const btnDel = document.createElement('button');
        btnDel.className = 'btn btn-danger btn-sm';
        btnDel.textContent = '🗑️ Delete';
        btnDel.addEventListener('click', () => this.deleteLayout(layout.id));

        footer.appendChild(btnEdit);
        footer.appendChild(btnDup);
        footer.appendChild(btnExport);
        footer.appendChild(btnPub);
        footer.appendChild(btnDel);
        card.appendChild(footer);

        return card;
    },

    async duplicateLayout(id, originalName) {
        try {
            const newName = `${originalName} (Copy)`;
            const res = await API.post(`/api/layouts/${id}/duplicate`, { name: newName });
            const data = await res.json();
            
            if (res.ok) {
                app.toast("Layout duplicated successfully!", "success");
                this.loadUserLayouts();
            } else {
                app.toast(data.error || "Duplication failed", "error");
            }
        } catch (e) {
            app.toast("An error occurred during cloning", "error");
        }
    },

    async deleteLayout(id) {
        // Safe UI validation check without blocking alert
        // We will execute deletions cleanly.
        try {
            const res = await API.delete(`/api/layouts/${id}`);
            if (res.ok) {
                app.toast("Layout deleted successfully.", "success");
                this.loadUserLayouts();
            } else {
                app.toast("Failed to delete layout", "error");
            }
        } catch (e) {
            app.toast("Connection error", "error");
        }
    },

    async togglePublish(layout) {
        const id = layout.id;
        const isPublic = layout.is_public;
        
        if (!app.user) {
            app.toast("Please sign in to publish layouts.", "info");
            app.showAuthModal('login');
            return;
        }
        
        try {
            if (isPublic) {
                const res = await API.post(`/api/layouts/${id}/unpublish`, {});
                if (res.ok) {
                    app.toast("Removed layout from marketplace.", "info");
                    this.loadUserLayouts();
                } else {
                    app.toast("Failed to unpublish layout", "error");
                }
            } else {
                // Email verification check pre-validation
                if (!app.user.is_verified) {
                    app.toast("You must verify your email address to publish layouts.", "warning");
                    app.navigateTo('profile');
                    return;
                }
                const res = await API.post(`/api/layouts/${id}/publish`, {});
                if (res.ok) {
                    app.toast("Layout published to marketplace!", "success");
                    this.loadUserLayouts();
                } else {
                    const data = await res.json();
                    app.toast(data.error || "Failed to publish layout", "error");
                }
            }
        } catch (e) {
            app.toast("Failed to toggle marketplace status", "error");
        }
    },

    exportLayout(layout) {
        if (!app.user) {
            app.toast("Please sign in to export custom layouts.", "info");
            app.showAuthModal('login');
            return;
        }
        if (!app.user.is_verified) {
            app.toast("Please verify your email address to export layouts.", "warning");
            app.navigateTo('profile');
            return;
        }

        const payload = {
            name: layout.name,
            description: layout.description || "",
            language: layout.language,
            direction: layout.direction || "ltr",
            mapping: layout.mapping
        };
        
        const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `${layout.name.toLowerCase().replace(/\s+/g, '_')}_mapping.json`;
        document.body.appendChild(a);
        a.click();
        
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        app.toast("Layout exported successfully!", "success");
    }
};

const LayoutEditorUI = {
    setupDone: false,

    onLoad(queries = {}) {
        this.setupUI();
        this.clearEditorForm();

        const id = queries.id;
        if (id) {
            document.getElementById('editor-page-title').textContent = "Modify Keyboard Layout";
            this.loadLayoutToForm(id);
        } else {
            document.getElementById('editor-page-title').textContent = "Create Keyboard Layout";
            this.addMappingRow("", ""); // add initial blank rows
            this.addMappingRow("", "");
        }
    },

    setupUI() {
        if (this.setupDone) return;

        const rowBtn = document.getElementById('btn-add-mapping-row');
        if (rowBtn) {
            rowBtn.addEventListener('click', () => {
                this.addMappingRow("", "");
            });
        }

        const editorForm = document.getElementById('layout-editor-form');
        if (editorForm) {
            editorForm.addEventListener('submit', (e) => this.handleSaveLayout(e));
        }

        const importModalBtn = document.getElementById('btn-trigger-import');
        if (importModalBtn) {
            importModalBtn.addEventListener('click', () => {
                document.getElementById('import-modal').classList.remove('hidden');
                document.getElementById('import-text-area').value = '';
                document.getElementById('import-file-input').value = '';
            });
        }

        const importSubmitBtn = document.getElementById('btn-import-submit');
        if (importSubmitBtn) {
            importSubmitBtn.addEventListener('click', () => this.handleImportLayout());
        }

        const templateSelect = document.getElementById('editor-template-select');
        if (templateSelect) {
            templateSelect.addEventListener('change', (e) => this.handleTemplateSelect(e));
        }

        this.setupDone = true;
    },

    handleTemplateSelect(e) {
        const val = e.target.value;
        if (!val) return;

        let mapping = null;
        let name = "";
        let lang = "";
        let direction = "ltr";

        if (val === 'default_en_ar') {
            mapping = typeof LOCAL_DEFAULT_EN_AR_MAPPING !== 'undefined' ? LOCAL_DEFAULT_EN_AR_MAPPING : {};
            name = "Custom English to Arabic";
            lang = "Arabic";
            direction = "rtl";
        } else if (val === 'default_ar_en') {
            mapping = typeof LOCAL_DEFAULT_AR_EN_MAPPING !== 'undefined' ? LOCAL_DEFAULT_AR_EN_MAPPING : {};
            name = "Custom Arabic to English";
            lang = "English";
            direction = "ltr";
        }

        if (mapping && Object.keys(mapping).length > 0) {
            document.getElementById('editor-layout-name').value = name;
            document.getElementById('editor-layout-lang').value = lang;
            document.getElementById('editor-layout-direction').value = direction;

            const container = document.getElementById('editor-mapping-rows');
            container.replaceChildren();

            Object.entries(mapping).forEach(([k, v]) => {
                this.addMappingRow(k, v);
            });

            app.toast("Mappings loaded from template!", "success");
            // Reset dropdown to let user trigger reload if needed
            e.target.value = "";
        }
    },

    clearEditorForm() {
        document.getElementById('editor-layout-id').value = '';
        document.getElementById('editor-layout-name').value = '';
        document.getElementById('editor-layout-lang').value = '';
        document.getElementById('editor-layout-desc').value = '';
        document.getElementById('editor-layout-direction').value = 'ltr';
        document.getElementById('editor-mapping-rows').replaceChildren();
    },

    addMappingRow(key = "", value = "") {
        const container = document.getElementById('editor-mapping-rows');
        if (!container) return;

        const row = document.createElement('tr');

        const tdKey = document.createElement('td');
        const inputKey = document.createElement('input');
        inputKey.type = 'text';
        inputKey.className = 'form-input mapping-key-input';
        inputKey.value = key;
        inputKey.maxLength = 5;
        inputKey.placeholder = 'e.g. a';
        tdKey.appendChild(inputKey);

        const tdValue = document.createElement('td');
        const inputValue = document.createElement('input');
        inputValue.type = 'text';
        inputValue.className = 'form-input mapping-val-input';
        inputValue.value = value;
        inputValue.placeholder = 'e.g. ش';
        tdValue.appendChild(inputValue);

        const tdAction = document.createElement('td');
        const delBtn = document.createElement('button');
        delBtn.type = 'button';
        delBtn.className = 'btn btn-danger btn-sm';
        delBtn.textContent = 'Remove';
        delBtn.addEventListener('click', () => {
            row.remove();
        });
        tdAction.appendChild(delBtn);

        row.appendChild(tdKey);
        row.appendChild(tdValue);
        row.appendChild(tdAction);

        container.appendChild(row);
    },

    async loadLayoutToForm(id) {
        try {
            const res = await API.get(`/api/layouts/${id}`);
            const layout = await res.json();
            
            if (!res.ok) {
                app.toast("Layout details could not be retrieved", "error");
                app.navigateTo('layouts');
                return;
            }

            document.getElementById('editor-layout-id').value = layout.id;
            document.getElementById('editor-layout-name').value = layout.name;
            document.getElementById('editor-layout-lang').value = layout.language;
            document.getElementById('editor-layout-desc').value = layout.description || '';
            document.getElementById('editor-layout-direction').value = layout.direction || 'ltr';

            const mapping = layout.mapping || {};
            const container = document.getElementById('editor-mapping-rows');
            container.replaceChildren();

            Object.entries(mapping).forEach(([key, val]) => {
                this.addMappingRow(key, val);
            });
        } catch (e) {
            app.toast("Failed to parse layout from DB", "error");
        }
    },

    async handleSaveLayout(e) {
        e.preventDefault();
        
        const id = document.getElementById('editor-layout-id').value;
        const name = document.getElementById('editor-layout-name').value.trim();
        const language = document.getElementById('editor-layout-lang').value.trim();
        const description = document.getElementById('editor-layout-desc').value.trim();
        const direction = document.getElementById('editor-layout-direction').value;

        // Compile mapping grid values
        const mapping = {};
        let mappingEmpty = false;
        
        const keysList = document.querySelectorAll('.mapping-key-input');
        const valsList = document.querySelectorAll('.mapping-val-input');

        for (let i = 0; i < keysList.length; i++) {
            const k = keysList[i].value;
            const v = valsList[i].value;

            if (k) {
                mapping[k] = v || "";
            } else {
                mappingEmpty = true;
            }
        }

        if (Object.keys(mapping).length === 0) {
            app.toast("Layout mapping must contain at least one character map entry.", "error");
            return;
        }

        const payload = {
            name,
            language,
            description,
            direction,
            mapping
        };

        try {
            let res;
            if (id) {
                res = await API.put(`/api/layouts/${id}`, payload);
            } else {
                res = await API.post('/api/layouts', payload);
            }

            const data = await res.json();
            if (res.ok) {
                app.toast(id ? "Layout updated!" : "Layout created successfully!", "success");
                app.navigateTo('layouts');
            } else {
                app.toast(data.error || "Save layout failed", "error");
            }
        } catch (err) {
            app.toast("Network saving failed", "error");
        }
    },

    async handleImportLayout() {
        const fileInput = document.getElementById('import-file-input');
        const textArea = document.getElementById('import-text-area');
        let rawContent = textArea.value.trim();

        const file = fileInput.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = async (e) => {
                await this.sendImportRequest(e.target.result);
            };
            reader.readAsText(file);
        } else if (rawContent) {
            await this.sendImportRequest(rawContent);
        } else {
            app.toast("Please upload a file or paste layout JSON content.", "error");
        }
    },

    async sendImportRequest(jsonString) {
        try {
            let parsed;
            try {
                parsed = JSON.parse(jsonString);
            } catch (e) {
                app.toast("Invalid JSON format. Please check syntax.", "error");
                return;
            }

            const res = await API.post('/api/layouts/import', { layout_json: parsed });
            const data = await res.json();
            
            if (res.ok) {
                app.toast(`Imported successfully as ${data.name}!`, "success");
                document.getElementById('import-modal').classList.add('hidden');
                app.navigateTo('layouts');
                LayoutsManagerUI.loadUserLayouts();
            } else {
                app.toast(data.error || "Import query failed", "error");
            }
        } catch (err) {
            app.toast("Failed to import layout package.", "error");
        }
    }
};
