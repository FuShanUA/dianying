import re

with open('app.py', 'r') as f:
    content = f.read()

# 1. State machine initialization
state_init = """# State for batch metadata processing
for k in ['batch_running', 'batch_paused', 'batch_targets', 'batch_index', 'batch_success', 'batch_skip']:
    if k not in st.session_state:
        st.session_state[k] = False if k in ['batch_running', 'batch_paused'] else 0 if k in ['batch_index', 'batch_success', 'batch_skip'] else []
"""
# Insert after `covers_dir = os.path.join(...)`
covers_dir_pos = content.find("covers_dir = os.path.join(base_dir, 'covers')")
if covers_dir_pos != -1:
    insert_pos = content.find("\n", covers_dir_pos) + 1
    content = content[:insert_pos] + state_init + "\n" + content[insert_pos:]

# 2. Extract process_single_batch_movie logic from the old render_batch_metadata_popover loop
old_batch_func_start = content.find('def render_batch_metadata_popover')
old_batch_func_end = content.find('def render_settings_popover')
old_batch_func = content[old_batch_func_start:old_batch_func_end]

# We completely rewrite `render_batch_metadata_popover` and add `render_batch_progress` right above it.
new_batch_code = """
def render_batch_progress(covers_dir):
    if not st.session_state.get('batch_running', False):
        return
        
    targets = st.session_state.batch_targets
    idx = st.session_state.batch_index
    total = len(targets)
    
    if idx >= total:
        st.session_state.batch_running = False
        st.success(t("batch_success", success=st.session_state.batch_success, skip=st.session_state.batch_skip))
        st.rerun()
        return
        
    m_id, m_title = targets[idx]
    
    st.markdown("---")
    st.markdown(f"### ✨ 正在批量补全: **{m_title}** ({idx+1}/{total})")
    
    # Progress Bar
    st.progress(idx / total if total > 0 else 0)
    
    pc1, pc2, pc3 = st.columns([1, 1, 8])
    with pc1:
        if st.session_state.batch_paused:
            if st.button("▶️ 继续", use_container_width=True, key="batch_resume_btn"):
                st.session_state.batch_paused = False
                st.rerun()
        else:
            if st.button("⏸️ 暂停", use_container_width=True, key="batch_pause_btn"):
                st.session_state.batch_paused = True
                st.rerun()
    with pc2:
        if st.button("⏹️ 停止", use_container_width=True, key="batch_stop_btn"):
            st.session_state.batch_running = False
            st.session_state.batch_paused = False
            st.rerun()
            
    if st.session_state.batch_paused:
        return
        
    # Process exactly 1 movie
    key = load_tmdb_key()
    details_en = get_tmdb_movie_details(m_title, key, lang='en-US')
    details_zh = get_tmdb_movie_details(m_title, key, lang='zh-CN')
    
    if not details_en and not details_zh:
        st.session_state.batch_skip += 1
    else:
        details = details_en if details_en else details_zh
        tmdb_id_str = str(details.get('id', ''))
        original_title = details.get('original_title')
        runtime = details.get('runtime')
        release_date = details.get('release_date')
        year = int(release_date.split('-')[0]) if release_date else None
        
        genre_names = [g.get('name') for g in (details_en or details).get('genres', [])]
        genres = ", ".join(genre_names)
        
        director_names = [c.get('name') for c in (details_en or details).get('credits', {}).get('crew', []) if c.get('job') == 'Director']
        director = ", ".join(director_names) if director_names else ""
        
        cast_names = [c.get('name') for c in (details_en or details).get('credits', {}).get('cast', [])][:15]
        actors = ", ".join(cast_names) if cast_names else ""
        
        plot = (details_en or details).get('overview')
        
        # Chinese fields
        title_zh = (details_zh or details).get('title') if details_zh else ""
        director_names_zh = [c.get('name') for c in (details_zh or details).get('credits', {}).get('crew', []) if c.get('job') == 'Director']
        director_zh = ", ".join(director_names_zh) if director_names_zh else ""
        
        cast_names_zh = [c.get('name') for c in (details_zh or details).get('credits', {}).get('cast', [])][:15]
        actors_zh = ", ".join(cast_names_zh) if cast_names_zh else ""
        
        plot_zh = (details_zh or details).get('overview')
        countries = [c.get('name') for c in details.get('production_countries', [])]
        country = ", ".join(countries) if countries else ""
        
        external_ids = details.get('external_ids', {})
        imdb_id = external_ids.get('imdb_id')
        
        wmdb_data = fetch_wmdb_ratings(imdb_id if imdb_id else m_title)
        douban_id = None
        douban_rating = None
        imdb_rating = details.get('vote_average')
        
        if wmdb_data:
            douban_id = wmdb_data.get('doubanId')
            douban_rating = wmdb_data.get('doubanRating')
            if wmdb_data.get('imdbRating'):
                imdb_rating = wmdb_data.get('imdbRating')
        
        poster_path = details.get('poster_path')
        local_cover = os.path.join(covers_dir, f"{m_id}.jpg")
        if poster_path and not (os.path.exists(local_cover) and os.path.getsize(local_cover) > 0):
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            try:
                import requests
                img_r = requests.get(poster_url, timeout=10)
                if img_r.status_code == 200:
                    with open(local_cover, 'wb') as img_f:
                        img_f.write(img_r.content)
            except Exception:
                pass
                
        existing = get_movie_details(m_id)
        def use_new_if_empty(key, new_val):
            return existing[key] if existing[key] else new_val
            
        update_movie_fields(m_id, {
            'original_title': use_new_if_empty('original_title', original_title),
            'director': use_new_if_empty('director', director),
            'actors': use_new_if_empty('actors', actors),
            'genres': use_new_if_empty('genres', genres),
            'year': use_new_if_empty('year', year),
            'runtime': use_new_if_empty('runtime', runtime),
            'country': use_new_if_empty('country', country),
            'plot': use_new_if_empty('plot', plot),
            'title_zh': use_new_if_empty('title_zh', title_zh),
            'director_zh': use_new_if_empty('director_zh', director_zh),
            'actors_zh': use_new_if_empty('actors_zh', actors_zh),
            'plot_zh': use_new_if_empty('plot_zh', plot_zh),
            'imdb_id': use_new_if_empty('imdb_id', imdb_id),
            'tmdb_id': use_new_if_empty('tmdb_id', tmdb_id_str),
            'douban_id': use_new_if_empty('douban_id', douban_id),
            'imdb_rating': imdb_rating,
            'douban_rating': douban_rating
        })
        st.session_state.batch_success += 1

    st.session_state.batch_index += 1
    st.rerun()

def render_batch_metadata_popover(covers_dir):
    with st.popover(t("batch_meta_title"), use_container_width=True):
        st.markdown(f"<h3 style='margin-top:0;'>{t('batch_title')}</h3>", unsafe_allow_html=True)
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM movies WHERE plot IS NULL OR plot = '' OR genres IS NULL OR genres = ''")
        incomplete_count = cur.fetchone()[0]
        conn.close()
        
        st.write(t("batch_warning", count=incomplete_count))
        
        if incomplete_count > 0:
            batch_limit = st.slider(t("batch_limit_label"), min_value=10, max_value=200, value=50, step=10, key="header_batch_limit")
            key = load_tmdb_key()
            if not key:
                st.warning(t("batch_key_warning"))
            else:
                if st.button(t("batch_start_btn"), use_container_width=True, key="header_batch_start_btn"):
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute(\"""
                        SELECT id, title 
                        FROM movies 
                        WHERE plot IS NULL OR plot = '' OR genres IS NULL OR genres = '' 
                        LIMIT ?
                    \""", (batch_limit,))
                    targets = cur.fetchall()
                    conn.close()
                    
                    if not targets:
                        st.info(t("batch_empty"))
                    else:
                        st.session_state.batch_targets = targets
                        st.session_state.batch_index = 0
                        st.session_state.batch_success = 0
                        st.session_state.batch_skip = 0
                        st.session_state.batch_running = True
                        st.session_state.batch_paused = False
                        st.rerun()
"""

content = content.replace(old_batch_func, new_batch_code)

# 3. Insert `render_batch_progress(covers_dir)` above the search/filters bar
filter_bar_start = content.find('# 1. Main Search and Filters Bar')
content = content[:filter_bar_start] + "render_batch_progress(covers_dir)\n\n    " + content[filter_bar_start:]

# 4. Adjust layout column widths
# Replace `sub_c1, sub_c2, sub_c3, sub_c4, sub_gap, sub_c5, sub_c6 = st.columns([1.1, 0.6, 1.4, 1.2, 0.4, 1.3, 1.1])`
old_layout_cols = "sub_c1, sub_c2, sub_c3, sub_c4, sub_gap, sub_c5, sub_c6 = st.columns([1.1, 0.6, 1.4, 1.2, 0.4, 1.3, 1.1])"
new_layout_cols = "sub_c1, sub_c2, sub_c3, sub_c4, sub_gap, sub_c5, sub_c6 = st.columns([1.1, 0.6, 1.4, 1.1, 0.1, 1.3, 1.5])"
content = content.replace(old_layout_cols, new_layout_cols)

# Replace `col_logo, col_ctrls = st.columns([2.5, 3.5])`
old_top_cols = "col_logo, col_ctrls = st.columns([2.5, 3.5])"
new_top_cols = "col_logo, col_ctrls = st.columns([1.8, 4.2])"
content = content.replace(old_top_cols, new_top_cols)

with open('app.py', 'w') as f:
    f.write(content)
print("Patched!")
