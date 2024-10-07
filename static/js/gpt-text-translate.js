$(document).ready(function () {
    $(".action-select").attr("data-placeholder", "Action");
    $(".action-select").select2();

    $select = $(".action-select").select2();

    $select.data('select2').$container.addClass('domain');
    $select.data('select2').$dropdown.addClass('domain');
});
