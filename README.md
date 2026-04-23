olá paulo, estou editando do codex

# Live Translator

Captura áudio do sistema (lives, vídeos, chamadas) e transcreve + traduz em tempo real usando Whisper local.

Dois modos:
- **Tradutor** — janela com texto original e tradução lado a lado
- **Legenda (OBS)** — browser source transparente para usar no OBS Studio

---

## Download

Acesse a [página de releases](../../releases) e baixe o arquivo `LiveTranslator-vX.X.X-windows.zip`.

1. Extraia em qualquer pasta
2. Execute `LiveTranslator.exe`

> Na primeira execução o modelo Whisper será baixado automaticamente (~500 MB para `small`, ~1.5 GB para `medium`).

---

## Requisitos

- Windows 10 64-bit ou superior
- Conexão com internet (apenas no primeiro uso, para baixar o modelo)

---

## Captura de áudio do sistema

Para capturar o que está tocando no PC (live, YouTube, etc.):

**Opção 1 — Stereo Mix (nativo)**
1. Botão direito no ícone de som → **Sons**
2. Aba **Gravação** → botão direito em área vazia → **Mostrar dispositivos desabilitados**
3. Botão direito em **Stereo Mix** → **Habilitar** → **Definir como padrão**

**Opção 2 — VB-Audio Virtual Cable (se não tiver Stereo Mix)**
- Instale gratuitamente em https://vb-audio.com/Cable
- Selecione **CABLE Output** como dispositivo no app

---

## Modo Legenda (OBS)

1. No app, selecione **Modo Legenda** e configure
2. Clique em **▶ Iniciar**
3. No OBS: **Fontes → + → Browser**
   - URL: `http://localhost:5050`
   - Largura: `1920` · Altura: `200`
   - Marque **Fundo transparente**

---

## Modelos Whisper

| Modelo | Tamanho | Velocidade | Qualidade |
|--------|---------|------------|-----------|
| tiny   | ~75 MB  | Muito rápido | Básica |
| base   | ~145 MB | Rápido | Razoável |
| small  | ~500 MB | Moderado | **Recomendado** |
| medium | ~1.5 GB | Lento | Máxima |

---

## Problemas comuns

| Problema | Solução |
|----------|---------|
| Nenhum dispositivo aparece | Habilite Stereo Mix (veja acima) |
| Transcrição em idioma errado | Selecione o idioma correto nas configurações |
| Texto não aparece | Aumente o volume da fonte de áudio |
| Erro ao iniciar servidor | Verifique se a porta 5050 está livre |
