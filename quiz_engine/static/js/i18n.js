const qeI18n = (() => {
  const translations = window.QE_TRANSLATIONS || {};
  const interpolate = (text, vars = {}) =>
    text.replace(/\{(\w+)\}/g, (match, key) =>
      Object.prototype.hasOwnProperty.call(vars, key) ? String(vars[key]) : match
    );

  const t = (key, vars) => {
    const text = translations[key] || key;
    return interpolate(text, vars);
  };

  return { t };
})();

window.qeI18n = qeI18n;
