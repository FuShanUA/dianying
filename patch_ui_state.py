import re

file_path = "/Users/shanfu/cc/Projects/movie-database-revival/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. search query
q_old = """    with col_q:
        search_query = st.text_input(t("search_label"), placeholder=t("search_placeholder"))"""
q_new = """    with col_q:
        search_query = st.text_input(t("search_label"), placeholder=t("search_placeholder"), key="filter_search_input")"""
content = content.replace(q_old, q_new)

# 2. Genre filter
g_old = """    with col_g:
        genres_list = [t("status_all")] + load_genres()
        def format_genre(g):
            if st.session_state.lang == 'zh':
                return GENRE_MAP_ZH.get(g, g)
            return g
        # Sort dropdown list by Chinese Pinyin in Chinese mode
        if st.session_state.lang == 'zh':
            sorted_genres = [t("status_all")] + sorted(load_genres(), key=lambda x: format_genre(x))
        else:
            sorted_genres = genres_list
        genre_filter = st.selectbox(t("filter_genre"), sorted_genres, format_func=format_genre)"""
g_new = """    with col_g:
        genres_list = ["All"] + load_genres()
        def format_genre(g):
            if g == "All": return t("status_all")
            if st.session_state.lang == 'zh':
                return GENRE_MAP_ZH.get(g, g)
            return g
        # Sort dropdown list by Chinese Pinyin in Chinese mode
        if st.session_state.lang == 'zh':
            sorted_genres = ["All"] + sorted(load_genres(), key=lambda x: format_genre(x))
        else:
            sorted_genres = genres_list
        genre_filter = st.selectbox(t("filter_genre"), sorted_genres, format_func=format_genre, key="filter_genre_sel")"""
content = content.replace(g_old, g_new)

# 3. Status filter
s_old = """    with col_s:
        status_filter_options = [t("status_all"), t("status_seen"), t("status_unseen")]
        status_selected = st.selectbox(t("filter_status"), status_filter_options)
        status_filter = "All"
        if status_selected == t("status_seen"):
            status_filter = "Seen"
        elif status_selected == t("status_unseen"):
            status_filter = "Unseen" """
s_new = """    with col_s:
        status_filter_options = ["All", "Seen", "Unseen"]
        def format_status(s):
            if s == "All": return t("status_all")
            if s == "Seen": return t("status_seen")
            if s == "Unseen": return t("status_unseen")
            return s
        status_selected = st.selectbox(t("filter_status"), status_filter_options, format_func=format_status, key="filter_status_sel")
        status_filter = status_selected"""
content = content.replace(s_old, s_new)

# 4. Country filter
c_old = """    with col_c:
        country_list = [t("status_all")] + load_countries()
        def format_country(c):
            if st.session_state.lang == 'zh':
                return COUNTRY_MAP_ZH.get(c, c)
            return c
        # Sort dropdown list by Chinese Pinyin in Chinese mode
        if st.session_state.lang == 'zh':
            sorted_countries = [t("status_all")] + sorted(load_countries(), key=lambda x: format_country(x))
        else:
            sorted_countries = country_list
        country_filter = st.selectbox(t("filter_country"), sorted_countries, format_func=format_country)"""
c_new = """    with col_c:
        country_list = ["All"] + load_countries()
        def format_country(c):
            if c == "All": return t("status_all")
            if st.session_state.lang == 'zh':
                return COUNTRY_MAP_ZH.get(c, c)
            return c
        # Sort dropdown list by Chinese Pinyin in Chinese mode
        if st.session_state.lang == 'zh':
            sorted_countries = ["All"] + sorted(load_countries(), key=lambda x: format_country(x))
        else:
            sorted_countries = country_list
        country_filter = st.selectbox(t("filter_country"), sorted_countries, format_func=format_country, key="filter_country_sel")"""
content = content.replace(c_old, c_new)

# 5. Year filter
y_old = """    with col_y:
        year_list = [t("status_all")] + load_years()
        year_filter = st.selectbox(t("filter_year"), year_list)"""
y_new = """    with col_y:
        year_list = ["All"] + load_years()
        def format_year(y):
            return t("status_all") if y == "All" else y
        year_filter = st.selectbox(t("filter_year"), year_list, format_func=format_year, key="filter_year_sel")"""
content = content.replace(y_old, y_new)

# 6. Sort filter
sort_old = """    with col_sort:
        sort_options = [t("sort_year"), t("sort_imdb"), t("sort_douban"), t("sort_alpha")]
        sort_selected = st.selectbox(t("sort_label"), sort_options)"""
sort_new = """    with col_sort:
        sort_options = ["Year", "IMDb", "Douban", "Alpha"]
        def format_sort(s):
            if s == "Year": return t("sort_year")
            if s == "IMDb": return t("sort_imdb")
            if s == "Douban": return t("sort_douban")
            if s == "Alpha": return t("sort_alpha")
            return s
        sort_selected = st.selectbox(t("sort_label"), sort_options, format_func=format_sort, key="filter_sort_sel")"""
content = content.replace(sort_old, sort_new)

# 7. Sort processing
s_proc_old = """    if sort_selected == t("sort_imdb"):
        return (tier, -imdb, -year, -m_id)
    elif sort_selected == t("sort_douban"):
        return (tier, -douban, -year, -m_id)
    elif sort_selected == t("sort_alpha"):
        return (tier, title, -year, -m_id)
    else: # Default Year sort
        return (tier, -year, -m_id)"""
s_proc_new = """    if sort_selected == "IMDb":
        return (tier, -imdb, -year, -m_id)
    elif sort_selected == "Douban":
        return (tier, -douban, -year, -m_id)
    elif sort_selected == "Alpha":
        return (tier, title, -year, -m_id)
    else: # Default Year sort
        return (tier, -year, -m_id)"""
content = content.replace(s_proc_old, s_proc_new)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("UI State patch applied successfully.")
