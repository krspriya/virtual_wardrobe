import os
import streamlit as st
import pandas as pd
from PIL import Image
import requests
from io import BytesIO
import base64
from closet import closet
from streamlit_option_menu import option_menu
import google.generativeai as genai
import ast

# Define the folder to save images and metadata
IMAGE_FOLDER = 'wardrobe_images'
METADATA_FILE = 'metadata.csv'

st.set_page_config(
    page_title="Virtual Wardrobe",
    page_icon="👔",
)

def add_bg_from_local(image_file):
    with open(image_file, "rb") as image:
        encoded_image = base64.b64encode(image.read()).decode()
    
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpeg;base64,{encoded_image}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Add local background image
add_bg_from_local("bg.jpg")

# Create the folder if it doesn't exist
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# Function to save metadata
def save_metadata(image_path, category, color, season):
    if os.path.exists(METADATA_FILE):
        df = pd.read_csv(METADATA_FILE)
        # Ensure correct headers
        if 'Image Path' not in df.columns or 'Category' not in df.columns or 'Color' not in df.columns or 'Season' not in df.columns:
            df = pd.DataFrame(columns=['Image Path', 'Category', 'Color', 'Season'])
    else:
        df = pd.DataFrame(columns=['Image Path', 'Category', 'Color', 'Season'])

    new_entry = pd.DataFrame({
        'Image Path': [image_path],
        'Category': [category],
        'Color': [color],
        'Season': [season]
    })

    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(METADATA_FILE, index=False)

# Function to load metadata
def load_metadata():
    if os.path.exists(METADATA_FILE):
        df = pd.read_csv(METADATA_FILE)
        # Ensure correct headers
        if 'Image Path' not in df.columns or 'Category' not in df.columns or 'Color' not in df.columns or 'Season' not in df.columns:
            df = pd.DataFrame(columns=['Image Path', 'Category', 'Color', 'Season'])
        return df
    else:
        return pd.DataFrame(columns=['Image Path', 'Category', 'Color', 'Season'])

# Function to delete an item
def delete_item(index):
    df = load_metadata()
    if not df.empty:
        image_path = df.at[index, 'Image Path']
        if os.path.exists(image_path):
            os.remove(image_path)
        df = df.drop(index).reset_index(drop=True)
        df.to_csv(METADATA_FILE, index=False)

# Google Generative AI setup
api_key = '####################################'  # Replace this with your valid API key
genai.configure(api_key=api_key)

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
}

# Initialize the model
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

# Title
closet("Radha's Wardrobe")

# Top bar option menu
selected_option = option_menu(
    None,
    ["Your Closet", "Add New Items", "Suggest Outfits"],
    icons=["wardrobe", "plus-circle", "lightbulb"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
)

# Add "Share with Friends" button in the top right corner
col1, col2 = st.columns([3, 1])
with col1:
    st.write("")

with col2:
    if st.button('Share with Friends'):
        query_params = st.query_params
        current_url = st.experimental_get_query_params()
        base_url = st.config.get_option('browser.serverAddress')
        port = st.config.get_option('browser.serverPort')
        shareable_url = f"{base_url}:{port}/?{current_url}"
        st.write("Share this URL with your friends:")
        st.code(shareable_url)

# Option to view closet content
if selected_option == "Your Closet":
    # Sidebar for filtering items
    st.sidebar.title("Filter Items")

    # Load metadata
    df = load_metadata()

    # Unique filters for color, category, and season
    unique_colors = df['Color'].unique()
    unique_categories = df['Category'].unique()
    unique_seasons = df['Season'].unique()

    selected_colors = st.sidebar.multiselect('Color:', unique_colors)
    selected_categories = st.sidebar.multiselect('Category:', unique_categories)
    selected_seasons = st.sidebar.multiselect('Season:', unique_seasons)

    # Apply filters
    if selected_colors:
        df = df[df['Color'].isin(selected_colors)]
    if selected_categories:
        df = df[df['Category'].isin(selected_categories)]
    if selected_seasons:
        df = df[df['Season'].isin(selected_seasons)]

    if not df.empty:
        cols = st.columns(4)
        for index, row in df.iterrows():
            with cols[index % 4]:
                st.image(row['Image Path'], use_column_width=True)
                st.write(f"**Category:** {row['Category']}")
                if st.button('Delete', key=f"delete_{index}"):
                    delete_item(index)
                    st.experimental_rerun()
    else:
        st.write('No items in the closet yet.')

# Option to add new items
if selected_option == "Add New Items":
    st.header("Add New Items")

    # Input fields
    uploaded_image = st.file_uploader("Add image", type=['png', 'jpg', 'jpeg'])

    category = st.selectbox('Select a category:', [
        'Hats', 'Shirts', 'Pants', 'Dresses', 'Jackets', 
        'Sweaters', 'Shorts', 'Skirts', 'Shoes', 'Accessories', 'Other'
    ])
    if category == 'Other':
        category = st.text_input('Specify category')

    color = st.selectbox('Color:', [
        'White', 'Black', 'Red', 'Blue', 'Green', 
        'Yellow', 'Orange', 'Purple', 'Pink', 'Brown', 'Other'
    ])
    if color == 'Other':
        color = st.text_input('Specify color')

    season = st.selectbox('Season:', ['Spring', 'Summer', 'Fall', 'Winter', 'Other'])
    if season == 'Other':
        season = st.text_input('Specify season')

    if st.button('Submit'):
        if uploaded_image:
            # Save the original image
            image_path = os.path.join(IMAGE_FOLDER, uploaded_image.name)
            with open(image_path, 'wb') as f:
                f.write(uploaded_image.getbuffer())

                # Save metadata
                save_metadata(image_path, category, color, season)
                st.success('Image and metadata saved successfully!')

# Option to suggest outfits
if selected_option == "Suggest Outfits":
    st.header("Suggest Outfits")

    # User input for prompt
    user_prompt = st.text_input("Enter your prompt for outfit suggestions:")

    if st.button('Get Outfit Suggestions'):
        if user_prompt:
            # Load metadata
            df = load_metadata()

            # Define the prompt
            prompt = f"""
            Instruction: User has a set of clothes and you are an AI fashion stylist. Now choose a set of clothes according to the user's need.
            Return only images path of multiple sets of clothes in 2D list format.
            set of clothes: {{ 
            Image Path,Category,Color,Season
            {'\n'.join([f"{row['Image Path'].replace('\\', '/')},{row['Category']},{row['Color']},{row['Season']}" for _, row in df.iterrows()])}
            }}
            User: {user_prompt}
            """

            # Send the prompt to the chat session
            try:
                chat_session = model.start_chat(history=[])
                response = chat_session.send_message(prompt)
                print("Response from AI:", response.text)

                # Clean and process the response to extract image paths
                try:
                    # Extract the part of the response containing the list of lists
                    response_clean = response.text.split('```python\n')[1].split('\n```')[0].strip()
                    
                    # Convert response to a list of lists
                    image_paths = ast.literal_eval(response_clean)
                    
                    # Replace backslashes with forward slashes in image paths
                    image_paths = [[path.replace('\\', '/') for path in outfit] for outfit in image_paths]

                    # Display the suggested outfits
                    st.subheader("Suggested Outfits:")
                    for i, outfit in enumerate(image_paths):
                        st.write(f"**Outfit {i+1}:**")
                        cols = st.columns(len(outfit))
                        for j, image_path in enumerate(outfit):
                            if os.path.exists(image_path):
                                img = Image.open(image_path)
                                cols[j].image(img, use_column_width=True)
                            else:
                                cols[j].write(f"Image path not found: {image_path}")
                except (SyntaxError, ValueError) as e:
                    st.error(f"Error parsing response: {e}")
            except Exception as e:
                st.error(f"Error sending message: {e}")
        else:
            st.warning("Please enter a prompt to get outfit suggestions.")
