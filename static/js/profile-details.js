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

        const formData = new FormData();
        formData.append('current_password', $currentPwd.val());
        formData.append('new_password', $newPwd.val());
        formData.append('confirm_password', $confirmPwd.val());

        $.ajax({
            url: change_password,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
        });
    });
});
