"""Motor de cálculo: evalúa expresiones de forma segura (sin eval)."""
import ast
import operator
import re

# Símbolos que muestra la interfaz -> símbolos de Python
_DISPLAY_TO_PY = {"×": "*", "÷": "/", "−": "-"}

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
_UNARY_OPS = {ast.USub: operator.neg, ast.UAdd: operator.pos}


class CalcError(Exception):
    """Error de cálculo con un mensaje apto para mostrar al usuario."""


def to_python(expr: str) -> str:
    for disp, py in _DISPLAY_TO_PY.items():
        expr = expr.replace(disp, py)
    # "50%" -> "(50/100)"
    return re.sub(r"(\d+(?:\.\d*)?)%", r"(\1/100)", expr)


def _eval_node(node):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval_node(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        left, right = _eval_node(node.left), _eval_node(node.right)
        if isinstance(node.op, ast.Div) and right == 0:
            raise CalcError("No se puede dividir entre 0")
        return _BIN_OPS[type(node.op)](left, right)
    raise CalcError("Expresión no válida")


def evaluate(expr: str) -> float:
    """Evalúa una expresión en formato de pantalla y devuelve el número."""
    expr = expr.strip()
    if not expr:
        raise CalcError("Expresión vacía")
    try:
        tree = ast.parse(to_python(expr), mode="eval")
    except SyntaxError:
        raise CalcError("Expresión incompleta") from None
    try:
        result = _eval_node(tree)
    except OverflowError:
        raise CalcError("Número demasiado grande") from None
    if isinstance(result, float) and (result != result or result in (float("inf"), float("-inf"))):
        raise CalcError("Número demasiado grande")
    return result


def format_number(value) -> str:
    """Formatea el resultado: sin '.0' sobrante y con 12 cifras significativas."""
    if isinstance(value, float) and value.is_integer() and abs(value) < 1e15:
        value = int(value)
    if isinstance(value, int):
        if abs(value) >= 1e15:
            return f"{value:.10g}".replace("-", "−")
        return str(value).replace("-", "−")
    text = f"{value:.12g}"
    return text.replace("-", "−")
