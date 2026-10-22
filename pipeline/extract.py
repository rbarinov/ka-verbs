import sys, pypdf, os
src, out = sys.argv[1], sys.argv[2]
r = pypdf.PdfReader(src)
with open(out, "w") as f:
    for i, p in enumerate(r.pages):
        try: t = p.extract_text() or ""
        except Exception as e: t = f"[ERR {e}]"
        f.write(f"\n=== PAGE {i+1} ===\n{t}")
print(os.path.basename(out), len(r.pages))
