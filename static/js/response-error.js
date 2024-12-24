const errorNotification = (status, message) => {
    console.log('status', status);
    console.log('message', message);

    const $modalError = $('#modal-error');
    const $closeModalError = $('#close-modal-error');
    const $errorMessage = $modalError.find('.error-text');

    if (!message || !status || status >= 500) {
        message = 'Something went wrong';
    }

    $errorMessage.text(message);

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
