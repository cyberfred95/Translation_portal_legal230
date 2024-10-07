$(document).ready(function () {
    $(".actions-select").attr("data-placeholder", "Action");
    $(".actions-select").select2();

    $select = $(".actions-select").select2();

    $select.data('select2').$container.addClass('domain');
    $select.data('select2').$dropdown.addClass('domain');
});
