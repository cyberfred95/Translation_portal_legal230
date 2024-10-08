$(document).ready(function () {
    $(".text-action-select").attr("data-placeholder", "Action");
    var $sourceTextarea = $("#source-text");
    var $translatedTextarea = $("#translated-text");

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
            '<div class="flex flex-col gap-1.5">' +
            '<div class="font-medium text-4">' + splitText[0] + '</div>' +
            '<div class="font-normal text-3.5 text-gray-590">' + splitText[1] + '</div>' +
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
        let form = $(this);

        let formData = new FormData(form[0]);

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
                $('#translated-text').val(response.translated_text);
                $('#expert-revision').removeClass('hidden');
            },
            error: function (xhr, status, error) {
                console.error('Translation error:', error);
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
