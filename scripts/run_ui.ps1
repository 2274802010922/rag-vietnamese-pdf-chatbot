$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..
.\.venv\Scripts\python.exe -m streamlit run ui/streamlit_app.py
