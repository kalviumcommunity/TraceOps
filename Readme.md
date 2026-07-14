# TraceOps Workspace

This repository contains the standardized development environment and data pipeline structure for the customer analytics and trace operation projects. The project uses an isolated python environment with strictly managed and pinned dependencies to guarantee reproducible results on any machine.

## Setup

Follow these steps to replicate the development environment on your local machine.

### 1. Clone the repository
```bash
git clone https://github.com/kalviumcommunity/TraceOps.git
cd TraceOps
```

### 2. Create a virtual environment
Ensure you have Python 3.8+ installed. Run this command in the project root:
```bash
# macOS and Linux
python3 -m venv venv

# Windows
python -m venv venv
```
*(Note: If your Windows path contains spaces and the generated launcher fails, recreate the environment using `python -m virtualenv venv` and copy the base `python.exe` over `venv\Scripts\python.exe`.)*

### 3. Activate the virtual environment
Activating redirects Python and pip commands to run inside the isolated environment.
```bash
# macOS and Linux
source venv/bin/activate

# Windows (Command Prompt)
venv\Scripts\activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure environment variables
Copy the template `.env.example` file to `.env` and fill in any necessary configurations:
```bash
# Windows
Copy-Item .env.example .env

# macOS / Linux
cp .env.example .env
```

---

## Project Structure

The workspace follows a predictable, team-friendly directory hierarchy:

```text
TraceOps/
├── data/
│   ├── raw/          ← Source data (never modify files here, read-only)
│   └── processed/    ← Cleaned and transformed data ready for analysis
├── notebooks/        ← Jupyter exploration and reporting (numbered sequentially)
├── scripts/          ← Repeatable, modular Python pipeline scripts
├── output/           ← Generated exports: reports, plots, and CSVs
├── venv/             ← Virtual environment folder (never committed to git)
├── .env              ← Local private configuration secrets (never committed to git)
├── .env.example      ← Template for environment variables (version controlled)
├── .gitignore        ← Rules for files/directories to exclude from version control
├── requirements.txt  ← Pinned package dependencies for reproducibility
└── Readme.md         ← Project documentation
```

---

## Verifying the Setup

To verify that all libraries load successfully and the environment is properly configured, run:

```bash
python scripts/verify_setup.py
```

This script will attempt to import all required libraries (`pandas`, `numpy`, `matplotlib`, `seaborn`, `scikit-learn`, `python-dotenv`, `openpyxl`) and output their installed versions.
