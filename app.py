import streamlit as st
import pandas as pd
import re
import pdfplumber 
from fpdf import FPDF
import io

# 1. MINERAL CONFIGURATION
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

# --- 2. HELPER FUNCTIONS ---

def clean_val(val):
    """Extracts numeric value from strings like '<0.01' or 'Trace'"""
    if pd.isna(val) or str(val).strip() == "": return 0.0
    s = str(val).lower()
    if any(x in s for x in ['trace', '<', 'n.d', 'nil', 'nd']): return 0.0
    match = re.search(r"[-+]?\d*\.\d+|\d+", s)
    return float(match.group()) if match else 0.0

def create_pdf(val_data, total_value):
    """Generates PDF using 'Times' core font"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", 'B', 16)
    pdf.cell(0, 10, "Thamani Mineral Analysis Report", ln=True, align='C')
    pdf.ln(10)
    
    # Table Header
    pdf.set_font("Times", 'B', 11)
    pdf.cell(50, 10, "Mineral", 1)
    pdf.cell(35, 10, "Oxide %", 1)
    pdf.cell(35, 10, "Element %", 1)
    pdf.cell(60, 10, "Value (TZS/MT)", 1)
    pdf.ln()
    
    # Table Content
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
    return pdf.output(dest='S')

# --- 3. UI SETUP ---

st.set_page_config(page_title="Thamani Analytics", layout="wide")
st.sidebar.title("💎 Menu")
page = st.sidebar.radio("Go to:", ["Welcome Home", "Mineral Scanner"])

if page == "Welcome Home":
    st.title("🔬 Thamani Mineral Analytics")
    st.markdown("""
    ### Welcome to the **Thamani Digital Lab**.
    
    This tool bridges the gap between **Laboratory Science** and **Market Value** for the mining sector.
    
    * ⚡ **Auto-Extract:** Read Excel and PDF reports from any lab.
    * 🧪 **Stoichiometric Conversion:** Convert Oxides to pure Element %.
    * 💰 **Real-time Valuation:** Estimates TZS value per Metric Ton.
    """)
    st.info("👈 Use the sidebar menu to open the **Mineral Scanner**.")
    st.divider()
    st.caption("Developed by Glory Benson | Chemist & Digital Researcher |0616648724")

elif page == "Mineral Scanner":
    st.title("📊 Mineral Valuation Scanner")
    file = st.file_uploader("Upload Lab Report (Excel or PDF)", type=['xlsx', 'pdf'])

    if file:
        extracted = {}
        try:
            # Step 1: Data Extraction
            if file.name.endswith('.pdf'):
                with pdfplumber.open(file) as pdf:
                    content = " ".join([p.extract_text() for p in pdf.pages if p.extract_text()]) 
                search_text = content.upper().replace(" ", "")
                for key in CHEMICAL_MAP.keys():
                    pattern = rf"{key}.*?(\d+\.?\d*)"
                    match = re.search(pattern, search_text)
                    if match:
                        extracted[key] = float(match.group(1))
            else:
                df = pd.read_excel(file).astype(str)
                # Scan entire Excel for keywords
                for r in range(len(df)):
                    for c in range(len(df.columns)):
                        # Adding str() converts the number to text first
                        cell_txt = str(df.iloc[r, c]).strip().upper().replace(" ", "")
                        if cell_txt in CHEMICAL_MAP and c + 1 < len(df.columns):
                            extracted[cell_txt] = clean_val(df.iloc[r, c + 1])
                            # Inside your create_pdf function, ensure this line exists:
                def create_pdf(val_data, total_value):
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", 'B', 12)
    
                              # THIS IS THE MISSING LINK:
                    for item in val_data: 
                                  # Now 'item' is defined for the lines below
                        clean_name = item['Mineral'].replace('$', '').replace('_', '')
                        pdf.cell(50, 10, clean_name, 1)
                        pdf.cell(40, 10, str(item['Oxide %']), 1)
                        pdf.ln()
    
                              # ... rest of your code ...
                 return pdf.output(dest='S')
            # Step 2: Math & Calculations
            # --- 1. THE CALCULATION LOOP ---
            if extracted:
               val_data = []
               total_value = 0
               for k, v in extracted.items():
                   m = CHEMICAL_MAP[k]
                   e_pct = v * m['factor']
    
                # Define it here...
                   price_val = e_pct * m['price'] 
                   val_data.append({
                       "Mineral": m['label'],
                       "Oxide %": round(v, 2),
                       "Element %": round(e_pct, 4),
               # ...and use the SAME name here!
                       "Value (TZS/MT)": round(price_val, 2) 
                   })
                   total_value += price_val # Use it here too

                # Step 3: Display Results
              # 1. Convert your list of results into a DataFrame
                   results_df = pd.DataFrame(val_data)

                # 2. Use st.table instead of st.dataframe
             # This is the ONLY way to make the subscripts look professional
                   st.table(results_df)

                # 3. Use st.metric for the big total at the bottom
                   st.metric("Total Market Value", f"{total_value:,.2f} TZS/MT")
                
                # Step 4: PDF Generation
                   report_pdf = create_pdf(val_data, total_value)
                   st.download_button(
                       label="Download Analysis PDF",
                       data=report_pdf,
                       file_name="Thamani_Valuation_Report.pdf",
                       mime="application/pdf"
                   )
            else:
                st.warning("No minerals recognized. Ensure the file contains labels like SIO2 or FE2O3.")

        except Exception as e:
            st.error(f"Error during processing: {e}")
