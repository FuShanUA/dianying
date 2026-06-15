import streamlit as st

st.markdown("""
<style>
/* Reset */
.card-wrapper {
    background: red;
    height: 150px;
    position: relative;
}
/* Magic */
div[data-testid="stVerticalBlock"] > div.element-container:has(.card-wrapper) + div.element-container {
    margin-top: -160px !important;
    opacity: 0.5 !important; /* semi transparent to see it */
    z-index: 10 !important;
}
div[data-testid="stVerticalBlock"] > div.element-container:has(.card-wrapper) + div.element-container button {
    height: 150px !important;
    width: 100% !important;
}
</style>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown('<div class="card-wrapper">Poster 1</div>', unsafe_allow_html=True)
    if st.button(" ", key="btn_1", use_container_width=True):
        st.success("Clicked 1")
with col2:
    st.markdown('<div class="card-wrapper">Poster 2</div>', unsafe_allow_html=True)
    if st.button(" ", key="btn_2", use_container_width=True):
        st.success("Clicked 2")
