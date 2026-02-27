# Race Database — Percorsi Ciclistici

Archivio professionale di percorsi ciclistici. Costruito con [Astro](https://astro.build), deployato con Netlify Drop.

---

## Setup iniziale (una volta sola)

### 1. Prerequisiti
- [Node.js](https://nodejs.org) v18+
- Account [Netlify](https://netlify.com) gratuito

### 2. Installa e testa in locale
```bash
npm install
npm run dev
# → http://localhost:4321
```

---

## Come aggiungere una gara

### 1. Genera il report HTML
```bash
python genera_report.py mia_gara.gpx
# inserisci il titolo nel dialog → genera es. Stelvio_2024.html
```

### 2. Copia l'HTML in `/public/gare/`
```
public/gare/stelvio-2024.html
```
⚠️ Usa slug kebab-case: minuscolo, trattini, niente spazi.

### 3. Crea il JSON in `/gare-sorgenti/`
Crea `gare-sorgenti/stelvio-2024.json`:
```json
{
  "slug": "stelvio-2024",
  "titolo": "Stelvio Bike Day 2024",
  "data": "2024-08-10",
  "genere": "Maschile",
  "categoria": "Elite",
  "disciplina": "Strada",
  "distanza_km": 87.5,
  "dislivello_m": 2760,
  "luogo": "Alto Adige, IT",
  "tempo": "5h14m"
}
```

### 4. Builda
```bash
npm run build
```

### 5. Deploya su Netlify
1. Vai su [app.netlify.com/drop](https://app.netlify.com/drop)
2. Trascina la cartella `dist/` nel browser
3. Online in 30 secondi

Per aggiornare il sito: ripeti dal punto 4.

---

## Valori validi per i campi JSON

| Campo | Valori |
|-------|--------|
| `genere` | `"Maschile"` · `"Femminile"` |
| `categoria` | `"Elite"` · `"U23"` · `"Junior"` · `"Allievi"` |
| `disciplina` | `"Strada"` · `"Criterium"` · `"Cronometro"` |

---

## Struttura del progetto

```
gare-archivio/
├── gare-sorgenti/       ← un JSON per gara (metadati)
├── public/gare/         ← un HTML per gara (report)
├── src/
│   ├── pages/
│   │   ├── index.astro
│   │   └── gare/[slug].astro
│   ├── components/GaraCard.astro
│   ├── layouts/Base.astro
│   └── lib/gare.js
└── package.json
```
