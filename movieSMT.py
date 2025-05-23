import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
from rapidfuzz import fuzz

st.markdown(
    """
    <style>
    /* Main background */
    .main {
        background-color: #e6f0ff;  /* Light blue */
    }

    /* Sidebar background */
    section[data-testid="stSidebar"] {
        background-color: #cce0ff;  /* Darker blue */
    }

    /* Optional: tweak text color for contrast */
    .css-1d391kg, .css-q8sbsg, .css-10trblm, .css-1v0mbdj {
        color: #000000 !important;  /* Black text */
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ---------- Page Configuration ----------
st.set_page_config(page_title="BookSMT", layout="wide")

# ---------- Configuration ----------
DATA_URL = "https://raw.githubusercontent.com/olivialaven/MGT502_project/refs/heads/main/merged_items.csv"
SIMILAR_ITEMS_URL = "https://raw.githubusercontent.com/olivialaven/MGT502_project/refs/heads/main/streamlit/similar_items.csv"
USERS = {
    "robertdowneyjr": {"password": "welovevlachos", "books": [942, 858, 8541, 4141, 8442]},
    "danieldieckmann": {"password": "welovevlachos", "books": [183, 884, 3881, 8434, 831]}
}

# ---------- Load Data ----------
@st.cache_data
def load_data():
    return pd.read_csv(DATA_URL)

@st.cache_data
def load_similar_items():
    return pd.read_csv(SIMILAR_ITEMS_URL)

df = load_data()
similar_df = load_similar_items()

TOP_TEN_SWITZERLAND = df['i'].value_counts().head(5).index.tolist()
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
    x = (img.width - (bbox[2] - bbox[0])) / 2
    y = (img.height - (bbox[3] - bbox[1])) / 2
    draw.text((x, y), text, fill=(80, 80, 80), font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ---------- Main Logic ----------
def main():
    if st.session_state.get("logged_out"):
        st.title("👋 Goodbye!")
        st.success("Thanks for visiting BookSMT. See you soon!")
        st.session_state.logged_out = False
        return

    for key in ["authenticated", "page", "basket", "selected_book"]:
        if key not in st.session_state:
            st.session_state[key] = False if key == "authenticated" else None if key == "selected_book" else [] if key == "basket" else "main"

    if not st.session_state.authenticated:
        login()
    else:
        navigation_sidebar()
        if st.session_state.page == "main":
            show_main_page()
        elif st.session_state.page == "book_detail":
            show_book_detail(st.session_state.selected_book)
        elif st.session_state.page == "checkout":
            show_checkout_page()

# ---------- Sidebar Navigation ----------
def navigation_sidebar():
    with st.sidebar:
        st.title("📚 BookSMT")
        if st.button("🏠 Home"):
            switch_to_main()
        if st.button("🧺 Basket"):
            st.session_state.page = "checkout"
            st.rerun()
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.page = "main"
            st.session_state.selected_book = None
            st.session_state.basket = []
            st.session_state.logged_out = True
            st.rerun()

# ---------- Login ----------
def login():
    st.title("🔐 Login to BookSMT")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in USERS and USERS[username]["password"] == password:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.page = "main"
            st.rerun()
        else:
            st.error("Invalid username or password.")

# ---------- Display Books ----------
def display_books(book_ids, section="default"):
    books = df[df['i'].isin(book_ids)]
    books = books[books['Title'].notna()]
    placeholder_img = generate_placeholder_image()

    for i in range(0, len(books), 5):
        row_books = books.iloc[i:i+5]
        cols = st.columns(5)
        for idx, (_, row) in enumerate(row_books.iterrows()):
            with cols[idx]:
                st.image(row['image'] if pd.notna(row['image']) else placeholder_img, use_container_width=True)
                button_key = f"{section}_book_{int(row['i'])}"
                if st.button("View", key=button_key):
                    st.session_state.selected_book = row['i']
                    st.session_state.page = "book_detail"
                    st.rerun()

# ---------- Basket ----------
def display_basket():
    st.subheader("🧺 Your Basket")
    if not st.session_state.basket:
        st.info("Your basket is empty.")
        return
    placeholder_img = generate_placeholder_image()
    basket_books = df[df['i'].isin(st.session_state.basket)]
    for i in range(0, len(basket_books), 5):
        row_books = basket_books.iloc[i:i+5]
        cols = st.columns(5)
        for idx, (_, row) in enumerate(row_books.iterrows()):
            with cols[idx]:
                st.image(row['image'] if pd.notna(row['image']) else placeholder_img, use_container_width=True)
                if st.button("Remove", key=f"remove_{row['i']}"):
                    st.session_state.basket.remove(row['i'])
                    st.rerun()
    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🗑️ Clear Basket"):
            st.session_state.basket = []
            st.rerun()
    with col2:
        if st.button("🧾 Go to Checkout"):
            st.session_state.page = "checkout"
            st.rerun()

# ---------- Main Page ----------
def show_main_page():
    st.title("🎬 BookSMT Dashboard")
    st.subheader("🔍 Search for a Book")
    search_query = st.text_input("Search by title or author")
    if search_query:
        results = df[df['Title'].notna()].copy()
        query = search_query.lower()

        def fuzzy_score(row):
            title = str(row['Title']).lower()
            author = str(row['Author']).lower() if pd.notna(row['Author']) else ""
            if query in title or query in author:
                return 100
            if title.startswith(query):
                return 95
            return max(fuzz.partial_ratio(query, title), fuzz.partial_ratio(query, author))

        results["score"] = results.apply(fuzzy_score, axis=1)
        results = results[results["score"] >= 60].sort_values(by=["score", "Title"], ascending=[False, True]).head(10)
        if results.empty:
            st.warning("No good matches found.")
        else:
            st.markdown("#### 🔎 Search Results")
            display_books(results['i'].astype(int).tolist(), section="search")
        st.markdown("---")

    st.subheader("🆕 New to BookSMT")
    display_books(NEW_TO_BOOKSMT, section="new")

    st.subheader("🇨🇭 Top Five in Switzerland")
    display_books(TOP_TEN_SWITZERLAND, section="topten")

    st.subheader("📖 Recommended For You")
    display_books(USERS[st.session_state.username]["books"], section=st.session_state.username)

    display_basket()

# ---------- Book Detail Page ----------
def show_book_detail(book_id):
    book = df[df['i'] == book_id].squeeze()
    placeholder_img = generate_placeholder_image()
    st.title(book['Title'])

    if st.button("⬅️ Back to Home"):
        switch_to_main()

    cols = st.columns([1, 2])
    with cols[0]:
        st.image(book['image'] if pd.notna(book['image']) else placeholder_img, use_container_width=True)
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
            if st.button("🧺 Add to Basket"):
                st.session_state.basket.append(book['i'])
                st.success("Book added to basket!")
        else:
            st.info("✅ Already in basket")

    # Similar items section
    similar_row = similar_df[similar_df['item_id'] == book_id]
    if not similar_row.empty:
        st.subheader("📚 Similar Books")
        similar_ids = [
            int(similar_row.iloc[0][col])
            for col in similar_row.columns[1:6]  # Only take the first 5 similar items
            if pd.notna(similar_row.iloc[0][col])
            ]
    
        display_books(similar_ids, section=f"similar_{book_id}")

        


    # More from same author
    author = book['Author']
    if pd.notna(author):
        same_author_books = df[(df['Author'] == author) & (df['i'] != book['i'])]
        if not same_author_books.empty:
            st.subheader(f"📚 More from {author}")
            display_books(same_author_books['i'].astype(int).tolist()[:5], section=f"more_{book_id}")
        else:
            st.subheader("📚 More from this author")
            st.info("No other books by this author found.")

# ---------- Checkout Page ----------
def show_checkout_page():
    st.title("📦 Reserve Your Books")
    if not st.session_state.basket:
        st.info("Your basket is empty.")
        if st.button("⬅️ Back to Main"):
            switch_to_main()
        return
    basket_books = df[df['i'].isin(st.session_state.basket)]
    placeholder_img = generate_placeholder_image()
    st.subheader("🧺 Your Items")
    for _, book in basket_books.iterrows():
        st.markdown(f"**{book['Title']}** by {book['Author']}")
        st.image(book['image'] if pd.notna(book['image']) else placeholder_img, width=100)
        st.markdown("---")
    if st.button("✅ Reserve Book"):
        st.success("🎉 Reservation successful! Thank you.")
        st.balloons()
        st.session_state.basket = []
        if st.button("⬅️ Return to Main Page"):
            switch_to_main()
    elif st.button("⬅️ Cancel and Go Back"):
        switch_to_main()

# ---------- Navigation ----------
def switch_to_main():
    st.session_state.page = "main"
    st.session_state.selected_book = None
    st.rerun()

# ---------- Run App ----------
if __name__ == "__main__":
    main()
