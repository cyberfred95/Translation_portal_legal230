// Fonctions utilitaires pour manipuler le DOM et afficher les messages/vues

import { getApiKey } from '../utils/storage.js';
import { chargerLanguesEtDomaines } from '../index.js';

/**
 * Affiche la vue des paramètres (clé API).
 */
export function showSettingsView() {
  const mainContent = document.getElementById("main-content");
  const settingsView = document.getElementById("settings-view");
  const noApiMessage = document.getElementById("no-api-message");
  const addedValueMessage = document.getElementById("added-value");
  const apiErrorMessage = document.getElementById("api-error-message");
  const apiKeyInput = document.getElementById("api-key");

  if (mainContent) mainContent.style.display = "none";
  if (settingsView) settingsView.style.display = "block";
  if (noApiMessage) noApiMessage.style.display = "none";
  if (addedValueMessage) addedValueMessage.style.display = "none";
  if (apiErrorMessage) apiErrorMessage.style.display = "none";
  if (apiKeyInput) apiKeyInput.value = getApiKey() || "";
}

/**
 * Affiche la vue principale (traduction).
 */
export function showMainView() {
  console.log("showMainView appelée");
  const settingsView = document.getElementById("settings-view");
  const settingsBtn = document.getElementById("settings-btn");
  const success = document.getElementById("api-key-success");
  const error = document.getElementById("api-key-error");
  const testResult = document.getElementById("test-result");
  const mainContent = document.getElementById("main-content");
  const noApiMessage = document.getElementById("no-api-message");
  const addedValueMessage = document.getElementById("added-value");

  if (settingsView) settingsView.style.display = "none";
  if (settingsBtn) settingsBtn.style.display = "block";
  if (success) {
    success.textContent = "";
    success.style.display = "none";
  }
  if (error) {
    error.textContent = "";
    error.style.display = "none";
  }
  if (testResult) {
    testResult.textContent = "";
    testResult.classList.remove("has-text");
  }
  // Affichage conditionnel selon la présence de la clé API
  const apiKey = getApiKey();
  const apiErrorMessage = document.getElementById("api-error-message");
  
  // Masquer le message d'erreur global au début
  if (apiErrorMessage) apiErrorMessage.style.display = "none";
  
  if (!apiKey) {
    if (mainContent) mainContent.style.display = "none";
    if (noApiMessage) noApiMessage.style.display = "block";
    if (addedValueMessage) addedValueMessage.style.display = "block";
  } else {
    if (mainContent) mainContent.style.display = "block";
    if (noApiMessage) noApiMessage.style.display = "none";
    if (addedValueMessage) addedValueMessage.style.display = "none";
    // On refetch à chaque retour sur la main view
    chargerLanguesEtDomaines();
  }
}

/**
 * Affiche un message d'erreur temporaire.
 * @param {string} message - Le message à afficher.
 */
export function showError(message) {
  const errorElement = document.getElementById("error-message");
  errorElement.textContent = message;
  errorElement.style.display = "block";
  setTimeout(() => {
    errorElement.style.display = "none";
  }, 5000);
}

/**
 * Affiche un message de succès temporaire.
 * @param {string} message - Le message à afficher.
 */
export function showSuccess(message) {
  const successElement = document.getElementById("success-message");
  successElement.textContent = message;
  successElement.style.display = "block";
  setTimeout(() => {
    successElement.style.display = "none";
  }, 3000);
}

/**
 * Affiche ou masque l'indicateur de chargement.
 * @param {boolean} isLoading - true pour afficher, false pour masquer.
 */
export function setLoading(isLoading) {
  document.getElementById("loading").style.display = isLoading ? "block" : "none";
  document.getElementById("translate-btn").disabled = isLoading;
}

/**
 * Affiche le résultat du test API dans #test-result, avec la classe .has-text uniquement si du texte est présent.
 * @param {string} text
 */
export function setTestResult(text) {
  const testResult = document.getElementById("test-result");
  testResult.textContent = text || "";
  if (text && text.trim() !== "") {
    testResult.classList.add("has-text");
  } else {
    testResult.classList.remove("has-text");
  }
} 