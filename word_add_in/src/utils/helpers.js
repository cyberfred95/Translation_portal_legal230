// Fonction utilitaire pour remplir un élément <select> avec des options

/**
 * Remplit un élément select avec des options à partir d'un tableau d'objets.
 * @param {HTMLSelectElement} selectElement - L'élément select à remplir.
 * @param {Array} items - Les objets à utiliser pour les options.
 * @param {string} valueKey - La clé pour la valeur de l'option.
 * @param {string} textKey - La clé pour le texte affiché.
 */
export function populateSelect(selectElement, items, valueKey, textKey) {
  selectElement.innerHTML = "";
  items.forEach((item) => {
    const option = document.createElement("option");
    option.value = item[valueKey];
    option.textContent = item[textKey];
    selectElement.appendChild(option);
  });
} 