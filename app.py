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
        clean_name = item['Mineral'].replace('$', '').replace('_', '')
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
page = st.sidebar.radio("Go to:", ["login","register","Welcome Home", "Mineral Scanner"])
# --- 3. PAGE: ANIMATED INTRO ---
if st.session_state.page == "intro":
    st.markdown('<div class="welcome-text"><h1>THAMANI MINERAL ANALYTICS</h1><p><i>Kutambua Madini kwa Usahihi wa Kidijitali</i></p></div>', unsafe_allow_html=True)
    st.write("")
    st.write("✨ This application calculates free element amount in oxide and estimate their market value in Tanzania.")
    if st.button("PROCEED TO SECURE GATE"):
        st.session_state.page = "gate"
        st.rerun()

# --- 4. PAGE: SECURE GATE ---
elif st.session_state.page == "gate":
    st.title("🔒 Security Access")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("LOGIN"): 
            st.session_state.page = "auth_page"
            st.session_state.auth_mode = "Login"
            st.rerun()
    with col2:
        if st.button("CREATE ACCOUNT"): 
            st.session_state.page = "auth_page"
            st.session_state.auth_mode = "Register"
            st.rerun()

# --- 5. PAGE: AUTHENTICATION (Login/Signup) ---
elif st.session_state.page == "auth_page":
    # Define auth_choice immediately to prevent NameError
    auth_choice = st.radio("Select Option", ["Login", "Register"], index=0 if st.session_state.auth_mode == "Login" else 1, horizontal=True)

    if auth_choice == "Login":
        login_user = st.text_input("Username / Phone")
        login_pass = st.text_input("Password", type="password")
        if st.button("LOG IN"):
            st.success(f"Welcome back, {login_user}!")
            st.session_state.page = "dashboard"
            st.rerun()
       
    else:
        st.subheader("New Registration")
        new_user = st.text_input("Full Name", placeholder="e.g. Juma Hamisi")
        provider = st.selectbox("Network", ["M-Pesa (Vodacom)", "Tigo Pesa", "Airtel Money", "HaloPesa"])
        new_phone = st.text_input("Phone Number", placeholder="07XXXXXXXX")
        new_pass = st.text_input("Create Password", type="password")
            
    if st.button("Go Back"):
        st.session_state.page = "gate"
        st.rerun()
            
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
            # ==========================================
# 1. BACK-END: DATABASE & SECURITY ENGINES
# ==========================================

def init_db():
    """Initializes the SQLite database with Tables for Users and Analysis History"""
    conn = sqlite3.connect('thamani_data.db')
    c = conn.cursor()
    # Table for Registered Miners
    c.execute('''CREATE TABLE IF NOT EXISTS miners 
                 (username TEXT, phone TEXT, password TEXT, credits INTEGER)''')
    # Table for Traceable Analysis Results
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  miner_name TEXT, mineral TEXT, purity REAL, 
                  lat TEXT, lon TEXT, timestamp TEXT, digital_hash TEXT)''')
    conn.commit()
    conn.close()

def save_analysis(miner, mineral, purity, lat, lon):
    """Saves a traceable record and generates a digital fingerprint (Hash)"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Create a unique hash to prevent data tampering
    raw_data = f"{miner}{mineral}{purity}{lat}{lon}{timestamp}"
    digital_hash = hashlib.sha256(raw_data.encode()).hexdigest()[:16]
    
    conn = sqlite3.connect('thamani_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO history (miner_name, mineral, purity, lat, lon, timestamp, digital_hash) VALUES (?,?,?,?,?,?,?)",
              (miner, mineral, purity, lat, lon, timestamp, digital_hash))
    conn.commit()
    conn.close()
    return digital_hash

