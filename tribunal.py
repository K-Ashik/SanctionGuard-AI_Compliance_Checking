import json
import os
import streamlit as st
from rapidfuzz import process, fuzz
from colorama import Fore, init
import google.generativeai as genai
from groq import Groq

# Initialize Colorama
init(autoreset=True)

class SanctionTribunal:
    def __init__(self, db_file="consolidated_sanctions.json"):
        # 🔒 KEYS: Look in Streamlit Secrets first, then Environment Variables
        try:
            self.groq_api_key = st.secrets["GROQ_API_KEY"]
            self.google_api_key = st.secrets["GOOGLE_API_KEY"]
        except:
            # Fallback for local testing
            self.groq_api_key = os.getenv("GROQ_API_KEY")
            self.google_api_key = os.getenv("GOOGLE_API_KEY")

        if not self.groq_api_key or not self.google_api_key:
            print(f"{Fore.RED}❌ Warning: API Keys missing. Set them in .streamlit/secrets.toml")

        # Initialize Clients
        self.groq_client = Groq(api_key=self.groq_api_key)
        genai.configure(api_key=self.google_api_key)
        
        # --- MODELS CONFIGURATION ---
        self.MODEL_PROSECUTOR = "llama-3.3-70b-versatile"
        
        # 🛡️ DEFENSE (Auto-Fallback)
        self.PREFERRED_DEFENSE = "openai/gpt-oss-20b"
        self.FALLBACK_DEFENSE = "mixtral-8x7b-32768"
        self.MODEL_DEFENSE = self.verify_defense_model()
        
        # ⚖️ JUDGE (Strictly enforced as requested)
        # ✅ FIX: We now initialize the actual GenerativeModel object
        self.judge_model_id = "gemini-2.5-flash" 
        try:
            self.judge_model = genai.GenerativeModel(self.judge_model_id)
        except Exception:
            # Fallback if 2.5 is not found (just in case)
            print(f"{Fore.YELLOW}⚠️ Gemini 2.5 not found, falling back to 1.5-flash")
            self.judge_model = genai.GenerativeModel("gemini-1.5-flash")

        print(f"{Fore.CYAN}📂 Loading Evidence Room ({db_file})...")
        try:
            with open(db_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            self.entity_names = [e['name'] for e in self.data['entities']]
            print(f"{Fore.GREEN}✅ Tribunal Ready. {len(self.entity_names)} entities loaded.")
        except FileNotFoundError:
            print(f"{Fore.RED}❌ Database missing. Please run evidence_manager.py")
            self.data = {'entities': []}
            self.entity_names = []

    def verify_defense_model(self):
        """Checks if the preferred model is reachable; falls back if not."""
        if not self.groq_api_key:
            return self.FALLBACK_DEFENSE
            
        try:
            # A quick, 1-token dry run to see if the model exists
            self.groq_client.chat.completions.create(
                model=self.PREFERRED_DEFENSE,
                messages=[{"role": "user", "content": "Ping"}],
                max_tokens=1
            )
            print(f"{Fore.GREEN}✅ Defense Model Verified: {self.PREFERRED_DEFENSE}")
            return self.PREFERRED_DEFENSE
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Preferred model ({self.PREFERRED_DEFENSE}) unavailable. Switching to fallback ({self.FALLBACK_DEFENSE}).")
            return self.FALLBACK_DEFENSE

    def get_entity_details(self, name):
        for e in self.data['entities']:
            if e['name'] == name:
                return e
        return None

    def scan_database(self, query_name):
        if not self.entity_names:
            return None, 0
            
        # Use token_set_ratio for smart partial matching
        match = process.extractOne(query_name, self.entity_names, scorer=fuzz.token_set_ratio)
        if match:
            # match is (name, score, index)
            return self.get_entity_details(match[0]), match[1]
        return None, 0