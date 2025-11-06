document.addEventListener('DOMContentLoaded', function () {
  const root = document.querySelector('.dashboard-page');
  if (!root) return;

  // Exemple: initialisation de l'intro si nécessaire
  const intro = root.querySelector('.dashboard-intro');
  if (intro && intro.hasAttribute('data-style')) {
    // prêt pour des comportements spécifiques plus tard
  }

  // Appliquer les couleurs de fond des icônes à partir de data-bg
  root.querySelectorAll('.dashboard-icon').forEach((el) => {
    const bg = el.getAttribute('data-bg');
    if (bg) {
      el.style.background = bg;
    }
  });

  // Coloration des badges de statut (utilise utils/status-utils.js)
  if (typeof window.applyStatusMapping === 'function') {
    window.applyStatusMapping(root);
  }
});


