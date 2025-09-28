# NodeJS
sudo apt install curl -y
curl -sL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install nodejs -y

# PM2
npm install pm2 -g
pm2 startup systemd
pm2 save

# FFMPEG
sudo apt install ffmpeg

# Install and start backend nodejs
cd ./pc-api
npm install
pm2 start index.js --name "pc-api" --watch
cd ../

cd ./pc-ws
npm install
pm2 start index.js --name "pc-ws" --watch
cd ../

cd ./pc-fe
npm install
pm2 start index.js --name "pc-fe" --watch
cd ../

pm2 save

# AI
cd ./pc-ai
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
cd ../