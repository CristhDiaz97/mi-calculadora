"""Interfaz gráfica de la calculadora con CustomTkinter."""
import re

import customtkinter as ctk

import theme as t
from engine import CalcError, evaluate, format_number

OPERATORS = "+−×÷"

# (texto, tipo) por fila
LAYOUT = [
    [("C", "func"), ("⌫", "func"), ("%", "func"), ("÷", "op")],
    [("7", "digit"), ("8", "digit"), ("9", "digit"), ("×", "op")],
    [("4", "digit"), ("5", "digit"), ("6", "digit"), ("−", "op")],
    [("1", "digit"), ("2", "digit"), ("3", "digit"), ("+", "op")],
    [("±", "func"), ("0", "digit"), (".", "digit"), ("=", "equals")],
]

KEY_MAP = {"*": "×", "/": "÷", "-": "−", "+": "+", ",": "."}


def font(size, weight="normal"):
    return ctk.CTkFont(family=t.FONT_FAMILY, size=size, weight=weight)


class CalculatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title("Calculadora")
        self.configure(fg_color=t.BG)
        self.minsize(320, 520)

        self.expr = ""              # expresión en pantalla
        self.just_evaluated = False  # True justo después de pulsar "="
        self.last_op = None          # (operador, operando) para repetir "="
        self.history = []            # [(expresión, resultado)]
        self.history_visible = False
        self.shown_expr = ""         # línea superior tras pulsar "="

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_calculator()
        self._build_history()
        self._bind_keys()
        self._resize_window()
        self._refresh()

    # ---------- Construcción ----------

    def _build_calculator(self):
        calc = ctk.CTkFrame(self, fg_color="transparent")
        calc.grid(row=0, column=0, sticky="nsew", padx=14, pady=14)
        calc.grid_columnconfigure(0, weight=1)
        calc.grid_rowconfigure(2, weight=1)

        # Barra superior: tema e historial
        top = ctk.CTkFrame(calc, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew")
        self.theme_switch = ctk.CTkSwitch(
            top, text="🌙 Oscuro", font=font(13), command=self._toggle_theme,
            progress_color=t.ACCENT, text_color=t.TEXT_MUTED,
        )
        self.theme_switch.select()
        self.theme_switch.pack(side="left")
        self.history_btn = ctk.CTkButton(
            top, text="🕘 Historial", width=110, height=30, corner_radius=15,
            font=font(13), fg_color=t.BUTTON_STYLES["func"][0],
            hover_color=t.BUTTON_STYLES["func"][1], text_color=t.TEXT,
            command=self._toggle_history,
        )
        self.history_btn.pack(side="right")

        # Pantalla
        display = ctk.CTkFrame(calc, fg_color=t.PANEL, corner_radius=t.CORNER_RADIUS)
        display.grid(row=1, column=0, sticky="ew", pady=(12, 12))
        display.grid_columnconfigure(0, weight=1)
        self.expr_label = ctk.CTkLabel(
            display, text="", anchor="e", font=font(t.EXPR_FONT_SIZE),
            text_color=t.TEXT_MUTED, height=28,
        )
        self.expr_label.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 0))
        self.result_label = ctk.CTkLabel(
            display, text="0", anchor="e", font=font(t.RESULT_FONT_MAX, "bold"),
            text_color=t.TEXT, height=70,
        )
        self.result_label.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 14))

        # Teclado
        pad = ctk.CTkFrame(calc, fg_color="transparent")
        pad.grid(row=2, column=0, sticky="nsew")
        for c in range(4):
            pad.grid_columnconfigure(c, weight=1, uniform="col")
        for r, row in enumerate(LAYOUT):
            pad.grid_rowconfigure(r, weight=1, uniform="row")
            for c, (label, kind) in enumerate(row):
                fg, hover, text_color = t.BUTTON_STYLES[kind]
                size = t.BUTTON_FONT_SIZE + (4 if kind in ("op", "equals") else 0)
                ctk.CTkButton(
                    pad, text=label, fg_color=fg, hover_color=hover,
                    text_color=text_color, corner_radius=t.CORNER_RADIUS,
                    font=font(size, "bold" if kind != "digit" else "normal"),
                    command=lambda v=label: self.press(v),
                ).grid(row=r, column=c, sticky="nsew", padx=5, pady=5)

    def _build_history(self):
        self.history_frame = ctk.CTkFrame(
            self, fg_color=t.PANEL, corner_radius=t.CORNER_RADIUS, width=t.HISTORY_WIDTH,
        )
        self.history_frame.grid_rowconfigure(1, weight=1)
        self.history_frame.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self.history_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 6))
        ctk.CTkLabel(header, text="Historial", font=font(18, "bold"),
                     text_color=t.TEXT).pack(side="left")
        ctk.CTkButton(
            header, text="Borrar", width=64, height=26, corner_radius=13,
            font=font(12), fg_color="transparent", border_width=1,
            border_color=t.ACCENT, text_color=t.ACCENT,
            hover_color=t.BUTTON_STYLES["op"][0], command=self._clear_history,
        ).pack(side="right")

        self.history_list = ctk.CTkScrollableFrame(self.history_frame, fg_color="transparent")
        self.history_list.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 10))
        self.history_list.grid_columnconfigure(0, weight=1)
        self._render_history()

    def _bind_keys(self):
        self.bind("<Key>", self._on_key)
        self.bind("<Return>", lambda e: self.press("="))
        self.bind("<KP_Enter>", lambda e: self.press("="))
        self.bind("<BackSpace>", lambda e: self.press("⌫"))
        self.bind("<Delete>", lambda e: self.press("C"))
        self.bind("<Escape>", lambda e: self.press("C"))
        self.bind("<Control-c>", lambda e: self._copy_result())

    # ---------- Lógica de botones ----------

    def press(self, key):
        handlers = {
            "C": self._clear, "⌫": self._backspace, "=": self._equals,
            "±": self._negate, "%": self._percent, ".": self._decimal,
        }
        if key in handlers:
            handlers[key]()
        elif key in OPERATORS:
            self._operator(key)
        elif key.isdigit():
            self._digit(key)
        self._refresh()

    def _start_from_result(self, keep):
        """Tras '=', decide si seguir con el resultado o empezar de cero."""
        if self.just_evaluated:
            self.just_evaluated = False
            if not keep:
                self.expr = ""
            elif self.expr.startswith("Error"):
                self.expr = ""

    def _digit(self, d):
        self._start_from_result(keep=False)
        if self.expr.endswith("%") or self.expr.endswith(")"):
            self.expr += "×"
        # Evita ceros a la izquierda como "007"
        if re.search(r"(^|[+−×÷(])0$", self.expr):
            self.expr = self.expr[:-1]
        self.expr += d

    def _decimal(self):
        self._start_from_result(keep=False)
        current = re.search(r"[\d.]*$", self.expr).group()
        if "." in current:
            return
        if self.expr.endswith("%") or self.expr.endswith(")"):
            self.expr += "×"
        self.expr += "0." if not current else "."

    def _operator(self, op):
        self._start_from_result(keep=True)
        if not self.expr:
            if op == "−":
                self.expr = "−"
            else:
                self.expr = "0" + op
            return
        if self.expr[-1] in OPERATORS:
            if self.expr == "−":
                return
            self.expr = self.expr[:-1] + op
        else:
            self.expr += op

    def _percent(self):
        self._start_from_result(keep=True)
        if self.expr and (self.expr[-1].isdigit() or self.expr[-1] == "."):
            self.expr += "%"

    def _negate(self):
        self._start_from_result(keep=True)
        m = re.search(r"\(−([\d.]+%?)\)$", self.expr)
        if m:
            self.expr = self.expr[: m.start()] + m.group(1)
            return
        m = re.search(r"^−([\d.e+]+%?)$", self.expr)
        if m:
            self.expr = m.group(1)
            return
        m = re.search(r"[\d.]+(e[+−]\d+)?%?$", self.expr)
        if m:
            prefix = self.expr[: m.start()]
            self.expr = ("−" + m.group()) if not prefix else f"{prefix}(−{m.group()})"

    def _backspace(self):
        if self.just_evaluated:
            self.just_evaluated = False
            return
        self.expr = self.expr[:-1]

    def _clear(self):
        self.expr = ""
        self.just_evaluated = False
        self.last_op = None

    def _equals(self):
        if self.just_evaluated:
            # Repetir la última operación: 5 + 3 = = = -> 8, 11, 14
            if not self.last_op or self.expr.startswith("Error"):
                return
            expr = self.expr + self.last_op[0] + self.last_op[1]
        else:
            expr = self.expr.rstrip(OPERATORS)
            if not expr:
                return
            m = re.search(r"([+−×÷])(\(?−?[\d.]+%?\)?)$", expr)
            self.last_op = (m.group(1), m.group(2)) if m else None
        try:
            result = format_number(evaluate(expr))
        except CalcError as err:
            self.shown_expr = expr + " ="
            self.expr = f"Error: {err}"
            self.just_evaluated = True
            self.last_op = None
            return
        self._add_history(expr, result)
        self.shown_expr = expr + " ="
        self.expr = result
        self.just_evaluated = True

    # ---------- Pantalla ----------

    def _refresh(self):
        if self.just_evaluated:
            self.expr_label.configure(text=self.shown_expr)
            result_text = self.expr
            self.result_label.configure(text_color=t.ACCENT if not self.expr.startswith("Error") else ("#D93025", "#FF6B6B"))
        else:
            self.shown_expr = ""
            result_text = self.expr or "0"
            self.result_label.configure(text_color=t.TEXT)
            # Vista previa del resultado mientras se escribe
            preview = ""
            if any(op in self.expr[1:] for op in OPERATORS) or "%" in self.expr:
                try:
                    preview = "= " + format_number(evaluate(self.expr.rstrip(OPERATORS)))
                except CalcError:
                    pass
            self.expr_label.configure(text=preview)

        if result_text.startswith("Error"):
            size = t.RESULT_FONT_MIN
        else:
            size = max(t.RESULT_FONT_MIN, min(t.RESULT_FONT_MAX, int(t.RESULT_FONT_MAX * 11 / max(len(result_text), 11))))
        self.result_label.configure(text=result_text, font=font(size, "bold"))

    # ---------- Historial ----------

    def _add_history(self, expr, result):
        self.history.insert(0, (expr, result))
        del self.history[50:]
        self._render_history()

    def _render_history(self):
        for child in self.history_list.winfo_children():
            child.destroy()
        if not self.history:
            ctk.CTkLabel(self.history_list, text="Aún no hay operaciones",
                         font=font(13), text_color=t.TEXT_MUTED).grid(row=0, column=0, pady=20)
            return
        hover = t.BUTTON_STYLES["digit"][1]
        for i, (expr, result) in enumerate(self.history):
            item = ctk.CTkFrame(self.history_list, fg_color="transparent", corner_radius=10,
                                cursor="hand2")
            item.grid(row=i, column=0, sticky="ew", padx=4, pady=2)
            item.grid_columnconfigure(0, weight=1)
            expr_lbl = ctk.CTkLabel(item, text=f"{expr} =", anchor="e", font=font(13),
                                    text_color=t.TEXT_MUTED, height=20)
            expr_lbl.grid(row=0, column=0, sticky="ew", padx=12, pady=(8, 0))
            res_lbl = ctk.CTkLabel(item, text=result, anchor="e", font=font(20, "bold"),
                                   text_color=t.ACCENT, height=26)
            res_lbl.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))
            for w in (item, expr_lbl, res_lbl):
                w.bind("<Button-1>", lambda e, r=result: self._use_history(r))
                w.bind("<Enter>", lambda e, f=item: f.configure(fg_color=hover))
                w.bind("<Leave>", lambda e, f=item: f.configure(fg_color="transparent"))

    def _use_history(self, result):
        """Inserta un resultado del historial en la expresión actual."""
        if self.just_evaluated or not self.expr or self.expr[-1] not in OPERATORS:
            self.expr = result
            self.just_evaluated = False
        else:
            self.expr += result if not result.startswith("−") else f"({result})"
        self._refresh()

    def _clear_history(self):
        self.history.clear()
        self._render_history()

    def _toggle_history(self):
        self.history_visible = not self.history_visible
        if self.history_visible:
            self.history_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 14), pady=14)
            self.grid_columnconfigure(1, weight=0, minsize=t.HISTORY_WIDTH)
        else:
            self.history_frame.grid_remove()
            self.grid_columnconfigure(1, weight=0, minsize=0)
        self._resize_window()

    # ---------- Varios ----------

    def _resize_window(self):
        width = t.CALC_WIDTH + (t.HISTORY_WIDTH + 14 if self.history_visible else 0)
        self.geometry(f"{width}x{t.WINDOW_HEIGHT}")

    def _toggle_theme(self):
        dark = self.theme_switch.get() == 1
        ctk.set_appearance_mode("dark" if dark else "light")
        self.theme_switch.configure(text="🌙 Oscuro" if dark else "☀️ Claro")

    def _on_key(self, event):
        char = KEY_MAP.get(event.char, event.char)
        if char and (char.isdigit() or char in OPERATORS or char in ".%"):
            self.press(char)

    def _copy_result(self):
        text = self.result_label.cget("text")
        if text and not text.startswith("Error"):
            self.clipboard_clear()
            self.clipboard_append(text.replace("−", "-"))
