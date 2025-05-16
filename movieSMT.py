import streamlit as st
import pandas as pd

# ---------- Configuration ----------
DATA_URL = "https://raw.githubusercontent.com/olivialaven/MGT502_project/refs/heads/main/merged_items.csv"
USERS = {
    "olivialaven": {"password": "ilovevlachos", "books": [942, 858, 8541, 4141, 8442]},
    "danieldieckmann": {"password": "1234", "books": [183, 884, 3881, 84834, 831]}
}
NEW_TO_BOOKSMT = [235, 8482, 8316, 5886, 584, 838]
TOP_TEN_SWITZERLAND = [2663, 948, 48482, 8482, 8316, 123]

# ---------- Load Data ----------
@st.cache_data
def load_data():
    return pd.read_csv(DATA_URL)

df = load_data()

# ---------- Main Logic ----------
def main():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "page" not in st.session_state:
        st.session_state.page = "main"
    if "basket" not in st.session_state:
        st.session_state.basket = []
    if "selected_book" not in st.session_state:
        st.session_state.selected_book = None

    if not st.session_state.authenticated:
        login()
    else:
        if st.session_state.page == "main":
            show_main_page()
        elif st.session_state.page == "book_detail":
            show_book_detail(st.session_state.selected_book)
        elif st.session_state.page == "checkout":
            show_checkout_page()

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

# ---------- Logout ----------
def logout_button():
    if st.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.page = "main"
        st.session_state.selected_book = None
        st.session_state.basket = []
        st.rerun()

# ---------- Display Books ----------
def display_books(book_ids, section="default"):
    books = df[df['i'].isin(book_ids)]
    books = books[books['Title'].notna()]

    if books.empty:
        st.info("No books found for this section.")
        return

    for i in range(0, len(books), 5):
        row_books = books.iloc[i:i+5]
        cols = st.columns(5)
        for idx, (_, row) in enumerate(row_books.iterrows()):
            with cols[idx]:
                image_url = row['image'] if pd.notna(row['image']) else None
                if image_url:
                    st.image(image_url, use_container_width=True)
                else:
                    st.markdown("📕 *Cover not available*")

                button_key = f"{section}_book_{int(row['i']) if pd.notna(row['i']) else i+idx}"
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

    basket_books = df[df['i'].isin(st.session_state.basket)]
    for i in range(0, len(basket_books), 5):
        row_books = basket_books.iloc[i:i+5]
        cols = st.columns(5)
        for idx, (_, row) in enumerate(row_books.iterrows()):
            with cols[idx]:
                if pd.notna(row['image']):
                    st.image(row['image'], use_container_width=True)
                else:
                    st.markdown("📕 *Cover not available*")
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
    logout_button()

    st.subheader("🆕 New to BookSMT")
    display_books(NEW_TO_BOOKSMT, section="new")

    st.subheader("🇨🇭 Top Five in Switzerland")
    display_books(TOP_TEN_SWITZERLAND, section="topten")

    st.subheader("📖 Recommended For You")
    user_books = USERS[st.session_state.username]["books"]
    display_books(user_books, section=st.session_state.username)

    display_basket()

# ---------- Book Detail Page ----------
def show_book_detail(book_id):
    book = df[df['i'] == book_id].squeeze()
    st.title(book['Title'])

    if st.button("⬅️ Back to Home"):
        switch_to_main()

    cols = st.columns([1, 2])
    with cols[0]:
        image_url = book['image'] if pd.notna(book['image']) else book['image']
        if pd.notna(image_url):
            st.image(image_url, use_container_width=True)
        else:
            st.warning("No image available.")

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

    # More by the same author
    author = book['Author']
    if pd.notna(author):
        same_author_books = df[(df['Author'] == author) & (df['i'] != book['i'])]
        if not same_author_books.empty:
            st.subheader(f"📚 More from {author}")
            similar_ids = same_author_books['i'].dropna().astype(int).unique()[:5]
            display_books(similar_ids, section=f"more_{book_id}")
        else:
            st.subheader("📚 More from this author")
            st.info("No other books by this author found.")

# ---------- Checkout Page ----------
def show_checkout_page():
    st.title("💳 Checkout")

    if not st.session_state.basket:
        st.info("Your basket is empty.")
        if st.button("⬅️ Back to Main"):
            switch_to_main()
        return

    basket_books = df[df['i'].isin(st.session_state.basket)]

    st.subheader("🧺 Your Items")
    for _, book in basket_books.iterrows():
        st.markdown(f"**{book['Title']}** by {book['Author']}")
        if pd.notna(book['image']):
            st.image(book['image'], width=100)
        st.markdown("---")

    st.subheader("💳 Payment Options")
    st.markdown("🔘 **Apple Pay (Mock)**")

    if st.button("✅ Pay with Apple Pay"):
        st.success("🎉 Mock payment successful! Thank you.")
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
