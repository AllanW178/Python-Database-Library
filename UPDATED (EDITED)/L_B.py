import easygui as eg
import sqlite3
import os
from datetime import datetime


# -----------------------------
# Database Setup
# -----------------------------
def setup_database():
    """Connect to or create the database and its tables."""
    try:
        conn = sqlite3.connect('library_database.db')
        cursor = conn.cursor()

        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS Authors (
            Author_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Author_Name TEXT NOT NULL,
            Country TEXT
        );

        CREATE TABLE IF NOT EXISTS Borrowers (
            Borrower_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Borrower_Name TEXT NOT NULL,
            Email TEXT UNIQUE,
            Phone TEXT
        );

        CREATE TABLE IF NOT EXISTS Library_database (
            Book_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Title TEXT NOT NULL,
            Genre TEXT,
            Date_Published TEXT,
            Pages INTEGER,
            Author_ID INTEGER,
            FOREIGN KEY (Author_ID) REFERENCES Authors(Author_ID)
        );

        CREATE TABLE IF NOT EXISTS Loans (
            Loan_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Book_ID INTEGER NOT NULL,
            Borrower_ID INTEGER NOT NULL,
            Loan_Date TEXT NOT NULL,
            Return_Date TEXT,
            FOREIGN KEY (Book_ID) REFERENCES Library_database(Book_ID),
            FOREIGN KEY (Borrower_ID) REFERENCES Borrowers(Borrower_ID)
        );
        """)

        conn.commit()
        return conn, cursor

    except sqlite3.Error as e:
        eg.exceptionbox(f"Database error: {e}", "Error")
        return None, None


# -----------------------------
# Add Author
# -----------------------------
def add_author(conn, cursor):
    """Add a new author to the database."""
    msg = "Enter author details"
    title = "Add Author"
    fields = ["Author Name", "Country (Optional)"]
    values = eg.multenterbox(msg, title, fields)

    if not values:
        return

    Author_Name, Country = [v.strip() for v in values]

    if not Author_Name:
        eg.msgbox("Author name is required.", "Input Error")
        return

    try:
        cursor.execute(
            "INSERT INTO Authors (Author_Name, Country) VALUES (?, ?)",
            (Author_Name, Country or None)
        )
        conn.commit()
        eg.msgbox(f"Author '{Author_Name}' added successfully!", "Success")
    except sqlite3.Error as e:
        eg.exceptionbox(f"Failed to add author: {e}", "Database Error")


# -----------------------------
# Add Book
# -----------------------------
def add_book(conn, cursor):
    """Add a new book linked to an existing author."""
    cursor.execute("SELECT Author_ID, Author_Name FROM Authors")
    authors = cursor.fetchall()

    if not authors:
        eg.msgbox("No authors available. Please add an author first.", "Missing Author")
        return

    author_names = [a[1] for a in authors]

    # Handle different author list sizes safely
    if len(author_names) == 1:
        author_choice = author_names[0]
        eg.msgbox(f"Only one author found: '{author_choice}' will be assigned.", "Author Selected")
    else:
        author_choice = eg.choicebox("Select the author of this book:", "Select Author", author_names)
        if not author_choice:
            return

    author_id = next(a[0] for a in authors if a[1] == author_choice)

    msg = "Enter book details"
    title = "Add Book"
    fields = ["Title", "Genre (Optional)", "Date Published (DD/MM/YYYY)", "Pages (Optional)"]
    values = eg.multenterbox(msg, title, fields)

    if not values:
        return

    Title, Genre, Date_Published, Pages = [v.strip() for v in values]

    if not Title:
        eg.msgbox("Title is required.", "Input Error")
        return

    # Validate and format date
    if Date_Published:
        try:
            parsed_date = datetime.strptime(Date_Published, "%d/%m/%Y")
            Date_Published = parsed_date.strftime("%d/%m/%Y")
        except ValueError:
            eg.msgbox("Please enter a valid date in DD/MM/YYYY format.", "Input Error")
            return
    else:
        Date_Published = None

    # Validate pages
    if Pages and not Pages.isdigit():
        eg.msgbox("Pages must be a number.", "Input Error")
        return

    try:
        cursor.execute("""
            INSERT INTO Library_database (Title, Genre, Date_Published, Pages, Author_ID)
            VALUES (?, ?, ?, ?, ?)
        """, (Title, Genre or None, Date_Published, int(Pages) if Pages else None, author_id))
        conn.commit()
        eg.msgbox(f"Book '{Title}' added successfully!", "Success")
    except sqlite3.Error as e:
        eg.exceptionbox(f"Failed to add book: {e}", "Database Error")


# -----------------------------
# Show Books
# -----------------------------
def show_books(cursor):
    """Display all books in a scrollable window."""
    try:
        cursor.execute("""
            SELECT L.Title, L.Genre, L.Date_Published, L.Pages, A.Author_Name
            FROM Library_database L
            LEFT JOIN Authors A ON L.Author_ID = A.Author_ID
            ORDER BY L.Title
        """)
        rows = cursor.fetchall()

        if not rows:
            eg.msgbox("No books found in the library.", "Book List")
            return

        display_text = f"{'Title':<35}{'Genre':<20}{'Date Published':<15}{'Pages':<8}{'Author':<30}\n"
        display_text += "=" * 110 + "\n"

        for title, genre, date, pages, author in rows:
            display_text += f"{title:<35}{(genre or ''):<20}{(date or ''):<15}{str(pages or ''):<8}{(author or ''):<30}\n"

        eg.codebox("Library Books", "Book List", display_text)

    except sqlite3.Error as e:
        eg.exceptionbox(f"Failed to retrieve books: {e}", "Database Error")


# -----------------------------
# Main Program
# -----------------------------
if __name__ == "__main__":
    conn, cursor = setup_database()
    if not conn:
        exit()

    if os.path.exists("library_database.db"):
        eg.msgbox("Library database is ready to use.", "Database Status")
    else:
        eg.msgbox("New database created.", "Database Status")

    while True:
        choice = eg.buttonbox(
            "What would you like to do?",
            "Library Management Menu",
            ["Add Author", "Add Book", "View Books", "Exit"]
        )

        if choice == "Add Author":
            add_author(conn, cursor)
        elif choice == "Add Book":
            add_book(conn, cursor)
        elif choice == "View Books":
            show_books(cursor)
        elif choice in ("Exit", None):
            break

    conn.close()
    eg.msgbox("Goodbye!", "Exit Program")
