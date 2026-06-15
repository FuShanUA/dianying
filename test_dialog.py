import streamlit as st

@st.dialog("Test Dialog")
def my_dialog():
    st.write("Dialog is open!")
    if st.button("Rerun inside"):
        st.rerun()
    if st.button("Update state"):
        st.session_state.foo = "bar"

if st.button("Open Dialog"):
    my_dialog()
