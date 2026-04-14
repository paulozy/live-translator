"""
Classe App: gerencia a navegacao entre telas e persiste o config.
"""

import tkinter as tk
from ..config import load_config, save_config
from .mode_select import ModeSelectWindow
from .setup_translator import SetupWindow
from .setup_caption import CaptionSetupWindow
from .translator_app import TranslatorApp
from .caption_app import CaptionApp


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.cfg  = load_config()
        self._show_mode_select()
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.root.destroy()

    def _clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    # ── Selecao de modo ───────────────────────────────────────────────────────
    def _show_mode_select(self):
        self._clear()
        ModeSelectWindow(self.root, self.cfg.get("mode"), self._on_mode_selected)

    def _on_mode_selected(self, mode: str):
        self.cfg["mode"] = mode
        save_config(self.cfg)
        self._clear()
        if mode == "translator":
            tcfg = self.cfg.get("translator", {})
            if all(k in tcfg for k in ("src_lang", "tgt_lang", "device")):
                TranslatorApp(self.root, tcfg, on_back=self._show_mode_select)
            else:
                SetupWindow(self.root, tcfg,
                            on_complete=self._on_translator_setup,
                            on_back=self._show_mode_select)
        else:
            ccfg = self.cfg.get("caption", {})
            if all(k in ccfg for k in ("src_lang", "tgt_lang", "device")):
                CaptionApp(self.root, ccfg, on_back=self._show_mode_select)
            else:
                CaptionSetupWindow(self.root, ccfg,
                                   on_complete=self._on_caption_setup,
                                   on_back=self._show_mode_select)

    def _on_translator_setup(self, tcfg: dict):
        self.cfg["translator"] = tcfg
        save_config(self.cfg)
        self._clear()
        TranslatorApp(self.root, tcfg, on_back=self._show_mode_select)

    def _on_caption_setup(self, ccfg: dict):
        self.cfg["caption"] = ccfg
        save_config(self.cfg)
        self._clear()
        CaptionApp(self.root, ccfg, on_back=self._show_mode_select)
