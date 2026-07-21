"""
book.py
-------
Book catalog management: add, update, delete and search books.
Fields: Book ID, Title, Author, Publisher, Category, ISBN,
Total Copies, Available Copies.
"""

import tkinter as tk
from tkinter import messagebox
from mysql.connector import Error

import config
import theme

COLUMNS = (
    "book_id", "title", "author", "publisher", "category",
    "isbn", "total_copies", "available_copies",
)
HEADINGS = (
    "Book ID", "Title", "Author", "Publisher", "Category",
    "ISBN", "Total Copies", "Available",
)


class BookWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title(f"{config.APP_NAME} - Manage Books")
        self.geometry("1100x680")
        self.minsize(980, 600)
        self.configure(bg=theme.BG_APP)
        theme.apply_theme(self)

        self.selected_book_id = None

        self.vars = {col: tk.StringVar() for col in COLUMNS}
        self.var_search = tk.StringVar()

        self._build_ui()
        self.load_books()

    # ------------------------------------------------------------
    def _build_ui(self):
        header = theme.make_header(self, "Manage Books", "Add, update, delete and search the catalog")
        header.pack(fill="x", padx=24, pady=(20, 10))

        # ---- form card ----
        form_outer, form = theme.make_card(self)
        form_outer.pack(fill="x", padx=24, pady=(0, 12))

        grid = tk.Frame(form, bg=theme.BG_CARD)
        grid.pack(fill="x", padx=20, pady=16)

        fields = [
            ("Book ID", "book_id"),
            ("Title", "title"),
            ("Author", "author"),
            ("Publisher", "publisher"),
            ("Category", "category"),
            ("ISBN", "isbn"),
            ("Total Copies", "total_copies"),
            ("Available Copies", "available_copies"),
        ]

        for i, (label, key) in enumerate(fields):
            r, c = divmod(i, 4)
            cell = tk.Frame(grid, bg=theme.BG_CARD)
            cell.grid(row=r, column=c, padx=10, pady=8, sticky="w")
            tk.Label(
                cell, text=label, font=theme.FONT_BODY_BOLD, bg=theme.BG_CARD, fg=theme.TEXT_DARK
            ).pack(anchor="w")
            entry = theme.make_entry(cell, self.vars[key], width=20)
            entry.pack(anchor="w", pady=(2, 0))
            if key == "book_id":
                self.entry_book_id = entry

        # ---- action buttons ----
        btns = tk.Frame(form, bg=theme.BG_CARD)
        btns.pack(fill="x", padx=20, pady=(0, 16))
        theme.StyledButton(btns, text="Add Book", kind="success", command=self.add_book).pack(
            side="left", padx=(0, 8)
        )
        theme.StyledButton(btns, text="Update", kind="info", command=self.update_book).pack(
            side="left", padx=8
        )
        theme.StyledButton(btns, text="Delete", kind="danger", command=self.delete_book).pack(
            side="left", padx=8
        )
        theme.StyledButton(btns, text="Clear Form", kind="muted", command=self.clear_form).pack(
            side="left", padx=8
        )

        # ---- search bar ----
        search_frame = tk.Frame(self, bg=theme.BG_APP)
        search_frame.pack(fill="x", padx=24, pady=(4, 8))
        tk.Label(
            search_frame, text="Search:", font=theme.FONT_BODY_BOLD, bg=theme.BG_APP
        ).pack(side="left", padx=(0, 8))
        search_entry = theme.make_entry(search_frame, self.var_search, width=40)
        search_entry.pack(side="left")
        search_entry.bind("<KeyRelease>", lambda e: self.load_books())
        theme.StyledButton(
            search_frame, text="Refresh", kind="muted", width=10, command=self.load_books
        ).pack(side="left", padx=8)

        # ---- table ----
        table_outer = tk.Frame(self, bg=theme.BG_APP)
        table_outer.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        self.tree = theme.styled_treeview(table_outer, COLUMNS, height=16)
        
        # Base setup for all columns
        for col, heading in zip(COLUMNS, HEADINGS):
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=100, anchor="center")
            
        # Specific custom column alignments and spacing adjustments
        self.tree.column("title", width=200, anchor="w")
        self.tree.column("author", width=140, anchor="w")
        self.tree.column("publisher", width=140, anchor="w")
        self.tree.column("category", width=120, anchor="w")
        
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

    # ------------------------------------------------------------
    def clear_form(self):
        for v in self.vars.values():
            v.set("")
        self.selected_book_id = None
        self.entry_book_id.config(state="normal")

    def on_row_select(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        for key, value in zip(COLUMNS, values):
            self.vars[key].set(value)
        self.selected_book_id = values[0]
        self.entry_book_id.config(state="normal")

    # ------------------------------------------------------------
    def _validate_form(self, for_update=False):
        book_id = self.vars["book_id"].get().strip()
        title = self.vars["title"].get().strip()
        author = self.vars["author"].get().strip()
        total = self.vars["total_copies"].get().strip()
        available = self.vars["available_copies"].get().strip()

        if not book_id or not title or not author:
            messagebox.showerror("Validation Error", "Book ID, Title and Author are required.")
            return None
        if not total.isdigit() or int(total) < 0:
            messagebox.showerror("Validation Error", "Total Copies must be a non-negative number.")
            return None
        if not available.isdigit() or int(available) < 0:
            messagebox.showerror(
                "Validation Error", "Available Copies must be a non-negative number."
            )
            return None
        if int(available) > int(total):
            messagebox.showerror(
                "Validation Error", "Available Copies cannot exceed Total Copies."
            )
            return None

        return {
            "book_id": book_id,
            "title": title,
            "author": author,
            "publisher": self.vars["publisher"].get().strip(),
            "category": self.vars["category"].get().strip(),
            "isbn": self.vars["isbn"].get().strip(),
            "total_copies": int(total),
            "available_copies": int(available),
        }

    # ------------------------------------------------------------
    def add_book(self):
        data = self._validate_form()
        if not data:
            return
        try:
            conn = config.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT book_id FROM books WHERE book_id = %s", (data["book_id"],))
            if cursor.fetchone():
                messagebox.showerror("Duplicate Book ID", "A book with this ID already exists.")
                cursor.close()
                conn.close()
                return

            cursor.execute(
                """INSERT INTO books
                   (book_id, title, author, publisher, category, isbn, total_copies, available_copies)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    data["book_id"], data["title"], data["author"], data["publisher"],
                    data["category"], data["isbn"], data["total_copies"], data["available_copies"],
                ),
            )
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Success", "Book added successfully.")
            self.clear_form()
            self.load_books()
        except Error as e:
            messagebox.showerror("Database Error", f"Could not add book:\n{e}")

    def update_book(self):
        if not self.selected_book_id:
            messagebox.showwarning("No Selection", "Select a book from the table to update.")
            return
        data = self._validate_form(for_update=True)
        if not data:
            return
        try:
            conn = config.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE books SET title=%s, author=%s, publisher=%s, category=%s,
                   isbn=%s, total_copies=%s, available_copies=%s WHERE book_id=%s""",
                (
                    data["title"], data["author"], data["publisher"], data["category"],
                    data["isbn"], data["total_copies"], data["available_copies"],
                    self.selected_book_id,
                ),
            )
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Success", "Book updated successfully.")
            self.clear_form()
            self.load_books()
        except Error as e:
            messagebox.showerror("Database Error", f"Could not update book:\n{e}")

    def delete_book(self):
        if not self.selected_book_id:
            messagebox.showwarning("No Selection", "Select a book from the table to delete.")
            return
        if not messagebox.askyesno("Confirm Delete", "Delete this book? This cannot be undone."):
            return
        try:
            conn = config.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM books WHERE book_id = %s", (self.selected_book_id,))
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Success", "Book deleted successfully.")
            self.clear_form()
            self.load_books()
        except Error as e:
            messagebox.showerror(
                "Database Error",
                f"Could not delete book (it may have issue history linked to it):\n{e}",
            )

    # ------------------------------------------------------------
    def load_books(self):
        search = self.var_search.get().strip()
        try:
            conn = config.get_connection()
            cursor = conn.cursor()
            if search:
                like = f"%{search}%"
                cursor.execute(
                    """SELECT book_id, title, author, publisher, category, isbn,
                              total_copies, available_copies
                       FROM books
                       WHERE book_id LIKE %s OR title LIKE %s OR author LIKE %s
                          OR category LIKE %s OR isbn LIKE %s
                       ORDER BY title""",
                    (like, like, like, like, like),
                )
            else:
                cursor.execute(
                    """SELECT book_id, title, author, publisher, category, isbn,
                              total_copies, available_copies
                       FROM books ORDER BY title"""
                )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            theme.fill_treeview(self.tree, rows)
        except Error as e:
            messagebox.showerror("Database Error", f"Could not load books:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    theme.apply_theme(root)
    BookWindow(root)
    root.mainloop()