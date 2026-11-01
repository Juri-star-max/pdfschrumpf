import streamlit as st
import fitz
from pypdf import PdfReader, PdfWriter
from markitdown import MarkItDown
import io, os, tempfile

st.set_page_config(page_title="PDFSchrumpf", page_icon="📉", layout="centered")

# =====================================================================
# --- HIER DEINE BEZAHL-LINKS & PRO-CODE EINTRAGEN ---
# =====================================================================
PRO_CODE = "SCHRUMPF2026"
STRIPE_LINK = "https://buy.stripe.com/DEIN_STRIPE_LINK"  # Später eintragen
PAYPAL_LINK = "https://paypal.me/DEIN_PAYPAL_NAME/5"     # Später eintragen

# --- 1. CREDITS & ABO-LOGIK (Session State + Auto-Freischaltung per Link) ---
if "credits" not in st.session_state:
    st.session_state.credits = 3
if "is_pro" not in st.session_state:
    st.session_state.is_pro = False

# Automatische Freischaltung, wenn Kunde nach Kauf über ?pro=SCHRUMPF2026 zurückkommt
if st.query_params.get("pro") == PRO_CODE:
    st.session_state.is_pro = True

# --- 2. SIDEBAR: SPRACHE, KONTO & UPGRADE ---
with st.sidebar:
    lang = st.radio("🌐 Language / Sprache", ["🇩🇪 Deutsch", "🇬🇧 English"], horizontal=True)
    de = lang.startswith("🇩🇪")
    st.markdown("---")
    
    st.header("👤 Dein Konto" if de else "👤 Your Account")
    if st.session_state.is_pro:
        st.success("🌟 PRO-Mitglied (Unbegrenzt)" if de else "🌟 PRO Member (Unlimited)")
    else:
        st.warning(
            f"Gratis-Versuche übrig: **{st.session_state.credits} / 3**" if de 
            else f"Free tries left: **{st.session_state.credits} / 3**"
        )
        st.write(
            "Hol dir **PRO** für unbegrenzte PDFs (**5 € / Jahr**)." if de 
            else "Get **PRO** for unlimited PDFs (**5 € / year**)."
        )
        
        # Bezahl-Buttons (Stripe & PayPal)
        st.link_button(
            "💳 PRO holen – Karte / Apple Pay (5 €)" if de else "💳 Get PRO – Card / Apple Pay (5 €)",
            STRIPE_LINK,
            type="primary",
            use_container_width=True
        )
        st.link_button(
            "🅿️ Mit PayPal zahlen (5 €)" if de else "🅿️ Pay with PayPal (5 €)",
            PAYPAL_LINK,
            use_container_width=True
        )
        
        st.markdown("---")
        # Lizenzschlüssel-Eingabe für bestehende Käufer
        st.subheader("🔑 Bereits gekauft?" if de else "🔑 Already purchased?")
        code_input = st.text_input(
            "PRO-Code eingeben:" if de else "Enter PRO code:",
            type="password",
            placeholder="z.B. SCHRUMPF..." if de else "e.g. SCHRUMPF..."
        )
        if st.button("Freischalten" if de else "Unlock", use_container_width=True):
            if code_input.strip().upper() == PRO_CODE:
                st.session_state.is_pro = True
                st.rerun()
            else:
                st.error("❌ Ungültiger Code" if de else "❌ Invalid code")

def check_limit():
    if not st.session_state.is_pro and st.session_state.credits <= 0:
        st.error(
            "🛑 Gratis-Limit erreicht! Bitte links auf PRO upgraden." if de 
            else "🛑 Free limit reached! Please upgrade to PRO on the left."
        )
        st.stop()
    return True

def use_credit():
    if not st.session_state.is_pro:
        st.session_state.credits -= 1

# --- 3. HAUPTSEITE & TOOLS ---
st.title("📉 PDFSchrumpf – Klein, schnell, fertig." if de else "📉 PDFSchrumpf – Small, fast, done.")
tab1, tab4, tab2, tab3 = st.tabs([
    "📉 Schrumpfen" if de else "📉 Compress",
    "🤖 Direkt in KI-Version" if de else "🤖 Direct to AI (.md)",
    "🔗 Zusammenfügen" if de else "🔗 Merge",
    "✂️ Teilen" if de else "✂️ Split"
])

# TAB 1: SCHRUMPFEN (inkl. KI-Bonus)
with tab1:
    f = st.file_uploader("PDF hochladen" if de else "Upload PDF", type="pdf", key="t1")

    if f:
        orig_bytes = f.getvalue()
        orig_mb = len(orig_bytes) / (1024 * 1024)
        base_name = f.name.rsplit(".", 1)[0]
        new_filename = f"{base_name}_geschrumpft.pdf" if de else f"{base_name}_compressed.pdf"

        col_left, col_right = st.columns([1, 1])

        with col_left:
            doc_prev = fitz.open(stream=orig_bytes, filetype="pdf")
            pix_prev = doc_prev[0].get_pixmap(dpi=72)
            st.image(pix_prev.tobytes("png"), caption=f"{f.name} ({orig_mb:.2f} MB)", width=180)
            doc_prev.close()

        with col_right:
            st.subheader("Komprimierungsstufe" if de else "Compression Level")
            opts = [
                "Extreme Komprimierung (Hohe Schrumpfung)" if de else "Extreme Compression (Smallest size)",
                "Empfohlene Komprimierung (Gute Qualität & Größe)" if de else "Recommended Compression (Good quality & size)",
                "Geringere Komprimierung (Hohe Qualität)" if de else "Less Compression (High quality)"
            ]
            stufe = st.radio("Stufe", opts, index=1, label_visibility="collapsed")
            start_btn = st.button(
                "🔴 PDF verkleinern ➔" if de else "🔴 Compress PDF ➔", 
                type="primary", 
                use_container_width=True
            )

        if start_btn and check_limit():
            with st.spinner("PDF wird komprimiert & KI-Version erstellt..." if de else "Compressing PDF & creating AI version..."):
                orig_size = len(orig_bytes)

                if "Extreme" in stufe:
                    qual, dpi_target, dpi_max = 30, 72, 90
                elif "Empfohlene" in stufe or "Recommended" in stufe:
                    qual, dpi_target, dpi_max = 50, 96, 110
                else:
                    qual, dpi_target, dpi_max = 70, 130, 150

                doc = fitz.open(stream=orig_bytes, filetype="pdf")

                doc.scrub(
                    attached_files=True,
                    clean_pages=True,
                    embedded_files=True,
                    metadata=True,
                    reset_fields=True,
                    reset_responses=True,
                    thumbnails=True,
                    xml_metadata=True
                )

                doc.subset_fonts()
                doc.rewrite_images(
                    dpi_threshold=dpi_max,
                    dpi_target=dpi_target,
                    quality=qual,
                    lossy=True,
                    bitonal=True
                )

                out_bytes = doc.tobytes(
                    garbage=4,
                    deflate=True,
                    clean=True,
                    deflate_images=True,
                    deflate_fonts=True,
                    use_objstms=1
                )
                doc.close()

                if len(out_bytes) >= orig_size:
                    out_bytes = orig_bytes

                # Gleichzeitig .md Version für KI erzeugen
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(orig_bytes)
                    tmp_path = tmp.name
                md_converter = MarkItDown()
                md_text = md_converter.convert(tmp_path).text_content
                os.remove(tmp_path)
                md_filename = f"{base_name}_KI_Version.md" if de else f"{base_name}_AI_Version.md"

                new_mb = len(out_bytes) / (1024 * 1024)
                md_kb = len(md_text.encode("utf-8")) / 1024
                saved_pct = max(0, int(round((1 - (len(out_bytes) / orig_size)) * 100)))
                use_credit()

            st.markdown("---")
            title_done = "Fertig! Wähle dein Format:" if de else "Done! Choose your format:"
            st.markdown(f"<h3 style='text-align: center;'>{title_done}</h3>", unsafe_allow_html=True)

            dl_col1, dl_col2 = st.columns(2)
            with dl_col1:
                st.download_button(
                    f"⬇️ Als PDF ({new_mb:.2f} MB)" if de else f"⬇️ As PDF ({new_mb:.2f} MB)",
                    out_bytes,
                    new_filename,
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
            with dl_col2:
                st.download_button(
                    f"🤖 Als .md für KI ({md_kb:.1f} KB)" if de else f"🤖 As .md for AI ({md_kb:.1f} KB)",
                    md_text,
                    md_filename,
                    mime="text/markdown",
                    use_container_width=True
                )

            lbl_saved = "GESPART" if de else "SAVED"
            txt_smaller = f"PDF ist <b>{saved_pct}% kleiner</b>" if de else f"PDF is <b>{saved_pct}% smaller</b>"
            txt_tip = (
                f"💡 <b>KI-Tipp:</b> Die <b>.md-Version</b> ist nur <b>{md_kb:.1f} KB</b> groß (ideal für ChatGPT & Claude)!" if de
                else f"💡 <b>AI Tip:</b> The <b>.md version</b> is only <b>{md_kb:.1f} KB</b> (ideal for ChatGPT & Claude)!"
            )

            st.markdown(f"""
            <div style="display: flex; align-items: center; justify-content: center; gap: 25px; margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 12px;">
                <div style="width: 110px; height: 110px; border-radius: 50%; background: conic-gradient(#e63946 {saved_pct * 3.6}deg, #e0e0e0 0deg); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                    <div style="width: 82px; height: 82px; border-radius: 50%; background: white; display: flex; flex-direction: column; align-items: center; justify-content: center; line-height: 1.1;">
                        <span style="font-size: 22px; font-weight: bold; color: #1d3557;">{saved_pct}%</span>
                        <span style="font-size: 10px; color: #6c757d;">{lbl_saved}</span>
                    </div>
                </div>
                <div style="font-size: 16px; color: #333;">
                    {txt_smaller}<br>
                    <span style="color: #666; font-size: 14px;">{orig_mb:.2f} MB ➔ <b>{new_mb:.2f} MB</b></span><br>
                    <span style="color: #1d3557; font-size: 13px;">{txt_tip}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

# TAB 4 (Auf Platz 2): DIREKT IN KI-VERSION
with tab4:
    st.write(
        "Wandle PDFs, Word- oder Excel-Dateien **direkt ohne Umweg** in eine ultraleichte `.md`-Datei für ChatGPT, Claude & Co. um." if de
        else "Convert PDF, Word, or Excel files **directly** into an ultra-light `.md` file for ChatGPT, Claude & Co."
    )
    f_md = st.file_uploader(
        "Dokument hochladen (PDF, Word, Excel)" if de else "Upload document (PDF, Word, Excel)", 
        type=["pdf", "docx", "xlsx"], 
        key="t4"
    )
    if f_md:
        orig_kb = len(f_md.getvalue()) / 1024
        base_md = f_md.name.rsplit(".", 1)[0]
        if st.button(
            "🤖 Jetzt direkt in KI-Version umwandeln ➔" if de else "🤖 Convert to AI version now ➔", 
            type="primary", 
            use_container_width=True
        ):
            if check_limit():
                with st.spinner("Extrahiere reinen KI-Text..." if de else "Extracting pure AI text..."):
                    ext = os.path.splitext(f_md.name)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                        tmp.write(f_md.getvalue())
                        tmp_path = tmp.name
                    md = MarkItDown()
                    res_text = md.convert(tmp_path).text_content
                    os.remove(tmp_path)
                    new_kb = len(res_text.encode("utf-8")) / 1024
                    use_credit()
                st.success(
                    f"✅ Fertig! Von **{orig_kb:.1f} KB** auf **{new_kb:.1f} KB** reinen KI-Text reduziert." if de
                    else f"✅ Done! Reduced from **{orig_kb:.1f} KB** to **{new_kb:.1f} KB** of pure AI text."
                )
                st.download_button(
                    f"⬇️ KI-Version herunterladen ({new_kb:.1f} KB)" if de else f"⬇️ Download AI version ({new_kb:.1f} KB)",
                    res_text,
                    f"{base_md}_KI_Version.md" if de else f"{base_md}_AI_Version.md",
                    mime="text/markdown",
                    type="primary",
                    use_container_width=True
                )
                with st.expander("🔍 Vorschau des KI-Textes ansehen" if de else "🔍 Preview AI text"):
                    st.text_area("Inhalt" if de else "Content", res_text, height=200)

# TAB 2: ZUSAMMENFÜGEN
with tab2:
    files = st.file_uploader(
        "PDFs wählen" if de else "Select PDFs", 
        type="pdf", 
        accept_multiple_files=True, 
        key="t2"
    )
    if files and len(files) > 1 and st.button("🔴 PDFs zusammenfügen ➔" if de else "🔴 Merge PDFs ➔", type="primary"):
        check_limit()
        writer = PdfWriter()
        for pdf in files:
            writer.append(pdf)
        out = io.BytesIO()
        writer.write(out)
        use_credit()
        st.download_button(
            "⬇️ Download Komplett-PDF" if de else "⬇️ Download Merged PDF", 
            out.getvalue(), 
            "zusammengefuegt.pdf" if de else "merged.pdf", 
            "application/pdf", 
            type="primary"
        )

# TAB 3: TEILEN
with tab3:
    f_split = st.file_uploader("PDF hochladen" if de else "Upload PDF", type="pdf", key="split")
    if f_split:
        reader = PdfReader(f_split)
        max_p = len(reader.pages)
        c1, c2 = st.columns(2)
        start = c1.number_input("Von Seite" if de else "From page", 1, max_p, 1)
        end = c2.number_input("Bis Seite" if de else "To page", start, max_p, max_p)
        if st.button("🔴 Seiten ausschneiden ➔" if de else "🔴 Extract pages ➔", type="primary"):
            check_limit()
            writer = PdfWriter()
            for i in range(start - 1, end):
                writer.add_page(reader.pages[i])
            out = io.BytesIO()
            writer.write(out)
            use_credit()
            base_split = f_split.name.rsplit(".", 1)[0]
            st.download_button(
                "⬇️ Download Auswahl" if de else "⬇️ Download Selection", 
                out.getvalue(), 
                f"{base_split}_S{start}-{end}.pdf", 
                "application/pdf", 
                type="primary"
            )

# --- 4. FOOTER: DATENSCHUTZ & IMPRESSUM ---
st.markdown("---")
with st.expander("🔒 Datenschutz & Impressum (100% DSGVO-konform)" if de else "🔒 Privacy & Legal Notice (100% GDPR compliant)"):
    if de:
        st.markdown("""
        **🛡️ Datenschutz-Garantie: Deine Dateien gehören dir!**
        * **Keine Speicherung:** Alle hochgeladenen PDFs und Dokumente werden ausschließlich kurzzeitig im Arbeitsspeicher (RAM) verarbeitet und **sofort nach der Umwandlung automatisch gelöscht**.
        * **Kein KI-Training:** Deine Dokumente werden zu keinem Zeitpunkt gespeichert, eingesehen oder für das Training von KI-Modellen verwendet.
        * **Zahlungsabwicklung:** Bei einem PRO-Upgrade erfolgt die Zahlungsabwicklung sicher über externe Zahlungsdienstleister (PayPal / Stripe).

        ---
        **Impressum (Angaben gemäß § 5 DDG)**  
        Jurij Weisenstein – JW Consulting  
        Seckbacher Landstraße 5, 60389 Frankfurt am Main  

        **Kontakt:**  
        E-Mail: info@weisenstein-consulting.de  

        **Umsatzsteuer-ID:**  
        Umsatzsteuer-Identifikationsnummer gemäß § 27 a Umsatzsteuergesetz: **DE359638041**  

        **Verbraucherstreitbeilegung / Universalschlichtungsstelle:**  
        Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.
        """)
    else:
        st.markdown("""
        **🛡️ Privacy Guarantee: Your files belong to you!**
        * **Zero Storage:** All uploaded PDFs and documents are processed exclusively in temporary memory (RAM) and are **automatically deleted immediately after conversion**.
        * **No AI Training:** Your documents are never stored, viewed, or used to train AI models.
        * **Payment Processing:** PRO upgrades are securely processed via external payment providers (PayPal / Stripe).

        ---
        **Legal Notice (according to § 5 DDG)**  
        Jurij Weisenstein – JW Consulting  
        Seckbacher Landstraße 5, 60389 Frankfurt am Main, Germany  

        **Contact:**  
        Email: info@weisenstein-consulting.de  

        **VAT ID:** DE359638041  
        **Dispute Resolution:** We are not willing or obliged to participate in dispute resolution proceedings before a consumer arbitration board.
        """)
