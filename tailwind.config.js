/** @type {import('tailwindcss').Config} */
const defaultTheme = require('tailwindcss/defaultTheme');

module.exports = {
  content: [
    './**/templates/**/*.html'
  ],
  theme: {
    extend: {
      // On garde notre police personnalisée
      fontFamily: {
        sans: ['Poppins', ...defaultTheme.fontFamily.sans],
      },
      // ON AJOUTE LA PALETTE DE COULEURS "PRIMARY" ICI
      colors: {
        primary: {
          "50":"#eff6ff","100":"#dbeafe","200":"#bfdbfe","300":"#93c5fd","400":"#60a5fa","500":"#3b82f6","600":"#2563eb","700":"#1d4ed8","800":"#1e40af","900":"#1e3a8a","950":"#172554"
        },
      }
    },
  },
  plugins: [
    require("daisyui")
  ],
  daisyui: {
    themes: [
      {
        kidsapp_theme: { // On conserve votre thème personnalisé pour le reste de l'application
          "primary": "#3b82f6",     
          "secondary": "#a855f7",   
          "accent": "#10b981",      
          "neutral": "#1f2937",     
          "base-100": "#ffffff",    
          "base-200": "#f3f4f6",    
          "base-300": "#e5e7eb",    
          "info": "#3abff8",
          "success": "#36d399",
          "warning": "#fbbd23",
          "error": "#f87272",
        },
      },
    ],
  },
}