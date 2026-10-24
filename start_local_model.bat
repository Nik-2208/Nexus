@echo off
setlocal enabledelayedexpansion

REM NEXUS: Launch Local Gemma 4 Model Server via llama-server on Loopback (127.0.0.1:8080)
set "MODEL_PATH=%~dp0google_gemma-4-E2B-it-Q4_0.gguf"
set "LOG_PATH=%~dp0llama_server.log"

if not exist "!MODEL_PATH!" (
    echo [ERROR] Model GGUF file not found at: !MODEL_PATH!
    pause
    exit /b 1
)

REM 1. Look for llama-server in WinGet installation path or on PATH
set "LLAMA_SERVER_EXE="

if exist "%LOCALAPPDATA%\Microsoft\WinGet\Packages\ggml.llamacpp_Microsoft.Winget.Source_8wekyb3d8bbwe\llama-server.exe" (
    set "LLAMA_SERVER_EXE=%LOCALAPPDATA%\Microsoft\WinGet\Packages\ggml.llamacpp_Microsoft.Winget.Source_8wekyb3d8bbwe\llama-server.exe"
) else (
    where llama-server.exe >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        for /f "delims=" %%i in ('where llama-server.exe') do (
            if not defined LLAMA_SERVER_EXE set "LLAMA_SERVER_EXE=%%i"
        )
    )
)

if not defined LLAMA_SERVER_EXE (
    echo [ERROR] llama-server.exe was not found.
    echo Please install llama.cpp via: winget install --id ggml.llamacpp
    pause
    exit /b 1
)

echo ===============================================================================
echo [NEXUS LOCAL INFERENCE LAUNCHER]
echo Executable: !LLAMA_SERVER_EXE!
echo Model File: !MODEL_PATH!
echo Target URL: http://127.0.0.1:8080/v1
echo Log File:   !LOG_PATH!
echo Settings:   4 CPU threads, 2048 context window, loopback binding
echo ===============================================================================

"!LLAMA_SERVER_EXE!" -m "!MODEL_PATH!" --host 127.0.0.1 --port 8080 -c 2048 -t 4 --log-file "!LOG_PATH!"
