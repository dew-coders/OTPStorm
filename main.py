#!/usr/bin/env python3
"""
OTPStorm — Multi-Provider OTP Flood Tool

Entry point for backward compatibility.
Run directly:  python main.py
Or as module:  python -m otpstorm
"""

import sys
import os

# Ensure the package is importable from the project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from otpstorm.cli import main

if __name__ == "__main__":
    main()
