$(document).ready(function () {

    $(".glossary-language-source").attr("data-placeholder", "Select from the list");
    $(".glossary-language-target").attr("data-placeholder", "Select from the list");

    $(".glossary-language-source").select2();
    $(".glossary-language-target").select2();

    $('.glossary-language-select').select2().each(function () {
        var $select = $(this);
        $select.data('select2').$container.addClass('glossary languages');
        $select.data('select2').$dropdown.addClass('glossary languages');
    });

    let file

    const $modal = $('#modal');
    const $closeIcon = $('#closeIcon');
    const maxFileSize = 5 * 1024 * 1024; // 5MB

    $('#openModal').on('click', function () {
        $modal.removeClass('hidden');
        $closeIcon.removeClass('hidden');
    });

    $('#closeModal, #closeIcon').on('click', function () {
        $('#uploadButton').removeClass('bg-transparent border border-red-400 text-red-400').addClass('bg-green-500');
        $('#downloadSample').removeClass('bg-transparent border border-gray-200 text-gray-400').addClass('bg-green-500 text-green-400 border border-green-400');
        $('.glossary-container').removeClass('bg-red-150').addClass('bg-gray-25');

        $modal.addClass('hidden');
        $closeIcon.addClass('hidden');
    });

    $(window).on('click', function (event) {
        if (event.target == $modal[0]) {
            $('#uploadButton').removeClass('bg-transparent border border-red-400 text-red-400').addClass('bg-green-500');
            $('#downloadSample').removeClass('bg-transparent border border-gray-200 text-gray-400').addClass('bg-green-500 text-green-400 border border-green-400');
            $('.glossary-container').removeClass('bg-red-150').addClass('bg-gray-25');

            $modal.addClass('hidden');
            $closeIcon.addClass('hidden');
        }
    });

    $('#uploadButton').on('click', function () {
        $('.glossary-file').click();
    });

    $('.glossary-file').on('change', function (e) {
        file = e.target.files[0];
        if (file) {
            $('#uploadButton').removeClass('bg-transparent border border-red-400 text-red-400').addClass('bg-green-500');
            $('#downloadSample').removeClass('bg-transparent border border-gray-200 text-gray-400').addClass('bg-green-500 text-green-400 border border-green-400');
            $('.glossary-container').removeClass('bg-red-150').addClass('bg-gray-25');
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

    $('button[data-url]').on('click', function () {
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

    $(document).on('click', '.delete-project', function () {
        $('.tooltip').addClass('opacity-0 invisible').removeClass('opacity-100 visible');
        $(this).find('.tooltip').removeClass('opacity-0 invisible').addClass('opacity-100 visible');
    });

    $(document).on('click', function (e) {
        if (!$(e.target).closest('.delete-project').length) {
            $('.tooltip').addClass('opacity-0 invisible').removeClass('opacity-100 visible');
        }
    });

    $(document).on('click', '.allow-delete', function () {
        const $deleteButton = $(this).closest('.delete-project');
        const deleteUrl = $deleteButton.data('delete-url');

        if (!deleteUrl) {
            return;
        }

        $.ajax({
            url: deleteUrl,
            type: 'DELETE',
            processData: false,
            contentType: false,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            success: function () {
                $deleteButton.closest('tr').remove();
            },
            error: function () {
                errorNotification();
            }
        });
    });

    $(document).on('click', '.cancel-delete', function (e) {
        e.stopPropagation();
        $(this).closest('.tooltip').addClass('opacity-0 invisible').removeClass('opacity-100 visible');
    });

    const $edit_modal = $('#edit-modal');
    const $form = $edit_modal.find('form');
    const $input = $form.find('input[type="text"]');
    const $editButtons = $('.edit-glossary');
    let currentEditUrl;

    $editButtons.on('click', function () {
        const glossaryName = $(this).closest('td').find('span').text().trim();
        $input.val(glossaryName);
        $edit_modal.removeClass('hidden').addClass('flex');
        currentEditUrl = $(this).data('edit-url');
    });

    $('#close-edit-modal').on('click', function () {
        $edit_modal.removeClass('flex').addClass('hidden');
    });

    $form.on('submit', function (e) {
        e.preventDefault();

        const newName = $input.val();
        const formData = new FormData();
        formData.append('name', newName);

        $.ajax({
            url: currentEditUrl,
            type: 'PATCH',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            success: function () {
                $edit_modal.removeClass('flex').addClass('hidden');
                window.location.reload();
            },
            error: function () {
                errorNotification();
            }
        });
    });

    $(window).on('click', function (e) {
        if ($(e.target).is($edit_modal)) {
            $edit_modal.removeClass('flex').addClass('hidden');
        }
    });

    let sourceLanguage, targetLanguage

    $('.glossary-language-source[name="source_language"]').on('change', function () {
        sourceLanguage = $(this).val();
    });

    $('.glossary-language-target[name="target_language"]').on('change', function () {
        targetLanguage = $(this).val();
    });

    $(document).on('click', '.create-glossary', function (e) {
        e.preventDefault();

        if (!file) {
            $('#uploadButton').removeClass('bg-green-500 border border-green-400').addClass('bg-transparent border border-red-400 text-red-400');
            $('#downloadSample').removeClass('bg-green-500 text-green-400 ').addClass('bg-transparent border border-gray-200 text-gray-400');
            $('.glossary-container').removeClass('bg-gray-25').addClass('bg-red-150');
            return;
        }

        const formData = new FormData();

        formData.append('file', file);
        formData.append('source_language', sourceLanguage);
        formData.append('target_language', targetLanguage);

        $.ajax({
            url: add_glossary,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            success: function () {
                window.location.reload();
            },
            error: function () {
                errorNotification();
            }
        });
    });
});
