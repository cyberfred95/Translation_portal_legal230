document.addEventListener('DOMContentLoaded', function() {
    // ============================================================================
    // Configuration et constantes
    // ============================================================================
    const root = document.getElementById('writing-root');
    const urlProcess = root?.dataset.urlProcess;
    const trans = {
        processing: root?.dataset.transProcessing || 'Processing...',
        select_a_prompt: root?.dataset.transSelectAPrompt || 'Please select a prompt and enter some text.',
        error_occured: root?.dataset.transErrorOccured || 'An error occurred while processing your text.',
        process_text: root?.dataset.transProcessText || 'Apply',
        copied: root?.dataset.transCopied || 'Copied!',
        text_too_short: root?.dataset.transTextTooShort || 'Your text is too short to be processed.'
    };

    // Constantes de validation
    const VALIDATION = {
        MIN_WORDS: 8,
        MIN_CHARS: 32,
        CHAR_LIMIT: 2000,
        TEXTAREA_MIN_HEIGHT: 400
    };

    // ============================================================================
    // Éléments DOM
    // ============================================================================
    const promptRows = document.querySelectorAll('[data-prompt-row]');
    const processBtn = document.getElementById('process-btn');
    const inputText = document.getElementById('input-text');
    const resultsArea = document.getElementById('results-area');
    const noResults = document.getElementById('no-results');
    const resultText = document.getElementById('result-text');
    const copyBtn = document.getElementById('copy-btn');
    const charCountEl = document.getElementById('char-count');

    // ============================================================================
    // Fonctions utilitaires
    // ============================================================================
    
    /**
     * Récupère le token CSRF depuis le DOM
     * @returns {string|null} Token CSRF ou null si non trouvé
     */
    function getCSRFToken() {
        const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
        return tokenElement ? tokenElement.value : null;
    }

    /**
     * Calcule le nombre de mots dans le texte
     * @param {string} text - Texte à analyser
     * @returns {number} Nombre de mots
     */
    function getWordCount(text) {
        if (!text || text.length === 0) return 0;
        return text.split(/\s+/).filter(word => word.length > 0).length;
    }

    /**
     * Vérifie si le texte respecte les critères de validation
     * @param {string} text - Texte à valider
     * @returns {Object} Résultat de la validation avec détails
     */
    function validateText(text) {
        const wordCount = getWordCount(text);
        const charCount = text.length;
        
        return {
            isValid: wordCount >= VALIDATION.MIN_WORDS && charCount >= VALIDATION.MIN_CHARS,
            hasEnoughWords: wordCount >= VALIDATION.MIN_WORDS,
            hasEnoughChars: charCount >= VALIDATION.MIN_CHARS,
            wordCount,
            charCount
        };
    }

    /**
     * Met à jour le tooltip du bouton selon l'état de validation
     * @param {boolean} isValid - Indique si le texte est valide
     * @param {boolean} hasSelectedPrompt - Indique si un prompt est sélectionné
     */
    function updateButtonTooltip(isValid, hasSelectedPrompt) {
        if (!isValid && hasSelectedPrompt) {
            processBtn.title = trans.text_too_short;
        } else {
            processBtn.title = '';
        }
    }

    /**
     * Met à jour l'état et le tooltip du bouton de traitement
     */
    function checkProcessButton() {
        const text = inputText.value.trim();
        const hasText = text.length > 0;
        const hasSelectedPrompt = document.querySelector('input[name="selected_prompt"]:checked') !== null;
        const validation = validateText(text);
        
        const isValid = hasText && hasSelectedPrompt && validation.isValid;
        processBtn.disabled = !isValid;
        updateButtonTooltip(validation.isValid, hasSelectedPrompt);
    }

    /**
     * Calcule le nombre de caractères dans le texte (sans les retours à la ligne)
     * @returns {number} Nombre de caractères
     */
    function getInputCharCount() {
        return inputText.value.replace(/\n/g, '').length;
    }

    /**
     * Met à jour l'affichage du compteur de caractères
     */
    function updateCharCount() {
        const count = Math.min(getInputCharCount(), VALIDATION.CHAR_LIMIT);
        if (charCountEl) {
            charCountEl.textContent = `${count} / ${VALIDATION.CHAR_LIMIT}`;
        }
    }

    /**
     * Ajuste dynamiquement la hauteur du textarea
     */
    function resizeInputArea() {
        if (!inputText) return;
        inputText.style.height = 'auto';
        const nextHeight = Math.max(inputText.scrollHeight, VALIDATION.TEXTAREA_MIN_HEIGHT);
        inputText.style.height = `${nextHeight}px`;
    }

    /**
     * Tronque le texte à la limite de caractères autorisée
     */
    function truncateTextIfNeeded() {
        const current = getInputCharCount();
        if (current > VALIDATION.CHAR_LIMIT) {
            const over = current - VALIDATION.CHAR_LIMIT;
            const start = inputText.selectionStart || inputText.value.length;
            const deleteIndex = Math.max(0, start - over);
            inputText.value = inputText.value.slice(0, deleteIndex) + inputText.value.slice(deleteIndex + over);
        }
    }

    // ============================================================================
    // Fonctions de gestion de l'interface
    // ============================================================================
    
    /**
     * Réinitialise l'état visuel de toutes les lignes de prompt
     */
    function resetPromptRowsSelection() {
        promptRows.forEach(row => {
            row.classList.remove('bg-blue-50');
            row.style.backgroundColor = '';
        });
    }

    /**
     * Sélectionne visuellement une ligne de prompt
     * @param {HTMLElement} row - Ligne à sélectionner
     */
    function selectPromptRow(row) {
        row.classList.add('bg-blue-50');
        row.style.backgroundColor = '#eff6ff';
    }

    /**
     * Gère la sélection d'un prompt
     * @param {HTMLElement} row - Ligne de prompt cliquée
     */
    function handlePromptSelection(row) {
        resetPromptRowsSelection();
        selectPromptRow(row);
        
        const radio = row.querySelector('input[type="radio"]');
        if (radio) {
            radio.checked = true;
            inputText.disabled = false;
            checkProcessButton();
        }
    }

    /**
     * Affiche les résultats dans l'interface
     * @param {string|Array} result - Résultat à afficher
     */
    function displayResults(result) {
        resultText.textContent = Array.isArray(result) ? result.join('\n') : result;
        noResults.classList.add('hidden');
        resultsArea.classList.remove('hidden');
    }

    /**
     * Réinitialise l'état du bouton de traitement
     */
    function resetProcessButton() {
        processBtn.disabled = false;
        processBtn.textContent = trans.process_text;
        checkProcessButton();
    }

    /**
     * Met le bouton en état de chargement
     */
    function setProcessButtonLoading() {
        processBtn.disabled = true;
        processBtn.textContent = trans.processing;
    }

    /**
     * Traite la réponse de l'API
     * @param {Object} data - Données reçues de l'API
     */
    function handleAPIResponse(data) {
        if (data.result) {
            displayResults(data.result);
        } else if (data.detail) {
            alert(data.detail);
        } else {
            alert(trans.error_occured);
        }
    }

    /**
     * Envoie une requête de traitement à l'API
     * @param {string} promptId - ID du prompt sélectionné
     * @param {string} text - Texte à traiter
     */
    function processText(promptId, text) {
        const csrfToken = getCSRFToken();
        if (!csrfToken) {
            alert(trans.error_occured);
            return;
        }

        fetch(urlProcess, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                prompt: promptId,
                text: text
            })
        })
            .then(response => response.json())
            .then(data => handleAPIResponse(data))
            .catch(error => {
                console.error('Error:', error);
                alert(trans.error_occured);
            })
            .finally(() => resetProcessButton());
    }

    // ============================================================================
    // Gestionnaires d'événements
    // ============================================================================
    
    /**
     * Gère la sélection d'un prompt
     */
    promptRows.forEach(row => {
        row.addEventListener('click', function() {
            handlePromptSelection(this);
        });
    });

    /**
     * Gère les changements dans le champ de texte
     */
    inputText.addEventListener('input', function() {
        truncateTextIfNeeded();
        updateCharCount();
        resizeInputArea();
        checkProcessButton();
    });

    /**
     * Gère le clic sur le bouton de traitement
     */
    processBtn.addEventListener('click', function(e) {
        if (processBtn.disabled) {
            e.preventDefault();
            e.stopPropagation();
            return;
        }

        const selectedPrompt = document.querySelector('input[name="selected_prompt"]:checked');
        const text = inputText.value.trim();

        if (!selectedPrompt || !text) {
            alert(trans.select_a_prompt);
            return;
        }

        const validation = validateText(text);
        if (!validation.isValid) {
            alert(trans.text_too_short);
            return;
        }

        setProcessButtonLoading();
        processText(selectedPrompt.value, text);
    });

    /**
     * Gère le clic sur le bouton de copie
     */
    if (copyBtn) {
        copyBtn.addEventListener('click', function() {
            navigator.clipboard.writeText(resultText.textContent).then(() => {
                const originalText = copyBtn.textContent;
                copyBtn.textContent = trans.copied;
                setTimeout(() => {
                    copyBtn.textContent = originalText;
                }, 1000);
            });
        });
    }

    // ============================================================================
    // Initialisation
    // ============================================================================
    updateCharCount();
    resizeInputArea();
    checkProcessButton();
});
