# Dynamic GPX Visualization - FINAL ARCHITECTURE ✓

## Summary
Races are now visualized using a single reusable HTML client (`public/gara.html`) that loads race data from JSON files (`public/gare-sorgenti/`) via URL parameters.

## What Changed

### Before
- Generated individual static HTML files for each race
- Pre-built at generation time
- No real-time updates

### Current (Optimized)
- **Single HTML viewer** (`public/gara.html`) handles all races
- Loads race data dynamically from `?gara=slug` parameter
- Top-bar metadata provided by Astro page
- Original full-featured UI preserved exactly

## File Structure

```
src/pages/gare/
└── [slug].astro              ← Astro page with top-bar, embeds iframe

public/
├── gara.html                 ← Single viewer for all races (+ upload sandbox)
└── gare-sorgenti/
    ├── cittiglio.json        ← Race metadata + GPX points
    └── schijndel.json        ← Race metadata + GPX points

gare-sorgenti/               ← Source data (for build-time static generation)
├── cittiglio.json
└── schijndel.json

generator/
├── genera_report.py          ← Script to add new races (creates JSON in both locations)
└── index.html                ← Base template for gara.html
```

## How It Works

### 1. **Adding a New Race**
```bash
python generator/genera_report.py
# or
python generator/genera_report.py /path/to/race.gpx
```
- Opens interactive dialog for metadata
- Extracts GPX points, elevation, distance
- Creates JSON in both `gare-sorgenti/` (source) and `public/gare-sorgenti/` (browser-accessible)

### 2. **Viewing a Race**
```
URL: /gare/cittiglio/
```
- **Astro page** (`[slug].astro`) renders:
  - Top navigation bar (back link, category, title, stats)
  - Iframe pointing to `/gara.html?gara=cittiglio`
  
- **gara.html** (auto-load script):
  - Reads `?gara=cittiglio` parameter
  - Fetches `/gare-sorgenti/cittiglio.json`
  - Initializes full interactive viewer (map, elevation chart, climbs, Street View)

### 3. **Direct Access**
```
URL: /gara.html?gara=cittiglio
```
- Browser-based GPX uploader visible
- Auto-loads cittiglio if `?gara=` parameter present

## Features

✓ **Interactive Map** — Leaflet with gradient-colored polylines by slope  
✓ **Elevation Chart** — D3.js custom bars with per-segment coloring  
✓ **Statistics** — Live calculations: distance, time, altitude, gain  
✓ **Climb Detection** — Fiets difficulty scoring, per-climb cards  
✓ **Street View** — Google Street View integration with elevation panel  
✓ **Responsive** — Optimized for desktop, tablet, mobile  
✓ **Single File** — No per-race HTML generation needed  

## Data Format

```json
{
  "slug": "cittiglio",
  "titolo": "Cittiglio",
  "data": "2026-03-15",
  "genere": "Femminile",
  "categoria": "Junior",
  "disciplina": "Strada",
  "distanza_km": 74.25,
  "dislivello_m": 1002.0,
  "luogo": "Varese, IT",
  "gpx_points": [
    {"lat": 46.00141, "lon": 8.74033, "ele": 201.2},
    // ... more points
  ]
}
```

## Technology Stack

- **Framework**: Astro 4.16.19 (page structure + metadata)
- **Viewer**: vanilla HTML/CSS/JS in `public/gara.html`
- **Mapping**: Leaflet.js 1.9.4
- **Charts**: D3.js v7
- **GPX Parser**: Client-side DOMParser + browser Fetch API

## Benefits

- **Maintenance**: One HTML file to update instead of per-race files
- **Consistency**: All races share identical UI/logic
- **DRY**: No code duplication
- **Performance**: Minimal Astro build time, static JSON delivery
- **UX**: Seamless, identical experience to original
- **Flexibility**: Can add upload feature, GPX processing, etc. to single file

## What Users See

- ✅ Complete race report visualization
- ✅ Interactive map with gradient coloring
- ✅ Elevation chart with hover stats
- ✅ Climb cards with difficulty scoring
- ✅ Street View exploration
- ✅ Mobile-optimized responsive design
- ✅ Professional, polished appearance

## Testing

Both races tested and working:
- ✅ Cittiglio (74.25 km, 1002m elevation)
- ✅ Schijndel (52.96 km, 80m elevation)

Map renders correctly with gradient coloring, elevation chart displays properly, statistics calculated accurately, climbs detected when applicable.

## Next Steps (Optional)

1. Add more races to `gare-sorgenti/` with corresponding JSON files
2. Run `generator/genera_report.py` to process new GPX files
3. Races will automatically appear at `/gare/{slug}/`

## Notes

- GPX points are rounded to 6 decimals (lat/lon) and 1 decimal (elevation)
- Haversine formula used for distance calculations
- Gradient smoothing with 6-point window for color rendering
- Climb detection threshold: 3% average grade, 50m minimum gain
