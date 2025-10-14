$(document).ready(function () {
    // Appliquer le mapping des statuts au chargement de la page
    applyStatusMapping();

    const $modalRevision = $('#modal-revision');
    const $closeRevision = $('#close-revision');

    // Gestion du clic sur le bouton expert-revision dans le tableau
    $('table').on('click', '.expert-revision', function () {
        if ($(this).prop('disabled')) return;

        const button = $(this);
        const translatedFile = button.data('translated-file');
        const id = button.data('id');
        const display = button.data('display');

        // Transfert des données au bouton dans la modale
        $('.expert-revision', $modalRevision)
            .data('translated-file', translatedFile)
            .data('id', id);

        // Affichage de la modale selon data-display
        if (display === false || display === 'False') {
            // Afficher show-modal-true (formulaire avec bouton)
            $('.show-modal-true', $modalRevision).removeClass('hidden');
            $('.show-modal-false', $modalRevision).addClass('hidden');
        } else {
            // Afficher show-modal-false (message contact)
            $('.show-modal-true', $modalRevision).addClass('hidden');
            $('.show-modal-false', $modalRevision).removeClass('hidden');
        }
        
        $modalRevision.removeClass('hidden');
        $closeRevision.removeClass('hidden');
    });

    // Fermeture de la modale
    $('#close-revision').on('click', function () {
        $modalRevision.addClass('hidden');
        $closeRevision.addClass('hidden');
        $('.show-modal-true', $modalRevision).addClass('hidden');
        $('.show-modal-false', $modalRevision).addClass('hidden');
    });

    $(window).on('click', function (event) {
        if (event.target == $modalRevision[0]) {
            $modalRevision.addClass('hidden');
            $closeRevision.addClass('hidden');
            $('.show-modal-true', $modalRevision).addClass('hidden');
            $('.show-modal-false', $modalRevision).addClass('hidden');
        }
    });

    // Gestion du clic sur le bouton expert-revision dans la modale
    $modalRevision.on('click', '.expert-revision', function () {
        const translatedFile = $(this).data('translated-file');
        const id = $(this).data('id');

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

        $modalRevision.addClass('hidden');
        $closeRevision.addClass('hidden');
        $('.show-modal-true', $modalRevision).addClass('hidden');
        $('.show-modal-false', $modalRevision).addClass('hidden');
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

    // Gestion du téléchargement de fichiers
    $('.download-file').on('click', function(e) {
        e.preventDefault();
        const translatedFile = $(this).data('translated-file');
        if (translatedFile) {
            window.location.href = translatedFile;
        }
    });
});

