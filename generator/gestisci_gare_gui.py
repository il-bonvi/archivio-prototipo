#!/usr/bin/env python3
"""
gestisci_gare_gui.py — GUI tkinter per gestire il database delle gare.

Permette di:
  - Visualizzare tutte le gare
  - Modificare metadati
  - Eliminare gare
  - Rigenerare report da GPX
  - Fare git push per pubblicare sul sito
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

GENERI     = ["Maschile", "Femminile"]
CATEGORIE  = ["Elite", "U23", "Junior", "Allievi"]
DISCIPLINE = ["Strada", "Criterium", "Cronometro"]


class GareGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Gestore Gare — Archivio Ciclistico")
        self.geometry("900x700")
        self.resizable(True, True)

        style = ttk.Style()
        style.theme_use('clam')

        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Titolo
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(title_frame, text="GESTORE GARE", font=("Arial", 16, "bold")).pack(side=tk.LEFT)

        # Frame superiore: lista + pulsanti
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.BOTH, expand=True)

        # Lista gare
        list_frame = ttk.Frame(top_frame)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        ttk.Label(list_frame, text="Gare nel database:", font=("Arial", 10, "bold")).pack(anchor=tk.W)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Courier", 9), height=20)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox.bind('<<ListboxSelect>>', self.on_gara_select)
        scrollbar.config(command=self.listbox.yview)

        # Pulsanti
        btn_frame = ttk.Frame(top_frame)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.btn_modifica = ttk.Button(btn_frame, text="Modifica", command=self.modifica_gara, width=15)
        self.btn_modifica.pack(pady=5, fill=tk.X)

        self.btn_elimina = ttk.Button(btn_frame, text="Elimina", command=self.elimina_gara, width=15)
        self.btn_elimina.pack(pady=5, fill=tk.X)

        ttk.Button(btn_frame, text="Rigenera da GPX", command=self.rigenera_gpx, width=15).pack(pady=5, fill=tk.X)

        ttk.Separator(btn_frame, orient='horizontal').pack(pady=10, fill=tk.X)

        ttk.Button(btn_frame, text="Aggiorna lista", command=self.carica_gare, width=15).pack(pady=5, fill=tk.X)
        ttk.Button(btn_frame, text="Pubblica (git push)", command=self.git_push, width=15).pack(pady=5, fill=tk.X)

        # Info gara
        info_frame = ttk.LabelFrame(main_frame, text="Dettagli gara selezionata", padding=10)
        info_frame.pack(fill=tk.X, pady=(15, 0))

        self.info_text = tk.Text(info_frame, height=8, font=("Courier", 9), state=tk.DISABLED)
        self.info_text.pack(fill=tk.BOTH, expand=True)

        self.gare_list = []
        self.carica_gare()

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
                slug     = data.get('slug', '?')
                titolo   = data.get('titolo', '?')
                data_g   = data.get('data', '?')
                categoria = data.get('categoria', '?')
                self.listbox.insert(tk.END, f"[{slug}] {titolo} ({data_g}) - {categoria}")
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
        self.btn_modifica.config(state=tk.NORMAL)
        self.btn_elimina.config(state=tk.NORMAL)

        info = (
            f"TITOLO:        {data.get('titolo', '-')}\n"
            f"SLUG:          {data.get('slug', '-')}\n"
            f"DATA:          {data.get('data', '-')}\n"
            f"GENERE:        {data.get('genere', '-')}\n"
            f"CATEGORIA:     {data.get('categoria', '-')}\n"
            f"DISCIPLINA:    {data.get('disciplina', '-')}\n"
            f"DISTANZA:      {data.get('distanza_km', '-')} km\n"
            f"DISLIVELLO:    {data.get('dislivello_m', '-')} m\n"
            f"LUOGO:         {data.get('luogo', '-')}\n"
            f"TEMPO:         {data.get('tempo', '-')}\n"
        )
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, info)
        self.info_text.config(state=tk.DISABLED)

    def get_selected_gara(self):
        """Ritorna la gara selezionata o None."""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona una gara.")
            return None
        idx = selection[0]
        if idx >= len(self.gare_list):
            return None
        return self.gare_list[idx]

    def modifica_gara(self):
        result = self.get_selected_gara()
        if result:
            EditWindow(self, result[0], result[1], self.carica_gare)

    def elimina_gara(self):
        result = self.get_selected_gara()
        if result is None:
            return

        filepath, data = result
        slug   = data.get('slug', filepath.stem)
        titolo = data.get('titolo', slug)

        msg = (
            f"Stai per eliminare:\n  {titolo}\n  (slug: {slug})\n\n"
            f"Verranno eliminati:\n"
            f"  - gare-sorgenti/{filepath.name}\n"
            f"  - public/gare/{slug}.html\n\nProcedi?"
        )

        if messagebox.askyesno("Eliminare gara?", msg):
            try:
                filepath.unlink()
                html_path = GARE_PUBLIC_DIR / f"{slug}.html"
                if html_path.exists():
                    html_path.unlink()

                messagebox.showinfo("Successo", f"Gara '{titolo}' eliminata.")
                self.carica_gare()

                if messagebox.askyesno("Pubblicare?", "Fare git push per aggiornare il sito?"):
                    self.git_push(commit_msg=f"Elimina gara: {titolo}")

            except Exception as e:
                messagebox.showerror("Errore", f"Errore durante eliminazione:\n{e}")

    def rigenera_gpx(self):
        """Apre finestra di selezione GPX e lancia genera_report.py."""
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

        try:
            result = subprocess.run(
                [sys.executable, str(ARCHIVIO_DIR / "generator" / "genera_report.py"), str(gpx_path)],
                cwd=ARCHIVIO_DIR,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                messagebox.showinfo("Successo", "Report generato con successo!")
                self.carica_gare()
            else:
                messagebox.showerror("Errore", f"Errore durante generazione:\n{result.stdout}\n{result.stderr}")
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante esecuzione:\n{e}")

    def git_push(self, commit_msg: str = None):
        """Esegue git add, commit e push."""
        if commit_msg is None:
            commit_msg = f"Aggiorna database gare ({datetime.now().strftime('%Y-%m-%d %H:%M')})"

        try:
            # git add .
            r1 = subprocess.run(["git", "add", "."], cwd=ARCHIVIO_DIR,
                                 capture_output=True, text=True)
            if r1.returncode != 0:
                messagebox.showerror("git add fallito", r1.stderr or r1.stdout)
                return

            # Controlla se c'è qualcosa da committare
            status = subprocess.run(["git", "status", "--porcelain"], cwd=ARCHIVIO_DIR,
                                     capture_output=True, text=True)
            if not status.stdout.strip():
                messagebox.showinfo("Nessuna modifica", "Nessuna modifica da pubblicare.")
                return

            # git commit
            r2 = subprocess.run(["git", "commit", "-m", commit_msg], cwd=ARCHIVIO_DIR,
                                  capture_output=True, text=True)
            if r2.returncode != 0:
                messagebox.showerror("git commit fallito", r2.stderr or r2.stdout)
                return

            # git push
            r3 = subprocess.run(["git", "push"], cwd=ARCHIVIO_DIR,
                                  capture_output=True, text=True)
            if r3.returncode == 0:
                messagebox.showinfo(
                    "Pubblicato!",
                    f"Push completato.\n\nCommit: {commit_msg}\n\n"
                    f"GitHub Actions sta deployando...\n"
                    f"https://github.com/il-bonvi/archivio-prototipo/actions"
                )
            else:
                messagebox.showerror("git push fallito", r3.stderr or r3.stdout)

        except FileNotFoundError:
            messagebox.showerror("Errore", "git non trovato. Assicurati che git sia installato e nel PATH.")
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante git push:\n{e}")


class EditWindow(tk.Toplevel):
    def __init__(self, parent, filepath, data, callback):
        super().__init__(parent)

        self.title(f"Modifica: {data.get('titolo', filepath.stem)}")
        self.geometry("500x600")
        self.resizable(False, True)

        self.filepath = filepath
        self.data = data.copy()
        self.callback = callback

        main = ttk.Frame(self, padding=15)
        main.pack(fill=tk.BOTH, expand=True)

        self.fields = {}
        row = 0

        field_defs = [
            ('titolo',       'Titolo gara *',       'text'),
            ('data',         'Data (YYYY-MM-DD)',    'text'),
            ('genere',       'Genere',               'combo', GENERI),
            ('categoria',    'Categoria',            'combo', CATEGORIE),
            ('disciplina',   'Disciplina',           'combo', DISCIPLINE),
            ('distanza_km',  'Distanza (km)',        'text'),
            ('dislivello_m', 'Dislivello (m)',       'text'),
            ('luogo',        'Luogo',                'text'),
            ('tempo',        'Tempo',                'text'),
        ]

        for field_data in field_defs:
            key        = field_data[0]
            label      = field_data[1]
            field_type = field_data[2]

            ttk.Label(main, text=label, font=("Arial", 9, "bold")).grid(
                row=row, column=0, sticky=tk.W, pady=(10, 5))

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

        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=(20, 0), sticky=tk.EW)

        ttk.Button(btn_frame, text="Salva", command=self.salva).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Annulla", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def salva(self):
        try:
            for key, widget in self.fields.items():
                value = widget.get().strip()
                if value:
                    if key == 'distanza_km':
                        self.data[key] = float(value)
                    elif key == 'dislivello_m':
                        self.data[key] = int(value)
                    else:
                        self.data[key] = value
                else:
                    self.data.pop(key, None)

            self.filepath.write_text(
                json.dumps(self.data, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )

            messagebox.showinfo("Successo", "Modifiche salvate!")
            self.callback()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante salvataggio:\n{e}")


if __name__ == '__main__':
    GARE_SORGENTI_DIR.mkdir(parents=True, exist_ok=True)
    GARE_PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    app = GareGUI()
    app.mainloop()