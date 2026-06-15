import os
import re

file_path = "/Users/shanfu/cc/Projects/movie-database-revival/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. DB Migration
db_migration = """    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='movies'")
    if not cur.fetchone():"""
db_migration_new = """    cur.execute("PRAGMA table_info(movies)")
    columns = [info[1] for info in cur.fetchall()]
    if columns and 'title_zh' not in columns:
        cur.execute("ALTER TABLE movies ADD COLUMN title_zh TEXT")
        cur.execute("ALTER TABLE movies ADD COLUMN director_zh TEXT")
        cur.execute("ALTER TABLE movies ADD COLUMN actors_zh TEXT")
        cur.execute("ALTER TABLE movies ADD COLUMN plot_zh TEXT")
        conn.commit()
        
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='movies'")
    if not cur.fetchone():"""
if db_migration in content:
    content = content.replace(db_migration, db_migration_new)
else:
    print("Warning: db_migration failed to match")

# 2. TMDB API change
tmdb_api = """def get_tmdb_movie_details(tmdb_id, api_key):
    if not api_key:
        return None
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
    params = {"api_key": api_key, "language": st.session_state.get('lang', 'zh'), "append_to_response": "credits,external_ids"}"""
tmdb_api_new = """def get_tmdb_movie_details(tmdb_id, api_key, lang=None):
    if not api_key:
        return None
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
    req_lang = lang if lang else st.session_state.get('lang', 'zh')
    params = {"api_key": api_key, "language": req_lang, "append_to_response": "credits,external_ids"}"""
if tmdb_api in content:
    content = content.replace(tmdb_api, tmdb_api_new)
else:
    print("Warning: tmdb_api failed to match")


# 3. Batch Update Loop parsing
batch_1_old = """                            # Autocomplete fields via APIs
                            details = get_tmdb_movie_details(m_title, key)
                            if not details:
                                skip_count += 1
                                continue"""
batch_1_new = """                            # Autocomplete fields via APIs
                            details_en = get_tmdb_movie_details(m_title, key, lang='en-US')
                            details_zh = get_tmdb_movie_details(m_title, key, lang='zh-CN')
                            
                            if not details_en and not details_zh:
                                skip_count += 1
                                continue
                                
                            details = details_en if details_en else details_zh"""
if batch_1_old in content:
    content = content.replace(batch_1_old, batch_1_new)
else:
    print("Warning: batch_1 failed to match")

batch_2_old = """                            genre_names = [g.get('name') for g in details.get('genres', [])]
                            genres = ", ".join(genre_names)
                            
                            director_names = [c.get('name') for c in details.get('credits', {}).get('crew', []) if c.get('job') == 'Director']
                            director = ", ".join(director_names) if director_names else ""
                            
                            cast_names = [c.get('name') for c in details.get('credits', {}).get('cast', [])][:15]
                            actors = ", ".join(cast_names) if cast_names else ""
                            
                            plot = details.get('overview')"""
batch_2_new = """                            genre_names = [g.get('name') for g in (details_en or details).get('genres', [])]
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
                            
                            plot_zh = (details_zh or details).get('overview')"""
if batch_2_old in content:
    content = content.replace(batch_2_old, batch_2_new)
else:
    print("Warning: batch_2 failed to match")


# Batch DB update
batch_update_old = """                                'plot': use_new_if_empty('plot', plot),
                                'imdb_id': use_new_if_empty('imdb_id', imdb_id),"""
batch_update_new = """                                'plot': use_new_if_empty('plot', plot),
                                'title_zh': use_new_if_empty('title_zh', title_zh),
                                'director_zh': use_new_if_empty('director_zh', director_zh),
                                'actors_zh': use_new_if_empty('actors_zh', actors_zh),
                                'plot_zh': use_new_if_empty('plot_zh', plot_zh),
                                'imdb_id': use_new_if_empty('imdb_id', imdb_id),"""
if batch_update_old in content:
    content = content.replace(batch_update_old, batch_update_new)
else:
    print("Warning: batch_update failed to match")


# 4. Single Update Loop parsing
single_1_old = """                                    details = get_tmdb_movie_details(r.get("id"), current_tmdb_key)
                                    if details:"""
single_1_new = """                                    details_en = get_tmdb_movie_details(r.get("id"), current_tmdb_key, lang='en-US')
                                    details_zh = get_tmdb_movie_details(r.get("id"), current_tmdb_key, lang='zh-CN')
                                    details = details_en if details_en else details_zh
                                    if details:"""
if single_1_old in content:
    content = content.replace(single_1_old, single_1_new)
else:
    print("Warning: single_1 failed to match")

single_2_old = """                                        genre_names = [g.get("name") for g in details.get("genres", [])]
                                        genres = ", ".join(genre_names)
                                        director_names = [c.get("name") for c in details.get("credits", {}).get("crew", []) if c.get("job") == "Director"]
                                        director = ", ".join(director_names) if director_names else ""
                                        cast_names = [c.get("name") for c in details.get("credits", {}).get("cast", [])][:15]
                                        actors = ", ".join(cast_names) if cast_names else ""
                                        plot = details.get("overview")"""
single_2_new = """                                        genre_names = [g.get("name") for g in (details_en or details).get("genres", [])]
                                        genres = ", ".join(genre_names)
                                        director_names = [c.get("name") for c in (details_en or details).get("credits", {}).get("crew", []) if c.get("job") == "Director"]
                                        director = ", ".join(director_names) if director_names else ""
                                        cast_names = [c.get("name") for c in (details_en or details).get("credits", {}).get("cast", [])][:15]
                                        actors = ", ".join(cast_names) if cast_names else ""
                                        plot = (details_en or details).get("overview")
                                        
                                        # Chinese fields
                                        title_zh = (details_zh or details).get("title") if details_zh else ""
                                        director_names_zh = [c.get("name") for c in (details_zh or details).get("credits", {}).get("crew", []) if c.get("job") == "Director"]
                                        director_zh = ", ".join(director_names_zh) if director_names_zh else ""
                                        cast_names_zh = [c.get("name") for c in (details_zh or details).get("credits", {}).get("cast", [])][:15]
                                        actors_zh = ", ".join(cast_names_zh) if cast_names_zh else ""
                                        plot_zh = (details_zh or details).get("overview")"""
if single_2_old in content:
    content = content.replace(single_2_old, single_2_new)
else:
    print("Warning: single_2 failed to match")

single_update_old = """                                            "plot": use_new_if_empty("plot", plot),
                                            "imdb_id": use_new_if_empty("imdb_id", imdb_id),"""
single_update_new = """                                            "plot": use_new_if_empty("plot", plot),
                                            "title_zh": use_new_if_empty("title_zh", title_zh),
                                            "director_zh": use_new_if_empty("director_zh", director_zh),
                                            "actors_zh": use_new_if_empty("actors_zh", actors_zh),
                                            "plot_zh": use_new_if_empty("plot_zh", plot_zh),
                                            "imdb_id": use_new_if_empty("imdb_id", imdb_id),"""
if single_update_old in content:
    content = content.replace(single_update_old, single_update_new)
else:
    print("Warning: single_update failed to match")


# 5. UI Edit form
edit_old = """        e_plot = st.text_area(t("form_plot"), value=(movie['plot'] if movie['plot'] else ""))"""
edit_new = """        e_plot = st.text_area(t("form_plot"), value=(movie['plot'] if movie['plot'] else ""))
        
        st.markdown("**Localizations (Chinese)**")
        e_title_zh = st.text_input("译名 (中文)", value=(movie.get('title_zh', '') if dict(movie).get('title_zh') else ""))
        e_director_zh = st.text_input("导演 (中文)", value=(movie.get('director_zh', '') if dict(movie).get('director_zh') else ""))
        e_actors_zh = st.text_area("演员 (中文)", value=(movie.get('actors_zh', '') if dict(movie).get('actors_zh') else ""))
        e_plot_zh = st.text_area("剧情梗概 (中文)", value=(movie.get('plot_zh', '') if dict(movie).get('plot_zh') else ""))"""
if edit_old in content:
    content = content.replace(edit_old, edit_new)
else:
    print("Warning: edit failed to match")

edit_update_old = """                'plot': e_plot if e_plot else None,"""
edit_update_new = """                'plot': e_plot if e_plot else None,
                'title_zh': e_title_zh if e_title_zh else None,
                'director_zh': e_director_zh if e_director_zh else None,
                'actors_zh': e_actors_zh if e_actors_zh else None,
                'plot_zh': e_plot_zh if e_plot_zh else None,"""
if edit_update_old in content:
    content = content.replace(edit_update_old, edit_update_new)
else:
    print("Warning: edit_update failed to match")

# 6. UI Display Conditional
ui_title_old = """                # Custom styled title & original title
                st.markdown(f'<h2 class="movie-title-header">{movie["title"]}</h2>', unsafe_allow_html=True)
                if movie['original_title']:
                    st.markdown(f'<p class="movie-orig-title">{movie["original_title"]}</p>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<p class="movie-orig-title">{t("no_alt_title")}</p>', unsafe_allow_html=True)"""
ui_title_new = """                # Custom styled title & original title
                st.markdown(f'<h2 class="movie-title-header">{movie["title"]}</h2>', unsafe_allow_html=True)
                
                orig_title = movie['original_title'] if movie['original_title'] else ""
                title_zh = dict(movie).get('title_zh', '')
                
                # Show original title if it exists and differs from current main title and translated title
                if orig_title and orig_title != movie['title'] and orig_title != title_zh:
                    st.markdown(f'<p class="movie-orig-title">{orig_title}</p>', unsafe_allow_html=True)
                
                # Show translated title as sub-title in ZH mode
                if st.session_state.lang == 'zh' and title_zh:
                    st.markdown(f'<p class="movie-orig-title" style="color:#818CF8;">{title_zh}</p>', unsafe_allow_html=True)
                    
                if not orig_title and not title_zh:
                    st.markdown(f'<p class="movie-orig-title">{t("no_alt_title")}</p>', unsafe_allow_html=True)"""
if ui_title_old in content:
    content = content.replace(ui_title_old, ui_title_new)
else:
    print("Warning: ui_title failed to match")

ui_dir_old = """                # Director
                st.markdown(f'<p class="movie-metadata-label">{t("director_label")}</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="movie-metadata-value" style="margin-bottom:0.6rem;">{movie["director"] if movie["director"] else t("unknown_director")}</p>', unsafe_allow_html=True)"""
ui_dir_new = """                # Director
                st.markdown(f'<p class="movie-metadata-label">{t("director_label")}</p>', unsafe_allow_html=True)
                
                dir_display = movie["director"] if movie["director"] else t("unknown_director")
                if st.session_state.lang == 'zh' and dict(movie).get("director_zh"):
                    dir_display = movie["director_zh"]
                
                st.markdown(f'<p class="movie-metadata-value" style="margin-bottom:0.6rem;">{dir_display}</p>', unsafe_allow_html=True)"""
if ui_dir_old in content:
    content = content.replace(ui_dir_old, ui_dir_new)
else:
    print("Warning: ui_dir failed to match")

ui_plot_old = """            # Full details down
            st.markdown(f'<p class="movie-metadata-label">{t("plot_label")}</p>', unsafe_allow_html=True)
            st.markdown(f'<p style="color:{text_color};opacity:0.85;font-size:0.92rem;line-height:1.5;margin-bottom:1rem;">{movie["plot"] if movie["plot"] else t("plot_missing")}</p>', unsafe_allow_html=True)
        
            st.markdown(f'<p class="movie-metadata-label">{t("actors_label")}</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="movie-metadata-value" style="font-size:0.9rem;margin-bottom:1rem;">{movie["actors"] if movie["actors"] else t("unknown_actors")}</p>', unsafe_allow_html=True)"""
ui_plot_new = """            # Full details down
            st.markdown(f'<p class="movie-metadata-label">{t("plot_label")}</p>', unsafe_allow_html=True)
            plot_display = movie["plot"] if movie["plot"] else t("plot_missing")
            if st.session_state.lang == 'zh' and dict(movie).get("plot_zh"):
                plot_display = movie["plot_zh"]
            st.markdown(f'<p style="color:{text_color};opacity:0.85;font-size:0.92rem;line-height:1.5;margin-bottom:1rem;">{plot_display}</p>', unsafe_allow_html=True)
        
            st.markdown(f'<p class="movie-metadata-label">{t("actors_label")}</p>', unsafe_allow_html=True)
            actors_display = movie["actors"] if movie["actors"] else t("unknown_actors")
            if st.session_state.lang == 'zh' and dict(movie).get("actors_zh"):
                actors_display = movie["actors_zh"]
            st.markdown(f'<p class="movie-metadata-value" style="font-size:0.9rem;margin-bottom:1rem;">{actors_display}</p>', unsafe_allow_html=True)"""
if ui_plot_old in content:
    content = content.replace(ui_plot_old, ui_plot_new)
else:
    print("Warning: ui_plot failed to match")


with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Bilingual patch applied successfully.")
