/**
 * Système de Toast modulaire et réutilisable
 * 
 * @module Toast
 * 
 * @example
 * Toast.success('Message de succès');
 * Toast.error('Message d\'erreur');
 * 
 * @example
 * Toast.success('Message', {
 *   title: 'Titre',
 *   duration: 5000,
 *   showProgress: true
 * });
 */

(function() {
  'use strict';

  // ============================================================================
  // CONSTANTES
  // ============================================================================

  const DEFAULT_CONFIG = {
    duration: 5000,
    showProgress: true
  };

  const ANIMATION_DURATION = 300;
  const CONTAINER_ID = 'toast-container';
  const EXIT_ANIMATION_CLASS = 'toast-exiting';

  const TOAST_TYPES = {
    SUCCESS: 'success',
    ERROR: 'error',
    WARNING: 'warning',
    INFO: 'info'
  };

  const TOAST_ICONS = {
    [TOAST_TYPES.SUCCESS]: '<i class="ph ph-check-circle"></i>',
    [TOAST_TYPES.ERROR]: '<i class="ph ph-x-circle"></i>',
    [TOAST_TYPES.WARNING]: '<i class="ph ph-warning"></i>',
    [TOAST_TYPES.INFO]: '<i class="ph ph-info"></i>'
  };

  // ============================================================================
  // GESTION DU CONTENEUR
  // ============================================================================

  /**
   * Récupère ou crée le conteneur de toasts
   * @returns {HTMLElement|null} Le conteneur de toasts
   */
  function getContainer() {
    if (!document.body) {
      return null;
    }
    
    let container = document.getElementById(CONTAINER_ID);
    if (!container) {
      container = document.createElement('div');
      container.id = CONTAINER_ID;
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    return container;
  }

  /**
   * Supprime le conteneur s'il est vide
   */
  function cleanupContainer() {
    const container = document.getElementById(CONTAINER_ID);
    if (container && container.children.length === 0) {
      container.remove();
    }
  }

  // ============================================================================
  // UTILITAIRES
  // ============================================================================

  /**
   * Récupère le message traduit pour le bouton de fermeture
   * @returns {string} Message traduit
   */
  function getCloseLabel() {
    if (window.toastMessages && window.toastMessages.close) {
      return window.toastMessages.close;
    }
    return '';
  }

  /**
   * Crée un élément DOM avec les attributs spécifiés
   * @param {string} tag - Tag HTML
   * @param {string} className - Classe CSS
   * @param {Object} attributes - Attributs HTML
   * @returns {HTMLElement} Élément créé
   */
  function createElement(tag, className, attributes = {}) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    Object.entries(attributes).forEach(([key, value]) => {
      element.setAttribute(key, value);
    });
    return element;
  }

  // ============================================================================
  // CRÉATION DES ÉLÉMENTS DOM
  // ============================================================================

  /**
   * Crée l'élément icône du toast
   * @param {string} type - Type de toast
   * @returns {HTMLElement} Élément icône
   */
  function createIcon(type) {
    const icon = createElement('div', 'toast-icon');
    icon.innerHTML = TOAST_ICONS[type] || TOAST_ICONS[TOAST_TYPES.INFO];
    return icon;
  }

  /**
   * Crée l'élément contenu du toast
   * @param {string} message - Message à afficher
   * @param {string|null} title - Titre optionnel
   * @returns {HTMLElement} Élément contenu
   */
  function createContent(message, title) {
    const content = createElement('div', 'toast-content');

    if (title) {
      const titleEl = createElement('div', 'toast-title');
      titleEl.textContent = title;
      content.appendChild(titleEl);
    }

    const messageEl = createElement('div', title ? 'toast-message' : 'toast-title');
    messageEl.textContent = message;
    content.appendChild(messageEl);

    return content;
  }

  /**
   * Crée le bouton de fermeture
   * @param {HTMLElement} toast - Élément toast parent
   * @returns {HTMLElement} Bouton de fermeture
   */
  function createCloseButton(toast) {
    const closeBtn = createElement('button', 'toast-close', {
      type: 'button',
      'aria-label': getCloseLabel()
    });
    closeBtn.innerHTML = '<i class="ph ph-x"></i>';
    closeBtn.addEventListener('click', () => removeToast(toast));
    return closeBtn;
  }

  /**
   * Crée la barre de progression
   * @returns {Object} Objet contenant progress et progressBar
   */
  function createProgressBar() {
    const progress = createElement('div', 'toast-progress');
    const progressBar = createElement('div', 'toast-progress-bar');
    progressBar.style.width = '100%';
    progress.appendChild(progressBar);
    return { progress, progressBar };
  }

  /**
   * Initialise l'animation de la barre de progression
   * @param {HTMLElement} progressBar - Barre de progression
   * @param {number} duration - Durée en millisecondes
   */
  function startProgressAnimation(progressBar, duration) {
    progressBar.style.transition = `width ${duration}ms linear`;
    progressBar.offsetWidth; // Force reflow
    progressBar.style.width = '0%';
  }

  // ============================================================================
  // GESTION DU TIMER
  // ============================================================================

  /**
   * Classe pour gérer l'état du timer d'un toast
   */
  class ToastTimer {
    constructor(duration) {
      this.duration = duration;
      this.remainingTime = duration;
      this.startTime = Date.now();
      this.timeoutId = null;
    }

    start(callback) {
      this.startTime = Date.now();
      this.timeoutId = setTimeout(callback, this.remainingTime);
    }

    pause() {
      if (this.timeoutId) {
        clearTimeout(this.timeoutId);
        this.timeoutId = null;
        const elapsed = Date.now() - this.startTime;
        this.remainingTime -= elapsed;
      }
    }

    resume(callback) {
      if (this.remainingTime > 0) {
        this.start(callback);
      }
    }

    cancel() {
      if (this.timeoutId) {
        clearTimeout(this.timeoutId);
        this.timeoutId = null;
      }
    }
  }

  /**
   * Gère la pause de la barre de progression
   * @param {HTMLElement} progressBar - Barre de progression
   * @param {number} currentWidth - Largeur actuelle en pourcentage
   */
  function pauseProgressBar(progressBar, currentWidth) {
    progressBar.style.transition = 'none';
    progressBar.style.width = currentWidth + '%';
  }

  /**
   * Reprend la barre de progression
   * @param {HTMLElement} progressBar - Barre de progression
   * @param {number} remainingTime - Temps restant en millisecondes
   */
  function resumeProgressBar(progressBar, remainingTime) {
    const currentWidth = parseFloat(progressBar.style.width) || 100;
    progressBar.style.transition = `width ${remainingTime}ms linear`;
    progressBar.offsetWidth; // Force reflow
    progressBar.style.width = '0%';
  }

  // ============================================================================
  // FONCTION PRINCIPALE DE CRÉATION
  // ============================================================================

  /**
   * Crée et affiche un toast
   * @param {string} type - Type de toast
   * @param {string} message - Message à afficher
   * @param {Object} options - Options de configuration
   * @returns {HTMLElement|null} Élément toast créé
   */
  function createToast(type, message, options = {}) {
    const config = { ...DEFAULT_CONFIG, ...options };
    const container = getContainer();
    
    if (!container) {
      return null;
    }

    const toast = createElement('div', `toast toast-${type}`, {
      role: 'alert',
      'aria-live': 'polite'
    });

    toast.appendChild(createIcon(type));
    toast.appendChild(createContent(message, config.title));
    toast.appendChild(createCloseButton(toast));

    let progressBar = null;
    if (config.showProgress && config.duration > 0) {
      const { progress, progressBar: bar } = createProgressBar();
      progressBar = bar;
      toast.appendChild(progress);
    }

    container.appendChild(toast);

    if (config.duration > 0) {
      const timer = new ToastTimer(config.duration);
      toast._timer = timer;

      timer.start(() => removeToast(toast));

      if (progressBar) {
        startProgressAnimation(progressBar, config.duration);
      }

      toast.addEventListener('mouseenter', () => {
        timer.pause();
        if (progressBar) {
          const currentWidth = parseFloat(progressBar.style.width) || 100;
          pauseProgressBar(progressBar, currentWidth);
        }
      });

      toast.addEventListener('mouseleave', () => {
        timer.resume(() => removeToast(toast));
        if (progressBar) {
          resumeProgressBar(progressBar, timer.remainingTime);
        }
      });
    }

    return toast;
  }

  // ============================================================================
  // SUPPRESSION
  // ============================================================================

  /**
   * Supprime un toast avec animation
   * @param {HTMLElement} toast - Élément toast à supprimer
   */
  function removeToast(toast) {
    if (toast._timer) {
      toast._timer.cancel();
    }
    toast.classList.add(EXIT_ANIMATION_CLASS);

    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
      cleanupContainer();
    }, ANIMATION_DURATION);
  }

  // ============================================================================
  // API PUBLIQUE
  // ============================================================================

  const Toast = {
    success: (message, options = {}) => {
      return createToast(TOAST_TYPES.SUCCESS, message, options);
    },

    error: (message, options = {}) => {
      return createToast(TOAST_TYPES.ERROR, message, options);
    },

    warning: (message, options = {}) => {
      return createToast(TOAST_TYPES.WARNING, message, options);
    },

    info: (message, options = {}) => {
      return createToast(TOAST_TYPES.INFO, message, options);
    },

    clear: () => {
      const container = document.getElementById(CONTAINER_ID);
      if (container) {
        const toasts = container.querySelectorAll('.toast');
        toasts.forEach(toast => removeToast(toast));
      }
    }
  };

  // ============================================================================
  // INITIALISATION
  // ============================================================================

  window.Toast = Toast;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', getContainer);
  } else {
    getContainer();
  }
})();
