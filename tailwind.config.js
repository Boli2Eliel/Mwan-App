/** @type {import('tailwindcss').Config} */
const defaultTheme = require('tailwindcss/defaultTheme');
module.exports = {
  content: [
    './**/templates/**/*.html'
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Poppins', ...defaultTheme.fontFamily.sans], // On définit Poppins comme police par défaut
      },
    },
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: [
      {
        kidsapp_theme: { // Le nom de notre thème personnalisé
          "primary": "#3b82f6",     // Un bleu vif et moderne pour les actions principales
          "secondary": "#a855f7",   // Un violet pour les accents secondaires
          "accent": "#10b981",      // Un vert pour les succès et notifications
          "neutral": "#1f2937",     // Un gris très foncé pour la barre latérale
          "base-100": "#ffffff",    // Le fond des cartes et éléments (blanc pur)
          "base-200": "#f3f4f6",    // Le fond général de la page (gris très clair)
          "base-300": "#e5e7eb",    // La couleur des bordures
          "info": "#3abff8",
          "success": "#36d399",
          "warning": "#fbbd23",
          "error": "#f87272",
        },
      },
    ],
  },
}
