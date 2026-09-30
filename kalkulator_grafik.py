"""
Kalkulator & Grafik - Aplikasi Desktop
========================================
Aplikasi kalkulator dengan fitur grafik, dibangun dengan Tkinter (GUI bawaan
Python) dan Matplotlib (untuk menggambar grafik). Ini adalah aplikasi desktop
asli: berjalan sebagai jendela sendiri, tanpa browser.

Cara menjalankan:
    1. Pastikan Python 3 sudah terpasang di komputer.
    2. Pasang library yang dibutuhkan (sekali saja):
           pip install matplotlib numpy
       Catatan (khusus Linux/Debian/Ubuntu): jika muncul error "No module
       named tkinter", pasang dulu dengan:
           sudo apt install python3-tk
    3. Jalankan aplikasinya:
           python kalkulator_grafik.py
"""

import ast
import math
import operator
import tkinter as tk
from tkinter import ttk

import numpy as np
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk,
)
from matplotlib.figure import Figure

# ---------------------------------------------------------------------------
# Evaluator ekspresi matematika yang aman (tidak pakai eval() mentah)
# ---------------------------------------------------------------------------

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}
_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}
_FUNCTIONS = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "sqrt": math.sqrt,
    "abs": abs,
    "log": math.log10,
    "ln": math.log,
    "exp": math.exp,
}
_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
}


def safe_eval(expr: str, x_value: float | None = None) -> float:
    """Mengevaluasi ekspresi matematika dari teks dengan aman.

    Mendukung angka, + - * / % ^, tanda kurung, fungsi (sin, cos, tan, sqrt,
    abs, log, ln, exp), konstanta (pi, e), dan variabel 'x' bila x_value diisi
    (dipakai untuk menggambar grafik).
    """
    expr = expr.replace("^", "**")
    tree = ast.parse(expr, mode="eval")

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Nilai tidak didukung")
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
            return _BIN_OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
            return _UNARY_OPS[type(node.op)](_eval(node.operand))
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in _FUNCTIONS:
                args = [_eval(a) for a in node.args]
                return _FUNCTIONS[node.func.id](*args)
            raise ValueError("Fungsi tidak dikenali")
        if isinstance(node, ast.Name):
            if node.id == "x" and x_value is not None:
                return x_value
            if node.id in _CONSTANTS:
                return _CONSTANTS[node.id]
            raise ValueError(f"Nama tidak dikenali: {node.id}")
        raise ValueError("Ekspresi tidak valid")

    return _eval(tree)


# ---------------------------------------------------------------------------
# Aplikasi utama
# ---------------------------------------------------------------------------

BG = "#12151a"
PANEL = "#1a1e26"
PANEL2 = "#20252f"
TEXT = "#eef1f6"
SUB = "#8a93a6"
ACCENT = "#5ee6c4"
ACCENT2 = "#ff9d5c"
OP_BG = "#2c3345"
DANGER = "#ff6b6b"


class CalculatorGraphApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Kalkulator & Grafik")
        self.geometry("420x640")
        self.minsize(360, 560)
        self.configure(bg=BG)

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=PANEL,
            foreground=SUB,
            padding=(16, 10),
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", PANEL2)],
            foreground=[("selected", ACCENT)],
        )

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        self.calc_tab = tk.Frame(notebook, bg=PANEL)
        self.graph_tab = tk.Frame(notebook, bg=PANEL)
        notebook.add(self.calc_tab, text="Kalkulator")
        notebook.add(self.graph_tab, text="Grafik")

        self._build_calculator(self.calc_tab)
        self._build_graph(self.graph_tab)

        self.bind("<Key>", self._on_keypress)

    # ---------------------- Tab Kalkulator ----------------------
    def _build_calculator(self, parent):
        self.expr = ""

        display = tk.Frame(parent, bg=PANEL2)
        display.pack(fill="x", padx=16, pady=16)

        self.expr_var = tk.StringVar(value=" ")
        self.result_var = tk.StringVar(value="0")

        tk.Label(
            display, textvariable=self.expr_var, anchor="e",
            bg=PANEL2, fg=SUB, font=("Consolas", 12),
        ).pack(fill="x", padx=14, pady=(12, 0))

        tk.Label(
            display, textvariable=self.result_var, anchor="e",
            bg=PANEL2, fg=TEXT, font=("Consolas", 28, "bold"),
        ).pack(fill="x", padx=14, pady=(0, 12))

        grid = tk.Frame(parent, bg=PANEL)
        grid.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        rows = [
            [("C", "clear"), ("%", "fn"), ("\u221a", "fn"), ("\u232b", "fn")],
            [("(", "op"), (")", "op"), ("x\u00b2", "fn"), ("\u00f7", "op")],
            [("7", "num"), ("8", "num"), ("9", "num"), ("\u00d7", "op")],
            [("4", "num"), ("5", "num"), ("6", "num"), ("\u2212", "op")],
            [("1", "num"), ("2", "num"), ("3", "num"), ("+", "op")],
            [("\u00b1", "fn"), ("0", "num"), (".", "num"), ("=", "eq")],
        ]

        colors = {
            "num": (PANEL2, TEXT),
            "op": (OP_BG, ACCENT),
            "fn": (OP_BG, ACCENT2),
            "clear": (OP_BG, DANGER),
            "eq": (ACCENT, "#0b0f12"),
        }

        for r, row in enumerate(rows):
            grid.rowconfigure(r, weight=1)
            for c, (label, kind) in enumerate(row):
                grid.columnconfigure(c, weight=1)
                bg, fg = colors[kind]
                btn = tk.Button(
                    grid, text=label, bg=bg, fg=fg,
                    font=("Consolas", 14, "bold" if kind == "eq" else "normal"),
                    relief="flat", activebackground=bg, activeforeground=fg,
                    command=lambda lbl=label: self._handle_key(lbl),
                )
                btn.grid(row=r, column=c, sticky="nsew", padx=5, pady=5)

    def _trailing_number(self):
        """Mencari angka terakhir di ujung ekspresi (untuk %, ±, x²)."""
        i = len(self.expr)
        j = i
        while j > 0 and (self.expr[j - 1].isdigit() or self.expr[j - 1] == "."):
            j -= 1
        if j > 0 and self.expr[j - 1] == "-" and (j == 1 or not self.expr[j - 2].isdigit()):
            j -= 1
        if j == i:
            return None, None, None
        return self.expr[j:i], j, i

    def _refresh_display(self):
        self.expr_var.set(self.expr if self.expr else " ")
        self.result_var.set(self.expr if self.expr else "0")

    def _handle_key(self, label):
        if label == "C":
            self.expr = ""
            self.expr_var.set(" ")
            self.result_var.set("0")
            return
        if label == "\u232b":  # backspace
            self.expr = self.expr[:-1]
            self._refresh_display()
            return
        if label == "=":
            try:
                to_eval = (
                    self.expr.replace("\u00d7", "*")
                    .replace("\u00f7", "/")
                    .replace("\u2212", "-")
                    .replace("\u221a(", "sqrt(")
                )
                value = safe_eval(to_eval)
                self.expr_var.set(self.expr + " =")
                self.result_var.set(str(round(value, 10)))
                self.expr = str(value)
            except Exception:
                self.result_var.set("Error")
            return
        if label == "%":
            num, start, end = self._trailing_number()
            if num is not None:
                self.expr = self.expr[:start] + f"({num}/100)"
            self._refresh_display()
            return
        if label == "\u00b1":  # ±
            num, start, end = self._trailing_number()
            if num is not None:
                flipped = num[1:] if num.startswith("-") else "-" + num
                self.expr = self.expr[:start] + flipped
            elif self.expr == "":
                self.expr = "-"
            self._refresh_display()
            return
        if label == "x\u00b2":
            num, start, end = self._trailing_number()
            if num is not None:
                self.expr = self.expr[:start] + f"({num}^2)"
            self._refresh_display()
            return
        if label == "\u221a":  # √
            self.expr += "\u221a("
            self._refresh_display()
            return

        self.expr += label
        self._refresh_display()

    def _on_keypress(self, event):
        key_map = {"*": "\u00d7", "/": "\u00f7", "-": "\u2212"}
        ch = event.char
        if ch and (ch.isdigit() or ch in ".()+-*/"):
            self._handle_key(key_map.get(ch, ch))
        elif event.keysym == "Return":
            self._handle_key("=")
        elif event.keysym == "BackSpace":
            self._handle_key("\u232b")
        elif event.keysym == "Escape":
            self._handle_key("C")
        elif ch == "%":
            self._handle_key("%")

    # ---------------------- Tab Grafik ----------------------
    def _build_graph(self, parent):
        controls = tk.Frame(parent, bg=PANEL)
        controls.pack(fill="x", padx=16, pady=(16, 8))

        tk.Label(
            controls, text="y =", bg=PANEL, fg=SUB, font=("Consolas", 12)
        ).pack(side="left")

        self.fn_var = tk.StringVar(value="sin(x)")
        entry = tk.Entry(
            controls, textvariable=self.fn_var, bg=PANEL2, fg=TEXT,
            insertbackground=TEXT, font=("Consolas", 12), relief="flat",
        )
        entry.pack(side="left", fill="x", expand=True, padx=8, ipady=6)
        entry.bind("<Return>", lambda e: self._plot())

        plot_btn = tk.Button(
            controls, text="Plot", bg=ACCENT, fg="#0b0f12",
            font=("Consolas", 11, "bold"), relief="flat",
            command=self._plot,
        )
        plot_btn.pack(side="left", padx=(0, 0))

        self.figure = Figure(figsize=(4, 3.4), dpi=100, facecolor=PANEL2)
        self.ax = self.figure.add_subplot(111)
        self._style_axes()

        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=16, pady=8)

        # Toolbar bawaan Matplotlib: sudah mendukung pan & zoom
        toolbar_frame = tk.Frame(parent, bg=PANEL)
        toolbar_frame.pack(fill="x", padx=16, pady=(0, 12))
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.config(background=PANEL)
        toolbar.update()

        self.error_var = tk.StringVar(value="")
        tk.Label(
            parent, textvariable=self.error_var, bg=PANEL, fg=DANGER,
            font=("Consolas", 10),
        ).pack(fill="x", padx=16)

        self._plot()

    def _style_axes(self):
        self.ax.set_facecolor(PANEL2)
        self.ax.tick_params(colors=SUB, labelsize=8)
        for spine in self.ax.spines.values():
            spine.set_color(SUB)
        self.ax.axhline(0, color=SUB, linewidth=1)
        self.ax.axvline(0, color=SUB, linewidth=1)
        self.ax.grid(True, color="#2a3040", linewidth=0.6)

    def _plot(self):
        expr = self.fn_var.get().strip() or "x"
        xs = np.linspace(-10, 10, 800)
        ys = []
        try:
            for xv in xs:
                try:
                    ys.append(safe_eval(expr, x_value=float(xv)))
                except Exception:
                    ys.append(float("nan"))
            self.error_var.set("")
        except Exception:
            self.error_var.set("Fungsi tidak valid")
            return

        self.ax.clear()
        self._style_axes()
        self.ax.plot(xs, ys, color=ACCENT, linewidth=2)
        self.ax.set_xlim(-10, 10)
        finite_ys = [y for y in ys if math.isfinite(y)]
        if finite_ys:
            margin = max(1.0, (max(finite_ys) - min(finite_ys)) * 0.1)
            self.ax.set_ylim(min(finite_ys) - margin, max(finite_ys) + margin)
        self.canvas.draw()


if __name__ == "__main__":
    app = CalculatorGraphApp()
    app.mainloop()
