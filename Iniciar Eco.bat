@echo off
REM Iniciar Eco.bat
REM Duplo-clique aqui para abrir o Eco (backend + interface).
REM Na primeira vez, instala tudo sozinho (pode demorar alguns minutos).

cd /d "%~dp0frontend"

if not exist node_modules (
    echo ==========================================================
    echo  Primeira execucao: instalando dependencias do frontend
    echo  Isso pode demorar alguns minutos. Nao feche esta janela.
    echo ==========================================================
    call npm install
    call npm approve-scripts electron
    call npm rebuild electron
)

if not exist "..\backend\.env" (
    echo Criando arquivo .env padrao...
    copy "..\backend\.env.example" "..\backend\.env" >nul
)

echo.
echo Verificando dependencias do Python...
pip install -r "..\backend\requirements.txt" --quiet --disable-pip-version-check

echo.
echo Iniciando o Eco...
call npm start

echo.
echo Janela do Eco fechada. Pressione qualquer tecla para sair.
pause >nul
