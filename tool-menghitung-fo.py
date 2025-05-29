from fpdf import FPDF
from io import BytesIO
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Validasi Thermal Retort", layout="centered")

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

# ===== Dummy Data & Perhitungan =====
temps = [30, 35, 45, 60, 75, 85, 95, 110, 115, 121, 122, 121, 118]
z = 10
f0 = np.cumsum([max(0, (t - 121.1)/z) for t in temps])

fig, ax = plt.subplots()
ax.plot(range(1, len(temps)+1), temps, label="Suhu (°C)", marker='o')
ax.axhline(90, color='red', linestyle='--', label="Ambang F₀ (90°C)")
ax.axhline(121.1, color='green', linestyle='--', label="Target BPOM (121.1°C)")
ax.set_xlabel("Menit")
ax.set_ylabel("Suhu (°C)")

ax2 = ax.twinx()
ax2.plot(range(1, len(f0)+1), f0, color='orange', label="F₀ Akumulatif", linestyle='--')
ax2.set_ylabel("F₀")

ax.legend(loc="upper left")
ax2.legend(loc="upper right")

st.title("📄 Validasi Thermal Retort")
st.pyplot(fig)

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
    label=⬇️ Download Laporan PDF",
    data=buffer,
    file_name="laporan_validasi.pdf",
    mime="application/pdf"
)

st.success("Laporan berhasil dibuat dan siap diunduh.")
