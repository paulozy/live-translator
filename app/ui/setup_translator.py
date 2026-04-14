import tkinter as tk
from tkinter import ttk, messagebox
from ..constants import COLORS, LANGUAGES, TARGET_LANGUAGES, WHISPER_MODELS
from ..recognizer import SOUNDDEVICE_OK, WHISPER_OK

try:
    import sounddevice as sd
except ImportError:
    sd = None


class SetupWindow:
    def __init__(self, root: tk.Tk, initial_cfg: dict, on_complete, on_back=None):
        self.root        = root
        self.initial_cfg = initial_cfg
        self.on_complete = on_complete
        self.on_back     = on_back
        self._build()

    def _build(self):
        self.root.title("Live Translator — Configuracao")
        self.root.configure(bg=COLORS["bg"])
        self.root.resizable(False, False)
        self._center()

        if self.on_back:
            back_row = tk.Frame(self.root, bg=COLORS["bg"])
            back_row.pack(fill="x", padx=20, pady=(12, 0))
            tk.Button(back_row, text="← Voltar",
                      font=("Segoe UI", 9),
                      bg=COLORS["bg"], fg=COLORS["muted"],
                      activebackground=COLORS["bg"], activeforeground=COLORS["text"],
                      relief="flat", cursor="hand2", bd=0,
                      command=self.on_back).pack(side="left")

        tk.Label(self.root, text="🎙", font=("Segoe UI Emoji", 36),
                 bg=COLORS["bg"], fg=COLORS["accent"]).pack(pady=(20, 4))
        tk.Label(self.root, text="Live Translator",
                 font=("Segoe UI", 22, "bold"),
                 bg=COLORS["bg"], fg=COLORS["text"]).pack()
        tk.Label(self.root, text="Configure uma vez, use para sempre",
                 font=("Segoe UI", 11),
                 bg=COLORS["bg"], fg=COLORS["muted"]).pack(pady=(2, 20))

        card = tk.Frame(self.root, bg=COLORS["surface"],
                        highlightthickness=1, highlightbackground=COLORS["border"])
        card.pack(padx=40, fill="x")

        # Idioma da live
        self._section(card, "Idioma da live")
        self.src_var = tk.StringVar(value=self.initial_cfg.get("src_lang", "Coreano"))
        for name, info in LANGUAGES.items():
            tk.Radiobutton(card, text=f"{info['flag']}  {name}",
                           variable=self.src_var, value=name,
                           font=("Segoe UI", 12),
                           bg=COLORS["surface"], fg=COLORS["text"],
                           selectcolor=COLORS["surface2"],
                           activebackground=COLORS["surface"],
                           activeforeground=COLORS["accent"],
                           borderwidth=0, cursor="hand2").pack(anchor="w", padx=20, pady=3)

        # Traduzir para
        self._section(card, "Traduzir para")
        self.tgt_var = tk.StringVar(value=self.initial_cfg.get("tgt_lang", "Portugues"))
        for lang in TARGET_LANGUAGES:
            flag = "🇧🇷" if lang == "Portugues" else "🇺🇸"
            tk.Radiobutton(card, text=f"{flag}  {lang}",
                           variable=self.tgt_var, value=lang,
                           font=("Segoe UI", 12),
                           bg=COLORS["surface"], fg=COLORS["text"],
                           selectcolor=COLORS["surface2"],
                           activebackground=COLORS["surface"],
                           activeforeground=COLORS["accent"],
                           borderwidth=0, cursor="hand2").pack(anchor="w", padx=20, pady=3)

        # Dispositivo de audio
        self._section(card, "Dispositivo de audio")
        self.device_var   = tk.StringVar()
        self.device_combo = ttk.Combobox(card, textvariable=self.device_var,
                                         state="readonly", width=44,
                                         font=("Segoe UI", 10))
        self.device_combo.pack(padx=20, pady=(0, 4), fill="x")
        self._load_devices()

        # Modelo Whisper
        self._section(card, "Modelo Whisper")
        self.whisper_var = tk.StringVar(
            value=self.initial_cfg.get("whisper_model", "small"))
        for name, desc in WHISPER_MODELS.items():
            row = tk.Frame(card, bg=COLORS["surface"])
            row.pack(anchor="w", padx=20, pady=2)
            tk.Radiobutton(row, text=name,
                           variable=self.whisper_var, value=name,
                           font=("Segoe UI", 11, "bold"),
                           bg=COLORS["surface"], fg=COLORS["text"],
                           selectcolor=COLORS["surface2"],
                           activebackground=COLORS["surface"],
                           activeforeground=COLORS["accent"],
                           borderwidth=0, cursor="hand2",
                           width=7, anchor="w").pack(side="left")
            tk.Label(row, text=desc, font=("Segoe UI", 9),
                     bg=COLORS["surface"], fg=COLORS["muted"]).pack(side="left")

        note = tk.Frame(card, bg=COLORS["surface"])
        note.pack(padx=20, pady=(12, 16), fill="x")
        if not WHISPER_OK:
            tk.Label(note,
                     text="⚠ Whisper nao instalado — usando Google Speech como fallback",
                     font=("Segoe UI", 9), bg=COLORS["surface"], fg=COLORS["warning"],
                     wraplength=400, justify="left").pack(anchor="w")
        else:
            tk.Label(note,
                     text="Modelos serao baixados automaticamente na 1ª execucao.",
                     font=("Segoe UI", 9),
                     bg=COLORS["surface"], fg=COLORS["muted"]).pack(anchor="w")

        tk.Button(self.root, text="Comecar  →",
                  font=("Segoe UI", 13, "bold"),
                  bg=COLORS["accent"], fg="white",
                  activebackground=COLORS["accent2"], activeforeground="white",
                  relief="flat", cursor="hand2", padx=28, pady=10,
                  command=self._finish).pack(pady=20)

    def _section(self, parent, title: str):
        tk.Label(parent, text=title.upper(),
                 font=("Segoe UI", 9, "bold"),
                 bg=COLORS["surface"], fg=COLORS["muted"]).pack(
            anchor="w", padx=20, pady=(16, 6))

    def _load_devices(self):
        if not SOUNDDEVICE_OK:
            self.device_combo["values"] = ["(instale sounddevice)"]
            self.device_var.set("(instale sounddevice)")
            return
        saved = self.initial_cfg.get("device", "")
        devices = sd.query_devices()
        loopback, others = [], []
        for i, d in enumerate(devices):
            if d["max_input_channels"] > 0:
                label = f"{i}: {d['name']}"
                low   = d["name"].lower()
                if any(k in low for k in ["cable", "stereo mix", "loopback",
                                           "what u hear", "virtual", "wave out"]):
                    loopback.append(label)
                else:
                    others.append(label)
        all_devs = loopback + others
        self.device_combo["values"] = all_devs or ["(nenhum dispositivo encontrado)"]
        if saved and saved in all_devs:
            self.device_var.set(saved)
        elif loopback:
            self.device_var.set(loopback[0])
        elif all_devs:
            self.device_var.set(all_devs[0])

    def _center(self):
        self.root.update_idletasks()
        w, h = 520, 820
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _finish(self):
        dev = self.device_var.get()
        if not dev or "nenhum" in dev or "instale" in dev:
            messagebox.showerror("Erro", "Selecione um dispositivo de audio valido.")
            return
        self.on_complete({
            "src_lang":      self.src_var.get(),
            "tgt_lang":      self.tgt_var.get(),
            "device":        dev,
            "whisper_model": self.whisper_var.get(),
        })
