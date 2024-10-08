$(document).ready(function () {


    // ------------- SELECT -------------


    $(document).on('select2:open', () => {
        document.querySelector('.select2-search__field').setAttribute('placeholder', 'Search');
        $(".select2-search__field")[0].focus();
    });


    // ------------- CHANGE LANGUAGE -------------


    const getCurrentURL = () => {
        return window.location.href;
    }

    $(".en").click(function () {
        const url = getCurrentURL();
        window.location.href = url.replace("fr", 'en');
    });

    $(".fr").click(function () {
        const url = getCurrentURL();
        window.location.href = url.replace("en", 'fr');
    });

});


// ------------- ERROR HANDLER -------------


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
