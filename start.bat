@echo off
echo ========================================
echo   Live Audio Translator - Iniciando...
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Baixe em https://python.org e marque "Add Python to PATH"
    pause
    exit /b
)

python -c "import sounddevice" >nul 2>&1
if errorlevel 1 (
    echo Instalando dependencias...
    pip install sounddevice numpy SpeechRecognition anthropic
    echo.
)

python translator.py
pause
