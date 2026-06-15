import re

with open('app.py', 'r') as f:
    content = f.read()

# 1. Remove render_batch_progress call from the main layout
content = content.replace("render_batch_progress(covers_dir)\n\n    ", "")

# 2. Extract and delete the old render_batch_progress and render_batch_metadata_popover functions
start1 = content.find("def render_batch_progress(covers_dir):")
end1 = content.find("def render_batch_metadata_popover(covers_dir):")
start2 = end1
end2 = content.find("def render_settings_popover", start2)

content = content[:start1] + content[end2:]

# 3. Create the new dialogs code
new_dialogs = """
@st.dialog("🎬")
def add_movie_dialog():
    st.markdown(f"<h3 style='margin-top:0;'>{t('add_entry_title')}</h3>", unsafe_allow_html=True)
    new_title = st.text_input("Add movie:", label_visibility="collapsed", placeholder=t("add_entry_placeholder"), key="dialog_new_title")
    if st.button(t("create_entry_btn"), use_container_width=True, key="dialog_create_btn") and new_title.strip():
        new_id = insert_new_movie(new_title.strip())
        st.success(t("create_entry_success", id=new_id))
        st.session_state.selected_movie_id = new_id
        st.query_params["movie_id"] = str(new_id)
        st.query_params["lang"] = st.session_state.lang
        st.rerun()

@st.dialog("✨", width="large")
def batch_metadata_dialog(covers_dir):
    st.markdown(f"<h3 style='margin-top:0;'>{t('batch_title')}</h3>", unsafe_allow_html=True)
    
    if st.session_state.get('batch_running', False) or st.session_state.get('batch_paused', False):
        targets = st.session_state.batch_targets
        idx = st.session_state.batch_index
        total = len(targets)
        
        if idx >= total:
            st.session_state.batch_running = False
            st.success(t("batch_success", success=st.session_state.batch_success, skip=st.session_state.batch_skip))
            if st.button("完成 / Finish", use_container_width=True):
                st.rerun()
            return
            
        m_id, m_title = targets[idx]
        st.markdown(f"**🔄 正在处理 / Processing:** {m_title} ({idx+1}/{total})")
        st.progress(idx / total if total > 0 else 0)
        
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
            if st.button("⏹️ 停止 / Stop", use_container_width=True, key="batch_stop_btn"):
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

"""

insert_pos = content.find("def render_settings_popover")
content = content[:insert_pos] + new_dialogs + "\n" + content[insert_pos:]

# 4. Modify the sub_c5 and sub_c6 blocks to trigger dialogs via normal buttons
old_c5_block = """            with sub_c5:
                with st.popover("➕ " + t("add_entry_title"), use_container_width=True):
                    st.markdown(f"<h3 style='color:{text_color};margin-top:0;'>{t('add_entry_title')}</h3>", unsafe_allow_html=True)
                    new_title = st.text_input("Add movie:", label_visibility="collapsed", placeholder=t("add_entry_placeholder"), key="header_new_title")
                    if st.button(t("create_entry_btn"), use_container_width=True, key="header_create_btn") and new_title.strip():
                        new_id = insert_new_movie(new_title.strip())
                        st.success(t("create_entry_success", id=new_id))
                        st.session_state.selected_movie_id = new_id
                        st.query_params["movie_id"] = str(new_id)
                        st.query_params["lang"] = st.session_state.lang
                        st.rerun()
            with sub_c6:
                render_batch_metadata_popover(covers_dir)"""

new_c5_block = """            with sub_c5:
                if st.button("➕ " + t("add_entry_title"), use_container_width=True):
                    add_movie_dialog()
            with sub_c6:
                if st.button(t("batch_meta_title"), use_container_width=True):
                    batch_metadata_dialog(covers_dir)"""

content = content.replace(old_c5_block, new_c5_block)

with open('app.py', 'w') as f:
    f.write(content)
print("Patched dialogs!")
