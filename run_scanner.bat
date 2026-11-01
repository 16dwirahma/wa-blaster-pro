@echo off
title Universal Document Scanner - Localhost
echo Mengaktifkan Virtual Environment...
call venv\Scripts\activate
echo Menjalankan Aplikasi Streamlit...
streamlit run scanner.py
pause