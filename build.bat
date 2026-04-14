@echo off
echo ========================================
echo   Live Translator - Gerando .exe
echo ========================================
echo.

:: Tenta encontrar o Python de varias formas
set PYTHON=
for %%p in (python.exe py.exe python3.exe) do (
    if not defined PYTHON (
        where %%p >nul 2>&1 && set PYTHON=%%p
    )
)

:: Se nao achou pelo PATH, procura nos locais padrao de instalacao
if not defined PYTHON (
    for %%d in (
        "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python39\python.exe"
        "C:\Python313\python.exe"
        "C:\Python312\python.exe"
        "C:\Python311\python.exe"
        "C:\Python310\python.exe"
    ) do (
        if not defined PYTHON (
            if exist %%d set PYTHON=%%d
        )
    )
)

if not defined PYTHON (
    echo.
    echo ERRO: Python nao encontrado!
    echo.
    echo 1. Baixe em https://python.org
    echo 2. Durante a instalacao, marque "Add python.exe to PATH"
    echo 3. Feche esta janela e abra novamente
    echo.
    pause
    exit /b 1
)

echo Python encontrado: %PYTHON%
echo.

echo [1/3] Instalando dependencias...
%PYTHON% -m pip install --upgrade pip
%PYTHON% -m pip install faster-whisper sounddevice numpy SpeechRecognition
%PYTHON% -m pip install transformers sentencepiece
%PYTHON% -m pip install torch --index-url https://download.pytorch.org/whl/cpu
%PYTHON% -m pip install pyinstaller
if errorlevel 1 (
    echo.
    echo ERRO ao instalar dependencias. Verifique sua conexao com a internet.
    pause
    exit /b 1
)

echo.
echo [2/3] Gerando executavel (pode demorar 10-20 minutos)...
%PYTHON% -m PyInstaller ^
    --noconfirm ^
    --onedir ^
    --windowed ^
    --name "LiveTranslator" ^
    --icon "app/assets/icon.ico" ^
    --hidden-import="faster_whisper" ^
    --hidden-import="ctranslate2" ^
    --hidden-import="sounddevice" ^
    --hidden-import="speech_recognition" ^
    --hidden-import="transformers" ^
    --hidden-import="sentencepiece" ^
    --collect-all faster_whisper ^
    --collect-all ctranslate2 ^
    --collect-all tokenizers ^
    --collect-all huggingface_hub ^
    --collect-all transformers ^
    --collect-all sentencepiece ^
    translator.py

if errorlevel 1 (
    echo.
    echo ERRO ao gerar executavel.
    pause
    exit /b 1
)

echo.
echo ========================================
echo [3/3] Pronto!
echo ========================================
echo.
echo O executavel esta em: dist\LiveTranslator\LiveTranslator.exe
echo.
echo Compacte a pasta dist\LiveTranslator\ em ZIP para distribuir.
echo Na primeira execucao os modelos serao baixados automaticamente.
echo.
pause