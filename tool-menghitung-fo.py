from fpdf import FPDF
from io import BytesIO
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Tools menghitung F0", layout="wide")
st.title("Validasi Thermal Proses Sterilisasi - PT Rumah Retort Bersama")

st.markdown("""
Aplikasi ini menghitung nilai **F₀ (F-nol)** dari data suhu per menit selama proses sterilisasi.
Gunakan input manual atau upload file Excel berisi suhu tiap menit.
""")

# Metadata form
st.sidebar.header("📝 Form Metadata Proses")
nama_produk = st.sidebar.text_input("Nama Produk")
tanggal_proses = st.sidebar.date_input("Tanggal Proses")
nama_operator = st.sidebar.text_input("Nama Operator")
nama_alat = st.sidebar.text_input("Nama Alat Retort")

# Fungsi hitung F₀
def calculate_f0(temps, T_ref=121.1, z=10):
    f0_values = []
    for T in temps:
        if T < 90:
            f0_values.append(0)
        else:
            f0_values.append(10 ** ((T - T_ref) / z))
    return np.cumsum(f0_values)

# ===== Fungsi untuk ekstrak suhu =====
def extract_suhu(df_data):
    try:
        suhu_col = None
        for col in df_data.columns:
            numeric_col = pd.to_numeric(df_data[col], errors='coerce')
            if (numeric_col > 90).sum() > 2:
                suhu_col = col
                break

        if suhu_col is None:
            raise ValueError("Kolom suhu tidak ditemukan.")

        suhu = pd.to_numeric(df_data[suhu_col], errors='coerce').dropna().tolist()
        return suhu

    except Exception as e:
        st.error(f"Gagal ekstrak suhu dari file: {e}")
        return []

# ===== Fungsi cek suhu minimal 121.1°C selama ≥3 menit =====
def check_minimum_holding_time(temps, min_temp=121.1, min_duration=3):
    holding_minutes = 0
    for t in temps:
        if t >= min_temp:
            holding_minutes += 1
        else:
            holding_minutes = 0
        if holding_minutes >= min_duration:
            return True
    return False

# Pilihan metode input
input_method = st.radio("🔘 Pilih Metode Input", ["Manual", "Upload Excel"])
temps = []

if input_method == "Manual":
    st.subheader("📋 Input Manual Suhu per Menit")
    waktu = st.number_input("Jumlah menit", min_value=1, max_value=120, value=10)
    for i in range(waktu):
        temp = st.number_input(f"Menit ke-{i+1}: Suhu (°C)", value=25.0, step=0.1)
        temps.append(temp)

if temps:
    f0 = calculate_f0(temps)
    st.info(f"📊 Data suhu valid ditemukan: {len(temps)} menit")
    st.success(f"✅ Nilai F₀ Total: {f0[-1]:.2f}")

    valid = check_minimum_holding_time(temps)
    if valid:
        st.success("✅ Suhu ≥121.1°C tercapai minimal selama 3 menit")
    else:
        st.warning("⚠️ Suhu ≥121.1°C belum tercapai selama 3 menit")

# ===== Custom PDF Class =====
class PDF(FPDF):
    def chapter_title(self, title):
        self.set_font("Arial", 'B', 12)
        self.cell(0, 10, title, ln=True)

    def chapter_body(self, text):
        self.set_font("Arial", size=12)
        self.multi_cell(0, 10, text)

    def add_metadata(self, produk, tanggal, operator, alat, f0_total, passed):
        self.add_page()
        self.chapter_title("Metadata Proses")
        self.chapter_body(f"Produk: {produk}\nTanggal Proses: {tanggal}\nOperator: {operator}\nAlat Retort: {alat}")

        self.chapter_title("Hasil Validasi")
        status_text = "Lolos" if passed else "Tidak Lolos"
        text = f"Nilai F0 Total: {f0_total:.2f}\nValidasi Suhu >= 121.1 C selama 3 menit: {status_text}"
        self.chapter_body(text)

    def add_graphic(self, img_buffer):
        self.image(img_buffer, x=10, y=self.get_y(), w=180)

# Simpan grafik ke buffer
img_buffer = BytesIO()
fig.savefig(img_buffer, format='png')
img_buffer.seek(0)

# Metadata Dummy
nama_produk = "Sarden Ikan"
tanggal_proses = datetime.now().strftime("%d-%m-%Y")
nama_operator = "Budi Santoso"
nama_alat = "Retort R2B-01"
nilai_f0 = f0[-1]
valid = check_minimum_holding_time(temps)

# Buat PDF
pdf = PDF()
pdf.add_metadata(nama_produk, tanggal_proses, nama_operator, nama_alat, nilai_f0, valid)
pdf.add_graphic(img_buffer)

pdf_bytes = pdf.output(dest='S')
buffer = BytesIO(pdf_bytes)

st.download_button(
    label="Download Laporan PDF",
    data=buffer,
    file_name="laporan_validasi.pdf",
    mime="application/pdf"
)

st.success("Laporan berhasil dibuat dan siap diunduh.")
