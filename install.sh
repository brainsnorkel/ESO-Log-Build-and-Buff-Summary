#!/bin/bash
# Installation script for ESO Report Tool

set -e

echo "🔧 ESO Report Tool Installer"
echo "=============================="
echo ""

# Determine installation directory
if [ -d "$HOME/bin" ]; then
    INSTALL_DIR="$HOME/bin"
elif [ -d "/usr/local/bin" ]; then
    INSTALL_DIR="/usr/local/bin"
else
    echo "Creating $HOME/bin directory..."
    mkdir -p "$HOME/bin"
    INSTALL_DIR="$HOME/bin"
fi

echo "📁 Installation directory: $INSTALL_DIR"
echo ""

# Get the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create symlink to the executable
echo "🔗 Creating symlink..."
ln -sf "$PROJECT_DIR/eso-report" "$INSTALL_DIR/eso-report"

echo "✅ Installation complete!"
echo ""
echo "📝 Usage:"
echo "  eso-report <report_code> --discord-webhook-post"
echo ""
echo "💡 Make sure $INSTALL_DIR is in your PATH"
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo ""
    echo "⚠️  $INSTALL_DIR is not in your PATH!"
    echo "   Add this to your ~/.zshrc or ~/.bashrc:"
    echo "   export PATH=\"\$HOME/bin:\$PATH\""
fi
echo ""
echo "🎉 Ready to use!"

