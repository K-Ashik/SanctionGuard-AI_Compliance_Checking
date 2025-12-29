import streamlit as st
import json
import time
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from tribunal import SanctionTribunal

# --- PAGE CONFIG ---
st.set_page_config(page_title="SanctionGuard AI", page_icon="⚖️", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .reportview-container { background: #f0f2f6; }
    .prosecutor-box { background-color: #ffe6e6; padding: 15px; border-radius: 8px; border-left: 5px solid #ff4b4b; font-size: 0.95em; font-family: 'Courier New', monospace; }
    .defense-box { background-color: #e6f3ff; padding: 15px; border-radius: 8px; border-left: 5px solid #0083b8; font-size: 0.95em; font-family: 'Courier New', monospace; }
    .verdict-box { background-color: #262730; color: white; padding: 20px; border-radius: 10px; margin-top: 10px; border: 1px solid #ffd700; }
    .intro-box { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #ddd; margin-bottom: 25px; }
    .stProgress > div > div > div > div { background-color: #ffd700; }
</style>
""", unsafe_allow_html=True)

# --- COMPREHENSIVE COUNTRY LIST ---
COUNTRIES = [
    "Unknown", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Argentina", "Armenia", "Australia", "Austria", 
    "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", 
    "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cambodia", 
    "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Brazzaville)", 
    "Congo (Kinshasa)", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic", "Denmark", "Djibouti", "Dominican Republic", 
    "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Ethiopia", "Fiji", "Finland", "France", 
    "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Guatemala", "Guinea", "Guyana", "Haiti", "Honduras", 
    "Hong Kong", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Ivory Coast", 
    "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Liberia", 
    "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", 
    "Mexico", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar (Burma)", "Namibia", "Nepal", 
    "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", 
    "Pakistan", "Palestine", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", 
    "Romania", "Russia", "Rwanda", "Saudi Arabia", "Senegal", "Serbia", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", 
    "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Sweden", "Switzerland", "Syria", 
    "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Trinidad and Tobago", "Tunisia", "Turkey", 
    "Turkmenistan", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay", "Uzbekistan", 
    "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"
]

# --- HELPERS ---
def clean_text(text):
    """Sanitizes text for FPDF to prevent crashes with emojis/smart quotes."""
    if not isinstance(text, str): return str(text)
    replacements = {
        '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"', 
        '\u2013': '-', '\u00a0': ' ', '\t': ' '
    }
    for old, new in replacements.items(): text = text.replace(old, new)
    return text.encode('latin-1', 'replace').decode('latin-1')

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'SanctionGuard AI // Tribunal Record', 0, 1, 'C')
        self.ln(5)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pdf_report(case_data):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"CASE: {clean_text(case_data['target_name']).upper()}", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 10, f"ID: {hash(case_data['target_name']) % 10000} | Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True)
    
    # Dynamic Line
    current_y = pdf.get_y()
    pdf.line(10, current_y, 200, current_y)
    pdf.ln(5)
    
    # Verdict Highlight
    pdf.set_font("Arial", "B", 14)
    if "HIGH" in case_data['verdict']: pdf.set_text_color(255, 0, 0)
    else: pdf.set_text_color(0, 150, 0)
    pdf.cell(0, 10, clean_text(f"VERDICT: {case_data['verdict']} ({case_data['confidence']}%)"), ln=True)
    pdf.set_text_color(0, 0, 0)
    
    # Details
    pdf.set_font("Arial", "", 10)
    details = f"Match: {case_data['match_name']} ({case_data['match_score']}%)\nReasoning: {case_data['reasoning']}"
    pdf.multi_cell(0, 6, clean_text(details))
    pdf.ln(5)
    
    # Arguments
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(200, 50, 50)
    pdf.cell(0, 6, "PROSECUTION:", ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(0,0,0)
    pdf.multi_cell(0, 5, clean_text(case_data['pros_arg']))
    pdf.ln(3)
    
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(50, 50, 200)
    pdf.cell(0, 6, "DEFENSE:", ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(0,0,0)
    pdf.multi_cell(0, 5, clean_text(case_data['def_arg']))
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- SESSION STATE INITIALIZATION ---
if 'case_result' not in st.session_state:
    st.session_state.case_result = None

# --- LOAD TRIBUNAL ---
@st.cache_resource
def load_tribunal():
    try:
        return SanctionTribunal()
    except Exception as e:
        return None

tribunal = load_tribunal()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/9255/9255435.png", width=80)
    st.title("SanctionGuard")
    st.write("### ⚙️ Settings")
    threshold = st.slider("Fuzzy Sensitivity", 50, 100, 60, help="Lower values catch typos. Higher values require exact matches.")
    
    if tribunal:
        st.success("✅ System Online: Connected to OFAC & UN DB")
    else:
        st.error("❌ API Keys Missing! See 'secrets.toml'")
        
    st.markdown("---")
    st.info("Powered by:\n\n* **Judge:** Gemini 2.5 Flash\n* **Prosecution:** Llama 3.3\n* **Defense:** GPT-OSS 20B")

# --- MAIN APP ---
st.title("⚖️ SanctionGuard AI")

# Intro Box
st.markdown("""
<div class="intro-box">
    <strong>What is this tool?</strong><br>
    SanctionGuard replaces traditional "keyword matching" with an <strong>AI-powered Tribunal</strong>. 
    Instead of just flagging a name, this system convenes three AI agents to debate the risk:
    <ul>
        <li><strong>The Prosecutor</strong> (Llama 3.3) analyzes the evidence to find risk.</li>
        <li><strong>The Defense</strong> (GPT-OSS 20B) argues for context and false positives.</li>
        <li><strong>The Judge</strong> (Gemini 2.5 Flash) issues a final, explainable verdict.</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Tabs
tab1, tab2 = st.tabs(["🔍 Single Search", "📂 Batch Screening"])

# === TAB 1: SINGLE SEARCH ===
with tab1:
    st.markdown("Provide entity details below to convene the tribunal.")
    col1, col2 = st.columns(2)
    name_input = col1.text_input("Entity Name", placeholder="e.g. Pegah Aluminum")
    country_input = col2.selectbox("Country (Optional Context)", COUNTRIES)
    
    # 1. ACTION BUTTON
    if st.button("🚀 Convene Tribunal", key="btn_single"):
        if not tribunal: st.error("Database not loaded."); st.stop()
        
        with st.status("🔍 Scanning...", expanded=True) as status:
            match, score = tribunal.scan_database(name_input)
            
            if match and score >= threshold:
                status.update(label="⚠️ Match Found! Convening Tribunal...", state="error")
                
                # --- AI AGENTS (THEATRICAL PROMPTS) ---
                
                # Prosecutor Prompt: Aggressive, Courtroom Style
                pros_prompt = (
                    f"Role: Aggressive Sanctions Prosecutor. "
                    f"Address the court directly ('Your Honor...'). "
                    f"Evidence: Input '{name_input}' matches sanctioned entity '{match['name']}' ({int(score)}%). Country: {country_input}. "
                    f"Task: Argue forcefully that this is a risk. Keep it under 60 words. Be punchy."
                )
                pros_arg = tribunal.groq_client.chat.completions.create(
                    messages=[{"role":"user","content":pros_prompt}], 
                    model=tribunal.MODEL_PROSECUTOR
                ).choices[0].message.content
                
                # Defense Prompt: Protective, Technical
                def_prompt = (
                    f"Role: Defense Attorney. "
                    f"Address the court directly ('Your Honor, I object...'). "
                    f"Evidence: Input '{name_input}' vs Match '{match['name']}'. "
                    f"Prosecution's Claim: '{pros_arg}'. "
                    f"Task: Highlight that name matches are not identity matches. Point out missing birth dates/biometrics. "
                    f"Keep it under 60 words. Be respectful but firm."
                )
                def_arg = tribunal.groq_client.chat.completions.create(
                    messages=[{"role":"user","content":def_prompt}], 
                    model=tribunal.MODEL_DEFENSE
                ).choices[0].message.content
                
                # Judge Prompt: Decisive, Percentage
                judge_prompt = (
                    f"Act as a Judge and respond like a legal Judge. "
                    f"Prosecution Argument: {pros_arg} "
                    f"Defense Argument: {def_arg} "
                    f"Weigh the risk based on the name match ({int(score)}%) and country. "
                    f"Output strictly valid JSON: {{ \"verdict\": \"HIGH RISK\" or \"LOW RISK\", \"confidence\": <int 0-100>, \"reasoning\": \"<short judicial summary>\" }}"
                )
                judge_resp = tribunal.judge_model.generate_content(judge_prompt).text
                
                try:
                    verdict = json.loads(judge_resp.replace("```json","").replace("```",""))
                    
                    # SAVE TO SESSION STATE
                    st.session_state.case_result = {
                        "match": match, "score": score,
                        "pros_arg": pros_arg, "def_arg": def_arg,
                        "verdict": verdict,
                        "name_input": name_input, "country_input": country_input
                    }
                    
                except: st.error("Judicial Error: Could not reach a verdict.")
            else:
                st.session_state.case_result = None
                status.update(label="✅ No Match Found", state="complete")
                st.success(f"No sanctioned entities match '{name_input}' closely.")

    # 2. DISPLAY LOGIC (PERSISTENT)
    if st.session_state.case_result:
        res = st.session_state.case_result
        st.error(f"**MATCH DETECTED:** '{res['match']['name']}' ({int(res['score'])}%)")

        c1, c2 = st.columns(2)
        c1.markdown(f"<div class='prosecutor-box'><b>👨‍⚖️ Prosecution:</b><br>{res['pros_arg']}</div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='defense-box'><b>🛡️ Defense:</b><br>{res['def_arg']}</div>", unsafe_allow_html=True)
        
        verdict = res['verdict']
        color = "red" if "HIGH" in verdict['verdict'] else "green"
        st.markdown(f"<div class='verdict-box'><h3 style='color:{color}'>{verdict['verdict']} ({verdict['confidence']}%)</h3>{verdict['reasoning']}</div>", unsafe_allow_html=True)
        
        # PDF Download (Dynamic Filename)
        pdf_data = {
            "target_name": res['name_input'], "target_country": res['country_input'],
            "match_name": res['match']['name'], "match_score": int(res['score']),
            "pros_arg": res['pros_arg'], "def_arg": res['def_arg'],
            "verdict": verdict['verdict'], "confidence": verdict['confidence'], "reasoning": verdict['reasoning']
        }
        
        safe_filename = f"SanctionGuard_Case_{res['name_input'].replace(' ', '_')}.pdf"
        
        st.download_button(
            label="📄 Download PDF Report", 
            data=create_pdf_report(pdf_data), 
            file_name=safe_filename, 
            mime="application/pdf"
        )

# === TAB 2: BATCH SCREENING ===
with tab2:
    st.markdown("### 📂 Bulk Upload")
    st.info("Upload a CSV file containing a column named **'name'** (and optional 'country'). The AI will screen all entities automatically.")
    
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    
    if uploaded_file and st.button("Start Batch Screening"):
        if not tribunal: st.error("Database not loaded."); st.stop()
        
        df = pd.read_csv(uploaded_file)
        df.columns = [c.lower() for c in df.columns]
        
        if 'name' not in df.columns:
            st.error("CSV must have a 'name' column!")
        else:
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for index, row in df.iterrows():
                progress = (index + 1) / len(df)
                progress_bar.progress(progress)
                status_text.text(f"Scanning {index+1}/{len(df)}: {row['name']}...")
                
                # 1. Tier 1 Scan
                match, score = tribunal.scan_database(row['name'])
                
                result_row = {
                    "Entity Name": row['name'],
                    "Status": "CLEAR",
                    "Match Score": 0,
                    "Verdict": "N/A",
                    "Reasoning": "No close match found."
                }
                
                # 2. Tier 2 Tribunal (Only if match found)
                if match and score >= threshold:
                    result_row['Match Score'] = int(score)
                    
                    # Call Judge Directly
                    judge_prompt = f"""
                    Role: Sanction Judge. 
                    Input: {row['name']}. Match: {match['name']} ({int(score)}%). 
                    Task: Is this High Risk? Output strictly JSON: {{ "verdict": "HIGH" or "LOW", "reasoning": "short reason" }}
                    """
                    try:
                        resp = tribunal.judge_model.generate_content(judge_prompt).text
                        v_json = json.loads(resp.replace("```json","").replace("```",""))
                        
                        result_row['Status'] = "⚠️ FLAGGED"
                        result_row['Verdict'] = v_json.get('verdict', 'UNKNOWN')
                        result_row['Reasoning'] = v_json.get('reasoning', '')
                    except:
                        result_row['Status'] = "ERROR"
                
                results.append(result_row)
            
            # Completion
            progress_bar.progress(1.0)
            status_text.success("Batch Screening Complete!")
            
            # Show Results
            res_df = pd.DataFrame(results)
            st.dataframe(res_df.style.applymap(lambda v: 'color: red; font-weight: bold;' if v == '⚠️ FLAGGED' else '', subset=['Status']))
            
            # Download CSV
            csv = res_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Results (CSV)", csv, "screening_results.csv", "text/csv")