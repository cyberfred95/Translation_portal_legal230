// Global base.js - comportements transverses
(function () {
  // Namespace simple pour éviter la pollution globale
  window.AppBase = window.AppBase || {};

  AppBase.dispatchEvent = function (name, detail) {
    document.dispatchEvent(new CustomEvent(name, { detail }));
  };

  /**
   * Get translation based on current language code
   * Utility function available globally for consistent i18n
   * @param {string} enText - English text
   * @param {string} frText - French text
   * @returns {string} Translated text
   */
  AppBase.getTranslation = function (enText, frText) {
    const lang = window.language_code || 'en';
    return lang === 'fr' ? frText : enText;
  };

  /**
   * Extrait le message d'erreur d'un objet d'erreur AJAX
   * @param {Object} error - Objet d'erreur AJAX
   * @param {string} defaultMessage - Message par défaut si aucun message n'est trouvé
   * @returns {string} Message d'erreur
   */
  AppBase.extractErrorMessage = function (error, defaultMessage) {
    if (error?.responseJSON?.detail) {
      return error.responseJSON.detail;
    }
    if (error?.detail) {
      return error.detail;
    }
    if (error?.message) {
      return error.message;
    }
    if (defaultMessage) {
      return defaultMessage;
    }
    // Message par défaut selon la langue
    return AppBase.getTranslation(
      'Something went wrong',
      'Quelque chose s\'est mal passé.'
    );
  };

  /**
   * Affiche un message d'erreur via Toast ou console
   * @param {Object|string} error - Objet d'erreur AJAX ou message d'erreur
   * @param {string} defaultMessage - Message par défaut si error est un objet
   */
  AppBase.showError = function (error, defaultMessage) {
    const errorMessage = typeof error === 'string' 
      ? error 
      : AppBase.extractErrorMessage(error, defaultMessage);
    
    if (window.Toast && typeof window.Toast.error === 'function') {
      window.Toast.error(errorMessage);
    } else {
      console.error('Error:', errorMessage);
    }
  };
})();
