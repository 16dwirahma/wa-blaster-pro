import streamlit as st
import pandas as pd
import urllib.parse

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="WA Blaster Pro - Multi-Account & VCF Generator",
    page_icon="📱",
    layout="wide"
)

# Inisialisasi Session State
if "df_data" not in st.session_state:
    st.session_state["df_data"] = None

# Template Default Text Blast (Hanya menyapa Nama saja)
default_pesan_ctbc = (
    "Halo Bapak/Ibu {Nama},\n\n"
    "Perkenalkan saya Dwi dari Bank CTBC. Kami ingin menginformasikan fasilitas Pinjaman Tanpa Agunan (KTA) "
    "dengan bunga ringan dan proses cepat tanpa jaminan.\n\n"
    "Apakah ada waktu sejenak untuk berdiskusi lebih lanjut?"
)

if "pesan_template" not in st.session_state:
    st.session_state["pesan_template"] = default_pesan_ctbc

st.title("📱 WA Blaster Pro - Multi-Account & VCF Generator")

# Sidebar Konfigurasi
with st.sidebar:
    st.header("⚙️ Konfigurasi Perangkat")
    st.info("Mode Standalone (Operasional Lokal)")
    
    st.subheader("⚙️ Setting Multi-Akun WhatsApp (6 Akun)")
    akun_opsi = [f"Akun WA {i+1} (Utama)" if i==0 else f"Akun WA {i+1}" for i in range(6)]
    pilihan_akun = st.selectbox("Pilih Akun WhatsApp Pengirim:", akun_opsi)
    
    wa_pengirim = st.text_input("Atau Ketik Nomor WA Pengirim Aktif:", value="625888140182")
    st.success(f"Active Sender: {wa_pengirim}")

# Buat Tab Antarmuka
tab1, tab2 = st.tabs(["📁 Upload Excel & Auto VCF", "🚀 Kirim Blast Pesan"])

# Helper fungsi untuk mendeteksi kolom secara fleksibel
def get_lead_columns(df):
    cols_lower = [str(c).strip().lower() for c in df.columns]
    hp_col = next((df.columns[i] for i, c in enumerate(cols_lower) if any(k in c for k in ['hp', 'telepon', 'phone', 'no', 'wa'])), df.columns[0])
    nama_col = next((df.columns[i] for i, c in enumerate(cols_lower) if any(k in c for k in ['nama', 'name'])), df.columns[1] if len(df.columns) > 1 else df.columns[0])
    jabatan_col = next((df.columns[i] for i, c in enumerate(cols_lower) if any(k in c for k in ['jabatan', 'title', 'posis'])), None)
    kantor_col = next((df.columns[i] for i, c in enumerate(cols_lower) if any(k in c for k in ['kantor', 'pt', 'perusahaan', 'company', 'org'])), None)
    return hp_col, nama_col, jabatan_col, kantor_col

# ==========================================
# TAB 1: UPLOAD EXCEL & AUTO VCF
# ==========================================
with tab1:
    st.subheader("📁 Upload File Excel Prospek Lead")
    uploaded_file = st.file_uploader("Pilih file Excel (.xlsx / .xls):", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            st.session_state["df_data"] = df
            st.success(f"Berhasil memuat {len(df)} data kontak dari Excel!")
            st.dataframe(df, use_container_width=True)
            
            hp_col, nama_col, jabatan_col, kantor_col = get_lead_columns(df)
            
            # Generate VCF otomatis tanpa perlu pilih opsi manual
            vcf_output = ""
            for idx, row in df.iterrows():
                raw_hp = str(row[hp_col]).strip().replace(".0", "")
                if not raw_hp.startswith("62") and raw_hp.startswith("0"):
                    raw_hp = "62" + raw_hp[1:]
                
                nama = str(row[nama_col]).strip()
                jabatan = str(row[jabatan_col]).strip() if jabatan_col and pd.notna(row[jabatan_col]) else ""
                kantor = str(row[kantor_col]).strip() if kantor_col and pd.notna(row[kantor_col]) else ""
                
                vcf_output += "BEGIN:VCARD\n"
                vcf_output += "VERSION:3.0\n"
                vcf_output += f"FN:{nama}\n"
                if jabatan:
                    vcf_output += f"TITLE:{jabatan}\n"
                if kantor:
                    vcf_output += f"ORG:{kantor}\n"
                vcf_output += f"TEL;TYPE=CELL:{raw_hp}\n"
                vcf_output += "END:VCARD\n"
            
            st.markdown("---")
            st.subheader("📥 Download File VCF Kontak")
            st.success("File VCF berhasil di-generate secara otomatis dari Excel!")
            st.download_button(
                label="📥 Download File VCF (.vcf)",
                data=vcf_output,
                file_name="Kontak_Lead_Nasabah.vcf",
                mime="text/vcard",
                type="primary"
            )
                
        except Exception as e:
            st.error(f"Gagal membaca file Excel: {e}")
    else:
        st.info("Silakan unggah file Excel prospek Anda di atas. File VCF akan langsung otomatis dibuat & siap di-download.")

# ==========================================
# TAB 2: KIRIM BLAST PESAN
# ==========================================
with tab2:
    st.subheader("🚀 Panel Blasting WhatsApp")
    
    df_active = st.session_state.get("df_data", None)
    
    if df_active is not None and not df_active.empty:
        jumlah_kontak = len(df_active)
        st.write(f"Jumlah data siap kirim: **{jumlah_kontak} kontak** menggunakan pengirim **{wa_pengirim}**.")
    else:
        st.warning("⚠️ Belum ada data Excel yang diunggah. Silakan unggah terlebih dahulu di tab '📁 Upload Excel & Auto VCF'.")
    
    # Text area template pesan (Hanya menyapa Nama)
    pesan_template = st.text_area(
        "Template Pesan WhatsApp:",
        value=st.session_state["pesan_template"],
        height=180,
        help="Gunakan placeholder {Nama} untuk menyapa nasabah secara personal."
    )
    
    st.session_state["pesan_template"] = pesan_template
    
    col_btn1, col_btn2 = st.columns(2)
    show_preview = False
    start_blast = False
    
    with col_btn1:
        if st.button("🔍 Preview Pesan"):
            show_preview = True
                
    with col_btn2:
        if st.button("🚀 Mulai Blasting & Buka WhatsApp", type="primary"):
            start_blast = True

    # Menampilkan Preview Kontak Pertama
    if show_preview:
        if df_active is not None and not df_active.empty:
            st.markdown("---")
            st.subheader("📋 Preview Data Lead Pertama & Teks Pesan")
            st.info("💡 *Catatan: Tombol 'Preview Pesan' menampilkan sampel kontak #1. Untuk mengirim pesan ke seluruh nasabah, klik tombol merah '🚀 Mulai Blasting & Buka WhatsApp' di atas.*")
            
            hp_col, nama_col, jabatan_col, kantor_col = get_lead_columns(df_active)
            
            sample_row = df_active.iloc[0]
            s_nama = str(sample_row.get(nama_col, "-"))
            s_hp = str(sample_row.get(hp_col, "-")).strip().replace(".0", "")
            if not s_hp.startswith("62") and s_hp.startswith("0"):
                s_hp = "62" + s_hp[1:]
            s_jabatan = str(sample_row.get(jabatan_col, "-")) if jabatan_col else "-"
            s_kantor = str(sample_row.get(kantor_col, "-")) if kantor_col else "-"
            
            pesan_sample = pesan_template.replace("{Nama}", s_nama)
            encoded_sample = urllib.parse.quote(pesan_sample)
            wa_sample_link = f"https://wa.me/{s_hp}?text={encoded_sample}"
            
            # Kartu Preview Kontak Pertama
            st.info(f"""
            📌 **Detail Nasabah (Kontak #1):**
            * **Nama Nasabah:** {s_nama}
            * **Nomor WA:** {s_hp}
            * **Jabatan:** {s_jabatan}
            * **Nama PT / Perusahaan:** {s_kantor}
            
            ---
            💬 **Preview Teks Pesan Terkirim:**  
            {pesan_sample}
            """)
            st.markdown(f'<a href="{wa_sample_link}" target="_blank" style="display:inline-block; background-color:#25D366; color:white; padding:10px 18px; text-decoration:none; border-radius:8px; font-weight:bold;">💬 Uji Kirim Chat WA ke Kontak #1 ({s_nama})</a>', unsafe_allow_html=True)
            st.markdown("---")
        else:
            st.error("Silakan unggah data Excel terlebih dahulu untuk melihat preview!")

    # Menampilkan Daftar Blasting Semua Kontak
    if start_blast:
        if df_active is not None and not df_active.empty:
            st.markdown("---")
            st.subheader("📲 Daftar Link Kirim WA (Semua Kontak)")
            hp_col, nama_col, jabatan_col, kantor_col = get_lead_columns(df_active)
            
            for idx, row in df_active.iterrows():
                raw_hp = str(row.get(hp_col, "")).strip().replace(".0", "")
                if not raw_hp.startswith("62") and raw_hp.startswith("0"):
                    raw_hp = "62" + raw_hp[1:]
                
                nama_val = str(row.get(nama_col, "-"))
                jabatan_val = str(row.get(jabatan_col, "-")) if jabatan_col else "-"
                kantor_val = str(row.get(kantor_col, "-")) if kantor_col else "-"
                
                pesan_jadi = pesan_template.replace("{Nama}", nama_val)
                encoded_msg = urllib.parse.quote(pesan_jadi)
                wa_link = f"https://wa.me/{raw_hp}?text={encoded_msg}"
                
                st.markdown(
                    f'🟢 **[{idx+1}] {nama_val}** | 📱 {raw_hp} | 💼 {jabatan_val} | 🏢 {kantor_val} '
                    f'➔ <a href="{wa_link}" target="_blank" style="background-color:#25D366; color:white; padding:4px 12px; border-radius:5px; text-decoration:none; font-weight:bold;">💬 Kirim WA</a>',
                    unsafe_allow_html=True
                )
        else:
            st.error("Data kontak kosong! Harap unggah file Excel terlebih dahulu.")