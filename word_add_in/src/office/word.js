// Fonctions spécifiques à l'intégration avec Word/Office.js

import { showError, showSettingsView, showSuccess } from '../ui/dom.js';
import { callLexaAPI } from '../api/lexamtApi.js';
import { getApiKey } from '../utils/storage.js';
import { updateReplaceBtnState } from '../ui/events.js';
import { i18n as i18nInstance } from '../i18n/i18n.js';

const getI18n = () => (typeof window !== 'undefined' && window.i18n) ? window.i18n : i18nInstance;

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
        const translatedText = await callLexaAPI(apiKey, range.text, sourceLang, targetLang, domain);
        if (translatedText) {
          const textToInsert = Array.isArray(translatedText) ? translatedText[0] : translatedText;
          range.insertText(textToInsert, Word.InsertLocation.replace);
          await context.sync();
          showSuccess(i18n ? i18n.t('ui.translationSuccess') : 'Traduction insérée avec succès');
        }
      } else {
        showError(i18n ? i18n.t('ui.noTextSelected') : 'Aucun texte sélectionné');
      }
    });
  } catch (error) {
    const errorLabel = i18n ? i18n.t('ui.translationError') : 'Erreur lors de la traduction';
    showError(`${errorLabel}: ${error.message || error.toString()}`);
  }
} 