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

    $('#delete-resources-btn').on('click', function () {
        const $button = $(this);
        const $inputContainer = $('#input-invite');
        const $hiddenInput = $('#delete-confirmation');

        if (!clickedResourcesOnce) {
            clickedResourcesOnce = true;

            $button.text('Confirm Deletion');
            $button.attr('type', 'submit');
            $inputContainer.removeClass('hidden');
        } else {
            const inputValue = $hiddenInput.val();

            if (inputValue) {
                $.ajax({
                    url: '/delete-accounts',
                    type: 'POST',
                    data: { confirmation: inputValue },
                    success: function () {
                        alert('Resources deleted successfully!');
                        $('#invite-modal').addClass('hidden');
                    },
                    error: function () {
                        alert('Error deleting accounts.');
                    }
                });
            } else {
                alert("Please enter your password to confirm.");
            }
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
