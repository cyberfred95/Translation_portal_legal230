// Gestion centralisée des événements de l'interface utilisateur

import { showSettingsView, showMainView, setTestResult, showError } from './dom.js';
import { getApiKey, setApiKey } from '../utils/storage.js';
import { testApiKey, loadLanguages, loadDomains, callLexaAPI } from '../api/lexamtApi.js';
import { populateSelect } from '../utils/helpers.js';
import { handleSelectionChange as wordHandleSelectionChange } from '../office/word.js';
import { setSourceLang, setTargetLang, setSelectedDomain } from '../utils/storage.js';
import { chargerLanguesEtDomaines } from '../index.js';

// Accéder à i18n via window.i18n qui est défini globalement
// pour éviter les imports circulaires
const getI18n = () => window.i18n;

const getPlaceholderText = () => {
  const i18n = getI18n();
  return i18n ? i18n.t('ui.selectText') : 'Sélectionnez un texte';
};

const getLoadingText = () => {
  const i18n = getI18n();
  return i18n ? i18n.t('ui.translating') : 'Traduction en cours...';
};

/**
 * Initialise tous les listeners de l'UI.
 */
export function initializeUIEvents() {
  const settingsBtn = document.getElementById("settings-btn");
  const saveApiKeyBtn = document.getElementById("save-api-key");
  const testApiKeyBtn = document.getElementById("test-api-key");
  const backToMainBtn = document.getElementById("back-to-main");
  const translateBtn = document.getElementById("translate-btn");
  const replaceBtn = document.getElementById("replace-btn");
  const swapLanguagesBtn = document.getElementById("swap-languages");

  if (settingsBtn) {
    // Supprimer les anciens listeners en clonant le bouton
    const newSettingsBtn = settingsBtn.cloneNode(true);
    settingsBtn.parentNode.replaceChild(newSettingsBtn, settingsBtn);
    
    // Réattacher le listener sur le nouveau bouton
    const freshSettingsBtn = document.getElementById("settings-btn");
    freshSettingsBtn.addEventListener("click", (e) => {
      e.preventDefault();
      const settingsView = document.getElementById("settings-view");
      if (settingsView && settingsView.style.display === "block") {
        showMainView();
      } else {
        showSettingsView();
      }
    });
  }
  
  if (saveApiKeyBtn) saveApiKeyBtn.addEventListener("click", onSaveApiKey);
  if (testApiKeyBtn) testApiKeyBtn.addEventListener("click", onTestApiKey);
  if (backToMainBtn) backToMainBtn.addEventListener("click", showMainView);
  if (translateBtn) translateBtn.addEventListener("click", insertTranslationWithoutReplace);
  if (replaceBtn) {
    replaceBtn.disabled = true;
    replaceBtn.addEventListener("click", replaceSelectionWithTranslationBox);
  }
  if (swapLanguagesBtn) swapLanguagesBtn.addEventListener("click", swapLanguages);

  // Gestion du changement de sélection Word - vérifier que Office.context est disponible
  if (typeof Office !== 'undefined' && Office.context && Office.context.document) {
    Office.context.document.addHandlerAsync(Office.EventType.DocumentSelectionChanged, wordHandleSelectionChange, (asyncResult) => {
      if (asyncResult.status === Office.AsyncResultStatus.Failed) {
        // Gestion silencieuse des erreurs d'enregistrement du handler
      }
    });
  } else {
    // Contexte Office non disponible (mode développement ou hors Word)
  }

  // Ajout des listeners pour sauvegarder la sélection de langue
  const sourceLangSelect = document.getElementById("source-lang");
  const targetLangSelect = document.getElementById("target-lang");
  if (sourceLangSelect) {
    sourceLangSelect.addEventListener("change", (e) => {
      setSourceLang(e.target.value);
    });
  }
  if (targetLangSelect) {
    targetLangSelect.addEventListener("change", (e) => {
      setTargetLang(e.target.value);
    });
  }

  const domainSelect = document.getElementById("domain");
  if (domainSelect) {
    domainSelect.addEventListener("change", (e) => {
      setSelectedDomain(e.target.value);
    });
  }
}

// Fonctions de callback pour les boutons

function onSaveApiKey() {
  const apiKey = document.getElementById("api-key").value;
  const successMessage = document.getElementById("api-key-success");
  const errorMessage = document.getElementById("api-key-error");
  const previousApiKey = getApiKey();
  const i18n = getI18n();

  setApiKey(apiKey);
  errorMessage.style.display = "none";

  if (!apiKey) {
    if (previousApiKey) {
      successMessage.textContent = i18n ? i18n.t('ui.apiKeyDeleted') : 'API supprimée';
      successMessage.style.display = "block";
    } else {
      successMessage.textContent = "";
      successMessage.style.display = "none";
    }
  } else {
    successMessage.textContent = i18n ? i18n.t('ui.apiKeySaved') : 'Clé API sauvegardée. Testez ou retournez à l\'accueil.';
    successMessage.style.display = "block";
    // Ne pas recharger automatiquement les langues et domaines depuis la vue paramètres
    // L'utilisateur peut tester la clé ou retourner à l'accueil où les langues seront chargées
  }
}

async function onTestApiKey() {
  const apiKey = getApiKey();
  const i18n = getI18n();

  if (!apiKey) {
    setTestResult(i18n ? i18n.t('ui.apiKeyPrompt') : 'Veuillez configurer votre clé API dans les paramètres pour utiliser Lexa.');
    document.getElementById("test-result").style.color = "#dc2626";
    return;
  }

  setTestResult(i18n ? i18n.t('ui.translating') : 'Traduction en cours...');
  document.getElementById("test-result").style.color = "#6b7280";

  try {
    const ok = await testApiKey(apiKey);
    if (ok) {
      setTestResult(i18n ? i18n.t('ui.apiKeyValid') : 'Clé API valide');
      document.getElementById("test-result").style.color = "#16a34a";
    } else {
      setTestResult(i18n ? i18n.t('ui.apiKeyInvalid') : 'Clé API invalide');
      document.getElementById("test-result").style.color = "#dc2626";
    }
  } catch (error) {
    setTestResult(`${i18n ? i18n.t('ui.translationError') : 'Erreur lors de la traduction'}: ${error.message}`);
    document.getElementById("test-result").style.color = "#dc2626";
  }
}

// Fonction pour inverser les langues source/cible
function swapLanguages() {
  const sourceLangSelect = document.getElementById("source-lang");
  const targetLangSelect = document.getElementById("target-lang");
  const sourceVal = sourceLangSelect.value;
  sourceLangSelect.value = targetLangSelect.value;
  targetLangSelect.value = sourceVal;
  // Sauvegarde la nouvelle sélection
  setSourceLang(sourceLangSelect.value);
  setTargetLang(targetLangSelect.value);
}

// Nouvelle fonction : insère la traduction sans remplacer le texte sélectionné
async function insertTranslationWithoutReplace() {
  const apiKey = getApiKey();
  const sourceLang = document.getElementById("source-lang").value;
  const targetLang = document.getElementById("target-lang").value;
  const domain = document.getElementById("domain").value;
  const i18n = getI18n();

  if (!apiKey) {
    showError(i18n ? i18n.t('ui.apiKeyRequired') : 'Clé API requise');
    showSettingsView();
    return;
  }

  try {
    await Word.run(async (context) => {
      const range = context.document.getSelection();
      range.load("text");
      await context.sync();
      if (range.text.length > 0) {
        // Affiche l'animation de chargement dans l'encadré
        const resultBox = document.getElementById("translation-result");
        if (resultBox) {
          const loadingText = getLoadingText();
          resultBox.innerHTML = `<span class="translation-loading" style="font-style:italic; color:#888;">${loadingText}<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span></span>`;
          resultBox.style.display = "block";
          const replaceBtn = document.getElementById("replace-btn");
          if (replaceBtn) replaceBtn.disabled = true;
        }
        const translatedText = await callLexaAPI(apiKey, range.text, sourceLang, targetLang, domain);
        if (translatedText) {
          const placeholder = document.getElementById("translation-placeholder");
          if (placeholder) placeholder.style.display = "none";
          if (Array.isArray(translatedText)) {
            resultBox.innerHTML = translatedText.map(line => `<div>${line}</div>`).join("");
          } else {
            resultBox.textContent = translatedText;
          }
          resultBox.style.display = "block";
          const replaceBtn = document.getElementById("replace-btn");
          // Active le bouton seulement si on a une vraie traduction
          const placeholderText = getPlaceholderText();
          const loadingText = getLoadingText();
          const isValid = Array.isArray(translatedText)
            ? translatedText.some(line => line && line.trim() && line !== placeholderText && !line.startsWith(loadingText))
            : (translatedText && translatedText.trim() && translatedText !== placeholderText && !translatedText.startsWith(loadingText));
          if (replaceBtn) replaceBtn.disabled = !isValid;
          updateReplaceBtnState();
        }
      } else {
        showError(i18n ? i18n.t('ui.noTextSelected') : 'Aucun texte sélectionné');
      }
    });
  } catch (error) {
    const errorMsg = i18n ? i18n.t('ui.translationError') : 'Erreur lors de la traduction';
    showError(`${errorMsg}: ${error.message || error.toString()}`);
  }
}

// Nouvelle fonction : remplace la sélection Word par le texte de l'encadré de traduction
async function replaceSelectionWithTranslationBox() {
  const i18n = getI18n();
  const resultBox = document.getElementById("translation-result");
  if (!resultBox || resultBox.style.display === "none" || !resultBox.textContent.trim()) {
    showError(i18n ? i18n.t('ui.noTextSelected') : 'Aucun texte sélectionné');
    return;
  }
  // Récupère toutes les lignes (chaque div) ou le texte brut
  let lines = Array.from(resultBox.querySelectorAll('div')).map(div => div.textContent);
  if (lines.length === 0) {
    lines = [resultBox.textContent];
  }
  // Vérifie qu'il ne s'agit pas du placeholder ou du loading
  const placeholderText = getPlaceholderText();
  const loadingText = getLoadingText();
  const isValid = lines.some(line => line && line.trim() && line !== placeholderText && !line.startsWith(loadingText));
  if (!isValid) {
    showError(i18n ? i18n.t('ui.noTextSelected') : 'Aucun texte sélectionné');
    return;
  }
  const textToInsert = lines.join("\n");
  try {
    await Word.run(async (context) => {
      const range = context.document.getSelection();
      range.load("text");
      await context.sync();
      if (range.text.length > 0) {
        range.insertText(textToInsert, Word.InsertLocation.replace);
        await context.sync();
      } else {
        showError(i18n ? i18n.t('ui.noTextSelected') : 'Aucun texte sélectionné');
      }
    });
  } catch (error) {
    const errorMsg = i18n ? i18n.t('ui.translationError') : 'Erreur lors de la traduction';
    showError(`${errorMsg}: ${error.message || error.toString()}`);
  }
}

export function updateReplaceBtnState() {
  const resultBox = document.getElementById("translation-result");
  let hasValidTranslation = false;
  if (resultBox) {
    let lines = Array.from(resultBox.querySelectorAll('div')).map(div => div.textContent);
    if (lines.length === 0) lines = [resultBox.textContent];
    const placeholderText = getPlaceholderText();
    const loadingText = getLoadingText();
    hasValidTranslation = lines.some(line => line && line.trim() && line !== placeholderText && !line.startsWith(loadingText));
  }
  return hasValidTranslation;
} 