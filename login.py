"""
login.py
--------
Staff login screen. This is the application's entry point
(`python login.py`). On successful authentication it opens the
main dashboard and closes the login window.
"""

import hashlib
import tkinter as tk
from tkinter import messagebox

from mysql.connector import Error
import config
import theme
from register import RegisterWindow, hash_password


class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{config.APP_NAME} - Login")
        self.geometry("900x560")
        self.minsize(820, 520)
        self.configure(bg=theme.BG_APP)
        theme.apply_theme(self)

        self.var_username = tk.StringVar()
        self.var_password = tk.StringVar()

        self._build_ui()
        self.bind("<Return>", lambda e: self._login())

    # ------------------------------------------------------------
    def _build_ui(self):
        # Split screen: brand panel (left) + login form (right)
        container = tk.Frame(self, bg=theme.BG_APP)
        container.pack(fill="both", expand=True)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)

        brand = tk.Frame(container, bg=theme.PRIMARY_DARK)
        brand.grid(row=0, column=0, sticky="nsew")

        brand_inner = tk.Frame(brand, bg=theme.PRIMARY_DARK)
        brand_inner.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(
            brand_inner, text="📚", font=("Segoe UI", 54), bg=theme.PRIMARY_DARK, fg=theme.WHITE
        ).pack()
        tk.Label(
            brand_inner,
            text=config.APP_NAME,
            font=(theme.FONT_FAMILY, 22, "bold"),
            bg=theme.PRIMARY_DARK,
            fg=theme.WHITE,
        ).pack(pady=(10, 4))
        tk.Label(
            brand_inner,
            text="Manage books, members, and\ncirculation from one place.",
            font=theme.FONT_BODY,
            bg=theme.PRIMARY_DARK,
            fg=theme.SLATE_200,
            justify="center",
        ).pack()

        # Right: login form
        form_outer = tk.Frame(container, bg=theme.BG_APP)
        form_outer.grid(row=0, column=1, sticky="nsew")

        form = tk.Frame(form_outer, bg=theme.BG_APP)
        form.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            form, text="Staff Login", font=theme.FONT_H1, bg=theme.BG_APP, fg=theme.TEXT_DARK
        ).pack(anchor="w", pady=(0, 4))
        tk.Label(
            form,
            text="Enter your credentials to continue",
            font=theme.FONT_BODY,
            bg=theme.BG_APP,
            fg=theme.TEXT_MUTED,
        ).pack(anchor="w", pady=(0, 20))

        tk.Label(
            form, text="Username", font=theme.FONT_BODY_BOLD, bg=theme.BG_APP, fg=theme.TEXT_DARK
        ).pack(anchor="w")
        theme.make_entry(form, self.var_username, width=32).pack(anchor="w", pady=(4, 14))

        tk.Label(
            form, text="Password", font=theme.FONT_BODY_BOLD, bg=theme.BG_APP, fg=theme.TEXT_DARK
        ).pack(anchor="w")
        theme.make_entry(form, self.var_password, width=32, show="*").pack(
            anchor="w", pady=(4, 22)
        )

        theme.StyledButton(
            form, text="Log In", kind="primary", width=28, command=self._login
        ).pack(anchor="w", pady=(0, 12))

        bottom = tk.Frame(form, bg=theme.BG_APP)
        bottom.pack(anchor="w")
        tk.Label(
            bottom,
            text="Don't have an account?",
            font=theme.FONT_SMALL,
            bg=theme.BG_APP,
            fg=theme.TEXT_MUTED,
        ).pack(side="left")
        link = tk.Label(
            bottom,
            text=" Register here",
            font=(theme.FONT_FAMILY, 9, "bold underline"),
            bg=theme.BG_APP,
            fg=theme.PRIMARY,
            cursor="hand2",
        )
        link.pack(side="left")
        link.bind("<Button-1>", lambda e: self._open_register())

    # ------------------------------------------------------------
    def _open_register(self):
        RegisterWindow(self, on_success=lambda username: self.var_username.set(username))

    # ------------------------------------------------------------
    def _login(self):
        username = self.var_username.get().strip()
        password = self.var_password.get()

        if not username or not password:
            messagebox.showerror("Validation Error", "Please enter both username and password.")
            return

        try:
            conn = config.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM users WHERE username = %s", (username,)
            )
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if not user or user["password"] != hash_password(password):
                messagebox.showerror("Login Failed", "Invalid username or password.")
                return

            messagebox.showinfo("Welcome", f"Welcome back, {user['full_name']}!")
            self._open_dashboard(user)

        except Error as e:
            messagebox.showerror("Database Error", f"Could not connect to database:\n{e}")

    # ------------------------------------------------------------
    def _open_dashboard(self, user):
        self.withdraw()  # hide login window instead of destroying, in case of logout
        from dashboard import Dashboard  # local import avoids circular import at module load

        dash = Dashboard(self, user)
        dash.protocol("WM_DELETE_WINDOW", lambda: self._on_dashboard_close(dash))

    def _on_dashboard_close(self, dash):
        dash.destroy()
        self.destroy()


if __name__ == "__main__":
    app = LoginWindow()
    app.mainloop()
