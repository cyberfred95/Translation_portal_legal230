$(document).ready(function () {

    // L'ancien système de mapping des status a été remplacé par le système centralisé

    const $modal = $('#modal');
    const $closeIcon = $('#closeIcon');

    $('table').on('click', '.expert-revision', function () {
        const button = $(this);
        const translatedFile = button.data('translated-file');
        const display = button.data('display');
        console.log(typeof display);
        if (display === 'False') {
            $('.quote-hide').removeClass('hidden');
        } else if (display === 'True') {
            $('.quote-display').removeClass('hidden');
        }
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
            error: function (error) {
                errorNotification(error?.status, error?.responseJSON?.detail);
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
            success: function () {
                $deleteButton.closest('tr').remove();
            },
            error: function (error) {
                errorNotification(error?.status, error?.responseJSON?.detail);
            },
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

    // Le mapping des status est géré par le système centralisé en bas du fichier
});

/**
 * Status Management - Centralisé pour toutes les pages
 * Gère l'initialisation et le mapping des badges de status
 */

// Initialiser le mapping des status pour toutes les pages
function initializeStatusMapping() {
    console.log('initializeStatusMapping called');
    if (typeof applyStatusMapping === 'function') {
        console.log('Applying status mapping...');
        applyStatusMapping(document);
        console.log('Status mapping applied');
    } else {
        console.error('applyStatusMapping function not available!');
    }
}

// Fonction pour appliquer le mapping des status sur un élément spécifique
function applyStatusMappingToElement(element) {
    if (typeof applyStatusMapping === 'function') {
        applyStatusMapping(element);
    }
}

// Auto-initialisation quand le DOM est prêt
document.addEventListener('DOMContentLoaded', function() {
    console.log('Project History: DOM ready, initializing status mapping...');
    console.log('applyStatusMapping function available:', typeof applyStatusMapping);
    initializeStatusMapping();
});

// Export pour utilisation dans d'autres scripts
window.initializeStatusMapping = initializeStatusMapping;
window.applyStatusMappingToElement = applyStatusMappingToElement;

