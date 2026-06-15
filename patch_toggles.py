import re

file_path = "/Users/shanfu/cc/Projects/movie-database-revival/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# We need to replace the theme toggle and language select logic around line 1330.
# First, let's inject the callback functions before they are used.

callbacks_code = """
        with sub_c1:
            def toggle_theme_cb():
                st.session_state.theme = 'dark' if st.session_state.theme_toggle_btn else 'light'
            
            st.toggle("🌙", value=(st.session_state.theme == 'dark'), key="theme_toggle_btn", on_change=toggle_theme_cb)
                
        with sub_c2:
            def toggle_lang_cb():
                new_l = 'zh' if st.session_state.lang_select_btn == "简体中文" else 'en'
                st.session_state.lang = new_l
                st.query_params["lang"] = new_l
                save_env_vars({'UI_LANG': new_l})
                
            lang_options = ["简体中文", "English"]
            st.selectbox("🌐", lang_options, index=0 if st.session_state.lang == 'zh' else 1, label_visibility="collapsed", key="lang_select_btn", on_change=toggle_lang_cb)
"""

# The old code to replace
old_pattern = r'with sub_c1:.*?st\.rerun\(\)'
# Wait, st.rerun() is called twice, once for theme, once for lang.
# Let's match from `with sub_c1:` to the end of `with sub_c2:` block.

old_pattern_full = r'with sub_c1:.*?st\.rerun\(\)\s*with sub_c2:.*?st\.rerun\(\)'

content = re.sub(old_pattern_full, callbacks_code.strip(), content, flags=re.DOTALL)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Toggles patched with callbacks.")
