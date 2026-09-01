#!/bin/sh
# Rasterises icon.svg (the source) to the 128x128 icon.png the Marketplace needs.
# The Marketplace rejects SVG icons, so the PNG is committed alongside the SVG.
set -eu
cd "$(dirname "$0")/.."
rsvg-convert -w 128 -h 128 -o icon.png icon.svg
echo "wrote $(pwd)/icon.png"
