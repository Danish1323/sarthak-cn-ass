#!/usr/bin/env python3
"""
Compiles HTML and PDF Report from template with Base64 embedded screenshots.
"""

import os
import sys
import base64
from pathlib import Path
import subprocess

WORKSPACE_DIR = Path("/Users/danishshaikh1423/Downloads/sarthak-cn")
SCREENSHOTS_DIR = WORKSPACE_DIR / "screenshots"

def image_to_base64(path):
    if not os.path.exists(path):
        print(f"Warning: image path does not exist: {path}")
        return ""
    with open(path, "rb") as f:
        data = f.read()
    return f"data:image/png;base64,{base64.b64encode(data).decode('utf-8')}"

def main():
    template_path = WORKSPACE_DIR / "report_template.html"
    html_out_path = WORKSPACE_DIR / "Sudsline_Network_Investigation_Report.html"
    pdf_out_path = WORKSPACE_DIR / "Sudsline_Network_Investigation_Report.pdf"

    print("[*] Reading template...")
    template_text = template_path.read_text(encoding="utf-8")

    print("[*] Converting images to Base64...")
    top_b64 = image_to_base64(SCREENSHOTS_DIR / "topology_overview.png")
    plant_b64 = image_to_base64(SCREENSHOTS_DIR / "fig1_plant_site.png")
    hq_b64 = image_to_base64(SCREENSHOTS_DIR / "fig2_hq_edge.png")
    wan_b64 = image_to_base64(SCREENSHOTS_DIR / "fig4_wan_backbone.png")

    print("[*] Replacing placeholders...")
    final_html = template_text.replace("__TOPOLOGY_IMG__", top_b64)
    final_html = final_html.replace("__PLANT_IMG__", plant_b64)
    final_html = final_html.replace("__HQ_IMG__", hq_b64)
    final_html = final_html.replace("__WAN_IMG__", wan_b64)

    html_out_path.write_text(final_html, encoding="utf-8")
    print(f"[+] Written standalone HTML: {html_out_path} ({len(final_html):,} bytes)")

    print("[*] Invoking Google Chrome headless PDF compiler...")
    cmd = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_out_path}",
        str(html_out_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if pdf_out_path.exists():
        size_kb = pdf_out_path.stat().st_size / 1024
        print(f"[***] SUCCESS: PDF GENERATED: {pdf_out_path} ({size_kb:.1f} KB) [***]")
    else:
        print("[-] PDF Generation failed:", res.stderr)

if __name__ == "__main__":
    main()
