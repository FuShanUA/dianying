import re

with open('app.py', 'r') as f:
    content = f.read()

# Fix the render check
old_render = "if st.session_state.batch_logs:"
new_render = "if st.session_state.get('batch_logs'):"
content = content.replace(old_render, new_render)

# Fix the append logic
old_append = "st.session_state.batch_logs.append(f\"⚠️ 跳过: {m_title} (未找到TMDB数据)\")"
new_append = """if 'batch_logs' not in st.session_state:
                st.session_state.batch_logs = []
            st.session_state.batch_logs.append(f"⚠️ 跳过: {m_title} (未找到TMDB数据)")"""
content = content.replace(old_append, new_append)

# Fix the start button init
old_start = """                            st.session_state.batch_running = True
                            st.session_state.batch_paused = False
                            st.rerun()"""
new_start = """                            st.session_state.batch_running = True
                            st.session_state.batch_paused = False
                            st.session_state.batch_logs = []
                            st.rerun()"""
content = content.replace(old_start, new_start)

with open('app.py', 'w') as f:
    f.write(content)

print("Logs fix applied!")
