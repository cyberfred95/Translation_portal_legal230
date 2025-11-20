// Gestion centralisée des événements de l'interface utilisateur

import { showSettingsView, showMainView, setTestResult, showError } from './dom.js';
import { getApiKey, setApiKey } from '../utils/storage.js';
import { testApiKey, loadLanguages, loadDomains, callLexaAPI, getPortalUrl, checkSubscriptionStatus } from '../api/lexamtApi.js';
import { populateSelect } from '../utils/helpers.js';
import { handleSelectionChange as wordHandleSelectionChange } from '../office/word.js';
import { setSourceLang, setTargetLang, setSelectedDomain } from '../utils/storage.js';
import { chargerLanguesEtDomaines } from '../index.js';

// Accéder à i18n via window.i18n qui est défini globalement
// pour éviter les imports circulaires
const getI18n = () => window.i18n;

// Variable globale pour stocker le HTML traduit original de l'API
let translatedHtmlForWord = null;

const getPlaceholderText = () => {
  const i18n = getI18n();
  return i18n ? i18n.t('ui.selectText') : 'Sélectionnez un texte';
};

const getLoadingText = () => {
  const i18n = getI18n();
  return i18n ? i18n.t('ui.translating') : 'Traduction en cours...';
};

/**
 * Convertit OOXML en HTML enrichi pour l'API de traduction
 *
 * Styles supportés :
 * - Gras, italique, souligné, barré
 * - Exposant, indice
 * - Couleur du texte
 * - Police (font-family)
 * - Taille de police
 * - Listes à puces/numérotées
 */
const convertOoxmlToHtml = (ooxml) => {
  if (!ooxml) return '';

  // Parser le XML
  const parser = new DOMParser();
  const xmlDoc = parser.parseFromString(ooxml, 'text/xml');

  // Namespace Word
  const ns = {
    w: 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
  };

  let html = '';
  let currentListItems = [];
  let currentListLevel = -1;

  // Récupérer tous les paragraphes
  const paragraphs = xmlDoc.getElementsByTagNameNS(ns.w, 'p');

  for (let i = 0; i < paragraphs.length; i++) {
    const paragraph = paragraphs[i];
    let paragraphHtml = '';

    // Vérifier si c'est un élément de liste
    const pPr = paragraph.getElementsByTagNameNS(ns.w, 'pPr')[0];
    const numPr = pPr ? pPr.getElementsByTagNameNS(ns.w, 'numPr')[0] : null;
    const isListItem = numPr !== null && numPr !== undefined;

    let listLevel = 0;
    if (isListItem && numPr) {
      const ilvlNode = numPr.getElementsByTagNameNS(ns.w, 'ilvl')[0];
      if (ilvlNode) {
        listLevel = parseInt(ilvlNode.getAttribute('w:val') || '0', 10);
      }
    }

    // Récupérer tous les runs du paragraphe
    const runs = paragraph.getElementsByTagNameNS(ns.w, 'r');

    for (let run of runs) {
      const textNodes = run.getElementsByTagNameNS(ns.w, 't');
      const propsNode = run.getElementsByTagNameNS(ns.w, 'rPr')[0];

      let text = '';
      for (let textNode of textNodes) {
        text += textNode.textContent;
      }

      if (text) {
        // Détecter les styles
        let styles = {
          bold: false,
          italic: false,
          underline: false,
          strike: false,
          superscript: false,
          subscript: false,
          color: null,
          fontFamily: null,
          fontSize: null
        };

        if (propsNode) {
          styles.bold = propsNode.getElementsByTagNameNS(ns.w, 'b').length > 0;
          styles.italic = propsNode.getElementsByTagNameNS(ns.w, 'i').length > 0;
          styles.underline = propsNode.getElementsByTagNameNS(ns.w, 'u').length > 0;
          styles.strike = propsNode.getElementsByTagNameNS(ns.w, 'strike').length > 0;

          // Vérifier exposant/indice
          const vertAlignNodes = propsNode.getElementsByTagNameNS(ns.w, 'vertAlign');
          if (vertAlignNodes.length > 0) {
            const val = vertAlignNodes[0].getAttribute('w:val');
            if (val === 'superscript') styles.superscript = true;
            if (val === 'subscript') styles.subscript = true;
          }

          // Récupérer la couleur
          const colorNodes = propsNode.getElementsByTagNameNS(ns.w, 'color');
          if (colorNodes.length > 0) {
            const colorVal = colorNodes[0].getAttribute('w:val');
            if (colorVal && colorVal !== 'auto' && colorVal !== '000000') {
              styles.color = '#' + colorVal;
            }
          }

          // Récupérer la police
          const rFontsNodes = propsNode.getElementsByTagNameNS(ns.w, 'rFonts');
          if (rFontsNodes.length > 0) {
            // Essayer d'abord w:ascii, puis w:hAnsi, puis w:cs
            const fontNode = rFontsNodes[0];
            const fontFamily = fontNode.getAttribute('w:ascii') ||
              fontNode.getAttribute('w:hAnsi') ||
              fontNode.getAttribute('w:cs');
            if (fontFamily) {
              styles.fontFamily = fontFamily;
            }
          }

          // Récupérer la taille de police (en demi-points, donc diviser par 2)
          const szNodes = propsNode.getElementsByTagNameNS(ns.w, 'sz');
          if (szNodes.length > 0) {
            const sizeVal = szNodes[0].getAttribute('w:val');
            if (sizeVal) {
              const sizeInPt = parseInt(sizeVal, 10) / 2;
              styles.fontSize = `${sizeInPt}pt`;
            }
          }
        }

        // Construire le HTML avec les styles imbriqués
        let styledText = text;

        // Appliquer les styles de base
        if (styles.bold) styledText = `<b>${styledText}</b>`;
        if (styles.italic) styledText = `<i>${styledText}</i>`;
        if (styles.underline) styledText = `<u>${styledText}</u>`;
        if (styles.strike) styledText = `<s>${styledText}</s>`;
        if (styles.superscript) styledText = `<sup>${styledText}</sup>`;
        if (styles.subscript) styledText = `<sub>${styledText}</sub>`;

        // Appliquer les styles CSS (couleur, police, taille)
        const cssStyles = [];
        if (styles.color) cssStyles.push(`color:${styles.color}`);
        if (styles.fontFamily) cssStyles.push(`font-family:'${styles.fontFamily}'`);
        if (styles.fontSize) cssStyles.push(`font-size:${styles.fontSize}`);

        if (cssStyles.length > 0) {
          styledText = `<span style="${cssStyles.join(';')}">${styledText}</span>`;
        }

        paragraphHtml += styledText;
      }
    }

    // Gérer les listes
    if (paragraphHtml) {
      if (isListItem) {
        // Ajouter l'élément à la liste en cours
        currentListItems.push(paragraphHtml);
        currentListLevel = listLevel;

        // Vérifier si c'est le dernier paragraphe ou si le suivant n'est pas une liste
        const isLastParagraph = i === paragraphs.length - 1;
        let nextIsListItem = false;
        if (!isLastParagraph) {
          const nextParagraph = paragraphs[i + 1];
          const nextPPr = nextParagraph.getElementsByTagNameNS(ns.w, 'pPr')[0];
          const nextNumPr = nextPPr ? nextPPr.getElementsByTagNameNS(ns.w, 'numPr')[0] : null;
          nextIsListItem = nextNumPr !== null && nextNumPr !== undefined;
        }

        // Si c'est le dernier élément de liste, fermer la liste
        if (isLastParagraph || !nextIsListItem) {
          html += '<ul>';
          for (const item of currentListItems) {
            html += `<li>${item}</li>`;
          }
          html += '</ul>';
          currentListItems = [];
          currentListLevel = -1;

          // Ajouter un <br> si ce n'est pas le dernier paragraphe
          if (!isLastParagraph) {
            html += '<br>';
          }
        }
      } else {
        // Paragraphe normal
        if (paragraphs.length > 1 && i < paragraphs.length - 1) {
          html += paragraphHtml + '<br>';
        } else {
          html += paragraphHtml;
        }
      }
    }
  }

  return html;
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
        // Vérifier la visibilité du bouton Stripe
        try {
          updateSubscriptionButtonVisibility();
        } catch (error) {
          console.error("Erreur lors de la mise à jour de la visibilité du bouton abonnement:", error);
        }
      }
    });
  }

  // Listener pour le bouton Stripe
  const stripeBtn = document.getElementById("stripe-subscription-btn");
  if (stripeBtn) {
    stripeBtn.addEventListener("click", onManageSubscription);
  }

  if (saveApiKeyBtn) saveApiKeyBtn.addEventListener("click", onSaveApiKey);
  if (testApiKeyBtn) testApiKeyBtn.addEventListener("click", onTestApiKey);
  if (backToMainBtn) backToMainBtn.addEventListener("click", showMainView);

  // Utiliser l'approche OOXML
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
    // Vérifier la visibilité du bouton Stripe
    updateSubscriptionButtonVisibility();
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

// Fonction principale : insère la traduction sans remplacer le texte sélectionné
async function insertTranslationWithoutReplace() {
  const apiKey = getApiKey();
  const sourceLang = document.getElementById("source-lang").value;
  const targetLang = document.getElementById("target-lang").value;
  const domain = document.getElementById("domain").value;
  const i18n = getI18n();

  console.log("[Traduction] Démarrage de la traduction sans remplacement");

  if (!apiKey) {
    console.log("[Traduction] Erreur : Clé API manquante");
    showError(i18n ? i18n.t('ui.apiKeyRequired') : 'Clé API requise');
    showSettingsView();
    return;
  }

  try {
    await Word.run(async (context) => {
      const range = context.document.getSelection();
      const ooxmlResult = range.getOoxml();
      await context.sync();

      const ooxml = ooxmlResult.value;
      console.log("[Traduction] OOXML de la sélection capturé:", ooxml);

      // Convertir OOXML en HTML pour l'API
      const html = convertOoxmlToHtml(ooxml);
      console.log("[Traduction] HTML converti depuis OOXML:", html);

      if (html && typeof html === 'string' && html.trim().length > 0) {
        // Vérification simple : le HTML n'est pas vide
        console.log("[Traduction] Sélection non vide, HTML length:", html.length);
        // Affiche l'animation de chargement dans l'encadré
        const resultBox = document.getElementById("translation-result");
        if (resultBox) {
          const loadingText = getLoadingText();
          resultBox.innerHTML = `<span class="translation-loading" style="font-style:italic; color:#888;">${loadingText}<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span></span>`;
          resultBox.style.display = "block";
          const replaceBtn = document.getElementById("replace-btn");
          if (replaceBtn) replaceBtn.disabled = true;
          console.log("[Traduction] Animation de chargement affichée");
        }
        console.log("[Traduction] Appel de l'API avec :", { apiKey: apiKey ? "présente" : "absente", html, sourceLang, targetLang, domain });
        const translatedText = await callLexaAPI(apiKey, html, sourceLang, targetLang, domain);
        console.log("[Traduction] Réponse de l'API :", translatedText);
        if (translatedText) {
          const placeholder = document.getElementById("translation-placeholder");
          if (placeholder) placeholder.style.display = "none";

          // Stocker le HTML traduit original pour l'insertion dans Word
          translatedHtmlForWord = Array.isArray(translatedText) ? translatedText.join("") : translatedText;
          console.log("[Traduction] HTML traduit stocké pour Word:", translatedHtmlForWord);

          // Afficher le HTML dans la boîte de prévisualisation
          // On utilise innerHTML pour que le navigateur rende le HTML et affiche le formatage
          resultBox.innerHTML = translatedHtmlForWord;
          resultBox.style.display = "block";
          console.log("[Traduction] HTML traduit affiché dans la boîte");

          const replaceBtn = document.getElementById("replace-btn");
          // Active le bouton seulement si on a une vraie traduction
          const placeholderText = getPlaceholderText();
          const loadingText = getLoadingText();
          const isValid = translatedHtmlForWord && translatedHtmlForWord.trim() &&
            translatedHtmlForWord !== placeholderText &&
            !translatedHtmlForWord.startsWith(loadingText);
          if (replaceBtn) replaceBtn.disabled = !isValid;
          updateReplaceBtnState();
          console.log("[Traduction] Bouton de remplacement activé :", !replaceBtn.disabled);
        }
      } else {
        console.log("[Traduction] Erreur : Aucun texte sélectionné");
        showError(i18n ? i18n.t('ui.noTextSelected') : 'Aucun texte sélectionné');
      }
    });
  } catch (error) {
    console.log("[Traduction] Erreur lors de la traduction :", error);
    const errorMsg = i18n ? i18n.t('ui.translationError') : 'Erreur lors de la traduction';
    showError(`${errorMsg}: ${error.message || error.toString()}`);
  }
}

// Fonction principale : remplace la sélection Word par le texte de l'encadré de traduction
async function replaceSelectionWithTranslationBox() {
  const i18n = getI18n();
  const resultBox = document.getElementById("translation-result");
  console.log("[Remplacement] Démarrage du remplacement de la sélection");

  // Utiliser le HTML stocké plutôt que celui affiché dans la boîte
  if (!translatedHtmlForWord || !translatedHtmlForWord.trim()) {
    console.log("[Remplacement] Erreur : Aucun HTML traduit disponible");
    showError(i18n ? i18n.t('ui.noTextSelected') : 'Aucun texte sélectionné');
    return;
  }

  // Vérifie qu'il ne s'agit pas du placeholder ou du loading
  const placeholderText = getPlaceholderText();
  const loadingText = getLoadingText();
  const isValid = translatedHtmlForWord && translatedHtmlForWord.trim() &&
    translatedHtmlForWord !== placeholderText &&
    !translatedHtmlForWord.startsWith(loadingText);
  console.log("[Remplacement] Validation du HTML :", isValid);

  if (!isValid) {
    console.log("[Remplacement] Erreur : HTML invalide (placeholder ou loading)");
    showError(i18n ? i18n.t('ui.noTextSelected') : 'Aucun texte sélectionné');
    return;
  }

  try {
    await Word.run(async (context) => {
      const range = context.document.getSelection();
      range.load("text");
      await context.sync();
      console.log("[Remplacement] Sélection actuelle dans Word :", range.text);

      if (range.text.length > 0) {
        // Insère le HTML directement dans Word (plus rapide que la conversion OOXML)
        console.log("[Remplacement] Insertion du HTML dans Word :", translatedHtmlForWord);
        range.insertHtml(translatedHtmlForWord, Word.InsertLocation.replace);
        await context.sync();
        console.log("[Remplacement] Insertion terminée avec succès");
      } else {
        console.log("[Remplacement] Erreur : Aucune sélection dans Word");
        showError(i18n ? i18n.t('ui.noTextSelected') : 'Aucun texte sélectionné');
      }
    });
  } catch (error) {
    console.log("[Remplacement] Erreur lors du remplacement :", error);
    const errorMsg = i18n ? i18n.t('ui.translationError') : 'Erreur lors de la traduction';
    showError(`${errorMsg}: ${error.message || error.toString()}`);
  }
}

export function updateReplaceBtnState() {
  // Utiliser le HTML stocké plutôt que celui de la boîte
  const placeholderText = getPlaceholderText();
  const loadingText = getLoadingText();
  const hasValidTranslation = translatedHtmlForWord && translatedHtmlForWord.trim() &&
    translatedHtmlForWord !== placeholderText &&
    !translatedHtmlForWord.startsWith(loadingText);
  return hasValidTranslation;
}

/**
 * Gère le clic sur le bouton "Gérer mon abonnement Stripe"
 */
async function onManageSubscription() {
  const apiKey = getApiKey();
  const stripeBtn = document.getElementById("stripe-subscription-btn");
  const stripeError = document.getElementById("stripe-error");
  const i18n = getI18n();

  if (!apiKey) {
    stripeError.textContent = i18n ? i18n.t('ui.noApiKey') : "Aucune clé API configurée.";
    stripeError.style.display = "block";
    return;
  }

  // Afficher l'état de chargement
  stripeBtn.disabled = true;
  stripeBtn.textContent = i18n ? i18n.t('ui.subscriptionLoading') : "Chargement...";
  stripeError.style.display = "none";

  try {
    const portalUrl = await getPortalUrl(apiKey);

    // Ouvrir l'URL dans une nouvelle fenêtre
    
    window.open(portalUrl, '_blank');
    
  } catch (error) {
    // Gérer spécifiquement le cas "pas d'abonnement Stripe"
    if (error.message && (error.message.includes("no_stripe_customer") || error.message.includes("Aucun abonnement Stripe"))) {
      stripeError.textContent = i18n ? i18n.t('ui.noStripeSubscription') : "Aucun abonnement Stripe associé. Contactez support@lexamt.com";
    } else {
      stripeError.textContent = error.message || (i18n ? i18n.t('ui.subscriptionError') : "Erreur lors de la récupération du lien d'abonnement.");
    }
    stripeError.style.display = "block";
  } finally {
    // Restaurer le bouton
    stripeBtn.disabled = false;
    stripeBtn.textContent = i18n ? i18n.t('ui.manageSubscription') : 'Gérer mon abonnement';
  }
}

/**
 * Met à jour la visibilité du bouton d'abonnement Stripe
 */
async function updateSubscriptionButtonVisibility() {
  const apiKey = getApiKey();
  const section = document.getElementById("subscription-section");

  if (!section) return;

  if (!apiKey) {
    section.style.display = "none";
    return;
  }

  const hasSubscription = await checkSubscriptionStatus(apiKey);
  if (hasSubscription) {
    section.style.display = "block";
  } else {
    section.style.display = "none";
  }
} 