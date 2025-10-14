import streamlit as st

st.title("Chai Maker App")
if st.button("Make Chai"):
    st.success("Your chai is being brewed!")

add_masala = st.checkbox("Add Masala")
if add_masala:
    st.write("Masala has been added to your chai!")

tea_type = st.radio("Pick your chai base :", ["Milk", "Water", "Honey"])
st.write(f"You chose {tea_type} as your chai base.")

flavour = st.selectbox("Choose your flavour:", ["Cardamom", "Ginger", "Mint", "Cinnamon"])
st.write(f"You chose {flavour} as your flavour.")

sugar_level = st.slider("How much sugar do you want?", 0, 5, 2)
st.write(f"You added {sugar_level} spoons of sugar to your chai.")

cups = st.number_input("How many cups of chai do you want?", min_value=1, max_value=10, value=1)
st.write(f"You will get {cups} cup(s) of chai.")

name = st.text_input("Enter your name:")
if name:
    st.write(f"Hello {name}, your chai is on the way!")

dob = st.date_input("Enter your date of birth:")
st.write(f"Your date of birth is {dob}.")
