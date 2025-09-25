document.addEventListener('DOMContentLoaded', function() {
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

    // Listen for text input changes
    inputText.addEventListener('input', checkProcessButton);

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