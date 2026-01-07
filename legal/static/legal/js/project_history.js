/**
 * Project History JavaScript
 * Gère les interactions de la page project history
 */

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Show error notification using AppBase
 * @param {number} status - Code de statut HTTP (non utilisé, conservé pour compatibilité)
 * @param {string} detail - Message d'erreur détaillé
 */
/**
 * Show error notification using AppBase
 * @param {number} status - Code de statut HTTP (non utilisé, conservé pour compatibilité)
 * @param {string|Object} detail - Message d'erreur détaillé ou objet d'erreur
 */
function showError(status, detail) {
  const defaultMessage = window.deleteConfirmationMessages?.error || 'Error deleting translation. Please try again.';
  const errorMessage = typeof detail === 'string' ? detail : (detail?.detail || detail?.message || defaultMessage);
  
  if (window.AppBase && window.AppBase.showError) {
    window.AppBase.showError(errorMessage);
  } else {
    console.error('Error:', errorMessage);
  }
}

/**
 * Set button loading state
 */
function setButtonLoading(button, isLoading) {
  if (isLoading) {
    button.disabled = true;
    button.dataset.originalContent = button.innerHTML;
    button.innerHTML = '<i class="ph ph-spinner icon-16 ph-spin"></i>';
  } else {
    button.disabled = false;
    if (button.dataset.originalContent) {
      button.innerHTML = button.dataset.originalContent;
      delete button.dataset.originalContent;
    }
  }
}

/**
 * Create and return delete confirmation dialog elements
 */
function createDeleteDialog(msg) {
  const overlay = document.createElement('div');
  overlay.className = 'delete-confirmation-dialog-overlay';

  const dialog = document.createElement('div');
  dialog.className = 'delete-confirmation-dialog';

  const title = document.createElement('div');
  title.className = 'delete-confirmation-dialog-title';
  title.textContent = msg.title;

  const message = document.createElement('div');
  message.className = 'delete-confirmation-dialog-message';
  message.textContent = msg.message;

  const buttons = document.createElement('div');
  buttons.className = 'delete-confirmation-dialog-buttons';

  const cancelBtn = document.createElement('button');
  cancelBtn.className = 'delete-confirmation-dialog-button delete-confirmation-dialog-button-cancel';
  cancelBtn.textContent = msg.cancel;
  cancelBtn.type = 'button';

  const confirmBtn = document.createElement('button');
  confirmBtn.className = 'delete-confirmation-dialog-button delete-confirmation-dialog-button-confirm';
  confirmBtn.textContent = msg.confirm;
  confirmBtn.type = 'button';

  buttons.appendChild(cancelBtn);
  buttons.appendChild(confirmBtn);
  dialog.appendChild(title);
  dialog.appendChild(message);
  dialog.appendChild(buttons);

  return { overlay, dialog, cancelBtn, confirmBtn };
}

/**
 * Show delete confirmation dialog
 */
function showDeleteConfirmation(documentId, button) {
  // Prevent duplicate dialogs
  if (document.querySelector('.delete-confirmation-dialog')) {
    return;
  }

  // Use translated messages from Django i18n
  const msg = window.deleteConfirmationMessages || {
    title: 'Delete translation',
    message: 'Are you sure you want to delete this translation? Associated files will be permanently deleted.',
    cancel: 'No',
    confirm: 'Yes'
  };

  // Create dialog elements
  const { overlay, dialog, cancelBtn, confirmBtn } = createDeleteDialog(msg);

  // Add to DOM
  document.body.appendChild(overlay);
  document.body.appendChild(dialog);

  // Close function
  const closeDialog = () => {
    overlay.remove();
    dialog.remove();
    document.removeEventListener('keydown', escapeHandler);
  };

  // Escape key handler
  const escapeHandler = (e) => {
    if (e.key === 'Escape') {
      closeDialog();
    }
  };

  // Event handlers
  cancelBtn.addEventListener('click', closeDialog);
  overlay.addEventListener('click', closeDialog);
  confirmBtn.addEventListener('click', () => {
    closeDialog();
    deleteTranslation(documentId, button);
  });
  document.addEventListener('keydown', escapeHandler);
}

/**
 * Delete a translation document via API
 */
function deleteTranslation(documentId, button) {
  setButtonLoading(button, true);

  const deleteUrl = `${window.lara_api_url}/api/lara/documents/${documentId}/delete`;
  const params = new URLSearchParams({ user_uuid: window.user_uuid });

  fetch(`${deleteUrl}?${params}`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    },
  })
    .then(response => {
      if (!response.ok) {
        return response.json().then(err => Promise.reject(err));
      }
      return response.json();
    })
    .then(() => {
      window.location.reload();
    })
    .catch(error => {
      setButtonLoading(button, false);
      showError(error?.status, error?.detail || error?.message);
    });
}

// =============================================================================
// Main Initialization
// =============================================================================

// Protection contre les doubles initialisations
if (window.projectHistoryInitialized) {
  // Le script a déjà été initialisé, ne pas réinitialiser
} else {
  window.projectHistoryInitialized = true;

document.addEventListener('DOMContentLoaded', function () {
  const root = document.querySelector('.project-history-page');
  if (!root) return;

  // Protection contre les doubles initialisations sur le même élément
  if (root._projectHistoryInitialized) return;
  root._projectHistoryInitialized = true;

  if (typeof window.applyStatusMapping === 'function') {
    window.applyStatusMapping(root);
  }

  const modalRevision = root.querySelector('#modal-revision');
  const closeRevision = root.querySelector('#close-revision');

  // ============================================================================
  // GESTION DE LA MODALE DE RÉVISION EXPERTE
  // ============================================================================

  /**
   * Ferme la modale de révision experte
   */
  function closeRevisionModal() {
    if (!modalRevision) return;
    
    modalRevision.classList.add('hidden');
    if (closeRevision) {
      closeRevision.classList.add('hidden');
    }
    modalRevision.querySelectorAll('.show-modal-true, .show-modal-false').forEach(el => {
      el.classList.add('hidden');
    });
  }

  /**
   * Ouvre la modale de révision experte avec les données du projet
   * @param {string} translatedFile - URL du fichier traduit
   * @param {string} id - ID du projet
   * @param {string} display - Indicateur d'affichage ('true' ou 'false')
   */
  function openRevisionModal(translatedFile, id, display) {
    if (!modalRevision) return;

    const modalBtn = modalRevision.querySelector('.expert-revision');
    if (modalBtn) {
      modalBtn.dataset.translatedFile = translatedFile;
      modalBtn.dataset.id = id;
    }

    const showTrue = modalRevision.querySelector('.show-modal-true');
    const showFalse = modalRevision.querySelector('.show-modal-false');
    
    if (display === 'false' || display === 'False') {
      showTrue?.classList.remove('hidden');
      showFalse?.classList.add('hidden');
    } else {
      showTrue?.classList.add('hidden');
      showFalse?.classList.remove('hidden');
    }

    modalRevision.classList.remove('hidden');
    if (closeRevision) {
      closeRevision.classList.remove('hidden');
    }
  }

  /**
   * Met à jour le statut du projet dans le tableau après demande de devis
   * @param {string} projectId - ID du projet
   */
  function updateProjectStatusAfterQuoteRequest(projectId) {
    const projectRow = root.querySelector(`button.expert-revision[data-id="${projectId}"]`)?.closest('tr');
    if (!projectRow) return;

    const statusNode = projectRow.querySelector('.status');
    if (statusNode) {
      const newStatus = 'Sent to post-editing, not accepted yet';
      statusNode.textContent = newStatus;
      statusNode.setAttribute('data-status', newStatus);
      
      if (typeof window.applyStatusMapping === 'function') {
        window.applyStatusMapping(projectRow);
      }
    }
    
    const expertBtn = projectRow.querySelector('.expert-revision');
    if (expertBtn) {
      expertBtn.disabled = true;
      expertBtn.classList.add('disabled');
    }
  }

  // Gestion du clic sur le bouton expert-revision dans le tableau
  root.addEventListener('click', function (e) {
    const expertBtn = e.target.closest('.expert-revision');
    if (expertBtn && expertBtn.closest('table')) {
      if (expertBtn.disabled) return;

      const translatedFile = expertBtn.dataset.translatedFile;
      const id = expertBtn.dataset.id;
      const display = expertBtn.dataset.display;

      openRevisionModal(translatedFile, id, display);
    }
  });

  // Fermeture de la modale
  if (closeRevision) {
    closeRevision.addEventListener('click', closeRevisionModal);
  }

  // Fermeture au clic sur l'overlay
  if (modalRevision) {
    modalRevision.addEventListener('click', function (e) {
      if (e.target === modalRevision) {
        closeRevisionModal();
      }
    });
  }

  // Gestion du clic sur le bouton expert-revision dans la modale
  if (modalRevision) {
    // Supprimer l'ancien écouteur s'il existe
    if (modalRevision._expertRevisionHandler) {
      modalRevision.removeEventListener('click', modalRevision._expertRevisionHandler);
    }

    modalRevision._expertRevisionHandler = function (e) {
      const modalBtn = e.target.closest('.expert-revision');
      if (!modalBtn || modalBtn.closest('table')) return;

      // Empêcher la propagation pour éviter les déclenchements multiples
      e.stopPropagation();
      e.stopImmediatePropagation();

      // Protection contre les doubles soumissions
      if (modalBtn._isSubmitting) {
        e.preventDefault();
        return false;
      }

      const translatedFile = modalBtn.dataset.translatedFile;
      const id = modalBtn.dataset.id;

      if (!translatedFile || !id) {
        return;
      }

      // Marquer comme en cours de soumission
      modalBtn._isSubmitting = true;
      modalBtn.disabled = true;

      const formData = new FormData();
      formData.append('file_url', translatedFile);
      formData.append('project_id', id);

      fetch(window.expert_revision_file_url, {
        method: 'POST',
        body: formData,
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
          'Accept': 'application/json',
        },
      })
        .then(response => {
          if (!response.ok) {
            return response.json().then(err => Promise.reject(err));
          }
          return response.json();
        })
        .then(() => {
          updateProjectStatusAfterQuoteRequest(id);
          closeRevisionModal();
          
          if (window.Toast && window.expertRevisionMessages?.quoteRequestSuccess) {
            window.Toast.success(window.expertRevisionMessages.quoteRequestSuccess);
          }
        })
        .catch(error => {
          // Réactiver le bouton en cas d'erreur
          modalBtn._isSubmitting = false;
          modalBtn.disabled = false;

          // Afficher un toast d'erreur
          const errorMessage = error?.detail || error?.responseJSON?.detail || window.expertRevisionMessages?.quoteRequestError || 'An error occurred while requesting the quote.';
          if (window.Toast) {
            window.Toast.error(errorMessage);
          } else {
            const errorMessage = error?.detail || error?.responseJSON?.detail || 'An error occurred';
            if (window.Toast) {
              window.Toast.error(errorMessage);
            } else {
              console.error('Error:', errorMessage);
            }
          }
        });
    };

    modalRevision.addEventListener('click', modalRevision._expertRevisionHandler);
  }

  // Gestion du téléchargement de fichiers avec mini-menu si 2 fichiers
  root.addEventListener('click', function (e) {
    const downloadBtn = e.target.closest('.download-file');
    if (!downloadBtn) return;

    e.preventDefault();
    const translatedFile = downloadBtn.dataset.translatedFile;
    const reviewedFile = downloadBtn.dataset.reviewedFile;

    if (reviewedFile && translatedFile) {
      // Crée/affiche un petit menu pour choisir
      const existing = document.querySelector('.download-tooltip');
      if (existing) existing.remove();

      const tooltip = document.createElement('div');
      tooltip.className = 'download-tooltip';
      const list = document.createElement('div');
      list.className = 'download-tooltip-list';
      
      const optTranslated = document.createElement('button');
      optTranslated.type = 'button';
      optTranslated.className = 'download-tooltip-option';
      optTranslated.textContent = window.language_code === 'fr' ? 'Traduit' : 'Translated';
      
      const optReviewed = document.createElement('button');
      optReviewed.type = 'button';
      optReviewed.className = 'download-tooltip-option';
      optReviewed.textContent = window.language_code === 'fr' ? 'Post-édité' : 'Post-edited';
      
      list.appendChild(optTranslated);
      list.appendChild(optReviewed);
      tooltip.appendChild(list);
      document.body.appendChild(tooltip);

      // Calculer la position: sous et aligné sur le bouton
      const rect = downloadBtn.getBoundingClientRect();
      const top = rect.bottom + window.scrollY + 6;
      const left = rect.left + window.scrollX - (tooltip.offsetWidth - rect.width);
      tooltip.style.top = top + 'px';
      tooltip.style.left = left + 'px';

      // Gestion clics
      optTranslated.addEventListener('click', function () {
        window.location.href = translatedFile;
        tooltip.remove();
      });
      optReviewed.addEventListener('click', function () {
        window.location.href = reviewedFile;
        tooltip.remove();
      });

      // Fermer au clic extérieur ou scroll/resize
      setTimeout(function () {
        const closeFn = function (ev) {
          if (!tooltip.contains(ev.target) && !downloadBtn.contains(ev.target)) {
            tooltip.remove();
            document.removeEventListener('click', closeFn);
            window.removeEventListener('scroll', closeFn);
            window.removeEventListener('resize', closeFn);
          }
        };
        document.addEventListener('click', closeFn);
        window.addEventListener('scroll', closeFn);
        window.addEventListener('resize', closeFn);
      }, 0);
      return;
    }

    // Sinon télécharge le seul fichier disponible
    const fileUrl = reviewedFile || translatedFile;
    if (fileUrl) {
      window.location.href = fileUrl;
    }
  });

  // Gestion de la suppression d'une traduction
  root.addEventListener('click', function (e) {
    const deleteBtn = e.target.closest('.delete-translation');
    if (!deleteBtn) return;

    e.preventDefault();
    if (deleteBtn.disabled) return;
    
    showDeleteConfirmation(deleteBtn.dataset.id, deleteBtn);
  });

  // S'assure que les statuts restent synchronis 9s si la pagination met  0 jour le tableau dynamiquement
  document.addEventListener('page:updated', function () {
    applyStatuses(root);
  });
});

} // Fin de la protection contre les doubles initialisations

