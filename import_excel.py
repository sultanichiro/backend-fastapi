"""
import_excel.py — Script untuk mengimpor data historis dari Excel ke database.

Cara menjalankan (dari folder backend/):
    python model/import_excel.py

Kolom Excel yang dibutuhkan:
    - Tanggal        : tanggal kunjungan (datetime)
    - Lokasi Awal    : nama lokasi asal pedagang
    - Tujuan         : nama lokasi tujuan (lokasi mangkal)
    - Jam Mulai      : jam mulai mangkal (time)
    - Jam Selesai    : jam selesai mangkal (time)
    - Total Penjualan: total pendapatan dalam RUPIAH (bukan porsi)
    - Cuaca          : kondisi cuaca (opsional, default 'cerah')

CATATAN:
    Nilai 'Total Penjualan' disimpan apa adanya (rupiah) ke kolom jumlah_terjual.
    Frontend bisa menggunakan nilai ini sebagai pendapatan per kunjungan.
"""

import os
import sys
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime

# ============================================================
# SETUP PATH — agar .env dan file Excel bisa ditemukan
# dari manapun script dijalankan
# ============================================================

# Folder tempat script ini berada (backend/model/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Folder backend/ (satu level di atas model/)
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)

# Load .env dari folder backend/
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

# File Excel berada di folder model/
EXCEL_PATH = os.path.join(SCRIPT_DIR, "dataState.xlsx")

# ============================================================
# KONEKSI DATABASE
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL tidak ditemukan di .env")
    sys.exit(1)

engine = create_engine(DATABASE_URL, echo=False)

# ============================================================
# BACA EXCEL
# ============================================================

print(f"Membaca file: {EXCEL_PATH}")
df = pd.read_excel(EXCEL_PATH)
df.ffill(inplace=True)

print(f"Total baris data: {len(df)}")
print(f"Kolom: {list(df.columns)}")

# ============================================================
# MULAI TRANSAKSI DATABASE
# ============================================================

with engine.begin() as conn:

    # ===== 1. PASTIKAN PEDAGANG DEFAULT ADA =====
    res = conn.execute(text("SELECT id FROM pedagang LIMIT 1"))
    row_pedagang = res.fetchone()

    if row_pedagang:
        pedagang_id = row_pedagang[0]
        print(f"Menggunakan pedagang_id: {pedagang_id}")
    else:
        # Buat pedagang default jika belum ada
        conn.execute(text("""
            INSERT INTO pedagang (nama, username, password)
            VALUES ('Pedagang Default', 'pedagang_default', 'password_hashed')
        """))
        res = conn.execute(text("SELECT id FROM pedagang LIMIT 1"))
        pedagang_id = res.fetchone()[0]
        print(f"Pedagang default dibuat dengan id: {pedagang_id}")

    # ===== 2. INSERT LOKASI (skip jika sudah ada) =====
    lokasi_unik = set(df['Lokasi Awal']).union(set(df['Tujuan']))
    lokasi_map = {}

    print(f"\nMemproses {len(lokasi_unik)} lokasi unik...")

    for lokasi in lokasi_unik:
        # Cek apakah lokasi sudah ada untuk pedagang ini
        res = conn.execute(text("""
            SELECT id FROM lokasi
            WHERE nama = :nama AND pedagang_id = :pedagang_id
        """), {"nama": lokasi, "pedagang_id": pedagang_id})
        existing = res.fetchone()

        if existing:
            lokasi_map[lokasi] = existing[0]
            print(f"  [SKIP] Lokasi '{lokasi}' sudah ada (id: {existing[0]})")
        else:
            conn.execute(text("""
                INSERT INTO lokasi (pedagang_id, nama, latitude, longitude)
                VALUES (:pedagang_id, :nama, 0.0, 0.0)
            """), {
                "pedagang_id": pedagang_id,
                "nama": lokasi
            })
            res = conn.execute(text("""
                SELECT id FROM lokasi
                WHERE nama = :nama AND pedagang_id = :pedagang_id
            """), {"nama": lokasi, "pedagang_id": pedagang_id})
            lokasi_map[lokasi] = res.fetchone()[0]
            print(f"  [NEW]  Lokasi '{lokasi}' ditambahkan (id: {lokasi_map[lokasi]})")

    # ===== 3. INSERT KUNJUNGAN + PENJUALAN =====
    print(f"\nMemproses {len(df)} baris data kunjungan & penjualan...")

    sukses = 0
    gagal = 0

    for idx, row in df.iterrows():
        try:
            lokasi_id = lokasi_map[row['Tujuan']]

            # Parse waktu
            tanggal = row['Tanggal']
            mulai_raw = row['Jam Mulai']
            selesai_raw = row['Jam Selesai']

            # Handle jika Jam Mulai/Selesai sudah datetime atau masih time object
            if hasattr(mulai_raw, 'hour'):
                waktu_mulai = datetime.combine(tanggal.date(), mulai_raw)
                waktu_selesai = datetime.combine(tanggal.date(), selesai_raw)
            else:
                # Jika berupa string "HH:MM"
                from datetime import time as dtime
                h, m = str(mulai_raw).split(":")[:2]
                waktu_mulai = datetime.combine(tanggal.date(), dtime(int(h), int(m)))
                h, m = str(selesai_raw).split(":")[:2]
                waktu_selesai = datetime.combine(tanggal.date(), dtime(int(h), int(m)))

            # Durasi dalam JAM (float, 2 desimal)
            # Contoh: 1.5 = 1 jam 30 menit, 0.75 = 45 menit
            durasi_jam = round((waktu_selesai - waktu_mulai).total_seconds() / 3600, 2)
            durasi_jam = max(0.02, durasi_jam)  # minimum ~1 menit

            # Hari kuliah (Senin-Jumat = 1, Sabtu-Minggu = 0)
            hari_kuliah = 1 if tanggal.weekday() < 5 else 0

            # Kondisi cuaca
            cuaca = str(row['Cuaca']).strip() if pd.notna(row['Cuaca']) else 'cerah'

            # --- CEK DUPLIKAT ---
            res_cek = conn.execute(text("""
                SELECT id FROM kunjungan
                WHERE pedagang_id = :pedagang_id AND lokasi_id = :lokasi_id AND waktu_mulai = :waktu_mulai
            """), {"pedagang_id": pedagang_id, "lokasi_id": lokasi_id, "waktu_mulai": waktu_mulai})
            
            if res_cek.fetchone():
                print(f"  [SKIP] Kunjungan duplikat baris {idx}")
                continue

            # --- INSERT KUNJUNGAN ---
            result = conn.execute(text("""
                INSERT INTO kunjungan
                (pedagang_id, lokasi_id, waktu_mulai, waktu_selesai,
                 durasi_mangkal, kondisi_cuaca, hari_kuliah)
                VALUES (
                    :pedagang_id,
                    :lokasi_id,
                    :waktu_mulai,
                    :waktu_selesai,
                    :durasi,
                    :cuaca,
                    :hari_kuliah
                )
            """), {
                "pedagang_id": pedagang_id,
                "lokasi_id": lokasi_id,
                "waktu_mulai": waktu_mulai,
                "waktu_selesai": waktu_selesai,
                "durasi": durasi_jam,
                "cuaca": cuaca,
                "hari_kuliah": hari_kuliah
            })

            kunjungan_id = result.lastrowid

            # jumlah_terjual = nilai rupiah mentah (integer, tanpa format)
            jumlah_terjual = int(row['Total Penjualan']) if pd.notna(row['Total Penjualan']) else 0

            print(
    f"BARIS {idx} | Excel={row['Total Penjualan']} | "
    f"Simpan={jumlah_terjual} | Type={type(row['Total Penjualan'])}"
)

            conn.execute(text("""
                INSERT INTO penjualan
                (pedagang_id, lokasi_id, kunjungan_id,
                 jumlah_terjual, durasi_mangkal, kondisi_cuaca,
                 hari_kuliah, waktu_kunjungan, waktu_transaksi)
                VALUES (
                    :pedagang_id,
                    :lokasi_id,
                    :kunjungan_id,
                    :jumlah,
                    :durasi,
                    :cuaca,
                    :hari_kuliah,
                    :waktu_mulai,
                    :waktu_mulai
                )
            """), {
                "pedagang_id": pedagang_id,
                "lokasi_id": lokasi_id,
                "kunjungan_id": kunjungan_id,
                "jumlah": jumlah_terjual,
                "durasi": durasi_jam,
                "cuaca": cuaca,
                "hari_kuliah": hari_kuliah,
                "waktu_mulai": waktu_mulai
            })

            sukses += 1

        except Exception as e:
            print(f"  [ERROR] Baris {idx}: {e}")
            gagal += 1

print(f"""
===============================================
Import Selesai!
  Berhasil : {sukses} baris
  Gagal    : {gagal} baris
  Pedagang : id={pedagang_id}
  Lokasi   : {len(lokasi_map)} lokasi
===============================================
""")