/**
 * Project History JavaScript
 * Gère les interactions de la page project history
 */
document.addEventListener('DOMContentLoaded', function () {
  const root = document.querySelector('.project-history-page');
  if (!root) return;

  // Appliquer le mapping des statuts au chargement de la page
  if (typeof window.applyStatusMapping === 'function') {
    window.applyStatusMapping(root);
  }

  const modalRevision = root.querySelector('#modal-revision');
  const closeRevision = root.querySelector('#close-revision');

  // Gestion du clic sur le bouton expert-revision dans le tableau
  root.addEventListener('click', function (e) {
    const expertBtn = e.target.closest('.expert-revision');
    if (expertBtn && expertBtn.closest('table')) {
      if (expertBtn.disabled) return;

      const translatedFile = expertBtn.dataset.translatedFile;
      const id = expertBtn.dataset.id;
      const display = expertBtn.dataset.display;

      // Transfert des données au bouton dans la modale
      const modalBtn = modalRevision.querySelector('.expert-revision');
      if (modalBtn) {
        modalBtn.dataset.translatedFile = translatedFile;
        modalBtn.dataset.id = id;
      }

      // Affichage de la modale selon data-display
      const showTrue = modalRevision.querySelector('.show-modal-true');
      const showFalse = modalRevision.querySelector('.show-modal-false');
      
      if (display === 'false' || display === 'False') {
        showTrue.classList.remove('hidden');
        showFalse.classList.add('hidden');
      } else {
        showTrue.classList.add('hidden');
        showFalse.classList.remove('hidden');
      }

      modalRevision.classList.remove('hidden');
      if (closeRevision) closeRevision.classList.remove('hidden');
    }
  });

  // Fermeture de la modale
  if (closeRevision) {
    closeRevision.addEventListener('click', function () {
      modalRevision.classList.add('hidden');
      closeRevision.classList.add('hidden');
      modalRevision.querySelectorAll('.show-modal-true, .show-modal-false').forEach(el => {
        el.classList.add('hidden');
      });
    });
  }

  // Fermeture au clic sur l'overlay
  if (modalRevision) {
    modalRevision.addEventListener('click', function (e) {
      if (e.target === modalRevision) {
        modalRevision.classList.add('hidden');
        if (closeRevision) closeRevision.classList.add('hidden');
        modalRevision.querySelectorAll('.show-modal-true, .show-modal-false').forEach(el => {
          el.classList.add('hidden');
        });
      }
    });
  }

  // Gestion du clic sur le bouton expert-revision dans la modale
  if (modalRevision) {
    modalRevision.addEventListener('click', function (e) {
      const modalBtn = e.target.closest('.expert-revision');
      if (!modalBtn || modalBtn.closest('table')) return;

      const translatedFile = modalBtn.dataset.translatedFile;
      const id = modalBtn.dataset.id;

      const formData = new FormData();
      formData.append('file_url', translatedFile);
      formData.append('project_id', id);

      fetch(window.expert_revision_file_url, {
        method: 'POST',
        body: formData,
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
          'Accept': 'application/json',
        },
      })
        .then(response => {
          if (!response.ok) {
            return response.json().then(err => Promise.reject(err));
          }
          return response.json();
        })
        .then(() => {
          window.location.reload();
        })
        .catch(error => {
          if (typeof errorNotification === 'function') {
            errorNotification(error?.status, error?.detail || error?.responseJSON?.detail);
          }
        });

      modalRevision.classList.add('hidden');
      if (closeRevision) closeRevision.classList.add('hidden');
      modalRevision.querySelectorAll('.show-modal-true, .show-modal-false').forEach(el => {
        el.classList.add('hidden');
      });
    });
  }

  // Gestion du téléchargement de fichiers avec mini-menu si 2 fichiers
  root.addEventListener('click', function (e) {
    const downloadBtn = e.target.closest('.download-file');
    if (!downloadBtn) return;

    e.preventDefault();
    const translatedFile = downloadBtn.dataset.translatedFile;
    const reviewedFile = downloadBtn.dataset.reviewedFile;

    if (reviewedFile && translatedFile) {
      // Crée/affiche un petit menu pour choisir
      const existing = document.querySelector('.download-tooltip');
      if (existing) existing.remove();

      const tooltip = document.createElement('div');
      tooltip.className = 'download-tooltip';
      const list = document.createElement('div');
      list.className = 'download-tooltip-list';
      
      const optTranslated = document.createElement('button');
      optTranslated.type = 'button';
      optTranslated.className = 'download-tooltip-option';
      optTranslated.textContent = window.language_code === 'fr' ? 'Traduit' : 'Translated';
      
      const optReviewed = document.createElement('button');
      optReviewed.type = 'button';
      optReviewed.className = 'download-tooltip-option';
      optReviewed.textContent = window.language_code === 'fr' ? 'Post-édité' : 'Post-edited';
      
      list.appendChild(optTranslated);
      list.appendChild(optReviewed);
      tooltip.appendChild(list);
      document.body.appendChild(tooltip);

      // Calculer la position: sous et aligné sur le bouton
      const rect = downloadBtn.getBoundingClientRect();
      const top = rect.bottom + window.scrollY + 6;
      const left = rect.left + window.scrollX - (tooltip.offsetWidth - rect.width);
      tooltip.style.top = top + 'px';
      tooltip.style.left = left + 'px';

      // Gestion clics
      optTranslated.addEventListener('click', function () {
        window.location.href = translatedFile;
        tooltip.remove();
      });
      optReviewed.addEventListener('click', function () {
        window.location.href = reviewedFile;
        tooltip.remove();
      });

      // Fermer au clic extérieur ou scroll/resize
      setTimeout(function () {
        const closeFn = function (ev) {
          if (!tooltip.contains(ev.target) && !downloadBtn.contains(ev.target)) {
            tooltip.remove();
            document.removeEventListener('click', closeFn);
            window.removeEventListener('scroll', closeFn);
            window.removeEventListener('resize', closeFn);
          }
        };
        document.addEventListener('click', closeFn);
        window.addEventListener('scroll', closeFn);
        window.addEventListener('resize', closeFn);
      }, 0);
      return;
    }

    // Sinon télécharge le seul fichier disponible
    const fileUrl = reviewedFile || translatedFile;
    if (fileUrl) {
      window.location.href = fileUrl;
    }
  });
});

