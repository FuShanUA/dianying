import streamlit as st

st.markdown("""
<style>
/* Make the column relative */
div[data-testid="column"] { position: relative !important; }

/* The actual card */
.poster-card {
    background: #2c3e50;
    height: 200px;
    border-radius: 10px;
    color: white;
    padding: 10px;
}

/* Make the stButton container absolute and transparent */
div[data-testid="stButton"] {
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    width: 100% !important;
    height: 100% !important;
    opacity: 0.5 !important; /* Semi-transparent for testing */
    z-index: 10 !important;
}

div[data-testid="stButton"] button {
    width: 100% !important;
    height: 100% !important;
}
</style>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="poster-card">Poster 1</div>', unsafe_allow_html=True)
    if st.button(" ", key="btn_1", use_container_width=True):
        st.success("Clicked 1")

with col2:
    st.markdown('<div class="poster-card">Poster 2</div>', unsafe_allow_html=True)
    if st.button(" ", key="btn_2", use_container_width=True):
        st.success("Clicked 2")
