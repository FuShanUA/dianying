import re

file_path = "/Users/shanfu/cc/Projects/movie-database-revival/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Make sure loaded_count DOES NOT reset on language toggle by tracking language changes.
filter_old = """filter_key = f"{search_query}_{genre_filter}_{status_filter}_{country_filter}_{year_filter}_{sort_selected}"
import time
with open("filter_debug.log", "a") as dbg_f:
    dbg_f.write(f"[{time.time()}] filter_key: {filter_key} | lang: {st.session_state.lang}\\n")
if 'last_filter_key' not in st.session_state:
    st.session_state.last_filter_key = filter_key
elif st.session_state.last_filter_key != filter_key:
    st.session_state.last_filter_key = filter_key
    st.session_state.loaded_count = 36
    st.query_params["loaded_count"] = "36" """

filter_new = """filter_key = f"{search_query}_{genre_filter}_{status_filter}_{country_filter}_{year_filter}_{sort_selected}"
if 'last_filter_key' not in st.session_state:
    st.session_state.last_filter_key = filter_key
elif st.session_state.last_filter_key != filter_key:
    st.session_state.last_filter_key = filter_key
    st.session_state.loaded_count = 36
    st.query_params["loaded_count"] = "36" """

content = content.replace(filter_old, filter_new)

# explicit state assignment
explicit_old = """    # 1. Main Search and Filters Bar
    col_q, col_g, col_s, col_c, col_y, col_sort, col_slider = st.columns([2.0, 1.2, 1.1, 1.1, 1.1, 1.2, 1.1])
    with col_q:
        search_query = st.text_input(t("search_label"), placeholder=t("search_placeholder"), key="filter_search_input")"""

explicit_new = """    # Explicit state init
    for k in ["filter_search_input", "filter_genre_sel", "filter_status_sel", "filter_country_sel", "filter_year_sel", "filter_sort_sel"]:
        if k not in st.session_state:
            st.session_state[k] = "" if k == "filter_search_input" else "All" if k != "filter_sort_sel" else "Year"

    # 1. Main Search and Filters Bar
    col_q, col_g, col_s, col_c, col_y, col_sort, col_slider = st.columns([2.0, 1.2, 1.1, 1.1, 1.1, 1.2, 1.1])
    with col_q:
        search_query = st.text_input(t("search_label"), placeholder=t("search_placeholder"), key="filter_search_input")"""

if "Explicit state init" not in content:
    content = content.replace(explicit_old, explicit_new)


with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Explicit state patched.")
