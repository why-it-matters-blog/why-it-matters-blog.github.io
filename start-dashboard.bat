@echo off
cd /d "%~dp0"
python admin.py || py admin.py || (echo. & echo Python is not installed. Please install Python 3 from python.org. & pause)
