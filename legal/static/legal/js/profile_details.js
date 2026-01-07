/**
 * Gestion de la page Profile Details
 * 
 * Fonctionnalités :
 * - Navigation par onglets (Information / Security)
 * - Mise à jour des données utilisateur
 * - Déconnexion
 * - Suppression de toutes les traductions
 */

(function() {
  'use strict';

  // Protection contre l'initialisation multiple
  if (window.profileDetailsInitialized) {
    return;
  }
  window.profileDetailsInitialized = true;

  document.addEventListener('DOMContentLoaded', function () {
    const root = document.querySelector('.profile-details-page');
    if (!root || root._profileDetailsInitialized) {
      return;
    }
    root._profileDetailsInitialized = true;

    const changeDataUrl = root.getAttribute('data-change-url') || '';

    // ============================================================================
    // GESTION DES ONGLETS
    // ============================================================================

    const TabManager = {
      buttons: {
        info: root.querySelector('#profile-information'),
        security: root.querySelector('#profile-security'),
      },
      contents: {
        info: root.querySelector('#profile-information-content'),
        security: root.querySelector('#profile-security-content'),
      },

      show(tab) {
        const isInfo = tab === 'info';
        const { buttons, contents } = this;

        if (!buttons.info || !buttons.security || !contents.info || !contents.security) {
          return;
        }

        contents.info.classList.toggle('hidden', !isInfo);
        contents.security.classList.toggle('hidden', isInfo);

        buttons.info.classList.toggle('is-active', isInfo);
        buttons.security.classList.toggle('is-active', !isInfo);
        buttons.info.setAttribute('aria-selected', String(isInfo));
        buttons.security.setAttribute('aria-selected', String(!isInfo));
      },

      init() {
        if (this.buttons.info) {
          this.buttons.info.addEventListener('click', () => this.show('info'));
        }
        if (this.buttons.security) {
          this.buttons.security.addEventListener('click', () => this.show('security'));
        }
        this.show('info');
      }
    };

    // ============================================================================
    // MISE À JOUR DES DONNÉES UTILISATEUR
    // ============================================================================

    /**
     * Désactive le bouton de soumission pendant le traitement
     * @param {HTMLElement} button - Bouton à désactiver
     * @returns {Object} État original du bouton
     */
    function disableSubmitButton(button) {
      if (!button) return null;
      
      return {
        element: button,
        text: button.innerHTML,
        disabled: button.disabled
      };
    }

    /**
     * Réactive le bouton de soumission
     * @param {Object} buttonState - État original du bouton
     */
    function enableSubmitButton(buttonState) {
      if (!buttonState || !buttonState.element) return;
      
      buttonState.element.disabled = buttonState.disabled;
      buttonState.element.innerHTML = buttonState.text;
    }

    /**
     * Traite la réponse de la requête de mise à jour
     * @param {Response} response - Réponse HTTP
     * @returns {Promise<void>}
     */
    async function handleUpdateResponse(response) {
      if (response.ok) {
        if (window.Toast && typeof window.Toast.success === 'function') {
          const message = window.profileUpdateMessages?.success;
          if (message) {
            window.Toast.success(message);
          }
        }
      } else {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.detail || errorData.message || window.profileUpdateMessages?.error;
        
        if (window.Toast && typeof window.Toast.error === 'function' && errorMessage) {
          window.Toast.error(errorMessage);
        }
      }
    }

    /**
     * Gère la soumission du formulaire de modification des données
     */
    function handleUserDataUpdate() {
      const form = root.querySelector('form[name="change-user-data"]');
      if (!form || !changeDataUrl) return;

      // Supprimer l'ancien écouteur s'il existe
      if (form._submitHandler) {
        form.removeEventListener('submit', form._submitHandler);
      }

      const submitHandler = async (e) => {
        if (form._isSubmitting) {
          e.preventDefault();
          e.stopImmediatePropagation();
          return false;
        }
        
        e.preventDefault();
        e.stopImmediatePropagation();
        e.stopPropagation();
        
        form._isSubmitting = true;

        const submitButton = form.querySelector('button[type="submit"]');
        const buttonState = disableSubmitButton(submitButton);
        
        if (submitButton && window.profileUpdateMessages?.updating) {
          submitButton.disabled = true;
          submitButton.innerHTML = `<span>${window.profileUpdateMessages.updating}</span>`;
        }

        const formData = new FormData(form);
        const csrfToken = formData.get('csrfmiddlewaretoken') || '';

        try {
          const response = await fetch(changeDataUrl, {
            method: 'PUT',
            headers: { 'X-CSRFToken': csrfToken },
            body: formData,
            credentials: 'same-origin',
          });

          await handleUpdateResponse(response);
        } catch (err) {
          if (window.Toast && window.profileUpdateMessages?.errorData) {
            window.Toast.error(window.profileUpdateMessages.errorData);
          }
        } finally {
          form._isSubmitting = false;
          enableSubmitButton(buttonState);
        }
      };

      form._submitHandler = submitHandler;
      form.addEventListener('submit', submitHandler, { once: false, passive: false });
    }

    // ============================================================================
    // GESTION DE LA DÉCONNEXION
    // ============================================================================

    /**
     * Récupère la valeur d'un cookie
     * @param {string} name - Nom du cookie
     * @returns {string|null} Valeur du cookie ou null
     */
    function getCookie(name) {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) {
        return parts.pop().split(';').shift();
      }
      return null;
    }

    /**
     * Récupère le token CSRF depuis le cookie ou le formulaire
     * @returns {string|null} Token CSRF
     */
    function getCSRFToken() {
      let token = getCookie('csrftoken');
      if (!token) {
        const csrfInput = root.querySelector('[name=csrfmiddlewaretoken]');
        token = csrfInput ? csrfInput.value : null;
      }
      return token;
    }

    /**
     * Construit l'URL de déconnexion basée sur le préfixe de langue
     * @returns {string} URL de déconnexion
     */
    function getLogoutUrl() {
      const langPrefix = window.location.pathname.split('/')[1] || '';
      return langPrefix ? `/${langPrefix}/accounts/logout/` : '/accounts/logout/';
    }

    /**
     * Crée et soumet le formulaire de déconnexion
     * @param {string} csrfToken - Token CSRF
     */
    function submitLogoutForm(csrfToken) {
      const logoutForm = document.createElement('form');
      logoutForm.method = 'POST';
      logoutForm.action = getLogoutUrl();

      const csrfInput = document.createElement('input');
      csrfInput.type = 'hidden';
      csrfInput.name = 'csrfmiddlewaretoken';
      csrfInput.value = csrfToken;
      logoutForm.appendChild(csrfInput);

      document.body.appendChild(logoutForm);
      logoutForm.submit();
    }

    /**
     * Gère la déconnexion de l'utilisateur
     * @param {Event} e - Événement de clic
     */
    function handleLogout(e) {
      e.preventDefault();
      e.stopPropagation();

      const csrfToken = getCSRFToken();
      if (csrfToken) {
        submitLogoutForm(csrfToken);
      }
    }

    // ============================================================================
    // GESTION DE LA SUPPRESSION DES TRADUCTIONS
    // ============================================================================

    /**
     * Crée un élément de dialogue
     * @param {string} tag - Tag HTML
     * @param {string} className - Classe CSS
     * @param {string} textContent - Contenu texte
     * @returns {HTMLElement} Élément créé
     */
    function createDialogElement(tag, className, textContent = '') {
      const element = document.createElement(tag);
      element.className = className;
      if (textContent) {
        element.textContent = textContent;
      }
      return element;
    }

    /**
     * Crée le dialogue de confirmation de suppression
     * @param {Object} messages - Messages traduits
     * @returns {Object} Éléments du dialogue
     */
    function createDeleteConfirmationDialog(messages) {
      const overlay = createDialogElement('div', 'delete-confirmation-dialog-overlay');
      const dialog = createDialogElement('div', 'delete-confirmation-dialog');
      const title = createDialogElement('div', 'delete-confirmation-dialog-title', messages.title);
      const message = createDialogElement('div', 'delete-confirmation-dialog-message', messages.message);
      const buttons = createDialogElement('div', 'delete-confirmation-dialog-buttons');

      const cancelBtn = createDialogElement('button', 'delete-confirmation-dialog-button delete-confirmation-dialog-button-cancel', messages.cancel);
      cancelBtn.type = 'button';

      const confirmBtn = createDialogElement('button', 'delete-confirmation-dialog-button delete-confirmation-dialog-button-confirm', messages.confirm);
      confirmBtn.type = 'button';

      buttons.appendChild(cancelBtn);
      buttons.appendChild(confirmBtn);
      dialog.appendChild(title);
      dialog.appendChild(message);
      dialog.appendChild(buttons);

      return { overlay, dialog, cancelBtn, confirmBtn };
    }

    /**
     * Affiche le dialogue de confirmation de suppression
     * @param {Function} onConfirm - Callback de confirmation
     */
    function showDeleteConfirmationDialog(onConfirm) {
      if (document.querySelector('.delete-confirmation-dialog') || !window.deleteAllConfirmationMessages) {
        return;
      }

      const { overlay, dialog, cancelBtn, confirmBtn } = 
        createDeleteConfirmationDialog(window.deleteAllConfirmationMessages);

      document.body.appendChild(overlay);
      document.body.appendChild(dialog);

      const closeDialog = () => {
        overlay.remove();
        dialog.remove();
        document.removeEventListener('keydown', handleEscape);
      };

      const handleEscape = (e) => {
        if (e.key === 'Escape') closeDialog();
      };

      cancelBtn.addEventListener('click', closeDialog);
      overlay.addEventListener('click', closeDialog);
      confirmBtn.addEventListener('click', () => {
        closeDialog();
        onConfirm();
      });
      document.addEventListener('keydown', handleEscape);
    }

    /**
     * Met un bouton en état de chargement
     * @param {HTMLElement} button - Bouton à modifier
     * @param {string} loadingText - Texte de chargement
     * @returns {string} Contenu original
     */
    function setButtonLoading(button, loadingText) {
      const originalContent = button.innerHTML;
      button.disabled = true;
      button.innerHTML = `<i class="ph ph-spinner icon-24 ph-spin"></i><span class="btn-label">${loadingText}</span>`;
      return originalContent;
    }

    /**
     * Restaure un bouton depuis l'état de chargement
     * @param {HTMLElement} button - Bouton à restaurer
     * @param {string} originalContent - Contenu original
     */
    function restoreButton(button, originalContent) {
      button.disabled = false;
      button.innerHTML = originalContent;
    }

    /**
     * Affiche une erreur en utilisant AppBase si disponible, sinon fallback local
     * @param {Object|string} error - Objet d'erreur ou message d'erreur
     * @param {string} message - Message d'erreur par défaut (si error est un objet)
     */
    function showError(error, message) {
      if (window.AppBase && window.AppBase.showError) {
        window.AppBase.showError(error, message);
      } else {
        const errorMsg = typeof error === 'string' 
          ? error 
          : (error?.detail || error?.message || message || 'An error occurred');
        if (window.Toast) {
          window.Toast.error(errorMsg);
        } else {
          console.error('Error:', errorMsg);
        }
      }
    }

    /**
     * Supprime toutes les traductions de l'utilisateur
     */
    function deleteAllTranslations() {
      const button = root.querySelector('#delete-all-translations-btn');
      if (!button || !window.user_uuid || !window.lara_api_url || !window.deleteAllConfirmationMessages?.deleting) {
        return;
      }

      const originalContent = setButtonLoading(button, window.deleteAllConfirmationMessages.deleting);
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
          window.location.reload();
        })
        .catch(error => {
          restoreButton(button, originalContent);
          const errorMsg = window.deleteAllConfirmationMessages?.error;
          if (errorMsg) {
            showError(error, errorMsg);
          }
        });
    }

    // ============================================================================
    // GESTION DES ÉVÉNEMENTS
    // ============================================================================

    // ============================================================================
    // GESTION DE LA PÉRIODE DE RÉTENTION
    // ============================================================================

    /**
     * Envoie une requête PUT pour mettre à jour la période de rétention
     * @param {string} csrfToken - Token CSRF
     * @param {number} retentionPeriod - Nouvelle période de rétention
     * @returns {Promise<Response>}
     */
    async function _sendRetentionPeriodUpdate(csrfToken, retentionPeriod) {
      return fetch(changeDataUrl, {
        method: 'PUT',
        headers: {
          'X-CSRFToken': csrfToken,
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          retention_period: parseInt(retentionPeriod, 10),
        }),
        credentials: 'same-origin',
      });
    }

    /**
     * Met à jour la période de rétention de l'utilisateur
     * @param {number} retentionPeriod - Nouvelle période de rétention en jours
     */
    async function updateRetentionPeriod(retentionPeriod) {
      if (!changeDataUrl) {
        return;
      }

      const select = root.querySelector('#retention-period-select');
      if (!select) {
        return;
      }

      const originalValue = select.value;
      select.disabled = true;

      try {
        const csrfToken = getCSRFToken();
        if (!csrfToken) {
          throw new Error('CSRF token not found');
        }

        const response = await _sendRetentionPeriodUpdate(csrfToken, retentionPeriod);

        if (response.ok) {
          _showSuccessMessage(window.retentionPeriodMessages?.success);
        } else {
          const errorData = await response.json().catch(() => ({}));
          const errorMessage = errorData.detail || errorData.message || window.retentionPeriodMessages?.error;
          select.value = originalValue;
          _showErrorMessage(errorMessage);
        }
      } catch (error) {
        select.value = originalValue;
        _showErrorMessage(window.retentionPeriodMessages?.errorNetwork);
      } finally {
        select.disabled = false;
      }
    }

    /**
     * Affiche un message toast
     * @param {string} message - Message à afficher
     * @param {string} type - Type de message ('success' ou 'error')
     */
    function _showToastMessage(message, type) {
      if (!window.Toast || !message) {
        return;
      }
      
      const method = type === 'success' ? 'success' : 'error';
      if (typeof window.Toast[method] === 'function') {
        window.Toast[method](message);
      }
    }

    /**
     * Affiche un message de succès
     * @param {string} message - Message à afficher
     */
    function _showSuccessMessage(message) {
      _showToastMessage(message, 'success');
    }

    /**
     * Affiche un message d'erreur
     * @param {string} message - Message à afficher
     */
    function _showErrorMessage(message) {
      _showToastMessage(message, 'error');
    }

    /**
     * Initialise la gestion de la période de rétention
     */
    function initRetentionPeriod() {
      const select = root.querySelector('#retention-period-select');
      if (!select) {
        return;
      }

      let previousValue = select.value;

      select.addEventListener('change', (e) => {
        const newValue = e.target.value;
        
        // Vérifier si la valeur a vraiment changé
        if (newValue === previousValue) {
          return;
        }

        // Mettre à jour immédiatement pour un feedback visuel
        previousValue = newValue;
        
        // Mettre à jour via l'API
        updateRetentionPeriod(newValue);
      });
    }

    /**
     * Gère les clics sur les éléments interactifs
     * @param {Event} e - Événement de clic
     */
    function handleClick(e) {
      const logoutBtn = e.target.closest('#logout-btn');
      if (logoutBtn) {
        handleLogout(e);
        return;
      }

      const deleteBtn = e.target.closest('#delete-all-translations-btn');
      if (deleteBtn && !deleteBtn.disabled) {
        e.preventDefault();
        showDeleteConfirmationDialog(deleteAllTranslations);
      }
    }

    // ============================================================================
    // INITIALISATION
    // ============================================================================

    window.profileDetails = window.profileDetails || {};
    window.profileDetails.changeDataUrl = changeDataUrl;

    TabManager.init();
    handleUserDataUpdate();
    initRetentionPeriod();
    root.addEventListener('click', handleClick, true);
  });
})();
