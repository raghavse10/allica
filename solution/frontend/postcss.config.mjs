/**
 * Tailwind CSS v4 ships its PostCSS integration as a dedicated plugin. With
 * Next 15 this is the only configuration step we need — no tailwind.config.js
 * is required because tokens live in `src/styles/globals.css` via @theme.
 */
const config = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};

export default config;
