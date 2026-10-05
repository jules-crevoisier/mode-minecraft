#!/usr/bin/env bash
# Brasshaven @VERSION@ server - Minecraft @MINECRAFT@, Forge @FORGE@, Java 25.
# First run: installs Forge, asks you to accept the Minecraft EULA, then starts the server.
# Every run: copies the default configs if missing, backs the world up when the Brasshaven version changed,
# and starts with the JVM flags of jvm_args.txt (RAM: edit -Xms/-Xmx there).
set -euo pipefail
cd "$(dirname "$0")"

FORGE="@FORGE@"
JAR="@JAR@"
ARGS="libraries/net/minecraftforge/forge/$FORGE/unix_args.txt"

if ! command -v java >/dev/null 2>&1; then
    echo "Java 25 est introuvable / Java 25 not found: https://adoptium.net/temurin/releases/?version=25"
    exit 1
fi
JAVA_MAJOR=$(java -version 2>&1 | grep -m 1 'version "' | sed -E 's/.*version "([0-9]+).*/\1/' || true)
if [ "${JAVA_MAJOR:-0}" -lt 25 ] 2>/dev/null; then
    echo "Il faut Java 25 (trouvé : $JAVA_MAJOR) / Java 25 is required (found: $JAVA_MAJOR)."
    echo "https://adoptium.net/temurin/releases/?version=25"
    exit 1
fi

# 1. Forge (once)
if [ ! -f "$ARGS" ]; then
    echo "== Installation de Forge $FORGE / installing Forge $FORGE"
    URL="https://maven.minecraftforge.net/net/minecraftforge/forge/$FORGE/forge-$FORGE-installer.jar"
    if command -v curl >/dev/null 2>&1; then
        curl -fL -o forge-installer.jar "$URL"
    else
        wget -O forge-installer.jar "$URL"
    fi
    java -jar forge-installer.jar --installServer
    rm -f forge-installer.jar forge-installer.jar.log
fi

# 2. Default settings, only where the admin has none (an update never overwrites them)
mkdir -p config
[ -f server.properties ] || cp defaults/server.properties server.properties
[ -f config/brasshaven-common.toml ] || cp defaults/config/brasshaven-common.toml config/brasshaven-common.toml

# 3. One Brasshaven jar only: older ones (a new pack unzipped over the old folder) move to old-mods/
for f in mods/brasshaven-*.jar; do
    if [ -f "$f" ] && [ "$(basename "$f")" != "$JAR" ]; then
        mkdir -p old-mods
        echo "== $(basename "$f") -> old-mods/ (remplacé par / replaced by $JAR)"
        mv "$f" old-mods/
    fi
done

# 4. Backup of the world before the first start with a new Brasshaven version
WORLD=$(grep -E '^level-name=' server.properties 2>/dev/null | cut -d= -f2- || true)
WORLD=${WORLD:-world}
LAST=$(cat .brasshaven-version 2>/dev/null || true)
if [ -d "$WORLD" ] && [ "$LAST" != "@VERSION@" ]; then
    mkdir -p backups
    BACKUP="backups/$WORLD-before-@VERSION@-$(date +%Y%m%d-%H%M%S).tar.gz"
    echo "== Sauvegarde du monde / world backup: $BACKUP"
    tar -czf "$BACKUP" "$WORLD"
fi

# 5. EULA
if ! grep -qs '^eula=true' eula.txt; then
    echo "Minecraft EULA: https://aka.ms/MinecraftEULA"
    read -r -p "Acceptes-tu le CLUF de Minecraft ? / Do you accept the Minecraft EULA? [o/y/N] " answer
    case "$answer" in
        [oOyY]*) echo "eula=true" > eula.txt ;;
        *) echo "Le serveur ne peut pas démarrer sans / The server cannot start without it."; exit 1 ;;
    esac
fi

echo "@VERSION@" > .brasshaven-version
exec java @jvm_args.txt @"$ARGS" nogui "$@"
