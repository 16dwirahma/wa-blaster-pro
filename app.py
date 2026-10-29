import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import io
import urllib.parse

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="WA Blaster Pro - Validasi LinkedIn & Kontak VCF",
    page_icon="📱",
    layout="wide"
)

# Inisialisasi API Key Gemini
api_key = None
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

st.sidebar.markdown("### 🔑 Konfigurasi API & Device")
if api_key:
    genai.configure(api_key=api_key)
    st.sidebar.success("Gemini API Key dimuat otomatis dari sistem!")
else:
    user_api_key = st.sidebar.text_input("Masukkan Gemini API Key:", type="password")
    if user_api_key:
        genai.configure(api_key=user_api_key)
        api_key = user_api_key
        st.sidebar.success("API Key berhasil disimpan!")
    else:
        st.sidebar.warning("Silakan masukkan Gemini API Key terlebih dahulu.")

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Setting Device WA")
default_wa = st.sidebar.text_input("Nomor Utama (WA 1):", value="625888140182")
st.sidebar.markdown(f"<div style='background-color: #d4edda; color: #155724; padding: 10px; border-radius: 5px; text-align: center;'><b>WA Active: {default_wa}</b></div>", unsafe_allow_html=True)

# Judul Utama Aplikasi
st.markdown("## 📱 WA Blaster Pro - Validasi LinkedIn & Kontak VCF")
st.markdown("---")

# Tab Menu Utama
tab1, tab2 = st.tabs(["📸 Scan Hardcopy (Foto Doc)", "📁 Upload Excel / Data Riset"])

# --- TAB 1: OCR HARDCOPY ---
with tab1:
    st.markdown("### 📸 Upload Foto Dokumen Hardcopy Database")
    uploaded_image = st.file_uploader("Pilih foto dokumen (JPG/PNG)", type=["jpg", "jpeg", "png"])
    
    if uploaded_image is not None:
        image = Image.open(uploaded_image)
        st.image(image, caption="Dokumen Prospek Terunggah", use_container_width=True)
        
        if st.button("🚀 Proses OCR dengan Gemini AI"):
            if not api_key:
                st.error("Gemini API Key belum dikonfigurasi!")
            else:
                with st.spinner("Mengekstrak data prospek dari gambar..."):
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        prompt = (
                            "Ekstrak data kontak dari gambar ini ke dalam format tabel bersih "
                            "dengan kolom: nama, no_hp, nama_pt, jabatan. "
                            "Pastikan nomor HP diawali dengan format internasional (contoh: 628...). "
                            "Berikan dalam bentuk tabel markdown."
                        )
                        response = model.generate_content([image, prompt])
                        st.markdown("### Hasil Ekstraksi OCR:")
                        st.markdown(response.text)
                    except Exception as e:
                        st.error(f"Terjadi kesalahan saat memproses gambar: {e}")

# --- TAB 2: UPLOAD EXCEL ---
with tab2:
    st.markdown("### 📁 Upload File Excel Database Prospek")
    uploaded_file = st.file_uploader("Pilih file Excel (.xlsx) atau CSV", type=["xlsx", "csv"])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.success(f"File berhasil dimuat! Total baris data: {len(df)}")
            
            # Normalisasi Header Otomatis agar cocok dengan file Excel (nama, no_hp, nama_pt, jabatan)
            df.columns = [str(col).strip().lower() for col in df.columns]
            
            col_nama = next((c for c in df.columns if 'nama' in c and 'pt' not in c), None)
            col_hp = next((c for c in df.columns if 'hp' in c or 'phone' in c or 'whatsapp' in c or 'telp' in c), None)
            col_pt = next((c for c in df.columns if 'pt' in c or 'perusahaan' in c or 'company' in c or 'institution' in c), None)
            col_jabatan = next((c for c in df.columns if 'jabatan' in c or 'title' in c or 'position' in c or 'posisi' in c), None)
            
            if col_nama and col_hp:
                # Standarisasi nomor HP: tambahkan 62 di depan jika diawali angka 8
                def clean_phone(val):
                    val_str = str(val).strip()
                    if val_str.endswith('.0'):
                        val_str = val_str[:-2]
                    val_str = ''.join(filter(str.isdigit, val_str))
                    if val_str.startswith('0'):
                        val_str = '62' + val_str[1:]
                    elif val_str.startswith('62'):
                        pass
                    elif val_str.startswith('8'):
                        val_str = '62' + val_str
                    return val_str

                df['cleaned_hp'] = df[col_hp].apply(clean_phone)
                
                # Tampilkan Preview Data Prospek di Layar (Tanpa kolom cleaned_hp)
                st.markdown("### Preview Data Prospek:")
                display_cols = [c for c in [col_nama, col_hp, col_pt, col_jabatan] if c is not None]
                st.dataframe(df[display_cols].head())
                
                st.markdown("---")
                st.markdown("### 📥 Download Kontak VCF")
                st.markdown(f"Total data siap diunduh ke HP: **{len(df)}** dari **{len(df)}** data.")
                
                # Pembuatan VCF dengan format gabungan Nama (PT - Jabatan) agar langsung muncul di preview kontak HP
                vcf_data = []
                for _, row in df.iterrows():
                    name = str(row[col_nama]).strip() if pd.notna(row[col_nama]) else ""
                    phone = str(row['cleaned_hp']).strip()
                    title = str(row[col_jabatan]).strip() if col_jabatan and pd.notna(row[col_jabatan]) else ""
                    org = str(row[col_pt]).strip() if col_pt and pd.notna(row[col_pt]) else ""
                    
                    # Format Nama Tampilan Kontak agar langsung menyertakan Perusahaan & Jabatan
                    display_name = f"{name} - {org} ({title})" if org and title else name
                    
                    vcf_card = (
                        f"BEGIN:VCARD\n"
                        f"VERSION:3.0\n"
                        f"FN:{display_name}\n"
                        f"N:{name};;;;\n"
                        f"TEL:{phone}\n"
                        f"TITLE:{title}\n"
                        f"ORG:{org}\n"
                        f"END:VCARD\n"
                    )
                    vcf_data.append(vcf_card)
                
                vcf_string = "".join(vcf_data)
                
                st.download_button(
                    label="📥 Download VCF",
                    data=vcf_string,
                    file_name="kontak_prospek_wa_blaster.vcf",
                    mime="text/vcard"
                )
                
                st.markdown("---")
                st.markdown("### 💬 Template Pesan & Blasting WhatsApp")
                
                default_template = "Halo Bapak/Ibu {Nama},\n\nPerkenankan saya Dwi dari Bank CTBC. Kami ingin menginformasikan fasilitas Pinjaman Tanpa Agunan (KTA) dengan bunga ringan."
                message_template = st.text_area("Template Pesan WhatsApp (Gunakan tag {Nama}):", value=default_template, height=120)
                
                st.markdown("### 📋 Daftar Aksi Kirim WhatsApp:")
                
                for _, row in df.iterrows():
                    nama_prospek = str(row[col_nama]) if pd.notna(row[col_nama]) else "-"
                    no_hp_bersih = str(row['cleaned_hp'])
                    no_hp_tampil = str(row[col_hp]) if pd.notna(row[col_hp]) else "-"
                    jabatan_prospek = str(row[col_jabatan]) if col_jabatan and pd.notna(row[col_jabatan]) else "-"
                    pt_prospek = str(row[col_pt]) if col_pt and pd.notna(row[col_pt]) else "-"
                    
                    custom_msg = message_template.replace("{Nama}", nama_prospek)
                    encoded_message = urllib.parse.quote(custom_msg)
                    wa_link = f"https://wa.me/{no_hp_bersih}?text={encoded_message}"
                    
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.markdown(
                            f"👤 **{nama_prospek}**<br>"
                            f"📞 No HP: `{no_hp_tampil}` (WA: `{no_hp_bersih}`)<br>"
                            f"💼 Jabatan: *{jabatan_prospek}*<br>"
                            f"🏢 Perusahaan: **{pt_prospek}** | ✅ Match",
                            unsafe_allow_html=True
                        )
                    with col2:
                        st.markdown(f"<br>[💬 Kirim WA]({wa_link})", unsafe_allow_html=True)
                    st.divider()
                    
            else:
                st.warning("⚠️ Kolom 'nama' atau 'no_hp' tidak terdeteksi otomatis pada file Excel Anda.")
        except Exception as e:
            st.error(f"Gagal membaca file Excel/CSV: {e}")