from fpdf import FPDF
from io import BytesIO
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Contoh data suhu
waktu = np.arange(0, 61, 5)  # menit
suhu = [30, 35, 45, 60, 75, 85, 95, 110, 115, 121, 122, 121, 118]

# Plot grafik suhu vs waktu
fig, ax = plt.subplots()
ax.plot(waktu[:len(suhu)], suhu, marker='o', linestyle='-', color='blue')
ax.set_title('Grafik Suhu vs Waktu')
ax.set_xlabel('Waktu (menit)')
ax.set_ylabel('Suhu (°C)')

# Simpan grafik ke BytesIO
img_buffer = BytesIO()
fig.savefig(img_buffer, format='png')
img_buffer.seek(0)

# Buat PDF
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)
pdf.cell(200, 10, txt="Laporan Uji Validasi Thermal Retort", ln=True, align="C")
pdf.ln(10)

# Tambahkan grafik ke PDF
pdf.image(img_buffer, x=10, y=30, w=180)

# Output PDF ke memori
pdf_bytes = pdf.output(dest='S').  # <- jika return-nya str
buffer = BytesIO(pdf_bytes)

# Tampilkan di Streamlit
st.title("📄 Validasi Thermal Retort")
st.write("Grafik suhu terhadap waktu berhasil dibuat dan dimasukkan ke dalam laporan PDF.")
st.pyplot(fig)

st.download_button(
    label="⬇️ Download Laporan PDF",
    data=buffer,
    file_name="laporan_validasi.pdf",
    mime="application/pdf"
)
