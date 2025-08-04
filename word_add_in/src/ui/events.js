// Gestion centralisée des événements de l'interface utilisateur

import { showSettingsView, showMainView, setTestResult, showError } from './dom.js';
import { getApiKey, setApiKey } from '../utils/storage.js';
import { testApiKey, loadLanguages, loadDomains, callLexaAPI } from '../api/lexamtApi.js';
import { populateSelect } from '../utils/helpers.js';
import { handleSelectionChange as wordHandleSelectionChange } from '../office/word.js';
import { setSourceLang, setTargetLang, setSelectedDomain } from '../utils/storage.js';
import { chargerLanguesEtDomaines } from '../index.js';

const TRANSLATION_PLACEHOLDER_TEXT = "Sélectionnez un texte";
const TRANSLATION_LOADING_TEXT = "Traduction en cours...";

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

  if (settingsBtn) settingsBtn.addEventListener("click", () => {
    const settingsView = document.getElementById("settings-view");
    if (settingsView.style.display === "block") {
      showMainView();
    } else {
      showSettingsView();
    }
  });
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
  if (Office && Office.context && Office.context.document) {
    Office.context.document.addHandlerAsync(Office.EventType.DocumentSelectionChanged, wordHandleSelectionChange, (asyncResult) => {
      if (asyncResult.status === Office.AsyncResultStatus.Failed) {
        console.error("Impossible d'enregistrer le gestionnaire de changement de sélection.");
      }
    });
  } else {
    console.warn("Office.context not available during initialization");
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

  setApiKey(apiKey);
  errorMessage.style.display = "none";

  if (!apiKey) {
    if (previousApiKey) {
      successMessage.textContent = "API supprimée";
      successMessage.style.display = "block";
    } else {
      successMessage.textContent = "";
      successMessage.style.display = "none";
    }
  } else {
    successMessage.textContent = "Clé API sauvegardée. Testez ou retournez à l'accueil.";
    successMessage.style.display = "block";
    // Ne pas recharger automatiquement les langues et domaines depuis la vue paramètres
    // L'utilisateur peut tester la clé ou retourner à l'accueil où les langues seront chargées
  }
}

async function onTestApiKey() {
  const apiKey = getApiKey();

  if (!apiKey) {
    setTestResult("Veuillez d'abord sauvegarder une clé API.");
    document.getElementById("test-result").style.color = "#dc2626";
    return;
  }

  setTestResult("Test en cours...");
  document.getElementById("test-result").style.color = "#6b7280";

  try {
    const ok = await testApiKey(apiKey);
    if (ok) {
      setTestResult("Connexion réussie ! L'API est fonctionnelle.");
      document.getElementById("test-result").style.color = "#16a34a";
    } else {
      setTestResult(`Échec de la connexion.`);
      document.getElementById("test-result").style.color = "#dc2626";
    }
  } catch (error) {
    setTestResult(`Erreur réseau: ${error.message}`);
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

  if (!apiKey) {
    showError("Clé API non configurée.");
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
          resultBox.innerHTML = `<span class=\"translation-loading\" style=\"font-style:italic; color:#888;\">${TRANSLATION_LOADING_TEXT}<span class=\"dot\">.</span><span class=\"dot\">.</span><span class=\"dot\">.</span></span>`;
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
          const isValid = Array.isArray(translatedText)
            ? translatedText.some(line => line && line.trim() && line !== TRANSLATION_PLACEHOLDER_TEXT && !line.startsWith(TRANSLATION_LOADING_TEXT))
            : (translatedText && translatedText.trim() && translatedText !== TRANSLATION_PLACEHOLDER_TEXT && !translatedText.startsWith(TRANSLATION_LOADING_TEXT));
          if (replaceBtn) replaceBtn.disabled = !isValid;
          updateReplaceBtnState();
        }
      } else {
        showError("Veuillez sélectionner du texte à traduire.");
      }
    });
  } catch (error) {
    console.error(error);
    showError(`Erreur: ${error.message || error.toString()}`);
  }
}

// Nouvelle fonction : remplace la sélection Word par le texte de l'encadré de traduction
async function replaceSelectionWithTranslationBox() {
  const resultBox = document.getElementById("translation-result");
  if (!resultBox || resultBox.style.display === "none" || !resultBox.textContent.trim()) {
    showError("Aucune traduction à insérer.");
    return;
  }
  // Récupère toutes les lignes (chaque div) ou le texte brut
  let lines = Array.from(resultBox.querySelectorAll('div')).map(div => div.textContent);
  if (lines.length === 0) {
    lines = [resultBox.textContent];
  }
  // Vérifie qu'il ne s'agit pas du placeholder ou du loading
  const isValid = lines.some(line => line && line.trim() && line !== TRANSLATION_PLACEHOLDER_TEXT && !line.startsWith(TRANSLATION_LOADING_TEXT));
  if (!isValid) {
    showError("Aucune traduction à insérer.");
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
        // showSuccess("La traduction a été insérée dans le document.");
      } else {
        showError("Veuillez sélectionner du texte à remplacer.");
      }
    });
  } catch (error) {
    console.error(error);
    showError(`Erreur: ${error.message || error.toString()}`);
  }
}

export function updateReplaceBtnState() {
  const resultBox = document.getElementById("translation-result");
  let hasValidTranslation = false;
  if (resultBox) {
    let lines = Array.from(resultBox.querySelectorAll('div')).map(div => div.textContent);
    if (lines.length === 0) lines = [resultBox.textContent];
    hasValidTranslation = lines.some(line => line && line.trim() && line !== TRANSLATION_PLACEHOLDER_TEXT && !line.startsWith(TRANSLATION_LOADING_TEXT));
  }
  return hasValidTranslation;
} 