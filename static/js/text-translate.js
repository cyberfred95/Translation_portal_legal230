$(document).ready(function () {

    let sourceQuill = new Quill('#source-text', {
        theme: 'snow',
        placeholder: language_code === 'en'?'Add your text here':'Ajoutez votre texte ici',
        modules: {
            toolbar: false
        }
    });

    let translatedQuill = new Quill('#translated-text', {
        theme: 'snow',
        modules: {
            toolbar: false
        }
    });

    $(".source-language").attr("data-placeholder", language_code === 'en' ? "Source language" : "Langue source");
    $(".target-language").attr("data-placeholder", language_code === 'en' ? "Target language" : "Langue cible");
    $(".domain-select").attr("data-placeholder", language_code === 'en' ? "Glossary" : "Glossaire");

    $(".source-language").select2();
    $(".target-language").select2();
    $(".domain-select").select2({
        placeholder: $(".domain-select").data('placeholder'),
        allowClear: false
    });

    $sourceSelect = $(".source-language").select2();
    $targetSelect = $(".target-language").select2();

    $sourceSelect.data('select2').$container.addClass('languages');
    $sourceSelect.data('select2').$dropdown.addClass('languages');

    $targetSelect.data('select2').$container.addClass('languages');
    $targetSelect.data('select2').$dropdown.addClass('languages');

    // Fonctions pour sauvegarder/restaurer les langues et glossaires dans localStorage
    function saveLanguageSelection() {
        const sourceLang = $('select[name="source_language"]').val();
        const targetLang = $('select[name="target_language"]').val();
        
        if (sourceLang) localStorage.setItem('translate_source_language', sourceLang);
        if (targetLang) localStorage.setItem('translate_target_language', targetLang);
    }

    function saveGlossarySelection() {
        const glossary = $('select[name="domain_name"]').val();
        if (glossary) {
            const sourceLang = $('select[name="source_language"]').val();
            const targetLang = $('select[name="target_language"]').val();
            // Sauvegarder avec la combinaison de langues comme clé
            if (sourceLang && targetLang) {
                const langKey = `${sourceLang}_${targetLang}`;
                localStorage.setItem(`translate_glossary_${langKey}`, glossary);
            }
        }
    }

    function restoreLanguageSelection() {
        const savedSourceLang = localStorage.getItem('translate_source_language');
        const savedTargetLang = localStorage.getItem('translate_target_language');
        
        if (savedSourceLang) {
            $('select[name="source_language"]').val(savedSourceLang).trigger('change');
        }
        if (savedTargetLang) {
            $('select[name="target_language"]').val(savedTargetLang).trigger('change');
        }
    }

    function getSavedGlossary() {
        const sourceLang = $('select[name="source_language"]').val();
        const targetLang = $('select[name="target_language"]').val();
        if (sourceLang && targetLang) {
            const langKey = `${sourceLang}_${targetLang}`;
            return localStorage.getItem(`translate_glossary_${langKey}`);
        }
        return null;
    }

    // Restaurer les langues sauvegardées au chargement
    restoreLanguageSelection();

    // Event listener pour sauvegarder la sélection du glossaire
    $('select[name="domain_name"]').on('change', function () {
        saveGlossarySelection();
        validateTranslateButton();
    });

    // Spinner pour le chargement des glossaires (placé à gauche du dropdown)
    (function initGlossarySpinner(){
        const domainSelect = $('select.domain-select');
        if ($('#glossary-spinner').length === 0 && domainSelect.length) {
            const spinner = $('<span id="glossary-spinner" class="inline-block w-5 h-5 mr-2 rounded-full border border-gray-300 border-t-green-800 animate-spin hidden"></span>');
            // Insérer le spinner juste avant le conteneur Select2 (qui se trouve juste après le <select>)
            const select2Container = domainSelect.next('.select2');
            if (select2Container.length) {
                select2Container.before(spinner);
            } else {
                // fallback: avant le <select>
                domainSelect.before(spinner);
            }
        }
    })();

    function enhanceSelect2Arrows() {
        $('.select2-container .select2-selection').each(function () {
            // Assurer un contexte de positionnement
            $(this).css({ position: 'relative' });
            // Ajouter du padding à droite du texte pour ne pas chevaucher l'icône
            $(this).find('.select2-selection__rendered').css({ 'padding-right': '2rem' });

            const $arrow = $(this).find('.select2-selection__arrow');
            // Cacher l'élément flèche par défaut
            $arrow.find('b').hide();

            // Positionner proprement l'icône
            $arrow.css({
                position: 'absolute',
                right: '8px',
                top: '50%',
                transform: 'translateY(-50%)',
                width: '20px',
                height: '20px',
                display: 'flex',
                'align-items': 'center',
                'justify-content': 'center'
            });

            // Forcer une seule icône et utiliser la version pleine (fill)
            $arrow.find('i.ph').remove();
            $arrow.append('<i class="ph ph-caret-down ph-fill text-gray-500 text-lg"></i>');
        });
    }

    // Appliquer les icônes Phosphor aux flèches des dropdowns
    enhanceSelect2Arrows();

    let sourceLanguage, targetLanguage;

    const getDomains = () => {
        if (sourceLanguage && targetLanguage) {
            $.ajax({
                url: `${get_domains}?source_language=${sourceLanguage}&target_language=${targetLanguage}`,
                type: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                beforeSend: function(){
                    $('#glossary-spinner').removeClass('hidden');
                },
                success: function (response) {
                    let domainSelect = $('select[name="domain_name"]');
                    if (response.data.length !== 0) {
                        domainSelect.empty();
                        // laisser activé pour garder le même style
                        domainSelect.append($('<option></option>').attr('value', '').text('Domain').prop('disabled', true));

                        $.each(response.data, function (index, domain) {
                            domainSelect.append($('<option></option>').attr('value', domain).text(domain));
                        });

                        // Essayer de restaurer le glossaire précédemment utilisé pour cette combinaison de langues
                        const savedGlossary = getSavedGlossary();
                        let selectedVal = null;
                        
                        if (savedGlossary && domainSelect.find(`option[value="${savedGlossary}"]`).length > 0) {
                            // Le glossaire sauvegardé existe dans la liste, l'utiliser
                            selectedVal = savedGlossary;
                        } else {
                            // Sinon, sélectionner le premier domaine valide (y compris le générique)
                            selectedVal = domainSelect.find('option:not(:disabled):first').val();
                        }
                        
                        if (selectedVal) {
                            domainSelect.val(selectedVal).trigger('change.select2');
                        }
                        // Revalider le bouton après sélection
                        if (typeof validateTranslateButton === 'function') {
                            validateTranslateButton();
                        }
                    }
                },
                error: function (error) {
                    errorNotification(error?.status, error?.responseJSON?.detail);
                },
                complete: function(){
                    $('#glossary-spinner').addClass('hidden');
                }
            });
        }
    }

    $('select[name="source_language"]').change(function () {
        sourceLanguage = $(this).val();
        // Sauvegarder la sélection
        saveLanguageSelection();
        // Réinitialiser le glossaire (Select2) lorsqu'on change la langue source
        const domainSelect = $('select[name="domain_name"]');
        domainSelect.val(null).trigger('change');
        validateTranslateButton();
        getDomains();
    });

    $('select[name="target_language"]').change(function () {
        targetLanguage = $(this).val();
        // Sauvegarder la sélection
        saveLanguageSelection();
        // Réinitialiser le glossaire (Select2) lorsqu'on change la langue cible
        const domainSelect = $('select[name="domain_name"]');
        domainSelect.val(null).trigger('change');
        validateTranslateButton();
        getDomains();
    });

    $('form[name="text-translate"]').on('submit', function (e) {
        e.preventDefault();
        const CHAR_LIMIT = 2000;
        const currentCount = sourceQuill.getText().replace(/\n/g, '').length;
        if (currentCount > CHAR_LIMIT) {
            return;
        }
        let htmlContent = sourceQuill.root.innerHTML;

        $('#text').val(htmlContent);

        let form = $(this);

        let formData = new FormData(form[0]);

        $('#main-loader').removeClass('hidden');

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
            success: function (response) {
                translatedQuill.root.innerHTML = response.translated_text[0];
            },
            error: function (error) {
                errorNotification(error?.status, error?.responseJSON?.detail);
            },
            complete: function () {
                $('#main-loader').addClass('hidden');
            }
        });
    });

    $("#clear, #clear-source").on("click", function () {
        translatedQuill.deleteText(0, translatedQuill.getLength());
        sourceQuill.deleteText(0, sourceQuill.getLength());

        resizeTextAreas();
        validateTranslateButton();
    });


    $('#copy, .copy').click(function () {
        var translatedText = translatedQuill.getText();
        var translatedHtml = translatedQuill.root.innerHTML;

        if (translatedHtml) {
            if (navigator.clipboard && window.ClipboardItem) {
                var htmlBlob = new Blob([translatedHtml], { type: 'text/html' });
                var textBlob = new Blob([translatedText], { type: 'text/plain' });
                var data = [
                    new ClipboardItem({
                        'text/html': htmlBlob,
                        'text/plain': textBlob
                    })
                ];

                navigator.clipboard.write(data).then(function () {
                    showTooltip();
                }).catch(function (error) {
                    console.error('Помилка копіювання: ', error);
                });
            } else {
                console.error('Clipboard API не підтримується у цьому браузері.');
                alert('Ваш браузер не підтримує Clipboard API. Спробуйте оновити браузер.');
            }
        }
    });


    const showTooltip = () => {
        $('#tooltip').removeClass('invisible opacity-0').addClass('visible opacity-100');
        setTimeout(function () {
            $('#tooltip').removeClass('visible opacity-100').addClass('invisible opacity-0');
        }, 2000);
    }

    $('#detect-language').click(function () {
        const sourceText = sourceQuill.getText();

        const data = {text: sourceText}

        $('#main-loader').removeClass('hidden');

        $.ajax({
            url: detect_text_language,
            type: 'POST',
            data: data,
            dataType: 'json',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
                'Accept': 'application/json',
            },
            success: function (response) {
                const detectedLanguage = response.language.toLowerCase();

                const $select = $('select[name="source_language"]');

                $select.val(detectedLanguage).trigger('change');
            },
            error: function (error) {
                errorNotification(error?.status, error?.responseJSON?.detail);
            },
            complete: function () {
                $('#main-loader').addClass('hidden');
            }
        });
    });

    function resizeTextAreas() {
        var $sourceEditor = $("#source-text .ql-editor");
        var $translatedEditor = $("#translated-text .ql-editor");

        $sourceEditor.css("height", "auto");
        $translatedEditor.css("height", "auto");

        var maxHeight = Math.max(
            $sourceEditor[0]?.scrollHeight || 0,
            $translatedEditor[0]?.scrollHeight || 0
        );

        maxHeight = Math.max(maxHeight, 400);

        $sourceEditor.css("height", maxHeight + "px");
        $translatedEditor.css("height", maxHeight + "px");
    }

    const CHAR_LIMIT = 2000;
    function getSourceCharCount() {
        return sourceQuill.getText().replace(/\n/g, '').length;
    }
    function updateCharCount() {
        var count = getSourceCharCount();
        $('#source-char-count').text(Math.min(count, CHAR_LIMIT));
    }

    function validateTranslateButton() {
        const hasSource = $('select[name="source_language"]').val();
        const hasTarget = $('select[name="target_language"]').val();
        const hasDomain = $('select[name="domain_name"]').val();
        const disabled = !(hasSource && hasTarget && hasDomain);
        $("#btn-translate").prop('disabled', disabled);
    }

    sourceQuill.on("text-change", function(delta, oldDelta, source){
        if (source !== 'user') {
            updateCharCount();
            validateTranslateButton();
            return;
        }
        var count = getSourceCharCount();
        if (count > CHAR_LIMIT) {
            var over = count - CHAR_LIMIT;
            var sel = sourceQuill.getSelection(true);
            var deleteIndex = sel ? Math.max(0, sel.index - over) : Math.max(0, sourceQuill.getLength() - 1 - over);
            sourceQuill.deleteText(deleteIndex, over, 'user');
            updateCharCount();
            return;
        }
        resizeTextAreas();
        updateCharCount();
        validateTranslateButton();
    });
    translatedQuill.on("text-change", function(){
        resizeTextAreas();
        const hasTranslated = translatedQuill.getText().replace(/\n/g, '').length > 0;
        if (hasTranslated) {
            $('#btn-copy').removeClass('hidden');
        } else {
            $('#btn-copy').addClass('hidden');
        }
    });

    resizeTextAreas();
    // init état du bouton copier
    const hasTranslatedInit = translatedQuill.getText().replace(/\n/g, '').length > 0;
    if (hasTranslatedInit) {
        $('#btn-copy').removeClass('hidden');
    } else {
        $('#btn-copy').addClass('hidden');
    }
    updateCharCount();
    validateTranslateButton();
});


/**
 * MODAL
 */
document.addEventListener('DOMContentLoaded', function() {
    // Tronquer proprement le collage au lieu de bloquer complètement
    const sourceRoot = document.querySelector('#source-text .ql-editor')?.parentElement;
    if (sourceRoot) {
        sourceRoot.addEventListener('paste', function (e) {
            var clipboardData = e.clipboardData || window.clipboardData;
            if (!clipboardData) return;
            var text = clipboardData.getData('text');
            if (typeof text !== 'string') return;
            var current = (window.sourceQuill || null) ? window.sourceQuill.getText().replace(/\n/g, '').length : getSourceCharCount();
            var available = 2000 - current;
            if (available <= 0) {
                e.preventDefault();
                return;
            }
            var toInsert = text.replace(/\r?\n/g, ' ').slice(0, available);
            e.preventDefault();
            var sel = (window.sourceQuill || null) ? window.sourceQuill.getSelection(true) : null;
            if (!sel) sel = { index: (window.sourceQuill || null) ? window.sourceQuill.getLength() : 0, length: 0 };
            (window.sourceQuill || null) ? window.sourceQuill.insertText(sel.index, toInsert, 'user') : null;
        }, true);
    }
    const modal = document.getElementById('modal');
    const closeModalBtn = document.getElementById('closeModal');
    const closeIcon = document.getElementById('closeIcon');
    const checkbox = document.querySelector('input[type="checkbox"].peer');

    function closeModal() {
        modal.classList.add('hidden');
        checkbox.checked = false;
    }

    checkbox.addEventListener('change', function() {
        if (!checkbox.checked) {
            modal.classList.add('hidden');
        } else {
            modal.classList.remove('hidden');
        }
    });

    closeModalBtn?.addEventListener('click', closeModal);
    closeIcon?.addEventListener('click', closeModal);

    modal?.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeModal();
        }
    });
});
