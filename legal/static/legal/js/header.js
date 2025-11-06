/**
 * Header JavaScript
 * Gère le changement de langue via le sélecteur dans le header
 */
document.addEventListener('DOMContentLoaded', function () {
  const langSwitchers = document.querySelectorAll('.header-lang-link.en, .header-lang-link.fr');
  
  if (!langSwitchers || langSwitchers.length === 0) {
    return;
  }

  langSwitchers.forEach(function (switcher) {
    switcher.addEventListener('click', function (e) {
      e.preventDefault();
      
      const lang = this.classList.contains('en') ? 'en' : 'fr';
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = '/i18n/setlang/';

      // Ajouter le token CSRF
      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
      if (csrfToken) {
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken.value;
        form.appendChild(csrfInput);
      }

      // Ajouter la langue sélectionnée
      const langInput = document.createElement('input');
      langInput.type = 'hidden';
      langInput.name = 'language';
      langInput.value = lang;
      form.appendChild(langInput);

      // Soumettre le formulaire
      document.body.appendChild(form);
      form.submit();
    });
  });
});
