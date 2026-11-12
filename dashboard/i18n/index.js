/* English-only dashboard localization. */
(function () {
  "use strict";

  var LANG = "en";
  var STORAGE_KEY = "javis.ui_lang"; // Kept for compatibility with existing browser profiles.
  var COOKIE_KEY = "javis_lang";     // Kept for compatibility with server request handling.
  var dictionary = {};
  var ready = false;
  var loading = null;
  var retryCount = 0;
  var retryTimer = 0;

  function humanize(key) {
    return String(key || "").replace(/[._-]+/g, " ").replace(/\s+/g, " ").trim() || "Unavailable";
  }

  function t(key, values) {
    var name = String(key || "");
    var value = dictionary[name];
    if (value == null || value === "") value = humanize(name);
    return String(value).replace(/\{(\w+)\}/g, function (match, name) {
      return values && values[name] != null ? String(values[name]) : match;
    });
  }

  function applyDom(root) {
    (root || document).querySelectorAll("[data-i18n]").forEach(function (el) {
      var key = el.getAttribute("data-i18n");
      el.textContent = t(key);
    });
    [["data-i18n-title", "title"], ["data-i18n-aria", "aria-label"],
      ["data-i18n-ph", "placeholder"], ["data-i18n-empty", "data-empty-hint"]]
      .forEach(function (pair) {
        (root || document).querySelectorAll("[" + pair[0] + "]").forEach(function (el) {
          var key = el.getAttribute(pair[0]);
          el.setAttribute(pair[1], t(key));
        });
      });
  }

  function init() {
    if (loading) return loading;
    try { localStorage.setItem(STORAGE_KEY, LANG); } catch (e) { /* private browsing */ }
    try {
      document.cookie = COOKIE_KEY + "=en; path=/; max-age=31536000; SameSite=Lax";
      document.documentElement.lang = LANG;
    } catch (e) { /* browser policy */ }
    loading = fetch("/static/i18n/en.json", { cache: "no-cache" })
      .then(function (response) {
        if (!response.ok) throw new Error("English interface dictionary unavailable");
        return response.json();
      })
      .then(function (data) {
        dictionary = data && typeof data === "object" ? data : {};
        ready = true;
        retryCount = 0;
        if (retryTimer) clearTimeout(retryTimer);
        retryTimer = 0;
        applyDom();
        window.dispatchEvent(new CustomEvent("javis:i18n", { detail: { lang: LANG } }));
        return LANG;
      })
      .catch(function () {
        // Keep the interface usable during a static-file failure; keyed text is humanized.
        dictionary = {};
        ready = true;
        applyDom();
        window.dispatchEvent(new CustomEvent("javis:i18n", { detail: { lang: LANG } }));
        loading = null;
        retryCount += 1;
        retryTimer = setTimeout(init, Math.min(1000 * Math.pow(2, retryCount - 1), 8000));
        return LANG;
      });
    return loading;
  }

  function setLang() {
    try { localStorage.setItem(STORAGE_KEY, LANG); } catch (e) { /* private browsing */ }
    return init();
  }

  var categoryLabels = {
    "Kh\u00e1c": "Other", "V\u0103n ph\u00f2ng": "Office", "Nh\u1eafn tin": "Messaging",
    "Marketing": "Marketing", "Qu\u1ea3ng c\u00e1o": "Advertising", "Kho \u1ee9ng d\u1ee5ng": "App stores",
    "B\u00e1n h\u00e0ng": "Sales", "L\u1eadp tr\u00ecnh": "Development"
  };
  function catLabel(raw) {
    var value = String(raw == null ? "" : raw).trim();
    return categoryLabels[value] || value;
  }

  window.JavisI18n = {
    t: t,
    catLabel: catLabel,
    init: init,
    setLang: setLang,
    lang: function () { return LANG; },
    ready: function () { return ready; },
    applyDom: applyDom
  };
  window.t = t;
  window.JavisI18n.init();
})();
