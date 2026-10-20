# Baixa o que falta para rodar o Frentes pelo código-fonte (chamado pelo executar.bat).
# Tudo sem administrador:
#   - uv: instalador oficial, na pasta do usuário (o uv baixa o Python sozinho depois);
#   - Node.js: versão LTS portátil, dentro de .ferramentas\node neste projeto (não mexe no sistema).
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
# Windows antigos ainda negociam TLS 1.0 por padrão; os sites abaixo exigem 1.2.
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$raiz = Split-Path -Parent $PSScriptRoot

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host 'Baixando o uv (ele cuida do Python)...'
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    $ferramentas = Join-Path $raiz '.ferramentas'
    $arquitetura = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { 'arm64' } else { 'x64' }
    # Numa variável primeiro: no PowerShell 5.1 o Invoke-RestMethod passa a lista inteira como um
    # objeto só pelo pipe; guardada, ela é percorrida item a item. A primeira LTS é a mais nova.
    $versoes = Invoke-RestMethod https://nodejs.org/dist/index.json
    $versao = ($versoes | Where-Object { $_.lts } | Select-Object -First 1).version
    $nome = "node-$versao-win-$arquitetura"
    Write-Host "Baixando o Node.js $versao (portátil, em .ferramentas\node)..."
    $zip = Join-Path $env:TEMP "$nome.zip"
    Invoke-WebRequest "https://nodejs.org/dist/$versao/$nome.zip" -OutFile $zip
    New-Item -ItemType Directory -Force $ferramentas | Out-Null
    $destino = Join-Path $ferramentas 'node'
    if (Test-Path $destino) { Remove-Item -Recurse -Force $destino }
    Expand-Archive $zip -DestinationPath $ferramentas -Force
    Rename-Item (Join-Path $ferramentas $nome) 'node'
    Remove-Item $zip
}
