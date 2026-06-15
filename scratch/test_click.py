import streamlit as st

st.markdown("""
<style>
div[data-testid="column"] { position: relative !important; }
div[data-testid="stButton"] {
    position: absolute !important;
    top: 0 !important; left: 0 !important;
    width: 100% !important; height: 100% !important;
    z-index: 10 !important; opacity: 0.5 !important;
}
div[data-testid="stButton"] button {
    width: 100% !important; height: 100% !important;
}
</style>
""", unsafe_allow_html=True)

cols = st.columns(3)
for i in range(3):
    with cols[i]:
        st.markdown(f"<div style='background:lightblue; height: 100px;'>Poster {i}</div>", unsafe_allow_html=True)
        if st.button(" ", key=f"btn_{i}"):
            st.success(f"Clicked {i}")
