// Fonctions utilitaires pour gérer la clé API dans le stockage local

/**
 * Récupère la clé API sauvegardée dans le localStorage.
 * @returns {string|null} La clé API ou null si absente.
 */
export function getApiKey() {
  return localStorage.getItem("lexamt_api_key");
}

/**
 * Sauvegarde la clé API dans le localStorage.
 * @param {string} apiKey - La clé API à sauvegarder.
 */
export function setApiKey(apiKey) {
  localStorage.setItem("lexamt_api_key", apiKey);
} 

/**
 * Sauvegarde la langue source sélectionnée dans le localStorage.
 * @param {string} langCode
 */
export function setSourceLang(langCode) {
  localStorage.setItem("lexamt_source_lang", langCode);
}

/**
 * Récupère la langue source sélectionnée depuis le localStorage.
 * @returns {string|null}
 */
export function getSourceLang() {
  return localStorage.getItem("lexamt_source_lang");
}

/**
 * Sauvegarde la langue cible sélectionnée dans le localStorage.
 * @param {string} langCode
 */
export function setTargetLang(langCode) {
  localStorage.setItem("lexamt_target_lang", langCode);
}

/**
 * Récupère la langue cible sélectionnée depuis le localStorage.
 * @returns {string|null}
 */
export function getTargetLang() {
  return localStorage.getItem("lexamt_target_lang");
}

/**
 * Sauvegarde le domaine sélectionné dans le localStorage.
 * @param {string} domainId
 */
export function setSelectedDomain(domainId) {
  localStorage.setItem("lexamt_selected_domain", domainId);
}

/**
 * Récupère le domaine sélectionné depuis le localStorage.
 * @returns {string|null}
 */
export function getSelectedDomain() {
  return localStorage.getItem("lexamt_selected_domain");
} 