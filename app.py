import streamlit as st
import pandas as pd
import re
import pdfplumber 
from fpdf import FPDF
import io
import sqlite3
import hashlib
from datetime import datetime

# ==========================================
# 1. CONFIGURATION & DATABASE
# ==========================================
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

def init_db():
    conn = sqlite3.connect('thamani_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS miners 
                 (username TEXT, phone TEXT, password TEXT, credits INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  miner_name TEXT, mineral TEXT, purity REAL, 
                  lat TEXT, lon TEXT, timestamp TEXT, digital_hash TEXT)''')
    conn.commit()
    conn.close()

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def clean_val(val):
    if pd.isna(val) or str(val).strip() == "": return 0.0
    s = str(val).lower()
    if any(x in s for x in ['trace', '<', 'n.d', 'nil', 'nd']): return 0.0
    match = re.search(r"[-+]?\d*\.\d+|\d+", s)
    return float(match.group()) if match else 0.0

def create_pdf(val_data, total_value):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "MINERAL ANALYSIS REPORT", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(60, 10, "Mineral", 1)
    pdf.cell(60, 10, "Oxide %", 1)
    pdf.cell(60, 10, "Value (TZS/MT)", 1)
    pdf.ln()
    pdf.set_font("Arial", '', 12)
    for item in val_data:
        name = str(item['Mineral']).replace('$', '').replace('_', '')
        pdf.cell(60, 10, name, 1)
        pdf.cell(60, 10, str(item['Oxide %']), 1)
        pdf.cell(60, 10, f"{item['Value (TZS/MT)']:,.2f}", 1)
        pdf.ln()
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"TOTAL MARKET VALUE: {total_value:,.2f} TZS/MT", ln=True)
    return bytes(pdf.output(dest='S'))

# ==========================================
# 3. STREAMLIT UI & NAVIGATION
# ==========================================
st.set_page_config(page_title="Thamani mineral Analytics", layout="wide")
init_db()  # This creates the thamani_data.db file

# Initialize Session States correctly
if "user_db" not in st.session_state:
    # We keep this for the 'admin' bypass, but real users go to SQLite
    st.session_state.user_db = {"admin": "1234"} 

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "current_user" not in st.session_state:
    st.session_state.current_user = "" # <--- Fixed the empty assignment

# --- STEP 1: AUTHENTICATION CHECK ---
if not st.session_state.logged_in:
    st.title("🔐 Thamani Security Gate")
    auth_choice = st.radio("Select Action", ["Login", "Register"], horizontal=True)
    # --- REGISTRATION SECTION ---
if auth_choice == "Register":
    st.subheader("📝 Create New Account")
    reg_user = st.text_input("Username", key="reg_u")
    reg_pw = st.text_input("Password", type="password", key="reg_p")
    reg_phone = st.text_input("Phone Number", key="reg_ph")

    if st.button("CREATE ACCOUNT"):
        if reg_user == "" or reg_pw == "":
            st.warning("All fields are required.")
        else:
            conn = sqlite3.connect('thamani_data.db')
            c = conn.cursor()
            
            # Check if username already exists in SQLite
            c.execute("SELECT * FROM miners WHERE username = ?", (reg_user,))
            existing_user = c.fetchone()
            
            if existing_user:
                st.error("This username is already taken in the database.")
            else:
                # Insert into SQLite permanently
                c.execute("INSERT INTO miners (username, password, phone, credits) VALUES (?, ?, ?, ?)", 
                          (reg_user, reg_pw, reg_phone, 0))
                conn.commit()
                st.success(f"✅ {reg_user} registered permanently! Switch to Login.")
                st.rerun()
            conn.close()
            
    else:
        st.subheader("🔑 User Login")
        login_user = st.text_input("Username", key="login_user")
        login_pw = st.text_input("Password", type="password", key="login_pw")
        
        if st.button("LOG IN"):
            if login_user in st.session_state.user_db and st.session_state.user_db[login_user] == login_pw:
                st.session_state.logged_in = True
                st.session_state.current_user = login_user
                st.success(f"Access Granted! Welcome {login_user}")
                st.rerun() 
            else:
                st.error("Invalid Username or Password.")

    st.divider()
    st.caption("Developed by Glory Benson | Chemist & Digital Researcher | 0616648724")

# --- STEP 2: AUTHORIZED ACCESS (The "Hidden" part) ---
else: 
    # EVERYTHING BELOW THIS LINE MUST BE INDENTED!
    st.sidebar.title(f"💎 Welcome, {st.session_state.current_user}")
    nav_selection = st.sidebar.radio("Go to:", ["Welcome Home", "Thamani Mineral Analytics"])
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    if nav_selection == "Welcome Home":
        st.title("🔬 Welcome Home")
        # Home content here...

    elif nav_selection == "Thamani Mineral Analytics":
        st.title("📊 Mineral Analytics")
        st.markdown("""
        ### Welcome to the **Thamani Digital Lab**.
        * ⚡ **Auto-Extract:** Read Excel and PDF reports.
        * 🧪 **Stoichiometric Conversion:** Convert Oxides to pure Element %.
        * 💰 **Real-time Valuation:** Estimates TZS value per Metric Ton.
        """)
        st.info("👈 Select **Thamani Mineral Analytics** in the sidebar to begin.")
        st.divider()
        st.caption("Developed by Glory Benson | Chemist & Digital Researcher | 0616648724")

    elif nav_selection == "Thamani Mineral Analytics":
        st.title("📊 Thamani Mineral Analytics")
        file = st.file_uploader("Upload Lab Report (Excel or PDF)", type=['xlsx', 'pdf'])
        
        if file:
            extracted = {}
            try:
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
                    for r in range(len(df)):
                        for c in range(len(df.columns)):
                            cell_txt = str(df.iloc[r, c]).strip().upper().replace(" ", "")
                            if cell_txt in CHEMICAL_MAP and c + 1 < len(df.columns):
                                extracted[cell_txt] = clean_val(df.iloc[r, c + 1])

                if extracted:
                    val_data = []
                    total_value = 0
                    for k, v in extracted.items():
                        m = CHEMICAL_MAP[k]
                        e_pct = v * m['factor']
                        price_val = e_pct * m['price'] 
                        val_data.append({
                            "Mineral": m['label'],
                            "Oxide %": round(v, 2),
                            "Element %": round(e_pct, 4),
                            "Value (TZS/MT)": round(price_val, 2) 
                        })
                        total_value += price_val

                    st.write("### Analysis Results")
                    st.table(pd.DataFrame(val_data))
                    st.metric("Total Market Value", f"{total_value:,.2f} TZS/MT")
                
                    report_pdf_bytes = create_pdf(val_data, total_value)
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=report_pdf_bytes,
                        file_name="Thamani_Report.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.warning("No minerals recognized. Check file format.")

            except Exception as e:
                st.error(f"Error during processing: {e}")
        
        st.divider()
        st.caption("Developed by Glory Benson | Chemist & Digital Researcher | 0616648724")
