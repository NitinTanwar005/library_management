"""
dashboard.py
------------
Main menu shown after a successful login. Presents tile-style
buttons that open each functional module (books, members,
issue/return, reports) in its own window, plus quick stats pulled
from the database.
"""

import tkinter as tk
from tkinter import messagebox
from mysql.connector import Error

import config
import theme


class Dashboard(tk.Toplevel):
    def __init__(self, master, user):
        super().__init__(master)
        self.user = user
        self.title(f"{config.APP_NAME} - Dashboard")
        self.geometry("1080x680")
        self.minsize(960, 600)
        self.configure(bg=theme.BG_APP)
        theme.apply_theme(self)

        self._build_topbar()
        self._build_body()
        self.refresh_stats()

    # ------------------------------------------------------------
    def _build_topbar(self):
        topbar = tk.Frame(self, bg=theme.PRIMARY_DARK, height=64)
        topbar.pack(fill="x", side="top")
        topbar.pack_propagate(False)

        tk.Label(
            topbar,
            text=f"📚  {config.APP_NAME}",
            font=theme.FONT_H2,
            bg=theme.PRIMARY_DARK,
            fg=theme.WHITE,
        ).pack(side="left", padx=24)

        right = tk.Frame(topbar, bg=theme.PRIMARY_DARK)
        right.pack(side="right", padx=24)

        tk.Label(
            right,
            text=f"{self.user.get('full_name', 'Staff')}  ·  {self.user.get('role', 'Librarian')}",
            font=theme.FONT_BODY,
            bg=theme.PRIMARY_DARK,
            fg=theme.SLATE_200,
        ).pack(side="left", padx=(0, 16))

        theme.StyledButton(
            right, text="Logout", kind="danger", width=10, command=self._logout
        ).pack(side="left")

    # ------------------------------------------------------------
    def _build_body(self):
        body = tk.Frame(self, bg=theme.BG_APP)
        body.pack(fill="both", expand=True, padx=30, pady=24)

        header = theme.make_header(
            body, "Dashboard", "Overview and quick access to every module", bg=theme.BG_APP
        )
        header.pack(fill="x", pady=(0, 18))

        # ---- stat cards ----
        self.stats_frame = tk.Frame(body, bg=theme.BG_APP)
        self.stats_frame.pack(fill="x", pady=(0, 24))
        self.stat_labels = {}
        for key, label, kind in [
            ("books", "Total Books", "primary"),
            ("members", "Total Members", "info"),
            ("issued", "Books Issued", "success"),
            ("overdue", "Overdue Books", "danger"),
        ]:
            self._make_stat_card(self.stats_frame, key, label, kind)

        # ---- module tiles ----
        tiles_frame = tk.Frame(body, bg=theme.BG_APP)
        tiles_frame.pack(fill="both", expand=True)
        for i in range(3):
            tiles_frame.grid_columnconfigure(i, weight=1, uniform="tile")

        tiles = [
            ("📖", "Manage Books", "Add, update, delete and search the catalog", self.open_books),
            ("👥", "Manage Members", "Add, update, delete and search members", self.open_members),
            ("🔄", "Issue / Return", "Issue books, process returns, calculate fines", self.open_issue_return),
            ("📊", "Reports", "View issued/overdue books, export to Excel/CSV", self.open_reports),
            ("➕", "Register Staff", "Create a new staff login account", self.open_register),
            ("🚪", "Logout", "Sign out of the application", self._logout),
        ]

        for idx, (icon, title, desc, cmd) in enumerate(tiles):
            row, col = divmod(idx, 3)
            self._make_tile(tiles_frame, icon, title, desc, cmd, row, col)

    # ------------------------------------------------------------
    def _make_stat_card(self, parent, key, label, kind):
        color_map = {
            "primary": theme.PRIMARY,
            "info": theme.INFO,
            "success": theme.SUCCESS,
            "danger": theme.DANGER,
        }
        color = color_map[kind]

        card = tk.Frame(parent, bg=theme.BG_CARD, highlightbackground=theme.BORDER,
                         highlightthickness=1)
        card.pack(side="left", fill="both", expand=True, padx=8, ipady=6)

        bar = tk.Frame(card, bg=color, height=4)
        bar.pack(fill="x", side="top")

        inner = tk.Frame(card, bg=theme.BG_CARD)
        inner.pack(fill="both", expand=True, padx=18, pady=14)

        value_lbl = tk.Label(
            inner, text="—", font=(theme.FONT_FAMILY, 26, "bold"), bg=theme.BG_CARD, fg=color
        )
        value_lbl.pack(anchor="w")
        tk.Label(
            inner, text=label, font=theme.FONT_BODY, bg=theme.BG_CARD, fg=theme.TEXT_MUTED
        ).pack(anchor="w")

        self.stat_labels[key] = value_lbl

    def _make_tile(self, parent, icon, title, desc, command, row, col):
        tile = tk.Frame(parent, bg=theme.BG_CARD, highlightbackground=theme.BORDER,
                         highlightthickness=1, cursor="hand2")
        tile.grid(row=row, column=col, sticky="nsew", padx=8, pady=8, ipady=10)

        inner = tk.Frame(tile, bg=theme.BG_CARD)
        inner.pack(fill="both", expand=True, padx=18, pady=16)

        tk.Label(inner, text=icon, font=("Segoe UI", 28), bg=theme.BG_CARD).pack(anchor="w")
        tk.Label(
            inner, text=title, font=theme.FONT_H3, bg=theme.BG_CARD, fg=theme.TEXT_DARK
        ).pack(anchor="w", pady=(8, 2))
        tk.Label(
            inner,
            text=desc,
            font=theme.FONT_SMALL,
            bg=theme.BG_CARD,
            fg=theme.TEXT_MUTED,
            wraplength=240,
            justify="left",
        ).pack(anchor="w")

        for widget in (tile, inner, *inner.winfo_children()):
            widget.bind("<Button-1>", lambda e: command())

    # ------------------------------------------------------------
    def refresh_stats(self):
        try:
            conn = config.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM books")
            books_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM members")
            members_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM issued_books WHERE status = 'Issued'")
            issued_count = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM issued_books WHERE status = 'Issued' AND due_date < CURDATE()"
            )
            overdue_count = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            self.stat_labels["books"].config(text=str(books_count))
            self.stat_labels["members"].config(text=str(members_count))
            self.stat_labels["issued"].config(text=str(issued_count))
            self.stat_labels["overdue"].config(text=str(overdue_count))
        except Error as e:
            messagebox.showerror("Database Error", f"Could not load dashboard stats:\n{e}")

    # ------------------------------------------------------------
    # Module launchers
    # ------------------------------------------------------------
    def open_books(self):
        from book import BookWindow
        BookWindow(self)

    def open_members(self):
        from member import MemberWindow
        MemberWindow(self)

    def open_issue_return(self):
        from issue_return import IssueReturnWindow
        IssueReturnWindow(self, on_change=self.refresh_stats)

    def open_reports(self):
        from report import ReportWindow
        ReportWindow(self)

    def open_register(self):
        from register import RegisterWindow
        RegisterWindow(self)

    def _logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to log out?"):
            self.destroy()
            self.master.deiconify()
            self.master.var_username.set("")
            self.master.var_password.set("")
