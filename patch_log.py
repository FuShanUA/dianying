import re

file_path = "/Users/shanfu/cc/Projects/movie-database-revival/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

log_old = """filter_key = f"{search_query}_{genre_filter}_{status_filter}_{country_filter}_{year_filter}_{sort_selected}"
if 'last_filter_key' not in st.session_state:"""
log_new = """filter_key = f"{search_query}_{genre_filter}_{status_filter}_{country_filter}_{year_filter}_{sort_selected}"
import time
with open("filter_debug.log", "a") as dbg_f:
    dbg_f.write(f"[{time.time()}] filter_key: {filter_key} | lang: {st.session_state.lang}\\n")
if 'last_filter_key' not in st.session_state:"""
content = content.replace(log_old, log_new)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Log injected.")
