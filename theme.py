"""
theme.py
--------
Centralized look-and-feel for the whole application: colors, fonts,
and small factory functions that build consistently styled Tkinter
widgets (buttons, labels, entries, headers, Treeviews).

Every screen module imports from here instead of hard-coding colors
so the whole app stays visually consistent and easy to re-theme.
"""

import tkinter as tk
from tkinter import ttk

# ------------------------------------------------------------------
# Color palette (Indigo / Slate)
# ------------------------------------------------------------------
PRIMARY = "#4338CA"        # indigo-700   - headers, primary actions
PRIMARY_DARK = "#312E81"   # indigo-900   - sidebar / topbar background
PRIMARY_LIGHT = "#6366F1"  # indigo-500   - hover state

SLATE_900 = "#0F172A"
SLATE_800 = "#1E293B"
SLATE_700 = "#334155"
SLATE_500 = "#64748B"
SLATE_200 = "#E2E8F0"
SLATE_100 = "#F1F5F9"
SLATE_50 = "#F8FAFC"

WHITE = "#FFFFFF"

SUCCESS = "#16A34A"        # green  - save / add / confirm
SUCCESS_DARK = "#15803D"
DANGER = "#DC2626"         # red    - delete / cancel-destructive
DANGER_DARK = "#B91C1C"
INFO = "#2563EB"           # blue   - neutral / view / search
INFO_DARK = "#1D4ED8"
WARNING = "#D97706"        # amber  - overdue / warnings

BG_APP = SLATE_100
BG_CARD = WHITE
TEXT_DARK = SLATE_900
TEXT_MUTED = SLATE_500
BORDER = SLATE_200

# ------------------------------------------------------------------
# Fonts
# ------------------------------------------------------------------
FONT_FAMILY = "Segoe UI"

FONT_H1 = (FONT_FAMILY, 22, "bold")
FONT_H2 = (FONT_FAMILY, 16, "bold")
FONT_H3 = (FONT_FAMILY, 12, "bold")
FONT_BODY = (FONT_FAMILY, 10)
FONT_BODY_BOLD = (FONT_FAMILY, 10, "bold")
FONT_SMALL = (FONT_FAMILY, 9)
FONT_BUTTON = (FONT_FAMILY, 10, "bold")


# ------------------------------------------------------------------
# ttk style setup (call once, right after the root window is made)
# ------------------------------------------------------------------
def apply_theme(root: tk.Tk):
    """Configure global ttk styles used across all screens."""
    root.configure(bg=BG_APP)
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    # Treeview (table) styling - striped rows handled by tags
    style.configure(
        "Lib.Treeview",
        background=WHITE,
        fieldbackground=WHITE,
        foreground=TEXT_DARK,
        rowheight=28,
        font=FONT_BODY,
        borderwidth=0,
    )
    style.configure(
        "Lib.Treeview.Heading",
        background=PRIMARY,
        foreground=WHITE,
        font=FONT_BODY_BOLD,
        relief="flat",
    )
    style.map(
        "Lib.Treeview.Heading",
        background=[("active", PRIMARY_LIGHT)],
    )
    style.map(
        "Lib.Treeview",
        background=[("selected", PRIMARY_LIGHT)],
        foreground=[("selected", WHITE)],
    )

    # Entry
    style.configure(
        "Lib.TEntry",
        fieldbackground=WHITE,
        borderwidth=1,
        relief="solid",
        padding=6,
    )

    # Combobox
    style.configure("Lib.TCombobox", padding=6)

    # Notebook (tabs), used by dashboard/report screens if needed
    style.configure("Lib.TNotebook", background=BG_APP, borderwidth=0)
    style.configure(
        "Lib.TNotebook.Tab",
        background=SLATE_200,
        foreground=TEXT_DARK,
        padding=(16, 8),
        font=FONT_BODY_BOLD,
    )
    style.map(
        "Lib.TNotebook.Tab",
        background=[("selected", PRIMARY)],
        foreground=[("selected", WHITE)],
    )

    return style


# ------------------------------------------------------------------
# Reusable styled widgets
# ------------------------------------------------------------------
class StyledButton(tk.Button):
    """
    A flat, color-coded button.
    kind: 'primary' | 'success' | 'danger' | 'info' | 'muted'
    """

    PALETTE = {
        "primary": (PRIMARY, PRIMARY_DARK, WHITE),
        "success": (SUCCESS, SUCCESS_DARK, WHITE),
        "danger": (DANGER, DANGER_DARK, WHITE),
        "info": (INFO, INFO_DARK, WHITE),
        "muted": (SLATE_200, SLATE_500, TEXT_DARK),
    }

    def __init__(self, master, text="", kind="primary", command=None, width=14, **kwargs):
        bg, active_bg, fg = self.PALETTE.get(kind, self.PALETTE["primary"])
        super().__init__(
            master,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=active_bg,
            activeforeground=fg,
            font=FONT_BUTTON,
            relief="flat",
            bd=0,
            width=width,
            cursor="hand2",
            padx=10,
            pady=8,
            **kwargs,
        )
        self._bg = bg
        self._active_bg = active_bg
        self.bind("<Enter>", lambda e: self.config(bg=active_bg))
        self.bind("<Leave>", lambda e: self.config(bg=bg))


def make_label(master, text, font=FONT_BODY, fg=TEXT_DARK, bg=BG_CARD, **kwargs):
    return tk.Label(master, text=text, font=font, fg=fg, bg=bg, **kwargs)


def make_header(master, text, subtitle=None, bg=BG_APP):
    """A page header block: bold title + optional muted subtitle."""
    frame = tk.Frame(master, bg=bg)
    tk.Label(frame, text=text, font=FONT_H1, fg=TEXT_DARK, bg=bg).pack(anchor="w")
    if subtitle:
        tk.Label(frame, text=subtitle, font=FONT_BODY, fg=TEXT_MUTED, bg=bg).pack(
            anchor="w", pady=(2, 0)
        )
    return frame


def make_entry(master, textvariable=None, width=30, show=None):
    e = tk.Entry(
        master,
        textvariable=textvariable,
        width=width,
        font=FONT_BODY,
        relief="solid",
        bd=1,
        highlightthickness=1,
        highlightbackground=BORDER,
        highlightcolor=PRIMARY,
        show=show if show else "",
    )
    return e


def make_card(master, bg=BG_CARD):
    """A white 'card' panel with a subtle border, used to group form fields."""
    outer = tk.Frame(master, bg=BORDER)
    inner = tk.Frame(outer, bg=bg)
    inner.pack(fill="both", expand=True, padx=1, pady=1)
    return outer, inner


def styled_treeview(master, columns, height=14):
    """
    Build a ttk.Treeview configured with the app theme, striped rows,
    and a vertical scrollbar. Returns the Treeview widget.
    Caller is responsible for inserting rows and tagging alternate
    rows with 'oddrow' / 'evenrow' for the stripe effect.
    """
    container = tk.Frame(master, bg=BG_CARD)
    container.pack(fill="both", expand=True)

    tree = ttk.Treeview(
        container,
        columns=columns,
        show="headings",
        style="Lib.Treeview",
        height=height,
    )
    vsb = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)

    tree.tag_configure("oddrow", background=SLATE_50)
    tree.tag_configure("evenrow", background=WHITE)
    tree.tag_configure("overdue", background="#FEE2E2", foreground=DANGER_DARK)

    return tree


def fill_treeview(tree, rows, overdue_check=None):
    """
    Clear and refill a Treeview with rows (list of tuples), applying
    the striped-row tags automatically. overdue_check, if given, is a
    function(row) -> bool marking a row with the 'overdue' style.
    """
    tree.delete(*tree.get_children())
    for i, row in enumerate(rows):
        if overdue_check and overdue_check(row):
            tag = "overdue"
        else:
            tag = "evenrow" if i % 2 == 0 else "oddrow"
        tree.insert("", "end", values=row, tags=(tag,))
