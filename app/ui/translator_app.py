import threading
import queue
import tkinter as tk
from tkinter import scrolledtext, messagebox

from ..constants import COLORS, LANGUAGES
from ..recognizer import WHISPER_OK, SOUNDDEVICE_OK, SR_OK, load_whisper_model, RecognizerEngine
from ..translation import Translator
from .setup_translator import SetupWindow


class TranslatorApp:
    def __init__(self, root: tk.Tk, cfg: dict, on_back=None):
        self.root           = root
        self.cfg            = cfg
        self.on_back        = on_back
        self.is_running     = False
        self.trans_queue: queue.Queue = queue.Queue()
        self._whisper       = None
        self._whisper_ready = False
        self._recognizer: RecognizerEngine | None = None
        self._translator    = Translator()
        self._build()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        if WHISPER_OK:
            self._preload_whisper()
        else:
            self._set_status("warning", "Whisper nao instalado — usando Google Speech")

    # ── Whisper ──────────────────────────────────────────────────────────────
    def _preload_whisper(self):
        name = self.cfg.get("whisper_model", "small")
        self._set_status("loading", f"Carregando Whisper ({name})...")

        def _load():
            self._whisper       = load_whisper_model(name)
            self._whisper_ready = True
            self._translator.set_status_callback(self._set_status)
            self._set_status("idle", "Pronto")

        threading.Thread(target=_load, daemon=True).start()

    # ── UI ───────────────────────────────────────────────────────────────────
    def _build(self):
        self.root.title("Live Translator")
        self.root.geometry("680x580")
        self.root.configure(bg=COLORS["bg"])
        self.root.resizable(True, True)
        self._center()

        hdr = tk.Frame(self.root, bg=COLORS["surface"], height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        if self.on_back:
            tk.Button(hdr, text="←", font=("Segoe UI", 12),
                      bg=COLORS["surface"], fg=COLORS["muted"],
                      activebackground=COLORS["surface2"], activeforeground=COLORS["text"],
                      relief="flat", cursor="hand2", bd=0,
                      command=self._go_back).pack(side="left", padx=(12, 0))

        tk.Label(hdr, text="🎙  Live Translator",
                 font=("Segoe UI", 14, "bold"),
                 bg=COLORS["surface"], fg=COLORS["text"]).pack(side="left", padx=10)

        src, tgt = self.cfg["src_lang"], self.cfg["tgt_lang"]
        tgt_flag = "🇧🇷" if tgt == "Portugues" else "🇺🇸"
        tk.Label(hdr, text=f"{LANGUAGES[src]['flag']} {src}  →  {tgt_flag} {tgt}",
                 font=("Segoe UI", 11),
                 bg=COLORS["surface"], fg=COLORS["muted"]).pack(side="left", padx=4)

        self.status_dot   = tk.Label(hdr, text="●", font=("Segoe UI", 14),
                                      bg=COLORS["surface"], fg=COLORS["muted"])
        self.status_dot.pack(side="right", padx=(0, 16))
        self.status_label = tk.Label(hdr, text="Iniciando...",
                                      font=("Segoe UI", 10),
                                      bg=COLORS["surface"], fg=COLORS["muted"])
        self.status_label.pack(side="right")

        bar = tk.Frame(self.root, bg=COLORS["bg"], pady=12)
        bar.pack(fill="x", padx=20)

        self.btn_start = tk.Button(bar, text="▶  Iniciar",
                                    font=("Segoe UI", 11, "bold"),
                                    bg=COLORS["accent"], fg="white",
                                    activebackground=COLORS["accent2"],
                                    activeforeground="white",
                                    relief="flat", cursor="hand2",
                                    padx=20, pady=7, command=self._toggle)
        self.btn_start.pack(side="left")

        tk.Button(bar, text="Limpar", font=("Segoe UI", 10),
                  bg=COLORS["surface2"], fg=COLORS["muted"],
                  activebackground=COLORS["border"], activeforeground=COLORS["text"],
                  relief="flat", cursor="hand2", padx=14, pady=7,
                  command=self._clear).pack(side="left", padx=8)

        tk.Button(bar, text="⚙  Configuracoes", font=("Segoe UI", 10),
                  bg=COLORS["surface2"], fg=COLORS["muted"],
                  activebackground=COLORS["border"], activeforeground=COLORS["text"],
                  relief="flat", cursor="hand2", padx=14, pady=7,
                  command=self._open_settings).pack(side="right")

        panels = tk.Frame(self.root, bg=COLORS["bg"])
        panels.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        tk.Label(panels, text="ORIGINAL", font=("Segoe UI", 9, "bold"),
                 bg=COLORS["bg"], fg=COLORS["muted"]).pack(anchor="w", pady=(0, 4))

        self.orig_box = scrolledtext.ScrolledText(
            panels, font=("Segoe UI", 12), wrap="word",
            relief="flat", bd=0, bg=COLORS["orig_bg"], fg=COLORS["text"],
            insertbackground=COLORS["text"],
            highlightthickness=1, highlightbackground=COLORS["border"],
            state="disabled", height=7)
        self.orig_box.pack(fill="both", expand=True)

        tk.Label(panels, text="TRADUCAO", font=("Segoe UI", 9, "bold"),
                 bg=COLORS["bg"], fg=COLORS["accent"]).pack(anchor="w", pady=(14, 4))

        self.trans_box = scrolledtext.ScrolledText(
            panels, font=("Segoe UI", 12), wrap="word",
            relief="flat", bd=0, bg=COLORS["trans_bg"], fg=COLORS["trans_fg"],
            insertbackground=COLORS["trans_fg"],
            highlightthickness=1, highlightbackground=COLORS["accent2"],
            state="disabled", height=7)
        self.trans_box.pack(fill="both", expand=True)

    def _center(self):
        self.root.update_idletasks()
        w, h = 680, 580
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _set_status(self, state: str, msg: str):
        colors = {"idle": COLORS["muted"], "running": COLORS["success"],
                  "loading": COLORS["warning"], "error": COLORS["error"],
                  "warning": COLORS["warning"]}
        c = colors.get(state, COLORS["muted"])
        def _update():
            try:
                self.status_dot.config(fg=c)
                self.status_label.config(text=msg, fg=c)
            except Exception:
                pass  # widget destruido por navegacao — ignorar
        self.root.after(0, _update)

    def _append(self, box, text: str):
        def do():
            box.config(state="normal")
            box.insert("end", text + "\n\n")
            box.see("end")
            box.config(state="disabled")
        self.root.after(0, do)

    def _clear(self):
        for box in (self.orig_box, self.trans_box):
            box.config(state="normal")
            box.delete("1.0", "end")
            box.config(state="disabled")

    # ── Navegacao ─────────────────────────────────────────────────────────────
    def _go_back(self):
        self._stop()
        if self.on_back:
            for w in self.root.winfo_children():
                w.destroy()
            self.on_back()

    def _open_settings(self):
        self._stop()
        for w in self.root.winfo_children():
            w.destroy()
        SetupWindow(self.root, self.cfg,
                    on_complete=self._on_settings_done,
                    on_back=self._go_back)

    def _on_settings_done(self, new_cfg: dict):
        self.cfg = new_cfg
        for w in self.root.winfo_children():
            w.destroy()
        self.__init__(self.root, self.cfg, self.on_back)

    # ── Controle ──────────────────────────────────────────────────────────────
    def _toggle(self):
        if self.is_running:
            self._stop()
        else:
            self._start()

    def _start(self):
        if not SOUNDDEVICE_OK:
            messagebox.showerror("Erro", "Instale sounddevice:\npip install sounddevice")
            return
        if WHISPER_OK and not self._whisper_ready:
            messagebox.showinfo("Aguarde",
                "O modelo Whisper ainda esta carregando.\nTente novamente em instantes.")
            return
        if not WHISPER_OK and not SR_OK:
            messagebox.showerror("Erro",
                "Nenhum reconhecedor disponivel.\n"
                "Instale: pip install openai-whisper imageio-ffmpeg")
            return
        try:
            device_index = int(self.cfg.get("device", "").split(":")[0])
        except Exception:
            messagebox.showerror("Erro", "Dispositivo de audio invalido. Reconfigure.")
            return

        self.is_running = True
        self.btn_start.config(text="⏹  Parar", bg=COLORS["error"],
                               activebackground="#c04040")
        self._set_status("running", "Ouvindo...")
        self._translator.set_status_callback(self._set_status)

        src_lang  = self.cfg["src_lang"]
        lang_code = LANGUAGES[src_lang]["code"]

        self._recognizer = RecognizerEngine(
            device_index = device_index,
            lang_code    = lang_code,
            get_whisper  = lambda: self._whisper,
            on_text      = self._on_recognized,
            set_status   = self._set_status,
        )
        self._recognizer.start()
        threading.Thread(target=self._translate_loop, daemon=True).start()

    def _stop(self):
        self.is_running = False
        if self._recognizer:
            self._recognizer.stop()
            self._recognizer = None
        try:
            self.btn_start.config(text="▶  Iniciar", bg=COLORS["accent"],
                                   activebackground=COLORS["accent2"])
        except Exception:
            pass
        self._set_status("idle", "Parado")

    def _on_close(self):
        self.is_running = False
        self.root.destroy()

    # ── Processamento ─────────────────────────────────────────────────────────
    def _on_recognized(self, text: str):
        self._append(self.orig_box, text)
        self.trans_queue.put(text)

    def _translate_loop(self):
        src_code = LANGUAGES[self.cfg["src_lang"]]["src"]
        tgt_lang = self.cfg["tgt_lang"]
        while self.is_running:
            try:
                text = self.trans_queue.get(timeout=1)
            except queue.Empty:
                continue
            try:
                self._set_status("loading" if not self._translator._model_cache
                                 else "running", "Traduzindo...")
                result = self._translator.translate(text, src_code, tgt_lang)
                self._append(self.trans_box, result)
                self._set_status("running", "Ouvindo...")
            except Exception as e:
                self._set_status("error", f"Erro traducao: {e}")
