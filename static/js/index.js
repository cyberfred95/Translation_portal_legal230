$(document).ready(function () {


    // ------------- SELECT -------------


    $(document).on('select2:open', function () {
        var $searchField = $('.select2-search__field');
        if ($searchField.length) {
            $searchField.attr('placeholder', language_code === 'en' ? 'Search' : 'Recherche');
            $searchField.focus();
        }
    });


    // ------------- CHANGE LANGUAGE -------------


    const getCurrentURL = () => {
        return window.location.href;
    }

    $(".en").click(function () {
        const url = getCurrentURL();
        window.location.href = url.replace('fr', 'en');
    });

    $(".fr").click(function () {
        const url = getCurrentURL();
        window.location.href = url.replace('en', 'fr');
    });


    // ------------- HEADER -------------


    $('.profile-trigger').on('click', function (e) {
        e.stopPropagation();
        $('#dropdown').toggleClass('hidden');
    });

    $(document).on('click', function (e) {
        if (!$(e.target).closest('.profile-container').length) {
            $('#dropdown').addClass('hidden');
        }
    });


    $(document).on('click', '[id$="-open"]', function () {
        const modalId = $(this).attr('id').replace('-open', '');
        $(`#${modalId}`).removeClass('hidden');
    });

    $(document).on('click', '[id$="-close"]', function () {
        const modalId = $(this).attr('id').replace('-close', '');
        $(`#${modalId}`).addClass('hidden');
    });

    $(document).on('click', '.modal', function (e) {
        if ($(e.target).hasClass('modal')) {
            $(this).addClass('hidden');
        }
    });

    $(document).on('click', '.modal button', function () {
        const action = $(this).text().trim().toLowerCase();
        if (action === 'так') {
            alert('Акаунт буде видалено!');
        } else if (action === 'ні') {
            $(this).closest('.modal').addClass('hidden');
        }
    });

});


// ------------- LOADING -------------

const startLoading = () => {
    $('#main-loader').removeClass('hidden');
}

const stopLoading = () => {
    $('#main-loader').addClass('hidden');
};
