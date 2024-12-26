$(document).ready(function () {
    const $toggleBtn = $('#toggle-password-btn');
    const $passwordForm = $('#password-form');

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

    $('#password-form').on('submit', function (e) {
        e.preventDefault();

        const currentPassword = $('#current-password').val();
        const newPassword = $('#new-password').val();
        const confirmPassword = $('#confirm-password').val();

        if (newPassword !== confirmPassword) {
            alert('New passwords do not match!');
            return;
        }

        console.log({
            currentPassword,
            newPassword,
            confirmPassword
        });

        alert('Password updated successfully!');

        $(this)[0].reset();
        $passwordForm.addClass('hidden');
        $toggleBtn.text('Change Password');
    });
});
