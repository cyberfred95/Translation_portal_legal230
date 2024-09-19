$(document).ready(function() {
    const $modal = $('#modal');
    const $closeIcon = $('#closeIcon');

    $('#openModal').on('click', function() {
        $modal.removeClass('hidden');
        $closeIcon.removeClass('hidden');
    });

    $('#closeModal, #closeIcon').on('click', function() {
        $modal.addClass('hidden');
        $closeIcon.addClass('hidden');
    });

    $(window).on('click', function(event) {
        if (event.target == $modal[0]) {
            $modal.addClass('hidden');
            $closeIcon.addClass('hidden');
        }
    });
});
