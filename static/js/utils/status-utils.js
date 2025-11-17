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

  var STATUS_ALIASES = {
    'being translated': 'Being translated',
    'processing': 'Processing',
    'processing...': 'Processing...',
    'processing…': 'Processing...',
    'in progress': 'In progress',
    'en cours': 'In progress',
    'sent to post-editing, not accepted yet': 'Sent to post-editing, not accepted yet',
    'sent to post-editing, accepted': 'Sent to post-editing, accepted',
    'post-edited file uploaded': 'Post-edited file uploaded',
    'translated': 'Translated',
    'document traduit': 'Translated',
    'error': 'Error',
    'erreur': 'Error',
    'demande de devis envoyee': 'Sent to post-editing, not accepted yet',
    'demande de devis acceptée': 'Sent to post-editing, accepted',
    'demande de devis acceptee': 'Sent to post-editing, accepted',
    'document relu importé': 'Post-edited file uploaded',
    'document relu importe': 'Post-edited file uploaded',
    'traitement': 'Processing',
    'traitement en cours': 'Processing',
  };

  function toAsciiLower(value) {
    return value
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase();
  }

  function normalize(rawStatus) {
    var raw = (rawStatus || '').toString().trim();
    if (!raw) return '';
    var lower = raw.toLowerCase();
    var asciiLower = toAsciiLower(raw);
    if (STATUS_ALIASES[lower]) return STATUS_ALIASES[lower];
    if (STATUS_ALIASES[asciiLower]) return STATUS_ALIASES[asciiLower];
    return raw;
  }

  function findStatusDef(rawStatus) {
    var norm = normalize(rawStatus);
    for (var i = 0; i < STATUS_DEFS.length; i++) {
      if (STATUS_DEFS[i].raw === norm) return { def: STATUS_DEFS[i], canonical: norm };
    }
    return { def: null, canonical: norm };
  }

  function mapStatus(rawStatus, languageCode) {
    var lang = languageCode || (global.language_code || 'fr');
    var lookup = findStatusDef(rawStatus);
    if (lookup.def) return lookup.def.label(lang);
    return lookup.canonical;
  }

  function mapStatusWithCategory(rawStatus, languageCode) {
    var lang = languageCode || (global.language_code || 'fr');
    var lookup = findStatusDef(rawStatus);
    if (lookup.def) {
      return {
        label: lookup.def.label(lang),
        category: lookup.def.category,
        canonical: lookup.canonical
      };
    }
    return { label: lookup.canonical, category: 'default', canonical: lookup.canonical };
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

  function parseErrorReasons(raw) {
    if (!raw) return [];
    var parsed = [];
    try {
      var json = JSON.parse(raw);
      if (Array.isArray(json)) {
        parsed = json;
      } else if (json && typeof json === 'string') {
        parsed = [json];
      }
    } catch (e) {
      parsed = String(raw).split(/\r?\n/);
    }
    return parsed
      .map(function (item) {
        if (typeof item !== 'string') {
          try {
            return JSON.stringify(item);
          } catch (err) {
            return '';
          }
        }
        return item;
      })
      .map(function (item) { return item.replace(/\s+/g, ' ').trim(); })
      .filter(function (item) { return item.length > 0; });
  }

  function applyStatusMapping(root) {
    var scope = root || document;
    var lang = global.language_code || 'fr';
    var nodes = scope.querySelectorAll('.status-badge .status');
    nodes.forEach(function (el) {
      var raw = el.getAttribute('data-status') || el.textContent;
      var mapped = mapStatusWithCategory(raw, lang);
      el.textContent = mapped.label;
      el.setAttribute('data-status', mapped.canonical || mapped.label);
      var badge = el.closest('.status-badge');
      if (badge) {
        badge.classList.remove(
          'status-completed',
          'status-error',
          'status-progress',
          'status-attention',
          'status-attention-orange',
          'status-default',
          'status-post-editing'
        );
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

      if (mapped.category === 'error') {
        var reasons = parseErrorReasons(el.getAttribute('data-error-reason'));
        if (reasons.length) {
          var tooltip = reasons.map(function (reason) { return '- ' + reason; }).join('\n');
          badge.setAttribute('title', tooltip);
          badge.setAttribute('data-error-tooltip', tooltip);
          return;
        }
      }
      badge.removeAttribute('title');
      badge.removeAttribute('data-error-tooltip');
    });
  }

  global.mapStatus = mapStatus;
  global.mapStatusWithCategory = mapStatusWithCategory;
  global.applyStatusMapping = applyStatusMapping;
})(window);


