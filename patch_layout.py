import re

with open('app.py', 'r') as f:
    content = f.read()

# 1. Update I18N
content = content.replace('"settings_stats": "⚙️ 设置",', '"settings_stats": "⚙️ 其它设置",\n        "batch_meta_title": "✨ 批量补全",')
content = content.replace('"settings_stats": "⚙️ Settings",', '"settings_stats": "⚙️ Other Settings",\n        "batch_meta_title": "✨ Batch Metadata",')

# 2. Extract batch metadata to its own function
batch_block_start = content.find('        st.markdown("---")\n        \n        # Batch Autocomplete in settings popover')
batch_block_end = content.find('                    st.rerun()\n\n# Helper to render the manual edit form') + len('                    st.rerun()\n')

batch_block = content[batch_block_start:batch_block_end]

# Modify batch block to be a new function
new_func = """
def render_batch_metadata_popover(covers_dir):
    with st.popover(t("batch_meta_title"), use_container_width=True):
        st.markdown(f"<h3 style='color:{{text_color}};margin-top:0;'>{{t('batch_title')}}</h3>", unsafe_allow_html=True)
"""
# Deduce indentation - we just need to replace the `        ` with `        `
# Wait, the original batch block starts with 8 spaces indentation. We just paste it inside `with st.popover`.
new_func_body = batch_block.replace('        st.markdown("---")\n        \n        # Batch Autocomplete in settings popover', '        # Batch Autocomplete')

# But wait, in the original, it uses `text_color`. So `text_color` must be passed or accessed.
# Let's just use simple text.
new_func = """
def render_batch_metadata_popover(covers_dir):
    with st.popover(t("batch_meta_title"), use_container_width=True):
""" + new_func_body

content = content[:batch_block_start] + content[batch_block_end:]
# insert new function right above render_settings_popover
insert_pos = content.find('def render_settings_popover')
content = content[:insert_pos] + new_func + '\n' + content[insert_pos:]

# 3. Update the top header controls
old_ctrls = """    with col_ctrls:
        # Mini controls columns: lang, theme, slider, settings, add (settings & add hidden in cloud)
        if is_cloud:
            sub_c1, sub_c2, sub_c3 = st.columns([1.5, 0.8, 2.0])
        else:
            sub_c1, sub_c2, sub_c3, sub_c4, sub_c5 = st.columns([1.2, 0.8, 2.0, 1.2, 1.8])
        
        with sub_c1:
            def toggle_lang_cb():
                new_l = 'zh' if st.session_state.lang_select_btn == "简体中文" else 'en'
                st.session_state.lang = new_l
                st.query_params["lang"] = new_l
                save_env_vars({'UI_LANG': new_l})
                
            lang_options = ["简体中文", "English"]
            st.selectbox("🌐", lang_options, index=0 if st.session_state.lang == 'zh' else 1, label_visibility="collapsed", key="lang_select_btn", on_change=toggle_lang_cb)
            
        with sub_c2:
            def toggle_theme_cb():
                st.session_state.theme = 'dark' if st.session_state.theme_toggle_btn else 'light'
            
            st.toggle("🌙", value=(st.session_state.theme == 'dark'), key="theme_toggle_btn", on_change=toggle_theme_cb)
            
        with sub_c3:
            cols_per_row = st.slider(t("columns_slider_label"), min_value=2, max_value=8, value=6, step=1, key="poster_cols_per_row", label_visibility="collapsed")
                
        if not is_cloud:
            with sub_c4:
                render_settings_popover(total_count, seen_count, text_color, sub_text_color, covers_dir)
                
            with sub_c5:
                render_add_movie_popover()"""

new_ctrls = """    with col_ctrls:
        if is_cloud:
            sub_c1, sub_c2, sub_c3 = st.columns([1.5, 0.8, 2.0])
            with sub_c1:
                def toggle_lang_cb():
                    new_l = 'zh' if st.session_state.lang_select_btn == "简体中文" else 'en'
                    st.session_state.lang = new_l
                    st.query_params["lang"] = new_l
                    save_env_vars({'UI_LANG': new_l})
                lang_options = ["简体中文", "English"]
                st.selectbox("🌐", lang_options, index=0 if st.session_state.lang == 'zh' else 1, label_visibility="collapsed", key="lang_select_btn", on_change=toggle_lang_cb)
            with sub_c2:
                def toggle_theme_cb():
                    st.session_state.theme = 'dark' if st.session_state.theme_toggle_btn else 'light'
                st.toggle("🌙", value=(st.session_state.theme == 'dark'), key="theme_toggle_btn", on_change=toggle_theme_cb)
            with sub_c3:
                cols_per_row = st.slider(t("columns_slider_label"), min_value=2, max_value=8, value=6, step=1, key="poster_cols_per_row", label_visibility="collapsed")
        else:
            # Layout requested: Settings area on the left, gap, then Add Movie and Batch Meta on the right.
            # Using st.columns with specific flex widths to push right items to the far right.
            sub_c1, sub_c2, sub_c3, sub_c4, spacer, sub_c5, sub_c6 = st.columns([1.0, 0.6, 1.4, 1.1, 0.3, 1.2, 1.0])
            with sub_c1:
                def toggle_lang_cb():
                    new_l = 'zh' if st.session_state.lang_select_btn == "简体中文" else 'en'
                    st.session_state.lang = new_l
                    st.query_params["lang"] = new_l
                    save_env_vars({'UI_LANG': new_l})
                lang_options = ["简体中文", "English"]
                st.selectbox("🌐", lang_options, index=0 if st.session_state.lang == 'zh' else 1, label_visibility="collapsed", key="lang_select_btn", on_change=toggle_lang_cb)
            with sub_c2:
                def toggle_theme_cb():
                    st.session_state.theme = 'dark' if st.session_state.theme_toggle_btn else 'light'
                st.toggle("🌙", value=(st.session_state.theme == 'dark'), key="theme_toggle_btn", on_change=toggle_theme_cb)
            with sub_c3:
                cols_per_row = st.slider(t("columns_slider_label"), min_value=2, max_value=8, value=6, step=1, key="poster_cols_per_row", label_visibility="collapsed")
            with sub_c4:
                render_settings_popover(total_count, seen_count, text_color, sub_text_color, covers_dir)
            with sub_c5:
                render_add_movie_popover()
            with sub_c6:
                render_batch_metadata_popover(covers_dir)"""

content = content.replace(old_ctrls, new_ctrls)

with open('app.py', 'w') as f:
    f.write(content)
print("Patched!")
