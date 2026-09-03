import os, glob, pymupdf

for root, dirs, files in os.walk("."):
    for f in files:
        if f.lower().endswith(".pdf"):
            path = os.path.join(root, f)
            try:
                doc = pymupdf.open(path)
                for i, page in enumerate(doc):
                    t = page.get_text("text")
                    if "Claridge" in t or "Sandalwood" in t or "Westmora" in t:
                        print(f"FOUND IN: {path} (Page {i+1})")
                        break
            except Exception as e:
                pass

for root, dirs, files in os.walk(r"C:\Users\Admin\.gemini\antigravity-ide\brain"):
    for f in files:
        if f.lower().endswith(".pdf"):
            path = os.path.join(root, f)
            try:
                doc = pymupdf.open(path)
                for i, page in enumerate(doc):
                    t = page.get_text("text")
                    if "Claridge" in t or "Sandalwood" in t or "Westmora" in t:
                        print(f"FOUND IN ARTIFACT: {path} (Page {i+1})")
                        break
            except Exception as e:
                pass
