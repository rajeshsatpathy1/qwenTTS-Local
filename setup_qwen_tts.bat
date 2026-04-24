@echo off
setlocal

REM Local setup for Qwen3-TTS on Windows
REM Requires: conda installed and available in PATH

set ENV_NAME=qwen3-tts

echo Creating conda environment %ENV_NAME% with Python 3.12...
call conda create -n %ENV_NAME% python=3.12 -y
if errorlevel 1 goto :fail

echo Activating environment...
call conda activate %ENV_NAME%
if errorlevel 1 goto :fail

echo Installing project requirements...
pip install -U -r requirements.txt
if errorlevel 1 goto :fail

echo.
echo Setup complete.
echo.
echo Next steps:
echo   1. conda activate %ENV_NAME%
echo   2. cd /d "%~dp0"
echo   3. python narrate_dialogue.py samples\inputs\quickstart_dialogue.txt --characters samples\inputs\quickstart_characters.json --model-size 0.6B --output-dir output_quickstart --merge-output
echo.
echo Notes:
echo   - Use 0.6B first on an 8-16 GB VRAM GPU.
echo   - If you later want better quality and have enough VRAM, switch to --model-size 1.7B.
echo   - On Windows, FlashAttention 2 is often unavailable; the script falls back automatically.
echo   - If Hugging Face prompts for access, run: huggingface-cli login
goto :eof

:fail
echo.
echo Setup failed. Review the error above.
exit /b 1
