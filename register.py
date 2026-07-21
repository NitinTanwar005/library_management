"""
register.py
------------
Staff registration screen. New librarian/admin accounts are created
here. Passwords are hashed with SHA-256 before being stored — the
raw password is never written to the database.
"""

import re
import hashlib
import tkinter as tk
from tkinter import messagebox

from mysql.connector import Error
import config
import theme


def hash_password(raw_password: str) -> str:
    return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()


class RegisterWindow(tk.Toplevel):
    """
    Registration window, opened on top of the login screen.
    on_success is called (no args) after a successful registration so
    the login screen can, e.g., pre-fill the username field.
    """

    def __init__(self, master, on_success=None):
        super().__init__(master)
        self.on_success = on_success
        self.title(f"{config.APP_NAME} - Staff Registration")
        
        # INCREASED HEIGHT TO 640 SO THE BUTTONS ARE VISIBLE
        self.geometry("460x640")
        
        self.configure(bg=theme.BG_APP)
        self.resizable(False, False)
        self.grab_set()  # modal

        self.var_name = tk.StringVar()
        self.var_username = tk.StringVar()
        self.var_email = tk.StringVar()
        self.var_password = tk.StringVar()
        self.var_confirm = tk.StringVar()
        self.var_role = tk.StringVar(value="Librarian")

        self._build_ui()

    # ------------------------------------------------------------
    def _build_ui(self):
        header = theme.make_header(
            self, "Create Staff Account", "Register a new librarian / admin login"
        )
        header.pack(fill="x", padx=30, pady=(24, 10))

        outer, card = theme.make_card(self)
        outer.pack(fill="both", expand=True, padx=30, pady=10)

        pad = {"padx": 24, "pady": (14, 4)}

        theme.make_label(card, "Full Name", font=theme.FONT_BODY_BOLD).pack(anchor="w", **pad)
        theme.make_entry(card, self.var_name, width=34).pack(anchor="w", padx=24)

        theme.make_label(card, "Username", font=theme.FONT_BODY_BOLD).pack(anchor="w", **pad)
        theme.make_entry(card, self.var_username, width=34).pack(anchor="w", padx=24)

        theme.make_label(card, "Email", font=theme.FONT_BODY_BOLD).pack(anchor="w", **pad)
        theme.make_entry(card, self.var_email, width=34).pack(anchor="w", padx=24)

        theme.make_label(card, "Role", font=theme.FONT_BODY_BOLD).pack(anchor="w", **pad)
        role_frame = tk.Frame(card, bg=theme.BG_CARD)
        role_frame.pack(anchor="w", padx=24)
        for role in ("Librarian", "Admin"):
            tk.Radiobutton(
                role_frame,
                text=role,
                variable=self.var_role,
                value=role,
                bg=theme.BG_CARD,
                font=theme.FONT_BODY,
                activebackground=theme.BG_CARD,
            ).pack(side="left", padx=(0, 16))

        theme.make_label(card, "Password", font=theme.FONT_BODY_BOLD).pack(anchor="w", **pad)
        theme.make_entry(card, self.var_password, width=34, show="*").pack(anchor="w", padx=24)

        theme.make_label(card, "Confirm Password", font=theme.FONT_BODY_BOLD).pack(
            anchor="w", **pad
        )
        theme.make_entry(card, self.var_confirm, width=34, show="*").pack(anchor="w", padx=24)

        btn_frame = tk.Frame(card, bg=theme.BG_CARD)
        btn_frame.pack(fill="x", padx=24, pady=24)
        
        theme.StyledButton(
            btn_frame, text="Register", kind="success", width=14, command=self._handle_registration
        ).pack(side="left")
        
        theme.StyledButton(
            btn_frame, text="Cancel", kind="muted", width=10, command=self.destroy
        ).pack(side="right")

    # ------------------------------------------------------------
    def _validate(self):
        name = self.var_name.get().strip()
        username = self.var_username.get().strip()
        email = self.var_email.get().strip()
        password = self.var_password.get()
        confirm = self.var_confirm.get()

        if not name or not username or not password:
            messagebox.showerror("Validation Error", "Name, username and password are required.")
            return None
        if len(username) < 4:
            messagebox.showerror("Validation Error", "Username must be at least 4 characters.")
            return None
        if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            messagebox.showerror("Validation Error", "Please enter a valid email address.")
            return None
        if len(password) < 6:
            messagebox.showerror("Validation Error", "Password must be at least 6 characters.")
            return None
        if password != confirm:
            messagebox.showerror("Validation Error", "Passwords do not match.")
            return None

        return {
            "full_name": name,
            "username": username,
            "email": email,
            "password": password,
            "role": self.var_role.get(),
        }

    # ------------------------------------------------------------
    def _handle_registration(self):
        data = self._validate()
        if not data:
            return

        try:
            conn = config.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (data["username"],))
            if cursor.fetchone():
                messagebox.showerror("Registration Failed", "That username is already taken.")
                cursor.close()
                conn.close()
                return

            cursor.execute(
                """INSERT INTO users (full_name, username, password, role, email)
                   VALUES (%s, %s, %s, %s, %s)""",
                (
                    data["full_name"],
                    data["username"],
                    hash_password(data["password"]),
                    data["role"],
                    data["email"],
                ),
            )
            conn.commit()
            cursor.close()
            conn.close()

            messagebox.showinfo("Success", "Account created successfully. You may now log in.")
            if self.on_success:
                self.on_success(data["username"])
            self.destroy()

        except Error as e:
            messagebox.showerror("Database Error", f"Could not register account:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    theme.apply_theme(root)
    RegisterWindow(root)
    root.mainloop()