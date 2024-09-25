const errorNotification = () => {
    const $modalError = $('#modal-error');
    const $closeModalError = $('#close-modal-error');

    $modalError.removeClass('hidden');
    $closeModalError.removeClass('hidden');

    $closeModalError.on('click', function () {
        $modalError.addClass('hidden');
        $closeModalError.addClass('hidden');
    });

    $(window).on('click', function (event) {
        if ($(event.target).is($modalError)) {
            $modalError.addClass('hidden');
            $closeModalError.addClass('hidden');
        }
    });

    $(document).on('click', '.reload', function () {
        window.location.reload();
    });
};
