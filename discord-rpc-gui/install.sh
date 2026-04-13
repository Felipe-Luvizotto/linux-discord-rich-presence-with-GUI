#!/bin/bash
# ============================================================
# Instalador - Discord Rich Presence GUI para Linux
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/share/discord-rpc-gui"
BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/applications"
BINARY_NAME="linux-discord-rich-presence"

echo "╔══════════════════════════════════════════════════╗"
echo "║   Discord Rich Presence GUI - Instalador         ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Checar dependências
echo "[1/5] Verificando dependências..."

missing=""
python3 -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk" 2>/dev/null || missing="python3-gi (GTK)"

if [ -n "$missing" ]; then
    echo ""
    echo "⚠ Dependência faltando: $missing"
    echo ""
    echo "Instale com:"
    echo "  sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0"
    echo ""
    read -p "Deseja tentar instalar agora? (s/n): " choice
    if [ "$choice" = "s" ] || [ "$choice" = "S" ]; then
        sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0
    else
        echo "Instale as dependências e rode o instalador novamente."
        exit 1
    fi
fi
echo "  ✓ Dependências OK"

# Criar diretórios
echo "[2/5] Criando diretórios..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$APP_DIR"
mkdir -p "$HOME/.config/linux-discord-rich-presence"
echo "  ✓ Diretórios criados"

# Copiar arquivos
echo "[3/5] Copiando arquivos..."
cp "$SCRIPT_DIR/discord-rpc-gui.py" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/discord-rpc-gui.py"

# Copiar binário se existir na pasta
if [ -f "$SCRIPT_DIR/$BINARY_NAME" ]; then
    cp "$SCRIPT_DIR/$BINARY_NAME" "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/$BINARY_NAME"
    echo "  ✓ Binário copiado"
elif [ -f "$SCRIPT_DIR/target/release/$BINARY_NAME" ]; then
    cp "$SCRIPT_DIR/target/release/$BINARY_NAME" "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/$BINARY_NAME"
    echo "  ✓ Binário copiado (de target/release)"
elif command -v "$BINARY_NAME" &>/dev/null; then
    echo "  ✓ Binário já instalado no sistema"
else
    echo "  ⚠ Binário '$BINARY_NAME' não encontrado."
    echo "    Copie o binário compilado para: $INSTALL_DIR/$BINARY_NAME"
fi
echo "  ✓ Arquivos copiados"

# Criar lançador
echo "[4/5] Criando atalho no menu..."
cat > "$BIN_DIR/discord-rpc-gui" << 'LAUNCHER'
#!/bin/bash
cd "$HOME/.local/share/discord-rpc-gui"
exec python3 discord-rpc-gui.py "$@"
LAUNCHER
chmod +x "$BIN_DIR/discord-rpc-gui"

# Criar .desktop
cat > "$APP_DIR/discord-rpc-gui.desktop" << DESKTOP
[Desktop Entry]
Name=Discord Rich Presence
Comment=Configurar Discord Rich Presence com interface gráfica
Exec=$BIN_DIR/discord-rpc-gui
Icon=discord
Terminal=false
Type=Application
Categories=Utility;Network;
Keywords=discord;rich;presence;status;
DESKTOP
echo "  ✓ Atalho criado"

# Atualizar desktop database
echo "[5/5] Finalizando..."
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$APP_DIR" 2>/dev/null || true
fi
echo "  ✓ Instalação concluída!"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   Instalação concluída!                          ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║                                                  ║"
echo "║  Para abrir:                                     ║"
echo "║    • Procure 'Discord Rich Presence' no menu     ║"
echo "║    • Ou execute: discord-rpc-gui                 ║"
echo "║                                                  ║"
echo "║  Para desinstalar:                               ║"
echo "║    rm -rf ~/.local/share/discord-rpc-gui         ║"
echo "║    rm ~/.local/bin/discord-rpc-gui               ║"
echo "║    rm ~/.local/share/applications/discord-rpc-*  ║"
echo "║                                                  ║"
echo "╚══════════════════════════════════════════════════╝"
