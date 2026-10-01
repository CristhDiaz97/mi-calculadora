"""Colores, fuentes y medidas. Cada color es (modo claro, modo oscuro)."""

FONT_FAMILY = "Segoe UI"

BG = ("#F2F2F7", "#121214")
PANEL = ("#FFFFFF", "#1C1C1F")
TEXT = ("#1C1C1E", "#F5F5F7")
TEXT_MUTED = ("#8A8A8E", "#8E8E93")

ACCENT = ("#FF8A00", "#FF9F0A")
ACCENT_HOVER = ("#E67A00", "#FFB340")
ACCENT_TEXT = ("#FFFFFF", "#FFFFFF")

BUTTON_STYLES = {
    # tipo: (fondo, hover, texto)
    "digit": (("#FFFFFF", "#2C2C30"), ("#E5E5EA", "#3A3A3F"), TEXT),
    "func": (("#D8D8DE", "#48484E"), ("#C7C7CD", "#5A5A60"), TEXT),
    "op": (("#FFE2BF", "#3D2A12"), ("#FFD199", "#4E3515"), ACCENT),
    "equals": (ACCENT, ACCENT_HOVER, ACCENT_TEXT),
}

CORNER_RADIUS = 18
BUTTON_FONT_SIZE = 24
RESULT_FONT_MAX = 52
RESULT_FONT_MIN = 22
EXPR_FONT_SIZE = 18

CALC_WIDTH = 380
HISTORY_WIDTH = 260
WINDOW_HEIGHT = 600
