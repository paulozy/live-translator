"""
Reconhecimento de fala: faster-whisper local (preferencial) ou Google Speech (fallback).
Exporta: WHISPER_OK, SR_OK, SOUNDDEVICE_OK, load_whisper_model, RecognizerEngine
"""

import io
import re
import wave
import time
import queue
import threading
import collections

# ── Imports opcionais ─────────────────────────────────────────────────────────
try:
    from faster_whisper import WhisperModel as _WhisperModel
    WHISPER_OK = True
except ImportError:
    WHISPER_OK = False

try:
    import sounddevice as sd
    import numpy as np
    SOUNDDEVICE_OK = True
except ImportError:
    SOUNDDEVICE_OK = False

try:
    import speech_recognition as sr
    SR_OK = True
except ImportError:
    SR_OK = False

from .constants import SAMPLE_RATE, CHUNK_SECONDS, CHANNELS

# ── Cache de modelos faster-whisper ──────────────────────────────────────────
_CACHE: dict = {}
_LOCK         = threading.Lock()

# Regex: remove tokens de ruido/silencio gerados pelo Whisper
_JUNK_RE = re.compile(
    r'\[.*?\]'           # [MUSIC], [APPLAUSE], [BLANK_AUDIO], etc.
    r'|\(.*?\)'          # (Music), (Applause), etc.
    r'|♪.*?♪'           # notas musicais
    r'|Subtitles by.*$'  # creditos de legenda
    r'|^\s*\.\s*$',      # so um ponto
    re.IGNORECASE | re.DOTALL,
)

# Frases que o Whisper alucina frequentemente em silencio
_HALLUCINATION_BLACKLIST = {
    "thank you",
    "thank you.",
    "thanks for watching",
    "thanks for watching.",
    "subscribe",
    "you",
    "you.",
}

# Volume RMS minimo para considerar audio como fala
_RMS_THRESHOLD = 0.01


def load_whisper_model(name: str):
    """Carrega e cacheia o modelo faster-whisper com quantizacao int8 (thread-safe)."""
    with _LOCK:
        if name not in _CACHE:
            _CACHE[name] = _WhisperModel(name, device="cpu", compute_type="int8")
        return _CACHE[name]


def _clean(text: str) -> str:
    return _JUNK_RE.sub("", text).strip()


def _is_hallucination(text: str, prev_text: str) -> bool:
    """
    Retorna True se o texto parecer uma alucinacao do Whisper.
    Checa: blacklist, repeticao interna e similaridade com texto anterior.
    """
    lower = text.strip().lower()

    # 1. Blacklist de frases conhecidas
    if lower in _HALLUCINATION_BLACKLIST:
        return True

    # 2. Repeticao interna: mesmo segmento aparece 3+ vezes
    words = text.strip().split()
    if len(words) >= 6:
        mid = len(words) // 3
        chunk_a = " ".join(words[:mid]).lower()
        chunk_b = " ".join(words[mid:mid * 2]).lower()
        if chunk_a == chunk_b:
            return True

    # 3. Similaridade > 80% com o texto anterior
    if prev_text:
        prev_words = set(prev_text.lower().split())
        curr_words = set(lower.split())
        if prev_words and len(curr_words) > 0:
            overlap = len(prev_words & curr_words) / len(prev_words)
            if overlap > 0.8:
                return True

    return False


def _ndarray_to_wav(audio_np) -> io.BytesIO:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_np.tobytes())
    buf.seek(0)
    return buf


class RecognizerEngine:
    """
    Captura audio do dispositivo e transcreve em chunks.

    Parametros:
        device_index   : indice do dispositivo sounddevice
        lang_code      : codigo BCP-47 para fallback Google Speech (ex: "pt-BR")
        get_whisper    : callable() -> modelo faster-whisper carregado ou None
        on_text        : callable(str) chamado a cada transcricao nova
        set_status     : callable(state, msg) para atualizar a UI
    """

    def __init__(self, device_index: int, lang_code: str,
                 get_whisper, on_text, set_status):
        self._device_index = device_index
        self._lang_code    = lang_code
        self._get_whisper  = get_whisper
        self._on_text      = on_text
        self._set_status   = set_status
        self._running      = False
        self._audio_queue: queue.Queue = queue.Queue()

    def start(self) -> None:
        self._running = True
        threading.Thread(target=self._capture_loop,   daemon=True).start()
        threading.Thread(target=self._recognize_loop, daemon=True).start()

    def stop(self) -> None:
        self._running = False

    # ── Captura ──────────────────────────────────────────────────────────────
    def _capture_loop(self) -> None:
        collected = []

        def cb(indata, frames, time_info, status):
            collected.append(indata.copy())

        with sd.InputStream(device=self._device_index, channels=CHANNELS,
                            samplerate=SAMPLE_RATE, dtype="int16",
                            callback=cb, blocksize=2048):
            while self._running:
                time.sleep(CHUNK_SECONDS)
                if collected:
                    chunk = np.concatenate(collected, axis=0)
                    collected.clear()
                    self._audio_queue.put(chunk)

    # ── Reconhecimento ────────────────────────────────────────────────────────
    def _recognize_loop(self) -> None:
        buf          = collections.deque(maxlen=2)   # 2 chunks × 3s = 6s de contexto
        prev_text    = ""
        whisper_lang = self._lang_code.split("-")[0]  # "pt-BR" → "pt"
        recognizer   = sr.Recognizer() if SR_OK else None

        while self._running:
            try:
                chunk = self._audio_queue.get(timeout=1)
            except queue.Empty:
                continue

            buf.append(chunk)
            text  = ""
            model = self._get_whisper()

            if WHISPER_OK and model:
                audio_f32 = (np.concatenate(list(buf), axis=0)
                               .flatten().astype(np.float32) / 32768.0)
                rms = float(np.sqrt(np.mean(audio_f32 ** 2)))
                if rms < _RMS_THRESHOLD:
                    continue
                try:
                    segments, _ = model.transcribe(
                        audio_f32,
                        language=whisper_lang,
                        vad_filter=True,
                        condition_on_previous_text=False,
                        no_speech_threshold=0.8,
                        temperature=0,
                        beam_size=5,
                    )
                    text = _clean(" ".join(s.text for s in segments))
                except Exception as e:
                    self._set_status("error", str(e))
                    continue

            elif SR_OK and recognizer:
                try:
                    wav = _ndarray_to_wav(chunk)
                    with sr.AudioFile(wav) as src:
                        data = recognizer.record(src)
                    text = recognizer.recognize_google(data, language=self._lang_code)
                except sr.UnknownValueError:
                    continue
                except sr.RequestError as e:
                    self._set_status("error", f"Erro Google Speech: {e}")
                    continue
                except Exception as e:
                    self._set_status("error", str(e))
                    continue
            else:
                self._set_status("error", "Nenhum reconhecedor disponivel")
                break

            if text and not _is_hallucination(text, prev_text):
                prev_text = text
                self._on_text(text)
