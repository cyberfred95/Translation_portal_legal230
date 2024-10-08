$(document).ready(function() {
    $(".actions-select").attr("data-placeholder", "Action");

    $('.actions-select').select2({
        templateResult: formatOption,
        templateSelection: formatSelection,
        escapeMarkup: function(m) { return m; }
    });

    var $select = $(".actions-select");
    $select.data('select2').$container.addClass('domain');
    $select.data('select2').$dropdown.addClass('domain');

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
});
