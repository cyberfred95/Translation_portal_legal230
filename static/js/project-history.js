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

    // Gestion du téléchargement de fichiers avec mini-menu si 2 fichiers
    $('.download-file').on('click', function(e) {
        e.preventDefault();
        const $btn = $(this);
        const translatedFile = $btn.data('translated-file');
        const reviewedFile = $btn.data('reviewed-file');

        if (reviewedFile && translatedFile) {
            // Crée/affiche un petit menu pour choisir, positionné en coordonnées écran
            const existing = $('.download-tooltip');
            if (existing.length) { existing.remove(); }

            const $tooltip = $('<div class="download-tooltip fixed z-50 bg-white rounded-md shadow-lg p-1.5 border border-gray-200"></div>');
            const $list = $('<div class="flex flex-col min-w-[160px]"></div>');
            const $optTranslated = $('<button type="button" class="download-file-option text-left px-3 py-2 hover:bg-gray-100 whitespace-nowrap text-sm"></button>').text(language_code === 'fr' ? 'Traduit' : 'Translated');
            const $optReviewed = $('<button type="button" class="download-file-option text-left px-3 py-2 hover:bg-gray-100 whitespace-nowrap text-sm"></button>').text(language_code === 'fr' ? 'Post-édité' : 'Post-edited');
            $list.append($optTranslated, $optReviewed);
            $tooltip.append($list);
            $('body').append($tooltip);

            // Calculer la position: sous et aligné sur le bouton
            const rect = $btn[0].getBoundingClientRect();
            const top = rect.bottom + window.scrollY + 6; // 6px d'espacement
            const left = rect.left + window.scrollX - ($tooltip.outerWidth() - rect.width);
            $tooltip.css({ top: top + 'px', left: left + 'px' });

            // Gestion clics
            $optTranslated.on('click', function(){ window.location.href = translatedFile; $tooltip.remove(); });
            $optReviewed.on('click', function(){ window.location.href = reviewedFile; $tooltip.remove(); });

            // Fermer au clic extérieur ou scroll/resize
            setTimeout(function(){
                const closeFn = function(ev){
                    if (!$(ev.target).closest($tooltip).length && !$(ev.target).closest($btn).length) {
                        $tooltip.remove();
                        $(document).off('click._dl', closeFn);
                        $(window).off('scroll._dl resize._dl', closeFn);
                    }
                };
                $(document).on('click._dl', closeFn);
                $(window).on('scroll._dl resize._dl', closeFn);
            }, 0);
            return;
        }

        // Sinon télécharge le seul fichier disponible
        const fileUrl = reviewedFile || translatedFile;
        if (fileUrl) {
            window.location.href = fileUrl;
        }
    });
});

