$(document).ready(function () {

    let file

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
        $('.glossary-file').click();;
    });

    $('.glossary-file').on('change', function (e) {
        file = e.target.files[0];
        if (file) {
            if (file.size <= maxFileSize) {
                showUploadedFile(file.name);
            } else {
                window.showGlossaryWarning(window.glossaryMessages?.fileTooBig || 'File size exceeds 5MB limit.');
                $(this).val('');
                file = null;
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
        file = null;
    }
    
    // Exposer la fonction globalement
    window.resetGlossaryUploadArea = resetUploadArea;


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
                $deleteButton.closest('.glossary-row').fadeOut(300, function() {
                    $(this).remove();
                });
                
                // Afficher un toast de succès
                if (window.Toast && window.glossaryMessages?.deletedSuccess) {
                    window.Toast.success(window.glossaryMessages.deletedSuccess);
                }
            },
            error: function (error) {
                // Afficher un toast d'erreur
                const errorMessage = error?.responseJSON?.detail || window.glossaryMessages?.deleteError || 'An error occurred while deleting the glossary.';
                if (window.Toast) {
                    window.Toast.error(errorMessage);
                } else {
                    errorNotification(error?.status, error?.responseJSON?.detail);
                }
            },
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
            error: function (error) {
                errorNotification(error?.status, error?.responseJSON?.detail);
            },
        });
    });

    $(window).on('click', function (e) {
        if ($(e.target).is($edit_modal)) {
            $edit_modal.removeClass('flex').addClass('hidden');
        }
    });

    // Fonction pour formater la date au format dd/mm/yyyy
    function formatDate(dateString) {
        if (!dateString) return '';
        
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) return dateString;
            
            const day = String(date.getDate()).padStart(2, '0');
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const year = date.getFullYear();
            return `${day}/${month}/${year}`;
        } catch (e) {
            return dateString;
        }
    }

    // Fonction pour créer une ligne de tableau pour un glossaire
    function createGlossaryRow(glossary) {
        const glossaryId = glossary.id || glossary.glossary_id || '';
        const glossaryName = glossary.name || '';
        const sourceLang = glossary.source_language || '';
        const targetLang = glossary.target_language || (glossary.target_languages ? glossary.target_languages.split(',')[0] : '');
        const createdAt = formatDate(glossary.created_at);
        const deleteUrl = `/fr/glossaries/${glossaryId}/`;

        return `
            <tr class="border-b border-gray-100 hover:bg-gray-50 glossary-row">
                <td style="padding: 1rem 2rem; vertical-align: middle;">
                    <span class="doc-title" style="color:#181932;font-size:1rem;font-weight:500;">${glossaryName}</span>
                </td>
                <td style="padding: 1rem; vertical-align: middle; text-align: center;">
                    <span class="lang-label" style="color:#181932;font-size:1rem;font-weight:500;">${sourceLang}</span>
                </td>
                <td style="padding: 1rem; vertical-align: middle; text-align: center;">
                    <span class="lang-label" style="color:#181932;font-size:1rem;font-weight:500;">${targetLang}</span>
                </td>
                <td style="padding: 1rem 2rem; vertical-align: middle; text-align: center; color:#181932; font-size:1rem;">
                    ${createdAt}
                </td>
                <td style="padding: 1rem 2rem; vertical-align: middle; text-align: center;">
                    <div class="table-actions">
                        <button type="button" 
                                class="delete-project"
                                data-delete-url="${deleteUrl}"
                                style="background: none; border: none; cursor: pointer; position: relative;">
                            <i class="ph ph-trash" style="font-size: 16px; color: #DC2626;"></i>
                            <div class="tooltip invisible opacity-0 transition-opacity duration-300 absolute z-10 w-auto py-2 px-2 bg-white text-black rounded-md bottom-14 left-1/2 transform -translate-x-1/2 translate-y-full shadow-lg" style="font-size: 11px;">
                                <div class="flex items-center gap-1.5">
                                    <i class="ph-fill ph-check-circle allow-delete" style="font-size: 14px; color: #00BBA7;"></i>
                                    <i class="ph-fill ph-x-circle cancel-delete" style="font-size: 14px; color: #FD625E;"></i>
                                </div>
                                <div class="absolute w-3 h-3 bg-white transform rotate-45 left-1/2 -translate-x-1/2 -bottom-1.5 shadow-lg"></div>
                            </div>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }

    // Fonction pour ajouter un glossaire à la liste
    function addGlossaryToList(glossary) {
        const $tbody = $('table tbody');
        const $emptyRow = $tbody.find('tr:has(td[colspan="5"])');
        
        // Si le tableau est vide, supprimer la ligne "No glossaries found"
        if ($emptyRow.length > 0) {
            $emptyRow.remove();
        }
        
        // Créer la nouvelle ligne
        const $newRow = $(createGlossaryRow(glossary));
        
        // Ajouter la ligne en haut du tableau avec une animation
        $newRow.hide();
        $tbody.prepend($newRow);
        $newRow.fadeIn(300);
    }

    $(document).on('click', '.create-glossary', function (e) {
        e.preventDefault();

        // Cacher les warnings existants
        window.hideGlossaryWarning();

        if (!file) {
            window.showGlossaryWarning(window.glossaryMessages?.pleaseSelectFile || 'Please select a file to upload');
            return;
        }

        const $button = $(this);
        
        // Désactiver le bouton et afficher le spinner
        $button.prop('disabled', true)
               .addClass('cursor-not-allowed opacity-75');
        
        // Créer et insérer le spinner juste avant le texte "Continue"
        const spinner = '<svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" style="margin-right: 0.5rem;"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>';
        $button.prepend(spinner);

        const formData = new FormData();
        formData.append('file', file);
        // Languages are now automatically detected from CSV file

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
            success: function (response) {
                // Fermer la modal
                $modal.addClass('hidden');
                $closeIcon.addClass('hidden');
                resetUploadArea();
                
                // Afficher un toast de succès
                if (window.Toast && window.glossaryMessages?.addedSuccess) {
                    window.Toast.success(window.glossaryMessages.addedSuccess);
                }
                
                // Ajouter le nouveau glossaire à la liste sans recharger la page
                if (response) {
                    addGlossaryToList(response);
                }
            },
            error: function (error) {
                // Retirer le spinner et réactiver le bouton en cas d'erreur
                $button.prop('disabled', false)
                       .removeClass('cursor-not-allowed opacity-75')
                       .find('svg.animate-spin').remove();
                
                // Afficher le message d'erreur dans le warning ET dans un toast
                const errorMessage = error?.responseJSON?.detail || window.glossaryMessages?.errorOccurred || 'An error occurred while adding the glossary.';
                window.showGlossaryWarning(errorMessage);
                
                if (window.Toast) {
                    window.Toast.error(errorMessage);
                }
            },
        });
    });

    // Fonctions de gestion des warnings pour la modal
    function showWarning(message) {
        $('#glossary-warning-text').text(message);
        $('#glossary-warning').removeClass('hidden');
    }
    
    function hideWarning() {
        $('#glossary-warning').addClass('hidden');
        $('#glossary-warning-text').text('');
    }
    
    // Exposer les fonctions globalement
    window.showGlossaryWarning = showWarning;
    window.hideGlossaryWarning = hideWarning;
    
    // Validation du formulaire de la modal (only file required now)
    function validateGlossaryForm() {
        const hasFile = $('.glossary-file')[0]?.files.length > 0;
        
        // Cacher le warning lors de la validation
        hideWarning();
        
        const isValid = hasFile;
        
        const $continueButton = $('#continueButton');
        
        if (isValid) {
            $continueButton.prop('disabled', false)
                          .removeClass('bg-gray-400 cursor-not-allowed')
                          .addClass('bg-green-800 hover:bg-green-600 cursor-pointer');
        } else {
            $continueButton.prop('disabled', true)
                          .removeClass('bg-green-800 hover:bg-green-600 cursor-pointer')
                          .addClass('bg-gray-400 cursor-not-allowed');
        }
    }
    
    // Vérifier lors de la sélection d'un fichier
    $('.glossary-file').on('change', validateGlossaryForm);
    
    // Vérifier lors de la suppression du fichier
    $(document).on('click', '.remove-file', function() {
        setTimeout(validateGlossaryForm, 100);
    });
    
    // Réinitialiser le formulaire quand la modal se ferme
    $('#closeModal, #closeIcon').on('click', function() {
        $('.glossary-file').val('');
        hideWarning();
        
        // Réinitialiser la zone d'upload
        if (typeof window.resetGlossaryUploadArea === 'function') {
            window.resetGlossaryUploadArea();
        }
        
        validateGlossaryForm();
    });
    
    // Fermer la modal en cliquant en dehors
    $(window).on('click', function(event) {
        if (event.target.id === 'modal') {
            $('#closeModal').click();
        }
    });
});
