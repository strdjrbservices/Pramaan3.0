import sys, os
sys.path.insert(0, os.getcwd())
import json
from api.pdf_extractor_offline import extract_fields_from_pdf_offline

def test_full_offline():
    p_path = r"media/uploads/4BB40F7D6EEF-KHTRBDS.PDF"
    result = extract_fields_from_pdf_offline(p_path)
    fields = result.get("fields", {})
    
    print("STATUS:", result.get("status"))
    print("\n=== INFO_OF_SALES (Sales Comparison Approach Top Box) ===")
    info_sales = fields.get("INFO_OF_SALES", {})
    for k, v in info_sales.items():
        print(f"  {k}:\n    -> {v}")

    print("\n=== FLATTENED CHECK ===")
    print("Offered:", fields.get("There are ____ comparable properties currently offered for sale in the subject neighborhood ranging in price from$ ___to $___"))
    print("Sales:", fields.get("There are ___comparable sales in the subject neighborhoodwithin the past twelvemonths ranging in sale price from$___ to $____"))

if __name__ == "__main__":
    test_full_offline()














