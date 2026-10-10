# evergreen-utils
Library of analytics and utilities for McGill Evergreen Pension &amp; Portfolio Management
zz

## Simulated Pension Model

### Setup
1. You will need python v3.12.7 or greater: [python](https://www.python.org/downloads/)

*** Remember to set "Add python.exe to PATH" when installing ***

3. On your computer, open a terminal.
- For MAC: open Terminal
- For Windows: open PowerShell OR CommandPrompt

From here, enter the following commands one-by-one:
```
git clone https://github.com/matthew-chang04/evergreen-utils
```

3. Set up virtual environment:

for MAC:
```
cd evergreen-utils
python3 -m venv .venv
source .venv/bin/activate
pip install requirements.txt
```

for Windows:
```
cd evergreen-utils
python -m venv .venv
.venv/Scripts/activate.bat
pip install requirements.txt
```

4. Run the dashboard:
```
streamlit run dashboard.py
```

### Overview

When inside the dashboard you will see a few tools:
1. Strategic Asset Allocation
