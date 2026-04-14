import threading
import queue
import tkinter as tk
from tkinter import scrolledtext, messagebox

from ..constants import COLORS, CAPTION_SRC_LANGUAGES
from ..config import hex_to_rgba
from ..recognizer import WHISPER_OK, SOUNDDEVICE_OK, SR_OK, load_whisper_model, RecognizerEngine
from ..translation import Translator
from ..caption_server import CaptionServer, CAPTION_HTML_TEMPLATE
from .setup_caption import CaptionSetupWindow


class CaptionApp:
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
        self._current_text  = ""
        self._text_version  = 0
        self._server: CaptionServer | None = None
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
            self._set_status("idle", "Pronto")

        threading.Thread(target=_load, daemon=True).start()

    # ── UI ───────────────────────────────────────────────────────────────────
    def _build(self):
        self.root.title("Live Translator — Legenda")
        self.root.geometry("700x660")
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

        tk.Label(hdr, text="🎤  Modo Legenda",
                 font=("Segoe UI", 14, "bold"),
                 bg=COLORS["surface"], fg=COLORS["text"]).pack(side="left", padx=10)

        src  = self.cfg.get("src_lang", "")
        tgt  = self.cfg.get("tgt_lang", "Sem traducao")
        info = CAPTION_SRC_LANGUAGES.get(src, {})
        lbl  = f"{info.get('flag', '')} {src}"
        if tgt != "Sem traducao":
            lbl += f"  →  {tgt}"
        tk.Label(hdr, text=lbl, font=("Segoe UI", 11),
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

        # Browser Source info
        port    = self.cfg.get("port", 5050)
        url_str = f"http://localhost:{port}"

        obs = tk.Frame(self.root, bg=COLORS["surface"],
                       highlightthickness=1, highlightbackground=COLORS["border"])
        obs.pack(fill="x", padx=20, pady=(0, 8))

        url_row = tk.Frame(obs, bg=COLORS["surface"])
        url_row.pack(fill="x", padx=16, pady=(10, 6))
        tk.Label(url_row, text="Browser Source URL:",
                 font=("Segoe UI", 10, "bold"),
                 bg=COLORS["surface"], fg=COLORS["muted"]).pack(side="left")
        url_entry = tk.Entry(url_row, font=("Segoe UI", 11),
                             bg=COLORS["surface2"], fg=COLORS["accent"],
                             insertbackground=COLORS["text"],
                             relief="flat", highlightthickness=0,
                             state="readonly", width=28)
        url_entry.pack(side="left", padx=8)
        url_entry.insert(0, url_str)

        tk.Button(url_row, text="Copiar", font=("Segoe UI", 9),
                  bg=COLORS["accent2"], fg="white",
                  relief="flat", cursor="hand2", padx=8, pady=2,
                  command=lambda: (self.root.clipboard_clear(),
                                   self.root.clipboard_append(url_str))).pack(side="left")

        tk.Label(obs,
                 text="No OBS: Fontes → + → Browser  ·  Cole a URL  ·  "
                      "Largura: 1920  Altura: 200  ·  Marque 'Fundo transparente'",
                 font=("Segoe UI", 9),
                 bg=COLORS["surface"], fg=COLORS["muted"],
                 wraplength=640, justify="left").pack(anchor="w", padx=16, pady=(0, 10))

        panels = tk.Frame(self.root, bg=COLORS["bg"])
        panels.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        tk.Label(panels, text="TRANSCRICAO", font=("Segoe UI", 9, "bold"),
                 bg=COLORS["bg"], fg=COLORS["muted"]).pack(anchor="w", pady=(0, 4))

        self.orig_box = scrolledtext.ScrolledText(
            panels, font=("Segoe UI", 12), wrap="word",
            relief="flat", bd=0, bg=COLORS["orig_bg"], fg=COLORS["text"],
            insertbackground=COLORS["text"],
            highlightthickness=1, highlightbackground=COLORS["border"],
            state="disabled", height=6)
        self.orig_box.pack(fill="both", expand=True)

        if tgt != "Sem traducao":
            tk.Label(panels, text=f"TRADUCAO ({tgt.upper()})",
                     font=("Segoe UI", 9, "bold"),
                     bg=COLORS["bg"], fg=COLORS["accent"]).pack(anchor="w", pady=(12, 4))
            self.trans_box = scrolledtext.ScrolledText(
                panels, font=("Segoe UI", 12), wrap="word",
                relief="flat", bd=0, bg=COLORS["trans_bg"], fg=COLORS["trans_fg"],
                insertbackground=COLORS["trans_fg"],
                highlightthickness=1, highlightbackground=COLORS["accent2"],
                state="disabled", height=6)
            self.trans_box.pack(fill="both", expand=True)
        else:
            self.trans_box = None

    def _center(self):
        self.root.update_idletasks()
        w, h = 700, 660
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
        if box is None:
            return
        def do():
            box.config(state="normal")
            box.insert("end", text + "\n\n")
            box.see("end")
            box.config(state="disabled")
        self.root.after(0, do)

    def _set_caption(self, text: str):
        self._current_text = text
        self._text_version += 1

    def _clear(self):
        self._set_caption("")
        for box in (self.orig_box, self.trans_box):
            if box is None:
                continue
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
        CaptionSetupWindow(self.root, self.cfg,
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
            messagebox.showerror("Erro", "Dispositivo invalido. Reconfigure.")
            return

        # Inicia servidor HTTP
        port = self.cfg.get("port", 5050)
        html = self._build_html()
        self._server = CaptionServer(
            port,
            lambda: {"text": self._current_text, "version": self._text_version},
            html,
        )
        if not self._server.start():
            messagebox.showerror("Erro",
                f"Nao foi possivel iniciar o servidor na porta {port}.\n"
                "Verifique se outra instancia esta rodando ou escolha outra porta.")
            self._server = None
            return

        self.is_running = True
        self.btn_start.config(text="⏹  Parar", bg=COLORS["error"],
                               activebackground="#c04040")
        self._set_status("running", "Ouvindo...")
        self._translator.set_status_callback(self._set_status)

        src_lang  = self.cfg.get("src_lang", "Portugues")
        lang_info = CAPTION_SRC_LANGUAGES.get(src_lang, {})
        lang_code = lang_info.get("code", "pt-BR")
        tgt       = self.cfg.get("tgt_lang", "Sem traducao")

        def on_text(text: str):
            self._append(self.orig_box, text)
            if tgt == "Sem traducao":
                self._set_caption(text)
            else:
                self.trans_queue.put(text)

        self._recognizer = RecognizerEngine(
            device_index = device_index,
            lang_code    = lang_code,
            get_whisper  = lambda: self._whisper,
            on_text      = on_text,
            set_status   = self._set_status,
        )
        self._recognizer.start()

        if tgt != "Sem traducao":
            threading.Thread(target=self._translate_loop, daemon=True).start()

    def _stop(self):
        self.is_running = False
        if self._recognizer:
            self._recognizer.stop()
            self._recognizer = None
        if self._server:
            self._server.stop()
            self._server = None
        try:
            self.btn_start.config(text="▶  Iniciar", bg=COLORS["accent"],
                                   activebackground=COLORS["accent2"])
        except Exception:
            pass
        self._set_status("idle", "Parado")

    def _on_close(self):
        self._stop()
        self.root.destroy()

    def _build_html(self) -> str:
        return (CAPTION_HTML_TEMPLATE
                .replace("__FONT_SIZE__",  str(self.cfg.get("font_size",  48)))
                .replace("__TEXT_COLOR__", self.cfg.get("text_color", "#ffffff"))
                .replace("__BG_RGBA__",    hex_to_rgba(
                    self.cfg.get("bg_color", "#000000"),
                    self.cfg.get("bg_opacity", 0.65))))

    # ── Traducao ──────────────────────────────────────────────────────────────
    def _translate_loop(self):
        src_info = CAPTION_SRC_LANGUAGES.get(self.cfg.get("src_lang", "Portugues"), {})
        src_code = src_info.get("src", "pt")
        tgt_lang = self.cfg.get("tgt_lang", "Sem traducao")

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
                self._set_caption(result)
                self._set_status("running", "Ouvindo...")
            except Exception as e:
                self._set_status("error", f"Erro traducao: {e}")
