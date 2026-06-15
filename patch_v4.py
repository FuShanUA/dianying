import re

with open('app.py', 'r') as f:
    content = f.read()

# Make sure we have a logs list in state
if "'batch_logs'" not in content:
    content = content.replace("'show_add_movie_dialog']:", "'show_add_movie_dialog', 'batch_logs']:")

# Find the skip warning part
old_skip_block = """        if not details_en and not details_zh:
            st.session_state.batch_skip += 1
            st.warning(f"未能获取到 {m_title} 的数据，已跳过")
            import time
            time.sleep(1) # Give user a moment to see the skip warning"""

new_skip_block = """        if not details_en and not details_zh:
            st.session_state.batch_skip += 1
            st.session_state.batch_logs.append(f"⚠️ 跳过: {m_title} (未找到TMDB数据)")"""

content = content.replace(old_skip_block, new_skip_block)

# Display the logs below the progress
old_progress_block = """        m_id, m_title = targets[idx]
        st.markdown(f"**🔄 正在处理 / Processing:** {m_title} ({idx+1}/{total})")
        st.progress(idx / total if total > 0 else 0)"""

new_progress_block = """        m_id, m_title = targets[idx]
        st.markdown(f"**🔄 正在处理 / Processing:** {m_title} ({idx+1}/{total})")
        st.progress(idx / total if total > 0 else 0)
        
        if st.session_state.batch_logs:
            with st.expander("跳过日志 / Skip Logs", expanded=True):
                for log in st.session_state.batch_logs[-5:]:
                    st.write(log)"""

content = content.replace(old_progress_block, new_progress_block)

# Clear logs on start
old_start_block = """                        st.session_state.batch_running = True
                        st.session_state.batch_paused = False
                        st.rerun()"""

new_start_block = """                        st.session_state.batch_running = True
                        st.session_state.batch_paused = False
                        st.session_state.batch_logs = []
                        st.rerun()"""

content = content.replace(old_start_block, new_start_block)

with open('app.py', 'w') as f:
    f.write(content)

print("Logs feature added!")
