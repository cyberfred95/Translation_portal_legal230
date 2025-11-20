// Fonctions pour interagir avec l'API Lexa
// Toutes les fonctions ici gèrent les appels réseau à l'API Lexa

// Configuration de l'environnement
const API_VERSION = 'v1/';

function getBaseUrl() {
  // L'API est toujours sur le même domaine que l'add-in
  return `https://${window.location.hostname}/api/${API_VERSION}`;
}

const BASE_URL = getBaseUrl();

async function fetchWithApiKey(url, apiKey) {
  const response = await fetch(url, {
    headers: { Authorization: `Bearer ${apiKey}` },
  });
  let debugJson = null;
  try {
    const clone = response.clone();
    debugJson = await clone.json();
  } catch { }
  if (!response.ok) {
    const error = new Error();
    error.status = response.status;
    const contentType = response.headers.get('content-type') || '';
    if (debugJson) {
      error.body = debugJson;
    } else if (contentType.includes('application/json')) {
      try {
        error.body = await response.json();
      } catch {
        error.body = null;
      }
    } else {
      error.bodyText = await response.text();
    }
    throw error;
  }
  return await response.json();
}

/**
 * Charge la liste des langues disponibles via l'API Lexa.
 * @param {string} apiKey - La clé API à utiliser pour l'authentification.
 * @returns {Promise<Array>} - Un tableau d'objets langue.
 */
export async function loadLanguages(apiKey) {
  return fetchWithApiKey(`${BASE_URL}languages/`, apiKey);
}

/**
 * Charge la liste des domaines disponibles via l'API Lexa.
 * @param {string} apiKey - La clé API à utiliser pour l'authentification.
 * @returns {Promise<Array>} - Un tableau d'objets domaine.
 */
export async function loadDomains(apiKey) {
  return fetchWithApiKey(`${BASE_URL}domains/`, apiKey);
}

/**
 * Teste la validité de la clé API en appelant l'endpoint des langues.
 * @param {string} apiKey - La clé API à tester.
 * @returns {Promise<boolean>} - true si la clé est valide, sinon false.
 */
export async function testApiKey(apiKey) {
  const response = await fetch(`${BASE_URL}languages/`, {
    headers: { Authorization: `Bearer ${apiKey}` },
  });
  return response.ok;
}

/**
 * Appelle l'API Lexa pour traduire un texte.
 * @param {string} apiKey - La clé API.
 * @param {string} text - Le texte à traduire.
 * @param {string} sourceLang - Langue source.
 * @param {string} targetLang - Langue cible.
 * @param {string} domain - Domaine de traduction.
 * @returns {Promise<string>} - Le texte traduit.
 */
export async function callLexaAPI(apiKey, text, sourceLang, targetLang, domain) {
  const response = await fetch(`${BASE_URL}translate/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      action: "text_translate",
      text: text,
      source_language: sourceLang,
      target_language: targetLang,
      domain_name: domain,
    }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Erreur de l'API Lexa.");
  }
  const result = await response.json();
  return result.translated_text;
}

/**
 * Récupère l'URL du portail client Stripe.
 * @param {string} apiKey - La clé API.
 * @returns {Promise<string>} - L'URL du portail.
 */
export async function getPortalUrl(apiKey) {
  const response = await fetch(`${BASE_URL}stripe-portal-session/`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${apiKey}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    // Propager le message d'erreur du backend
    throw new Error(error.detail || "Erreur lors de la récupération du lien d'abonnement.");
  }

  const result = await response.json();
  return result.url;
}

/**
 * Vérifie si l'utilisateur a un abonnement Stripe actif.
 * @param {string} apiKey - La clé API.
 * @returns {Promise<boolean>} - true si l'utilisateur a un abonnement, false sinon.
 */
export async function checkSubscriptionStatus(apiKey) {
  try {
    const response = await fetch(`${BASE_URL}stripe-portal-session/?check_only=true`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${apiKey}`,
      },
    });
    return response.ok;
  } catch (error) {
    return false;
  }
} 