@echo off

REM Activate the virtual environment
call venv\Scripts\activate

REM Execute the Python script
python run.py
timeout /t 5

REM Deactivate the virtual environment
deactivate
