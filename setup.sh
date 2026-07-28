#!/usr/bin/env bash
#
# OTPStorm Setup Script
# Auto-detects Kali/Debian PEP 668 and handles it cleanly.
#

set -e

echo "╔══════════════════════════════════════╗"
echo "║   ⚡ OTPStorm v2.0 — Setup           ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "❌ Python 3 is required. Install: sudo apt install python3 python3-pip"
    exit 1
fi
echo "✅ Python $(python3 --version | cut -d' ' -f2)"

# Detect Kali/Debian PEP 668
if [ -f /etc/os-release ] && grep -qi "kali\|debian" /etc/os-release 2>/dev/null; then
    echo "⚠  Kali/Debian detected — using --break-system-packages"
    python3 -m pip install --break-system-packages -r requirements.txt
else
    python3 -m pip install -r requirements.txt
fi

echo ""
echo "✅ Setup complete!"
echo "   Run: python3 main.py <phone> --loops 5 --delay 30"
echo ""
