@echo off
rem Executa o Frentes no modo de uso local (docs/06-arquitetura.md §11):
rem na primeira vez baixa o que faltar (uv e Node.js portátil, sem administrador),
rem gera o build do front-end e inicia o app em http://127.0.0.1:8765.
chcp 65001 >nul
setlocal
cd /d "%~dp0"

rem Onde ficam as ferramentas baixadas pelo scripts\preparar.ps1. No fim do PATH: o que
rem já estiver instalado no computador tem preferência.
set "PATH=%PATH%;%USERPROFILE%\.local\bin;%CD%\.ferramentas\node"

where uv >nul 2>nul && where npm >nul 2>nul || (
  echo Preparando o computador para o Frentes (só na primeira vez; precisa de internet^)...
  powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\preparar.ps1" || goto :erro
)
where uv >nul 2>nul || (
  echo O uv não foi instalado. Instale manualmente em https://docs.astral.sh/uv/
  goto :erro
)
where npm >nul 2>nul || (
  echo O Node.js não foi instalado. Instale a versão LTS em https://nodejs.org/
  goto :erro
)

if not exist "frontend\node_modules\" (
  echo Instalando as dependências do front-end...
  call npm --prefix frontend ci || goto :erro
)

echo Gerando o front-end...
call npm --prefix frontend run build || goto :erro

rem Na primeira vez, o uv também baixa o Python e as dependências do back-end.
echo Iniciando o Frentes. Feche esta janela ou use Ctrl+C para encerrar.
uv run --directory backend frentes
if errorlevel 1 goto :erro
exit /b 0

:erro
echo.
echo Não foi possível iniciar o Frentes. Veja a mensagem acima.
pause
exit /b 1
