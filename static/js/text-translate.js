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
    $(".domain-select").select2();

    $sourceSelect = $(".source-language").select2();
    $targetSelect = $(".target-language").select2();

    $sourceSelect.data('select2').$container.addClass('languages');
    $sourceSelect.data('select2').$dropdown.addClass('languages');

    $targetSelect.data('select2').$container.addClass('languages');
    $targetSelect.data('select2').$dropdown.addClass('languages');

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
                success: function (response) {
                    let domainSelect = $('select[name="domain_name"]');
                    if (response.data.length !== 0) {
                        domainSelect.empty();
                        domainSelect.prop('disabled', false);
                        domainSelect.append($('<option></option>').attr('value', '').text('Domain').prop('disabled', true));

                        $.each(response.data, function (index, domain) {
                            domainSelect.append($('<option></option>').attr('value', domain).text(domain));
                        });

                        domainSelect.find('option:not(:disabled):first').prop('selected', true);
                    }
                },
                error: function (error) {
                    errorNotification(error?.status, error?.responseJSON?.detail);
                },
            });
        }
    }

    $('select[name="source_language"]').change(function () {
        sourceLanguage = $(this).val();
        getDomains();
    });

    $('select[name="target_language"]').change(function () {
        targetLanguage = $(this).val();
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

        maxHeight = Math.max(maxHeight, 200);

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

    sourceQuill.on("text-change", function(delta, oldDelta, source){
        if (source !== 'user') {
            updateCharCount();
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
    });
    translatedQuill.on("text-change", resizeTextAreas);

    resizeTextAreas();
    updateCharCount();
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
