import argparse, csv, json, sys
from pathlib import Path
from typing import List, Dict
from PIL import Image
import pytesseract

def load_rules(rules_dir: Path) -> Dict[str, List[Dict[str, str]]]:
    rules = {}
    for p in rules_dir.glob("*.json"):
        with open(p, "r", encoding="utf-8") as f:
            rules[p.stem] = json.load(f)
    return rules

def ocr_image(path: Path) -> str:
    try:
        img = Image.open(path)
        return pytesseract.image_to_string(img)
    except Exception as e:
        return f"[OCR_ERROR] {e}"

def scan_file(path: Path, rules: Dict[str, List[Dict[str, str]]]) -> List[Dict[str, str]]:
    text = ocr_image(path)
    results = []
    for strategy, items in rules.items():
        for r in items:
            indicator = r.get("indicator", "")
            notes = r.get("notes", "")
            if indicator.lower() in text.lower():
                results.append({
                    "file": path.name,
                    "strategy": strategy,
                    "indicator": indicator,
                    "notes": notes
                })
    return results

def main():
    ap = argparse.ArgumentParser(description="Essential Eight OCR misconfiguration scanner")
    ap.add_argument("--input", required=True, help="Folder with screenshots (PNG/JPG)")
    ap.add_argument("--rules", default="rules", help="Rules folder")
    ap.add_argument("--out", default="scan_report.csv", help="CSV output file")
    args = ap.parse_args()

    in_dir = Path(args.input)
    rules_dir = Path(args.rules)
    out_path = Path(args.out)

    if not in_dir.exists():
        print(f"Input folder not found: {in_dir}", file=sys.stderr)
        sys.exit(1)
    if not rules_dir.exists():
        print(f"Rules folder not found: {rules_dir}", file=sys.stderr)
        sys.exit(1)

    rules = load_rules(rules_dir)
    exts = {".png", ".jpg", ".jpeg", ".bmp"}
    files = [p for p in in_dir.iterdir() if p.suffix.lower() in exts]

    all_results: List[Dict[str, str]] = []
    for f in files:
        all_results.extend(scan_file(f, rules))

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["file","strategy","indicator","notes"])
        w.writeheader()
        for row in all_results:
            w.writerow(row)

    print(f"Scan complete. Results saved to {out_path} ({len(all_results)} finding(s)).")

if __name__ == "__main__":
    main()
