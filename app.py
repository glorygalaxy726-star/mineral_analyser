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
                 (username TEXT PRIMARY KEY, phone TEXT, password TEXT, credits INTEGER)''')
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
# 3. UI INITIALIZATION
# ==========================================
st.set_page_config(page_title="Thamani mineral Analytics", layout="wide")
init_db()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = ""

# ==========================================
# 4. PAGE 1: SECURITY GATE (LOGIN/REGISTER)
# ==========================================
if not st.session_state.logged_in:
    st.title("🔐 Thamani Security Gate")
    auth_choice = st.radio("Select Action", ["Login", "Register"], horizontal=True)

    if auth_choice == "Register":
        st.subheader("📝 Create New Account")
        reg_user = st.text_input("Username", key="reg_u")
        reg_pw = st.text_input("Password", type="password", key="reg_p")
        reg_phone = st.text_input("Phone Number", key="reg_ph")

        if st.button("CREATE ACCOUNT"):
            if reg_user == "" or reg_pw == "":
                st.warning("Username and Password are required.")
            else:
                conn = sqlite3.connect('thamani_data.db')
                c = conn.cursor()
                try:
                    c.execute("INSERT INTO miners (username, password, phone, credits) VALUES (?, ?, ?, ?)", 
                              (reg_user, reg_pw, reg_phone, 0))
                    conn.commit()
                    st.success(f"✅ Account for {reg_user} created permanently! Now switch to Login.")
                except sqlite3.IntegrityError:
                    st.error("This username is already taken in the database.")
                conn.close()

    else:
        st.subheader("🔑 User Login")
        login_user = st.text_input("Username", key="log_u")
        login_pw = st.text_input("Password", type="password", key="log_p")

        if st.button("LOG IN"):
            conn = sqlite3.connect('thamani_data.db')
            c = conn.cursor()
            c.execute("SELECT * FROM miners WHERE username=? AND password=?", (login_user, login_pw))
            result = c.fetchone()
            conn.close()

            if result:
                st.session_state.logged_in = True
                st.session_state.current_user = login_user
                st.success("Access Granted!")
                st.rerun()
            else:
                st.error("Invalid Username or Password.")

    st.divider()
    st.caption("Developed by Glory Benson | Chemist & Digital Researcher | 0616648724")

# ==========================================
# 5. PAGE 2: AUTHORIZED APP CONTENT
# ==========================================
else:
    # SIDEBAR SETUP
    st.sidebar.title(f"💎 Welcome, {st.session_state.current_user}")
    nav_selection = st.sidebar.radio("Go to:", ["Welcome Home", "Thamani Mineral Analytics"])
    # In your sidebar
    lang = st.sidebar.radio("Language / Lugha", ["English", "Kiswahili"])
    st.sidebar.divider() # Adds a nice line before the logout
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # --- SUB-PAGE: WELCOME HOME ---
    if nav_selection == "Welcome Home":
        st.title("🔬 Thamani Mineral Analytics")
       # --- Section 1: The Vision Statement ---
        st.write("""
       ### 💎 Thamani Vision: Bridging Science & Value
       This is where **precision meets passion**. Building this system was driven by a single goal: 
       to turn complex laboratory data into actionable intelligence. As a **Chemist and Digital Researcher**, 
       I believe that the true value of our minerals lies not just in the earth, but in the **clarity** of the data we extract from them.
       """)

        st.divider() # Adds a clean line between the vision and the welcome

# --- Section 2: The User Welcome ---
        st.markdown(f"""
        ### Welcome to the **Thamani Digital Lab**, {st.session_state.current_user}.
        * ⚡ **Auto-Extract:** Read Excel and PDF reports.
        * 🧪 **Stoichiometric Conversion:** Convert Oxides to pure Element %.
        * 💰 **Real-time Valuation:** Estimates TZS value per Metric Ton.
        """)
        st.info("👈 Select **Thamani Mineral Analytics** in the sidebar to begin.")

    # --- SUB-PAGE: ANALYTICS MAIN LOGIC ---
    elif nav_selection == "Thamani Mineral Analytics":
        st.title("📊 Mineral Analytics Engine")
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
                        if match: extracted[key] = float(match.group(1))
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
                    # --- POST-PROCESSING: MOISTURE & LOI ALERTS ---
                    # We assume 'extracted' is your dictionary of results
                    moisture_val = extracted.get("H2O", 0) or extracted.get("MOISTURE", 0)
                    loi_val = extracted.get("LOI", 0)

                    # 🚩 Set your limits here
                    MOISTURE_LIMIT = 5.0  # e.g., 5%
                    LOI_LIMIT = 10.0      # e.g., 10%

                    st.markdown("### 📋 Status Report / Ripoti ya Hali")

                    # --- MOISTURE CHECK ---
                    if moisture_val > MOISTURE_LIMIT:
                        if lang == "Kiswahili":
                           st.error(f"⚠️ **ONYO LA UNYEVUNYEVU:** Kiasi cha {moisture_val}% kimezidi kiwango! Hii itapunguza sana bei yako ya mauzo.")
                        else:
                            st.error(f"⚠️ **MOISTURE ALERT:** {moisture_val}% exceeds the limit! This will significantly reduce your net sale price.")
                    else:
                        if lang == "Kiswahili":
                           st.success(f"✅ **UNYEVUNYEVU:** {moisture_val}% iko ndani ya kiwango salama.")
                        else:
                            st.success(f"✅ **MOISTURE:** {moisture_val}% is within acceptable limits.")

                    # --- LOI CHECK ---
                    if loi_val > LOI_LIMIT:
                        if lang == "Kiswahili":
                           st.warning(f"⚠️ **ONYO LA LOI:** Uzito unaopotea kwa moto ({loi_val}%) ni mkubwa. Unaweza kutozwa faini na kiwanda cha uchenjuaji.")
                        else:
                            st.warning(f"⚠️ **LOI ALERT:** Ignition loss of {loi_val}% is high. You may face processing penalties from the smelter.")
                    else:
                        if lang == "Kiswahili":
                           st.success(f"✅ **LOI:** {loi_val}% ni kiasi kidogo, uzalishaji utakuwa mzuri.")
                        else: 
                            st.success(f"✅ **LOI:** {loi_val}% is low, indicating good processing yield.")

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
                st.error(f"Error: {e}")

    # CAPTION FOR THE AUTHORIZED AREA
    st.divider()
    st.caption("Developed by Glory Benson | Chemist & Digital Researcher | 0616648724")
    
