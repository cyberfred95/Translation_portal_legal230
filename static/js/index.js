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

    let clickedResourcesOnce = false;
    $('#open-invite-modal').on('click', function (event) {
        event.stopPropagation();
        $('#invite-modal').removeClass('hidden');
    });

    $(document).on('click', function () {
        $('#invite-modal').addClass('hidden');
    });

    $('.modal-content').on('click', function (event) {
        event.stopPropagation();
    });

    $('form[name="invite"]').on('submit', function (e) {
        e.preventDefault();

        const formData = new FormData(this);
        $.ajax({
            url: invite_user_url,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            success: function () {
                $('#invite-modal').addClass('hidden');
            },
            error: function (error) {
                $('#invite-modal').addClass('hidden');
                errorNotification(error?.status, error?.responseJSON?.detail);
            }
        });
    });
});


// ------------- LOADING -------------


const startLoading = () => {
    $('#main-loader').removeClass('hidden');
}

const stopLoading = () => {
    $('#main-loader').addClass('hidden');
};
