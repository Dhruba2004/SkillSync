import streamlit as st


st.title("Hello, Chai App")

st.subheader("Brewed with streamlit")

st.text("Welcome to your first interactive app!")

chai = st.selectbox("Your fav chai:", ["Masala chai", "Lemon chai", "Green chai", "Ginger chai"])

st.write(f"You selected {chai}. Enjoy your cup of chai!")

st.success("Your chai has been brewed successfully!")
