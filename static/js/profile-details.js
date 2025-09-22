$(document).ready(function () {
    const $toggleBtn = $('#toggle-password-btn');
    const $passwordForm = $('#password-form');
    const $currentPwd = $('#current-password');
    const $newPwd = $('#new-password');
    const $confirmPwd = $('#confirm-password');
    const $updateBtn = $('#update-password-btn');
    const $confirmError = $('#confirm-error');

    $toggleBtn.on('click', function () {
        const isHidden = $passwordForm.hasClass('hidden');
        $passwordForm.toggleClass('hidden');
        $toggleBtn.text(isHidden ? 'Close' : 'Change Password');
    });

    function toggleVisibility(id, $icon) {
        const $input = $('#' + id);
        const isPassword = $input.attr('type') === 'password';

        $input.attr('type', isPassword ? 'text' : 'password');

        $icon.find('.eye-icon.open').toggleClass('hidden', !isPassword);
        $icon.find('.eye-icon.closed').toggleClass('hidden', isPassword);
    }

    $('.toggle-visibility').on('click', function () {
        const id = $(this).data('target');
        toggleVisibility(id, $(this));
    });

    function validateForm() {
        const currentVal = $currentPwd.val().trim();
        const newVal = $newPwd.val().trim();
        const confirmVal = $confirmPwd.val().trim();

        let isValid = true;

        if (!currentVal || !newVal || !confirmVal) {
            isValid = false;
        }
        if (newVal !== confirmVal && (newVal.length > 0 && confirmVal.length > 0)) {
            isValid = false;
            $confirmError
                .text('Passwords do not match')
                .removeClass('hidden');
        } else {
            $confirmError.addClass('hidden');
        }

        $updateBtn.prop('disabled', !isValid);
    }

    $currentPwd.on('input', validateForm);
    $newPwd.on('input', validateForm);
    $confirmPwd.on('input', validateForm);

    $('#password-form').on('submit', function (e) {
        e.preventDefault();

        const formData = new FormData(this);

        $.ajax({
            url: change_password_url,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            success: function () {
                $('#success-change-password').removeClass('hidden');
            },
            error: function (error) {
                errorNotification(error?.status, error?.responseJSON?.detail);
            }
        });
    });

    let clickedOnce = false;

    $('#modal-delete-account').on('click', function (event) {
        event.stopPropagation();
        $('#delete-account-modal').removeClass('hidden');
    });

    $('#success-update-btn').on('click', function (event) {
        event.stopPropagation();
        $('#success-update-user-data').addClass('hidden');
        window.location.reload();
    });

    $('#success-change-password-btn').on('click', function (event) {
        event.stopPropagation();
        $('#success-change-password').addClass('hidden');
    });

    $(document).on('click', function () {
        $('#success-change-password').addClass('hidden');
    });

    $(document).on('click', function () {
        const $element = $('#success-update-user-data');

        if ($element.hasClass('hidden')) {
            $element.addClass('hidden');
        } else {
            window.location.reload();
        }
    });

    $(document).on('click', function () {
        $('#delete-account-modal').addClass('hidden');
    });

    $('.modal-content').on('click', function (event) {
        event.stopPropagation();
    });

    $('#cancel-account-btn').on('click', function () {
        $('#delete-account-modal').addClass('hidden');
    });

    $('#delete-account-btn').on('click', function (event) {
        event.preventDefault();

        const $button = $(this);
        const $inputContainer = $('#input-container');
        const $hiddenInput = $('#delete-account');

        if (!clickedOnce) {
            clickedOnce = true;

            $button.text('Confirm Deletion');
            $button.attr('type', 'submit');
            $inputContainer.removeClass('hidden');
        } else {
            const inputValue = $hiddenInput.val();
            const encodedValue = btoa(inputValue);

            const formData = new FormData();

            formData.append('password', encodedValue);

            $.ajax({
                url: delete_user_url,
                type: 'DELETE',
                data: formData,
                processData: false,
                contentType: false,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                success: function () {
                    $('#delete-account-modal').addClass('hidden');
                    window.location.reload();
                },
                error: function (error) {
                    errorNotification(error?.status, error?.responseJSON?.detail);
                }
            });
        }
    });

    let clickedResourcesOnce = false;

    $('#modal-delete-resources').on('click', function (event) {
        event.stopPropagation();
        $('#delete-resources-modal').removeClass('hidden');
    });

    $(document).on('click', function () {
        $('#delete-resources-modal').addClass('hidden');
    });

    $('.modal-content').on('click', function (event) {
        event.stopPropagation();
    });

    $('#cancel-resources-btn').on('click', function () {
        $('#delete-resources-modal').addClass('hidden');
    });

    $('#delete-resources-btn').on('click', function (event) {
        event.preventDefault();

        const $button = $(this);
        const $inputContainer = $('#input-resources');
        const $hiddenInput = $('#delete-resources');

        if (!clickedResourcesOnce) {
            clickedResourcesOnce = true;

            $button.text('Confirm Deletion');
            $button.attr('type', 'submit');
            $inputContainer.removeClass('hidden');
        } else {
            const inputValue = $hiddenInput.val();
            const encodedValue = btoa(inputValue);

            const formData = new FormData();

            formData.append('password', encodedValue);

            if (inputValue) {
                $.ajax({
                    url: delete_resources_url,
                    type: 'POST',
                    data: formData,
                    processData: false,
                    contentType: false,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    success: function () {
                        $('#delete-resources-modal').addClass('hidden');
                    },
                    error: function (error) {
                        errorNotification(error?.status, error?.responseJSON?.detail);
                    }
                });
            }
        }
    });

    $('form[name="change-user-data"]').on('submit', function (e) {
        e.preventDefault();

        const formData = new FormData(this);

        $.ajax({
            url: change_data_url,
            type: 'PUT',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            success: function () {
                $('#success-update-user-data').removeClass('hidden');
            },
            error: function (error) {
                errorNotification(error?.status, error?.responseJSON?.detail);
            }
        });
    });


    // ------------- TABS -------------

    function showTab(tabId) {
        // Masquer tous les contenus de tabs
        $('.tab-content').hide();
        // Afficher le contenu du tab sélectionné
        $(`#${tabId}-content`).show();

        // Retirer les styles actifs de tous les boutons
        $('button.tab').removeClass('bg-white text-gray-900 font-bold');
        $('button.tab').addClass('text-gray-900 hover:text-gray-900 text-gray-300');

        // Ajouter les styles actifs au bouton sélectionné
        $(`#${tabId}`).removeClass('text-gray-900 hover:text-gray-900 text-gray-300');
        $(`#${tabId}`).addClass('bg-white text-gray-900 font-bold');
    }

    let initialTab = 'profile-information';

    showTab(initialTab);

    $('#profile-information').click(function () {
        showTab('profile-information');
    });

    $('#profile-security').click(function () {
        showTab('profile-security');
    });

});
