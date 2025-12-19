'use strict';

(function (global) {
  var DEFAULT_LANG = 'fr';
  var BADGE_CLASSES = [
    'status-completed',
    'status-error',
    'status-progress',
    'status-attention',
    'status-attention-orange',
    'status-default',
    'status-post-editing'
  ];
  var STATUS_DEFS = [
    { raw: 'Being translated', category: 'in-progress', label: function(){ return 'Processing'; } },
    { raw: 'Sent to post-editing, not accepted yet', category: 'attention-orange', label: function(lang){ return lang === 'en' ? 'Quote sent' : 'Devis envoyé'; } },
    { raw: 'Sent to post-editing, accepted', category: 'attention', label: function(lang){ return lang === 'en' ? 'Quote accepted' : 'Devis accepté'; } },
    { raw: 'Review in progress', category: 'attention-orange', label: function(lang){ return lang === 'en' ? 'Reviewing' : 'Révision'; } },
    { raw: 'Document reviewed', category: 'completed', label: function(lang){ return lang === 'en' ? 'Reviewed' : 'Relu'; } },
    { raw: 'Translated', category: 'completed', label: function(lang){ return lang === 'en' ? 'Translated' : 'Traduit'; } },
    { raw: 'Error', category: 'error', label: function(lang){ return lang === 'en' ? 'Error' : 'Erreur'; } },
  ];
  var STATUS_ALIASES = {
    'being translated': 'Being translated',
    'processing': 'Being translated',
    'sent to post-editing, not accepted yet': 'Sent to post-editing, not accepted yet',
    'sent to post-editing, accepted': 'Sent to post-editing, accepted',
    'translated': 'Translated',
    'document traduit': 'Translated',
    'traduit': 'Translated',
    'error': 'Error',
    'erreur': 'Error',
    'demande de devis envoyee': 'Sent to post-editing, not accepted yet',
    'demande de devis envoyée': 'Sent to post-editing, not accepted yet',
    'devis envoyé': 'Sent to post-editing, not accepted yet',
    'devis envoye': 'Sent to post-editing, not accepted yet',
    'quote sent': 'Sent to post-editing, not accepted yet',
    'demande de devis acceptée': 'Sent to post-editing, accepted',
    'demande de devis acceptee': 'Sent to post-editing, accepted',
    'devis accepté': 'Sent to post-editing, accepted',
    'devis accepte': 'Sent to post-editing, accepted',
    'quote accepted': 'Sent to post-editing, accepted',
    'review in progress': 'Review in progress',
    'révision en cour': 'Review in progress',
    'revision en cour': 'Review in progress',
    'document reviewed': 'Document reviewed',
    'document relu': 'Document reviewed'
  };
  var STATUS_LOOKUP = STATUS_DEFS.reduce(function (acc, def) {
    acc[def.raw] = def;
    return acc;
  }, {});
  var ICON_LOOKUP = {
    'completed': 'ph ph-check-circle',
    'error': 'ph ph-warning-circle',
    'in-progress': 'ph ph-clock-clockwise',
    'attention': 'ph ph-megaphone',
    'attention-orange': 'ph ph-megaphone',
    'post-editing': 'ph ph-info',
    'default': 'ph ph-circle'
  };

  function getLanguage(languageCode) {
    return languageCode || global.language_code || DEFAULT_LANG;
  }

  function toAsciiLower(value) {
    return value
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase();
  }

  function normalizeStatus(rawStatus) {
    var raw = (rawStatus || '').toString().trim();
    if (!raw) return '';
    var lower = raw.toLowerCase();
    var asciiLower = toAsciiLower(raw);
    if (STATUS_ALIASES[lower]) return STATUS_ALIASES[lower];
    if (STATUS_ALIASES[asciiLower]) return STATUS_ALIASES[asciiLower];
    return raw;
  }

  function resolveStatus(rawStatus) {
    var canonical = normalizeStatus(rawStatus);
    return {
      canonical: canonical,
      def: STATUS_LOOKUP[canonical] || null
    };
  }

  function mapStatus(rawStatus, languageCode) {
    return mapStatusWithCategory(rawStatus, languageCode).label;
  }

  function mapStatusWithCategory(rawStatus, languageCode) {
    var lang = getLanguage(languageCode);
    var resolved = resolveStatus(rawStatus);
    if (resolved.def) {
      return {
        label: resolved.def.label(lang),
        category: resolved.def.category,
        canonical: resolved.canonical
      };
    }
    return {
      label: resolved.canonical,
      category: 'default',
      canonical: resolved.canonical
    };
  }

  function updateBadgeVisuals(badge, category) {
    var targetClass = categoryToBadgeClass(category);
    badge.classList.remove.apply(badge.classList, BADGE_CLASSES);
    badge.classList.add(targetClass);
    var iconClass = ICON_LOOKUP[category] || ICON_LOOKUP.default;
    var iconEl = badge.querySelector('i');
    if (!iconEl) {
      iconEl = document.createElement('i');
      badge.insertBefore(iconEl, badge.firstChild);
    }
    iconEl.className = iconClass;
    iconEl.style.fontSize = '16px';
    iconEl.style.color = 'inherit';
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

  function sanitizeReason(reason) {
    if (typeof reason !== 'string') {
      try {
        return JSON.stringify(reason);
      } catch (err) {
        return '';
      }
    }
    return reason
      .replace(/error\s*text\s*:?/i, '')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function parseErrorReasons(raw) {
    if (!raw) return [];
    var buffered = [];
    var payload = raw;

    try {
      var parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        buffered = parsed;
      } else if (parsed) {
        buffered = [parsed];
      }
    } catch (err) {
      buffered = String(payload).split(/\r?\n/);
    }

    return buffered
      .map(sanitizeReason)
      .filter(function (item) { return item && item.length; });
  }

  function destroyStatusTooltip(badge) {
    if (!badge) return;
    badge.classList.remove('has-tooltip');
    badge.removeAttribute('data-error-tooltip');
    var tooltip = badge.querySelector('.status-tooltip');
    if (tooltip) {
      tooltip.remove();
    }
  }

  function renderStatusTooltip(badge, reasons, languageCode) {
    if (!badge || !reasons.length) return;
    var tooltip = badge.querySelector('.status-tooltip');
    if (!tooltip) {
      tooltip = document.createElement('div');
      tooltip.className = 'status-tooltip';
      badge.appendChild(tooltip);
    } else {
      tooltip.innerHTML = '';
    }

    var heading = document.createElement('div');
    heading.className = 'status-tooltip-title';
    heading.textContent = languageCode === 'en' ? 'Error details' : 'Détails de l\u2019erreur';
    tooltip.appendChild(heading);

    var body = document.createElement('div');
    body.className = 'status-tooltip-body';
    reasons.forEach(function (reason) {
      var line = document.createElement('div');
      line.className = 'status-tooltip-line';
      line.textContent = reason;
      body.appendChild(line);
    });
    tooltip.appendChild(body);

    badge.classList.add('has-tooltip');
    badge.setAttribute('data-error-tooltip', 'true');
  }

  function applyStatusMapping(root) {
    var scope = root || document;
    var lang = getLanguage();
    var nodes = scope.querySelectorAll('.status-badge .status');

    nodes.forEach(function (el) {
      var raw = el.getAttribute('data-status') || el.textContent;
      var mapped = mapStatusWithCategory(raw, lang);
      el.textContent = mapped.label;
      el.setAttribute('data-status', mapped.canonical);

      var badge = el.closest('.status-badge');
      if (!badge) return;

      updateBadgeVisuals(badge, mapped.category);

      if (mapped.category === 'error') {
        var reasons = parseErrorReasons(el.getAttribute('data-error-reason'));
        if (reasons.length) {
          renderStatusTooltip(badge, reasons, lang);
          return;
        }
      }
      destroyStatusTooltip(badge);
    });
  }

  global.mapStatus = mapStatus;
  global.mapStatusWithCategory = mapStatusWithCategory;
  global.applyStatusMapping = applyStatusMapping;
})(window);


