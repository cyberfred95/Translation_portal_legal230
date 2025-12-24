document.addEventListener('DOMContentLoaded', function () {
  const root = document.querySelector('.profile-details-page');
  if (!root) return;

  const changeDataUrl = root.getAttribute('data-change-url') || '';

  const tabButtons = {
    info: root.querySelector('#profile-information'),
    security: root.querySelector('#profile-security'),
  };
  const tabContents = {
    info: root.querySelector('#profile-information-content'),
    security: root.querySelector('#profile-security-content'),
  };

  function showTab(tab) {
    if (!tabButtons.info || !tabButtons.security) return;
    if (!tabContents.info || !tabContents.security) return;

    const isInfo = tab === 'info';
    tabContents.info.classList.toggle('hidden', !isInfo);
    tabContents.security.classList.toggle('hidden', isInfo);

    // Active state on buttons
    tabButtons.info.classList.toggle('is-active', isInfo);
    tabButtons.security.classList.toggle('is-active', !isInfo);
    tabButtons.info.setAttribute('aria-selected', String(isInfo));
    tabButtons.security.setAttribute('aria-selected', String(!isInfo));
  }

  if (tabButtons.info) {
    tabButtons.info.addEventListener('click', () => showTab('info'));
  }
  if (tabButtons.security) {
    tabButtons.security.addEventListener('click', () => showTab('security'));
  }

  // Expose URL if other scripts need it later
  window.profileDetails = window.profileDetails || {};
  window.profileDetails.changeDataUrl = changeDataUrl;

  // Set initial tab state (Information visible by default)
  showTab('info');

  // Handle form submission as PUT to changeDataUrl
  const form = root.querySelector('form[name="change-user-data"]');
  if (form && changeDataUrl) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(form);

      // Extract CSRF token
      const csrfToken = formData.get('csrfmiddlewaretoken') || '';

      try {
        const response = await fetch(changeDataUrl, {
          method: 'PUT',
          headers: {
            'X-CSRFToken': csrfToken,
          },
          body: formData,
          credentials: 'same-origin',
        });

        if (!response.ok) {
          return;
        }

        // Show success modal
        const modal = root.querySelector('#success-update-user-data');
        if (modal) modal.classList.remove('hidden');
      } catch (err) {
        // Silent error handling
      }
    });
  }

  // Close success modal on button click or overlay click
  const modal = root.querySelector('#success-update-user-data');
  const modalBtn = root.querySelector('#success-update-btn');
  if (modalBtn && modal) {
    modalBtn.addEventListener('click', () => {
      modal.classList.add('hidden');
    });
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.add('hidden');
      }
    });
  }

  // Logout functionality
  function handleLogout(e) {
    e.preventDefault();
    e.stopPropagation();
    
    // Try to get CSRF token from cookie first
    let csrfToken = getCookie('csrftoken');
    
    // If not found in cookie, try to get it from the form's hidden input
    if (!csrfToken) {
      const csrfInput = root.querySelector('[name=csrfmiddlewaretoken]');
      if (csrfInput) {
        csrfToken = csrfInput.value;
      }
    }
    
    if (!csrfToken) {
      return;
    }

    // Get current language prefix from URL (e.g., /fr/ or /en/)
    const currentPath = window.location.pathname;
    const langPrefix = currentPath.split('/')[1] || '';
    const logoutUrl = langPrefix ? `/${langPrefix}/accounts/logout/` : '/accounts/logout/';

    // Create form and submit to logout URL
    const logoutForm = document.createElement('form');
    logoutForm.method = 'POST';
    logoutForm.action = logoutUrl;
    
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = csrfToken;
    logoutForm.appendChild(csrfInput);
    
    document.body.appendChild(logoutForm);
    logoutForm.submit();
  }

  // Attach logout handler using event delegation
  root.addEventListener('click', function(e) {
    const logoutBtn = e.target.closest('#logout-btn');
    if (logoutBtn) {
      handleLogout(e);
    }
  }, true);

  // =============================================================================
  // Delete All Translations Functionality
  // =============================================================================

  /**
   * Creates a confirmation dialog for deleting all translations
   * @param {Object} msg - Messages object with title, message, cancel, confirm
   * @returns {Object} Dialog elements (overlay, dialog, cancelBtn, confirmBtn)
   */
  function createDeleteConfirmationDialog(msg) {
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
   * Sets up and shows the delete confirmation dialog
   * @param {Function} onConfirm - Callback when user confirms deletion
   */
  function showDeleteConfirmationDialog(onConfirm) {
    // Prevent duplicate dialogs
    if (document.querySelector('.delete-confirmation-dialog')) {
      return;
    }

    const msg = window.deleteAllConfirmationMessages || {
      title: 'Delete all translations',
      message: 'Are you sure you want to delete all your translations? All associated files will be permanently deleted.',
      cancel: 'No',
      confirm: 'Yes'
    };

    const { overlay, dialog, cancelBtn, confirmBtn } = createDeleteConfirmationDialog(msg);

    document.body.appendChild(overlay);
    document.body.appendChild(dialog);

    const closeDialog = () => {
      overlay.remove();
      dialog.remove();
      document.removeEventListener('keydown', escapeHandler);
    };

    const escapeHandler = (e) => {
      if (e.key === 'Escape') {
        closeDialog();
      }
    };

    cancelBtn.addEventListener('click', closeDialog);
    overlay.addEventListener('click', closeDialog);
    confirmBtn.addEventListener('click', () => {
      closeDialog();
      onConfirm();
    });
    document.addEventListener('keydown', escapeHandler);
  }

  /**
   * Sets button to loading state
   * @param {HTMLElement} button - Button element
   * @param {string} loadingText - Text to display while loading
   * @returns {string} Original button HTML content
   */
  function setButtonLoading(button, loadingText) {
    const originalContent = button.innerHTML;
    button.disabled = true;
    button.innerHTML = `<i class="ph ph-spinner icon-24 ph-spin"></i><span class="btn-label">${loadingText}</span>`;
    return originalContent;
  }

  /**
   * Restores button from loading state
   * @param {HTMLElement} button - Button element
   * @param {string} originalContent - Original button HTML content
   */
  function restoreButton(button, originalContent) {
    button.disabled = false;
    button.innerHTML = originalContent;
  }

  /**
   * Shows error notification or fallback alert
   * @param {Object} error - Error object
   * @param {string} defaultMessage - Default error message
   */
  function showError(error, defaultMessage) {
    const errorMsg = error?.detail || error?.message || defaultMessage;
    if (typeof errorNotification === 'function') {
      errorNotification(error?.status || 500, errorMsg);
    } else {
      alert(errorMsg);
    }
  }

  /**
   * Deletes all user translations via API
   */
  function deleteAllTranslations() {
    const button = root.querySelector('#delete-all-translations-btn');
    if (!button || !window.user_uuid || !window.lara_api_url) {
      return;
    }

    const deletingText = window.deleteAllConfirmationMessages?.deleting || 'Deleting...';
    const originalContent = setButtonLoading(button, deletingText);

    const deleteUrl = `${window.lara_api_url}/api/lara/documents/user/${window.user_uuid}/delete-all`;
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
        // Reload page immediately after successful deletion
        window.location.reload();
      })
      .catch(error => {
        restoreButton(button, originalContent);
        const errorMsg = window.deleteAllConfirmationMessages?.error || 'Error deleting translations. Please try again.';
        showError(error, errorMsg);
      });
  }

  // Attach delete all handler
  root.addEventListener('click', function(e) {
    const deleteBtn = e.target.closest('#delete-all-translations-btn');
    if (deleteBtn && !deleteBtn.disabled) {
      e.preventDefault();
      showDeleteConfirmationDialog(deleteAllTranslations);
    }
  });
});



