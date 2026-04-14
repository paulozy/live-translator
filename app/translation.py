"""
Traducao de texto: Helsinki-NLP (local) com fallback para Google Translate.
Exporta: HELSINKI_OK, Translator
"""

from urllib import request as _urlrequest, parse as _urlparse
import json as _json

try:
    from transformers import MarianMTModel, MarianTokenizer
    HELSINKI_OK = True
except ImportError:
    HELSINKI_OK = False

from .constants import HELSINKI_MODELS

# Mapa de nome de idioma -> codigo ISO
_TGT_MAP = {
    "Ingles":    "en",
    "Portugues": "pt",
    "Espanhol":  "es",
    "Frances":   "fr",
    "Alemao":    "de",
}


class Translator:
    """
    Traduz texto usando Helsinki-NLP quando disponivel, com pivot via ingles
    para portugues e fallback para Google Translate.

    Uso:
        t = Translator(set_status=self._set_status)
        result = t.translate(text, src_code="ko", tgt_lang="Portugues")
    """

    def __init__(self, set_status=None):
        self._model_cache: dict = {}
        self._set_status = set_status or (lambda state, msg: None)

    def set_status_callback(self, cb) -> None:
        """Atualiza o callback de status (chamado apos o modelo Whisper carregar)."""
        self._set_status = cb

    def translate(self, text: str, src_code: str, tgt_lang: str) -> str:
        """
        src_code : codigo ISO do idioma de origem (ex: "ko", "pt", "en")
        tgt_lang : nome do idioma destino (ex: "Portugues", "Ingles") ou "Sem traducao"
        """
        tgt_code = _TGT_MAP.get(tgt_lang)
        if not tgt_code or tgt_code == src_code:
            return text

        # Modelo Helsinki direto
        m_name = HELSINKI_MODELS.get((src_code, tgt_code))
        if m_name and HELSINKI_OK:
            m, t = self._load_model(m_name)
            return self._run_model(text, m, t)

        # Pivot: src -> en -> pt
        if tgt_code == "pt" and src_code != "en" and HELSINKI_OK:
            m1_name = HELSINKI_MODELS.get((src_code, "en"))
            m2_name = HELSINKI_MODELS.get(("en", "pt"))
            if m1_name and m2_name:
                m1, t1  = self._load_model(m1_name)
                english = self._run_model(text, m1, t1)
                m2, t2  = self._load_model(m2_name)
                return self._run_model(english, m2, t2)

        # Fallback Google Translate
        return self._google_translate(text, src_code, tgt_code)

    # ── Internos ──────────────────────────────────────────────────────────────
    def _load_model(self, model_name: str):
        if model_name not in self._model_cache:
            short = model_name.split("/")[-1]
            self._set_status("loading", f"Baixando {short}...")
            tok   = MarianTokenizer.from_pretrained(model_name)
            model = MarianMTModel.from_pretrained(model_name)
            self._model_cache[model_name] = (model, tok)
        return self._model_cache[model_name]

    def _run_model(self, text: str, model, tok) -> str:
        inputs = tok([text], return_tensors="pt", padding=True,
                     truncation=True, max_length=512)
        out = model.generate(**inputs)
        return tok.decode(out[0], skip_special_tokens=True)

    def _google_translate(self, text: str, src_code: str, tgt_code: str) -> str:
        url    = "https://translate.googleapis.com/translate_a/single"
        params = _urlparse.urlencode({
            "client": "gtx", "sl": src_code, "tl": tgt_code, "dt": "t", "q": text
        })
        req = _urlrequest.Request(
            f"{url}?{params}", headers={"User-Agent": "Mozilla/5.0"})
        with _urlrequest.urlopen(req, timeout=10) as resp:
            data = _json.loads(resp.read().decode("utf-8"))
        return "".join(seg[0] for seg in data[0] if seg[0])
