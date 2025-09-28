@echo off
REM ============================
REM NodeJS & NPM
REM ============================

echo Pastikan NodeJS v18 sudah terinstall manual di Windows (https://nodejs.org/)
echo Jika belum, install NodeJS dulu sebelum lanjut.
pause

REM ============================
REM PM2
REM ============================

npm install -g pm2
pm2 startup
pm2 save

REM ============================
REM FFMPEG
REM ============================
echo Pastikan FFMPEG sudah diinstall manual di Windows (https://ffmpeg.org/download.html)
pause

REM ============================
REM Install and start backend nodejs
REM ============================

cd pc-api
npm install
pm2 start index.js --name "pc-api" --watch
cd ..

cd pc-ws
npm install
pm2 start index.js --name "pc-ws" --watch
cd ..

cd pc-fe
npm install
pm2 start index.js --name "pc-fe" --watch
cd ..

pm2 save

REM ============================
REM Python AI
REM ============================

cd pc-ai
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
python main.py
cd ..
