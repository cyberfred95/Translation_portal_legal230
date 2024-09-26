$(document).ready(function () {

    $('td').each(function () {
        var statusElement = $(this).find('.status');
        var statusText = statusElement.text().trim();
        switch (statusText) {
            case 'Being translated':
                statusElement.text('Processing...');
                statusElement.addClass('text-green-700');
                break;
            case 'Translated':
                statusElement.text('Translated');
                statusElement.addClass('bg-green-350 text-green-650');
                break;
            case 'Sent to post-editing, not accepted yet':
                statusElement.text('Request for post-editing sent');
                statusElement.addClass('bg-yellow-100 text-yellow-400');
                break;
            case 'Sent to post-editing, accepted':
                statusElement.text('Request for post-editing accepted');
                statusElement.addClass('bg-blue-100 text-blue-400');
                break;
            case 'Post-edited file uploaded':
                statusElement.text('Post-edited file uploaded');
                statusElement.addClass('bg-green-370 text-green-750');
                break;
            case 'Error':
                statusElement.text('Error');
                statusElement.addClass('bg-red-100 text-red-400');
                break;
            default:
                break;
        }
    });

    const $modal = $('#modal');
    const $closeIcon = $('#closeIcon');

    $('table').on('click', '.expert-revision', function () {
        const button = $(this);
        const translatedFile = button.data('translated-file');
        const id = button.data('id');

        $modal.data('translatedFile', translatedFile);
        $modal.data('projectId', id);

        $modal.removeClass('hidden');
        $closeIcon.removeClass('hidden');
    });

    $('#closeIcon').on('click', function () {
        $modal.addClass('hidden');
        $closeIcon.addClass('hidden');
    });

    $(window).on('click', function (event) {
        if (event.target == $modal[0]) {
            $modal.addClass('hidden');
            $closeIcon.addClass('hidden');
        }
    });

    $modal.on('click', '.expert-revision', function () {
        const translatedFile = $modal.data('translatedFile');
        const id = $modal.data('projectId');

        let formData = new FormData();
        formData.append('file_url', translatedFile);
        formData.append('project_id', id);

        $.ajax({
            type: 'POST',
            url: expert_revision_file_url,
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
                'Accept': 'application/json',
            },
            dataType: 'json',
            success: function () {
                window.location.reload();
            },
            error: function (xhr, status, error) {
                console.error('Error:', error);
            }
        });

        $modal.addClass('hidden');
        $closeIcon.addClass('hidden');
    });

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
        const projectId = $deleteButton.data('project-id');
        if (!projectId) {
            console.error('Project ID not found');
            return;
        }
        const formData = new FormData();
        formData.append('project_id', projectId);
        $.ajax({
            url: single_project,
            type: 'DELETE',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            success: function (response) {
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

    $('.download-file').on('click', function(e) {
        e.preventDefault();
        const $button = $(this);
        const translatedFile = $button.data('translated-file');
        const reviewedFile = $button.data('reviewed-file');

        if (reviewedFile) {
            const $tooltip = $button.siblings('.download-tooltip');
            $tooltip.toggleClass('hidden');

            $(document).one('click', function closeTooltip(e) {
                if (!$(e.target).closest('.download-tooltip').length && !$(e.target).closest('.download-file').length) {
                    $tooltip.addClass('hidden');
                } else {
                    $(document).one('click', closeTooltip);
                }
            });
        } else if (translatedFile) {
            window.location.href = translatedFile;
        }
    });

    $(document).on('click', '.download-file-option', function(e) {
        e.preventDefault();
        e.stopPropagation();
        const fileUrl = $(this).data('file-url');
        if (fileUrl) {
            window.location.href = fileUrl;
        }
    });
});

