import re

with open('app.py', 'r') as f:
    content = f.read()

# 1. Add delete_movie
old_delete_loc = """def insert_new_movie(title):"""
new_delete_loc = """def delete_movie(movie_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
    conn.commit()
    conn.close()

def insert_new_movie(title):"""
content = content.replace(old_delete_loc, new_delete_loc)

# 2. Add Reset Button to Filters bar
old_columns_def = """    col_q, col_y, col_g, col_c, col_l, col_s, col_sort = st.columns([2.0, 1.1, 1.1, 1.1, 1.1, 1.1, 1.2])"""
new_columns_def = """    col_q, col_y, col_g, col_c, col_l, col_s, col_sort, col_reset = st.columns([2.0, 1.1, 1.1, 1.1, 1.1, 1.1, 1.2, 0.4])"""
content = content.replace(old_columns_def, new_columns_def)

old_col_sort = """    with col_sort:
        sort_by_sel = st.selectbox(t("filter_sort"), ["Added Date", "Year", "Rating (IMDb)", "Rating (Douban)", "Runtime"], key=f"sort_by_sel{lang_suffix}")"""
new_col_sort = """    with col_sort:
        sort_by_sel = st.selectbox(t("filter_sort"), ["Added Date", "Year", "Rating (IMDb)", "Rating (Douban)", "Runtime"], key=f"sort_by_sel{lang_suffix}")
    with col_reset:
        st.markdown("<div style='margin-top: 1.83rem;'></div>", unsafe_allow_html=True)
        if st.button("🔄", help="Reset Filters", use_container_width=True):
            for k in ["filter_search_input", f"filter_year_sel{lang_suffix}", f"filter_genre_sel{lang_suffix}", f"filter_country_sel{lang_suffix}", f"filter_lang_sel{lang_suffix}", f"filter_status_sel{lang_suffix}", f"sort_by_sel{lang_suffix}"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()"""
content = content.replace(old_col_sort, new_col_sort)

# 3. Add Delete Button to Detail View
old_detail_buttons = """                st.markdown("---")
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("✨ " + t("auto_complete_title"), use_container_width=True):
                        st.session_state.batch_targets = [(movie['id'], movie['title'])]
                        st.session_state.batch_index = 0
                        st.session_state.batch_success = 0
                        st.session_state.batch_skip = 0
                        st.session_state.batch_running = True
                        st.session_state.batch_paused = False
                        st.session_state.batch_logs = []
                        st.session_state.show_batch_dialog = True
                        st.rerun()
                with col_btn2:
                    if st.button("✏️ " + t("manual_edit_title"), use_container_width=True):
                        st.session_state.edit_target_movie = movie
                        st.session_state.show_movie_edit_dialog = True
                        st.rerun()"""
new_detail_buttons = """                st.markdown("---")
                col_btn1, col_btn2, col_btn3 = st.columns([1,1,0.5])
                with col_btn1:
                    if st.button("✨ " + t("auto_complete_title"), use_container_width=True):
                        st.session_state.batch_targets = [(movie['id'], movie['title'])]
                        st.session_state.batch_index = 0
                        st.session_state.batch_success = 0
                        st.session_state.batch_skip = 0
                        st.session_state.batch_running = True
                        st.session_state.batch_paused = False
                        st.session_state.batch_logs = []
                        st.session_state.show_batch_dialog = True
                        st.rerun()
                with col_btn2:
                    if st.button("✏️ " + t("manual_edit_title"), use_container_width=True):
                        st.session_state.edit_target_movie = movie
                        st.session_state.show_movie_edit_dialog = True
                        st.rerun()
                with col_btn3:
                    if st.button("🗑️", use_container_width=True):
                        st.session_state.delete_confirm = movie['id']
                        st.rerun()
                if st.session_state.get('delete_confirm') == movie['id']:
                    st.error("确定要永久删除这部影片吗？ / Permanently delete?" )
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        if st.button("确认 / Confirm", use_container_width=True, type="primary"):
                            delete_movie(movie['id'])
                            st.session_state.selected_movie_id = None
                            if "movie_id" in st.query_params:
                                del st.query_params["movie_id"]
                            del st.session_state['delete_confirm']
                            st.rerun()
                    with cc2:
                        if st.button("取消 / Cancel", use_container_width=True):
                            del st.session_state['delete_confirm']
                            st.rerun()"""
content = content.replace(old_detail_buttons, new_detail_buttons)

# 4. Remove whitespace (padding-top block-container)
old_css_padding = """        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }"""
new_css_padding = """        padding-top: 0rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* Reduce general vertical gap between elements globally */
    div[data-testid="stVerticalBlock"] {
        gap: 0.5rem !important;
    }"""
content = content.replace(old_css_padding, new_css_padding)

with open('app.py', 'w') as f:
    f.write(content)

print("Updates applied")
