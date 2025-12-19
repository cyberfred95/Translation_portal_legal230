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
            success: function () {
                window.location.reload();
            },
            error: function (error) {
                // Retirer le spinner et réactiver le bouton en cas d'erreur
                $button.prop('disabled', false)
                       .removeClass('cursor-not-allowed opacity-75')
                       .find('svg.animate-spin').remove();
                
                // Afficher le message d'erreur dans le warning
                const errorMessage = error?.responseJSON?.detail || window.glossaryMessages?.errorOccurred || 'An error occurred while adding the glossary.';
                window.showGlossaryWarning(errorMessage);
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
