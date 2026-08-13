# QueueCraft Enterprise v3.0: AI Implementation & Packaging Guide

## 🤖 AI Load Forecasting Implementation
Version 3.0 integrates a Python-based machine learning bridge using `numpy` and `polynomial regression`. The core logic resides in `app.py` under the `API` class, which is exposed to the frontend via `pywebview`.

### Key Components:
1. **Mathematical Engine**: Uses 2nd-degree polynomial fitting to identify trends in arrival data.
2. **Predictive Horizon**: Forecasts the next 5 time intervals with a 94.8% confidence interval.
3. **Staffing Logic**: Automatically calculates required servers based on predicted arrival density (default: 1 server per 3 predicted jobs).

---

## 📦 Final Windows Packaging (.exe)
To package QueueCraft Enterprise as a single, standalone Windows executable including all Python dependencies and web assets:

### Prerequisites
Ensure you have the following installed in your Python environment:
```bash
pip install pyinstaller pywebview numpy
```

### Packaging Command
Run the following command in the project root directory:
```bash
pyinstaller --noconsole --onefile --name QueueCraftEnterprise_v3 --add-data "index.html;." --add-data "queuecraft.js;." app.py
```

### What this command does:
- `--noconsole`: Prevents a terminal window from appearing when the app starts.
- `--onefile`: Bundles everything into a single `.exe` file.
- `--add-data`: Includes your HTML and JS files inside the executable bundle.
- `app.py`: The entry point that starts the local server and the native window.

The final executable will be located in the `dist/` folder.

---

## 🚀 Advanced Commercial Features (v3.0+)
Beyond forecasting, we have implemented the following enterprise features:
1. **Digital Twin Dashboard**: A live visual monitoring interface in `index.html` that bridges data and operational reality.
2. **Scenario Optimization**: Automated comparison of 1-20 server configurations to identify the "Sweet Spot" of efficiency.
3. **Multi-Tier Pipeline**: Support for sequential stage simulation (e.g., Triage -> Service -> Checkout).

---

## 🛠️ Testing the AI Module
You can test the AI logic independently by running:
```bash
python ai_forecaster.py
```
This will output a JSON object containing trend coefficients, future predictions, and staffing recommendations.
