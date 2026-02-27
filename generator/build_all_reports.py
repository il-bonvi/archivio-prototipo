#!/usr/bin/env python3
"""
build_all_reports.py — Genera tutti gli HTML dalle gare JSON esistenti.
Usa i metadati JSON per riempire i report senza richiedere i GPX originali.
"""

import sys
import json
import base64
import re
from pathlib import Path

# Cartella dell'archivio
ARCHIVIO_DIR = Path(__file__).parent.parent

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

AUTOLOAD_TEMPLATE = """<!--GPXREPORT_START-->
<script>
(function(){{
    console.log('Report stub loaded: {title}');
}})();
</script>
<!--GPXREPORT_END-->"""


def find_template(template_path):
    """Cerca il template index.html"""
    if template_path.exists():
        return template_path
    return None


def generate_report_from_json(gara_json_path, template_html, output_html_path):
    """
    Genera un HTML di report stub da un JSON di gara SOLO se il file non esiste.
    Se il file HTML esiste già, non lo sovrascrivi (potrebbe contenere il GPX).
    """
    try:
        # Se il file HTML esiste già, non sovrascrivere
        if output_html_path.exists():
            return True  # File già presente, skip
        
        # Leggi il JSON
        with open(gara_json_path, 'r', encoding='utf-8') as f:
            gara = json.load(f)
        
        # Usa il titolo dal JSON
        title = gara.get('titolo', 'Report')
        
        # Leggi il template
        html = template_html
        
        # Rimuovi vecchio autoload se esiste
        html = re.sub(r'<!--GPXREPORT_START-->.*?<!--GPXREPORT_END-->', '', html, flags=re.DOTALL)
        
        # Sostituisci il titolo
        html = re.sub(r'<title>[^<]*</title>', f'<title>{title}</title>', html)
        
        # Mostra data-content
        html = re.sub(r'(#data-content\s*\{[^}]*)display\s*:\s*none', r'\1display: block', html)
        
        # Nascondi upload-section
        html = re.sub(r'(<div id="upload-section")([^>]*)>', r'\1\2 style="display:none!important">', html)
        
        # Rimuovi reset-bar
        html = re.sub(r'<div id="reset-bar".*?</div>', '', html, flags=re.DOTALL)
        html = html.replace("if (rb) rb.style.display = 'flex';", "// report: reset-bar rimosso")
        html = html.replace("document.getElementById('reset-bar').style.display = 'none';", "// report: reset-bar rimosso")
        
        # Nascondi sv-hint
        html = re.sub(r'(<p class="sv-hint")', r'\1 style="display:none"', html)
        
        # Aggiungi title bar
        html = html.replace('<div class="container">', '<div class="container">\n' + TITLE_HTML.format(title=title), 1)
        
        # Aggiungi stub autoload
        autoload = AUTOLOAD_TEMPLATE.format(title=title)
        html = html.replace('</body>', autoload + '\n</body>', 1)
        
        # Salva l'HTML
        output_html_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return True
    except Exception as e:
        print(f"  [FAIL] {gara_json_path.name}: {e}")
        return False


def main():
    """Genera tutti i report HTML dai JSON"""
    
    json_dir = ARCHIVIO_DIR / 'gare-sorgenti'
    # Genera i file in public/ così Astro li copia automaticamente in dist/
    html_dir = ARCHIVIO_DIR / 'public' / 'gare'
    template_path = Path(__file__).parent / 'index.html'
    
    if not json_dir.exists():
        print(f"[FAIL] Cartella gare-sorgenti non trovata: {json_dir}")
        sys.exit(1)
    
    if not template_path.exists():
        print(f"[FAIL] Template non trovato: {template_path}")
        sys.exit(1)
    
    # Leggi il template una sola volta
    with open(template_path, 'r', encoding='utf-8') as f:
        template_html = f.read()
    
    # Trova tutti i JSON
    json_files = list(json_dir.glob('*.json'))
    
    if not json_files:
        print(f"[OK] Nessun JSON trovato in {json_dir}")
        return 0
    
    print(f"[*] Generando {len(json_files)} report HTML...")
    success = 0
    
    for json_file in sorted(json_files):
        slug = json_file.stem
        output_file = html_dir / f"{slug}.html"
        
        if generate_report_from_json(json_file, template_html, output_file):
            print(f"  [OK] {slug}")
            success += 1
        else:
            print(f"  [FAIL] {slug}")
    
    print(f"\n[*] Risultato: {success}/{len(json_files)} report generati")
    return 0 if success == len(json_files) else 1


if __name__ == '__main__':
    sys.exit(main())
