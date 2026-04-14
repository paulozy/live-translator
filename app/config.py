"""
Persistencia de configuracao em JSON e utilitarios de cor.
"""

import os
import json

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".live_translator_config.json")


def load_config() -> dict:
    """Carrega config do disco. Migra formato antigo (plano) para o novo (aninhado)."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                cfg = json.load(f)
            # Migracao: formato antigo -> novo
            if "src_lang" in cfg and "mode" not in cfg:
                old = {k: cfg[k] for k in ("src_lang", "tgt_lang", "device") if k in cfg}
                return {"mode": "translator", "translator": old, "caption": {}}
            return cfg
        except Exception:
            pass
    return {"mode": None, "translator": {}, "caption": {}}


def save_config(data: dict) -> None:
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def hex_to_rgba(hex_color: str, opacity: float) -> str:
    """Converte '#rrggbb' + opacity (0.0–1.0) para 'rgba(r,g,b,a)'."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{opacity:.2f})"
