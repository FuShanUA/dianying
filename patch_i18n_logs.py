import re

with open('app.py', 'r') as f:
    content = f.read()

# 1. Fix "关闭 / Close" at finish
content = content.replace(
    'if st.button("关闭 / Close", use_container_width=True, key="batch_finish_close"):',
    'if st.button("关闭" if st.session_state.lang == \'zh\' else "Close", use_container_width=True, key="batch_finish_close"):'
)

# 2. Fix "正在处理 / Processing"
content = content.replace(
    'st.markdown(f"**🔄 正在处理 / Processing:** {m_title} ({idx+1}/{total})")',
    'status_label = "正在处理" if st.session_state.lang == \'zh\' else "Processing"\n        st.markdown(f"**🔄 {status_label}:** {m_title} ({idx+1}/{total})")'
)

# 3. Fix Expander title
content = content.replace(
    'with st.expander("跳过日志 / Skip Logs", expanded=True):',
    'expander_title = "执行日志" if st.session_state.lang == \'zh\' else "Execution Logs"\n            with st.expander(expander_title, expanded=True):'
)

# 4. Fix Pause/Resume/Stop buttons
old_buttons = """        with pc1:
            if st.session_state.batch_paused:
                if st.button("▶️ 继续 / Resume", use_container_width=True, key="batch_resume_btn"):
                    st.session_state.batch_paused = False
                    st.rerun()
            else:
                if st.button("⏸️ 暂停 / Pause", use_container_width=True, key="batch_pause_btn"):
                    st.session_state.batch_paused = True
                    st.rerun()
        with pc2:
            if st.button("⏹️ 停止并退出 / Stop & Close", use_container_width=True, key="batch_stop_btn"):"""

new_buttons = """        with pc1:
            if st.session_state.batch_paused:
                resume_label = "▶️ 继续" if st.session_state.lang == 'zh' else "▶️ Resume"
                if st.button(resume_label, use_container_width=True, key="batch_resume_btn"):
                    st.session_state.batch_paused = False
                    st.rerun()
            else:
                pause_label = "⏸️ 暂停" if st.session_state.lang == 'zh' else "⏸️ Pause"
                if st.button(pause_label, use_container_width=True, key="batch_pause_btn"):
                    st.session_state.batch_paused = True
                    st.rerun()
        with pc2:
            stop_label = "⏹️ 停止并退出" if st.session_state.lang == 'zh' else "⏹️ Stop & Close"
            if st.button(stop_label, use_container_width=True, key="batch_stop_btn"):"""
content = content.replace(old_buttons, new_buttons)

# 5. Fix Skip Log
old_skip_log = """            if 'batch_logs' not in st.session_state:
                st.session_state.batch_logs = []
            st.session_state.batch_logs.append(f"⚠️ 跳过: {m_title} (未找到TMDB数据)")"""

new_skip_log = """            if 'batch_logs' not in st.session_state:
                st.session_state.batch_logs = []
            skip_msg = f"⚠️ 跳过: {m_title} (未找到TMDB数据)" if st.session_state.lang == 'zh' else f"⚠️ Skip: {m_title} (No TMDB Data)"
            st.session_state.batch_logs.append(skip_msg)"""
content = content.replace(old_skip_log, new_skip_log)

# 6. Add Success Log (we need to inject this right after st.session_state.batch_success += 1)
old_success_inc = "st.session_state.batch_success += 1"
new_success_inc = """st.session_state.batch_success += 1
            if 'batch_logs' not in st.session_state:
                st.session_state.batch_logs = []
            success_msg = f"✅ 成功: {m_title}" if st.session_state.lang == 'zh' else f"✅ Success: {m_title}"
            st.session_state.batch_logs.append(success_msg)"""
content = content.replace(old_success_inc, new_success_inc)

# 7. Fix bottom "关闭 / Close" button
content = content.replace(
    'if st.button("关闭 / Close", use_container_width=True, key="batch_close_setup"):',
    'if st.button("关闭" if st.session_state.lang == \'zh\' else "Close", use_container_width=True, key="batch_close_setup"):'
)

with open('app.py', 'w') as f:
    f.write(content)

print("i18n and success log applied!")
