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

    if Date_Published:
        try:
            parsed_date = datetime.strptime(Date_Published, "%d/%m/%Y")
            Date_Published = parsed_date.strftime("%d/%m/%Y")
        except ValueError:
            eg.msgbox("Please enter a valid date in DD/MM/YYYY format.", "Input Error")
            return
    else:
        Date_Published = None

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
# Add Borrower
# -----------------------------
def add_borrower(conn, cursor):
    """Add a new borrower."""
    msg = "Enter borrower details"
    title = "Add Borrower"
    fields = ["Borrower Name", "Email (Optional)", "Phone (Optional)"]
    values = eg.multenterbox(msg, title, fields)

    if not values:
        return

    Borrower_Name, Email, Phone = [v.strip() for v in values]

    if not Borrower_Name:
        eg.msgbox("Borrower name is required.", "Input Error")
        return

    try:
        cursor.execute(
            "INSERT INTO Borrowers (Borrower_Name, Email, Phone) VALUES (?, ?, ?)",
            (Borrower_Name, Email or None, Phone or None)
        )
        conn.commit()
        eg.msgbox(f"Borrower '{Borrower_Name}' added successfully!", "Success")
    except sqlite3.Error as e:
        eg.exceptionbox(f"Failed to add borrower: {e}", "Database Error")


# -----------------------------
# Record Loan
# -----------------------------
def record_loan(conn, cursor):
    """Record a book loan to a borrower."""
    # Get available books
    cursor.execute("SELECT Book_ID, Title FROM Library_database")
    books = cursor.fetchall()
    if not books:
        eg.msgbox("No books available. Please add a book first.", "Missing Book")
        return

    # Get borrowers
    cursor.execute("SELECT Borrower_ID, Borrower_Name FROM Borrowers")
    borrowers = cursor.fetchall()
    if not borrowers:
        eg.msgbox("No borrowers found. Please add a borrower first.", "Missing Borrower")
        return

    book_titles = [b[1] for b in books]
    borrower_names = [b[1] for b in borrowers]

    book_choice = eg.choicebox("Select a book to loan:", "Select Book", book_titles)
    if not book_choice:
        return
    borrower_choice = eg.choicebox("Select borrower:", "Select Borrower", borrower_names)
    if not borrower_choice:
        return

    book_id = next(b[0] for b in books if b[1] == book_choice)
    borrower_id = next(b[0] for b in borrowers if b[1] == borrower_choice)
    loan_date = datetime.now().strftime("%d/%m/%Y")

    try:
        cursor.execute("""
            INSERT INTO Loans (Book_ID, Borrower_ID, Loan_Date)
            VALUES (?, ?, ?)
        """, (book_id, borrower_id, loan_date))
        conn.commit()
        eg.msgbox(f"Book '{book_choice}' loaned to '{borrower_choice}' on {loan_date}.", "Success")
    except sqlite3.Error as e:
        eg.exceptionbox(f"Failed to record loan: {e}", "Database Error")


# -----------------------------
# Mark Book as Returned
# -----------------------------
def return_book(conn, cursor):
    """Mark a book as returned."""
    cursor.execute("""
        SELECT L.Loan_ID, B.Title, R.Borrower_Name, L.Loan_Date
        FROM Loans L
        JOIN Library_database B ON L.Book_ID = B.Book_ID
        JOIN Borrowers R ON L.Borrower_ID = R.Borrower_ID
        WHERE L.Return_Date IS NULL
    """)
    loans = cursor.fetchall()

    if not loans:
        eg.msgbox("No active loans found.", "Return Book")
        return

    loan_list = [f"{b} (Borrowed by {r} on {d})" for _, b, r, d in loans]
    choice = eg.choicebox("Select a loan to mark as returned:", "Return Book", loan_list)
    if not choice:
        return

    loan_id = loans[loan_list.index(choice)][0]
    return_date = datetime.now().strftime("%d/%m/%Y")

    try:
        cursor.execute("UPDATE Loans SET Return_Date = ? WHERE Loan_ID = ?", (return_date, loan_id))
        conn.commit()
        eg.msgbox(f"Book marked as returned on {return_date}.", "Success")
    except sqlite3.Error as e:
        eg.exceptionbox(f"Failed to mark book as returned: {e}", "Database Error")


# -----------------------------
# Show All Loans
# -----------------------------
def show_loans(cursor):
    """Display all loan records."""
    try:
        cursor.execute("""
            SELECT L.Loan_ID, B.Title, R.Borrower_Name, L.Loan_Date, L.Return_Date
            FROM Loans L
            JOIN Library_database B ON L.Book_ID = B.Book_ID
            JOIN Borrowers R ON L.Borrower_ID = R.Borrower_ID
            ORDER BY L.Loan_Date DESC
        """)
        rows = cursor.fetchall()

        if not rows:
            eg.msgbox("No loan records found.", "Loan List")
            return

        display_text = f"{'Loan ID':<8}{'Book Title':<30}{'Borrower':<25}{'Loan Date':<15}{'Return Date':<15}\n"
        display_text += "=" * 95 + "\n"

        for loan_id, title, borrower, loan_date, return_date in rows:
            display_text += f"{loan_id:<8}{title:<30}{borrower:<25}{loan_date:<15}{(return_date or 'Not Returned'):<15}\n"

        eg.codebox("Library Loans", "Loan Records", display_text)

    except sqlite3.Error as e:
        eg.exceptionbox(f"Failed to retrieve loans: {e}", "Database Error")


# -----------------------------
# Show Books
# -----------------------------
def show_books(cursor):
    """Display all books."""
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
            [
                "Add Author",
                "Add Book",
                "Add Borrower",
                "Record Loan",
                "Return Book",
                "View Books",
                "View Loans",
                "Exit"
            ]
        )

        if choice == "Add Author":
            add_author(conn, cursor)
        elif choice == "Add Book":
            add_book(conn, cursor)
        elif choice == "Add Borrower":
            add_borrower(conn, cursor)
        elif choice == "Record Loan":
            record_loan(conn, cursor)
        elif choice == "Return Book":
            return_book(conn, cursor)
        elif choice == "View Books":
            show_books(cursor)
        elif choice == "View Loans":
            show_loans(cursor)
        elif choice in ("Exit", None):
            break

    conn.close()
    eg.msgbox("Goodbye!", "Exit Program")
