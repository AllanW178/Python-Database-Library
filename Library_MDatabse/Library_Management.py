# we need to import easygui, sqlite3, and os in order to make the program works (three modules).
import easygui as eg
import sqlite3
import os


# Database setup here
def setup_database():
    """
    Sets up the connection to our library database. If it doesn't exist yet,
    it creates the database file and the necessary table for our books.
    This is the first thing we do to make sure everything is ready.
    """
    try:
        # Tries to connect to our 'Library_Database.db' file.
        # If the file isn't there, Python just creates it for us.
        conn = sqlite3.connect('Library_Database.db')
        cursor = conn.cursor()

        # This command creates the 'Library_Database' table if it's not already there.
        # Think of this table as our digital bookshelf. It has columns for book details.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Library_Database (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Author TEXT NOT NULL,
                Title TEXT NOT NULL,
                Genre TEXT,
                Date_Published TEXT,
                Pages INTEGER
            )
        ''')

        # Saves all the changes we just made (like creating the table).
        conn.commit()
        return conn, cursor

    except sqlite3.Error as e:
        # Uh oh, something went wrong with the database connection.
        # We'll pop up a friendly error message to the user.
        eg.exceptionbox(msg=f"A database error occurred: {e}", title="Database Error")
        return None, None


# Add Book Function 
def add_book(conn, cursor):
    """
    Guides the user through adding a new book to the database.
    We'll ask for details, check that they make sense, and then
    store the book on our digital shelf.
    """
    msg = "Enter new book information"
    title = "Add Book"
    fieldNames = ["Author", "Title", "Genre (Optional)", "Pages (Optional)"]
    # Uses a nice little pop-up window to get the book's basic info.
    fieldValues = eg.multenterbox(msg, title, fieldNames)

    if fieldValues is None:
        return  # Looks like the user clicked "Cancel," so we'll stop here.
    Author, Title, Genre, Pages = fieldValues

    # Quick check to make sure the user didn't forget the author or title.
    # We can't have a book without those!
    if not Author or not Title:
        eg.msgbox("Author and Title are required.", "Input Error")
        return

    # Get Published Date 
    msg = "Enter Date Published"
    title = "Date Published"
    fieldNames = ["Day (DD)", "Month (MM)", "Year (YYYY)"]
    # Now, we'll get the publication date separately.
    dateValues = eg.multenterbox(msg, title, fieldNames)
    if dateValues is None:
        return # The user canceled again.
    Day, Month, Year = dateValues

    # Let's make sure the date entered is actually a set of numbers.
    if not (Day.isdigit() and Month.isdigit() and Year.isdigit()):
        eg.msgbox("Day, Month, and Year must be numbers.", "Input Error")
        return

    try:
        # Converts our text date into actual numbers we can use.
        Day, Month, Year = int(Day), int(Month), int(Year)
        # Does a quick sanity check to see if the date is valid.
        if not (1 <= Day <= 31 and 1 <= Month <= 12 and 1000 <= Year <= 9999):
            eg.msgbox("Please enter a valid date (DD/MM/YYYY).", "Input Error")
            return
    except ValueError:
        # Oops, something wasn't a number. Let the user know.
        eg.msgbox("Invalid numbers entered for date.", "Input Error")
        return

    # Formats the date into a clean string, like '09/10/2025'.
    Date_Published = f"{Day:02d}/{Month:02d}/{Year}"

    # Now, let's check the page count. It's optional, but if they enter something,
    # it better be a number!
    if Pages and not Pages.isdigit():
        eg.msgbox("Pages must be a number.", "Input Error")
        return

    try:
        # Adds the new book to our 'bookshelf' (the database table).
        # We use a special `?` syntax to keep things safe from bad data.
        cursor.execute('''
            INSERT INTO Library_Database (Author, Title, Genre, Date_Published, Pages)
            VALUES (?, ?, ?, ?, ?)
        ''', (Author, Title, Genre, Date_Published, Pages if Pages else None))
        conn.commit() # Saves the new book for good.
        eg.msgbox(f"Book '{Title}' added successfully!", "Success")

    except sqlite3.Error as e:
        # A problem occurred while trying to save the book.
        # We'll show an error pop-up with the details.
        eg.exceptionbox(msg=f"Failed to add book: {e}", title="Database Error")


# Show Books Function 
def show_books(cursor):
    """
    Pulls all the books from our database and displays them in a neat, easy-to-read list.
    It's like looking at the contents of our whole library at once.
    """
    try:
        # Grabs all the book information from our table.
        cursor.execute("SELECT Author, Title, Genre, Date_Published, Pages FROM Library_Database")
        rows = cursor.fetchall()

        if not rows:
            # If the database is empty, we'll let the user know.
            eg.msgbox("No books found in the database.", "Book List")
            return

        # Sets up the heading for our list, making it look clean and organized.
        display_text = f"{'Author':<30}{'Title':<35}{'Genre':<35}{'Date Published':<25}{'Pages':<10}\n"
        display_text += "=" * 150 + "\n"

        # Loops through each book and adds its details to our display text.
        for Author, Title, Genre, Date_Published, Pages in rows:
            display_text += f"{Author:<30}{Title:<35}{Genre or '':<35}{Date_Published or '':<25}{str(Pages or ''):<10}\n"

        # Displays the entire list of books in a special scrollable text box.
        eg.codebox("All Books", "Book List", display_text)

    except sqlite3.Error as e:
        # Something went wrong while trying to get the book list.
        eg.exceptionbox(msg=f"Failed to retrieve books: {e}", title="Database Error")


# Main Program
if __name__ == "__main__":
    # The program starts here. First, we get our database ready to go.
    conn, cursor = setup_database()
    if not conn:
        exit() # If we can't connect, there's no point in going on.

    # Tells the user if we just created a new library file or found an existing one.
    if os.path.exists("Library_Database.db"):
        eg.msgbox("The Library Database file is found and it is ready to use", "Database Status")
    else:
        eg.msgbox("New database created.", "Database Status")

    while True:
        # Shows the main menu with options for what the user wants to do.
        choice = eg.buttonbox(
            "What would you like to do?",
            "Library Menu",
            choices=["Add Book", "Check Books", "Exit"]
        )

        # Responds based on which button the user clicks.
        if choice == "Add Book":
            add_book(conn, cursor)
        elif choice == "Check Books":
            show_books(cursor)
        elif choice == "Exit" or choice is None:
            break # Time to say goodbye and close the program.

    # Once the loop is over, we close the connection to our database.
    conn.close()
    eg.msgbox("Goodbye!", "Exiting Program")



