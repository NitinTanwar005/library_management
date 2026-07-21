"""
member.py
---------
Library member management: add, update, delete and search members.
Fields: Member ID, Name, Roll/Employee No, Email, Phone, Address.
"""

import re
import tkinter as tk
from tkinter import messagebox
from mysql.connector import Error

import config
import theme

COLUMNS = ("member_id", "name", "roll_no", "email", "phone", "address")
HEADINGS = ("Member ID", "Name", "Roll/Employee No", "Email", "Phone", "Address")


class MemberWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title(f"{config.APP_NAME} - Manage Members")
        self.geometry("1080x660")
        self.minsize(960, 580)
        self.configure(bg=theme.BG_APP)
        theme.apply_theme(self)

        self.selected_member_id = None
        self.vars = {col: tk.StringVar() for col in COLUMNS}
        self.var_search = tk.StringVar()

        self._build_ui()
        self.load_members()

    # ------------------------------------------------------------
    def _build_ui(self):
        header = theme.make_header(self, "Manage Members", "Add, update, delete and search members")
        header.pack(fill="x", padx=24, pady=(20, 10))

        form_outer, form = theme.make_card(self)
        form_outer.pack(fill="x", padx=24, pady=(0, 12))

        grid = tk.Frame(form, bg=theme.BG_CARD)
        grid.pack(fill="x", padx=20, pady=16)

        fields = [
            ("Member ID", "member_id"),
            ("Name", "name"),
            ("Roll/Employee No", "roll_no"),
            ("Email", "email"),
            ("Phone", "phone"),
            ("Address", "address"),
        ]
        for i, (label, key) in enumerate(fields):
            r, c = divmod(i, 3)
            cell = tk.Frame(grid, bg=theme.BG_CARD)
            cell.grid(row=r, column=c, padx=10, pady=8, sticky="w")
            tk.Label(
                cell, text=label, font=theme.FONT_BODY_BOLD, bg=theme.BG_CARD, fg=theme.TEXT_DARK
            ).pack(anchor="w")
            width = 34 if key == "address" else 22
            entry = theme.make_entry(cell, self.vars[key], width=width)
            entry.pack(anchor="w", pady=(2, 0))
            if key == "member_id":
                self.entry_member_id = entry

        btns = tk.Frame(form, bg=theme.BG_CARD)
        btns.pack(fill="x", padx=20, pady=(0, 16))
        theme.StyledButton(btns, text="Add Member", kind="success", command=self.add_member).pack(
            side="left", padx=(0, 8)
        )
        theme.StyledButton(btns, text="Update", kind="info", command=self.update_member).pack(
            side="left", padx=8
        )
        theme.StyledButton(btns, text="Delete", kind="danger", command=self.delete_member).pack(
            side="left", padx=8
        )
        theme.StyledButton(btns, text="Clear Form", kind="muted", command=self.clear_form).pack(
            side="left", padx=8
        )

        search_frame = tk.Frame(self, bg=theme.BG_APP)
        search_frame.pack(fill="x", padx=24, pady=(4, 8))
        tk.Label(
            search_frame, text="Search:", font=theme.FONT_BODY_BOLD, bg=theme.BG_APP
        ).pack(side="left", padx=(0, 8))
        search_entry = theme.make_entry(search_frame, self.var_search, width=40)
        search_entry.pack(side="left")
        search_entry.bind("<KeyRelease>", lambda e: self.load_members())
        theme.StyledButton(
            search_frame, text="Refresh", kind="muted", width=10, command=self.load_members
        ).pack(side="left", padx=8)

        table_outer = tk.Frame(self, bg=theme.BG_APP)
        table_outer.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        self.tree = theme.styled_treeview(table_outer, COLUMNS, height=14)
        for col, heading in zip(COLUMNS, HEADINGS):
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=140, anchor="center")
        self.tree.column("name", width=180, anchor="w")
        self.tree.column("address", width=220, anchor="w")
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

    # ------------------------------------------------------------
    def clear_form(self):
        for v in self.vars.values():
            v.set("")
        self.selected_member_id = None

    def on_row_select(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        for key, value in zip(COLUMNS, values):
            self.vars[key].set(value)
        self.selected_member_id = values[0]

    # ------------------------------------------------------------
    def _validate_form(self):
        member_id = self.vars["member_id"].get().strip()
        name = self.vars["name"].get().strip()
        email = self.vars["email"].get().strip()
        phone = self.vars["phone"].get().strip()

        if not member_id or not name:
            messagebox.showerror("Validation Error", "Member ID and Name are required.")
            return None
        if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            messagebox.showerror("Validation Error", "Please enter a valid email address.")
            return None
        if phone and not re.match(r"^[\d+\-\s()]{7,15}$", phone):
            messagebox.showerror("Validation Error", "Please enter a valid phone number.")
            return None

        return {
            "member_id": member_id,
            "name": name,
            "roll_no": self.vars["roll_no"].get().strip(),
            "email": email,
            "phone": phone,
            "address": self.vars["address"].get().strip(),
        }

    # ------------------------------------------------------------
    def add_member(self):
        data = self._validate_form()
        if not data:
            return
        try:
            conn = config.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT member_id FROM members WHERE member_id = %s", (data["member_id"],)
            )
            if cursor.fetchone():
                messagebox.showerror(
                    "Duplicate Member ID", "A member with this ID already exists."
                )
                cursor.close()
                conn.close()
                return

            cursor.execute(
                """INSERT INTO members (member_id, name, roll_no, email, phone, address)
                   VALUES (%s,%s,%s,%s,%s,%s)""",
                (
                    data["member_id"], data["name"], data["roll_no"],
                    data["email"], data["phone"], data["address"],
                ),
            )
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Success", "Member added successfully.")
            self.clear_form()
            self.load_members()
        except Error as e:
            messagebox.showerror("Database Error", f"Could not add member:\n{e}")

    def update_member(self):
        if not self.selected_member_id:
            messagebox.showwarning("No Selection", "Select a member from the table to update.")
            return
        data = self._validate_form()
        if not data:
            return
        try:
            conn = config.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE members SET name=%s, roll_no=%s, email=%s, phone=%s, address=%s
                   WHERE member_id=%s""",
                (
                    data["name"], data["roll_no"], data["email"], data["phone"],
                    data["address"], self.selected_member_id,
                ),
            )
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Success", "Member updated successfully.")
            self.clear_form()
            self.load_members()
        except Error as e:
            messagebox.showerror("Database Error", f"Could not update member:\n{e}")

    def delete_member(self):
        if not self.selected_member_id:
            messagebox.showwarning("No Selection", "Select a member from the table to delete.")
            return
        if not messagebox.askyesno("Confirm Delete", "Delete this member? This cannot be undone."):
            return
        try:
            conn = config.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM members WHERE member_id = %s", (self.selected_member_id,))
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Success", "Member deleted successfully.")
            self.clear_form()
            self.load_members()
        except Error as e:
            messagebox.showerror(
                "Database Error",
                f"Could not delete member (they may have issue history linked to them):\n{e}",
            )

    # ------------------------------------------------------------
    def load_members(self):
        search = self.var_search.get().strip()
        try:
            conn = config.get_connection()
            cursor = conn.cursor()
            if search:
                like = f"%{search}%"
                cursor.execute(
                    """SELECT member_id, name, roll_no, email, phone, address
                       FROM members
                       WHERE member_id LIKE %s OR name LIKE %s OR roll_no LIKE %s
                          OR email LIKE %s OR phone LIKE %s
                       ORDER BY name""",
                    (like, like, like, like, like),
                )
            else:
                cursor.execute(
                    "SELECT member_id, name, roll_no, email, phone, address FROM members ORDER BY name"
                )
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            theme.fill_treeview(self.tree, rows)
        except Error as e:
            messagebox.showerror("Database Error", f"Could not load members:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    theme.apply_theme(root)
    MemberWindow(root)
    root.mainloop()
