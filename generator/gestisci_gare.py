#!/usr/bin/env python3
"""
gestisci_gare_gui.py — Gestore GUI per le gare (list, view, edit, delete, add).

Uso:
    python generator/gestisci_gare_gui.py

Funzionalità:
  - Elenco di tutte le gare nel database
  - Visualizza dettagli race (metadati + GPX)
  - Modifica metadati race
  - Elimina race dal database
  - Aggiungi nuova race (riusa dialog genera_report.py)
"""

import sys
import json
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

ARCHIVIO_DIR = Path(__file__).parent.parent
GARE_DIR = ARCHIVIO_DIR / "gare-sorgenti"
GARE_DIR.mkdir(parents=True, exist_ok=True)

CATEGORIE = ["Elite", "U23", "Junior", "Allievi"]
GENERI = ["Maschile", "Femminile"]
DISCIPLINE = ["Strada", "Criterium", "Cronometro"]

BG = "#ede9e2"
ACCENT = "#fc5200"
FG = "#1a1a1a"


# ── UTILITÀ ──────────────────────────────────────────────────────────────────

def load_all_races():
    """Carica tutte le gare da gare-sorgenti/"""
    races = []
    for json_file in sorted(GARE_DIR.glob("*.json")):
        try:
            data = json.loads(json_file.read_text(encoding='utf-8'))
            races.append((data.get("slug", "?"), data))
        except Exception:
            pass
    return races


def save_race(slug: str, data: dict):
    """Salva race JSON in entrambe le location"""
    json_path = GARE_DIR / f"{slug}.json"
    data_clean = {k: v for k, v in data.items() if v is not None}
    json_str = json.dumps(data_clean, ensure_ascii=False, indent=2)
    
    json_path.write_text(json_str, encoding='utf-8')
    
    public_json_dir = ARCHIVIO_DIR / "public" / "gare-sorgenti"
    public_json_dir.mkdir(parents=True, exist_ok=True)
    (public_json_dir / f"{slug}.json").write_text(json_str, encoding='utf-8')


def delete_race(slug: str):
    """Elimina race da entrambe le location"""
    json_path = GARE_DIR / f"{slug}.json"
    if json_path.exists():
        json_path.unlink()
    
    public_json_path = ARCHIVIO_DIR / "public" / "gare-sorgenti" / f"{slug}.json"
    if public_json_path.exists():
        public_json_path.unlink()


# ── MAIN GUI ──────────────────────────────────────────────────────────────────

class RaceManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📋 Gestore Gare")
        self.root.geometry("900x600")
        self.root.configure(bg=BG)
        
        self.root.option_add("*Background", BG)
        self.root.option_add("*Foreground", FG)
        self.root.option_add("*Font", ("Helvetica", 10))
        
        # Header
        header = tk.Frame(self.root, bg=ACCENT, height=60)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)
        
        title = tk.Label(header, text="📋 Gestore Gare", font=("Helvetica", 18, "bold"), 
                        bg=ACCENT, fg="white")
        title.pack(pady=12)
        
        # Content
        content = tk.Frame(self.root, bg=BG)
        content.pack(side="top", fill="both", expand=True, padx=12, pady=12)
        
        # Left: List
        left = tk.Frame(content, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        
        tk.Label(left, text="Gare nel database:", font=("Helvetica", 11, "bold"), bg=BG).pack(anchor="w", pady=(0, 6))
        
        list_frame = tk.Frame(left, bg="white", relief="solid", bd=1)
        list_frame.pack(fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.race_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, bg="white", 
                                       selectmode="single", font=("Helvetica", 10), bd=0)
        self.race_listbox.pack(side="left", fill="both", expand=True)
        self.race_listbox.bind("<<ListboxSelect>>", self.on_race_select)
        scrollbar.config(command=self.race_listbox.yview)
        
        # Right: Details
        right = tk.Frame(content, bg=BG)
        right.pack(side="right", fill="both", expand=True, padx=(6, 0))
        
        tk.Label(right, text="Dettagli gara:", font=("Helvetica", 11, "bold"), bg=BG).pack(anchor="w", pady=(0, 6))
        
        self.info_frame = tk.Frame(right, bg="white", relief="solid", bd=1)
        self.info_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        self.info_text = tk.Text(self.info_frame, bg="white", fg=FG, font=("Courier", 9), 
                                height=20, wrap="word", relief="flat", bd=0, padx=8, pady=8)
        self.info_text.pack(fill="both", expand=True)
        self.info_text.config(state="disabled")
        
        # Buttons
        button_frame = tk.Frame(self.root, bg=BG)
        button_frame.pack(side="bottom", fill="x", padx=12, pady=12)
        
        tk.Button(button_frame, text="➕ Aggiungi nuova", font=("Helvetica", 10),
                 bg=ACCENT, fg="white", padx=12, pady=8, relief="flat", bd=0,
                 cursor="hand2", command=self.add_race).pack(side="left", padx=(0, 6))
        
        tk.Button(button_frame, text="✏️ Modifica", font=("Helvetica", 10),
                 bg="#9ca3af", fg="white", padx=12, pady=8, relief="flat", bd=0,
                 cursor="hand2", command=self.edit_race).pack(side="left", padx=6)
        
        tk.Button(button_frame, text="🗑️ Elimina", font=("Helvetica", 10),
                 bg="#dc2626", fg="white", padx=12, pady=8, relief="flat", bd=0,
                 cursor="hand2", command=self.delete_race).pack(side="left", padx=6)
        
        self.refresh_list()
    
    def refresh_list(self):
        """Ricarica lista gare"""
        self.race_listbox.delete(0, tk.END)
        races = load_all_races()
        for slug, data in races:
            title = data.get("titolo", f"[{slug}]")
            self.race_listbox.insert(tk.END, f"  {title}")
    
    def on_race_select(self, event):
        """Mostra dettagli della gara selezionata"""
        idx = self.race_listbox.curselection()
        if not idx:
            return
        
        races = load_all_races()
        slug, data = races[idx[0]]
        
        gpx_count = len(data.get('gpx_points', []))
        info = f"""TITOLO:       {data.get('titolo', '—')}
SLUG:         {slug}
DATA:         {data.get('data', '—')}
GENERE:       {data.get('genere', '—')}
CATEGORIA:    {data.get('categoria', '—')}
DISCIPLINA:   {data.get('disciplina', '—')}
DISTANZA:     {data.get('distanza_km', '—')} km
DISLIVELLO:   {data.get('dislivello_m', '—')} m
LUOGO:        {data.get('luogo', '—')}
NOTE:         {(data.get('note', '') or '')[:100]}
GPX POINTS:   {gpx_count} punti"""
        
        self.info_text.config(state="normal")
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info)
        self.info_text.config(state="disabled")
    
    def add_race(self):
        """Chiama genera_report.py"""
        import subprocess
        try:
            subprocess.run([sys.executable, str(ARCHIVIO_DIR / "generator" / "genera_report.py")], check=False)
            self.refresh_list()
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile aggiungere gara: {e}")
    
    def edit_race(self):
        """Modifica metadati"""
        idx = self.race_listbox.curselection()
        if not idx:
            messagebox.showwarning("Attenzione", "Seleziona una gara prima")
            return
        
        races = load_all_races()
        slug, data = races[idx[0]]
        
        edit_win = tk.Toplevel(self.root)
        edit_win.title(f"Modifica: {data.get('titolo', slug)}")
        edit_win.geometry("500x550")
        edit_win.configure(bg=BG)
        
        fields = [
            ("titolo", "Titolo", "entry"),
            ("data", "Data (AAAA-MM-GG)", "entry"),
            ("luogo", "Luogo", "entry"),
            ("distanza_km", "Distanza (km)", "entry"),
            ("dislivello_m", "Dislivello (m)", "entry"),
            ("genere", "Genere", "combo", GENERI),
            ("categoria", "Categoria", "combo", CATEGORIE),
            ("disciplina", "Disciplina", "combo", DISCIPLINE),
        ]
        
        entries = {}
        
        for i, field_info in enumerate(fields):
            key, label = field_info[0], field_info[1]
            widget_type = field_info[2]
            
            tk.Label(edit_win, text=label, font=("Helvetica", 10, "bold"), bg=BG).grid(
                row=i, column=0, sticky="w", padx=12, pady=6)
            
            if widget_type == "combo":
                options = field_info[3]
                var = tk.StringVar(value=data.get(key, ""))
                combo = tk.OptionMenu(edit_win, var, *options)
                combo.config(width=30)
                combo.grid(row=i, column=1, sticky="ew", padx=12, pady=6)
                entries[key] = var
            else:
                entry = tk.Entry(edit_win, width=35, font=("Helvetica", 10))
                entry.insert(0, str(data.get(key, "") or ""))
                entry.grid(row=i, column=1, sticky="ew", padx=12, pady=6)
                entries[key] = entry
        
        def save_changes():
            for key, widget in entries.items():
                val = widget.get()
                if key in ("distanza_km", "dislivello_m"):
                    try:
                        val = float(val) if val else None
                    except:
                        val = None
                data[key] = val
            
            save_race(slug, data)
            messagebox.showinfo("Salvato", "Gara modificata con successo")
            self.refresh_list()
            edit_win.destroy()
        
        button_frame = tk.Frame(edit_win, bg=BG)
        button_frame.grid(row=len(fields), column=0, columnspan=2, sticky="ew", padx=12, pady=12)
        
        tk.Button(button_frame, text="Salva", bg=ACCENT, fg="white", padx=16, pady=6,
                 relief="flat", bd=0, cursor="hand2", command=save_changes).pack(side="left", padx=(0, 6))
        tk.Button(button_frame, text="Annulla", bg="#d1d5db", fg=FG, padx=16, pady=6,
                 relief="flat", bd=0, cursor="hand2", command=edit_win.destroy).pack(side="left")
        
        edit_win.columnconfigure(1, weight=1)
    
    def delete_race(self):
        """Elimina race"""
        idx = self.race_listbox.curselection()
        if not idx:
            messagebox.showwarning("Attenzione", "Seleziona una gara prima")
            return
        
        races = load_all_races()
        slug, data = races[idx[0]]
        title = data.get("titolo", slug)
        
        ok = messagebox.askyesno("Conferma", f"Eliminare '{title}'?\nQuesta azione è irreversibile.")
        if ok:
            delete_race(slug)
            messagebox.showinfo("Eliminato", "Gara rimossa dal database")
            self.refresh_list()


if __name__ == "__main__":
    root = tk.Tk()
    app = RaceManagerApp(root)
    root.mainloop()
