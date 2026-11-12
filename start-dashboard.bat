@echo off
cd /d "%~dp0"
python admin.py || py admin.py || (echo. & echo Python install nahi hai. python.org se Python 3 install karein. & pause)
