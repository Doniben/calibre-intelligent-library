#!/bin/bash
# Build script for Calibre plugin

echo "Building Biblioteca Inteligente plugin..."

# Remove old zip if exists
rm -f biblioteca-inteligente.zip

# Create zip with all plugin files
zip -r biblioteca-inteligente.zip \
    __init__.py \
    ui.py \
    config.py \
    search_dialog.py \
    plugin-import-name-biblioteca_inteligente.txt

echo "✓ Plugin built: biblioteca-inteligente.zip"
echo ""
echo "To install:"
echo "1. Open Calibre"
echo "2. Preferences → Plugins → Load plugin from file"
echo "3. Select biblioteca-inteligente.zip"
echo "4. Restart Calibre"
