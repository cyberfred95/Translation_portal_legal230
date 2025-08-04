// Fonctions spécifiques à l'intégration avec Word/Office.js

import { showError } from '../ui/dom.js';
import { callLexaAPI } from '../api/lexamtApi.js';
import { getApiKey } from '../utils/storage.js';
import { updateReplaceBtnState } from '../ui/events.js';

/**
 * Gère l'activation/désactivation du bouton de traduction selon la sélection.
 */
export async function handleSelectionChange() {
  await Word.run(async (context) => {
    const range = context.document.getSelection();
    range.load("text");
    await context.sync();
    document.getElementById("translate-btn").disabled = range.text.length === 0;
    const replaceBtn = document.getElementById("replace-btn");
    if (replaceBtn) {
      const hasValidTranslation = updateReplaceBtnState();
      replaceBtn.disabled = range.text.length === 0 || !hasValidTranslation;
    }
  });
}

/**
 * Traduit la sélection Word et remplace le texte par la traduction.
 */
export async function translateFromSelection() {
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
        const translatedText = await callLexaAPI(apiKey, range.text, sourceLang, targetLang, domain);
        if (translatedText) {
          const textToInsert = Array.isArray(translatedText) ? translatedText[0] : translatedText;
          range.insertText(textToInsert, Word.InsertLocation.replace);
          await context.sync();
          showSuccess("La sélection a été traduite et remplacée.");
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