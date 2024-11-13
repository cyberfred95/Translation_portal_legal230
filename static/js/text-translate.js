$(document).ready(function () {

    $(".source-language").attr("data-placeholder",language_code === 'en'? "Source language":"Langue source");
    $(".target-language").attr("data-placeholder",language_code === 'en'? "Target language":"Langue cible");
    $(".domain-select").attr("data-placeholder",language_code === 'en'? "Glossary":"Glossaire");

    $(".source-language").select2();
    $(".target-language").select2();
    $(".domain-select").select2();

    $domainSelect = $(".domain-select").select2();
    $sourceSelect = $(".source-language").select2();
    $targetSelect = $(".target-language").select2();

    $domainSelect.data('select2').$container.addClass('action gray');
    $domainSelect.data('select2').$dropdown.addClass('action gray');

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
                error: function () {
                    errorNotification();
                }
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

    $('form').on('submit', function (e) {
        e.preventDefault();
        let form = $(this);

        let formData = new FormData(form[0]);
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
                $('#translated-text').val(response.translated_text);
                $('#expert-revision').removeClass('hidden');
            },
            error: function () {
                errorNotification();
            }
        });
    });

    $('#expert-revision').click(function () {
        const sourceText = $('#source-text').val();
        const translatedText = $('#translated-text').val();

        const data = {result: translatedText, source_text: sourceText}

        $.ajax({
            url: expert_revision,
            type: 'POST',
            data: data,
            dataType: 'json',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
                'Accept': 'application/json',
            },
            success: function () {
                $('#expert-revision').addClass('hidden');
            },
            error: function () {
                errorNotification();
            }
        });
    });

    $("#clear").on("click", function() {
        $sourceTextarea.val('');
        $translatedTextarea.val('');
        resizeTextAreas();
    });

    $('#copy').click(function () {
        var translatedText = $('#translated-text').val();
        if (translatedText) {
            navigator.clipboard.writeText(translatedText).then(function () {
                showTooltip();
            }, function (error) {
                console.error('Error: ', error);
            });
        }
    });

    const showTooltip = () => {
        $('#tooltip').removeClass('invisible opacity-0').addClass('visible opacity-100');
        setTimeout(function () {
            $('#tooltip').removeClass('visible opacity-100').addClass('invisible opacity-0');
        }, 2000);
    }

    $('#detect-language').click(function () {
        const sourceText = $('#source-text').val();

        const data = {text: sourceText}

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
            error: function () {
                errorNotification();
            }
        });
    });

    var $sourceTextarea = $("#source-text");
    var $translatedTextarea = $("#translated-text");

    function resizeTextAreas() {
        $sourceTextarea.css("height", "auto");
        $translatedTextarea.css("height", "auto");

        var maxHeight = Math.max(
            $sourceTextarea[0].scrollHeight,
            $translatedTextarea[0].scrollHeight
        );

        maxHeight = Math.max(maxHeight, 200);

        $sourceTextarea.css("height", maxHeight + "px");
        $translatedTextarea.css("height", maxHeight + "px");
    }

    $sourceTextarea.on("input", function () {
        resizeTextAreas();
    });

    resizeTextAreas();
});
