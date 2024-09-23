$(document).ready(function () {
    $('input[name="username"]').attr('placeholder', 'Start typing');
    $('input[name="password"]').attr('placeholder', 'Start typing');


    $('form.login-body p').each(function() {
        if (!$(this).find('.form-group').length) {
            $(this).contents().wrapAll('<div class="form-group"></div>');
        }
    });
});
