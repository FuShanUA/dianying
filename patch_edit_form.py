import re

file_path = "/Users/shanfu/cc/Projects/movie-database-revival/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

old_block = """        st.markdown("**Localizations (Chinese)**")
        e_title_zh = st.text_input("译名 (中文)", value=(movie.get('title_zh', '') if dict(movie).get('title_zh') else ""))
        e_director_zh = st.text_input("导演 (中文)", value=(movie.get('director_zh', '') if dict(movie).get('director_zh') else ""))
        e_actors_zh = st.text_area("演员 (中文)", value=(movie.get('actors_zh', '') if dict(movie).get('actors_zh') else ""))
        e_plot_zh = st.text_area("剧情梗概 (中文)", value=(movie.get('plot_zh', '') if dict(movie).get('plot_zh') else ""))"""

new_block = """        st.markdown("**Localizations (Chinese)**")
        e_title_zh = st.text_input("译名 (中文)", value=(dict(movie).get('title_zh', '') if dict(movie).get('title_zh') else ""))
        e_director_zh = st.text_input("导演 (中文)", value=(dict(movie).get('director_zh', '') if dict(movie).get('director_zh') else ""))
        e_actors_zh = st.text_area("演员 (中文)", value=(dict(movie).get('actors_zh', '') if dict(movie).get('actors_zh') else ""))
        e_plot_zh = st.text_area("剧情梗概 (中文)", value=(dict(movie).get('plot_zh', '') if dict(movie).get('plot_zh') else ""))"""

content = content.replace(old_block, new_block)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Edit form patched.")
