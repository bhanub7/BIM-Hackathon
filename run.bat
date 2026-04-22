@echo off
echo ============================================================
echo  BIMRepair - Automated BIM Lint ^& Repair Assistant
echo ============================================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.9+
    pause
    exit /b 1
)

:: Install dependencies
echo [1/3] Installing dependencies...
pip install -r requirements.txt --quiet
echo.

:: Generate data
echo [2/3] Generating sample data...
python generators\generate_synthetic_dataset.py
python generators\generate_sample_ifc.py
echo.

:: Launch dashboard
echo [3/3] Launching BIMRepair dashboard...
echo.
echo   Open your browser to: http://localhost:8501
echo.
streamlit run app.py --server.port 8501

pause
