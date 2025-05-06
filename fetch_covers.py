import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO

# Load datasets (this runs once on every rerun)
interactions = pd.read_csv('https://raw.githubusercontent.com/olivialaven/MGT502_project/refs/heads/main/interactions_train.csv')
items = pd.read_csv("https://raw.githubusercontent.com/olivialaven/MGT502_project/refs/heads/main/items.csv")
recommendations = pd.read_csv("https://raw.githubusercontent.com/DanielDieckmann/Streamlit/refs/heads/main/top_recs.csv")

# === Functions ===

def get_recommendations_as_list(df, user_id, id_col='user_id', rec_col='recommendations'):
    result = df.loc[df[id_col] == int(user_id), rec_col]
    if not result.empty:
        return result.values[0].split()
    return []

def get_isbn_dict_by_book_ids(book_id_list, books_df, book_id_col='i', isbn_col='ISBN Valid'):
    book_id_list = list(map(str, book_id_list))
    books_df = books_df.copy()
    books_df[book_id_col] = books_df[book_id_col].astype(str)
    matched_df = books_df[books_df[book_id_col].isin(book_id_list)][[book_id_col, isbn_col]]
    matched_df[isbn_col] = matched_df[isbn_col].astype(str).str.split()
    isbn_dict = matched_df.set_index(book_id_col)[isbn_col].to_dict()
    return isbn_dict

def get_book_covers_by_isbn_dict(isbn_dict):
    cover_dict = {}
    for book_id, isbn_list in isbn_dict.items():
        cover_url = None
        for isbn in isbn_list:
            try:
                response = requests.get(f'https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}')
                if response.status_code != 200:
                    continue
                data = response.json()
                if 'items' not in data:
                    continue
                volume_info = data['items'][0].get('volumeInfo', {})
                image_links = volume_info.get('imageLinks', {})
                cover_url = image_links.get('thumbnail')
                if cover_url:
                    break
            except Exception as e:
                st.warning(f"Error fetching ISBN {isbn} for book {book_id}: {e}")
        cover_dict[book_id] = cover_url
    return cover_dict

def show_book_covers_from_dict(cover_dict):
    if not cover_dict:
        st.warning("No book covers to display.")
        return
    book_ids = list(cover_dict.keys())
    num_books = len(book_ids)
    fig, axes = plt.subplots(1, num_books, figsize=(2.5 * num_books, 5))
    if num_books == 1:
        axes = [axes]
    for i, book_id in enumerate(book_ids):
        ax = axes[i]
        cover_url = cover_dict[book_id]
        if cover_url:
            try:
                response = requests.get(cover_url)
                img = Image.open(BytesIO(response.content))
                ax.imshow(img)
            except:
                _show_placeholder(ax)
        else:
            _show_placeholder(ax)
        ax.axis('off')
    plt.tight_layout()
    st.pyplot(fig)

def _show_placeholder(ax):
    ax.text(0.5, 0.5, "Cover Not\nAvailable", ha='center', va='center', fontsize=10, wrap=True)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor('lightgray')

# === Streamlit App ===

st.title("Book Cover Recommender")

# Step 1: Get input from user
target_user_id = st.text_input("Enter a user ID (e.g., 5848):")

# Step 2: Button to trigger processing
if st.button("Run Code"):
    if not target_user_id.strip().isdigit():
        st.warning("Please enter a valid numeric user ID.")
    else:
        st.write("Running recommendation pipeline...")

        top_ten_user = get_recommendations_as_list(recommendations, target_user_id)
        st.write(f"Recommended book IDs: {top_ten_user}")

        isbn_dict = get_isbn_dict_by_book_ids(top_ten_user, items)
        st.write(f"ISBN dictionary: {isbn_dict}")

        cover_urls = get_book_covers_by_isbn_dict(isbn_dict)
        st.write(f"Cover URLs: {cover_urls}")

        show_book_covers_from_dict(cover_urls)
        st.success("Done!")
