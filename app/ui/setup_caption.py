import tkinter as tk
from tkinter import ttk, messagebox
from ..constants import (COLORS, CAPTION_SRC_LANGUAGES, CAPTION_TGT_LANGUAGES,
                          WHISPER_MODELS)
from ..recognizer import SOUNDDEVICE_OK, WHISPER_OK

try:
    import sounddevice as sd
except ImportError:
    sd = None


class CaptionSetupWindow:
    def __init__(self, root: tk.Tk, initial_cfg: dict, on_complete, on_back=None):
        self.root        = root
        self.initial_cfg = initial_cfg
        self.on_complete = on_complete
        self.on_back     = on_back
        self._build()

    def _build(self):
        self.root.title("Live Translator — Legenda")
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

        tk.Label(self.root, text="🎤", font=("Segoe UI Emoji", 28),
                 bg=COLORS["bg"], fg=COLORS["accent"]).pack(pady=(16, 2))
        tk.Label(self.root, text="Configuracao — Modo Legenda",
                 font=("Segoe UI", 16, "bold"),
                 bg=COLORS["bg"], fg=COLORS["text"]).pack()
        tk.Label(self.root, text="Legendas ao vivo para o OBS",
                 font=("Segoe UI", 10),
                 bg=COLORS["bg"], fg=COLORS["muted"]).pack(pady=(2, 10))

        # Botao fixo no rodape (empacotado antes do scroll)
        tk.Button(self.root, text="Comecar  →",
                  font=("Segoe UI", 13, "bold"),
                  bg=COLORS["accent"], fg="white",
                  activebackground=COLORS["accent2"], activeforeground="white",
                  relief="flat", cursor="hand2", padx=28, pady=10,
                  command=self._finish).pack(side="bottom", pady=16)

        # Scroll container
        scroll_wrapper = tk.Frame(self.root, bg=COLORS["bg"])
        scroll_wrapper.pack(fill="both", expand=True, padx=32)

        canvas    = tk.Canvas(scroll_wrapper, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_wrapper, orient="vertical", command=canvas.yview)
        self._scroll_frame = tk.Frame(canvas, bg=COLORS["bg"])
        self._scroll_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        card = tk.Frame(self._scroll_frame, bg=COLORS["surface"],
                        highlightthickness=1, highlightbackground=COLORS["border"])
        card.pack(fill="x", padx=0, pady=4)

        # Microfone
        self._section(card, "Microfone")
        self.device_var   = tk.StringVar()
        self.device_combo = ttk.Combobox(card, textvariable=self.device_var,
                                         state="readonly", width=44,
                                         font=("Segoe UI", 10))
        self.device_combo.pack(padx=20, pady=(0, 4), fill="x")
        self._load_mics()

        # Idioma que o streamer fala
        self._section(card, "Idioma que voce fala")
        self.src_var = tk.StringVar(value=self.initial_cfg.get("src_lang", "Portugues"))
        ttk.Combobox(card, textvariable=self.src_var,
                     values=list(CAPTION_SRC_LANGUAGES.keys()),
                     state="readonly", width=24,
                     font=("Segoe UI", 10)).pack(anchor="w", padx=20, pady=(0, 4))

        # Traducao para
        self._section(card, "Traducao para")
        self.tgt_var = tk.StringVar(value=self.initial_cfg.get("tgt_lang", "Sem traducao"))
        for lang in CAPTION_TGT_LANGUAGES:
            tk.Radiobutton(card, text=lang,
                           variable=self.tgt_var, value=lang,
                           font=("Segoe UI", 11),
                           bg=COLORS["surface"], fg=COLORS["text"],
                           selectcolor=COLORS["surface2"],
                           activebackground=COLORS["surface"],
                           activeforeground=COLORS["accent"],
                           borderwidth=0, cursor="hand2").pack(anchor="w", padx=20, pady=2)

        # Porta do servidor
        self._section(card, "Porta do servidor")
        port_row = tk.Frame(card, bg=COLORS["surface"])
        port_row.pack(anchor="w", padx=20, pady=(0, 4))
        self.port_var = tk.StringVar(value=str(self.initial_cfg.get("port", 5050)))
        tk.Entry(port_row, textvariable=self.port_var, width=8,
                 font=("Segoe UI", 11), bg=COLORS["surface2"], fg=COLORS["text"],
                 insertbackground=COLORS["text"], relief="flat",
                 highlightthickness=1,
                 highlightbackground=COLORS["border"]).pack(side="left")
        tk.Label(port_row, text="  → Browser Source: http://localhost:PORTA",
                 font=("Segoe UI", 9),
                 bg=COLORS["surface"], fg=COLORS["muted"]).pack(side="left")

        # Modelo Whisper
        self._section(card, "Modelo Whisper")
        self.whisper_var = tk.StringVar(
            value=self.initial_cfg.get("whisper_model", "small"))
        for name, desc in WHISPER_MODELS.items():
            wrow = tk.Frame(card, bg=COLORS["surface"])
            wrow.pack(anchor="w", padx=20, pady=2)
            tk.Radiobutton(wrow, text=name,
                           variable=self.whisper_var, value=name,
                           font=("Segoe UI", 11, "bold"),
                           bg=COLORS["surface"], fg=COLORS["text"],
                           selectcolor=COLORS["surface2"],
                           activebackground=COLORS["surface"],
                           activeforeground=COLORS["accent"],
                           borderwidth=0, cursor="hand2",
                           width=7, anchor="w").pack(side="left")
            tk.Label(wrow, text=desc, font=("Segoe UI", 9),
                     bg=COLORS["surface"], fg=COLORS["muted"]).pack(side="left")

        if not WHISPER_OK:
            tk.Label(card,
                     text="⚠ Whisper nao instalado — usando Google Speech como fallback",
                     font=("Segoe UI", 9), bg=COLORS["surface"], fg=COLORS["warning"],
                     wraplength=400).pack(anchor="w", padx=20, pady=(4, 0))

        # Aparencia da legenda
        self._section(card, "Aparencia da legenda")
        self._build_appearance(card)

    def _build_appearance(self, card):
        # Tamanho da fonte
        size_row = tk.Frame(card, bg=COLORS["surface"])
        size_row.pack(fill="x", padx=20, pady=(0, 6))
        tk.Label(size_row, text="Tamanho da fonte:",
                 font=("Segoe UI", 10),
                 bg=COLORS["surface"], fg=COLORS["text"]).pack(side="left")
        self.font_size_var = tk.IntVar(value=self.initial_cfg.get("font_size", 48))
        self.font_size_lbl = tk.Label(size_row, text=str(self.font_size_var.get()),
                                       font=("Segoe UI", 10, "bold"),
                                       bg=COLORS["surface"], fg=COLORS["accent"], width=3)
        self.font_size_lbl.pack(side="right")
        tk.Scale(size_row, from_=20, to=100, orient="horizontal",
                 variable=self.font_size_var,
                 command=lambda v: self.font_size_lbl.config(text=str(int(float(v)))),
                 bg=COLORS["surface"], fg=COLORS["text"],
                 troughcolor=COLORS["surface2"], activebackground=COLORS["accent"],
                 highlightthickness=0, bd=0, length=160).pack(side="left", padx=8)

        # Cor do texto
        color_row = tk.Frame(card, bg=COLORS["surface"])
        color_row.pack(fill="x", padx=20, pady=(0, 4))
        tk.Label(color_row, text="Cor do texto:",
                 font=("Segoe UI", 10),
                 bg=COLORS["surface"], fg=COLORS["text"]).pack(side="left")
        self.text_color_var = tk.StringVar(
            value=self.initial_cfg.get("text_color", "#ffffff"))
        for clr, lbl in [("#ffffff", "Branco"), ("#ffff00", "Amarelo"), ("#00ffff", "Ciano")]:
            tk.Button(color_row, text=lbl, width=7, font=("Segoe UI", 9),
                      bg=clr, fg="#000000", relief="flat", cursor="hand2",
                      command=lambda c=clr: self.text_color_var.set(c)).pack(side="left", padx=3)
        tk.Entry(color_row, textvariable=self.text_color_var, width=9,
                 font=("Segoe UI", 10), bg=COLORS["surface2"], fg=COLORS["text"],
                 insertbackground=COLORS["text"], relief="flat",
                 highlightthickness=1,
                 highlightbackground=COLORS["border"]).pack(side="left", padx=(6, 0))

        # Cor do fundo
        bg_row = tk.Frame(card, bg=COLORS["surface"])
        bg_row.pack(fill="x", padx=20, pady=(0, 4))
        tk.Label(bg_row, text="Fundo:",
                 font=("Segoe UI", 10),
                 bg=COLORS["surface"], fg=COLORS["text"]).pack(side="left")
        self.bg_color_var = tk.StringVar(
            value=self.initial_cfg.get("bg_color", "#000000"))
        for clr, lbl in [("#000000", "Preto"), ("#1a1a2e", "Azul"), ("#2d0000", "Vinho")]:
            tk.Button(bg_row, text=lbl, width=7, font=("Segoe UI", 9),
                      bg=clr, fg="#ffffff", relief="flat", cursor="hand2",
                      command=lambda c=clr: self.bg_color_var.set(c)).pack(side="left", padx=3)
        tk.Entry(bg_row, textvariable=self.bg_color_var, width=9,
                 font=("Segoe UI", 10), bg=COLORS["surface2"], fg=COLORS["text"],
                 insertbackground=COLORS["text"], relief="flat",
                 highlightthickness=1,
                 highlightbackground=COLORS["border"]).pack(side="left", padx=(6, 0))

        # Opacidade do fundo
        op_row = tk.Frame(card, bg=COLORS["surface"])
        op_row.pack(fill="x", padx=20, pady=(4, 16))
        tk.Label(op_row, text="Opacidade do fundo:",
                 font=("Segoe UI", 10),
                 bg=COLORS["surface"], fg=COLORS["text"]).pack(side="left")
        self.bg_opacity_var = tk.DoubleVar(
            value=self.initial_cfg.get("bg_opacity", 0.65))
        self._op_int_var = tk.IntVar(value=int(self.bg_opacity_var.get() * 100))
        self.op_lbl = tk.Label(op_row, text=f"{self._op_int_var.get()}%",
                                font=("Segoe UI", 10, "bold"),
                                bg=COLORS["surface"], fg=COLORS["accent"], width=5)
        self.op_lbl.pack(side="right")
        tk.Scale(op_row, from_=0, to=100, orient="horizontal",
                 variable=self._op_int_var,
                 command=lambda v: (self.bg_opacity_var.set(int(float(v)) / 100),
                                    self.op_lbl.config(text=f"{int(float(v))}%")),
                 bg=COLORS["surface"], fg=COLORS["text"],
                 troughcolor=COLORS["surface2"], activebackground=COLORS["accent"],
                 highlightthickness=0, bd=0, length=160).pack(side="left", padx=8)

    def _section(self, parent, title: str):
        tk.Label(parent, text=title.upper(),
                 font=("Segoe UI", 9, "bold"),
                 bg=COLORS["surface"], fg=COLORS["muted"]).pack(
            anchor="w", padx=20, pady=(14, 6))

    def _load_mics(self):
        if not SOUNDDEVICE_OK:
            self.device_combo["values"] = ["(instale sounddevice)"]
            self.device_var.set("(instale sounddevice)")
            return
        saved   = self.initial_cfg.get("device", "")
        devices = sd.query_devices()
        mics, loopback = [], []
        for i, d in enumerate(devices):
            if d["max_input_channels"] > 0:
                label = f"{i}: {d['name']}"
                low   = d["name"].lower()
                if any(k in low for k in ["cable", "stereo mix", "loopback",
                                           "what u hear", "virtual", "wave out"]):
                    loopback.append(label)
                else:
                    mics.append(label)
        all_devs = mics + loopback
        self.device_combo["values"] = all_devs or ["(nenhum microfone encontrado)"]
        if saved and saved in all_devs:
            self.device_var.set(saved)
        elif mics:
            self.device_var.set(mics[0])
        elif all_devs:
            self.device_var.set(all_devs[0])

    def _center(self):
        self.root.update_idletasks()
        w, h = 560, 780
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _finish(self):
        dev = self.device_var.get()
        if not dev or "nenhum" in dev or "instale" in dev:
            messagebox.showerror("Erro", "Selecione um microfone valido.")
            return
        try:
            port = int(self.port_var.get())
            if not (1024 <= port <= 65535):
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Porta invalida. Use um numero entre 1024 e 65535.")
            return
        self.on_complete({
            "src_lang":      self.src_var.get(),
            "tgt_lang":      self.tgt_var.get(),
            "device":        dev,
            "port":          port,
            "whisper_model": self.whisper_var.get(),
            "font_size":     self.font_size_var.get(),
            "text_color":    self.text_color_var.get(),
            "bg_color":      self.bg_color_var.get(),
            "bg_opacity":    self.bg_opacity_var.get(),
        })
