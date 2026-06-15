import streamlit as st

st.set_page_config(layout="wide")

st.markdown("""
<style>
/* Make the column relative */
div[data-testid="column"] {
    position: relative !important;
    background-color: lightgray;
    height: 200px;
    border: 1px solid black;
}

/* Absolute position the stButton container to cover the column */
div[data-testid="column"] div[data-testid="stButton"] {
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    width: 100% !important;
    height: 100% !important;
    z-index: 10 !important;
    opacity: 0 !important; /* Change to 0.5 to see it while testing */
}

div[data-testid="column"] div[data-testid="stButton"] button {
    width: 100% !important;
    height: 100% !important;
    cursor: pointer !important;
}
</style>
""", unsafe_allow_html=True)

if 'click_count' not in st.session_state:
    st.session_state.click_count = 0

def on_click():
    st.session_state.click_count += 1

cols = st.columns(3)
with cols[0]:
    st.markdown("<div style='padding: 20px;'><h3>Poster 1</h3><p>Click me</p></div>", unsafe_allow_html=True)
    st.button("Hidden Btn 1", on_click=on_click, key="btn1")

with cols[1]:
    st.markdown("<div style='padding: 20px;'><h3>Poster 2</h3><p>Click me</p></div>", unsafe_allow_html=True)
    st.button("Hidden Btn 2", on_click=on_click, key="btn2")

st.write(f"Button clicked: {st.session_state.click_count} times")
