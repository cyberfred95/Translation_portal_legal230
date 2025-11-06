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

  // Formatage des nombres des cartes (ex: 770002 -> 770 002)
  const numberFormatter = new Intl.NumberFormat('fr-FR');
  root.querySelectorAll('.dashboard-card .stat-value').forEach((el) => {
    const raw = el.getAttribute('data-original-count') || el.textContent;
    let normalized = (raw || '').toString().replace(/[^0-9\-.,]/g, '');
    normalized = normalized.replace(',', '.');
    const num = Number(normalized);
    if (!Number.isNaN(num)) {
      el.textContent = numberFormatter.format(num);
    }
  });

  // Formater les nombres pour le tooltip (points tous les 3 chiffres)
  const formatNumber = (num) => {
    if (num === '∞' || num === 'infinity') return '∞';
    // Ne formater que des entiers positifs/négatifs simples
    const isNegative = String(num).trim().startsWith('-');
    const digits = String(num).replace(/[^0-9]/g, '');
    if (!digits) return num;
    const withDots = digits.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return isNegative ? `-${withDots}` : withDots;
  };

  // Formater les tooltips avec des espaces
  root.querySelectorAll('.dashboard-icon-content[data-tooltip]').forEach((el) => {
    const tooltip = el.getAttribute('data-tooltip');
    if (tooltip && tooltip.includes(' / ')) {
      const [numerator, denominator] = tooltip.split(' / ');
      const formatted = `${formatNumber(numerator)} / ${formatNumber(denominator)}`;
      el.setAttribute('data-tooltip', formatted);
    }
  });

  // Afficher l'anneau et cacher le skeleton une fois les données prêtes
  // On attend un court délai pour que le formatage soit terminé
  requestAnimationFrame(() => {
    root.querySelectorAll('.dashboard-icon-wrapper').forEach((wrapper) => {
      wrapper.classList.add('loaded');
      const ring = wrapper.querySelector('.dashboard-icon-content');
      if (ring) {
        const target = ring.getAttribute('data-pct') || '0';
        // Forcer un reflow pour garantir la transition
        // eslint-disable-next-line no-unused-expressions
        ring.offsetHeight;
        ring.style.setProperty('--pct', String(target));
      }
    });
  });

  // Coloration des badges de statut (utilise utils/status-utils.js)
  if (typeof window.applyStatusMapping === 'function') {
    window.applyStatusMapping(root);
  }
});


