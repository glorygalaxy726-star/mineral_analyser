import streamlit as st
import pandas as pd
import re
import pdfplumber 
from fpdf import FPDF
import io

# 1. CONFIGURATION (LaTeX enabled for UI display)
CHEMICAL_MAP = {
    "SIO2": {"label": "$SiO_2$", "factor": 0.4674, "price": 3000},
    "FE2O3": {"label": "$Fe_2O_3$", "factor": 0.6994, "price": 15000},
    "AL2O3": {"label": "$Al_2O_3$", "factor": 0.5293, "price": 12000},
    "CAO": {"label": "$CaO$", "factor": 0.7147, "price": 5000},
    "MGO": {"label": "$MgO$", "factor": 0.6030, "price": 18000},
    "TIO2": {"label": "$TiO_2$", "factor": 0.5993, "price": 45000},
    "PBO": {"label": "$PbO$", "factor": 0.9283, "price": 55000},
    "MNO": {"label": "$MnO$", "factor": 0.7745, "price": 10000},
    "NA2O": {"label": "$Na_2O$", "factor": 0.7419, "price": 8000},
    "K2O": {"label": "$K_2O$", "factor": 0.8302, "price": 9500},
    "C": {"label": "Graphite (C)", "factor": 1.0, "price": 25000},
    "AU": {"label": "Au (Gold)", "factor": 1.0, "price": 180000000},
    "CU": {"label": "Cu (Copper)", "factor": 1.0, "price": 250000},
    "AG": {"label": "Ag (Silver)", "factor": 1.0, "price": 2000000}
}

# --- HELPER FUNCTIONS ---
def create_pdf(val_data, total_value):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", 'B', 16)
    pdf.cell(0, 10, "Thamani Mineral Analysis Report", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Times", 'B', 11)
    pdf.cell(50, 10, "Mineral", 1)
    pdf.cell(35, 10, "Oxide %", 1)
    pdf.cell(35, 10, "Element %", 1)
    pdf.cell(60, 10, "Value (TZS/MT)", 1)
    pdf.ln()
    
    pdf.set_font("Times", '', 10)
    for item in val_data:
        clean_name = item['Mineral'].replace('$', '')
        pdf.cell(50, 10, clean_name, 1)
        pdf.cell(35, 10, f"{item['Oxide %']:.2f}", 1)
        pdf.cell(35, 10, f"{item['Element %']:.2f}", 1)
        pdf.cell(60, 10, f"{item['Value (TZS/MT)']:,.2f}", 1)
        pdf.ln()
    
    pdf.ln(5)
    pdf.set_font("Times", 'B', 12)
    pdf.cell(0, 10, f"TOTAL MARKET VALUE: {total_value:,.2f} TZS/MT", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- UI SETUP ---
st.set_page_config(page_title="Thamani Analytics", layout="wide")
st.sidebar.title("💎 Thamani Menu")
page = st.sidebar.radio("Go to:", ["Welcome Home", "Mineral Scanner"])

if page == "Welcome Home":
    st.title("🔬 Thamani Mineral Analytics")
    st.markdown("### Bridging Laboratory Science and Market Value")
    st.write("Convert laboratory oxide results into stoichiometric element values and market pricing instantly.")
    st.info("👈 Use the sidebar menu to open the **Mineral Scanner**.")

elif page == "Mineral Scanner":
    st.title("📊 Mineral Scanner & Valuation")
    file = st.file_uploader("Upload Lab Report (Excel or PDF)", type=['xlsx', 'pdf'])

    if file:
        extracted = {}
        try:
            if file.name.endswith('.pdf'):
                with pdfplumber.open(file) as pdf:
                    full_content = " ".join([p.extract_text() for p in pdf.pages if p.extract_text()])
            else:
                df = pd.read_excel(file).astype(str)
                full_content = " ".join(df.values.flatten())

            search_text = full_content.upper().replace(" ", "")

            for key in CHEMICAL_MAP.keys():
                pattern = rf"{key}.*?(\d+\.?\d*)"
                match = re.search(pattern, search_text)
                if match:
                    extracted[key] = float(match.group(1))

            if extracted:
                val_data = []
                total_value = 0
                for k, v in extracted.items():
                    m = CHEMICAL_MAP[k]
                    e_pct = v * m['factor']
                    price_val = e_pct * m['price']
                    
                    val_data.append({
                        "Mineral": m['label'],
                        "Oxide %": v,
                        "Element %": e_pct,
                        "Value (TZS/MT)": price_val
                    })
                    total_value += price_val

                st.write("### Analysis Results")
                st.dataframe(pd.DataFrame(val_data), use_container_width=True)
                st.metric("Estimated Total Value", f"{total_value:,.2f} TZS/MT")
                
                report_pdf = create_pdf(val_data, total_value)
                st.download_button(
                    label="Download Analysis PDF",
                    data=report_pdf,
                    file_name="Thamani_Valuation_Report.pdf",
                    mime="application/pdf"
                )
            else:
                st.warning("No minerals recognized. Ensure the file contains labels like SIO2, FE2O3, etc.")

        except Exception as e:
            st.error(f"Error during processing: {e}")

    st.title("🔬 Thamani Mineral Analytics")
    st.markdown("""
    ### Welcome to the **Thamani Digital Lab**.
    
    This tool is designed for chemists,miners and mineral traders in Tanzania and world in general to quickly convert laboratory oxide results into 
    marketable element values.This tool bridges the gap between **Laboratory Science** and **Market Value** for the Tanzanian mining sector.
    
    **What you can do here:**
    
    * ⚡ **Auto-Extract:** Read Excel and pdf reports from any lab in Tanzania.
    
    * 🧪 **Stoichiometric conversion:** Convert Oxides (PbO, Na2O) to pure Element %.
    
    * 💰 **Real-time Valuation:** Estimates TZS value per Metric Ton based on purity.
    """)
    
    st.info("👈 Use the sidebar menu to open the **Mineral Scanner**.")
    st.divider()
    st.caption("Developed by Glory Benson | Chemist & digital researcher")
# --- 4. PAGE 2: MINERAL SCANNER ---
elif page == "Mineral Scanner":
    st.title("📊 Professional Mineral Valuation")
    st.write("Upload your Excel or pdf lab report below.")
    file = st.file_uploader("Upload Lab Report (Excel or PDF)", type=['xlsx', 'pdf'])

    if file:
        extracted = {}
        # Use .get() to avoid crashes if a key is missing
        for key, oxide_pct in extracted.items():
            meta = CHEMICAL_MAP.get(key)
    if meta:
        element_pct = oxide_pct * meta['factor']
        # ... rest of your math
        
                # Calculation Logic
        val_data = []
        total_value = 0
        for key, oxide_pct in extracted.items():
            meta = CHEMICAL_MAP[key]
            e_pct = oxide_pct * meta['factor']
            m_val = e_pct * meta['price']
            val_data.append({
                "Mineral": meta['label'],
                "Oxide %": oxide_pct,
                "Element %": round(e_pct, 4),
                "Value (TZS/MT)": round(m_val, 2)
            })
            total_value += m_val

        # Display Results
        st.table(pd.DataFrame(val_data))
        st.metric("Total Value", f"{total_value:,.2f} TZS/MT")
    
        # --- IF PDF ---
        if file.name.endswith('.pdf'):
            reader = pypdf.PdfReader(file)
            text = " ".join([page.extract_text() for page in reader.pages]).upper()
            for key in CHEMICAL_MAP.keys():
                if key in text:
                    match = re.search(rf"{key}\s*[:=-]?\s*(\d*\.?\d+)", text)
                    if match: extracted[key] = float(match.group(1))
        
        # --- IF EXCEL ---
        else:
            df = pd.read_excel(file, header=None)
            for r in range(len(df)):
                for c in range(len(df.columns)):
                    cell = str(df.iloc[r, c]).strip().upper().replace(" ", "")
                    if cell in CHEMICAL_MAP and c + 1 < len(df.columns):
                        extracted[cell] = clean_val(df.iloc[r, c + 1])

        # --- RESULTS (Same for both) ---
        if extracted:
            # (Your existing math loop for val_data and total_value goes here)
            st.table(val_data)
            st.metric("Total Value", f"{total_value:,.2f} TZS/MT")
            
            pdf_bytes = create_pdf(val_data, total_value)
            st.download_button("Download Analysis PDF", pdf_bytes, "analysis.pdf")
                    
        else:
            st.warning("No matching mineral labels found in the file.")
if file:
    try:
        # (All your Excel/PDF analysis code)
        if extracted:
            st.table(val_data)
            st.metric("Total Value", f"{total_value:,.2f}")
                
            # PDF Generation & Download
            pdf_bytes = create_pdf(val_data, total_value)
            st.download_button("Download Analysis PDF", pdf_bytes, "analysis.pdf")
        else:
            st.warning("No minerals found.")

    except Exception as e:
            st.error(f"Error: {e}")
        
