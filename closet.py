import streamlit as st
from PIL import Image

def closet(show_text="Welcome!"):
    # st.subheader("*Welcome,*")
    st.markdown(f"""
        <style>
            #animated-text {{
                font-size: 60px;
                font-weight: bold;
                font-family: Arial, sans-serif;
                animation: color-change 2s infinite alternate;
            }}
            @keyframes color-change {{
                from {{color: blue;}}
                to {{color: red;}}
            }}
        </style>
        <div id="animated-text">{show_text}</div>
        <script>
            // JavaScript for animation control (optional)
            // You can use JavaScript to control more complex animations
        </script>
    """, unsafe_allow_html=True)
    
