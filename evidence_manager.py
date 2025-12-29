import requests
import xml.etree.ElementTree as ET
import json
import os
from datetime import datetime
from tqdm import tqdm  # pip install tqdm

# --- CONFIGURATION ---
SOURCES = {
    "OFAC_SDN": "https://www.treasury.gov/ofac/downloads/sdn.xml"
}

# --- COUNTRY RISK DATABASE ---
HIGH_RISK_COUNTRIES = {
    "IR": {"name": "Iran", "risk_level": "CRITICAL", "reason": "FATF Blacklist / Broad US Sanctions"},
    "KP": {"name": "North Korea", "risk_level": "CRITICAL", "reason": "FATF Blacklist / Proliferation"},
    "RU": {"name": "Russia", "risk_level": "HIGH", "reason": "EU/US Sectoral Sanctions"},
    "VE": {"name": "Venezuela", "risk_level": "HIGH", "reason": "Political / Human Rights Sanctions"},
    "MM": {"name": "Myanmar", "risk_level": "HIGH", "reason": "FATF Blacklist"},
    "SY": {"name": "Syria", "risk_level": "CRITICAL", "reason": "State Sponsor of Terrorism"},
    "CU": {"name": "Cuba", "risk_level": "HIGH", "reason": "US Embargo"},
    "BY": {"name": "Belarus", "risk_level": "HIGH", "reason": "Aggression against Ukraine"},
}

OUTPUT_FILE = "consolidated_sanctions.json"

def download_file(url, filename):
    print(f"⬇️  Downloading from {url}...")
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    if response.status_code == 200:
        with open(filename, 'wb') as f, tqdm(
            desc=filename,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in response.iter_content(chunk_size=1024):
                size = f.write(chunk)
                bar.update(size)
        print("✅ Download Complete.")
        return True
    else:
        print(f"❌ Failed to download. Status Code: {response.status_code}")
        return False

def strip_namespace(tree):
    """
    Iterates through the XML tree and forcibly removes the {http://...} namespace 
    from every tag. This makes parsing 100x easier and error-proof.
    """
    for elem in tree.iter():
        if '}' in elem.tag:
            elem.tag = elem.tag.split('}', 1)[1]  # Keep only the tag name after '}'
    return tree

def parse_ofac_sdn(xml_file):
    print("⚙️  Parsing OFAC Data (This may take a moment)...")
    
    # Parse and Strip Namespaces immediately
    tree = ET.parse(xml_file)
    tree = strip_namespace(tree)
    root = tree.getroot()
    
    sanctioned_entities = []
    
    # Now we can just search for "sdnEntry" directly without worrying about URLs
    entries = root.findall(".//sdnEntry")
    
    for entry in tqdm(entries, desc="Processing Entities"):
        entity = {
            "source": "US_OFAC",
            "id": entry.find("uid").text if entry.find("uid") is not None else "N/A",
            "name": "Unknown",
            "type": "Unknown",
            "programs": [],
            "addresses": [],
            "remarks": entry.find("remarks").text if entry.find("remarks") is not None else ""
        }

        # Get Name (Last, First)
        last_name = entry.find("lastName").text if entry.find("lastName") is not None else ""
        first_name = entry.find("firstName").text if entry.find("firstName") is not None else ""
        
        # Handle cases where only one name exists (e.g., Vessels or Organizations)
        if last_name and first_name:
            entity["name"] = f"{last_name}, {first_name}".strip(", ")
        elif last_name:
            entity["name"] = last_name
        elif first_name:
            entity["name"] = first_name
            
        # Get Type
        entity["type"] = entry.find("sdnType").text if entry.find("sdnType") is not None else "Entity"

        # Get Sanction Programs
        program_list = entry.find("programList")
        if program_list is not None:
            entity["programs"] = [p.text for p in program_list.findall("program")]

        # Get Addresses & Check Country Risk
        address_list = entry.find("addressList")
        if address_list is not None:
            for addr in address_list.findall("address"):
                country = addr.find("country").text if addr.find("country") is not None else "Unknown"
                city = addr.find("city").text if addr.find("city") is not None else ""
                
                full_addr = f"{city}, {country}".strip(", ")
                entity["addresses"].append(full_addr)
                
                # Check Risk
                for code, data in HIGH_RISK_COUNTRIES.items():
                    if data["name"].lower() in country.lower():
                        entity["remarks"] += f" [RISK WARNING: Location match {data['name']}]"

        sanctioned_entities.append(entity)
        
    print(f"✅ Extracted {len(sanctioned_entities)} entities from OFAC.")
    return sanctioned_entities

def main():
    if download_file(SOURCES["OFAC_SDN"], "ofac_sdn.xml"):
        ofac_data = parse_ofac_sdn("ofac_sdn.xml")
        
        final_db = {
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "risk_definitions": HIGH_RISK_COUNTRIES,
            "entities": ofac_data
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(final_db, f, indent=4)
            
        print(f"\n🎉 Success! Database built at '{OUTPUT_FILE}'")
        print(f"Total Sanctioned Entities Tracked: {len(ofac_data)}")
        
        # Cleanup
        os.remove("ofac_sdn.xml")

if __name__ == "__main__":
    main()