// Bootstrap config à partir du DOM et exposition globale (compat historique)
(function () {
  var el = document.getElementById('translate-config');
  if (!el) return;
  window.get_domains = el.dataset.getDomains;
  window.translate = el.dataset.translate;
  window.single_project = el.dataset.singleProject;
  window.detect_language = el.dataset.detectLanguage;
  window.detect_text_language = el.dataset.detectTextLanguage;
  window.domain_groups = el.dataset.domainGroups;
  window.get_default_glossary = el.dataset.getDefaultGlossary;
  window.api_list_glossaries = el.dataset.apiListGlossaries;
  window.expert_revision_file_url = el.dataset.expertRevisionFileUrl;
  window.add_glossary = el.dataset.addGlossary;
  window.language_code = el.dataset.languageCode;
  try { window.languages = JSON.parse(el.dataset.languages || '[]'); } catch (e) { window.languages = []; }
  window.access_to_default_glossaries = (el.dataset.accessToDefaultGlossaries === 'true');
})();

$(document).ready(function () {


    // ------------- TABS -------------


    function showTab(tabId) {
        $('.translate-tab-content').addClass('translate-tab-content-hidden');
        $(`#${tabId}-content`).removeClass('translate-tab-content-hidden');
        $('button.translate-tab').removeClass('translate-tab-active');
        $('#expert-revision').addClass('hidden');
        $(`#${tabId}`).addClass('translate-tab-active');
    }

    function setHash(tab) {
        window.location.hash = tab;
    }

    let initialTab = 'text-translate';

    if (window.location.hash) {
        const hash = window.location.hash.substring(1);

        if (hash === 'document-translate') {
            initialTab = 'document-translate';
        } else if (hash === 'writing') {
            initialTab = 'writing';
        }
    }

    showTab(initialTab);
    setHash(initialTab);

    $('#text-translate').click(function () {
        showTab('text-translate');
        setHash('text-translate');
    });

    $('#document-translate').click(function () {
        showTab('document-translate');
        setHash('document-translate');
    });

    $('#writing').click(function () {
        showTab('writing');
        setHash('writing');
    });
});

