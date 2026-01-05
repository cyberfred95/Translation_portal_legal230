/**
 * Gestion de la page Glossaries
 * 
 * Fonctionnalités :
 * - Ajout de glossaires
 * - Suppression de glossaires
 * - Édition de glossaires
 */

(function() {
  'use strict';

  // Protection contre les doubles initialisations
  if (window.glossariesInitialized) {
    return;
  }
  window.glossariesInitialized = true;

  $(document).ready(function () {
    // ============================================================================
    // CONSTANTES
    // ============================================================================
    
    const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
    const FADE_ANIMATION_DURATION = 300;

    // ============================================================================
    // VARIABLES
    // ============================================================================
    
    let file = null;
    const $modal = $('#modal');
    const $closeIcon = $('#closeIcon');
    const $editModal = $('#edit-modal');
    const $editForm = $editModal.find('form');
    const $editInput = $editForm.find('input[type="text"]');
    let currentEditUrl = null;

    // ============================================================================
    // GESTION DE LA MODALE D'AJOUT
    // ============================================================================

    /**
     * Ouvre la modale d'ajout de glossaire
     */
    function openAddModal() {
      $modal.removeClass('hidden');
      $closeIcon.removeClass('hidden');
    }

    /**
     * Ferme la modale d'ajout de glossaire
     */
    function closeAddModal() {
      $modal.addClass('hidden');
      $closeIcon.addClass('hidden');
      resetUploadArea();
      hideWarning();
      validateGlossaryForm();
    }

    $('#openModal').on('click', openAddModal);
    $('#closeModal, #closeIcon').on('click', closeAddModal);

    $(window).on('click', function (event) {
      if (event.target === $modal[0]) {
        closeAddModal();
      }
    });

    // ============================================================================
    // GESTION DU FICHIER
    // ============================================================================

    /**
     * Affiche les informations du fichier sélectionné
     * @param {string} fileName - Nom du fichier
     */
    function showUploadedFile(fileName) {
      $('#fileName').text(fileName);
      $('#fileInfo').removeClass('hidden');
      $('#uploadButton').addClass('hidden');
    }

    /**
     * Réinitialise la zone d'upload
     */
    function resetUploadArea() {
      $('#uploadButton').removeClass('hidden');
      $('#fileInfo').addClass('hidden');
      $('.glossary-file').val('');
      file = null;
    }

    // Exposer la fonction globalement
    window.resetGlossaryUploadArea = resetUploadArea;

    $('#uploadButton').on('click', function () {
      $('.glossary-file').click();
    });

    $('.glossary-file').on('change', function (e) {
      file = e.target.files[0];
      if (file) {
        if (file.size <= MAX_FILE_SIZE) {
          showUploadedFile(file.name);
        } else {
          showWarning(window.glossaryMessages?.fileTooBig || 'File size exceeds 5MB limit.');
          $(this).val('');
          file = null;
        }
      }
      validateGlossaryForm();
    });

    $(document).on('click', '.remove-file', function () {
      resetUploadArea();
      setTimeout(validateGlossaryForm, 100);
    });


    // ============================================================================
    // GESTION DE LA SUPPRESSION
    // ============================================================================

    /**
     * Gère la suppression d'un glossaire
     * @param {string} deleteUrl - URL de suppression
     * @param {jQuery} $row - Ligne du tableau à supprimer
     */
    function deleteGlossary(deleteUrl, $row) {
      $.ajax({
        url: deleteUrl,
        type: 'DELETE',
        processData: false,
        contentType: false,
        headers: {
          'X-CSRFToken': getCookie('csrftoken')
        },
        success: function () {
          $row.fadeOut(FADE_ANIMATION_DURATION, function() {
            $(this).remove();
          });
          
          if (window.Toast && window.glossaryMessages?.deletedSuccess) {
            window.Toast.success(window.glossaryMessages.deletedSuccess);
          }
        },
        error: function (error) {
          const errorMessage = error?.responseJSON?.detail || window.glossaryMessages?.deleteError || 'An error occurred while deleting the glossary.';
          if (window.Toast) {
            window.Toast.error(errorMessage);
          } else {
            errorNotification(error?.status, error?.responseJSON?.detail);
          }
        },
      });
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
      const $row = $deleteButton.closest('.glossary-row');

      if (deleteUrl && $row.length) {
        deleteGlossary(deleteUrl, $row);
      }
    });

    $(document).on('click', '.cancel-delete', function (e) {
      e.stopPropagation();
      $(this).closest('.tooltip').addClass('opacity-0 invisible').removeClass('opacity-100 visible');
    });
  });
})();

    // ============================================================================
    // GESTION DE L'ÉDITION
    // ============================================================================

    /**
     * Ouvre la modale d'édition avec le nom du glossaire
     * @param {string} glossaryName - Nom actuel du glossaire
     * @param {string} editUrl - URL pour l'édition
     */
    function openEditModal(glossaryName, editUrl) {
      $editInput.val(glossaryName);
      currentEditUrl = editUrl;
      $editModal.removeClass('hidden').addClass('flex');
    }

    /**
     * Ferme la modale d'édition
     */
    function closeEditModal() {
      $editModal.removeClass('flex').addClass('hidden');
    }

    $('.edit-glossary').on('click', function () {
      const glossaryName = $(this).closest('td').find('span').text().trim();
      const editUrl = $(this).data('edit-url');
      openEditModal(glossaryName, editUrl);
    });

    $('#close-edit-modal').on('click', closeEditModal);

    $(window).on('click', function (e) {
      if ($(e.target).is($editModal)) {
        closeEditModal();
      }
    });

    $editForm.on('submit', function (e) {
      e.preventDefault();

      const newName = $editInput.val();
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
          closeEditModal();
          window.location.reload();
        },
        error: function (error) {
          errorNotification(error?.status, error?.responseJSON?.detail);
        },
      });
    });

    // ============================================================================
    // GESTION DE LA LISTE DES GLOSSAIRES
    // ============================================================================

    /**
     * Formate une date au format dd/mm/yyyy
     * @param {string} dateString - Date à formater
     * @returns {string} Date formatée
     */
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

    /**
     * Crée le HTML d'une ligne de tableau pour un glossaire
     * @param {Object} glossary - Données du glossaire
     * @returns {string} HTML de la ligne
     */
    function createGlossaryRowHTML(glossary) {
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

    /**
     * Ajoute un glossaire à la liste sans recharger la page
     * @param {Object} glossary - Données du glossaire
     */
    function addGlossaryToList(glossary) {
      const $tbody = $('table tbody');
      const $emptyRow = $tbody.find('tr:has(td[colspan="5"])');
      
      if ($emptyRow.length > 0) {
        $emptyRow.remove();
      }
      
      const $newRow = $(createGlossaryRowHTML(glossary));
      $newRow.hide();
      $tbody.prepend($newRow);
      $newRow.fadeIn(FADE_ANIMATION_DURATION);
    }

    // ============================================================================
    // GESTION DE L'AJOUT DE GLOSSAIRE
    // ============================================================================

    /**
     * Active l'état de chargement du bouton
     * @param {jQuery} $button - Bouton jQuery
     */
    function setButtonLoading($button) {
      $button.prop('disabled', true).addClass('cursor-not-allowed opacity-75');
      const spinner = '<svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" style="margin-right: 0.5rem;"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>';
      $button.prepend(spinner);
    }

    /**
     * Désactive l'état de chargement du bouton
     * @param {jQuery} $button - Bouton jQuery
     */
    function removeButtonLoading($button) {
      $button.prop('disabled', false)
             .removeClass('cursor-not-allowed opacity-75')
             .find('svg.animate-spin').remove();
    }

    /**
     * Gère la création d'un nouveau glossaire
     */
    function handleCreateGlossary() {
      hideWarning();

      if (!file) {
        showWarning(window.glossaryMessages?.pleaseSelectFile || 'Please select a file to upload');
        return;
      }

      const $button = $('.create-glossary');
      setButtonLoading($button);

      const formData = new FormData();
      formData.append('file', file);

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
          closeAddModal();
          
          if (window.Toast && window.glossaryMessages?.addedSuccess) {
            window.Toast.success(window.glossaryMessages.addedSuccess);
          }
          
          if (response) {
            addGlossaryToList(response);
          }
        },
        error: function (error) {
          removeButtonLoading($button);
          
          const errorMessage = error?.responseJSON?.detail || window.glossaryMessages?.errorOccurred || 'An error occurred while adding the glossary.';
          showWarning(errorMessage);
          
          if (window.Toast) {
            window.Toast.error(errorMessage);
          }
        },
      });
    }

    $(document).on('click', '.create-glossary', function (e) {
      e.preventDefault();
      handleCreateGlossary();
    });

    // ============================================================================
    // GESTION DES WARNINGS
    // ============================================================================

    /**
     * Affiche un message d'avertissement dans la modale
     * @param {string} message - Message à afficher
     */
    function showWarning(message) {
      $('#glossary-warning-text').text(message);
      $('#glossary-warning').removeClass('hidden');
    }

    /**
     * Cache le message d'avertissement
     */
    function hideWarning() {
      $('#glossary-warning').addClass('hidden');
      $('#glossary-warning-text').text('');
    }

    // Exposer les fonctions globalement
    window.showGlossaryWarning = showWarning;
    window.hideGlossaryWarning = hideWarning;
    
    // ============================================================================
    // VALIDATION DU FORMULAIRE
    // ============================================================================

    /**
     * Valide le formulaire d'ajout de glossaire
     */
    function validateGlossaryForm() {
      const hasFile = $('.glossary-file')[0]?.files.length > 0;
      const $continueButton = $('#continueButton');
      
      hideWarning();
      
      if (hasFile) {
        $continueButton.prop('disabled', false)
                      .removeClass('bg-gray-400 cursor-not-allowed')
                      .addClass('bg-green-800 hover:bg-green-600 cursor-pointer');
      } else {
        $continueButton.prop('disabled', true)
                      .removeClass('bg-green-800 hover:bg-green-600 cursor-pointer')
                      .addClass('bg-gray-400 cursor-not-allowed');
      }
    }
});
