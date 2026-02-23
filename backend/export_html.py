import markdown
import os

md_path = "/Users/aakashsangani/.gemini/antigravity/brain/531bac6a-6569-4187-b515-0f1bf64effc1/walkthrough.md"
html_path = "/Users/aakashsangani/.gemini/antigravity/brain/531bac6a-6569-4187-b515-0f1bf64effc1/walkthrough_export.html"

with open(md_path, 'r', encoding='utf-8') as f:
    text = f.read()
    
# Convert with formatting
html = markdown.markdown(text, extensions=['tables', 'fenced_code'])

# Wrap in basic HTML structure
html_doc = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body>
{html}
</body>
</html>
"""

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_doc)
    
print(f"HTML exported to {html_path}")
