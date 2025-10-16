'use strict';

(function (global) {
  var STATUS_DEFS = [
    { raw: 'Being translated', category: 'in-progress', label: function(){ return 'Processing'; } },
    { raw: 'Processing', category: 'in-progress', label: function(){ return 'Processing'; } },
    { raw: 'Processing...', category: 'in-progress', label: function(){ return 'Processing'; } },
    { raw: 'In progress', category: 'in-progress', label: function(lang){ return lang === 'en' ? 'In progress' : 'En cours'; } },

    { raw: 'Sent to post-editing, not accepted yet', category: 'attention-orange', label: function(lang){ return lang === 'en' ? 'Request for quote sent' : 'Demande de devis envoyée'; } },
    { raw: 'Sent to post-editing, accepted', category: 'attention', label: function(lang){ return lang === 'en' ? 'Request for quote accepted' : 'Demande de devis acceptée'; } },
    { raw: 'Post-edited file uploaded', category: 'post-editing', label: function(lang){ return lang === 'en' ? 'Proofread document uploaded' : 'Document relu importé'; } },

    { raw: 'Translated', category: 'completed', label: function(lang){ return lang === 'en' ? 'Translated' : 'Document traduit'; } },
    { raw: 'Error', category: 'error', label: function(lang){ return lang === 'en' ? 'Error' : 'Erreur'; } },
  ];

  function normalize(rawStatus) {
    return (rawStatus || '').trim();
  }

  function findStatusDef(rawStatus) {
    var norm = normalize(rawStatus);
    for (var i = 0; i < STATUS_DEFS.length; i++) {
      if (STATUS_DEFS[i].raw === norm) return STATUS_DEFS[i];
    }
    return null;
  }

  function mapStatus(rawStatus, languageCode) {
    var lang = languageCode || (global.language_code || 'fr');
    var def = findStatusDef(rawStatus);
    if (def) return def.label(lang);
    return normalize(rawStatus);
  }

  function mapStatusWithCategory(rawStatus, languageCode) {
    var lang = languageCode || (global.language_code || 'fr');
    var def = findStatusDef(rawStatus);
    if (def) return { label: def.label(lang), category: def.category };
    return { label: normalize(rawStatus), category: 'default' };
  }

  function categoryToBadgeClass(category) {
    switch (category) {
      case 'completed': return 'status-completed';
      case 'error': return 'status-error';
      case 'in-progress': return 'status-progress';
      case 'attention': return 'status-attention';
      case 'attention-orange': return 'status-attention-orange';
      case 'post-editing': return 'status-post-editing';
      default: return 'status-default';
    }
  }

  function categoryToIcon(category) {
    switch (category) {
      case 'completed': return { iconClass: 'ph ph-check-circle' };
      case 'error': return { iconClass: 'ph ph-warning-circle' };
      case 'in-progress': return { iconClass: 'ph ph-clock-clockwise' };
      case 'attention': return { iconClass: 'ph ph-megaphone' };
      case 'attention-orange': return { iconClass: 'ph ph-megaphone' };
      case 'post-editing': return { iconClass: 'ph ph-info' };
      default: return { iconClass: 'ph ph-circle' };
    }
  }

  function applyStatusMapping(root) {
    var scope = root || document;
    var lang = global.language_code || 'fr';
    var nodes = scope.querySelectorAll('td .status');
    nodes.forEach(function (el) {
      var mapped = mapStatusWithCategory(el.textContent, lang);
      el.textContent = mapped.label;
      var badge = el.closest('.status-badge');
      if (badge) {
        badge.classList.remove('status-completed','status-error','status-progress','status-attention','status-attention-orange','status-default','status-post-editing');
        badge.classList.add(categoryToBadgeClass(mapped.category));
        var iconCfg = categoryToIcon(mapped.category);
        var iconEl = badge.querySelector('i');
        if (!iconEl) {
          iconEl = document.createElement('i');
          badge.insertBefore(iconEl, badge.firstChild);
        }
        iconEl.className = iconCfg.iconClass;
        iconEl.style.fontSize = '16px';
        iconEl.style.color = 'inherit';
      }
    });
  }

  global.mapStatus = mapStatus;
  global.mapStatusWithCategory = mapStatusWithCategory;
  global.applyStatusMapping = applyStatusMapping;
})(window);


