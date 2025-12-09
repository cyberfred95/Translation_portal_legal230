// ============================================================================
// WRITING FUNCTIONALITY - TEMPORARILY DISABLED
// ============================================================================
// Cette fonctionnalité est temporairement désactivée en prévision d'une refonte.
// Tout le code est conservé en commentaire pour référence future.
// ============================================================================

/*
document.addEventListener('DOMContentLoaded', function() {
    // Récupération des data-attributes du root
    const root = document.getElementById('writing-root');
    const urlProcess = root?.dataset.urlProcess;
    const trans = {
        processing: root?.dataset.transProcessing || 'Processing...',
        select_a_prompt: root?.dataset.transSelectAPrompt || 'Please select a prompt and enter some text.',
        error_occured: root?.dataset.transErrorOccured || 'An error occurred while processing your text.',
        process_text: root?.dataset.transProcessText || 'Apply',
        copied: root?.dataset.transCopied || 'Copied!'
    };

    // Prompt data (construit depuis le DOM)
    // Utilise les radios existants pour reconstruire un mapping minimal id->meta
    const promptData = {};
    document.querySelectorAll('input[name="selected_prompt"]').forEach(radio => {
        const row = radio.closest('[data-prompt-row]');
        if (!row) return;
        // On peut enrichir si besoin en lisant des data-attributes sur row
        promptData[radio.value] = promptData[radio.value] || {};
    });
    // Handle prompt selection
    const promptRows = document.querySelectorAll('[data-prompt-row]');
    const processBtn = document.getElementById('process-btn');
    const inputText = document.getElementById('input-text');
    const resultsArea = document.getElementById('results-area');
    const noResults = document.getElementById('no-results');
    const resultText = document.getElementById('result-text');
    const copyBtn = document.getElementById('copy-btn');
    const promptMeta = document.getElementById('prompt-meta');

    promptRows.forEach(row => {
        row.addEventListener('click', function() {
            // Remove selected state from all rows
            promptRows.forEach(r => {
                r.classList.remove('bg-blue-50');
                r.style.backgroundColor = '';
            });

            // Add selected state to clicked row
            this.classList.add('bg-blue-50');
            this.style.backgroundColor = '#eff6ff';

            // Update radio button
            const radio = this.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;


                // Show prompt details
                const promptId = radio.value;
                console.log(promptData);
                console.log(promptId);
                const prompt = promptData[promptId];
                console.log(prompt);

                if (prompt) {
                    // document.getElementById('selected-prompt-name').textContent = prompt.name;
                    // document.getElementById('selected-prompt-description').textContent = prompt.description;
                    // document.getElementById('selected-prompt-model').textContent = prompt.model;
                    // document.getElementById('selected-prompt-temperature').textContent = prompt.temperature;

                    // Show meta info
                    // promptMeta.style.display = 'flex';

                    // Enable text input
                    inputText.disabled = false;

                    // Check if we can enable process button
                    checkProcessButton();
                }
            }
        });
    });

    // Check if process button should be enabled
    function checkProcessButton() {
        const hasText = inputText.value.trim().length > 0;
        const hasSelectedPrompt = document.querySelector('input[name="selected_prompt"]:checked');

        processBtn.disabled = !(hasText && hasSelectedPrompt);
    }

    const CHAR_LIMIT = 2000;
    const charCountEl = document.getElementById('char-count');

    function getInputCharCount() {
        return inputText.value.replace(/\n/g, '').length;
    }

    function updateCharCount() {
        const count = Math.min(getInputCharCount(), CHAR_LIMIT);
        if (charCountEl) {
            charCountEl.textContent = `${count} / ${CHAR_LIMIT}`;
        }
    }

    function resizeInputArea() {
        // Ajuster dynamiquement la hauteur du textarea, min 400px
        if (!inputText) return;
        inputText.style.height = 'auto';
        const minHeight = 400; // comme text-translate
        const nextHeight = Math.max(inputText.scrollHeight, minHeight);
        inputText.style.height = `${nextHeight}px`;
    }

    // Listen for text input changes
    inputText.addEventListener('input', function(e){
        // Tronquer à la limite de caractères, comme text-translate
        const current = getInputCharCount();
        if (current > CHAR_LIMIT) {
            const over = current - CHAR_LIMIT;
            const start = inputText.selectionStart || inputText.value.length;
            // Supprimer l'excédent en partant avant le curseur
            const deleteIndex = Math.max(0, start - over);
            inputText.value = inputText.value.slice(0, deleteIndex) + inputText.value.slice(deleteIndex + over);
        }
        updateCharCount();
        resizeInputArea();
        checkProcessButton();
    });

    // Initialiser l'affichage du compteur et l'état du bouton
    updateCharCount();
    resizeInputArea();
    checkProcessButton();

    // Handle process button click
    processBtn.addEventListener('click', function() {
        const selectedPrompt = document.querySelector('input[name="selected_prompt"]:checked');
        const text = inputText.value.trim();

        if (!selectedPrompt || !text) {
            alert(trans.select_a_prompt);
            return;
        }

        // Show loading state
        processBtn.disabled = true;
        processBtn.textContent = trans.processing;

        // Make API call
        fetch(urlProcess, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                prompt: selectedPrompt.value,
                text: text
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.result) {
                    // Show results
                    resultText.textContent = Array.isArray(data.result) ? data.result.join('\n') : data.result;
                    noResults.classList.add('hidden');
                    resultsArea.classList.remove('hidden');
                } else {
                    alert(trans.error_occured);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert(trans.error_occured);
            })
            .finally(() => {
                // Reset button state
                processBtn.disabled = false;
                processBtn.textContent = trans.process_text;
                checkProcessButton();
            });
    });

    // Handle copy button click
    if (copyBtn) {
        copyBtn.addEventListener('click', function() {
            navigator.clipboard.writeText(resultText.textContent).then(() => {
                // Show feedback
                const originalText = copyBtn.textContent;
                copyBtn.textContent = trans.copied;
                setTimeout(() => {
                    copyBtn.textContent = originalText;
                }, 1000);
            });
        });
    }
});
*/
