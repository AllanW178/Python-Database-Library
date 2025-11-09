import sqlite3
import easygui as eg
import re
import datetime

# ==========================================================
# Helper Functions (validation)
# ==========================================================

def get_valid_date(prompt, title="Enter Date"):
    """Ask user for a date in YYYY-MM-DD format and validate it."""
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    while True:
        date_str = eg.enterbox(f"{prompt}\n(Format: YYYY-MM-DD)", title)
        if date_str is None:
            return None
        if not pattern.match(date_str):
            eg.msgbox("Invalid date format. Please use YYYY-MM-DD (e.g. 2025-11-09).", "Invalid Input")
            continue
        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError:
            eg.msgbox("Invalid date. Please enter a real calendar date.", "Invalid Date")

def get_valid_int(prompt, title="Enter Number"):
    """Ask for a positive integer only."""
    while True:
        val = eg.enterbox(prompt, title)
        if val is None:
            return None
        if val.strip() == "":
            eg.msgbox("This field cannot be empty.", "Invalid Number")
            continue
        if val.isdigit():
            return int(val)
        eg.msgbox("Please enter a valid whole number (no decimals or letters).", "Invalid Number")

def non_empty_multenterbox(msg, title, fields):
    """
    Show a multenterbox and enforce that no field is left empty.
    Returns a list of stripped values or None if cancelled.
    """
    while True:
        values = eg.multenterbox(msg, title, fields)
        if values is None:
            return None
        # strip and validate
        values = [v.strip() if v is not None else "" for v in values]
        empty_indexes = [i for i, v in enumerate(values) if v == ""]
        if empty_indexes:
            eg.msgbox("All fields are required — please fill in every field.", "Missing Data")
            continue
        return values

# ==========================================================
# Database Setup
# ==========================================================

def connect_db():
    conn = sqlite3.connect("library_database.db")
    cursor = conn.cursor()

    # Verify all tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    existing = [r[0] for r in cursor.fetchall()]

    # Create tables if missing
    if "Authors" not in existing:
        cursor.execute("""
            CREATE TABLE Authors (
                Author_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Author_Name TEXT,
                Country TEXT
            )
        """)

    if "Library_database" not in existing:
        cursor.execute("""
            CREATE TABLE Library_database (
                Book_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Title TEXT(50),
                Genre TEXT(30),
                Date_Published TEXT,
                Pages INTEGER,
                Author_ID INTEGER,
                FOREIGN KEY (Author_ID) REFERENCES Authors(Author_ID)
            )
        """)

    if "Borrowers" not in existing:
        cursor.execute("""
            CREATE TABLE Borrowers (
                Borrower_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Borrower_Name TEXT,
                Email TEXT,
                Phone TEXT
            )
        """)

    if "Loans" not in existing:
        cursor.execute("""
            CREATE TABLE Loans (
                Loan_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Book_ID INTEGER,
                Borrower_ID INTEGER,
                Loan_Date TEXT,
                Return_Date TEXT,
                FOREIGN KEY (Book_ID) REFERENCES Library_database(Book_ID),
                FOREIGN KEY (Borrower_ID) REFERENCES Borrowers(Borrower_ID)
            )
        """)

    if "Book_Locations" not in existing:
        cursor.execute("""
            CREATE TABLE Book_Locations (
                Location_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Book_ID INTEGER,
                Location_Name TEXT,
                Copies INTEGER DEFAULT 1,
                FOREIGN KEY (Book_ID) REFERENCES Library_database(Book_ID)
            )
        """)

    conn.commit()
    return conn, cursor

# ==========================================================
# Add / View Functions
# ==========================================================

def add_author(conn, cursor):
    msg = "Enter author details:"
    fields = ["Author Name", "Country"]
    values = non_empty_multenterbox(msg, "Add Author", fields)
    if not values:
        return
    name, country = values
    cursor.execute("INSERT INTO Authors (Author_Name, Country) VALUES (?, ?)", (name, country))
    conn.commit()
    eg.msgbox(f"Author '{name}' added successfully.", "Success")

def view_authors(cursor):
    cursor.execute("SELECT Author_Name, Country FROM Authors")
    rows = cursor.fetchall()
    if not rows:
        eg.msgbox("No authors found.", "Authors")
        return
    display = f"{'Author Name':<30}{'Country':<20}\n" + "="*50 + "\n"
    for name, country in rows:
        display += f"{name:<30}{(country or ''):<20}\n"
    eg.codebox("Authors", "Author List", display)

def add_book(conn, cursor):
    cursor.execute("SELECT Author_ID, Author_Name FROM Authors")
    authors = cursor.fetchall()
    if not authors:
        eg.msgbox("No authors found. Add one first.", "Missing Data")
        return

    author_names = [a[1] for a in authors]
    if len(author_names) == 1:
        author_choice = author_names[0]
        eg.msgbox(f"Only one author found — selected: {author_choice}", "Author Selected")
    else:
        author_choice = eg.choicebox("Select an author:", "Select Author", author_names)
        if author_choice is None:
            return
    author_id = next(a[0] for a in authors if a[1] == author_choice)

    msg = "Enter book details:"
    fields = ["Title", "Genre", "Date Published (YYYY-MM-DD)", "Pages"]
    values = non_empty_multenterbox(msg, "Add Book", fields)
    if not values:
        return

    title, genre, date_published, pages = values

    # Validate date
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    if not pattern.match(date_published):
        eg.msgbox("Invalid date format. Use YYYY-MM-DD.", "Invalid Input")
        return

    try:
        datetime.datetime.strptime(date_published, "%Y-%m-%d")
    except ValueError:
        eg.msgbox("Invalid date. Please enter a real calendar date.", "Invalid Date")
        return

    if not pages.isdigit():
        eg.msgbox("Pages must be a positive integer.", "Invalid Input")
        return

    cursor.execute("""
        INSERT INTO Library_database (Title, Genre, Date_Published, Pages, Author_ID)
        VALUES (?, ?, ?, ?, ?)
    """, (title, genre, date_published, int(pages), author_id))
    conn.commit()
    eg.msgbox(f"Book '{title}' added successfully.", "Success")

def view_books(cursor):
    cursor.execute("""
        SELECT L.Book_ID, L.Title, L.Genre, L.Date_Published, L.Pages, A.Author_Name
        FROM Library_database L
        LEFT JOIN Authors A ON L.Author_ID = A.Author_ID
        ORDER BY L.Title COLLATE NOCASE
    """)
    rows = cursor.fetchall()
    if not rows:
        eg.msgbox("No books found.", "Books")
        return
    display = f"{'ID':<4}{'Title':<30}{'Genre':<12}{'Published':<12}{'Pages':<7}{'Author':<20}\n" + "="*95 + "\n"
    for bid, t, g, d, p, a in rows:
        display += f"{(bid or ''):<4}{(t or ''):<30}{(g or ''):<12}{(d or ''):<12}{(p or ''):<7}{(a or ''):<20}\n"
    eg.codebox("Books", "Book List", display)

def add_borrower(conn, cursor):
    msg = "Enter borrower details:"
    fields = ["Borrower Name", "Email", "Phone"]
    values = non_empty_multenterbox(msg, "Add Borrower", fields)
    if not values:
        return
    name, email, phone = values

    if "@" not in email or "." not in email:
        if not eg.ynbox("Email looks unusual. Do you want to continue anyway?", "Email Check"):
            return

    cursor.execute("INSERT INTO Borrowers (Borrower_Name, Email, Phone) VALUES (?, ?, ?)", (name, email, phone))
    conn.commit()
    eg.msgbox(f"Borrower '{name}' added successfully.", "Success")

def view_borrowers(cursor):
    cursor.execute("SELECT Borrower_ID, Borrower_Name, Email, Phone FROM Borrowers ORDER BY Borrower_Name COLLATE NOCASE")
    rows = cursor.fetchall()
    if not rows:
        eg.msgbox("No borrowers found.", "Borrowers")
        return
    display = f"{'ID':<4}{'Borrower Name':<30}{'Email':<30}{'Phone':<15}\n" + "="*85 + "\n"
    for bid, n, e, p in rows:
        display += f"{(bid or ''):<4}{(n or ''):<30}{(e or ''):<30}{(p or ''):<15}\n"
    eg.codebox("Borrowers", "Borrower List", display)

def add_book_location(conn, cursor):
    cursor.execute("SELECT Book_ID, Title FROM Library_database ORDER BY Title COLLATE NOCASE")
    books = cursor.fetchall()
    if not books:
        eg.msgbox("No books found. Add a book first.", "Missing Data")
        return

    book_titles = [b[1] for b in books]
    if len(book_titles) == 1:
        book_choice = book_titles[0]
        eg.msgbox(f"Only one book found — automatically selected:\n\n{book_choice}", "Info")
    else:
        book_choice = eg.choicebox("Select a book:", "Select Book", book_titles)
        if book_choice is None:
            return

    book_id = next(b[0] for b in books if b[1] == book_choice)

    while True:
        location = eg.enterbox("Enter location name:", "Book Location")
        if location is None:
            return
        location = location.strip()
        if location == "":
            eg.msgbox("Location cannot be empty.", "Invalid Input")
            continue
        break

    copies = get_valid_int("Enter number of copies:")
    if copies is None:
        return

    cursor.execute("""
        INSERT INTO Book_Locations (Book_ID, Location_Name, Copies)
        VALUES (?, ?, ?)
    """, (book_id, location, copies))
    conn.commit()
    eg.msgbox(f"Book '{book_choice}' stored at '{location}' ({copies} copies).", "Success")

def view_book_locations(cursor):
    cursor.execute("""
        SELECT L.Title, BL.Location_Name, BL.Copies
        FROM Book_Locations BL
        LEFT JOIN Library_database L ON BL.Book_ID = L.Book_ID
        ORDER BY L.Title COLLATE NOCASE, BL.Location_Name COLLATE NOCASE
    """)
    rows = cursor.fetchall()
    if not rows:
        eg.msgbox("No book locations found.", "Book Locations")
        return

    display = f"{'Book Title':<35}{'Location':<25}{'Copies':<7}\n" + "="*70 + "\n"
    for title, location, copies in rows:
        display += f"{(title or ''):<35}{(location or ''):<25}{(copies or 0):<7}\n"

    eg.codebox("Book Locations", "Book Locations List", display)

def add_loan(conn, cursor):
    cursor.execute("SELECT Book_ID, Title FROM Library_database ORDER BY Title COLLATE NOCASE")
    books = cursor.fetchall()
    if not books:
        eg.msgbox("No books found. Add a book first.", "Missing Data")
        return

    book_titles = [b[1] for b in books]
    if len(book_titles) == 1:
        book_choice = book_titles[0]
        eg.msgbox(f"Only one book found — automatically selected:\n\n{book_choice}", "Info")
    else:
        book_choice = eg.choicebox("Select a book:", "Select Book", book_titles)
        if book_choice is None:
            return
    book_id = next(b[0] for b in books if b[1] == book_choice)

    cursor.execute("SELECT Borrower_ID, Borrower_Name FROM Borrowers ORDER BY Borrower_Name COLLATE NOCASE")
    borrowers = cursor.fetchall()
    if not borrowers:
        eg.msgbox("No borrowers found. Add one first.", "Missing Data")
        return

    borrower_names = [b[1] for b in borrowers]
    if len(borrower_names) == 1:
        borrower_choice = borrower_names[0]
        eg.msgbox(f"Only one borrower found — automatically selected:\n\n{borrower_choice}", "Info")
    else:
        borrower_choice = eg.choicebox("Select a borrower:", "Select Borrower", borrower_names)
        if borrower_choice is None:
            return
    borrower_id = next(b[0] for b in borrowers if b[1] == borrower_choice)

    loan_date = get_valid_date("Enter Loan Date")
    if loan_date is None:
        return

    return_date = eg.enterbox("Enter Return Date (optional, YYYY-MM-DD):", "Return Date")
    if return_date:
        pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        if not pattern.match(return_date):
            eg.msgbox("Invalid date format. Ignoring return date.", "Invalid Input")
            return_date = None
        else:
            try:
                datetime.datetime.strptime(return_date, "%Y-%m-%d")
            except ValueError:
                eg.msgbox("Invalid return date entered. Ignoring return date.", "Invalid Date")
                return_date = None
    else:
        return_date = None

    cursor.execute("""
        INSERT INTO Loans (Book_ID, Borrower_ID, Loan_Date, Return_Date)
        VALUES (?, ?, ?, ?)
    """, (book_id, borrower_id, loan_date, return_date))
    conn.commit()
    eg.msgbox(f"Loan recorded: '{book_choice}' to '{borrower_choice}'.", "Success")

def view_loans(cursor):
    cursor.execute("""
        SELECT L.Loan_ID,
               B.Title,
               BR.Borrower_Name,
               L.Loan_Date,
               L.Return_Date
        FROM Loans L
        LEFT JOIN Library_database B ON L.Book_ID = B.Book_ID
        LEFT JOIN Borrowers BR ON L.Borrower_ID = BR.Borrower_ID
        ORDER BY L.Loan_Date DESC
    """)
    rows = cursor.fetchall()
    if not rows:
        eg.msgbox("No loans found.", "Loans")
        return
    display = f"{'Loan ID':<8}{'Book Title':<35}{'Borrower':<25}{'Loan Date':<12}{'Return Date':<12}\n" + "="*100 + "\n"
    for lid, title, borrower, loan_d, return_d in rows:
        display += f"{(lid or ''):<8}{(title or ''):<35}{(borrower or ''):<25}{(loan_d or ''):<12}{(return_d or ''):<12}\n"
    eg.codebox("Loans", "Loan List", display)

# ==========================================================
# Main Menu
# ==========================================================

def main():
    conn, cursor = connect_db()

    while True:
        choice = eg.buttonbox(
            "Library Database System",
            "Main Menu",
            choices=[
                "Add Author", "View Authors",
                "Add Book", "View Books",
                "Add Borrower", "View Borrowers",
                "Add Book Location", "View Book Locations",
                "Add Loan",
                "View Loans", "Exit"
            ]
        )

        if choice == "Add Author":
            add_author(conn, cursor)
        elif choice == "View Authors":
            view_authors(cursor)
        elif choice == "Add Book":
            add_book(conn, cursor)
        elif choice == "View Books":
            view_books(cursor)
        elif choice == "Add Borrower":
            add_borrower(conn, cursor)
        elif choice == "View Borrowers":
            view_borrowers(cursor)
        elif choice == "Add Book Location":
            add_book_location(conn, cursor)
        elif choice == "View Book Locations":
            view_book_locations(cursor)
        elif choice == "Add Loan":
            add_loan(conn, cursor)
        elif choice == "View Loans":
            view_loans(cursor)
        else:
            conn.close()
            break

if __name__ == "__main__":
    main()
