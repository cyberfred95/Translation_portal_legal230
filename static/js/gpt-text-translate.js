$(document).ready(function () {

    let sourceQuill = new Quill('#source-text', {
        theme: 'snow',
        placeholder: language_code === 'en' ? 'Add your text here' : 'Ajoutez votre texte ici',
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

    translatedQuill.enable(false);

    $(".text-action-select").attr('data-placeholder', language_code === 'en' ? 'Action' : 'Action');

    $('.text-action-select').select2({
        templateResult: formatOption,
        templateSelection: formatSelection,
        escapeMarkup: function (m) {
            return m;
        }
    });

    var $select = $(".text-action-select");
    $select.data('select2').$container.addClass('gray action');
    $select.data('select2').$dropdown.addClass('gray action');

    function formatOption(option) {
        if (!option.id) {
            return option.text;
        }
        var splitText = option.text.split('::');
        if (splitText.length < 2) {
            return option.text;
        }
        var $option = $(
            '<div class="flex flex-col gap-1.5 group">' +
            '<div class="font-medium text-4 group-hover:font-semibold">' + splitText[0] + '</div>' +
            '<div class="font-normal text-3.5 text-gray-425 group-hover:font-medium">' + splitText[1] + '</div>' +
            '</div>'
        );
        return $option;
    }

    function formatSelection(option) {
        if (!option.id) {
            return option.text;
        }
        var splitText = option.text.split('::');
        return splitText[0];
    }

    $('form').on('submit', function (e) {
        e.preventDefault();

        let htmlContent = sourceQuill.root.innerHTML;

        $('#text').val(htmlContent);

        let form = $(this);

        let formData = new FormData(form[0]);

        startLoading();

        $.ajax({
            url: gpt_process,
            type: 'POST',
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            data: formData,
            processData: false,
            contentType: false,
            success: function (response) {
                translatedQuill.root.innerHTML = response.result;

                $('#expert-revision').removeClass('hidden');
            },
            error: function (error) {
                errorNotification(error?.status, error?.responseJSON?.detail);
            },
            complete: function () {
                stopLoading();
            }
        });
    });

    $("#clear").on('click', function () {
        translatedQuill.deleteText(0, translatedQuill.getLength());
        sourceQuill.deleteText(0, sourceQuill.getLength());

        resizeTextAreas();
    });


    $('#copy').click(function () {
        var translatedHtml = translatedQuill.root.innerHTML;

        if (translatedHtml) {
            var blob = new Blob([translatedHtml], {type: 'text/html'});
            var data = [new ClipboardItem({'text/html': blob})];

            navigator.clipboard.write(data).then(function () {
                showTooltip();
            }).catch(function (error) {
                console.error('Error copying with formatting: ', error);
            });
        }
    });


    const showTooltip = () => {
        $('#tooltip').removeClass('invisible opacity-0').addClass('visible opacity-100');
        setTimeout(function () {
            $('#tooltip').removeClass('visible opacity-100').addClass('invisible opacity-0');
        }, 2000);
    }

    function resizeTextAreas() {
        var $sourceEditor = $("#source-text .ql-editor");
        var $translatedEditor = $("#translated-text .ql-editor");

        $sourceEditor.css('height', 'auto');
        $translatedEditor.css('height', 'auto');

        var maxHeight = Math.max(
            $sourceEditor[0]?.scrollHeight || 0,
            $translatedEditor[0]?.scrollHeight || 0
        );

        maxHeight = Math.max(maxHeight, 200);

        $sourceEditor.css('height', maxHeight + 'px');
        $translatedEditor.css('height', maxHeight + 'px');
    }

    sourceQuill.on('text-change', resizeTextAreas);
    translatedQuill.on('text-change', resizeTextAreas);

    resizeTextAreas();
});
