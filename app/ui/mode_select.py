import tkinter as tk
from ..constants import COLORS


class ModeSelectWindow:
    def __init__(self, root: tk.Tk, saved_mode: str | None, on_select):
        self.root       = root
        self.saved_mode = saved_mode
        self.on_select  = on_select
        self._build()

    def _build(self):
        self.root.title("Live Translator")
        self.root.configure(bg=COLORS["bg"])
        self.root.resizable(False, False)
        self._center()

        tk.Label(self.root, text="🎙", font=("Segoe UI Emoji", 36),
                 bg=COLORS["bg"], fg=COLORS["accent"]).pack(pady=(40, 4))
        tk.Label(self.root, text="Live Translator",
                 font=("Segoe UI", 22, "bold"),
                 bg=COLORS["bg"], fg=COLORS["text"]).pack()
        tk.Label(self.root, text="Escolha o modo de uso",
                 font=("Segoe UI", 11),
                 bg=COLORS["bg"], fg=COLORS["muted"]).pack(pady=(2, 32))

        row = tk.Frame(self.root, bg=COLORS["bg"])
        row.pack(padx=32, fill="x")
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)

        self._card(row, 0, "📺", "Modo Tradutor",
                   "Assista lives em outros\nidiomas com traducao\nem tempo real",
                   "translator")
        self._card(row, 1, "🎤", "Modo Legenda",
                   "Gere legendas da sua\nfala para o OBS via\nBrowser Source",
                   "caption")

    def _card(self, parent, col, icon, title, desc, mode):
        active = self.saved_mode == mode
        border = COLORS["accent"] if active else COLORS["border"]
        card   = tk.Frame(parent, bg=COLORS["surface"],
                          highlightthickness=2, highlightbackground=border,
                          cursor="hand2")
        card.grid(row=0, column=col, padx=8, sticky="nsew")

        tk.Label(card, text=icon, font=("Segoe UI Emoji", 32),
                 bg=COLORS["surface"], fg=COLORS["accent"]).pack(pady=(20, 6))
        tk.Label(card, text=title, font=("Segoe UI", 13, "bold"),
                 bg=COLORS["surface"], fg=COLORS["text"]).pack()
        tk.Label(card, text=desc, font=("Segoe UI", 10),
                 bg=COLORS["surface"], fg=COLORS["muted"],
                 justify="center").pack(pady=(8, 20))

        cb = lambda e, m=mode: self.on_select(m)
        card.bind("<Button-1>", cb)
        for child in card.winfo_children():
            child.bind("<Button-1>", cb)

    def _center(self):
        self.root.update_idletasks()
        w, h = 520, 440
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
