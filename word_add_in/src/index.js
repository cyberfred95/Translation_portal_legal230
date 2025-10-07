// Point d'entrée principal de l'add-in Lexa Word
// Initialise l'application et connecte tous les modules

import { initializeUIEvents } from './ui/events.js';
import { showSettingsView, showMainView } from './ui/dom.js';
import { getApiKey, getSourceLang, getTargetLang, getSelectedDomain } from './utils/storage.js';
import { loadLanguages, loadDomains } from './api/lexamtApi.js';
import { populateSelect } from './utils/helpers.js';
import { i18n } from './i18n/i18n.js';

// Office.onReady doit être appelé avant toute interaction avec l'API Office
if (typeof Office !== 'undefined') {
  Office.onReady((info) => {
    if (info.host === Office.HostType.Word) {
      initializeApp();
    }
  });
} else {
  // Fallback pour le développement/test en dehors de Word
  document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
  });
}

/**
 * Initialise l'application Lexa (UI, listeners, chargement initial)
 */
async function initializeApp() {
  // Initialiser le système i18n et attendre qu'il soit prêt
  await i18n.init();
  // Attendre suffisamment pour que initLanguageSelector() se termine (délai de 250ms dans i18n.init)
  await new Promise(resolve => setTimeout(resolve, 400));
  initializeUIEvents();
  
  // Ajouter le listener pour le lien 'Actualiser' de l'erreur API
  const refreshBtn = document.getElementById('api-error-refresh');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', (e) => {
      e.preventDefault();
      window.location.reload();
    });
  }
  
  const apiKey = getApiKey();
  document.getElementById("api-key").value = apiKey || "";
  showMainView();
  if (apiKey) {
    chargerLanguesEtDomaines();
  }
  // Désactiver le bouton de traduction initialement
  document.getElementById("translate-btn").disabled = true;
}

// Fonction utilitaire pour charger langues et domaines au démarrage
async function chargerLanguesEtDomaines() {
  const apiKey = getApiKey();
  if (!apiKey) return;
  const mainContent = document.getElementById("main-content");
  const noApiMessage = document.getElementById("no-api-message");
  const addedValueMessage = document.getElementById("added-value");
  const apiErrorMessage = document.getElementById("api-error-message");
  const apiErrorDetail = document.getElementById("api-error-detail");
  try {
    const languages = await loadLanguages(apiKey);
    populateSelect(document.getElementById("source-lang"), languages, "language_code", "name");
    populateSelect(document.getElementById("target-lang"), languages, "language_code", "name");
    // Sélectionne la langue source/cible sauvegardée ou la valeur par défaut
    const sourceSelect = document.getElementById("source-lang");
    const targetSelect = document.getElementById("target-lang");
    const savedSource = getSourceLang();
    const savedTarget = getTargetLang();
    if (sourceSelect) {
      if (savedSource && Array.from(sourceSelect.options).some(opt => opt.value === savedSource)) {
        sourceSelect.value = savedSource;
      } else {
        const frenchOption = Array.from(sourceSelect.options).find(opt => opt.textContent.trim().toLowerCase() === "french");
        if (frenchOption) sourceSelect.value = frenchOption.value;
      }
    }
    if (targetSelect) {
      if (savedTarget && Array.from(targetSelect.options).some(opt => opt.value === savedTarget)) {
        targetSelect.value = savedTarget;
      } else {
        const enUkOption = Array.from(targetSelect.options).find(opt => opt.textContent.trim().toLowerCase() === "english (uk)");
        if (enUkOption) targetSelect.value = enUkOption.value;
      }
    }
    const domains = await loadDomains(apiKey);
    populateSelect(document.getElementById("domain"), domains, "id", "name");
    const domainSelect = document.getElementById("domain");
    const savedDomain = getSelectedDomain();
    if (domainSelect) {
      if (savedDomain && Array.from(domainSelect.options).some(opt => opt.value === savedDomain)) {
        domainSelect.value = savedDomain;
      } else {
        // Si aucun domaine n'est sauvegardé, sélectionner le premier de la liste
        if (domainSelect.options.length > 0) {
          domainSelect.value = domainSelect.options[0].value;
        }
      }
    }
    // Si tout va bien, on masque le message d'erreur
    if (apiErrorMessage) apiErrorMessage.style.display = "none";
    if (apiErrorDetail) apiErrorDetail.textContent = "";
  } catch (error) {
    if (mainContent) mainContent.style.display = "none";
    if (noApiMessage) noApiMessage.style.display = "none";
    if (addedValueMessage) addedValueMessage.style.display = "none";
    if (apiErrorMessage) apiErrorMessage.style.display = "block";
    if (apiErrorDetail) {
      let code = error && (error.code || error.status || error.statusCode);
      let detail = error && error.body && error.body.detail;
      const contactAdminText = i18n ? i18n.t('ui.contactAdmin') : 'Contactez un administrateur';
      const errorCodeLabel = i18n ? i18n.t('ui.errorCodeLabel') : 'Code erreur :';
      
      if (detail) {
        apiErrorDetail.innerHTML = `${detail}<br><span style='display:inline-block;margin-top:10px;color:#b91c1c;font-size:13px;'>${contactAdminText}</span>`;
      } else if (error.bodyText) {
        apiErrorDetail.innerHTML = `<pre style='white-space:pre-wrap;word-break:break-all;'>${error.bodyText}</pre><span style='display:inline-block;margin-top:10px;color:#b91c1c;font-size:13px;'>${contactAdminText}</span>`;
      } else if (error.body) {
        apiErrorDetail.innerHTML = `<pre style='white-space:pre-wrap;word-break:break-all;'>${JSON.stringify(error.body, null, 2)}</pre><span style='display:inline-block;margin-top:10px;color:#b91c1c;font-size:13px;'>${contactAdminText}</span>`;
      } else if (code) {
        apiErrorDetail.innerHTML = `<strong>${errorCodeLabel}</strong> ${code}<br><span style='display:inline-block;margin-top:10px;color:#b91c1c;font-size:13px;'>${contactAdminText}</span>`;
      } else {
        apiErrorDetail.innerHTML = `<span style='color:#b91c1c;font-size:13px;'>${contactAdminText}</span>`;
      }
    }
  }
}

export { chargerLanguesEtDomaines }; 