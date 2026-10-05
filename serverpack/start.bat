@echo off
REM Brasshaven @VERSION@ server - Minecraft @MINECRAFT@, Forge @FORGE@, Java 25.
REM First run: installs Forge, asks you to accept the Minecraft EULA, then starts the server.
REM Every run: copies the default configs if missing, backs the world up when the Brasshaven version changed,
REM and starts with the JVM flags of jvm_args.txt (RAM: edit -Xms/-Xmx there).
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "FORGE=@FORGE@"
set "JAR=@JAR@"
set "ARGS=libraries\net\minecraftforge\forge\%FORGE%\win_args.txt"

where java >nul 2>nul
if errorlevel 1 (
    echo Java 25 est introuvable / Java 25 not found: https://adoptium.net/temurin/releases/?version=25
    goto :fail
)

REM 1. Forge (once)
if not exist "%ARGS%" (
    echo == Installation de Forge %FORGE% / installing Forge %FORGE%
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -UseBasicParsing -Uri 'https://maven.minecraftforge.net/net/minecraftforge/forge/%FORGE%/forge-%FORGE%-installer.jar' -OutFile 'forge-installer.jar'"
    if errorlevel 1 goto :fail
    java -jar forge-installer.jar --installServer
    if errorlevel 1 goto :fail
    del /q forge-installer.jar forge-installer.jar.log 2>nul
)

REM 2. Default settings, only where the admin has none (an update never overwrites them)
if not exist config mkdir config
if not exist server.properties copy /y defaults\server.properties server.properties >nul
if not exist config\brasshaven-common.toml copy /y defaults\config\brasshaven-common.toml config\brasshaven-common.toml >nul

REM 3. One Brasshaven jar only: older ones (a new pack unzipped over the old folder) move to old-mods\
for %%F in (mods\brasshaven-*.jar) do (
    if /i not "%%~nxF"=="%JAR%" (
        if not exist old-mods mkdir old-mods
        echo == %%~nxF -^> old-mods\ ^(remplace par / replaced by %JAR%^)
        move /y "%%F" old-mods\ >nul
    )
)

REM 4. Backup of the world before the first start with a new Brasshaven version
set "WORLD=world"
if exist server.properties (
    for /f "usebackq tokens=1,* delims==" %%A in ("server.properties") do (
        if "%%A"=="level-name" if not "%%B"=="" set "WORLD=%%B"
    )
)
set "LAST="
if exist .brasshaven-version set /p LAST=<.brasshaven-version
if exist "%WORLD%\" if not "%LAST%"=="@VERSION@" (
    if not exist backups mkdir backups
    for /f %%T in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "STAMP=%%T"
    echo == Sauvegarde du monde / world backup: backups\%WORLD%-before-@VERSION@-!STAMP!.zip
    tar -a -c -f "backups\%WORLD%-before-@VERSION@-!STAMP!.zip" "%WORLD%"
    if errorlevel 1 goto :fail
)

REM 5. EULA
findstr /b /c:"eula=true" eula.txt >nul 2>nul
if errorlevel 1 (
    echo Minecraft EULA: https://aka.ms/MinecraftEULA
    set /p "ANSWER=Acceptes-tu le CLUF de Minecraft ? / Do you accept the Minecraft EULA? [o/y/N] "
    if /i "!ANSWER!"=="o" (echo eula=true> eula.txt) else if /i "!ANSWER!"=="y" (echo eula=true> eula.txt) else (
        echo Le serveur ne peut pas demarrer sans / The server cannot start without it.
        goto :fail
    )
)

echo @VERSION@> .brasshaven-version
java @jvm_args.txt @%ARGS% nogui %*
pause
exit /b 0

:fail
pause
exit /b 1
