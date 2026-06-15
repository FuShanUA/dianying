import re

file_path = "/Users/shanfu/cc/Projects/movie-database-revival/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

s_old_pattern = r'    with col_s:\n        status_filter_options = \[t\("status_all"\), t\("status_seen"\), t\("status_unseen"\)\]\n        status_selected = st\.selectbox\(t\("filter_status"\), status_filter_options\)\n        status_filter = "All"\n        if status_selected == t\("status_seen"\):\n            status_filter = "Seen"\n        elif status_selected == t\("status_unseen"\):\n            status_filter = "Unseen"'

s_new = """    with col_s:
        status_filter_options = ["All", "Seen", "Unseen"]
        def format_status(s):
            if s == "All": return t("status_all")
            if s == "Seen": return t("status_seen")
            if s == "Unseen": return t("status_unseen")
            return s
        status_selected = st.selectbox(t("filter_status"), status_filter_options, format_func=format_status, key="filter_status_sel")
        status_filter = status_selected"""

if re.search(s_old_pattern, content):
    content = re.sub(s_old_pattern, s_new, content)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Status filter patched.")
else:
    print("Could not find status filter pattern.")
