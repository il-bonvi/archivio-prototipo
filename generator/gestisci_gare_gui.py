#!/usr/bin/env python3
"""
gestisci_gare_gui.py — GUI tkinter per gestire il database delle gare.

Permette di:
  - Visualizzare tutte le gare
  - Modificare metadati
  - Eliminare gare
  - Rigenerare report da GPX
  - Lanciare build automatica
"""

import sys
import json
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import datetime

# Cartella dell'archivio Astro
ARCHIVIO_DIR = Path(__file__).parent.parent
GARE_SORGENTI_DIR = ARCHIVIO_DIR / "gare-sorgenti"
GARE_PUBLIC_DIR = ARCHIVIO_DIR / "public" / "gare"

# Valori validi per i campi
GENERI = ["Maschile", "Femminile"]
CATEGORIE = ["Elite", "U23", "Junior", "Allievi"]
DISCIPLINE = ["Strada", "Criterium", "Cronometro"]


class GareGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Gestore Gare — Archivio Ciclistico")
        self.geometry("900x700")
        self.resizable(True, True)
        
        # Icona (opzionale)
        try:
            self.iconbitmap(default='')
        except:
            pass
        
        # Stile
        style = ttk.Style()
        style.theme_use('clam')
        
        # Frame principale
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Titolo
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        title_label = ttk.Label(title_frame, text="GESTORE GARE", font=("Arial", 16, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # Frame superiore: lista + pulsanti
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame lista
        list_frame = ttk.Frame(top_frame)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        ttk.Label(list_frame, text="Gare nel database:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        # Listbox con scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Courier", 9), height=20)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox.bind('<<ListboxSelect>>', self.on_gara_select)
        scrollbar.config(command=self.listbox.yview)
        
        # Frame pulsanti
        btn_frame = ttk.Frame(top_frame)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.btn_modifica = ttk.Button(btn_frame, text="Modifica", command=self.modifica_gara, width=15)
        self.btn_modifica.pack(pady=5, fill=tk.X)
        
        self.btn_elimina = ttk.Button(btn_frame, text="Elimina", command=self.elimina_gara, width=15)
        self.btn_elimina.pack(pady=5, fill=tk.X)
        
        ttk.Button(btn_frame, text="Rigenera da GPX", command=self.rigenera_gpx, width=15).pack(pady=5, fill=tk.X)
        
        ttk.Separator(btn_frame, orient='horizontal').pack(pady=10, fill=tk.X)
        
        ttk.Button(btn_frame, text="Aggiorna lista", command=self.carica_gare, width=15).pack(pady=5, fill=tk.X)
        ttk.Button(btn_frame, text="Build & Deploy", command=self.build_progetto, width=15).pack(pady=5, fill=tk.X)
        
        # Info gara
        info_frame = ttk.LabelFrame(main_frame, text="Dettagli gara selezionata", padding=10)
        info_frame.pack(fill=tk.X, pady=(15, 0))
        
        self.info_text = tk.Text(info_frame, height=8, font=("Courier", 9), state=tk.DISABLED)
        self.info_text.pack(fill=tk.BOTH, expand=True)
        
        # Carica gare
        self.gare_list = []
        self.carica_gare()
        
        # Disabilita pulsanti all'inizio
        self.btn_modifica.config(state=tk.DISABLED)
        self.btn_elimina.config(state=tk.DISABLED)
    
    def carica_gare(self):
        """Carica la lista di gare da disco."""
        self.listbox.delete(0, tk.END)
        self.gare_list = []
        
        json_files = sorted(GARE_SORGENTI_DIR.glob("*.json"))
        json_files = [f for f in json_files if f.name != "_ESEMPIO.json"]
        
        if not json_files:
            self.listbox.insert(tk.END, "[Nessuna gara nel database]")
            self.info_text.config(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, "Crea una nuova gara con:\npython generator/genera_report.py")
            self.info_text.config(state=tk.DISABLED)
            return
        
        for filepath in json_files:
            try:
                data = json.loads(filepath.read_text(encoding='utf-8'))
                slug = data.get('slug', '?')
                titolo = data.get('titolo', '?')
                data_gara = data.get('data', '?')
                categoria = data.get('categoria', '?')
                
                item_text = f"[{slug}] {titolo} ({data_gara}) - {categoria}"
                self.listbox.insert(tk.END, item_text)
                self.gare_list.append((filepath, data))
            except Exception as e:
                print(f"Errore lettura {filepath}: {e}")
    
    def on_gara_select(self, event):
        """Mostra dettagli gara selezionata."""
        selection = self.listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        if idx >= len(self.gare_list):
            return
        
        filepath, data = self.gare_list[idx]
        
        # Abilita pulsanti
        self.btn_modifica.config(state=tk.NORMAL)
        self.btn_elimina.config(state=tk.NORMAL)
        
        # Mostra info
        info = f"""TITOLO:        {data.get('titolo', '-')}
SLUG:          {data.get('slug', '-')}
DATA:          {data.get('data', '-')}
GENERE:        {data.get('genere', '-')}
CATEGORIA:     {data.get('categoria', '-')}
DISCIPLINA:    {data.get('disciplina', '-')}
DISTANZA:      {data.get('distanza_km', '-')} km
DISLIVELLO:    {data.get('dislivello_m', '-')} m
LUOGO:         {data.get('luogo', '-')}
TEMPO:         {data.get('tempo', '-')}
"""
        
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, info)
        self.info_text.config(state=tk.DISABLED)
    
    def get_selected_gara(self):
        """Ritorna la gara selezionata."""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona una gara.")
            return None
        
        idx = selection[0]
        if idx >= len(self.gare_list):
            return None
        
        return self.gare_list[idx]
    
    def modifica_gara(self):
        """Apre finestra di modifica."""
        result = self.get_selected_gara()
        if result is None:
            return
        
        filepath, data = result
        EditWindow(self, filepath, data, self.carica_gare)
    
    def elimina_gara(self):
        """Elimina la gara selezionata."""
        result = self.get_selected_gara()
        if result is None:
            return
        
        filepath, data = result
        slug = data.get('slug', filepath.stem)
        titolo = data.get('titolo', slug)
        
        msg = f"""Stai per eliminare:
  {titolo}
  (slug: {slug})

Verranno eliminati:
  - gare-sorgenti/{filepath.name}
  - public/gare/{slug}.html

Procedi?"""
        
        if messagebox.askyesno("Eliminare gara?", msg):
            try:
                filepath.unlink()
                html_path = GARE_PUBLIC_DIR / f"{slug}.html"
                if html_path.exists():
                    html_path.unlink()
                
                messagebox.showinfo("Successo", f"Gara '{titolo}' eliminata.")
                self.carica_gare()
                
                if messagebox.askyesno("Build", "Eseguire npm run build?"):
                    self.build_progetto()
            except Exception as e:
                messagebox.showerror("Errore", f"Errore durante eliminazione:\n{e}")
    
    def rigenera_gpx(self):
        """Apre finestra di selezione GPX."""
        gpx_file = filedialog.askopenfilename(
            parent=self,
            title="Seleziona file GPX",
            filetypes=[("GPX files", "*.gpx"), ("All files", "*.*")]
        )
        
        if not gpx_file:
            return
        
        gpx_path = Path(gpx_file)
        if not gpx_path.exists():
            messagebox.showerror("Errore", "File non trovato.")
            return
        
        # Lancia genera_report.py
        try:
            result = subprocess.run(
                [sys.executable, str(ARCHIVIO_DIR / "generator" / "genera_report.py"), str(gpx_path)],
                cwd=ARCHIVIO_DIR,
                capture_output=True,
                text=True
            )
            
            output = result.stdout + result.stderr
            
            if result.returncode == 0:
                messagebox.showinfo("Successo", "Report generato con successo!")
                self.carica_gare()
            else:
                messagebox.showerror("Errore", f"Errore durante generazione:\n{output}")
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante esecuzione:\n{e}")
    
    def build_progetto(self):
        """Esegue npm run build."""
        try:
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=ARCHIVIO_DIR,
                capture_output=True,
                text=True,
                shell=(sys.platform == "win32")
            )
            
            if result.returncode == 0:
                messagebox.showinfo(
                    "Build completata",
                    "Build eseguita con successo!\n\nOra trascina la cartella dist/ su:\nhttps://app.netlify.com/drop"
                )
            else:
                messagebox.showerror("Build fallita", result.stderr or result.stdout)
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante build:\n{e}")


class EditWindow(tk.Toplevel):
    def __init__(self, parent, filepath, data, callback):
        super().__init__(parent)
        
        self.title(f"Modifica: {data.get('titolo', filepath.stem)}")
        self.geometry("500x600")
        self.resizable(False, True)
        
        self.filepath = filepath
        self.data = data.copy()
        self.callback = callback
        
        # Frame principale
        main = ttk.Frame(self, padding=15)
        main.pack(fill=tk.BOTH, expand=True)
        
        # Campi
        self.fields = {}
        row = 0
        
        field_defs = [
            ('titolo', 'Titolo gara *', 'text'),
            ('data', 'Data (YYYY-MM-DD)', 'text'),
            ('genere', 'Genere', 'combo', GENERI),
            ('categoria', 'Categoria', 'combo', CATEGORIE),
            ('disciplina', 'Disciplina', 'combo', DISCIPLINE),
            ('distanza_km', 'Distanza (km)', 'text'),
            ('dislivello_m', 'Dislivello (m)', 'text'),
            ('luogo', 'Luogo', 'text'),
            ('tempo', 'Tempo', 'text'),
        ]
        
        for field_data in field_defs:
            key = field_data[0]
            label = field_data[1]
            field_type = field_data[2]
            
            ttk.Label(main, text=label, font=("Arial", 9, "bold")).grid(row=row, column=0, sticky=tk.W, pady=(10, 5))
            
            if field_type == 'text':
                entry = ttk.Entry(main, width=40)
                entry.insert(0, str(self.data.get(key, '')))
                entry.grid(row=row, column=1, sticky=tk.EW)
                self.fields[key] = entry
            
            elif field_type == 'combo':
                values = field_data[3]
                combo = ttk.Combobox(main, values=values, state='readonly', width=37)
                combo.set(self.data.get(key, ''))
                combo.grid(row=row, column=1, sticky=tk.EW)
                self.fields[key] = combo
            
            row += 1
        
        main.columnconfigure(1, weight=1)
        
        # Pulsanti
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=(20, 0), sticky=tk.EW)
        
        ttk.Button(btn_frame, text="Salva", command=self.salva).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Annulla", command=self.destroy).pack(side=tk.LEFT, padx=5)
    
    def salva(self):
        """Salva le modifiche."""
        try:
            # Leggi campi
            for key, widget in self.fields.items():
                value = widget.get().strip()
                
                if value:
                    # Converti tipi
                    if key == 'distanza_km':
                        self.data[key] = float(value)
                    elif key == 'dislivello_m':
                        self.data[key] = int(value)
                    else:
                        self.data[key] = value
                else:
                    # Rimuovi se vuoto
                    self.data.pop(key, None)
            
            # Salva JSON
            self.filepath.write_text(
                json.dumps(self.data, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            
            messagebox.showinfo("Successo", "Modifiche salvate!")
            self.callback()
            
            # Chiedi build
            if messagebox.askyesno("Build", "Eseguire npm run build?"):
                result = subprocess.run(
                    ["npm", "run", "build"],
                    cwd=ARCHIVIO_DIR,
                    capture_output=True,
                    text=True,
                    shell=(sys.platform == "win32")
                )
                
                if result.returncode == 0:
                    messagebox.showinfo("Build", "Build completata!")
                else:
                    messagebox.showerror("Build fallita", result.stderr or result.stdout)
            
            self.destroy()
        
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante salvataggio:\n{e}")


if __name__ == '__main__':
    # Crea cartelle se non esistono
    GARE_SORGENTI_DIR.mkdir(parents=True, exist_ok=True)
    GARE_PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    
    app = GareGUI()
    app.mainloop()
