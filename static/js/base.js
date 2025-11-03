// Global base.js - comportements transverses (placeholder)
(function () {
  // Namespace simple pour éviter la pollution globale
  window.AppBase = window.AppBase || {};

  AppBase.dispatchEvent = function (name, detail) {
    document.dispatchEvent(new CustomEvent(name, { detail }));
  };
})();
