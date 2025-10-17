document.addEventListener('DOMContentLoaded', function () {
  // Language switcher functionality (works wherever .en/.fr exist)
  var langSwitchers = document.querySelectorAll('.en, .fr');
  if (langSwitchers && langSwitchers.length > 0) {
    langSwitchers.forEach(function (switcher) {
      switcher.addEventListener('click', function () {
        var lang = this.classList.contains('en') ? 'en' : 'fr';

        var form = document.createElement('form');
        form.method = 'POST';
        form.action = '/i18n/setlang/';

        var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfToken) {
          var csrfInput = document.createElement('input');
          csrfInput.type = 'hidden';
          csrfInput.name = 'csrfmiddlewaretoken';
          csrfInput.value = csrfToken.value;
          form.appendChild(csrfInput);
        }

        var langInput = document.createElement('input');
        langInput.type = 'hidden';
        langInput.name = 'language';
        langInput.value = lang;
        form.appendChild(langInput);

        document.body.appendChild(form);
        form.submit();
      });
    });
  }
});


