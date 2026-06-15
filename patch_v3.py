import re

with open('app.py', 'r') as f:
    content = f.read()

# 1. Header Layout Gap Fix
# We need to find the `col_logo, col_ctrls = st.columns([1.8, 4.2])` and change it to `[1.0, 5.0]`
# And `sub_c1, sub_c2...` we can change `sub_gap` to 0.1 or remove it.
old_top_cols = "col_logo, col_ctrls = st.columns([1.8, 4.2])"
new_top_cols = "col_logo, col_ctrls = st.columns([1.0, 5.0])"
content = content.replace(old_top_cols, new_top_cols)

# 2. State Machine initialization for Batch Dialog
# Ensure we have `show_batch_dialog` initialized
state_init_block = "for k in ['batch_running', 'batch_paused', 'batch_targets', 'batch_index', 'batch_success', 'batch_skip']:"
if 'show_batch_dialog' not in content:
    new_state_init = "for k in ['batch_running', 'batch_paused', 'batch_targets', 'batch_index', 'batch_success', 'batch_skip', 'show_batch_dialog', 'show_add_movie_dialog']:"
    content = content.replace(state_init_block, new_state_init)

# 3. Rewrite batch_metadata_dialog to use state-machine and `show_batch_dialog`
start_idx = content.find('@st.dialog("✨", width="large")\ndef batch_metadata_dialog(covers_dir):')
if start_idx == -1:
    start_idx = content.find('@st.dialog("✨")\ndef batch_metadata_dialog(covers_dir):')

end_idx = content.find('insert_pos = content.find("def render_settings_popover")') 
if end_idx == -1:
    end_idx = content.find('def render_settings_popover')

old_dialog_code = content[start_idx:end_idx]

new_dialog_code = """@st.dialog("✨ Batch Meta")
def batch_metadata_dialog(covers_dir):
    st.markdown("<style>button[aria-label='Close'] { display: none; }</style>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='margin-top:0;'>{t('batch_title')}</h3>", unsafe_allow_html=True)
    
    if st.session_state.get('batch_running', False) or st.session_state.get('batch_paused', False):
        targets = st.session_state.batch_targets
        idx = st.session_state.batch_index
        total = len(targets)
        
        if idx >= total:
            st.session_state.batch_running = False
            st.success(t("batch_success", success=st.session_state.batch_success, skip=st.session_state.batch_skip))
            if st.button("关闭 / Close", use_container_width=True, key="batch_finish_close"):
                st.session_state.show_batch_dialog = False
                st.rerun()
            return
            
        m_id, m_title = targets[idx]
        st.markdown(f"**🔄 正在处理 / Processing:** {m_title} ({idx+1}/{total})")
        st.progress(idx / total if total > 0 else 0)
        
        # UI controls
        pc1, pc2 = st.columns(2)
        with pc1:
            if st.session_state.batch_paused:
                if st.button("▶️ 继续 / Resume", use_container_width=True, key="batch_resume_btn"):
                    st.session_state.batch_paused = False
                    st.rerun()
            else:
                if st.button("⏸️ 暂停 / Pause", use_container_width=True, key="batch_pause_btn"):
                    st.session_state.batch_paused = True
                    st.rerun()
        with pc2:
            if st.button("⏹️ 停止并退出 / Stop & Close", use_container_width=True, key="batch_stop_btn"):
                st.session_state.batch_running = False
                st.session_state.batch_paused = False
                st.session_state.show_batch_dialog = False
                st.rerun()
                
        if st.session_state.batch_paused:
            return
            
        # Process 1 movie
        key = load_tmdb_key()
        details_en = get_tmdb_movie_details(m_title, key, lang='en-US')
        details_zh = get_tmdb_movie_details(m_title, key, lang='zh-CN')
        
        if not details_en and not details_zh:
            st.session_state.batch_skip += 1
            st.warning(f"未能获取到 {m_title} 的数据，已跳过")
            import time
            time.sleep(1) # Give user a moment to see the skip warning
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
            
            import os
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
            def use_new_if_empty(k, new_val):
                return existing[k] if existing[k] else new_val
                
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

    else:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM movies WHERE plot IS NULL OR plot = '' OR genres IS NULL OR genres = ''")
        incomplete_count = cur.fetchone()[0]
        conn.close()
        
        st.write(t("batch_warning", count=incomplete_count))
        
        if incomplete_count > 0:
            batch_limit = st.slider(t("batch_limit_label"), min_value=10, max_value=200, value=50, step=10, key="dialog_batch_limit")
            key = load_tmdb_key()
            if not key:
                st.warning(t("batch_key_warning"))
            else:
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(t("batch_start_btn"), use_container_width=True, key="dialog_batch_start_btn"):
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
                with c2:
                    if st.button("关闭 / Close", use_container_width=True, key="batch_close_setup"):
                        st.session_state.show_batch_dialog = False
                        st.rerun()
"""

content = content.replace(old_dialog_code, new_dialog_code + "\n")

# Modify button triggers to use show_batch_dialog state
old_c5_block = """            with sub_c5:
                if st.button("➕ " + t("add_entry_title"), use_container_width=True):
                    add_movie_dialog()
            with sub_c6:
                if st.button(t("batch_meta_title"), use_container_width=True):
                    batch_metadata_dialog(covers_dir)"""

new_c5_block = """            with sub_c5:
                if st.button("➕ " + t("add_entry_title"), use_container_width=True):
                    add_movie_dialog()
            with sub_c6:
                if st.button(t("batch_meta_title"), use_container_width=True):
                    st.session_state.show_batch_dialog = True"""

content = content.replace(old_c5_block, new_c5_block)

# Insert the dialog renderers at the end of the main script or after the top bar
filter_bar_start = content.find('# 1. Main Search and Filters Bar')

dialog_triggers = """
if st.session_state.get('show_batch_dialog', False):
    batch_metadata_dialog(covers_dir)
"""

content = content[:filter_bar_start] + dialog_triggers + "\n" + content[filter_bar_start:]

with open('app.py', 'w') as f:
    f.write(content)

print("Patch v3 applied!")
