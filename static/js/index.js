$(document).ready(function () {


    // ------------- SELECT -------------


    $(document).on('select2:open', function () {
        var $searchField = $('.select2-search__field');
        if ($searchField.length) {
            $searchField.attr('placeholder', language_code === 'en' ? 'Search' : 'Recherche');
            $searchField.focus();
        }
    });

    $('.glossary-language-select').select2().each(function () {
        var $select = $(this);
        $select.data('select2').$container.addClass('glossary');
        $select.data('select2').$dropdown.addClass('glossary');
    });


    // ------------- CHANGE LANGUAGE -------------


    const getCurrentURL = () => {
        return window.location.href;
    }

    $(".en").click(function () {
        const url = getCurrentURL();
        window.location.href = url.replace('/fr/', '/en/');
    });

    $(".fr").click(function () {
        const url = getCurrentURL();
        window.location.href = url.replace('/en/', '/fr/');
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
});


// ------------- LOADING -------------


const startLoading = () => {
    $('#main-loader').removeClass('hidden');
}

const stopLoading = () => {
    $('#main-loader').addClass('hidden');
};
