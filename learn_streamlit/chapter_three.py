import streamlit as st
st.title("Chai Taste Poll")

col1 , col2 = st.columns(2)

with col1:
    st.header("Masala Chai")
    vote1 = st.button("Vote for Masala Chai")
with col2:
    st.header("Adrak Chai")
    vote2 = st.button("Vote for Adrak Chai")

if vote1:
    st.success("Thanks for voting Masala Chai!")
if vote2:
    st.success("Thanks for voting Adrak Chai!")

name = st.sidebar.text_input("Enter your name:")
tea = st.sidebar.selectbox("Select your favorite tea:", ["Masala Chai", "Adrak Chai", "Lemon Chai", "Green Tea"])
st.write(f"Hello {name}, you selected {tea} as your favorite tea.")

with st.expander("Show chai making instructions"):
    st.write("""
    1. Boil water in a pot.
    2. Add tea leaves and let it steep.
    3. Add milk and sugar to taste.
    4. Strain into a cup and enjoy!
    """)