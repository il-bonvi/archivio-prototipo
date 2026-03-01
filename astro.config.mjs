import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://il-bonvi.github.io',
  // Commenta base durante sviluppo, riabilita per build GitHub Pages
  // base: '/archivio-prototipo',

  build: {
    assets: 'assets'
  }
});
