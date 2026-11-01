import io
import cv2
import numpy as np
import pandas as pd
import pytesseract
import streamlit as st

# Konfigurasi Path Tesseract OCR di Windows
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

st.set_page_config(
    page_title="Universal Document & PDF Scanner",
    page_icon="📄",
    layout="centered",
)

st.markdown(
    """
    <h2 style='text-align: center;'>📄 Universal Document & PDF Scanner</h2>
    <p style='text-align: center; color: gray;'>Konversi PDF CamScanner & Foto Hardcopy langsung ke Excel (.xlsx).</p>
""",
    unsafe_allow_html=True,
)

# Upload File (Mendukung PDF, JPG, PNG)
uploaded_file = st.file_uploader(
    "Unggah File Dokumen (PDF CamScanner / Foto JPG / PNG)",
    type=["pdf", "jpg", "jpeg", "png"],
)

if uploaded_file is not None:
  file_type = uploaded_file.name.split(".")[-1].lower()

  if st.button("🔍 Proses & Konversi ke Excel", type="primary"):
    with st.spinner(
        "Sedang memindai halaman PDF/Dokumen dan menyusun tabel..."
    ):
      try:
        table_rows = []

        # ==========================================
        # JIKA FILE ADALAH PDF (CamScanner)
        # ==========================================
        if file_type == "pdf":
          import fitz  # PyMuPDF untuk konversi halaman PDF ke gambar

          doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")

          for page in doc:
            # Render halaman PDF menjadi gambar beresolusi tinggi (Zoom 2x agar tajam)
            pix = page.get_pixmap(dpi=200)
            img_bytes = pix.tobytes("png")
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Proses OCR menggunakan Tesseract dengan koordinat baris/kolom
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            thresh = cv2.adaptiveThreshold(
                gray,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11,
                2,
            )

            custom_config = r"--oem 3 --psm 6"
            data = pytesseract.image_to_data(
                thresh, config=custom_config, output_type=pytesseract.Output.DICT
            )

            n_boxes = len(data["text"])
            lines_dict = {}

            for i in range(n_boxes):
              text = data["text"][i].strip()
              if text:
                y_coord = data["top"][i]
                line_key = round(y_coord / 15) * 15
                if line_key not in lines_dict:
                  lines_dict[line_key] = []
                lines_dict[line_key].append((data["left"][i], text))

            for line_key in sorted(lines_dict.keys()):
              sorted_line_words = sorted(
                  lines_dict[line_key], key=lambda x: x[0]
              )
              row_texts = [word[1] for word in sorted_line_words]
              if row_texts:
                table_rows.append(row_texts)

        # ==========================================
        # JIKA FILE ADALAH GAMBAR (JPG / PNG)
        # ==========================================
        else:
          file_bytes = np.asarray(
              bytearray(uploaded_file.read()), dtype=np.uint8
          )
          img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

          gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
          thresh = cv2.adaptiveThreshold(
              gray,
              255,
              cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
              cv2.THRESH_BINARY,
              11,
              2,
          )

          custom_config = r"--oem 3 --psm 6"
          data = pytesseract.image_to_data(
              thresh, config=custom_config, output_type=pytesseract.Output.DICT
          )

          n_boxes = len(data["text"])
          lines_dict = {}

          for i in range(n_boxes):
            text = data["text"][i].strip()
            if text:
              y_coord = data["top"][i]
              line_key = round(y_coord / 15) * 15
              if line_key not in lines_dict:
                lines_dict[line_key] = []
              lines_dict[line_key].append((data["left"][i], text))

          for line_key in sorted(lines_dict.keys()):
            sorted_line_words = sorted(lines_dict[line_key], key=lambda x: x[0])
            row_texts = [word[1] for word in sorted_line_words]
            if row_texts:
              table_rows.append(row_texts)

        # ==========================================
        # PENYUSUNAN TABEL KE DATAFRAME & EXCEL
        # ==========================================
        if table_rows:
          max_cols = max(len(r) for r in table_rows) if table_rows else 1
          normalized_rows = [
              r + [""] * (max_cols - len(r)) for r in table_rows
          ]

          df = pd.DataFrame(normalized_rows)

          st.success("Berhasil memindai file PDF CamScanner ke Excel!")
          st.dataframe(df, use_container_width=True)

          buffer = io.BytesIO()
          with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, header=False)

          st.download_button(
              label="📥 Download Hasil Excel (.xlsx)",
              data=buffer.getvalue(),
              file_name="scanned_camscanner_data.xlsx",
              mime=(
                  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
              ),
              use_container_width=True,
          )
        else:
          st.warning("Gagal membaca isi tabel dari file.")

      except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses file: {e}")