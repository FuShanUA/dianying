import sys

with open('app.py', 'r') as f:
    content = f.read()

# 1. Update State initialization
content = content.replace("'show_add_movie_dialog', 'batch_logs']:", "'show_movie_edit_dialog', 'edit_target_movie', 'batch_logs']:")

# 2. Add movie_edit_dialog trigger
old_trigger = """    if st.session_state.get('show_batch_dialog', False):
        batch_metadata_dialog(covers_dir)"""
new_trigger = """    if st.session_state.get('show_batch_dialog', False):
        batch_metadata_dialog(covers_dir)
        
    if st.session_state.get('show_movie_edit_dialog', False):
        movie_edit_dialog(st.session_state.get('edit_target_movie', None))"""
content = content.replace(old_trigger, new_trigger)

# 3. Update top nav Add Movie button
old_add_btn = """            with sub_c5:
                if st.button("➕ " + t("add_entry_title"), use_container_width=True):
                    add_movie_dialog()"""
new_add_btn = """            with sub_c5:
                if st.button("➕ " + t("add_entry_title"), use_container_width=True):
                    st.session_state.edit_target_movie = None
                    st.session_state.show_movie_edit_dialog = True"""
content = content.replace(old_add_btn, new_add_btn)

# 4. Remove old add_movie_dialog
start_idx = content.find('@st.dialog("🎬")\ndef add_movie_dialog():')
end_idx = content.find('@st.dialog("✨ Batch Meta")')
if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + content[end_idx:]

# 5. Transform render_manual_edit_form into movie_edit_dialog
old_render_manual = """# Helper to render the manual edit form for a movie
def render_manual_edit_form(movie):
    with st.form(f"manual_edit_form_{movie['id']}"):
        e_title = st.text_input(t("form_title"), value=movie['title'])"""
new_movie_edit_dialog = """# Shared dialog for Add and Edit Movie
@st.dialog("🎬")
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

    e_title = st.text_input(t("form_title") + " *", value=movie['title'])"""
content = content.replace(old_render_manual, new_movie_edit_dialog)

# Indentation of fields inside movie_edit_dialog: they were indented by 8 spaces (inside `with st.form:`).
# Now they should be indented by 4 spaces. We can fix this by replacing the submit logic first.
old_form_submit = """        submit_edit = st.form_submit_button(t("form_submit"), use_container_width=True)
        if submit_edit:
            update_fields = {"""
new_form_submit = """    bc1, bc2 = st.columns(2)
    with bc1:
        submit_edit = st.button(t("form_submit"), use_container_width=True, type="primary")
    with bc2:
        close_btn = st.button("关闭" if st.session_state.lang == 'zh' else "Close", use_container_width=True)
        
    if close_btn:
        st.session_state.show_movie_edit_dialog = False
        st.rerun()

    if submit_edit:
        if not e_title.strip():
            st.error("标题不能为空" if st.session_state.lang == 'zh' else "Title is required")
        else:
            update_fields = {"""
content = content.replace(old_form_submit, new_form_submit)

old_update_block = """            update_movie_fields(movie['id'], update_fields)
            st.success(t("form_success"))
            st.rerun()"""
new_update_block = """            if movie['id'] is None:
                new_id = insert_new_movie(e_title.strip())
                update_movie_fields(new_id, update_fields)
                st.session_state.selected_movie_id = new_id
                st.query_params["movie_id"] = str(new_id)
            else:
                update_movie_fields(movie['id'], update_fields)
            st.session_state.show_movie_edit_dialog = False
            st.success(t("form_success"))
            st.rerun()"""
content = content.replace(old_update_block, new_update_block)

# Since we removed `with st.form:`, lines between `e_orig_title` and `submit_edit` are now over-indented by 4 spaces.
# It doesn't cause syntax errors in Python, but it's ugly. We will let it be for now to avoid regex nightmares.
# Wait, actually python requires correct indentation. Lines following `e_title = ...` that were inside `with st.form:` have 8 spaces.
# Since we removed `with st.form:`, the block has NO parent for those 8 spaces! This will cause an IndentationError.
# We must un-indent them!
lines = content.split('\n')
in_dialog = False
for i, line in enumerate(lines):
    if line.startswith('def movie_edit_dialog(movie=None):'):
        in_dialog = True
    elif in_dialog and line.startswith('    bc1, bc2 = st.columns(2)'):
        in_dialog = False
    elif in_dialog and line.startswith('        ') and not line.startswith('            '):
        # Unindent by 4 spaces
        lines[i] = line[4:]
content = '\n'.join(lines)

# 6. Refactor Detail view's right panel
# We need to replace from `tab_auto, tab_manual = st.tabs...` to `render_manual_edit_form(movie)`
start_str = 'tab_auto, tab_manual = st.tabs([t("tab_auto"), t("tab_manual")])'
end_str = 'render_manual_edit_form(movie)'

start_idx = content.find(start_str)
end_idx = content.find(end_str)

if start_idx != -1 and end_idx != -1:
    old_tabs_block = content[start_idx:end_idx + len(end_str)]
    new_tabs_block = """st.markdown("---")
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
    content = content.replace(old_tabs_block, new_tabs_block)


with open('app.py', 'w') as f:
    f.write(content)

print("Architecture patch applied!")
