import re

file_path = "/Users/shanfu/cc/Projects/movie-database-revival/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix the messy CSS section around line 505
messy_pattern = r'div\[data-testid="stVerticalBlock"\]:has\(> div\[data-testid="element-container"\] div\.details-panel-marker\) \{.*?(?=\s+/\*\s+Header styling\s+\*/)'
fixed_css = """div[data-testid="stVerticalBlock"]:has(> div[data-testid="element-container"] div.details-panel-marker) {{
        /* Height handled here for details panel if needed, but we also apply it below */
    }}"""

content = re.sub(messy_pattern, fixed_css, content, flags=re.DOTALL)

# Also fix line 634 (which is where the premium panel styling is)
# It should look like:
# div[data-testid="stVerticalBlock"]:has(> div[data-testid="element-container"] div.details-panel-marker) {{
#     height: calc(100vh - 175px) !important;
#     overflow-y: auto !important;
#     background: ...
# }}

premium_pattern = r'div\[data-testid="stVerticalBlock"\]:has\(> div\[data-testid="element-container"\] div\.details-panel-marker\) \{.*?(?=\.movie-poster-container)'

fixed_premium = """div[data-testid="stVerticalBlock"]:has(> div[data-testid="element-container"] div.details-panel-marker) {{
        height: calc(100vh - 175px) !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        background: {panel_bg};
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid {panel_border};
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        transition: background 0.3s ease, border-color 0.3s ease;
    }}
    
    """

content = re.sub(premium_pattern, fixed_premium, content, flags=re.DOTALL)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("CSS syntax fixed.")
