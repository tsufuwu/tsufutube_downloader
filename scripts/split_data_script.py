import os
import json
from data import TRANSLATIONS

# Ensure assets/locales exists
os.makedirs("assets/locales", exist_ok=True)

for lang_code, data in TRANSLATIONS.items():
    file_path = f"assets/locales/{lang_code}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Created {file_path}")
