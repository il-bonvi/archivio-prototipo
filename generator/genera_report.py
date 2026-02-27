#!/usr/bin/env python3
"""
genera_report.py — Genera report HTML da GPX e lo aggiunge all'archivio Astro.

Uso:
    python genera_report.py                        # dialog grafico completo
    python genera_report.py percorso.gpx           # salta selezione file
    python genera_report.py percorso.gpx --no-build  # salta npm run build

Lo script:
  1. Chiede di selezionare il file GPX
  2. Legge distanza e dislivello direttamente dal GPX
  3. Mostra form con tutti i metadati precompilati
  4. Genera HTML → public/gare/<slug>.html
  5. Crea JSON → gare-sorgenti/<slug>.json
  6. Lancia npm run build
"""

import sys
import re
import json
import math
import base64
import argparse
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import date

# ── CONFIGURAZIONE ───────────────────────────────────────────────────────────
# Cartella dell'archivio Astro. Torna indietro di una cartella da /generator
ARCHIVIO_DIR = Path(__file__).parent.parent
# ─────────────────────────────────────────────────────────────────────────────

AUTOLOAD_TEMPLATE = """<!--GPXREPORT_START-->
<script>
(function(){{
    var GPX_B64 = "{gpx_b64}";
    var GPX_NAME = "{gpx_name}";
    var gpxText = decodeURIComponent(escape(atob(GPX_B64)));
    window._gpxRawText = gpxText;
    window._gpxFileName = GPX_NAME;
    if (typeof parseGPX === 'function') parseGPX(gpxText);
}})();
</script>
<!--GPXREPORT_END-->"""

TITLE_HTML = """<div id="report-title-bar" style="
    text-align:center;
    padding: 18px 24px 10px;
    font-family: 'Inter', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: #111827;
    letter-spacing: -0.02em;
    border-bottom: 2px solid #fc5200;
    margin-bottom: 0;
">{title}</div>
"""

CATEGORIE  = ["Elite", "U23", "Junior", "Allievi"]
GENERI     = ["Maschile", "Femminile"]
DISCIPLINE = ["Strada", "Criterium", "Cronometro"]


# ── PARSING GPX ───────────────────────────────────────────────────────────────

def parse_gpx(gpx_path: Path) -> dict:
    """Estrae distanza (km) e dislivello positivo (m) dal file GPX."""
    try:
        tree = ET.parse(gpx_path)
        root = tree.getroot()
        # Namespace GPX 1.1 e 1.0
        ns = ''
        if root.tag.startswith('{'):
            ns = root.tag.split('}')[0] + '}'

        # Raccogli tutti i punti (trkpt o wpt)
        points = root.findall(f'.//{ns}trkpt')
        if not points:
            points = root.findall(f'.//{ns}rtept')

        if not points:
            return {'distanza_km': None, 'dislivello_m': None}

        coords = []
        for pt in points:
            try:
                lat = float(pt.get('lat'))
                lon = float(pt.get('lon'))
                ele_el = pt.find(f'{ns}ele')
                ele = float(ele_el.text) if ele_el is not None else None
                coords.append((lat, lon, ele))
            except (TypeError, ValueError):
                continue

        if not coords:
            return {'distanza_km': None, 'dislivello_m': None}

        # Distanza con formula Haversine
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371000
            φ1, φ2 = math.radians(lat1), math.radians(lat2)
            dφ = math.radians(lat2 - lat1)
            dλ = math.radians(lon2 - lon1)
            a = math.sin(dφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(dλ/2)**2
            return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        dist_m = sum(
            haversine(coords[i][0], coords[i][1], coords[i+1][0], coords[i+1][1])
            for i in range(len(coords)-1)
        )

        # Dislivello positivo (soglia 2m per filtrare rumore GPS)
        d_plus = 0.0
        eles = [c[2] for c in coords if c[2] is not None]
        for i in range(1, len(eles)):
            diff = eles[i] - eles[i-1]
            if diff > 2.0:
                d_plus += diff

        return {
            'distanza_km': round(dist_m / 1000, 2),
            'dislivello_m': round(d_plus),
        }

    except Exception as e:
        print(f"  Avviso: impossibile leggere dati dal GPX ({e})")
        return {'distanza_km': None, 'dislivello_m': None}


# ── SLUG ─────────────────────────────────────────────────────────────────────

def slugify(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-')


# ── DIALOG METADATI ───────────────────────────────────────────────────────────

def ask_metadata(default_title: str, gpx_data: dict) -> dict | None:
    import tkinter as tk
    from tkinter import ttk, messagebox

    result = {}

    root = tk.Tk()
    root.title("Aggiungi al database gare")
    root.resizable(False, False)
    root.attributes('-topmost', True)

    BG = "#f5f2ed"; FG = "#0f0f0f"; ACCENT = "#d4401a"
    FONT_LABEL = ("Helvetica", 10, "bold")
    FONT_ENTRY = ("Helvetica", 11)

    root.configure(bg=BG)

    tk.Frame(root, bg=ACCENT, height=4).pack(fill="x")
    tk.Label(root, text="Aggiungi percorso al database",
             font=("Helvetica", 13, "bold"), bg=BG, fg=FG, pady=12).pack()

    frame = tk.Frame(root, bg=BG, padx=24, pady=4)
    frame.pack(fill="both")
    frame.grid_columnconfigure(0, weight=1)

    def lbl(text, row_n):
        tk.Label(frame, text=text, font=FONT_LABEL, bg=BG, fg="#7a746b",
                 anchor="w").grid(row=row_n*2, column=0, columnspan=2,
                                  sticky="w", pady=(10,1))

    def ent(row_n, val=''):
        e = tk.Entry(frame, font=FONT_ENTRY, bg="white", fg=FG, relief="solid", bd=1)
        e.grid(row=row_n*2+1, column=0, columnspan=2, sticky="ew")
        if val: e.insert(0, str(val))
        return e

    def cmb(row_n, values):
        c = ttk.Combobox(frame, values=values, state="readonly", font=FONT_ENTRY)
        c.grid(row=row_n*2+1, column=0, columnspan=2, sticky="ew")
        c.current(0)
        return c

    lbl("Nome gara *", 0);      e_titolo    = ent(0, default_title)
    lbl("Slug URL *", 1);       e_slug      = ent(1)
    lbl("Data (AAAA-MM-GG) *",2);e_data     = ent(2, date.today().isoformat())
    lbl("Genere *", 3);         cb_genere   = cmb(3, GENERI)
    lbl("Categoria *", 4);      cb_cat      = cmb(4, CATEGORIE)
    lbl("Disciplina *", 5);     cb_disc     = cmb(5, DISCIPLINE)

    # Auto-slug
    slug_manual = tk.BooleanVar(value=False)
    def update_slug(*_):
        if not slug_manual.get():
            e_slug.delete(0, tk.END)
            e_slug.insert(0, slugify(e_titolo.get()))
    e_titolo.bind("<KeyRelease>", update_slug)
    e_slug.bind("<KeyPress>", lambda e: slug_manual.set(True))
    update_slug()

    # Seconda sezione: stats con giri
    frame2 = tk.Frame(root, bg=BG, padx=24, pady=4)
    frame2.pack(fill="both")
    frame2.grid_columnconfigure(0, weight=1)
    frame2.grid_columnconfigure(1, weight=1)
    frame2.grid_columnconfigure(2, weight=1)

    def lbl2(text, row_n, col, colspan=1):
        tk.Label(frame2, text=text, font=FONT_LABEL, bg=BG, fg="#7a746b",
                 anchor="w").grid(row=row_n*2, column=col, columnspan=colspan,
                                  sticky="w", padx=(0,8), pady=(10,1))

    def ent2(row_n, col, val='', colspan=1):
        e = tk.Entry(frame2, font=FONT_ENTRY, bg="white", fg=FG, relief="solid", bd=1)
        e.grid(row=row_n*2+1, column=col, columnspan=colspan, sticky="ew", padx=(0,8))
        if val != '': e.insert(0, str(val))
        return e

    # GPX raw values
    raw_km = gpx_data.get('distanza_km')
    raw_d  = gpx_data.get('dislivello_m')

    lbl2("Giri del circuito", 0, 0)
    giri_var = tk.IntVar(value=1)
    spin_giri = tk.Spinbox(frame2, from_=1, to=50, textvariable=giri_var,
                           font=FONT_ENTRY, bg="white", fg=FG, relief="solid", bd=1, width=5)
    spin_giri.grid(row=1, column=0, sticky="w", padx=(0,8))

    lbl2("Distanza (km)", 0, 1)
    e_km = ent2(0, 1, val=raw_km if raw_km else '')

    lbl2("Dislivello (m D+)", 0, 2)
    e_dp = ent2(0, 2, val=raw_d if raw_d else '')

    # Aggiorna km e D+ al cambio giri
    def update_stats(*_):
        try:
            g = int(giri_var.get())
        except:
            return
        if raw_km is not None:
            e_km.delete(0, tk.END)
            e_km.insert(0, str(round(raw_km * g, 2)))
        if raw_d is not None:
            e_dp.delete(0, tk.END)
            e_dp.insert(0, str(round(raw_d * g)))

    giri_var.trace_add('write', update_stats)

    lbl2("Luogo / Regione", 1, 0, colspan=2)
    e_luogo = ent2(1, 0, colspan=2)

    # Note
    tk.Label(frame2, text="Note (opzionali)", font=FONT_LABEL, bg=BG, fg="#7a746b",
             anchor="w").grid(row=4, column=0, columnspan=3, sticky="w", pady=(10,1))
    e_note = tk.Text(frame2, font=FONT_ENTRY, bg="white", fg=FG,
                     relief="solid", bd=1, height=3)
    e_note.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(0,4))

    # Bottoni
    btn_frame = tk.Frame(root, bg=BG, padx=24, pady=16)
    btn_frame.pack(fill="x")
    cancelled = tk.BooleanVar(value=False)

    def on_ok():
        errors = []
        if not e_titolo.get().strip(): errors.append("Nome gara obbligatorio")
        if not e_slug.get().strip():   errors.append("Slug obbligatorio")
        if not e_data.get().strip():   errors.append("Data obbligatoria")
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', e_data.get().strip()):
            errors.append("Data nel formato AAAA-MM-GG")
        if errors:
            messagebox.showerror("Errore", "\n".join(errors), parent=root)
            return

        def num_or_none(s):
            try: return float(s.strip()) if s.strip() else None
            except: return None

        result.update({
            "slug":         slugify(e_slug.get().strip()),
            "titolo":       e_titolo.get().strip(),
            "data":         e_data.get().strip(),
            "genere":       cb_genere.get(),
            "categoria":    cb_cat.get(),
            "disciplina":   cb_disc.get(),
            "distanza_km":  num_or_none(e_km.get()),
            "dislivello_m": num_or_none(e_dp.get()),
            "luogo":        e_luogo.get().strip() or None,
            "note":         e_note.get("1.0", tk.END).strip() or None,
        })
        root.destroy()

    def on_cancel():
        cancelled.set(True)
        root.destroy()

    tk.Button(btn_frame, text="Annulla", font=("Helvetica", 11),
              bg="#ede9e2", fg="#7a746b", relief="flat", bd=0,
              padx=16, pady=8, cursor="hand2",
              command=on_cancel).pack(side="right", padx=(8,0))

    tk.Button(btn_frame, text="Aggiungi al database →", font=("Helvetica", 11, "bold"),
              bg=ACCENT, fg="white", relief="flat", bd=0,
              padx=16, pady=8, cursor="hand2",
              command=on_ok).pack(side="right")

    root.bind("<Return>", lambda e: on_ok())
    root.bind("<Escape>", lambda e: on_cancel())
    root.mainloop()

    if cancelled.get() or not result:
        return None
    return result


# ── TEMPLATE ─────────────────────────────────────────────────────────────────

def find_template(template_arg):
    if template_arg:
        p = Path(template_arg)
        if p.exists(): return p
        sys.exit(f"Errore: template non trovato: {template_arg}")
    for c in [ARCHIVIO_DIR / 'index.html',
              Path(__file__).parent / 'index.html',
              Path.cwd() / 'index.html']:
        if c.exists(): return c
    sys.exit("Errore: index.html non trovato. Usa --template /path/index.html")


# ── SELEZIONE FILE GPX ────────────────────────────────────────────────────────

def pick_gpx_file():
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
    path = filedialog.askopenfilename(
        title='Seleziona file GPX',
        filetypes=[('GPX files', '*.gpx'), ('All files', '*.*')]
    )
    root.destroy()
    return Path(path) if path else None


# ── GENERA HTML ───────────────────────────────────────────────────────────────

def generate_html(gpx_path: Path, template_path: Path, title: str) -> str:
    try:
        gpx_text = gpx_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        gpx_text = gpx_path.read_text(encoding='latin-1')

    gpx_b64 = base64.b64encode(gpx_text.encode('utf-8')).decode('ascii')
    gpx_name = gpx_path.name
    html = template_path.read_text(encoding='utf-8')

    html = re.sub(r'<!--GPXREPORT_START-->.*?<!--GPXREPORT_END-->', '', html, flags=re.DOTALL)
    html = re.sub(r'<title>[^<]*</title>', f'<title>{title}</title>', html)
    html = re.sub(r'(#data-content\s*\{[^}]*)display\s*:\s*none', r'\1display: block', html)
    html = re.sub(r'(<div id="upload-section")([^>]*)>', r'\1\2 style="display:none!important">', html)
    html = re.sub(r'<div id="reset-bar".*?</div>', '', html, flags=re.DOTALL)
    html = html.replace("if (rb) rb.style.display = 'flex';", "// report: reset-bar rimosso")
    html = html.replace("document.getElementById('reset-bar').style.display = 'none';", "// report: reset-bar rimosso")
    html = re.sub(r'(<p class="sv-hint")', r'\1 style="display:none"', html)
    html = html.replace('<div class="container">', '<div class="container">\n' + TITLE_HTML.format(title=title), 1)
    autoload = AUTOLOAD_TEMPLATE.format(gpx_b64=gpx_b64, gpx_name=gpx_name.replace('"', '\\"'))
    html = html.replace('</body>', autoload + '\n</body>', 1)
    return html


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('gpx', nargs='?', default=None)
    parser.add_argument('--template', default=None)
    parser.add_argument('--no-build', action='store_true', dest='no_build')
    args = parser.parse_args()

    # 1. Seleziona GPX
    if args.gpx:
        gpx_path = Path(args.gpx)
        if not gpx_path.exists():
            sys.exit(f"Errore: file GPX non trovato: {args.gpx}")
    else:
        gpx_path = pick_gpx_file()
        if not gpx_path:
            sys.exit("Nessun file selezionato.")

    # 2. Leggi dati dal GPX
    print(f"⟳ Lettura GPX: {gpx_path.name}...")
    gpx_data = parse_gpx(gpx_path)
    if gpx_data['distanza_km']:
        print(f"  Distanza rilevata: {gpx_data['distanza_km']} km")
    if gpx_data['dislivello_m']:
        print(f"  Dislivello rilevato: +{gpx_data['dislivello_m']} m")

    # 3. Dialog metadati
    meta = ask_metadata(gpx_path.stem, gpx_data)
    if meta is None:
        print("Annullato.")
        sys.exit(0)

    slug  = meta["slug"]
    title = meta["titolo"]

    # 4. Cartelle destinazione
    out_html_dir = ARCHIVIO_DIR / "public" / "gare"
    out_json_dir = ARCHIVIO_DIR / "gare-sorgenti"
    out_html_dir.mkdir(parents=True, exist_ok=True)
    out_json_dir.mkdir(parents=True, exist_ok=True)

    html_path = out_html_dir / f"{slug}.html"
    json_path = out_json_dir / f"{slug}.json"

    # Avvisa se esiste già
    if html_path.exists() or json_path.exists():
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
        ok = messagebox.askyesno("File esistente",
            f"Esiste già una gara con slug '{slug}'.\nVuoi sovrascriverla?")
        root.destroy()
        if not ok:
            print("Operazione annullata.")
            sys.exit(0)

    # 5. Genera e salva HTML
    template_path = find_template(args.template)
    html_content  = generate_html(gpx_path, template_path, title)
    html_path.write_text(html_content, encoding='utf-8')
    print(f"✓ HTML  → {html_path}")

    # 6. Salva JSON (rimuovi None)
    meta_clean = {k: v for k, v in meta.items() if v is not None}
    json_path.write_text(json.dumps(meta_clean, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"✓ JSON  → {json_path}")

    # 7. Build
    if not args.no_build:
        print("\n⟳ npm run build...")
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=ARCHIVIO_DIR,
            shell=(sys.platform == "win32")
        )
        if result.returncode == 0:
            print("\n✓ Build completata!")
            print("  → Trascina la cartella  dist/  su  https://app.netlify.com/drop")
        else:
            print("\n✗ Build fallita.")
            sys.exit(1)
    else:
        print("\nBuild saltata. Lancia: npm run build")

    # 8. Popup finale
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
        msg = f'"{title}" aggiunto al database!\n\n'
        if not args.no_build:
            msg += "Build completata.\nOra trascina dist/ su:\nhttps://app.netlify.com/drop"
        else:
            msg += f"Slug: {slug}\nLancia npm run build quando sei pronto."
        messagebox.showinfo("Database aggiornato!", msg)
        root.destroy()
    except Exception:
        pass


if __name__ == '__main__':
    main()