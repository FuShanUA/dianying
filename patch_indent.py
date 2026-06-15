import re

with open('app.py', 'r') as f:
    content = f.read()

old_block = content[content.find('@st.dialog("🎬")\ndef movie_edit_dialog(movie=None):'):content.find('    bc1, bc2 = st.columns(2)')]

new_block = """@st.dialog("🎬")
def movie_edit_dialog(movie=None):
    st.markdown("<style>button[aria-label='Close'] { display: none; }</style>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='margin-top:0;'>{t('add_entry_title') if movie is None else t('manual_edit_title')}</h3>", unsafe_allow_html=True)
    if movie is None:
        movie = {
            'id': None, 'title': '', 'original_title': '', 'year': 0, 'runtime': 0,
            'original_language': '', 'languages': '', 'genres': '', 'director': '',
            'actors': '', 'plot': '', 'title_zh': '', 'director_zh': '', 'actors_zh': '',
            'plot_zh': '', 'imdb_id': '', 'imdb_rating': 0.0, 'douban_id': '',
            'douban_rating': 0.0, 'country': '', 'tmdb_id': ''
        }

    e_title = st.text_input(t("form_title") + " *", value=movie['title'])
    e_orig_title = st.text_input(t("form_orig_title"), value=(movie['original_title'] if movie['original_title'] else ""))
    
    col_y, col_r = st.columns(2)
    with col_y:
        e_year = st.number_input(t("form_year"), value=int(movie['year']) if movie['year'] else 0, step=1)
    with col_r:
        e_runtime = st.number_input(t("form_runtime"), value=int(movie['runtime']) if movie['runtime'] else 0, step=1)
            
    e_orig_lang = st.text_input(t("form_orig_lang"), value=dict(movie).get('original_language', ''))
    e_languages = st.text_input(t("form_audio_lang"), value=dict(movie).get('languages', ''))
    
    e_genres = st.text_input(t("form_genres"), value=(movie['genres'] if movie['genres'] else ""))
    e_director = st.text_input(t("form_director"), value=(movie['director'] if movie['director'] else ""))
    e_actors = st.text_area(t("form_actors"), value=(movie['actors'] if movie['actors'] else ""))
    e_plot = st.text_area(t("form_plot"), value=(movie['plot'] if movie['plot'] else ""))
    
    st.markdown("**Localizations (Chinese)**")
    e_title_zh = st.text_input("译名 (中文)", value=(dict(movie).get('title_zh', '') if dict(movie).get('title_zh') else ""))
    e_director_zh = st.text_input("导演 (中文)", value=(dict(movie).get('director_zh', '') if dict(movie).get('director_zh') else ""))
    e_actors_zh = st.text_area("演员 (中文)", value=(dict(movie).get('actors_zh', '') if dict(movie).get('actors_zh') else ""))
    e_plot_zh = st.text_area("剧情梗概 (中文)", value=(dict(movie).get('plot_zh', '') if dict(movie).get('plot_zh') else ""))
    
    col_id1, col_id2 = st.columns(2)
    with col_id1:
        e_imdb_id = st.text_input(t("form_imdb_id"), value=(movie['imdb_id'] if movie['imdb_id'] else ""))
        e_imdb_rating = st.number_input(t("form_imdb_rating"), value=float(movie['imdb_rating']) if movie['imdb_rating'] else 0.0, step=0.1)
    with col_id2:
        e_douban_id = st.text_input(t("form_douban_id"), value=(movie['douban_id'] if movie['douban_id'] else ""))
        e_douban_rating = st.number_input(t("form_douban_rating"), value=float(movie['douban_rating']) if movie['douban_rating'] else 0.0, step=0.1)
    
    e_country = st.text_input(t("form_country"), value=(movie['country'] if movie['country'] else ""))
    e_tmdb_id = st.text_input(t("form_tmdb_id"), value=(movie['tmdb_id'] if movie['tmdb_id'] else ""))
    
"""

content = content.replace(old_block, new_block)

with open('app.py', 'w') as f:
    f.write(content)
print("Indentation fixed")
