@echo off
rem Executa o Frentes no modo de uso local (docs/06-arquitetura.md §11):
rem gera o build do front-end e inicia o app em http://127.0.0.1:8765.
chcp 65001 >nul
setlocal
cd /d "%~dp0"

where uv >nul 2>nul || (
  echo O uv não foi encontrado. Instale em https://docs.astral.sh/uv/
  goto :erro
)
where npm >nul 2>nul || (
  echo O Node.js não foi encontrado. Instale a versão LTS em https://nodejs.org/
  goto :erro
)

if not exist "frontend\node_modules\" (
  echo Instalando as dependências do front-end...
  call npm --prefix frontend ci || goto :erro
)

echo Gerando o front-end...
call npm --prefix frontend run build || goto :erro

echo Iniciando o Frentes. Feche esta janela ou use Ctrl+C para encerrar.
uv run --directory backend frentes
if errorlevel 1 goto :erro
exit /b 0

:erro
echo.
echo Não foi possível iniciar o Frentes. Veja a mensagem acima.
pause
exit /b 1
