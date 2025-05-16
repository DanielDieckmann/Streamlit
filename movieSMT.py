import streamlit as st
import pandas as pd

# ---------- Configuration ----------
DATA_URL = "https://raw.githubusercontent.com/olivialaven/MGT502_project/refs/heads/main/merged_items.csv"
USERS = {
    "olivialaven": {"password": "1234", "books": [942, 858, 8541, 4141, 8442, 912, 12, 84, 1394, 8742]},
    "danieldieckmann": {"password": "1234", "books": [183, 884, 3881, 84834, 831, 8592, 8529, 12, 414, 1446]}
}
NEW_TO_BOOKSMT = [23, 8482, 8316, 5886, 584]
TOP_TEN_SWITZERLAND = [23, 948, 48482, 8482, 8316, 5886, 14373, 4242, 489, 11, 179]

# ---------- Load Data ----------
@st.cache_data
def load_data():
    return pd.read_csv(DATA_URL)

df = load_data()

# ---------- Main Logic ----------
def main():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.page = "main"

    if not st.session_state.authenticated:
        login()
    else:
        if st.session_state.page == "main":
            show_main_page()
        elif st.session_state.page == "book_detail":
            show_book_detail(st.session_state.selected_book)

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

# ---------- Logout Button ----------
def logout_button():
    if st.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.page = "main"
        st.session_state.selected_book = None
        st.rerun()

# ---------- Display Books ----------
def display_books(book_ids, section="default"):
    books = df[df['i'].isin(book_ids)]
    books = books[books['Title'].notna()]

    if books.empty:
        st.info("No books found for this section.")
        return

    # Display books in rows of 5
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



# ---------- Main Page ----------
def show_main_page():
    st.title("🎬 BookSMT Dashboard")
    logout_button()

    st.subheader("🆕 New to BookSMT")
    display_books(NEW_TO_BOOKSMT, section="new")

    st.subheader("🇨🇭 Top Ten in Switzerland")
    display_books(TOP_TEN_SWITZERLAND, section="topten")

    st.subheader("📖 Recommended For You")
    user_books = USERS[st.session_state.username]["books"]
    display_books(user_books, section=st.session_state.username)


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

def switch_to_main():
    st.session_state.page = "main"
    st.session_state.selected_book = None
    st.rerun()

# ---------- Run App ----------
if __name__ == "__main__":
    main()
