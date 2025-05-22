import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
from rapidfuzz import fuzz

# ---------- Configuration ----------
st.set_page_config(page_title="BookSMT", layout="wide")
DATA_URL = "https://raw.githubusercontent.com/olivialaven/MGT502_project/refs/heads/main/merged_items.csv"
SIMILAR_ITEMS_URL = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/similar_books.csv"

USERS = {
    "olivialaven": {"password": "ilovevlachos", "books": [942, 858, 8541, 4141, 8442]},
    "danieldieckmann": {"password": "1234", "books": [183, 884, 3881, 8434, 831]}
}

# ---------- Load Data ----------
@st.cache_data
def load_data():
    return pd.read_csv(DATA_URL)

@st.cache_data
def load_similar_items():
    return pd.read_csv(SIMILAR_ITEMS_URL)

df = load_data()
similar_books_df = load_similar_items()

top_books = df['i'].value_counts()
TOP_TEN_SWITZERLAND = top_books.head(5).index.tolist()
NEW_TO_BOOKSMT = [235, 8482, 8316, 5886, 838]

# ---------- Placeholder Image ----------
@st.cache_data
def generate_placeholder_image():
    img = Image.new('RGB', (150, 220), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    text = "Cover Not Available"
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (img.width - text_width) / 2
    y = (img.height - text_height) / 2
    draw.text((x, y), text, fill=(80, 80, 80), font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ---------- Display Books ----------
def display_books(book_ids, section="default"):
    books = df[df['i'].isin(book_ids)]
    books = books[books['Title'].notna()]
    placeholder_img = generate_placeholder_image()
    if books.empty:
        st.info("No books found for this section.")
        return
    for i in range(0, len(books), 5):
        row_books = books.iloc[i:i+5]
        cols = st.columns(5)
        for idx, (_, row) in enumerate(row_books.iterrows()):
            with cols[idx]:
                if pd.notna(row['image']):
                    st.image(row['image'], use_container_width=True)
                else:
                    st.image(placeholder_img, use_container_width=True)
                button_key = f"{section}_book_{int(row['i']) if pd.notna(row['i']) else i+idx}"
                if st.button("View", key=button_key):
                    st.session_state.selected_book = row['i']
                    st.session_state.page = "book_detail"
                    st.rerun()

# ---------- Book Detail Page ----------
def show_book_detail(book_id):
    book = df[df['i'] == book_id].squeeze()
    placeholder_img = generate_placeholder_image()

    st.title(book['Title'])
    if st.button("\u2b05\ufe0f Back to Home"):
        switch_to_main()

    cols = st.columns([1, 2])
    with cols[0]:
        if pd.notna(book['image']):
            st.image(book['image'], use_container_width=True)
        else:
            st.image(placeholder_img, use_container_width=True)

    with cols[1]:
        st.markdown(f"""
        ### {book['Title']}
        **Author:** {book['Author']}  
        **Published:** {book['date_published']}  
        **ISBN Valid:** {book['ISBN Valid']}  

        **Synopsis:**  
        {book['synopsis'] if pd.notna(book['synopsis']) else 'No synopsis available.'}
        """)

        if book['i'] not in st.session_state.basket:
            if st.button("\U0001f9fa Add to Basket"):
                st.session_state.basket.append(book['i'])
                st.success("Book added to basket!")
        else:
            st.info("\u2705 Already in basket")

    # ---------- Similar Books Section ----------
    similar_row = similar_books_df[similar_books_df['item_id'] == book_id]
    if not similar_row.empty:
        similar_ids = similar_row.iloc[0, 1:].dropna().astype(int).tolist()
        st.subheader("\ud83d\udcda Similar Books You Might Like")
        display_books(similar_ids[:5], section=f"similar_{book_id}")

    # ---------- More from Same Author ----------
    author = book['Author']
    if pd.notna(author):
        same_author_books = df[(df['Author'] == author) & (df['i'] != book['i'])]
        if not same_author_books.empty:
            st.subheader(f"\ud83d\udcda More from {author}")
            similar_ids = same_author_books['i'].dropna().astype(int).unique()[:5]
            display_books(similar_ids, section=f"more_{book_id}")
        else:
            st.subheader("\ud83d\udcda More from this author")
            st.info("No other books by this author found.")

# ---------- Run App ----------
# Continue with login(), logout_button(), show_main_page(), etc. from your existing code
# Paste those functions below this, unchanged unless you want help modifying those as well
