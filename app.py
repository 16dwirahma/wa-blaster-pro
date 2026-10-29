import io
import re
import urllib.parse
import google.generativeai as genai
from PIL import Image
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="WA Blaster Pro - Validasi LinkedIn & Kontak VCF",
    page_icon="📱",
    layout="wide",
)

st.title("📱 WA Blaster Pro - Validasi LinkedIn & Kontak VCF")

# Ambil API Key dari Streamlit Secrets
try:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    gemini_api_key = ""

with st.sidebar:
    st.subheader("🔑 Konfigurasi API & Device")
    if not gemini_api_key:
        gemini_api_key = st.text_input("Masukkan Gemini API Key:", type="password")
    else:
        st.success("🔑 Gemini API Key dimuat otomatis dari sistem!")

    st.divider()
    st.subheader("⚙️ Setting Device WA")
    nomor_utama = st.text_input("Nomor Utama (WA 1):", value="625888140182")
    if nomor_utama:
        st.success(f"WA Active: {nomor_utama}")

tab1, tab2 = st.tabs(["📸 Scan Hardcopy (Foto Doc)", "📂 Upload Excel / Data Riset"])

# --- TAB 1: OCR HARDCOPY DENGAN GEMINI AI ---
with tab1:
    st.subheader("📸 Upload Foto Dokumen Hardcopy Database")
    uploaded_image = st.file_uploader("Pilih foto dokumen (JPG/PNG)", type=["jpg", "jpeg", "png"])
    if uploaded_image is not None:
        st.image(uploaded_image, caption="Preview Dokumen", use_container_width=True)
        if st.button("🚀 Process & Extract Data dengan AI"):
            if not gemini_api_key:
                st.error("Silakan masukkan Gemini API Key terlebih dahulu!")
            else:
                with st.spinner("Membaca dokumen..."):
                    try:
                        image = Image.open(uploaded_image)
                        genai.configure(api_key=gemini_api_key)
                        model = genai.GenerativeModel("gemini-1.5-flash")
                        prompt = "Ekstrak data tabel dari foto dokumen ini ke format CSV murni dengan kolom: nama, no_hp, nama_pt, jabatan."
                        response = model.generate_content([image, prompt])
                        csv_text = response.text.strip()
                        csv_text = re.sub(r"```(csv)?", "", csv_text).strip()
                        st.session_state['df_prospek'] = pd.read_csv(io.StringIO(csv_text))
                        st.success("Data berhasil diekstrak!")
                    except Exception as e:
                        st.error(f"Gagal memproses: {e}")

# --- TAB 2: UPLOAD EXCEL / DATA RISET ---
with tab2:
    st.subheader("📂 Upload File Excel / Data Riset")
    uploaded_file = st.file_uploader("Unggah file Excel data prospek", type=["xlsx", "csv"])
    if uploaded_file is not None:
        if uploaded_file.name.endswith(".csv"):
            st.session_state['df_prospek'] = pd.read_csv(uploaded_file)
        else:
            st.session_state['df_prospek'] = pd.read_excel(uploaded_file)
        st.success("Data berhasil dimuat!")

# --- OLAH DATA PROSPEK, VCF, & BLASTING ---
if 'df_prospek' in st.session_state and st.session_state['df_prospek'] is not None:
    df = st.session_state['df_prospek']
    
    # Otomatisasi Header: lowercase & spasi jadi underscore
    col_mapping = {}
    for col in df.columns:
        clean_col = str(col).strip().lower().replace(" ", "_")
        col_mapping[col] = clean_col
    df = df.rename(columns=col_mapping)

    nama_col = next((c for c in df.columns if "nama" in c or "name" in c), None)
    hp_col = next((c for c in df.columns if "hp" in c or "phone" in c or "telp" in c or "wa" in c), None)

    if nama_col and hp_col:
        st.success(f"✅ Kolom '{nama_col}' dan '{hp_col}' terdeteksi secara otomatis!")
        
        df = df.rename(columns={nama_col: "nama", hp_col: "no_hp"})

        if "nama_pt" not in df.columns:
            df["nama_pt"] = "-"
        if "jabatan" not in df.columns:
            df["jabatan"] = "-"
        if "match_linkedin" not in df.columns:
            df["match_linkedin"] = True
        if "catatan_update" not in df.columns:
            df["catatan_update"] = ""

        st.markdown("### 📋 Tabel Interaktif Prospek")
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

        df_matched = edited_df[edited_df["match_linkedin"] == True]

        def generate_vcf(dataframe):
            vcf_lines = []
            for _, row in dataframe.iterrows():
                name = str(row["nama"])
                phone_raw = str(row["no_hp"])
                phone = re.sub(r"\D", "", phone_raw)
                if phone.startswith("0"):
                    phone = "62" + phone[1:]
                elif phone.startswith("8"):
                    phone = "62" + phone

                vcf_lines.append("BEGIN:VCARD")
                vcf_lines.append("VERSION:3.0")
                vcf_lines.append(f"FN:{name}")
                vcf_lines.append(f"TEL:{phone}")
                vcf_lines.append("END:VCARD")
            return "\n".join(vcf_lines)

        vcf_data = generate_vcf(df_matched)

        st.markdown("---")
        col_info, col_btn = st.columns([3, 1])
        with col_info:
            st.subheader("📥 Download Kontak VCF")
            st.write(f"Total data siap diunduh ke HP: **{len(df_matched)}** dari **{len(edited_df)}** data.")
        with col_btn:
            st.download_button(
                label="📥 Download VCF",
                data=vcf_data,
                file_name="prospek_wa_blaster.vcf",
                mime="text/vcard",
            )
        st.markdown("---")

        st.subheader("💬 Template Pesan & Blasting WhatsApp")
        template_pesan = st.text_area(
            "Template Pesan WhatsApp (Gunakan tag {Nama}):",
            value="Halo Bapak/Ibu {Nama},\n\nPerkenankan saya Dwi dari Bank CTBC. Kami ingin menginformasikan fasilitas Pinjaman Tanpa Agunan (KTA) dengan bunga ringan.\n\nApakah ada waktu sejenak untuk berdiskusi?",
        )

        st.markdown("### 📋 Daftar Aksi Kirim WhatsApp:")
        for index, row in edited_df.iterrows():
            nama = str(row["nama"])
            no_hp_raw = str(row["no_hp"])
            
            no_hp = re.sub(r"\D", "", no_hp_raw)
            if no_hp.startswith("0"):
                no_hp = "62" + no_hp[1:]
            elif no_hp.startswith("8"):
                no_hp = "62" + no_hp

            is_match = row["match_linkedin"]

            pesan_personal = template_pesan.replace("{Nama}", nama)
            encoded_message = urllib.parse.quote(pesan_personal)
            wa_link = f"https://wa.me/{no_hp}?text={encoded_message}"

            col1, col2 = st.columns([4, 1])
            with col1:
                status_badge = "✅ Match" if is_match else "❌ Skipped"
                st.markdown(f"👤 **{nama}** ({no_hp}) | {status_badge}")
            with col2:
                if is_match:
                    st.markdown(f"[💬 Kirim WA]({wa_link})", unsafe_allow_html=True)
                else:
                    st.markdown("*Dilewati*")
            st.divider()

    else:
        st.warning("⚠️ Kolom 'nama' atau 'no_hp' tidak terdeteksi otomatis. Pastikan ada kolom nama/no_hp pada Excel Anda.")