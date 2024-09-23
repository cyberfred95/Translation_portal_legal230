$(document).ready(function () {
    const $modal = $('#modal');
    const $closeIcon = $('#closeIcon');
    const maxFileSize = 5 * 1024 * 1024; // 5MB

    $('#openModal').on('click', function () {
        $modal.removeClass('hidden');
        $closeIcon.removeClass('hidden');
    });

    $('#closeModal, #closeIcon').on('click', function () {
        $modal.addClass('hidden');
        $closeIcon.addClass('hidden');
    });

    $(window).on('click', function (event) {
        if (event.target == $modal[0]) {
            $modal.addClass('hidden');
            $closeIcon.addClass('hidden');
        }
    });

    $('#uploadButton').on('click', function () {
        $('.glossary-file').click();
    });

    $('.glossary-file').on('change', function (e) {
        var file = e.target.files[0];
        if (file) {
            if (file.size <= maxFileSize) {
                showUploadedFile(file.name);
            } else {
                alert('File size exceeds 5MB limit.');
                $(this).val('');
            }
        }
    });

    function showUploadedFile(fileName) {
        $('#fileName').text(fileName);
        $('#fileInfo').removeClass('hidden');
        $('#uploadButton').addClass('hidden');
    }

    $(document).on('click', '.remove-file', function () {
        resetUploadArea();
    });

    function resetUploadArea() {
        $('#uploadButton').removeClass('hidden');
        $('#fileInfo').addClass('hidden');
        $('.glossary-file').val('');
    }

    $('button[data-url]').on('click', function() {
        const fileUrl = $(this).data('url');
        if (fileUrl) {
            downloadFile(fileUrl);
        }
    });

    function downloadFile(url) {
        const $link = $('<a>', {
            href: url,
            download: '',
            style: 'display: none;'
        }).appendTo('body');

        $link[0].click();

        $link.remove();
    }
});
