# Desain Database

## people_counting

### areas

```
area_id (int)
camera_id (int)
area_nama (int)
deskripsi (text)
polygon (json)
isactive (int)
timestamp (timestamp)
```

### cameras

```
camera_id (int)
name (varchar)
source_url (int)
location_note (varchar)
isactive (int)
timestamp (timestamp)
```

### counting

```
counting_id (int)
camera_id (int)
masuk (int)
keluar (int)
dalam (int)=
timestamp (timestamp)
```

### setting

```
setting_id
websocket
```

---

# Source Dataset

1. Dataset dibuat menggunakan cctv malio
   - https://cctvjss.jogjakota.go.id/malioboro/Malioboro_30_Pasar_Beringharjo.stream/playlist.m3u8
   - https://cctvjss.jogjakota.go.id/malioboro/NolKm_Utara.stream/playlist.m3u8
2. Alur Pembuatan Dataset  
   Convert streaming cctv ke image -> buat dataset dengan hasty ai -> eksport ke COCO -> convert coco to yolo -> build dataset dengan yolov8 -> convert ke OpenVINO

---

# Desain Sistem

```
video frame → deteksi bounding box → cek apakah bounding box masuk/keluar polygon → apakah sudah 5 detik -> kirim data ke rest api
```

---

# Deployment

## Manual

1. Clone Repository
   ```
   git clone https://github.com/RivalD21/pc-counting.git
   ```
2. Masuk Direktori
3. import people-counting.sql ke mysql
4. sesuaikan .env (username dan password database)
5. Jalankan sistem  
   a. backend api
   ```
   Masuk direktori pc-api, buka terminal di direktori dan jalankan perintah berikut
   "npm install"
   "node index.js" ---> Sistem Berjalan Di Port 3000
   ```
   b. websocket broker
   ```
   Masuk direktori pc-ws, buka terminal di direktori dan jalankan perintah berikut
   "npm install"
   "node index.js" ---> Sistem Berjalan Di Port 8080
   ```
   c. frontend
   ```
   Masuk direktori pc-dashboard, buka terminal di direktori dan jalankan perintah berikut
   "npm install"
   "node index.js" ---> Sistem Berjalan Di Port 7077
   ```
   d. people-counting
   ```
   Masuk direktori pc-ai, buka terminal di direktori dan jalankan perintah berikut
   "python -m venv venv"
   - Jika Di Windows jalankan
     "venv\Scripts\activate"
   - Jika Di Linux/Mac jalankan
     "source venv/bin/activate"
     "pip install -r requirements.txt"
     "python3 main.py"
   ```

---

## Installer

1. Clone Repository
   ```
   git clone https://github.com/RivalD21/pc-counting.git
   ```
2. Masuk Direktori
3. import people-counting.sql ke mysql (ini tidak dimasukkan ke installer karena tidak tau mysql di device ada password atau tidak)
4. sesuaikan .env (username dan password database)
5. Install Aplikasi  
   a. Windows  
   Double Click file installer.bat yang ada di direktori  
   b. Linux/Mac/WSL
   ```
   buka terminal, masuk ke direktori
   masukkan "chmod +x setup.sh"
   kemudian masukkan "./installer.sh"
   ```
6. Informasi Sistem  
   Backend-API running di port 3000  
   Websocket Brocker di port 8080  
   Frontend running di port 7077

---

# Checklist Fitur yang Anda kerjakan

1. Desain Database (Done)
2. Pengumpulan Dataset (Done)
3. Object Detection & Tracking (Done)
4. Counting & Polygon Area (Done)
5. Prediksi (Forecasting) (Done)
6. Integrasi API (API/Front End) (Done)
7. Deployment (Done)
