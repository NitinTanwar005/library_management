"""
issue_return.py
----------------
Circulation desk: issue a book to a member, return a book, and
automatically calculate a fine for late returns. Issuing is blocked
when no copies of the book are available.
"""

import tkinter as tk
from tkinter import messagebox
from datetime import date, timedelta
from mysql.connector import Error

import config
import theme

ISSUED_COLUMNS = (
    "issue_id", "book_id", "title", "member_id", "member_name",
    "issue_date", "due_date", "status",
)
ISSUED_HEADINGS = (
    "Issue ID", "Book ID", "Title", "Member ID", "Member Name",
    "Issue Date", "Due Date", "Status",
)


class IssueReturnWindow(tk.Toplevel):
    def __init__(self, master, on_change=None):
        super().__init__(master)
        self.on_change = on_change  # callback to refresh dashboard stats
        self.title(f"{config.APP_NAME} - Issue / Return")
        self.geometry("1150x700")
        self.minsize(1000, 620)
        self.configure(bg=theme.BG_APP)
        theme.apply_theme(self)

        self.var_book_id = tk.StringVar()
        self.var_member_id = tk.StringVar()
        self.var_return_issue_id = tk.StringVar()
        self.var_search = tk.StringVar()

        self._build_ui()
        self.load_issued()

    # ------------------------------------------------------------
    def _build_ui(self):
        header = theme.make_header(
            self, "Issue / Return Books", "Circulation desk — issue, return and calculate fines"
        )
        header.pack(fill="x", padx=24, pady=(20, 10))

        # ---- two side-by-side cards: Issue | Return ----
        cards_frame = tk.Frame(self, bg=theme.BG_APP)
        cards_frame.pack(fill="x", padx=24, pady=(0, 12))
        cards_frame.grid_columnconfigure(0, weight=1)
        cards_frame.grid_columnconfigure(1, weight=1)

        # Issue card
        issue_outer, issue_card = theme.make_card(cards_frame)
        issue_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        tk.Label(
            issue_card, text="Issue a Book", font=theme.FONT_H3, bg=theme.BG_CARD, fg=theme.TEXT_DARK
        ).pack(anchor="w", padx=18, pady=(14, 8))

        row1 = tk.Frame(issue_card, bg=theme.BG_CARD)
        row1.pack(fill="x", padx=18)
        tk.Label(row1, text="Book ID", font=theme.FONT_BODY_BOLD, bg=theme.BG_CARD).grid(
            row=0, column=0, sticky="w"
        )
        theme.make_entry(row1, self.var_book_id, width=18).grid(row=1, column=0, padx=(0, 12))
        tk.Label(row1, text="Member ID", font=theme.FONT_BODY_BOLD, bg=theme.BG_CARD).grid(
            row=0, column=1, sticky="w"
        )
        theme.make_entry(row1, self.var_member_id, width=18).grid(row=1, column=1)

        tk.Label(
            issue_card,
            text=f"Loan period: {config.LOAN_PERIOD_DAYS} days · Fine: {config.FINE_PER_DAY}/day late",
            font=theme.FONT_SMALL,
            bg=theme.BG_CARD,
            fg=theme.TEXT_MUTED,
        ).pack(anchor="w", padx=18, pady=(10, 4))

        theme.StyledButton(
            issue_card, text="Issue Book", kind="success", command=self.issue_book
        ).pack(anchor="w", padx=18, pady=(6, 16))

        # Return card
        return_outer, return_card = theme.make_card(cards_frame)
        return_outer.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        tk.Label(
            return_card, text="Return a Book", font=theme.FONT_H3, bg=theme.BG_CARD, fg=theme.TEXT_DARK
        ).pack(anchor="w", padx=18, pady=(14, 8))

        row2 = tk.Frame(return_card, bg=theme.BG_CARD)
        row2.pack(fill="x", padx=18)
        tk.Label(row2, text="Issue ID (select row below, or type it)",
                 font=theme.FONT_BODY_BOLD, bg=theme.BG_CARD).grid(row=0, column=0, sticky="w")
        theme.make_entry(row2, self.var_return_issue_id, width=18).grid(row=1, column=0, sticky="w")

        tk.Label(
            return_card,
            text="Fine is calculated automatically if returned after the due date.",
            font=theme.FONT_SMALL,
            bg=theme.BG_CARD,
            fg=theme.TEXT_MUTED,
        ).pack(anchor="w", padx=18, pady=(10, 4))

        theme.StyledButton(
            return_card, text="Return Book", kind="info", command=self.return_book
        ).pack(anchor="w", padx=18, pady=(6, 16))

        # ---- search / filter bar ----
        search_frame = tk.Frame(self, bg=theme.BG_APP)
        search_frame.pack(fill="x", padx=24, pady=(4, 8))
        tk.Label(
            search_frame, text="Search:", font=theme.FONT_BODY_BOLD, bg=theme.BG_APP
        ).pack(side="left", padx=(0, 8))
        search_entry = theme.make_entry(search_frame, self.var_search, width=40)
        search_entry.pack(side="left")
        search_entry.bind("<KeyRelease>", lambda e: self.load_issued())
        theme.StyledButton(
            search_frame, text="Show All", kind="muted", width=10, command=self._show_all
        ).pack(side="left", padx=8)
        theme.StyledButton(
            search_frame, text="Overdue Only", kind="danger", width=12, command=self._show_overdue
        ).pack(side="left", padx=8)

        # ---- table ----
        table_outer = tk.Frame(self, bg=theme.BG_APP)
        table_outer.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        self.tree = theme.styled_treeview(table_outer, ISSUED_COLUMNS, height=13)
        for col, heading in zip(ISSUED_COLUMNS, ISSUED_HEADINGS):
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=110, anchor="center")
        self.tree.column("title", width=200, anchor="w")
        self.tree.column("member_name", width=150, anchor="w")
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

        self._overdue_filter = False

    # ------------------------------------------------------------
    def _on_row_select(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        self.var_return_issue_id.set(values[0])  # issue_id

    def _show_all(self):
        self._overdue_filter = False
        self.load_issued()

    def _show_overdue(self):
        self._overdue_filter = True
        self.load_issued()

    # ------------------------------------------------------------
    def issue_book(self):
        book_id = self.var_book_id.get().strip()
        member_id = self.var_member_id.get().strip()

        if not book_id or not member_id:
            messagebox.showerror("Validation Error", "Book ID and Member ID are required.")
            return

        try:
            conn = config.get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM books WHERE book_id = %s", (book_id,))
            book = cursor.fetchone()
            if not book:
                messagebox.showerror("Not Found", "No book found with that Book ID.")
                cursor.close(); conn.close()
                return

            cursor.execute("SELECT * FROM members WHERE member_id = %s", (member_id,))
            member = cursor.fetchone()
            if not member:
                messagebox.showerror("Not Found", "No member found with that Member ID.")
                cursor.close(); conn.close()
                return

            # --- core business rule: block issuing when no copies available ---
            if book["available_copies"] <= 0:
                messagebox.showerror(
                    "No Copies Available",
                    f'"{book["title"]}" has no available copies right now.',
                )
                cursor.close(); conn.close()
                return

            issue_date = date.today()
            due_date = issue_date + timedelta(days=config.LOAN_PERIOD_DAYS)

            cursor.execute(
                """INSERT INTO issued_books (book_id, member_id, issue_date, due_date, status)
                   VALUES (%s,%s,%s,%s,'Issued')""",
                (book_id, member_id, issue_date, due_date),
            )
            cursor.execute(
                "UPDATE books SET available_copies = available_copies - 1 WHERE book_id = %s",
                (book_id,),
            )
            conn.commit()
            cursor.close()
            conn.close()

            messagebox.showinfo(
                "Book Issued",
                f'"{book["title"]}" issued to {member["name"]}.\nDue back on {due_date}.',
            )
            self.var_book_id.set("")
            self.var_member_id.set("")
            self.load_issued()
            if self.on_change:
                self.on_change()

        except Error as e:
            messagebox.showerror("Database Error", f"Could not issue book:\n{e}")

    # ------------------------------------------------------------
    def return_book(self):
        issue_id = self.var_return_issue_id.get().strip()
        if not issue_id or not issue_id.isdigit():
            messagebox.showerror("Validation Error", "Select or enter a valid Issue ID.")
            return

        try:
            conn = config.get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                "SELECT * FROM issued_books WHERE issue_id = %s", (issue_id,)
            )
            record = cursor.fetchone()
            if not record:
                messagebox.showerror("Not Found", "No issue record found with that Issue ID.")
                cursor.close(); conn.close()
                return
            if record["status"] == "Returned":
                messagebox.showinfo("Already Returned", "This book has already been returned.")
                cursor.close(); conn.close()
                return

            return_date = date.today()
            due_date = record["due_date"]
            fine = self.calculate_fine(due_date, return_date)

            cursor.execute(
                """UPDATE issued_books SET return_date=%s, fine=%s, status='Returned'
                   WHERE issue_id=%s""",
                (return_date, fine, issue_id),
            )
            cursor.execute(
                "UPDATE books SET available_copies = available_copies + 1 WHERE book_id = %s",
                (record["book_id"],),
            )
            conn.commit()
            cursor.close()
            conn.close()

            if fine > 0:
                messagebox.showwarning(
                    "Book Returned",
                    f"Book returned late.\nFine due: {fine:.2f} "
                    f"({(return_date - due_date).days} day(s) overdue).",
                )
            else:
                messagebox.showinfo("Book Returned", "Book returned on time. No fine due.")

            self.var_return_issue_id.set("")
            self.load_issued()
            if self.on_change:
                self.on_change()

        except Error as e:
            messagebox.showerror("Database Error", f"Could not process return:\n{e}")

    # ------------------------------------------------------------
    @staticmethod
    def calculate_fine(due_date, return_date) -> float:
        """Fine = FINE_PER_DAY for every day the book is returned late (0 if on time/early)."""
        overdue_days = (return_date - due_date).days
        if overdue_days > 0:
            return round(overdue_days * config.FINE_PER_DAY, 2)
        return 0.0

    # ------------------------------------------------------------
    def load_issued(self):
        search = self.var_search.get().strip()
        try:
            conn = config.get_connection()
            cursor = conn.cursor()

            base_query = """
                SELECT ib.issue_id, ib.book_id, b.title, ib.member_id, m.name,
                       ib.issue_date, ib.due_date, ib.status
                FROM issued_books ib
                JOIN books b ON ib.book_id = b.book_id
                JOIN members m ON ib.member_id = m.member_id
            """
            conditions = []
            params = []

            if self._overdue_filter:
                conditions.append("ib.status = 'Issued' AND ib.due_date < CURDATE()")

            if search:
                like = f"%{search}%"
                conditions.append(
                    "(ib.book_id LIKE %s OR b.title LIKE %s OR ib.member_id LIKE %s OR m.name LIKE %s)"
                )
                params.extend([like, like, like, like])

            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)
            base_query += " ORDER BY ib.issue_date DESC"

            cursor.execute(base_query, tuple(params))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            def is_overdue(row):
                # row = (issue_id, book_id, title, member_id, name, issue_date, due_date, status)
                status, due = row[7], row[6]
                return status == "Issued" and due < date.today()

            theme.fill_treeview(self.tree, rows, overdue_check=is_overdue)

        except Error as e:
            messagebox.showerror("Database Error", f"Could not load issued books:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    theme.apply_theme(root)
    IssueReturnWindow(root)
    root.mainloop()
