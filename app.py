import io
import pandas as pd
import streamlit as st

# Konfigurasi Halaman
st.set_page_config(
    page_title="WA Blaster Pro - Multi-Account & VCF Generator",
    page_icon="📱",
    layout="wide",
)

# Sidebar: Pengaturan Akun & Perangkat (Tanpa Gemini API)
with st.sidebar:
  st.markdown("### ⚙️ Konfigurasi Perangkat")
  st.success("Mode Standalone (Tanpa API Key Eksternal)")

  st.markdown("---")
  st.markdown("### ⚙️ Setting Multi-Akun WhatsApp (6 Akun)")

  selected_account = st.selectbox(
      "Pilih Akun WhatsApp Pengirim:",
      [
          "Akun WA 1 (Utama)",
          "Akun WA 2",
          "Akun WA 3",
          "Akun WA 4",
          "Akun WA 5",
          "Akun WA 6",
      ],
  )

  custom_sender = st.text_input(
      "Atau Ketik Nomor WA Pengirim Aktif:", "625888140182"
  )
  st.info(f"Active Sender: {custom_sender}")

# Header Utama Aplikasi
st.markdown(
    "## 📱 WA Blaster Pro - Multi-Account & VCF Generator"
)
st.markdown("---")

# Tab Navigasi Utama (Hanya tersisa Upload Excel & Blasting)
tab_excel, tab_blast = st.tabs(
    ["📁 Upload Excel / Data Riset", "🚀 Kirim Blast Pesan"]
)

# Inisialisasi Session State untuk menyimpan data yang di-upload
if "data_nasabah" not in st.session_state:
  st.session_state["data_nasabah"] = None

with tab_excel:
  st.markdown("### 📁 Upload Data Nasabah (Excel / CSV)")
  st.write(
      "Unggah file Excel hasil riset atau data nasabah Anda di sini untuk"
      " langsung diproses ke sistem blast."
  )

  uploaded_file = st.file_uploader(
      "Pilih file Excel (.xlsx) atau CSV", type=["xlsx", "csv"]
  )

  if uploaded_file is not None:
    try:
      if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
      else:
        df = pd.read_excel(uploaded_file)

      st.session_state["data_nasabah"] = df
      st.success(
          f"Berhasil memuat {len(df)} baris data calon nasabah unsecured"
          " loan!"
      )

      # Tampilkan pratinjau data
      st.markdown("#### Pratinjau Data Nasabah:")
      st.dataframe(df, use_container_width=True)

    except Exception as e:
      st.error(f"Gagal membaca file: {e}")
  else:
    st.info("Silakan unggah file Excel data nasabah terlebih dahulu.")

with tab_blast:
  st.markdown("### 🚀 Panel Blasting WhatsApp")

  if st.session_state["data_nasabah"] is not None:
    df_active = st.session_state["data_nasabah"]
    st.write(
        f"Jumlah data siap kirim: **{len(df_active)} kontak** menggunakan pengirim"
        f" **{custom_sender}**."
    )

    # Input Template Pesan
    pesan_template = st.text_area(
        "Template Pesan WhatsApp:",
        placeholder=(
            "Halo Bapak/Ibu [Nama], kami dari layanan Unsecured Loan menawarkan"
            " pinjaman tanpa agunan..."
        ),
        height=150,
    )

    col1, col2 = st.columns(2)
    with col1:
      btn_preview = st.button(
          "🔍 Preview Pesan", use_container_width=True, type="secondary"
      )
    with col2:
      btn_blast = st.button(
          "🚀 Mulai Blasting Sekarang", use_container_width=True, type="primary"
      )

    if btn_preview:
      st.info("Fitur Preview: Menampilkan contoh pesan ke nasabah pertama.")
      if not df_active.empty:
        sample_row = df_active.iloc[0].to_dict()
        st.write(f"Contoh hasil format untuk baris pertama: {sample_row}")

    if btn_blast:
      if not pesan_template.strip():
        st.warning("Mohon isi template pesan WhatsApp terlebih dahulu!")
      else:
        st.success(
            "Proses simulasi blasting dimulai! Pesan dikirimkan secara"
            f" berurutan melalui akun {custom_sender}."
        )
        # Placeholder untuk logika pengiriman pesan Anda selanjutnya
        progress_bar = st.progress(0)
        for i in range(100):
          progress_bar.progress(i + 1)
        st.balloons()
        st.success("Selesai! Seluruh pesan berhasil diproses.")
  else:
    st.warning(
        "⚠️ Belum ada data yang dimuat. Silakan upload file Excel terlebih"
        " dahulu di tab 'Upload Excel / Data Riset'."
    )