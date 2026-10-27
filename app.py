import streamlit as st
import pandas as pd
import urllib.parse

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="WA-Blaster & Contact CRM Pro",
    page_icon="📱",
    layout="wide"
)

st.title("📱 WA-Blaster & Contact Management Pro")
st.markdown("Aplikasi otomatisasi riset prospek, ekspor kontak (.vcf), dan generator kirim pesan massal KTA Bank CTBC.")

# Sidebar Status & Simulator Multi-Device WA
st.sidebar.header("⚙️ Konfigurasi Multi-Device WA")
num_devices = st.sidebar.selectbox("Pilih Jumlah Device WA Aktif:", [1, 2, 3], index=2)

device_1 = st.sidebar.text_input("Nomor Utama (WA 1):", "6281200000001")
device_2 = st.sidebar.text_input("Nomor Cadangan 1 (WA 2):", "6281200000002") if num_devices >= 2 else None
device_3 = st.sidebar.text_input("Nomor Cadangan 2 (WA 3):", "6281200000003") if num_devices >= 3 else None

st.sidebar.markdown("---")
st.sidebar.subheader("Status Koneksi Device")
st.sidebar.success(f"🟢 WA 1: {device_1} (Connected)")
if device_2:
    st.sidebar.info(f"🔵 WA 2: {device_2} (Ready)")
if device_3:
    st.sidebar.warning(f"🟡 WA 3: {device_3} (Standby)")

# Bagian 1: Upload & Filter Data Prospek
st.header("1. Upload & Filter Data Prospek")
uploaded_file = st.file_uploader(
    "Unggah file Excel (.xlsx) atau CSV data nasabah", type=["xlsx", "csv"]
)

if uploaded_file is not None:
    try:
        # Membaca file dengan dtype=str agar nomor HP tetap akurat sebagai string
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, dtype=str)
        else:
            df = pd.read_excel(uploaded_file, dtype=str)
            
        total_original = len(df)

        # Kolom Pencarian / Filter
        search_term = st.text_input("🔍 Cari berdasarkan Nama, Jabatan, atau Perusahaan:", "")
        
        if search_term:
            df_filtered = df[df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)].copy()
        else:
            df_filtered = df.copy()

        st.markdown(f"📊 **{len(df_filtered)} of {total_original} rows displayed** (Data aktif setelah filter)")
        st.dataframe(df_filtered, use_container_width=True)

        # Bagian 2: Ekspor Kontak ke Format VCF
        st.markdown("---")
        st.header("2. Ekspor Kontak ke VCF (Untuk WhatsApp / HP)")
        st.markdown("Ubah data prospek di atas menjadi file kontak `.vcf` agar bisa langsung diimpor ke handphone.")

        col1, col2 = st.columns(2)
        with col1:
            name_column = st.selectbox("Pilih Kolom Nama:", df.columns, index=1 if "Nama" in df.columns else 0)
        with col2:
            phone_column = st.selectbox("Pilih Kolom No HP:", df.columns, index=2 if "No_Hp" in df.columns else 0)

        if st.button("🚀 Generate File VCF"):
            vcf_content = ""
            for index, row in df_filtered.iterrows():
                nama = str(row[name_column])
                hp = str(row[phone_column])
                
                vcf_content += "BEGIN:VCARD\n"
                vcf_content += "VERSION:3.0\n"
                vcf_content += f"FN:{nama}\n"
                vcf_content += f"TEL:{hp}\n"
                vcf_content += "END:VCARD\n"

            st.download_button(
                label="📥 Download File .VCF Sekarang",
                data=vcf_content,
                file_name="prospek_kta_ctbc.vcf",
                mime="text/vcard"
            )

        # Bagian 3: WA Blaster & Auto Message Generator (Tanpa Sebut Jabatan & PT)
        st.markdown("---")
        st.header("3. WhatsApp Blaster & Auto Direct Message")
        st.markdown("Buat template pesan KTA CTBC yang dipersonalisasi dan kirim pesan secara cepat via direct link.")

        # Template Pesan Default (Tanpa Jabatan & PT)
        default_template = (
            "Halo Bapak/Ibu {Nama},\n\n"
            "Perkenalkan saya Dwi dari Bank CTBC. "
            "Kami ingin menginformasikan fasilitas Pinjaman Tanpa Agunan (KTA) dengan bunga ringan dan proses cepat tanpa jaminan.\n\n"
            "Apakah ada waktu sejenak untuk berdiskusi lebih lanjut?"
        )
        
        message_template = st.text_area("✍️ Template Pesan WhatsApp (Gunakan tag {Nama}):", value=default_template, height=150)

        if st.button("⚡ Generate Link WA Blaster"):
            devices = [d for d in [device_1, device_2, device_3] if d]
            
            wa_links = []
            assigned_devices = []
            
            for idx, (_, row) in enumerate(df_filtered.iterrows()):
                nama = str(row[name_column])
                hp = str(row[phone_column]).strip().replace("-", "").replace(" ", "").replace("+", "")
                
                # Format 62 jika berawalan 0
                if hp.startswith("0"):
                    hp = "62" + hp[1:]

                # Format isi pesan personal (hanya memanggil {Nama})
                pesan_custom = message_template.format(Nama=nama)
                pesan_encoded = urllib.parse.quote(pesan_custom)

                # Link Direct WA
                link_wa = f"https://wa.me/{hp}?text={pesan_encoded}"
                wa_links.append(link_wa)

                # Rotasi Device Sender
                sender_device = devices[idx % len(devices)]
                assigned_devices.append(sender_device)

            df_filtered["Pengirim (Device)"] = assigned_devices
            df_filtered["Direct Link WA"] = wa_links

            st.success("✅ Link WA Blaster berhasil dibuat! Rotasi nomor aktif untuk mencegah batasan WA.")
            
            # Tampilkan Tabel Hasil dengan Link WA Aktif
            st.write("📋 **Daftar Target Blasting & Link Langsung:**")
            
            for i, row in df_filtered.iterrows():
                col_info, col_btn = st.columns([3, 1])
                with col_info:
                    st.write(f"👤 **{row[name_column]}** ({row[phone_column]}) | *Sender: {row['Pengirim (Device)']}*")
                with col_btn:
                    st.link_button("📲 Kirim WA", row["Direct Link WA"])

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses data: {e}")
else:
    st.info("Silakan unggah file Excel (.xlsx) terlebih dahulu untuk mulai mengelola data prospek.")