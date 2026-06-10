/**
 * Smart Keyboard Converter AI - Converter UI Controller
 * Implements real-time client-side keyboard conversion for zero latency.
 */

const LOCAL_DEFAULT_EN_AR_MAPPING = {
    "q": "ض", "w": "ص", "e": "ث", "r": "ق", "t": "ف", "y": "غ", "u": "ع", "i": "ه", "o": "خ", "p": "ح", "[": "ج", "]": "د",
    "a": "ش", "s": "س", "d": "ي", "f": "ب", "g": "ل", "h": "ا", "j": "ت", "k": "ن", "l": "م", ";": "ك", "'": "ط",
    "z": "ئ", "x": "ء", "c": "ؤ", "v": "ر", "b": "لا", "n": "ى", "m": "ة", ",": "و", ".": "ز", "/": "ظ",
    "Q": "َ", "W": "ً", "E": "ُ", "R": "ٌ", "T": "لإ", "Y": "إ", "U": "`", "I": "ـ", "O": "x", "P": "؛", "{": "ج", "}": "د",
    "A": "ِ", "S": "ٍ", "D": "[", "F": "]", "G": "لأ", "H": "أ", "J": "ـ", "K": "،", "L": "/", ":": "ك", "\"": "ط",
    "Z": "~", "X": "ْ", "C": "}", "V": "{", "B": "لآ", "N": "آ", "M": "’", "<": ",", ">": ".", "?": "؟"
};

const LOCAL_DEFAULT_AR_EN_MAPPING = {};
Object.entries(LOCAL_DEFAULT_EN_AR_MAPPING).forEach(([k, v]) => {
    LOCAL_DEFAULT_AR_EN_MAPPING[v] = k;
});

const ConverterUI = {
    activeMode: 1,
    activeLayoutId: 'default_en_ar',
    layoutCache: { 
        'default_en_ar': LOCAL_DEFAULT_EN_AR_MAPPING,
        'default_ar_en': LOCAL_DEFAULT_AR_EN_MAPPING
    },
    isAIProcessing: false,

    setupDone: false,

    onLoad(queries = {}) {
        this.setupUI();
        this.loadLayoutDropdown();
        this.toggleAIModeVisibility();
        
        // Preset layout if supplied in URL
        if (queries.layout) {
            const select = document.getElementById('converter-layout-select');
            if (select) {
                select.value = queries.layout;
                this.activeLayoutId = queries.layout;
            }
        }
        this.runInstantConvert();
    },

    setupUI() {
        if (this.setupDone) return;
        
        const inputArea = document.getElementById('converter-input-area');
        if (inputArea) {
            inputArea.addEventListener('input', () => {
                this.updateCounters();
                this.runInstantConvert();
            });
        }

        // Layout Dropdown Switch
        const layoutSelect = document.getElementById('converter-layout-select');
        if (layoutSelect) {
            layoutSelect.addEventListener('change', async (e) => {
                this.activeLayoutId = e.target.value;
                await this.ensureLayoutMappingCached(this.activeLayoutId);
                this.runInstantConvert();
            });
        }

        // Mode toggles buttons selection
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const targetBtn = e.currentTarget;
                if (targetBtn.classList.contains('disabled')) return;
                
                document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
                targetBtn.classList.add('active');
                
                this.activeMode = parseInt(targetBtn.dataset.mode);
                this.updateModeUI();
            });
        });

        // AI trigger buttons actions
        const btnTriggerAI = document.getElementById('btn-trigger-ai-process');
        if (btnTriggerAI) {
            btnTriggerAI.addEventListener('click', () => this.runAIEnhancement());
        }

        // Copy / Utility actions
        this.bindUtilityButton('btn-clear-input', () => {
            inputArea.value = '';
            this.updateCounters();
            this.runInstantConvert();
        });
        
        this.bindUtilityButton('btn-paste-input', async () => {
            try {
                const text = await navigator.clipboard.readText();
                inputArea.value = text;
                this.updateCounters();
                this.runInstantConvert();
            } catch (err) {
                app.toast("Failed to read clipboard", "error");
            }
        });

        this.bindUtilityButton('btn-copy-converted', () => {
            const out = document.getElementById('converter-output-display').textContent;
            this.copyToClipboard(out, "Converted text copied!");
        });

        this.bindUtilityButton('btn-copy-ai', () => {
            const out = document.getElementById('converter-ai-display').textContent;
            this.copyToClipboard(out, "AI output copied!");
        });

        this.bindUtilityButton('btn-replace-original', () => {
            const aiText = document.getElementById('converter-ai-display').textContent;
            if (aiText && aiText !== "Click process to fetch AI enhancement...") {
                inputArea.value = aiText;
                this.runInstantConvert();
                app.toast("Replaced input with enhanced text!", "success");
            }
        });

        // AI setting sliders displays
        const aiTempRange = document.getElementById('converter-ai-temp');
        const aiTempLabel = document.getElementById('temp-val-display');
        if (aiTempRange && aiTempLabel) {
            aiTempRange.addEventListener('input', (e) => {
                aiTempLabel.textContent = e.target.value;
            });
        }

        this.setupDone = true;
    },

    bindUtilityButton(id, callback) {
        const btn = document.getElementById(id);
        if (btn) btn.addEventListener('click', callback);
    },

    updateCounters() {
        const inputArea = document.getElementById('converter-input-area');
        const counter = document.getElementById('input-char-counter');
        if (inputArea && counter) {
            counter.textContent = `${inputArea.value.length} / 10000`;
        }
    },

    toggleAIModeVisibility() {
        const aiEnabled = app.aiConfig.ai_enabled;
        const disabledWarning = document.getElementById('ai-global-disabled-msg');
        
        // Enable/disable AI mode buttons
        for (let m = 2; m <= 4; m++) {
            const btn = document.getElementById(`mode-btn-${m}`);
            if (btn) {
                if (aiEnabled) {
                    btn.classList.remove('disabled');
                    btn.removeAttribute('disabled');
                    if (disabledWarning) disabledWarning.classList.add('hidden');
                } else {
                    btn.classList.add('disabled');
                    btn.setAttribute('disabled', 'true');
                    if (disabledWarning) disabledWarning.classList.remove('hidden');
                }
            }
        }
        
        // Populate model dropdown if AI enabled
        if (aiEnabled) {
            const modelSelect = document.getElementById('converter-ai-model');
            if (modelSelect) {
                modelSelect.replaceChildren();
                app.aiConfig.available_models.forEach(model => {
                    const opt = document.createElement('option');
                    opt.value = model.id;
                    opt.textContent = model.name;
                    modelSelect.appendChild(opt);
                });
            }
        }
    },

    async loadLayoutDropdown() {
        const select = document.getElementById('converter-layout-select');
        if (!select) return;

        // Keep default options starting with default_, clear others
        const defaults = [];
        for (let i = 0; i < select.options.length; i++) {
            const opt = select.options[i];
            if (opt.value.startsWith('default_')) {
                defaults.push(opt);
            }
        }
        select.replaceChildren();
        defaults.forEach(opt => select.appendChild(opt));

        if (app.user) {
            try {
                const res = await API.get('/api/layouts');
                if (res.ok) {
                    const userLayouts = await res.json();
                    userLayouts.forEach(layout => {
                        const opt = document.createElement('option');
                        opt.value = layout.id;
                        opt.textContent = `${layout.name} (${layout.language})`;
                        select.appendChild(opt);
                        // Pre-cache mappings
                        this.layoutCache[layout.id] = layout.mapping;
                    });
                }
            } catch (e) {
                // Ignore failure
            }
        }
    },

    async ensureLayoutMappingCached(layoutId) {
        if (this.layoutCache[layoutId]) return;
        try {
            const res = await API.get(`/api/layouts/${layoutId}`);
            if (res.ok) {
                const layout = await res.json();
                this.layoutCache[layoutId] = layout.mapping;
            }
        } catch (e) {
            console.error("Failed to load layout details mapping:", e);
        }
    },

    updateModeUI() {
        const settingsPanel = document.getElementById('converter-ai-settings-block');
        const aiOutputCard = document.getElementById('ai-output-card');
        
        if (this.activeMode > 1) {
            if (settingsPanel) settingsPanel.classList.remove('hidden');
            if (aiOutputCard) aiOutputCard.classList.remove('hidden');
        } else {
            if (settingsPanel) settingsPanel.classList.add('hidden');
            if (aiOutputCard) aiOutputCard.classList.add('hidden');
        }
    },

    runInstantConvert() {
        const text = document.getElementById('converter-input-area').value;
        const display = document.getElementById('converter-output-display');
        const dirBadge = document.getElementById('output-direction-badge');
        
        if (!text) {
            display.textContent = "Converted text will appear here as you type...";
            display.classList.add('placeholder-text');
            if (dirBadge) dirBadge.textContent = 'LTR';
            return;
        }

        const mapping = this.layoutCache[this.activeLayoutId] || LOCAL_DEFAULT_EN_AR_MAPPING;
        
        // Prefix matching translation client side
        const converted = this.clientConvert(text, mapping);
        
        display.textContent = converted;
        display.classList.remove('placeholder-text');

        // Detect text direction
        const isRtl = this.detectRtlText(converted);
        display.style.direction = isRtl ? 'rtl' : 'ltr';
        display.style.textAlign = isRtl ? 'right' : 'left';
        
        if (dirBadge) {
            dirBadge.textContent = isRtl ? 'RTL' : 'LTR';
        }
    },

    clientConvert(text, mapping) {
        if (!mapping) return text;
        const sortedKeys = Object.keys(mapping).sort((a, b) => b.length - a.length);
        
        const result = [];
        let i = 0;
        const n = text.length;
        
        while (i < n) {
            let matched = false;
            for (const key of sortedKeys) {
                if (i + key.length <= n && text.substring(i, i + key.length) === key) {
                    result.push(mapping[key]);
                    i += key.length;
                    matched = true;
                    break;
                }
            }
            if (!matched) {
                result.push(text[i]);
                i++;
            }
        }
        return result.join('');
    },

    detectRtlText(text) {
        let rtlCount = 0;
        let ltrCount = 0;
        for (let i = 0; i < text.length; i++) {
            const charCode = text.charCodeAt(i);
            if (charCode >= 0x0590 && charCode <= 0x06FF) {
                rtlCount++;
            } else if ((charCode >= 65 && charCode <= 90) || (charCode >= 97 && charCode <= 122)) {
                ltrCount++;
            }
        }
        return rtlCount > ltrCount;
    },

    async runAIEnhancement() {
        const text = document.getElementById('converter-input-area').value;
        const aiDisplay = document.getElementById('converter-ai-display');
        const loader = document.getElementById('ai-loader-icon');
        
        if (!text) {
            app.toast("Input text cannot be empty.", "error");
            return;
        }

        if (this.isAIProcessing) return;
        this.isAIProcessing = true;
        
        if (loader) loader.classList.remove('hidden');
        aiDisplay.textContent = "AI model thinking...";
        aiDisplay.classList.add('placeholder-text');

        try {
            const aiSettings = {
                preferred_model: document.getElementById('converter-ai-model').value,
                temperature: parseFloat(document.getElementById('converter-ai-temp').value),
                prompt_prefix: document.getElementById('converter-ai-prompt').value
            };

            const payload = {
                text: text,
                layout_id: this.activeLayoutId,
                mode: this.activeMode,
                ai_settings: aiSettings
            };

            const res = await API.post('/api/converter/convert', payload);
            const resData = await res.json();
            
            if (!res.ok) {
                this.toastAIError(resData.error || "AI Enhancement failed.");
                return;
            }

            if (resData.ai_error) {
                this.toastAIError(resData.ai_error);
                return;
            }

            aiDisplay.textContent = resData.ai_enhanced_text;
            aiDisplay.classList.remove('placeholder-text');
            
            const isRtl = this.detectRtlText(resData.ai_enhanced_text);
            aiDisplay.style.direction = isRtl ? 'rtl' : 'ltr';
            aiDisplay.style.textAlign = isRtl ? 'right' : 'left';
            
        } catch (e) {
            this.toastAIError("An unexpected error occurred contacting the AI server.");
        } finally {
            this.isAIProcessing = false;
            if (loader) loader.classList.add('hidden');
        }
    },

    toastAIError(msg) {
        const aiDisplay = document.getElementById('converter-ai-display');
        aiDisplay.textContent = `Error: ${msg}`;
        aiDisplay.classList.add('placeholder-text');
        app.toast(msg, "error");
    },

    copyToClipboard(text, successMsg) {
        if (!text || text.startsWith("Converted text") || text.startsWith("Click process")) return;
        navigator.clipboard.writeText(text)
            .then(() => app.toast(successMsg, "success"))
            .catch(() => app.toast("Failed to copy text", "error"));
    }
};
