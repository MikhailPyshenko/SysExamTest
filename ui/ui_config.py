import customtkinter as ctk

from core.settings import AppSettings


_SCALING_APPLIED = False
_APPLIED_VALUES = (1.0, 1.0)


def apply_global_appearance(settings: AppSettings):
    mode = {
        "dark": "dark",
        "light": "light",
        "system": "system",
    }.get(settings.THEME, "dark")
    ctk.set_appearance_mode(mode)


def apply_adaptive_scaling(root, base_width: int = 1920, force: bool = False):
    """Умеренное масштабирование; применяется один раз, чтобы не было 'скачков'."""
    global _SCALING_APPLIED, _APPLIED_VALUES

    if _SCALING_APPLIED and not force:
        return _APPLIED_VALUES

    screen_width = root.winfo_screenwidth()
    scale = max(0.95, min(1.12, screen_width / base_width))
    font_scale = max(0.95, min(1.16, scale + 0.02))

    ctk.set_widget_scaling(font_scale)
    ctk.set_window_scaling(scale)

    _SCALING_APPLIED = True
    _APPLIED_VALUES = (scale, font_scale)
    return _APPLIED_VALUES


def center_window_adaptive(window, width: int, height: int):
    """Центрирование окна с адаптацией под текущий экран."""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    target_width = min(int(screen_width * 0.92), max(width, int(screen_width * 0.45)))
    target_height = min(int(screen_height * 0.9), max(height, int(screen_height * 0.45)))

    x = (screen_width - target_width) // 2
    y = (screen_height - target_height) // 2

    window.geometry(f"{target_width}x{target_height}+{x}+{y}")
    try:
        window.minsize(min(target_width, width), min(target_height, height))
    except Exception:
        pass
