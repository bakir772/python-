#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
الآلة الحاسبة العلمية - Scientific Calculator
=============================================
تطبيق آلة حاسبة احترافي مبني بمكتبة tkinter.
"""

from __future__ import annotations

import ast
import math
import operator
import re
import tkinter as tk
from dataclasses import dataclass
from functools import partial
from typing import Callable

# ==========================================
# الجزء الأول: محرك الحساب (منفصل تماماً عن الواجهة)
# ==========================================

class CalculatorError(Exception):
    """خطأ حسابي يحمل رسالة مفهومة للمستخدم."""
    pass

class ExpressionEvaluator:
    """تقييم التعبيرات الرياضية بأمان عبر شجرة الصياغة ast بدل eval."""
    
    MAX_EXPONENT = 10_000
    MAX_FACTORIAL = 170

    _BINARY_OPS: dict[type, Callable] = {
        ast.Add: operator.add,       # جمع القيم
        ast.Sub: operator.sub,       # طرح القيم
        ast.Mult: operator.mul,      # ضرب القيم
        ast.Div: operator.truediv,   # قسمة القيم
        ast.Pow: operator.pow,       # رفع الأسس
    }

    _UNARY_OPS: dict[type, Callable] = {
        ast.UAdd: operator.pos,      # الإشارة الموجبة
        ast.USub: operator.neg,      # الإشارة السالبة (عكس الإشارة)
    }

    _CONSTANTS = {"pi": math.pi, "e": math.e}

    def __init__(self) -> None:
        self.degrees = True  # True = درجات، False = راديان
        self._functions: dict[str, Callable] = {
            "sin": self._sin,
            "cos": self._cos,
            "tan": self._tan,
            "ln": math.log,
            "log": math.log10,
            "sqrt": math.sqrt,
            "root": self._root,
            "fact": self._factorial,
        }

    def evaluate(self, expression: str) -> float | int:
        """يحسب قيمة التعبير أو يرفع CalculatorError برسالة عربية."""
        prepared = self._preprocess(expression)
        try:
            tree = ast.parse(prepared, mode="eval")
            result = self._eval_node(tree.body)
        except CalculatorError:
            raise
        except SyntaxError as exc:
            raise CalculatorError("صيغة غير صحيحة") from exc
        except ZeroDivisionError as exc:
            raise CalculatorError("لا يمكن القسمة على صفر") from exc
        except OverflowError as exc:
            raise CalculatorError("النتيجة كبيرة جداً") from exc
        except ValueError as exc:
            raise CalculatorError("قيمة خارج نطاق الدالة") from exc
        except RecursionError as exc:
            raise CalculatorError("التعبير معقد جدًا") from exc

        if isinstance(result, complex):
            raise CalculatorError("النتيجة عدد مركب (غير مدعوم)")
        return result

    @staticmethod
    def format_result(value: float | int) -> str:
        """تنسيق النتيجة للعرض: أعداد صحيحة كاملة، وأرقام معنوية للكسور."""
        try:
            if isinstance(value, int) and abs(value) < 10 ** 15:
                return str(value)
            number = float(value)
        except OverflowError as exc:
            raise CalculatorError("النتيجة كبيرة جداً") from exc

        if math.isnan(number) or math.isinf(number):
            raise CalculatorError("النتيجة غير معرفة")

        if number.is_integer() and abs(number) < 1e15:
            return str(int(number))

        text = f"{number:.12g}"
        if "e" in text:
            mantissa, exponent = text.split("e")
            return f"({mantissa} × 10^{int(exponent)})"
        return text

    @staticmethod
    def _preprocess(expression: str) -> str:
        """المعالجة المسبقة للنص قبل تمريره للمحرك الرياضي."""
        text = expression.replace(" ", "")
        text = re.sub(r'(\d+(?:\.\d+)?)\%', r'(\1/100)', text)
        text = re.sub(r'√(\d+(?:\.\d+)?)', r'sqrt(\1)', text)
        text = text.replace("√", "sqrt")
        
        for old, new in (("×", "*"), ("÷", "/"), ("−", "-"), ("^", "**"), ("π", "pi")):
            text = text.replace(old, new)

        text = re.sub(r'(?<=[\d)])(?=[A-Za-z(])', '*', text)
        text = re.sub(r'(?<=\d)(?=\()', '*', text)
        text = re.sub(r'(?<=pi)(?=\d)', '*', text)
        return text

    def _eval_node(self, node: ast.AST):
        """تقييم العقد الشجيرية المأمونة بأمان عبر AST."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
                return node.value
            raise CalculatorError("قيمة غير مسموحة")

        if isinstance(node, ast.Name):
            if node.id in self._CONSTANTS:
                return self._CONSTANTS[node.id]
            raise CalculatorError(f"رمز غير معروف: {node.id}")

        if isinstance(node, ast.UnaryOp) and type(node.op) in self._UNARY_OPS:
            return self._UNARY_OPS[type(node.op)](self._eval_node(node.operand))

        # تم التصحيح هنا من Binop إلى BinOp
        if isinstance(node, ast.BinOp) and type(node.op) in self._BINARY_OPS:
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            if isinstance(node.op, ast.Pow):
                self._validate_power(left, right)
            return self._BINARY_OPS[type(node.op)](left, right)

        if isinstance(node, ast.Call):
            return self._eval_call(node)

        raise CalculatorError("عملية غير مدعومة")

    def _eval_call(self, node: ast.Call):
        """تنفيذ استدعاء الدوال الرياضية مثل sin و log وغيرها."""
        if not isinstance(node.func, ast.Name) or node.func.id not in self._functions or node.keywords:
            raise CalculatorError("دالة غير مدعومة")
        args = [self._eval_node(arg) for arg in node.args]
        try:
            return self._functions[node.func.id](*args)
        except TypeError as exc:
            raise CalculatorError("معاملات الدالة غير صحيحة") from exc

    def _validate_power(self, base, exponent) -> None:
        """التحقق من صحة الأسس لعدم تجاوز الحد الأقصى."""
        if abs(exponent) > self.MAX_EXPONENT:
            raise CalculatorError("الأس كبير جداً")

    def _to_radians(self, x: float) -> float:
        """تحويل الزاوية إلى راديان إذا كانت الإعدادات مفعلة بالدرجات."""
        return math.radians(x) if self.degrees else x

    @staticmethod
    def _clean(value: float) -> float:
        """يزيل أخطاء التقريب الصغيرة جداً مثل sin(180°) = 1e-16."""
        return 0.0 if abs(value) < 1e-12 else value

    def _sin(self, x: float) -> float:
        return self._clean(math.sin(self._to_radians(x)))

    def _cos(self, x: float) -> float:
        return self._clean(math.cos(self._to_radians(x)))

    def _tan(self, x: float) -> float:
        if self.degrees and (x - 90) % 180 == 0:
            raise CalculatorError("الظل غير معرف عند هذه الزاوية")
        return self._clean(math.tan(self._to_radians(x)))

    @staticmethod
    def _root(x: float, n: float) -> float:
        """الجذر النوني: root(x, n) مع دعم الجذور الفردية للأعداد السالبة."""
        if n == 0:
            raise CalculatorError("درجة الجذر لا يمكن أن تكون صفراً")
        is_int_n = float(n).is_integer()
        negative = x < 0
        if negative and not (is_int_n and int(n) % 2 == 1):
            raise CalculatorError("لا يوجد جذر حقيقي لعدد سالب بهذه الدرجة")
        result = abs(x) ** (1 / n)
        if is_int_n and n > 0:
            candidate = round(result)
            if candidate ** int(n) == abs(x):
                result = float(candidate)
        return -result if negative else result

    @classmethod
    def _factorial(cls, x: float) -> int:
        """حساب المضروب مع التحقق من الشروط المسموحة."""
        if not float(x).is_integer() or x < 0 or x > cls.MAX_FACTORIAL:
            raise CalculatorError(f"المضروب يقبل أعداداً صحيحة من 0 إلى {cls.MAX_FACTORIAL}")
        return math.factorial(int(x))


# ==========================================
# الجزء الثاني: المظهر والتخطيط
# ==========================================

@dataclass(frozen=True)
class Theme:
    """ألوان وخطوط الواجهة الرسمية (داكنة هادئة)."""
    bg: str = "#1e2430"
    display_bg: str = "#161b25"
    text: str = "#f1f5f9"
    muted: str = "#8b97a9"
    error: str = "#ef6b6b"
    font: str = "Segoe UI"
    
    digit: tuple = ("#2f3a4d", "#3b485e", "#f1f5f9")
    operator: tuple = ("#3d5a80", "#4a6d9a", "#ffffff")
    func: tuple = ("#252e3d", "#313d51", "#c9d3e0")
    action: tuple = ("#6b3a44", "#824653", "#ffffff")
    equals: tuple = ("#2e7d6b", "#3a9782", "#ffffff")

THEME = Theme()

BUTTON_LAYOUT: list[list[tuple]] = [
    [("DEG", "func", "angle"), ("sin", "func"), ("cos", "func"), ("tan", "func")],
    [("ln", "func"), ("log", "func"), ("π", "func"), ("e", "func")],
    [("√", "func"), ("ⁿ√", "func"), ("x²", "func"), ("xʸ", "func")],
    [("n!", "func"), ("(", "func"), (")", "func"), (",", "func")],
    [("C", "action"), ("⌫", "action"), ("%", "operator"), ("÷", "operator")],
    [("7", "digit"), ("8", "digit"), ("9", "digit"), ("×", "operator")],
    [("4", "digit"), ("5", "digit"), ("6", "digit"), ("−", "operator")],
    [("1", "digit"), ("2", "digit"), ("3", "digit"), ("+", "operator")],
    [("1/x", "func"), ("0", "digit"), (".", "digit"), ("=", "equals")],
]

INSERTIONS: dict[str, tuple[str, bool]] = {
    **{d: (d, True) for d in "0123456789"},
    ".": (".", True), "π": ("π", True), "e": ("e", True),
    "(": ("(", True), ")": (")", False), ",": (",", False),
    "sin": ("sin(", True), "cos": ("cos(", True), "tan": ("tan(", True),
    "ln": ("ln(", True), "log": ("log(", True), "√": ("sqrt(", True),
    "ⁿ√": ("root(", True), "n!": ("fact(", True), "x²": ("^2", False),
    "xʸ": ("^", False), "%": ("%", False), "+": ("+", False),
    "-": ("-", False), "×": ("*", False), "÷": ("/", False),
}

KEY_MAP = {
    **{d: d for d in "0123456789"},
    "+": "+", "-": "-", "*": "×", "/": "÷", ".": ".", ",": ",",
    "(": "(", ")": ")", "%": "%", "!": "n!", "^": "xʸ",
}

OPERATORS = "+-×÷"
FUNCTION_TAIL = re.compile(r"(?:sin|cos|tan|ln|log|root|fact|sqrt)\($")
MAX_EXPRESSION_LENGTH = 200
MAX_HISTORY = 50


# ==========================================
# الجزء الثالث: الواجهة الرسومية (UI)
# ==========================================

class CalculatorApp:
    """النافذة الرئيسية للحاسبة والتحكم بالتفاعل مع المستخدم."""
    
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.evaluator = ExpressionEvaluator()
        self.expression = ""
        self.just_evaluated = False
        self.history_results: list[str] = []

        self.expr_var = tk.StringVar()
        self.preview_var = tk.StringVar()

        self._configure_window()
        
        container = tk.Frame(root, bg=THEME.bg, padx=12, pady=12)
        container.pack()

        calc_frame = tk.Frame(container, bg=THEME.bg)
        calc_frame.grid(row=0, column=0, sticky="n")

        self._build_display(calc_frame)
        self._build_buttons(calc_frame)
        self._build_history(container)
        self._build_status_bar(root)

        root.bind("<Key>", self._on_key)
        self._refresh()

    def _configure_window(self) -> None:
        self.root.title("الآلة الحاسبة العلمية")
        self.root.configure(bg=THEME.bg)
        self.root.resizable(False, False)

    def _build_display(self, parent: tk.Frame) -> None:
        frame = tk.Frame(parent, bg=THEME.display_bg, padx=14, pady=10)
        frame.pack(fill="x", pady=(0, 10))

        self.preview_label = tk.Label(
            frame, textvariable=self.preview_var, anchor="e",
            font=(THEME.font, 12), fg=THEME.muted, bg=THEME.display_bg,
        )
        self.preview_label.pack(fill="x")

        self.expr_label = tk.Label(
            frame, textvariable=self.expr_var, anchor="e", width=22,
            font=(THEME.font, 28, "bold"), fg=THEME.text, bg=THEME.display_bg,
        )
        self.expr_label.pack(fill="x")

    def _build_buttons(self, parent: tk.Frame) -> None:
        grid = tk.Frame(parent, bg=THEME.bg)
        grid.pack()

        for r, row in enumerate(BUTTON_LAYOUT):
            for c, spec in enumerate(row):
                text, kind, *rest = spec
                key = rest[0] if rest else text
                base, hover, fg = getattr(THEME, kind)

                button = tk.Button(
                    grid, text=text, width=5, height=2, relief="flat", bd=0,
                    font=(THEME.font, 13, "bold" if kind in ("equals", "action") else "normal"),
                    bg=base, fg=fg, activebackground=hover, activeforeground=fg,
                    cursor="hand2", command=partial(self._press, key),
                )
                button.grid(row=r, column=c, padx=2, pady=2, sticky="nsew")

                button.bind("<Enter>", lambda e, b=button, col=hover: b.config(bg=col))
                button.bind("<Leave>", lambda e, b=button, col=base: b.config(bg=col))

                if key == "angle":
                    self.angle_button = button

    def _build_history(self, parent: tk.Frame) -> None:
        frame = tk.Frame(parent, bg=THEME.bg, padx=12)
        frame.grid(row=0, column=1, sticky="ns")

        tk.Label(
            frame, text="سجل العمليات", font=(THEME.font, 12, "bold"),
            fg=THEME.text, bg=THEME.bg,
        ).pack(anchor="e", pady=(0, 6))

        self.history_box = tk.Listbox(
            frame, width=26, height=17, bd=0, highlightthickness=0,
            font=(THEME.font, 10), bg=THEME.display_bg, fg=THEME.text,
            selectbackground=THEME.operator[0], activestyle="none",
        )
        self.history_box.pack(fill="y", expand=True)
        self.history_box.bind("<Double-Button-1>", self._on_history_pick)

        tk.Button(
            frame, text="مسح السجل", relief="flat", bd=0, cursor="hand2",
            font=(THEME.font, 10), bg=THEME.func[0], fg=THEME.func[2],
            activebackground=THEME.func[1], activeforeground=THEME.func[2],
            command=self._clear_history,
        ).pack(fill="x", pady=(8, 0))

    def _build_status_bar(self, parent: tk.Tk) -> None:
        tk.Label(
            parent, anchor="e", font=(THEME.font, 9), fg=THEME.muted, bg=THEME.bg,
            text="انقر مرتين على السجل لإعادة استخدام النتيجة | ⁿ√: الجذر النوني",
        ).pack(fill="x", padx=12, pady=(0, 8))

    def _press(self, key: str) -> None:
        if key == "=":
            self._evaluate()
        elif key == "C":
            self._clear()
        elif key == "⌫":
            self._backspace()
        elif key == "angle":
            self._toggle_angle_mode()
        elif key == "1/x":
            self._reciprocal()
        elif key in INSERTIONS:
            token, starts_new = INSERTIONS[key]
            self._insert(token, starts_new)

    def _insert(self, token: str, starts_new: bool) -> None:
        if self.just_evaluated and starts_new:
            self.expression = ""
            self.just_evaluated = False

        if not self.expression and token in "x+*^%),":
            return

        if len(self.expression) + len(token) > MAX_EXPRESSION_LENGTH:
            self._refresh("التعبير طويل جداً", is_error=True)
            return

        if token in OPERATORS and self.expression and self.expression[-1] in OPERATORS and not (token == "-" and self.expression[-1] in "x÷*+"):
            self.expression = self.expression[:-1]

        self.expression += token
        self._refresh()

    def _evaluate(self) -> None:
        if not self.expression:
            return
        try:
            value = self.evaluator.evaluate(self.expression)
            text = self.evaluator.format_result(value)
        except CalculatorError as exc:
            self._refresh(str(exc), is_error=True)
            return

        original = self.expression
        self._add_history(original, text)
        self.expression = text
        self.just_evaluated = True
        self._refresh(f"{original} =")

    def _clear(self) -> None:
        self.expression = ""
        self.just_evaluated = False
        self._refresh()

    def _backspace(self) -> None:
        self.just_evaluated = False
        match = FUNCTION_TAIL.search(self.expression)
        cut = len(match.group()) if match else 1
        self.expression = self.expression[:-cut]
        self._refresh()

    def _reciprocal(self) -> None:
        if not self.expression:
            return
        self.expression = f"1/({self.expression})"
        self.just_evaluated = False
        self._refresh()

    def _toggle_angle_mode(self) -> None:
        self.evaluator.degrees = not self.evaluator.degrees
        self.angle_button.config(text="DEG" if self.evaluator.degrees else "RAD")
        self._refresh()

    def _on_key(self, event: tk.Event) -> str | None:
        if event.keysym in ("Return", "KP_Enter") or event.char == "=":
            self._press("=")
        elif event.keysym == "BackSpace":
            self._press("⌫")
        elif event.keysym == "Escape":
            self._press("C")
        elif event.char in KEY_MAP:
            self._press(KEY_MAP[event.char])
        else:
            return None
        return "break"

    def _add_history(self, expression: str, result: str) -> None:
        self.history_box.insert(0, f"{expression} = {result}")
        self.history_results.insert(0, result)
        if len(self.history_results) > MAX_HISTORY:
            self.history_box.delete(MAX_HISTORY, "end")
            del self.history_results[MAX_HISTORY:]

    def _clear_history(self) -> None:
        self.history_box.delete(0, "end")
        self.history_results.clear()

    def _on_history_pick(self, _event: tk.Event) -> None:
        selection = self.history_box.curselection()
        if selection:
            self._insert(self.history_results[selection[0]], starts_new=True)

    def _refresh(self, message: str | None = None, is_error: bool = False) -> None:
        shown = self.expression or "0"
        if len(shown) > 22:
            shown = "..." + shown[-21:]
        size = 28 if len(shown) <= 14 else (22 if len(shown) <= 18 else 17)
        self.expr_label.config(font=(THEME.font, size, "bold"))
        self.expr_var.set(shown)

        if message is not None:
            self.preview_label.config(fg=THEME.error if is_error else THEME.muted)
            self.preview_var.set(message)
        else:
            self.preview_label.config(fg=THEME.muted)
            self.preview_var.set(self._live_preview())

    def _live_preview(self) -> str:
        if not self.expression or re.fullmatch(r"[\d.]+", self.expression):
            return ""
        try:
            value = self.evaluator.evaluate(self.expression)
            return "= " + self.evaluator.format_result(value)
        except CalculatorError:
            return ""


def main() -> None:
    root = tk.Tk()
    CalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()