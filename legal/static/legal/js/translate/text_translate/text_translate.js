$(document).ready(function () {
    if (window.__textTranslateInitialized) {
        return;
    }
    window.__textTranslateInitialized = true;

    const CHAR_LIMIT = 2000;
    const STORAGE_KEYS = {
        source: 'translate_source_language',
        target: 'translate_target_language',
        glossaryPrefix: 'translate_glossary_',
    };
    const SELECTORS = {
        source: 'select[name="source_language"]',
        target: 'select[name="target_language"]',
        domain: 'select[name="domain_name"]',
        form: 'form[name="text-translate"]',
    };
    const state = {
        isInitializing: true,
        isTranslating: false,
        sourceLanguage: null,
        targetLanguage: null,
    };
    const $els = {
        sourceSelect: $(SELECTORS.source),
        targetSelect: $(SELECTORS.target),
        domainSelect: $(SELECTORS.domain),
        translateForm: $(SELECTORS.form),
        translateBtn: $('#btn-translate'),
        clearButtons: $('#clear, #clear-source'),
        copyButtons: $('#copy, .copy'),
        detectBtn: $('#detect-language'),
        detectStatus: $('#text-detect-status'),
        translationSkeleton: $('#translation-skeleton'),
        translatedText: $('#translated-text'),
        tooltip: $('#tooltip'),
        syncBtn: $('#sync-target-to-source'),
        instructionsField: $('#translation-instructions'),
        qualityFeedbackRow: $('#quality-feedback-row'),
        qualityCommentsText: $('#quality-comments-text'),
        // Instructions modal elements
        instructionsModalBtn: $('#instructions-modal-btn'),
        instructionsModal: $('#instructions-modal'),
        closeInstructionsModal: $('#close-instructions-modal'),
        cancelInstructionsBtn: $('#cancel-instructions'),
        saveInstructionsBtn: $('#save-instructions'),
        instructionsIndicator: $('#instructions-indicator'),
    };

    const MIN_DETECTION_WORD_COUNT = 9;
    
    // Instructions configuration
    const INSTRUCTIONS_CONFIG = {
        MAX_LENGTH: 2000,
        MESSAGES: {
            saving: { en: 'Saving...', fr: 'Enregistrement...' },
            saved: { en: 'Instructions saved successfully.', fr: 'Instructions enregistrées avec succès.' },
            tooLong: { en: 'Instructions cannot exceed 2000 characters.', fr: 'Les instructions ne peuvent pas dépasser 2000 caractères.' }
        }
    };
    
    /**
     * Obtient un message traduit depuis la configuration des instructions
     * @param {string} key - Clé du message (saving, saved, tooLong)
     * @returns {string} Message traduit
     */
    function getInstructionsMessage(key) {
        const message = INSTRUCTIONS_CONFIG.MESSAGES[key];
        if (!message) return '';
        return getTranslation(message.en, message.fr);
    }
    
    // Instructions modal state
    let originalInstructionsValue = '';

    let detectStatusTimeout = null;
    let lastAutoDetectedText = '';
    let isTextLanguageDetectionInProgress = false;
    let textDetectionTriggered = false;

    /**
     * Get translation helper - uses AppBase if available, otherwise local fallback
     * @param {string} enText - English text
     * @param {string} frText - French text
     * @returns {string} Translated text
     */
    function getTranslation(enText, frText) {
        if (window.AppBase && window.AppBase.getTranslation) {
            return window.AppBase.getTranslation(enText, frText);
        }
        const lang = window.language_code || language_code || 'en';
        return lang === 'fr' ? frText : enText;
    }

    /**
     * Retourne les en-têtes AJAX standardisés
     * @returns {Object} En-têtes pour les requêtes AJAX
     */
    function getAjaxHeaders() {
        return {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken'),
        };
    }

    /**
     * Affiche une erreur via AppBase.showError si disponible, sinon console
     * @param {Object|string} error - Objet d'erreur ou message d'erreur
     */
    function showError(error) {
        if (window.AppBase && window.AppBase.showError) {
            window.AppBase.showError(error);
        } else {
            const errorMessage = typeof error === 'string' 
                ? error 
                : (error?.responseJSON?.detail || error?.message || getTranslation('Something went wrong', 'Quelque chose s\'est mal passé.'));
            console.error('Error:', errorMessage);
        }
    }

    const detectStatusFallbacks = {
        en: {
            detecting: 'Detecting language...',
            success: 'Language detected',
            error: 'Language detection error',
        },
        fr: {
            detecting: 'Détection de la langue en cours...',
            success: 'Langue détectée',
            error: 'Erreur lors de détection de langue',
        },
    };
    const detectStatusMessages = getDetectStatusMessages();

    const editors = initQuillEditors();
    initPlaceholders();
    initDomainSelect();
    enhanceSelect2Arrows();
    ensureGlossarySpinner();
    bindGlossaryChange();

    state.sourceLanguage = $els.sourceSelect.val() || null;
    state.targetLanguage = $els.targetSelect.val() || null;

    bindLanguageHandlers();
    bindSwapButton();
    restoreSavedLanguages();
    state.isInitializing = false;
    maybeFetchDomains('postRestore');

    setupFormSubmission();
    bindClearButtons();
    bindCopyButtons();
    bindDetectLanguage();
    initPasteLimiter();
    initModalToggles();
    bindEditorEvents();
    bindInstructionsModal();
    // Initialiser l'indicateur à gris (pas d'instructions) au démarrage
    updateInstructionsIndicator();
    // Charger les instructions sauvegardées au démarrage pour initialiser originalInstructionsValue
    loadSavedInstructions((savedValue) => {
        originalInstructionsValue = savedValue || '';
        updateInstructionsIndicator();
    });
    refreshInitialUiState();

    function initQuillEditors() {
        const source = new Quill('#source-text', {
            theme: 'snow',
            placeholder: getTranslation('Add your text here', 'Ajoutez votre texte ici'),
            modules: { toolbar: false }
        });

        const translated = new Quill('#translated-text', {
            theme: 'snow',
            modules: { toolbar: false }
        });

        if (typeof window !== 'undefined') {
            window.sourceQuill = source;
            window.translatedQuill = translated;
        }

        return { source, translated };
    }

    function initPlaceholders() {
        const placeholders = {
            '.source-language': getTranslation('Source language', 'Langue source'),
            '.target-language': getTranslation('Target language', 'Langue cible'),
            '.domain-select': getTranslation('Glossary', 'Glossaire'),
        };

        Object.entries(placeholders).forEach(([selector, text]) => {
            $(selector).attr('data-placeholder', text);
        });
    }

    function initDomainSelect() {
        $els.domainSelect.select2({
            placeholder: $els.domainSelect.data('placeholder'),
            allowClear: false,
            dropdownCssClass: 'glossary-resize',
            dropdownParent: $('.text-translate-domain-wrapper'),
        });

        updateGlossaryDropdownOffset($els.domainSelect.data('select2'));

        $els.domainSelect.on('select2:open', function () {
            updateGlossaryDropdownOffset($(this).data('select2'));
        });

        $(window).on('resize.glossaryDropdown', function () {
            updateGlossaryDropdownOffset($els.domainSelect.data('select2'));
        });

        applyLanguageSelect2($els.sourceSelect);
        applyLanguageSelect2($els.targetSelect);
    }

    function updateGlossaryDropdownOffset(instance) {
        const $container = instance?.$container;
        if (!$container?.length) return;

        const triggerWidth = $container.outerWidth();
        if (!triggerWidth) return;

        const wrapperEl = $container.closest('.text-translate-domain-wrapper').get(0);
        if (!wrapperEl) return;

        wrapperEl.style.setProperty('--glossary-right-offset', `-${triggerWidth}px`);
    }

    function applyLanguageSelect2($select) {
        const select2Instance = $select.select2().data('select2');
        select2Instance?.$container.addClass('languages');
        select2Instance?.$dropdown.addClass('languages');
    }

    function ensureGlossarySpinner() {
        if ($('#glossary-spinner').length) return;
        const spinner = $('<span id="glossary-spinner" class="inline-block w-5 h-5 mr-2 rounded-full border border-gray-300 border-t-green-800 animate-spin hidden"></span>');
        $els.domainSelect.parent('.text-translate-domain-wrapper').prepend(spinner);
    }

    function enhanceSelect2Arrows() {
        const containersSelector = '.text-translate-column .select2-container, .text-translate-column-selector .select2-container';
        $(containersSelector).css({ display: 'inline-block', width: 'auto', minWidth: 'auto' });

        const selectionsSelector = '.text-translate-column .select2-selection, .text-translate-column-selector .select2-selection';
        $(selectionsSelector).each(function () {
            $(this).css({ display: 'inline-flex', width: 'auto', minWidth: 'auto' });
            $(this).find('.select2-selection__rendered').css({ 'padding-right': '0.375rem' });

            const $arrow = $(this).find('.select2-selection__arrow');
            $arrow.find('b').hide();
            $arrow.css({
                position: 'static',
                right: 'auto',
                top: 'auto',
                transform: 'none',
                width: 'auto',
                height: 'auto',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginLeft: '0.25rem'
            });
            $arrow.find('i.ph').remove();
        });
    }

    function glossaryStorageKey() {
        if (!state.sourceLanguage || !state.targetLanguage) return null;
        return `${STORAGE_KEYS.glossaryPrefix}${state.sourceLanguage}_${state.targetLanguage}`;
    }

    function bindGlossaryChange() {
        $els.domainSelect.on('change', () => {
            const glossaryKey = glossaryStorageKey();
            const glossaryValue = $els.domainSelect.val();
            if (glossaryKey && glossaryValue) {
                localStorage.setItem(glossaryKey, glossaryValue);
            }
            validateTranslateButton();
        });
    }

    function bindLanguageHandlers() {
        $els.sourceSelect.off('change.textTranslate').on('change.textTranslate', function (event, extra) {
            handleLanguageChange('source', $(this).val(), event, extra);
        });

        $els.targetSelect.off('change.textTranslate').on('change.textTranslate', function (event, extra) {
            handleLanguageChange('target', $(this).val(), event, extra);
        });
    }

    function handleLanguageChange(type, value, event, extra) {
        const prop = type === 'source' ? 'sourceLanguage' : 'targetLanguage';
        state[prop] = value || null;
        persistLanguages();

        $els.domainSelect.val(null).trigger('change');
        validateTranslateButton();

        if (state.isInitializing) {
            return;
        }

        maybeFetchDomains(`${type}Change`);
    }

    function persistLanguages() {
        if (state.sourceLanguage) {
            localStorage.setItem(STORAGE_KEYS.source, state.sourceLanguage);
        }
        if (state.targetLanguage) {
            localStorage.setItem(STORAGE_KEYS.target, state.targetLanguage);
        }
    }

    function restoreSavedLanguages() {
        const savedSource = localStorage.getItem(STORAGE_KEYS.source);
        const savedTarget = localStorage.getItem(STORAGE_KEYS.target);

        if (savedSource) {
            $els.sourceSelect.val(savedSource).trigger('change');
        }

        if (savedTarget) {
            $els.targetSelect.val(savedTarget).trigger('change');
        } else if ($els.targetSelect.find('option[value="en"]').length) {
            $els.targetSelect.val('en').trigger('change');
        }
    }

    function maybeFetchDomains(reason) {
        if (!state.sourceLanguage || !state.targetLanguage) {
            return;
        }
        fetchDomains({ reason });
    }

    function fetchDomains(metadata) {
        $.ajax({
            url: `${get_domains}`,
            type: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            beforeSend() {
                $('#glossary-spinner').removeClass('hidden');
            },
            success(response) {
                populateDomains(response);
            },
            error: showError,
            complete() {
                $('#glossary-spinner').addClass('hidden');
            }
        });
    }

    function populateDomains(response) {
        if (!Array.isArray(response?.data) || response.data.length === 0) {
            return;
        }

        $els.domainSelect.empty();
        $els.domainSelect.append($('<option></option>').attr('value', '').text('Domain').prop('disabled', true));

        response.data.forEach((domain) => {
            $els.domainSelect.append($('<option></option>').attr('value', domain.name).text(domain.name));
        });

        const savedGlossaryKey = glossaryStorageKey();
        const savedGlossary = savedGlossaryKey ? localStorage.getItem(savedGlossaryKey) : null;

        let selectedValue = savedGlossary;
        if (!selectedValue || !$els.domainSelect.find(`option[value="${selectedValue}"]`).length) {
            selectedValue = $els.domainSelect.find('option:not(:disabled):first').val();
        }

        if (selectedValue) {
            $els.domainSelect.val(selectedValue).trigger('change');
        }
    }

    function bindSwapButton() {
        $els.syncBtn.on('click', () => {
            if (!$els.sourceSelect.length || !$els.targetSelect.length) {
                return;
            }

            const previousSource = $els.sourceSelect.val();
            const previousTarget = $els.targetSelect.val();

            if (!previousSource && !previousTarget) {
                return;
            }

            if (previousSource && previousTarget && previousSource === previousTarget) {
                validateTranslateButton();
                return;
            }

            $els.sourceSelect.val(null).trigger('change');
            $els.targetSelect.val(null).trigger('change');

            if (previousTarget) {
                $els.sourceSelect.val(previousTarget).trigger('change');
            }

            if (previousSource) {
                $els.targetSelect.val(previousSource).trigger('change');
            }
        });
    }

    function setupFormSubmission() {
        $els.translateForm.off('submit').on('submit', function (event) {
            event.preventDefault();
            if (state.isTranslating) return false;

            const textContent = editors.source.getText().trim();
            const htmlContent = editors.source.root.innerHTML.trim();
            const currentCount = textContent.replace(/\n/g, '').length;
            const isEmptyHtml = !htmlContent || htmlContent === '<p><br></p>' || htmlContent === '<p></p>';

            if (currentCount > CHAR_LIMIT || !textContent || isEmptyHtml) {
                return false;
            }

            state.isTranslating = true;
            $els.translateBtn.prop('disabled', true);

            $('#text').val(htmlContent);
            const formData = new FormData(this);
            
            // Ajouter les instructions sauvegardées (valeur réelle dans User, pas celle du textarea)
            formData.append('instructions', originalInstructionsValue || '');

            generateSkeleton();
            hideQualityFeedback(); // LARA: Masquer le retour qualité précédent

            $.ajax({
                url: translate,
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                success(response) {
                    editors.translated.root.innerHTML = response.translated_text[0];

                    // LARA: Afficher le retour qualité s'il existe (commentaire texte)
                    if (response.quality_feedback) {
                        showQualityFeedback(response.quality_feedback);
                    }
                },
                error(error) {
                    showError(error);
                    showTranslationResult();
                },
                complete() {
                    showTranslationResult();
                    resizeTextAreas();
                    state.isTranslating = false;
                    validateTranslateButton();
                }
            });

            return false;
        });
    }

    function generateSkeleton() {
        buildSkeletonFromSource();
        $els.translatedText.css({ visibility: 'hidden' });
        $els.translationSkeleton.removeClass('hidden');
        editors.translated.root.innerHTML = '';
    }

    function showTranslationResult() {
        $els.translationSkeleton.addClass('hidden');
        $els.translatedText.css({ visibility: 'visible' });
    }

    // LARA: Fonctions pour gérer l'affichage du retour qualité
    function showQualityFeedback(qualityData) {
        if (!qualityData) return;

        // Le retour qualité est un commentaire texte, pas un chiffre
        const { comments, suggestions } = qualityData;

        let feedbackText = '';

        if (comments) {
            feedbackText = comments;
        }

        if (suggestions) {
            if (feedbackText) {
                feedbackText += '\n\n' + suggestions;
            } else {
                feedbackText = suggestions;
            }
        }

        if (feedbackText) {
            $els.qualityCommentsText.text(feedbackText);
            $els.qualityFeedbackRow.removeClass('hidden');
        }
    }

    function hideQualityFeedback() {
        $els.qualityFeedbackRow.addClass('hidden');
        $els.qualityCommentsText.text('');
    }

    function bindClearButtons() {
        $els.clearButtons.on('click', () => {
            editors.source.deleteText(0, editors.source.getLength());
            editors.translated.deleteText(0, editors.translated.getLength());
            setInstructionsValue('');
            hideQualityFeedback();
            resizeTextAreas();
            validateTranslateButton();
        });
    }

    function bindCopyButtons() {
        $els.copyButtons.on('click', () => {
            const translatedText = editors.translated.getText();
            const translatedHtml = editors.translated.root.innerHTML;

            if (!translatedHtml) return;

            if (navigator.clipboard && window.ClipboardItem) {
                const htmlBlob = new Blob([translatedHtml], { type: 'text/html' });
                const textBlob = new Blob([translatedText], { type: 'text/plain' });
                const data = [new ClipboardItem({ 'text/html': htmlBlob, 'text/plain': textBlob })];

                navigator.clipboard.write(data).then(showTooltip).catch((error) => {
                    console.error('Erreur de copie : ', error);
                    const errorMessage = getTranslation(
                        'Error copying to clipboard.',
                        'Erreur lors de la copie dans le presse-papiers.'
                    );
                    showError(errorMessage);
                });
            } else {
                const errorMessage = getTranslation(
                    'Your browser does not support Clipboard API. Please update it.',
                    'Votre navigateur ne supporte pas Clipboard API. Merci de le mettre à jour.'
                );
                showError(errorMessage);
            }
        });
    }

    function showTooltip() {
        $els.tooltip.removeClass('invisible opacity-0').addClass('visible opacity-100');
        setTimeout(() => {
            $els.tooltip.removeClass('visible opacity-100').addClass('invisible opacity-0');
        }, 2000);
    }

    function bindDetectLanguage() {
        $els.detectBtn.on('click', () => {
            requestTextLanguageDetection({ autoTriggered: false });
        });
    }

    function showTextDetectStatus(message, variant = 'loading', autoHide = false) {
        if (!$els.detectStatus.length) return;
        clearTimeout(detectStatusTimeout);
        const variants = ['loading', 'success', 'error'];
        $els.detectStatus.removeClass('text-detect-status--hidden');
        variants.forEach(v => $els.detectStatus.removeClass(`text-detect-status--${v}`));
        $els.detectStatus.addClass(`text-detect-status--${variant}`);
        $els.detectStatus.find('.text-detect-label').text(variant === 'loading' ? '' : message);

        if (autoHide) {
            detectStatusTimeout = setTimeout(() => {
                $els.detectStatus.addClass('text-detect-status--fading');
                $els.detectStatus.find('.text-detect-label').css('opacity', 0);
                setTimeout(() => {
                    hideTextDetectStatus();
                }, 1000);
            }, 1000);
        }
    }

    function hideTextDetectStatus() {
        if (!$els.detectStatus.length) return;
        clearTimeout(detectStatusTimeout);
        $els.detectStatus.addClass('text-detect-status--hidden');
        $els.detectStatus.removeClass('text-detect-status--fading');
        $els.detectStatus.find('.text-detect-label').text('');
        $els.detectStatus.find('.text-detect-label').css('opacity', 1);
    }

    function getDetectStatusMessages() {
        if (!$els.detectStatus.length) {
            return {};
        }
        const $status = $els.detectStatus;
        const datasetMessages = {
            detecting: $status.data('message-detecting'),
            success: $status.data('message-success'),
            error: $status.data('message-error'),
        };
        const langKey = (typeof language_code === 'string' ? language_code : 'en').toLowerCase();
        const fallback = detectStatusFallbacks[langKey] || detectStatusFallbacks.en;
        return {
            detecting: datasetMessages.detecting || fallback.detecting,
            success: datasetMessages.success || fallback.success,
            error: datasetMessages.error || fallback.error,
        };
    }

    function formatSuccessDetectMessage(languageCode) {
        return detectStatusMessages.success || detectStatusFallbacks.en.success;
    }

    function initPasteLimiter() {
        const sourceRoot = document.querySelector('#source-text .ql-editor')?.parentElement;
        if (!sourceRoot) return;

        sourceRoot.addEventListener('paste', (event) => {
            const clipboardData = event.clipboardData || window.clipboardData;
            if (!clipboardData) return;

            // Tenter de récupérer le HTML formaté d'abord
            let htmlContent = clipboardData.getData('text/html');
            const textContent = clipboardData.getData('text');
            
            if (!textContent || typeof textContent !== 'string') return;

            const current = getSourceCharCount();
            const available = CHAR_LIMIT - current;

            if (available <= 0) {
                event.preventDefault();
                return;
            }

            event.preventDefault();

            const selection = editors.source.getSelection(true) || { index: editors.source.getLength(), length: 0 };
            
            // Si du contenu HTML est disponible et valide, l'utiliser pour conserver le formatage
            if (htmlContent && typeof htmlContent === 'string' && htmlContent.trim()) {
                // Vérifier la longueur du texte et tronquer si nécessaire
                const textLength = textContent.replace(/\r?\n/g, ' ').length;
                
                if (textLength > available) {
                    // Si le contenu dépasse la limite, utiliser le texte brut tronqué
                    const toInsert = textContent.replace(/\r?\n/g, ' ').slice(0, available);
                    editors.source.insertText(selection.index, toInsert, 'user');
                } else {
                    // Insérer le HTML formaté en conservant le style
                    // Supprimer d'abord la sélection s'il y en a une
                    if (selection.length > 0) {
                        editors.source.deleteText(selection.index, selection.length, 'user');
                    }
                    // Utiliser dangerouslyPasteHTML pour insérer le HTML avec formatage
                    editors.source.clipboard.dangerouslyPasteHTML(selection.index, htmlContent, 'user');
                }
            } else {
                // Fallback : utiliser le texte brut si pas de HTML disponible
                const toInsert = textContent.replace(/\r?\n/g, ' ').slice(0, available);
            editors.source.insertText(selection.index, toInsert, 'user');
            }
        }, true);
    }

    function initModalToggles() {
        const modal = document.getElementById('modal');
        const closeModalBtn = document.getElementById('closeModal');
        const closeIcon = document.getElementById('closeIcon');
        const checkbox = document.querySelector('input[type="checkbox"].peer');

        const closeModal = () => {
            modal?.classList.add('hidden');
            if (checkbox) checkbox.checked = false;
        };

        checkbox?.addEventListener('change', function () {
            if (!checkbox.checked) {
                modal?.classList.add('hidden');
            } else {
                modal?.classList.remove('hidden');
            }
        });

        closeModalBtn?.addEventListener('click', closeModal);
        closeIcon?.addEventListener('click', closeModal);
        modal?.addEventListener('click', function (event) {
            if (event.target === modal) closeModal();
        });
    }

    function bindEditorEvents() {
        editors.source.on('text-change', (delta, oldDelta, source) => {
            if (source !== 'user') {
                updateCharCount();
                validateTranslateButton();
                return;
            }

            const current = getSourceCharCount();
            if (current > CHAR_LIMIT) {
                const over = current - CHAR_LIMIT;
                const selection = editors.source.getSelection(true);
                const deleteIndex = selection ? Math.max(0, selection.index - over) : Math.max(0, editors.source.getLength() - 1 - over);
                editors.source.deleteText(deleteIndex, over, 'user');
                updateCharCount();
                return;
            }

            resizeTextAreas();
            updateCharCount();
            validateTranslateButton();
            scheduleAutoTextDetection();
        });

        editors.translated.on('text-change', () => {
            resizeTextAreas();
            const hasTranslated = editors.translated.getText().replace(/\n/g, '').length > 0;
            if (hasTranslated) {
                $('#btn-copy').removeClass('hidden');
            } else {
                $('#btn-copy').addClass('hidden');
            }
        });
    }

    function scheduleAutoTextDetection() {
        if (state.sourceLanguage) {
            return;
        }

        const textInfo = getSourceTextInfo();

        if (textInfo.wordCount < MIN_DETECTION_WORD_COUNT) {
            lastAutoDetectedText = '';
            textDetectionTriggered = false;
            return;
        }

        if (textDetectionTriggered || isTextLanguageDetectionInProgress) {
            return;
        }

        if (lastAutoDetectedText === textInfo.trimmed) {
            return;
        }

        requestTextLanguageDetection({ autoTriggered: true, textInfo });
    }

    function requestTextLanguageDetection({ autoTriggered = false, textInfo = null } = {}) {
        const info = textInfo || getSourceTextInfo();

        if (!info.trimmed) {
            hideTextDetectStatus();
            return;
        }

        if (autoTriggered) {
            if (state.sourceLanguage) {
                return;
            }
            if (info.wordCount < MIN_DETECTION_WORD_COUNT) {
                return;
            }
            if (isTextLanguageDetectionInProgress) {
                return;
            }
            if (textDetectionTriggered) {
                return;
            }
            if (lastAutoDetectedText === info.trimmed) {
                return;
            }
        } else if (isTextLanguageDetectionInProgress) {
            return;
        }

        textDetectionTriggered = autoTriggered;
        isTextLanguageDetectionInProgress = true;
        const detectingMessage = detectStatusMessages.detecting || detectStatusFallbacks.en.detecting;
        showTextDetectStatus(detectingMessage, 'loading', false);

        $.ajax({
            url: detect_text_language,
            type: 'POST',
            data: { text: info.raw },
            dataType: 'json',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
                'Accept': 'application/json',
            },
            success(response) {
                const detectedLanguage = response.language.toLowerCase();
                const currentSourceValue = $els.sourceSelect.val();
                if (!currentSourceValue || currentSourceValue.toLowerCase() !== detectedLanguage) {
                    $els.sourceSelect.val(detectedLanguage).trigger('change');
                }
                const successMessage = formatSuccessDetectMessage(detectedLanguage);
                showTextDetectStatus(successMessage, 'success', true);
                if (autoTriggered) {
                    lastAutoDetectedText = info.trimmed;
                }
            },
            error(error) {
                showError(error);
                const errorMessage = detectStatusMessages.error || detectStatusFallbacks.en.error;
                showTextDetectStatus(errorMessage, 'error', true);
            },
            complete() {
                isTextLanguageDetectionInProgress = false;
                textDetectionTriggered = false;
            }
        });
    }

    function getSourceTextInfo() {
        const raw = editors.source.getText() || '';
        const trimmed = raw.trim();
        return {
            raw,
            trimmed,
            wordCount: getWordCountFromText(trimmed),
        };
    }

    function getWordCountFromText(text) {
        if (!text) return 0;
        return text.trim().split(/\s+/).filter(Boolean).length;
    }

    function resizeTextAreas() {
        const $sourceEditor = $('#source-text .ql-editor');
        const $translatedEditor = $('#translated-text .ql-editor');

        $sourceEditor.css('height', 'auto');
        $translatedEditor.css('height', 'auto');

        const maxHeight = Math.max(
            $sourceEditor[0]?.scrollHeight || 0,
            $translatedEditor[0]?.scrollHeight || 0,
            400
        );

        $sourceEditor.css('height', `${maxHeight}px`);
        $translatedEditor.css('height', `${maxHeight}px`);
    }

    function getSourceCharCount() {
        return editors.source.getText().replace(/\n/g, '').length;
    }

    function updateCharCount() {
        $('#source-char-count').text(Math.min(getSourceCharCount(), CHAR_LIMIT));
    }

    function validateTranslateButton() {
        const sameLanguage = state.sourceLanguage && state.targetLanguage && state.sourceLanguage === state.targetLanguage;
        const hasDomain = Boolean($els.domainSelect.val());
        const isReady = state.sourceLanguage && state.targetLanguage && hasDomain && !sameLanguage;
        $els.translateBtn.prop('disabled', !isReady);

        if (sameLanguage) {
            return;
        }
    }

    function buildSkeletonFromSource() {
        const text = editors.source.getText().trim();
        const $skeleton = $els.translationSkeleton;
        const $qlEditor = $('#source-text .ql-editor');
        $skeleton.empty();

        if (!text) {
            $skeleton.append('<div class="skeleton-line" style="width: 60%;"></div>');
            $skeleton.append('<div class="skeleton-line" style="width: 80%;"></div>');
            return;
        }

        const qlEditorElement = $qlEditor[0];
        if (!qlEditorElement) {
            $skeleton.append('<div class="skeleton-line" style="width: 80%;"></div>');
            return;
        }

        const computedStyle = window.getComputedStyle(qlEditorElement);
        const fontFamily = computedStyle.fontFamily || 'Montserrat, sans-serif';
        const fontSize = parseFloat(computedStyle.fontSize) || 16;
        const paddingLeft = parseFloat(computedStyle.paddingLeft) || 0;
        const paddingRight = parseFloat(computedStyle.paddingRight) || 0;
        const availableWidth = Math.max(100, qlEditorElement.getBoundingClientRect().width - paddingLeft - paddingRight);

        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        context.font = `${fontSize}px ${fontFamily.split(',')[0].replace(/['"]/g, '').trim()}`;

        const logicalLines = text.split('\n')
            .map(line => line.trim())
            .filter((line, index, arr) => line.length > 0 || arr.slice(index + 1).some(l => l.length > 0));

        if (!logicalLines.length) {
            $skeleton.append('<div class="skeleton-line" style="width: 80%;"></div>');
            return;
        }

        const skeletonLines = [];

        logicalLines.forEach((logicalLine, lineIndex) => {
            const isLastLogicalLine = lineIndex === logicalLines.length - 1;

            if (!logicalLine.length) {
                if (!isLastLogicalLine) skeletonLines.push({ width: 0.05 * availableWidth, isEmpty: true });
                return;
            }

            const lineWidth = context.measureText(logicalLine).width;
            if (lineWidth <= availableWidth) {
                skeletonLines.push({ width: lineWidth });
                return;
            }

            const words = logicalLine.split(/\s+/);
            let currentLineWidth = 0;

            words.forEach((word, index) => {
                const wordWithSpace = word + (index < words.length - 1 ? ' ' : '');
                const wordWidth = context.measureText(wordWithSpace).width;

                if (currentLineWidth + wordWidth <= availableWidth) {
                    currentLineWidth += wordWidth;
                } else {
                    if (currentLineWidth > 0) skeletonLines.push({ width: currentLineWidth });
                    currentLineWidth = wordWidth;
                }
            });

            if (currentLineWidth > 0) {
                skeletonLines.push({ width: currentLineWidth });
            }
        });

        while (skeletonLines.length && skeletonLines[skeletonLines.length - 1].isEmpty) {
            skeletonLines.pop();
        }

        if (!skeletonLines.length) {
            const sampleWidth = context.measureText(text.substring(0, Math.min(50, text.length))).width;
            const widthPercent = Math.min(95, Math.max(25, (sampleWidth / availableWidth) * 100));
            $skeleton.append(`<div class="skeleton-line" style="width: ${widthPercent}%;"></div>`);
            return;
        }

        const skeletonHtml = skeletonLines.map((line) => {
            if (line.isEmpty) {
                return '<div class="skeleton-line" style="width: 5%; height: 0.5em; opacity: 0.3;"></div>';
            }
            const widthPercent = Math.min(98, Math.max(15, (line.width / availableWidth) * 100));
            return `<div class="skeleton-line" style="width: ${widthPercent}%;"></div>`;
        }).join('');

        $skeleton.append(skeletonHtml);
    }

    function refreshInitialUiState() {
        resizeTextAreas();
        const hasTranslatedInit = editors.translated.getText().replace(/\n/g, '').length > 0;
        $('#btn-copy').toggleClass('hidden', !hasTranslatedInit);
        updateCharCount();
        validateTranslateButton();
    }

    // ============================================
    // Instructions Modal Management
    // ============================================
    
    /**
     * Obtient la valeur actuelle des instructions depuis le champ
     * @returns {string} Valeur des instructions
     */
    function getInstructionsValue() {
        return $els.instructionsField.val() || '';
    }

    /**
     * Définit la valeur des instructions dans le champ
     * @param {string} value - Valeur à définir
     */
    function setInstructionsValue(value) {
        $els.instructionsField.val(value || '');
    }

    /**
     * Initialise les événements de la modal des instructions
     */
    function bindInstructionsModal() {
        $els.instructionsModalBtn.on('click', openInstructionsModal);
        $els.closeInstructionsModal.on('click', handleModalClose);
        $els.cancelInstructionsBtn.on('click', handleModalClose);
        $els.saveInstructionsBtn.on('click', handleSaveInstructions);
        
        // Fermer la modal en cliquant sur l'overlay
        $els.instructionsModal.on('click', function(event) {
            if (event.target === this) {
                handleModalClose(event);
            }
        });
    }

    /**
     * Ouvre la modal et charge les instructions sauvegardées
     */
    function openInstructionsModal() {
        loadSavedInstructions((savedValue) => {
            originalInstructionsValue = savedValue || '';
            $els.instructionsModal.removeClass('hidden');
        });
    }

    /**
     * Ferme la modal et restaure la valeur originale
     */
    function closeInstructionsModal() {
        setInstructionsValue(originalInstructionsValue);
        $els.instructionsModal.addClass('hidden');
    }

    /**
     * Gère la fermeture de la modal (avec prévention du comportement par défaut)
     */
    function handleModalClose(event) {
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }
        closeInstructionsModal();
    }

    /**
     * Charge les instructions sauvegardées depuis le serveur
     * @param {Function} callback - Fonction appelée après le chargement avec la valeur chargée
     */
    function loadSavedInstructions(callback) {
        $.ajax({
            url: get_saved_instructions || '/users/get-saved-instructions/',
            type: 'GET',
            headers: getAjaxHeaders(),
            success(response) {
                const savedValue = (response.saved_instructions || '').trim();
                setInstructionsValue(savedValue);
                if (callback) callback(savedValue);
            },
            error() {
                setInstructionsValue('');
                if (callback) callback('');
            }
        });
    }

    /**
     * Valide la longueur des instructions
     * @param {string} instructions - Instructions à valider
     * @returns {boolean} True si valide, False sinon
     */
    function validateInstructionsLength(instructions) {
        if (instructions.length > INSTRUCTIONS_CONFIG.MAX_LENGTH) {
            showError(getInstructionsMessage('tooLong'));
            return false;
        }
        return true;
    }

    /**
     * Valide et sauvegarde les instructions
     */
    function handleSaveInstructions(event) {
        event.preventDefault();
        event.stopPropagation();
        
        const instructions = getInstructionsValue().trim();
        
        if (!validateInstructionsLength(instructions)) {
            return;
        }

        saveInstructions(instructions);
    }

    /**
     * Gère l'état du bouton de sauvegarde (loading/normal)
     * @param {boolean} isLoading - True pour activer l'état loading
     * @param {string} [loadingText] - Texte à afficher pendant le chargement (optionnel)
     */
    function setSaveButtonState(isLoading, loadingText) {
        const $btn = $els.saveInstructionsBtn;
        if (isLoading) {
            $btn.data('original-text', $btn.text())
                .prop('disabled', true);
            if (loadingText) {
                $btn.text(loadingText);
            }
        } else {
            const originalText = $btn.data('original-text') || getTranslation('Save', 'Enregistrer');
            $btn.prop('disabled', false)
                .text(originalText);
        }
    }

    /**
     * Gère le succès de la sauvegarde des instructions
     * @param {string} instructions - Instructions sauvegardées
     */
    function handleSaveSuccess(instructions) {
        originalInstructionsValue = instructions;
        updateInstructionsIndicator();
        closeInstructionsModal();
        showSuccessMessage(getInstructionsMessage('saved'));
    }

    /**
     * Envoie la requête de sauvegarde des instructions
     * @param {string} instructions - Instructions à sauvegarder
     */
    function saveInstructions(instructions) {
        setSaveButtonState(true, getInstructionsMessage('saving'));

        $.ajax({
            url: save_instructions || '/users/save-instructions/',
            type: 'POST',
            data: { saved_instructions: instructions },
            headers: getAjaxHeaders(),
            success: () => handleSaveSuccess(instructions),
            error: showError,
            complete: () => setSaveButtonState(false)
        });
    }

    /**
     * Affiche un message de succès via Toast si disponible
     * @param {string} message - Message à afficher
     */
    function showSuccessMessage(message) {
        if (window.Toast && window.Toast.success) {
            window.Toast.success(message);
        }
    }

    /**
     * Vérifie si des instructions sont sauvegardées
     * @returns {boolean} True si des instructions existent
     */
    function hasSavedInstructions() {
        return Boolean(originalInstructionsValue && originalInstructionsValue.trim().length > 0);
    }

    /**
     * Met à jour l'indicateur visuel selon l'état des instructions
     */
    function updateInstructionsIndicator() {
        const hasInstructions = hasSavedInstructions();
        $els.instructionsIndicator.toggleClass('has-instructions', hasInstructions);
    }
});

