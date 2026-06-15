import re

with open('app.py', 'r') as f:
    content = f.read()

# Replace the entire batch_metadata_dialog definition
start_idx = content.find('@st.dialog("✨", width="large")\ndef batch_metadata_dialog(covers_dir):')
end_idx = content.find('insert_pos = content.find("def render_settings_popover")') # wait, that's from the patch script, not app.py!
end_idx = content.find('def render_settings_popover')

# Actually let's use regex or string replace.
old_dialog_code = content[start_idx:end_idx]

new_dialog_code = """@st.dialog("✨", width="large")
def batch_metadata_dialog(covers_dir):
    st.markdown(f"<h3 style='margin-top:0;'>{t('batch_title')}</h3>", unsafe_allow_html=True)
    
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
                    return
                
                # Setup UI for synchronous run
                st.markdown("---")
                progress_bar = st.progress(0)
                status_text = st.empty()
                st.info("💡 提示：正在运行中，关闭此弹窗即可随时中止任务。")
                
                success_count = 0
                skip_count = 0
                total = len(targets)
                
                for idx, (m_id, m_title) in enumerate(targets):
                    status_text.markdown(f"**🔄 正在处理 / Processing:** {m_title} ({idx+1}/{total})")
                    
                    details_en = get_tmdb_movie_details(m_title, key, lang='en-US')
                    details_zh = get_tmdb_movie_details(m_title, key, lang='zh-CN')
                    
                    if not details_en and not details_zh:
                        skip_count += 1
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
                        success_count += 1
                    
                    progress_bar.progress((idx + 1) / total)
                
                status_text.markdown(f"**✅ 补全完成 / Finished!**")
                st.success(t("batch_success", success=success_count, skip=skip_count))
                if st.button("关闭 / Close", use_container_width=True):
                    st.rerun()
"""

content = content.replace(old_dialog_code, new_dialog_code + "\n")

with open('app.py', 'w') as f:
    f.write(content)
print("Synchronous dialog logic applied!")
