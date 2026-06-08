import os, zipfile, xml.etree.ElementTree as ET, re

template_dir = os.path.join(os.path.dirname(__file__), "template")
NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
VAR_RE = re.compile(r"\{\{.*?\}\}|\{%.*?%\}")

for fname in sorted(os.listdir(template_dir)):
    if not fname.endswith(".docx"):
        continue
    path = os.path.join(template_dir, fname)
    print(f"\n=== {fname} ===")
    try:
        with zipfile.ZipFile(path) as zf:
            xml_bytes = zf.read("word/document.xml")
            root = ET.fromstring(xml_bytes)
            runs = [t.text for t in root.iter(f"{NS}t") if t.text]
            full = "".join(runs)
            matches = VAR_RE.findall(full)
            if matches:
                for m in matches:
                    print(f"  {m}")
            else:
                print("  [No Jinja2/docxtpl variables found]")
            print(f"\n  --- Full text preview (first 800 chars) ---")
            print(f"  {full[:800]}")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\n\nDONE")
