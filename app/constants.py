"""
Constantes globais: idiomas, modelos, paleta de cores.
"""

SAMPLE_RATE   = 16000
CHUNK_SECONDS = 3
CHANNELS      = 1

WHISPER_MODELS = {
    "tiny":   "~75 MB  · muito rapido · menor precisao",
    "base":   "~145 MB · rapido · precisao basica",
    "small":  "~465 MB · moderado · alta precisao  (recomendado)",
    "medium": "~1.5 GB · lento · precisao maxima",
}

# Idiomas suportados no Modo Tradutor (origem)
LANGUAGES = {
    "Coreano": {"code": "ko-KR", "flag": "🇰🇷", "src": "ko"},
    "Japones": {"code": "ja-JP", "flag": "🇯🇵", "src": "ja"},
    "Chines":  {"code": "zh-CN", "flag": "🇨🇳", "src": "zh"},
}

TARGET_LANGUAGES = ["Ingles", "Portugues"]

# Idiomas suportados no Modo Legenda (fala do streamer)
CAPTION_SRC_LANGUAGES = {
    "Portugues": {"code": "pt-BR", "flag": "🇧🇷", "src": "pt"},
    "Ingles":    {"code": "en-US", "flag": "🇺🇸", "src": "en"},
    "Espanhol":  {"code": "es-ES", "flag": "🇪🇸", "src": "es"},
    "Frances":   {"code": "fr-FR", "flag": "🇫🇷", "src": "fr"},
    "Alemao":    {"code": "de-DE", "flag": "🇩🇪", "src": "de"},
    "Italiano":  {"code": "it-IT", "flag": "🇮🇹", "src": "it"},
    "Russo":     {"code": "ru-RU", "flag": "🇷🇺", "src": "ru"},
    "Japones":   {"code": "ja-JP", "flag": "🇯🇵", "src": "ja"},
    "Coreano":   {"code": "ko-KR", "flag": "🇰🇷", "src": "ko"},
    "Chines":    {"code": "zh-CN", "flag": "🇨🇳", "src": "zh"},
}

CAPTION_TGT_LANGUAGES = ["Sem traducao", "Ingles", "Portugues", "Espanhol", "Frances"]

# Modelos Helsinki-NLP disponíveis (pares de idiomas)
HELSINKI_MODELS = {
    ("ko", "en"): "Helsinki-NLP/opus-mt-ko-en",
    ("ja", "en"): "Helsinki-NLP/opus-mt-ja-en",
    ("zh", "en"): "Helsinki-NLP/opus-mt-zh-en",
    ("en", "pt"): "Helsinki-NLP/opus-mt-tc-big-en-pt",
}

COLORS = {
    "bg":       "#0f0f0f",
    "surface":  "#1a1a1a",
    "surface2": "#242424",
    "border":   "#2e2e2e",
    "accent":   "#7c6af7",
    "accent2":  "#5b4fd4",
    "text":     "#f0f0f0",
    "muted":    "#888888",
    "orig_bg":  "#141414",
    "trans_bg": "#13131f",
    "trans_fg": "#a89eff",
    "success":  "#4caf82",
    "warning":  "#f0a050",
    "error":    "#e05555",
}
