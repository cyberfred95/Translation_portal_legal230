$(document).ready(function () {

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
                error: function (xhr, status, error) {
                    console.error("Error fetching domains:", error);
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
            url: text_translate,
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
            error: function (xhr, status, error) {
                console.error('Translation error:', error);
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
            error: function (xhr, status, error) {
                console.error('Expert revision error:', error);
            }
        });
    });

    $('#clear').click(function () {
        $('#source-text').val('');
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
});
