$(document).ready(function () {

    $('.js-example-basic-single.glossary').select2();

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
            error: function (xhr, status, error) {
                console.error('Error:', error);
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
        console.log('currentEditUrl', currentEditUrl);
    });

    $('#close-edit-modal').on('click', function () {
        $edit_modal.removeClass('flex').addClass('hidden');
    });

    $form.on('submit', function (e) {
        e.preventDefault();

        const newName = $input.val();
        const formData = new FormData();
        formData.append('name', newName);

        console.log('Submitting to URL:', currentEditUrl);

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
            error: function (error) {
                console.error('Error:', error);
            }
        });
    });

    $(window).on('click', function (e) {
        if ($(e.target).is($edit_modal)) {
            $edit_modal.removeClass('flex').addClass('hidden');
        }
    });

    let sourceLanguage, targetLanguage;

    const getDomains = () => {
        if (sourceLanguage && targetLanguage) {
            $.ajax({
                url: `${get_domains}?source_language=${sourceLanguage}&target_language=${targetLanguage}`,
                type: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                success: function (response) {
                    let domainSelect = $('select[name="domain_name"]');
                    domainSelect.empty().prop('disabled', false);
                    domainSelect.append($('<option></option>').attr('value', '').text('Domain').prop('disabled', true).prop('selected', true));

                    if (response.data && response.data.length > 0) {
                        $.each(response.data, function (index, domain) {
                            domainSelect.append($('<option></option>').attr('value', domain).text(domain));
                        });
                    } else {
                        domainSelect.append($('<option></option>').attr('value', '').text('No domains available').prop('disabled', true));
                    }
                },
                error: function (xhr, status, error) {
                    console.error("Error fetching domains:", error);
                }
            });
        }
    }

    $('.js-example-basic-single.glossary[name="source_language"]').on('change', function () {
        sourceLanguage = $(this).val();
        getDomains();
    });

    $('.js-example-basic-single.glossary[name="target_language"]').on('change', function () {
        targetLanguage = $(this).val();
        getDomains();
    });
});
