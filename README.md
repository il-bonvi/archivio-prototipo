# Race Database — Percorsi Ciclistici

Archivio professionale di percorsi ciclistici. Costruito con [Astro](https://astro.build), deployato su GitHub Pages.

🔗 **Live:** https://il-bonvi.github.io/archivio-prototipo

---

## Setup iniziale (una volta sola)

### 1. Prerequisiti
- [Node.js](https://nodejs.org) v18+
- Account GitHub con la repo `archivio-prototipo`

### 2. Installa e testa in locale
```bash
npm install
npm run dev
# → http://localhost:4321
```

### 3. Abilita GitHub Pages
1. Vai su **Settings → Pages** della repo
2. Sotto *Source* seleziona **GitHub Actions**
3. Salva

Da questo momento, ogni push su `main` triggera il deploy automatico.

---

## Come aggiungere una gara

### 1. Genera il report HTML
```bash
python generator/genera_report.py mia_gara.gpx
# inserisci il titolo nel dialog → genera es. stelvio-2024.html
```

Lo script in automatico:
- genera `public/gare/<slug>.html`
- crea `gare-sorgenti/<slug>.json`
- esegue `npm run build`

### 2. Committa e pusha
```bash
git add .
git commit -m "Aggiungi gara: Stelvio 2024"
git push
```

GitHub Actions builda e deploya in automatico. Il sito è aggiornato in ~1 minuto.

---

## Struttura del progetto

```
archivio-prototipo/
├── .github/
│   └── workflows/
│       └── deploy.yml           ← GitHub Actions (build + deploy)
├── gare-sorgenti/               ← JSON source per ogni gara (metadati + GPX)
├── public/
│   ├── gara.html                ← Unico visualizzatore web (tutte le gare)
│   └── gare-sorgenti/           ← JSON serviti al browser da gara.html
├── generator/
│   ├── index.html               ← Template base per gara.html
│   └── genera_report.py         ← Script che aggiunge nuove gare da GPX
├── src/
│   ├── pages/
│   │   ├── index.astro          ← Homepage con lista gare
│   │   └── gare/[slug].astro    ← Pagina race (top-bar Astro + iframe gara.html)
│   ├── components/GaraCard.astro← Card per lista homepage
│   ├── layouts/Base.astro
│   └── lib/gare.js
├── astro.config.mjs
├── package.json
└── MIGRATION_COMPLETE.md        ← Descrizione architettura
```

**Come funziona:**
- `/gare/[slug]/` → pagina Astro che mostra top-bar + iframe su `/gara.html?gara=slug`
- `/gara.html` → viewer unico (carica race in JSON da `?gara=` parameter)
- Nuovo race → `python genera_report.py` crea JSON in entrambe `gare-sorgenti/` e `public/gare-sorgenti/`

---

## Valori validi per i campi JSON

| Campo | Valori |
|-------|--------|
| `genere` | `"Maschile"` · `"Femminile"` |
| `categoria` | `"Elite"` · `"U23"` · `"Junior"` · `"Allievi"` |
| `disciplina` | `"Strada"` · `"Criterium"` · `"Cronometro"` |

---

## Sviluppo locale

```bash
npm run dev        # avvia dev server → http://localhost:4321
npm run build      # build completa (genera HTML + Astro)
npm run preview    # anteprima della build
```

> **Nota:** in locale i path funzionano senza il prefisso `/archivio-prototipo` perché
> `BASE_URL` è `/` in dev. Il prefisso viene applicato solo nella build di produzione.
