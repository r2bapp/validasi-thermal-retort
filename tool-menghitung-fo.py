from fpdf import FPDF
from io import BytesIO
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Unduh Data PDF dan Tools menghitung F0", layout="wide")
st.title("Tools Menghitung F0 - Rumah Retort Bersama")

st.markdown("""
Aplikasi ini menghitung nilai **F₀ (F-nol)** dari data suhu per menit selama proses sterilisasi.
Gunakan input manual suhu tiap menit.
""")

# Data form
st.sidebar.header("📝 Form Data Proses")
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
input_method = st.radio("🔘 Pilih Metode Input", ["Manual"])
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

    def add_data(self, produk, tanggal, operator, alat, f0_total, passed):
        self.add_page()
        self.chapter_title("Data Proses")
        self.chapter_body(f"Produk: {produk}\nTanggal Proses: {tanggal}\nOperator: {operator}\nAlat Retort: {alat}")

        self.chapter_title("Hasil Validasi")
        status_text = "Lolos" if passed else "Tidak Lolos"
        text = f"Nilai F0 Total: {f0_total:.2f}\nValidasi Suhu >= 121.1 C selama 3 menit: {status_text}"
        self.chapter_body(text)

    def add_graphic(self, img_buffer):
        self.image(img_buffer, x=10, y=self.get_y(), w=180)

   # Buat grafik
fig, ax = plt.subplots()
ax.plot(range(1, len(temps)+1), temps, label="Suhu (°C)", marker='o')
ax.axhline(90, color='red', linestyle='--', label="Ambang F₀ (90°C)")
ax.axhline(121.1, color='green', linestyle='--', label="Target BPOM (121.1°C)")
ax.set_xlabel("Menit")
ax.set_ylabel("Suhu (°C)")

ax2 = ax.twinx()
ax2.plot(range(1, len(f0)+1), f0, color='orange', label="F₀ Akumulatif", linestyle='--')
ax2.set_ylabel("F₀")

ax.legend(loc="center left")
ax2.legend(loc="center right")

# Tampilkan grafik
st.pyplot(fig)

# Simpan grafik ke BytesIO
fig.savefig("grafik_temp.png")
img_buffer.seek(0)

# Buat PDF
pdf = FPDF()
pdf.set_title("Laporan Validasi Thermal Retort")
pdf.set_author("Nama Operator")
pdf.set_creator("Aplikasi Streamlit")
pdf.add_page()
pdf.set_font("Arial", size=12)
pdf.cell(200, 10, txt="Laporan Uji Validasi Thermal Retort", ln=True, align="C")
pdf.ln(10)
pdf.image("grafik_temp.png", x=10, y=30, w=180)



# Output PDF ke memori
if st.button("📄 Ekspor ke PDF"):
        pdf = PDF()
        pdf.add_data(nama_produk, tanggal_proses, nama_operator, nama_alat, f0[-1], valid)
pdf_bytes = pdf.output(dest='S')
buffer = BytesIO(pdf_bytes)

# Tombol download di Streamlit
st.title("📄 Unduh Data PDF")
st.download_button(
    label="Download Laporan PDF",
    data=buffer,
    file_name="laporan_validasi.pdf",
    mime="application/pdf"
)

st.success("Laporan berhasil dibuat dan siap diunduh.")
