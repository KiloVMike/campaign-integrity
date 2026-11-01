import os
import subprocess
import sys

def verify_pdf_page_count(pdf_path):
    with open(pdf_path, 'rb') as f:
        data = f.read()
    # Count /Type /Page objects, excluding /Type /Pages
    page_count = data.count(b'/Type /Page') - data.count(b'/Type /Pages')
    return page_count

print("PDF verification script ready.")
