import re

file_path = "/Users/shanfu/cc/Projects/movie-database-revival/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

old_block = """                # Custom styled title & original title
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

new_block = """                # Custom styled title & original title
                orig_title = movie['original_title'] if movie['original_title'] else ""
                title_zh = dict(movie).get('title_zh', '')
                
                if st.session_state.lang == 'zh':
                    # Swap positions in Chinese mode
                    main_display = title_zh if title_zh else "尚未更新中文片名"
                    st.markdown(f'<h2 class="movie-title-header">{main_display}</h2>', unsafe_allow_html=True)
                    st.markdown(f'<p class="movie-orig-title" style="color:#818CF8;">{movie["title"]}</p>', unsafe_allow_html=True)
                    
                    if orig_title and orig_title != movie['title'] and orig_title != title_zh:
                        st.markdown(f'<p class="movie-orig-title">{orig_title}</p>', unsafe_allow_html=True)
                else:
                    # Original logic for English mode
                    st.markdown(f'<h2 class="movie-title-header">{movie["title"]}</h2>', unsafe_allow_html=True)
                    
                    if orig_title and orig_title != movie['title'] and orig_title != title_zh:
                        st.markdown(f'<p class="movie-orig-title">{orig_title}</p>', unsafe_allow_html=True)
                        
                    if not orig_title and not title_zh:
                        st.markdown(f'<p class="movie-orig-title">{t("no_alt_title")}</p>', unsafe_allow_html=True)"""

content = content.replace(old_block, new_block)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Title UI patched.")
