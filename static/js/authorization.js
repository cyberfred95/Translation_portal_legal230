$(document).ready(function () {
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


    // ------------- LOGIN -------------


    $('form[name="login"]').on('submit', function (e) {
        e.preventDefault();

        const form = $(this);
        const formData = new FormData(this);

        // Скидання червоних стилів перед новою спробою
        form.find('input').removeClass('border-red-400 text-red-400');
        form.find('.error-message').remove();

        $.ajax({
            url: form.attr('action'),
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            success: function () {
                window.location.href = '/';
            },
            error: function (error) {
                const detailMessage = error?.responseJSON?.detail || 'An unknown error occurred.';

                form.find('a[href*="forgot-password"]').before(`
                    <p class="error-message text-red-400 text-sm mb-4">${detailMessage}</p>
                `);

                form.find('input').each(function () {
                    $(this).addClass('border-red-400 text-red-400');
                });
            },
        });
    });

    $('form[name="login"] input').on('input', function () {
        const form = $(this).closest('form');
        form.find('input').removeClass('border-red-400 text-red-400');
        form.find('.error-message').remove();
    });
});
