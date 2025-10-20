from __future__ import annotations
from typing import Literal

import customtkinter as ctk
import platform
import tkinter as tk

# HIG spacing scale
SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 12
SPACING_LG = 16
SPACING_XL = 24

FontMode = Literal["system", "sfpro"]ThemeMode = Literal["system", "light", "dark"]

_current_font_family = None

# Attempt to use SF Pro (user must have installed fonts locally on macOS)
SF_CANDIDATES = ["SF Pro Display","SF Pro Text","SF Pro","SFProDisplay-Regular",
    "SFNS Display","San Francisco",
]


def detect_sf_pro(root: tk.Misc) -> str | None:
    """Выполняет detect sf pro."""
    families = set(tk.font.families(root))  # type: ignore[attr-defined]
    for cand in SF_CANDIDATES:
        if cand in families:
            return cand
    return None

def apply_font(root: tk.Misc, mode: FontMode = "sfpro"):
    """Выполняет apply font."""
    global _current_font_familyif mode == "sfpro" and platform.system() == "Darwin":
        fam = detect_sf_pro(root)
        if fam:
            _current_font_family = fambase_family = _current_font_family or "Helvetica"
    # Configure base sizes (HIG-ish)
    base_cfg = {"CTkLabel": (base_family,13),"CTkButton": (base_family,14),
        "CTkEntry": (base_family,13),"CTkTextbox": (base_family,12),
    }
    for widget_class, font_tuple in base_cfg.items():ctk.ThemeManager.theme["CTkFont"][widget_class] = font_tuple  # type: ignore

def set_theme(mode: ThemeMode = "system"):
    """Выполняет set theme."""
    ctk.set_appearance_mode(mode)
