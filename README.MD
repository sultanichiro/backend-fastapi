# ⚙️ FastAPI Backend - Project Tugas Akhir

Backend API menggunakan **FastAPI** dengan fitur:

* 🔐 Authentication (JWT)
* 🗄️ Database MySQL + SQLAlchemy
* 🔄 Migration dengan Alembic
* 📊 Data processing (Pandas, NumPy, SciPy)
* 📁 Upload file (multipart)
* 🔑 Password hashing (bcrypt)

---

# 📦 Tech Stack

* FastAPI
* Uvicorn
* SQLAlchemy
* Alembic
* MySQL (mysqlclient / PyMySQL)
* Pydantic
* Passlib (bcrypt)
* Python-JOSE (JWT)
* Pandas / NumPy / SciPy

---

---

# 🚀 Cara Menjalankan (AUTO SETUP)

## 1. Clone Repository

```
https://github.com/sultanichiro/ai-sate-optimization-backend.git
cd ai-sate-optimization-backend
```

---

## 2. Install Python (WAJIB)

Download:
👉 https://www.python.org/downloads/

Cek:

```
python --version
```

---

## 3. Buat Virtual Environment

```
python -m venv venv
```

Aktifkan:

### Windows

```
venv\Scripts\activate
```

### Linux / Mac

```
source venv/bin/activate
```

---

## 4. Install Dependency

```
pip install -r requirements.txt
```

---

## 5. Setup Database MySQL

### Install MySQL

👉 https://dev.mysql.com/downloads/mysql/

### Buat database:

```
CREATE DATABASE db_project;
```

---

## 6. Konfigurasi ENV

Buat file `.env` di folder `backend/`

```
DATABASE_URL=mysql://root:password@localhost:3306/db_project

SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

## 7. Jalankan Migration

```
alembic upgrade head
```

---

## 8. Jalankan Server

```
uvicorn app.main:app --reload
```

---

# 🌐 API Endpoint

## Swagger Docs

```
http://127.0.0.1:8000/docs
```

## ReDoc

```
http://127.0.0.1:8000/redoc
```

---

# 📦 Export Requirements (Jika Update Library)

```
pip freeze > requirements.txt
```

---

# 📱 Akses dari Flutter / Device

Gunakan URL berikut:

### Emulator Android:

```
http://10.0.2.2:8000
```

### HP / Device:

```
http://IP_KOMPUTER:8000
```

Contoh:

```
http://192.168.1.10:8000
```

---

# 🔐 Authentication (JWT)

Gunakan endpoint login untuk mendapatkan token:

```
Authorization: Bearer <token>
```

---

# 📁 Upload File

Gunakan:

```
multipart/form-data
```

---

# ⚠️ Troubleshooting

## ❌ Module not found

```
pip install -r requirements.txt
```

## ❌ Database tidak connect

* Pastikan MySQL aktif
* Cek username/password di `.env`

## ❌ Alembic error

```
alembic downgrade base
alembic upgrade head
```

---

# 🧪 Testing API

Gunakan:

* Postman
* Thunder Client
* Swagger UI

---

# 🧹 Best Practice

* Gunakan migration untuk perubahan DB

---

# 👨‍💻 Developer

Project Tugas Akhir Backend FastAPI 🚀
by Sultan Maulana Ichiro
