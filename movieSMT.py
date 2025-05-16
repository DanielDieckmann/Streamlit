import streamlit as st
import pandas as pd

# ---------- Configuration ----------
DATA_URL = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/your_file.csv"  # <-- Replace this!
USERS = {
    "olivialaven": {"password": "1234", "books": [942, 858, 8541, 4141, 8442, 912, 12, 84, 1394, 8742]},
    "danieldieckmann": {"password": "1234", "books": [183, 884, 3881, 84834, 831, 8592, 8529, 12, 414, 1446]}
}
NEW_TO_MOVIESMT = [23, 948, 48482, 8482, 8316, 5886, 584, 932, 9931, 5882]
TOP_TEN_SWITZERLAND = [23, 948, 48482, 8482, 8316, 5886, 14373, 4242, 489, 1233]

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
    st.title("🔐 Login to MovieSMT")
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
def display_books(book_ids):
    books = df[df['i'].isin(book_ids)]
    cols = st.columns(5)
    for idx, (_, row) in enumerate(books.iterrows()):
        with cols[idx % 5]:
            st.image(row['image'], width=100)
            if st.button(row['Title'], key=f"book_{row['i']}"):
                st.session_state.selected_book = row['i']
                st.session_state.page = "book_detail"
                st.rerun()

# ---------- Main Page ----------
def show_main_page():
    st.title("🎬 MovieSMT Dashboard")
    logout_button()

    st.subheader("🆕 New to MovieSMT")
    display_books(NEW_TO_MOVIESMT)

    st.subheader("🇨🇭 Top Ten in Switzerland")
    display_books(TOP_TEN_SWITZERLAND)

    st.subheader("📖 Recommended for You")
    user_books = USERS[st.session_state.username]["books"]
    display_books(user_books)

# ---------- Book Detail Page ----------
def show_book_detail(book_id):
    book = df[df['i'] == book_id].squeeze()
    st.title(book['Title'])

    st.button("⬅️ Back to Home", on_click=lambda: switch_to_main())

    cols = st.columns([1, 2])
    with cols[0]:
        st.image(book['image_original'], use_column_width=True)

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
