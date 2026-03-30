import streamlit as st
import pandas as pd
import re

# 1. Configuration & Constants
CHEMICAL_MAP = {
    "SIO2": {"label": "SiO$_2$", "factor": 0.4674, "symbol": "Si", "price": 3000},
    "FE2O3": {"label": "Fe$_2$O$_3$", "factor": 0.6994, "symbol": "Fe", "price": 15000},
    "AL2O3": {"label": "Al$_2$O$_3$", "factor": 0.5293, "symbol": "Al", "price": 12000},
    "CAO": {"label": "CaO", "factor": 0.7147, "symbol": "Ca", "price": 5000},
    "MGO": {"label": "MgO", "factor": 0.6030, "symbol": "Mg", "price": 18000},
    "TIO2": {"label": "TiO$_2$", "factor": 0.5993, "symbol": "Ti", "price": 45000},
    "PBO": {"label": "PbO", "factor": 0.9283, "symbol": "Pb", "price": 55000}, # Lead Oxide
    "MNO": {"label": "MnO", "factor": 0.7745, "symbol": "Mn", "price": 10000},
    "SIO2": {"label": "SiO$_2$", "factor": 0.4674, "symbol": "Si", "price": 3000},
    
    # SODIUM & POTASSIUM (Commonly as Oxides)
    "NA2O": {"label": "Na$_2$O", "factor": 0.7419, "symbol": "Na", "price": 8000},
    "K2O": {"label": "K$_2$O", "factor": 0.8302, "symbol": "K", "price": 9500},
    
    # GRAPHITE / CARBON (Free Element / Factor = 1.0)
    "C": {"label": "Graphite (C)", "factor": 1.0, "symbol": "C", "price": 25000},
    "GRAPHITE": {"label": "Graphite (C)", "factor": 1.0, "symbol": "C", "price": 25000},
    # FREE ELEMENTS (Factor = 1.0)
    "AU": {"label": "Au (Gold)", "factor": 1.0, "symbol": "Au", "price": 180000000}, # Price per 1% per Ton
    "CU": {"label": "Cu (Copper)", "factor": 1.0, "symbol": "Cu", "price": 250000},
    "AG": {"label": "Ag (Silver)", "factor": 1.0, "symbol": "Ag", "price": 2000000}
}

def clean_val(val):
    """Zero-Error Number Extractor"""
    if pd.isna(val) or str(val).strip() == "": return 0.0
    s = str(val).lower()
    if any(x in s for x in ['trace', '<', 'n.d', 'nil', 'nd']): return 0.0
    # Use regex to find only digits and decimals
    match = re.search(r"[-+]?\d*\.\d+|\d+", s)
    return float(match.group()) if match else 0.0



# --- 2. PAGE NAVIGATION SETUP ---
st.set_page_config(page_title="Thamani Analytics", layout="wide")

# Sidebar Menu
st.sidebar.title("💎 Thamani Menu")
page = st.sidebar.radio("Go to:", ["Welcome Home", "Mineral Scanner"])

# --- 3. PAGE 1: WELCOME HOME ---
if page == "Welcome Home":
    st.title("🔬 Thamani Mineral Analytics")
    st.markdown("""
    ### Welcome to the **Thamani Digital Lab**.
    
    This tool is designed for chemists and mineral traders in Tanzania and world in general to quickly convert laboratory oxide results into 
    marketable element values.This tool bridges the gap between **Laboratory Science** and **Market Value** for the Tanzanian mining sector.
    
    **What you can do here:**
    
    * ⚡ **Auto-Extract:** Read Excel reports from any lab in Tanzania.
    
    * 🧪 **Stoichiometric conversion:** Convert Oxides (PbO, Na2O) to pure Element %.
    
    * 💰 **Real-time Valuation:** Estimates TZS value per Metric Ton based on purity.
    """)
    
    st.info("👈 Use the sidebar menu to open the **Mineral Scanner**.")
    st.divider()
    st.caption("Developed by Glory Benson | Chemist & digital researcher")
# --- 4. PAGE 2: MINERAL SCANNER ---
elif page == "Mineral Scanner":
    st.title("📊 Professional Mineral Valuation")
    st.write("Upload your Excel lab report below.")

    file = st.file_uploader("Upload Lab Report (.xlsx)", type=['xlsx'])
    if file is not None:
      try:
        df = pd.read_excel(file, header=None)
        extracted = {}

        # Scan Grid
        for r in range(len(df)):
            for c in range(len(df.columns)):
                cell = str(df.iloc[r, c]).strip().upper().replace(" ", "")
                if cell in CHEMICAL_MAP:
                    if c + 1 < len(df.columns):
                        val = df.iloc[r, c + 1]
                        extracted[cell] = clean_val(val)

        if extracted:
            st.success(f"Successfully processed {len(extracted)} minerals.")
            c1, c2 = st.columns(2)
            
            total_value = 0
            with c1:
                st.subheader("Laboratory Results")
                for k, v in extracted.items():
                    st.write(f"{CHEMICAL_MAP[k]['label']}: **{v:.4f}%**")
            
            with c2:
                st.subheader("Market Valuation (per Ton)")
                val_data = []
                for k, v in extracted.items():
                    pure_pct = v * CHEMICAL_MAP[k]['factor']
                    price_rate = CHEMICAL_MAP[k]['price']
                    worth = pure_pct * price_rate
                    total_value += worth
                    
                    # This is the line that shows both the % and the Price
                    val_data.append({"Element": CHEMICAL_MAP[k]['symbol'], "Pure %": f"{pure_pct:.4f}", "Value (TZS)": f"{worth:,.2f}"})
                
                st.table(val_data)
                st.metric("Total Ore Value", f"{total_value:,.2f} TZS/MT")
        else:
            st.warning("No matching mineral labels found in the file.")
            
      except Exception as e:
              st.error(f"Critical Error: {e}")
