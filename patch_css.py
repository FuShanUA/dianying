import re

file_path = "/Users/shanfu/cc/Projects/movie-database-revival/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

old_code = 'div[data-testid="stVerticalBlock"]:has(div.details-panel-marker) {'
new_code = 'div[data-testid="stVerticalBlock"]:has(> div[data-testid="element-container"] > div.details-panel-marker) {'
content = content.replace(old_code, new_code)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed CSS selector for details panel.")
