# ⚖️ SanctionGuard AI: The Autonomous Compliance Tribunal

**SanctionGuard** is an AI-powered compliance platform that replaces traditional "keyword matching" with a multi-agent reasoning system. Instead of simply flagging a name, it convenes a digital tribunal to debate the risk, drastically reducing false positives.

[SanctionsGuard](https://github.com/user-attachments/assets/d9943a7c-46d8-4a16-9926-39f8f49fdcb7)


## 🚀 Key Features

* **Multi-Agent Tribunal:**
    * **👨‍⚖️ The Prosecutor (Llama 3.3):** Analyzes name matches and country risks to argue for strict enforcement.
    * **🛡️ The Defense (GPT-OSS 20B):** Identifies data gaps, typos, and lack of biometric evidence to argue for false positives.
    * **⚖️ The Judge (Gemini 2.5):** Synthesizes both arguments into a final, explainable verdict (High/Low Risk).
* **Tiered Architecture:** Uses **RapidFuzz** (Tier 1) for speed and **LLMs** (Tier 2) for reasoning, optimizing cost and latency.
* **Batch Screening:** Upload a CSV to screen hundreds of entities automatically.
* **Audit-Ready Reports:** Generates downloadable PDF case files with full tribunal transcripts.

## 🛠️ Tech Stack

* **Frontend:** Streamlit
* **AI Inference:** Groq (Llama 3.3, GPT-OSS, Mixtral) & Google Gemini
* **Data Processing:** Pandas, RapidFuzz
* **Reporting:** FPDF
* **Data Source:** Consolidated OFAC & UN Sanctions List (JSON)

## ⚙️ Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/yourusername/sanctionguard-ai.git](https://github.com/yourusername/sanctionguard-ai.git)
    cd sanctionguard-ai
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up API Keys:**
    Create a `.streamlit/secrets.toml` file (DO NOT commit this to GitHub):
    ```toml
    GROQ_API_KEY = "gsk_..."
    GOOGLE_API_KEY = "AIza..."
    ```

4.  **Run the application:**
    ```bash
    streamlit run app.py
    ```

## 📂 Project Structure

* `app.py`: Main Streamlit dashboard and UI logic.
* `tribunal.py`: The core AI logic class handling the "Trial" and model interactions.
* `evidence_manager.py`: Utility to download and parse the latest sanctions lists (OFAC/UN).
* `consolidated_sanctions.json`: The local vector/search database.

## 🛡️ License

This project is for educational and research purposes.
