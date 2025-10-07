// Module de gestion de l'internationalisation (i18n)
// Gère le chargement, le changement de langue et l'application des traductions

import { translations } from './translations.js';

class I18n {
  constructor() {
    this.currentLanguage = this.detectBrowserLanguage();
    this.translations = translations;
  }

  /**
   * Détecte la langue du navigateur et retourne un code de langue supporté
   * @returns {string} Code de langue (fr, en, es, de, it)
   */
  detectBrowserLanguage() {
    const browserLang = navigator.language || navigator.userLanguage;
    const langCode = browserLang.split('-')[0].toLowerCase();
    
    // Vérifie si la langue est supportée, sinon retourne 'fr' par défaut
    const supportedLanguages = ['fr', 'en', 'es', 'de', 'it'];
    return supportedLanguages.includes(langCode) ? langCode : 'fr';
  }

  /**
   * Change la langue courante
   * @param {string} langCode - Code de langue (fr, en, es, de, it)
   */
  setLanguage(langCode) {
    if (this.translations[langCode]) {
      this.currentLanguage = langCode;
      localStorage.setItem('lexa-language', langCode); // Utiliser une clé cohérente
      this.updateUI();
    } else {
      // Langue non supportée, on ignore la requête
    }
  }

  /**
   * Récupère la langue courante
   * @returns {string} Code de langue
   */
  getLanguage() {
    return this.currentLanguage;
  }

  /**
   * Récupère la langue sauvegardée ou détecte automatiquement
   * @returns {string} Code de langue
   */
  getSavedOrDetectedLanguage() {
    const savedLang = localStorage.getItem('lexa-language'); // Clé cohérente
    if (savedLang && this.translations[savedLang]) {
      return savedLang;
    }
    const detected = this.detectBrowserLanguage();
    return detected;
  }

  /**
   * Traduit une clé
   * @param {string} key - Clé de traduction (ex: 'ui.translate')
   * @returns {string} Texte traduit
   */
  t(key) {
    const keys = key.split('.');
    let value = this.translations[this.currentLanguage];
    
    for (const k of keys) {
      if (value && value[k] !== undefined) {
        value = value[k];
      } else {
        return key;
      }
    }
    
    return value;
  }

  /**
   * Met à jour tous les éléments de l'interface avec data-i18n
   */
  updateUI() {
    // Mettre à jour les éléments avec data-i18n
    const elements = document.querySelectorAll('[data-i18n]');
    elements.forEach(element => {
      const key = element.getAttribute('data-i18n');
      const translation = this.t(key);
      
      if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
        element.value = translation;
      } else {
        element.textContent = translation;
      }
    });

    // Mettre à jour les placeholders
    const placeholderElements = document.querySelectorAll('[data-i18n-placeholder]');
    placeholderElements.forEach(element => {
      const key = element.getAttribute('data-i18n-placeholder');
      element.placeholder = this.t(key);
    });

    // Mettre à jour les attributs title
    const titleElements = document.querySelectorAll('[data-i18n-title]');
    titleElements.forEach(element => {
      const key = element.getAttribute('data-i18n-title');
      element.title = this.t(key);
    });

    // Mettre à jour le sélecteur de langue pour refléter la langue active
    this.updateLanguageSelector();

    // Déclencher un événement personnalisé pour notifier le changement de langue
    window.dispatchEvent(new CustomEvent('languageChanged', { 
      detail: { language: this.currentLanguage } 
    }));
    
  }
  
  /**
   * Met à jour le sélecteur de langue avec le drapeau actuel
   */
  updateLanguageSelector() {
    const selectedFlag = document.getElementById('selected-flag');
    const selectButton = document.getElementById('language-select-button');
    
    if (selectedFlag && selectButton && this.translations[this.currentLanguage]) {
      const lang = this.translations[this.currentLanguage];
      selectedFlag.src = lang.flag;
      selectedFlag.alt = this.currentLanguage;
      selectButton.title = lang.name;
    } else {
      // Impossible de mettre à jour le sélecteur de langue (probablement hors du taskpane)
    }
  }

  /**
   * Crée le sélecteur de langue si les éléments n'existent pas
   */
  createLanguageSelector() {
    const headerControls = document.querySelector('.header-controls');
    
    if (!headerControls) {
      return;
    }

    // Vérifier si le sélecteur existe déjà
    const existing = document.getElementById('language-selector');
    if (existing) existing.remove();

    // Créer la structure complète du dropdown
    const customSelect = document.createElement('div');
    customSelect.className = 'custom-select';
    customSelect.id = 'language-selector';

    customSelect.innerHTML = `
      <div class="select-button" id="language-select-button" data-i18n-title="ui.selectLanguage" title="Choisir la langue de l'interface">
        <img src="/word_add_in/assets/flags/fr.svg" class="flag-img" id="selected-flag" alt="FR" />
        <span class="dropdown-arrow">▼</span>
      </div>
      <div class="options-container" id="language-options">
        <!-- Les options seront remplies dynamiquement par JavaScript -->
      </div>
    `;

    // Insérer avant le bouton settings
    const settingsBtn = headerControls.querySelector('#settings-btn');
    if (settingsBtn) {
      headerControls.insertBefore(customSelect, settingsBtn);
    } else {
      headerControls.appendChild(customSelect);
    }
  }

  /**
   * Initialise le sélecteur de langue avec dropdown personnalisé
   */
  initLanguageSelector() {
    const selectButton = document.getElementById('language-select-button');
    const optionsContainer = document.getElementById('language-options');
    const selectedFlag = document.getElementById('selected-flag');
    
    if (!selectButton || !optionsContainer || !selectedFlag) {
      return;
    }

    // Vider les options existantes
    optionsContainer.innerHTML = '';

    // Ajouter les options pour chaque langue (drapeaux uniquement)
    Object.keys(this.translations).forEach(langCode => {
      const lang = this.translations[langCode];
      
      const optionDiv = document.createElement('div');
      optionDiv.className = 'option-item';
      optionDiv.dataset.lang = langCode;
      optionDiv.title = lang.name;
      
      optionDiv.innerHTML = `<img src="${lang.flag}" class="flag-img" alt="${langCode}" />`;
      
      // Utiliser une fonction fléchée pour éviter les problèmes de contexte
      optionDiv.addEventListener('click', (e) => {
        e.stopPropagation();
        this.selectLanguage(langCode);
      });
      optionsContainer.appendChild(optionDiv);
    });

    // Supprimer les anciens listeners pour éviter les doublons
    const newSelectButton = selectButton.cloneNode(true);
    selectButton.parentNode.replaceChild(newSelectButton, selectButton);
    
    // Récupérer les nouveaux éléments après le clonage
    const freshSelectButton = document.getElementById('language-select-button');
    const freshOptionsContainer = document.getElementById('language-options');
    
    // Ajouter le listener pour le toggle dropdown
    freshSelectButton.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      const isVisible = freshOptionsContainer.classList.contains('show');
      
      if (isVisible) {
        freshOptionsContainer.classList.remove('show');
      } else {
        freshOptionsContainer.classList.add('show');
      }
    });

    // Fermer dropdown si on clique ailleurs (utiliser once: false car on veut que ça persiste)
    const closeDropdown = (e) => {
      // Ne PAS fermer si on clique sur le bouton settings
      if (e.target.closest('#settings-btn')) return;
      
      if (!e.target.closest('#language-selector')) {
        freshOptionsContainer.classList.remove('show');
      }
    };
    
    // Supprimer l'ancien listener et en ajouter un nouveau
    document.removeEventListener('click', closeDropdown);
    document.addEventListener('click', closeDropdown);

    // Mettre à jour l'affichage avec la langue courante
    this.updateLanguageSelector();
  }

  /**
   * Sélectionne une langue et met à jour l'interface
   */
  selectLanguage(langCode) {
    if (!this.translations[langCode]) {
      return;
    }
    
    this.currentLanguage = langCode;
    const lang = this.translations[langCode];
    
    // Sauvegarder la langue
    localStorage.setItem('lexa-language', langCode);
    
    // Mettre à jour l'affichage du bouton
    const selectedFlag = document.getElementById('selected-flag');
    const selectButton = document.getElementById('language-select-button');
    const optionsContainer = document.getElementById('language-options');
    
    if (selectedFlag && selectButton) {
      selectedFlag.src = lang.flag;
      selectedFlag.alt = langCode;
      selectButton.title = lang.name;
    }
    
    // Mettre à jour les options sélectionnées
    document.querySelectorAll('.option-item').forEach(item => {
      item.classList.toggle('selected', item.dataset.lang === langCode);
    });
    
    // Fermer le dropdown
    if (optionsContainer) {
      optionsContainer.classList.remove('show');
    }
    
    // Appliquer les traductions à TOUTE l'interface
    this.updateUI();
  }

  /**
   * Initialise le système i18n
   */
  async init() {
    try {
      // Attendre que le DOM soit complètement chargé
      if (document.readyState === 'loading') {
        await new Promise(resolve => {
          document.addEventListener('DOMContentLoaded', resolve, { once: true });
        });
      }
      
      // Attendre que window.load soit déclenché si pas encore fait
      if (document.readyState !== 'complete') {
        await new Promise(resolve => {
          window.addEventListener('load', resolve, { once: true });
        });
      }
      
      // Petit délai supplémentaire pour s'assurer que tout est prêt
      await new Promise(resolve => setTimeout(resolve, 150));
      
      const lang = this.getSavedOrDetectedLanguage();
      this.currentLanguage = lang; // Définir sans appeler setLanguage pour éviter double updateUI
      
      // Appliquer les traductions initiales
      this.updateUI();
      
      // Initialiser le sélecteur avec un délai pour s'assurer que le DOM est stable
      setTimeout(() => {
        this.initLanguageSelector();
      }, 250);
    } catch (_error) {
      // Erreur d'initialisation silencieuse pour éviter les logs inutiles
    }
  }
}

// Créer et exporter l'instance globale
export const i18n = new I18n();

// Rendre disponible globalement pour faciliter l'utilisation
if (typeof window !== 'undefined') {
  window.i18n = i18n;
}
