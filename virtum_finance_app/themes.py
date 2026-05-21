from __future__ import annotations

from .constants import PALETAS


def get_theme(theme_key: str) -> dict:
    return PALETAS.get(theme_key or "original", PALETAS["original"])


def build_stylesheet(theme_key: str) -> str:
    t = get_theme(theme_key)
    return f"""
        QMainWindow {{ background: {t["BG"]}; }}
        QWidget {{ color: {t["TEXT"]}; font-family: "Segoe UI"; font-size: 10pt; }}
        QDialog {{ background: {t["BG"]}; }}

        QToolTip {{
            background: {t["CARD"]};
            color: {t["TEXT"]};
            border: 1px solid {t["BORDER"]};
            padding: 6px;
            border-radius: 6px;
        }}

        QMenuBar {{
            background: {t["CARD"]};
            border-bottom: 1px solid {t["BORDER"]};
        }}
        QMenuBar::item {{
            background: transparent;
            padding: 6px 10px;
            margin: 2px 4px;
            border-radius: 8px;
            color: {t["TEXT"]};
        }}
        QMenuBar::item:selected {{ background: {t["HOVER_BG"]}; }}
        QMenuBar::item:pressed {{ background: {t["ACCENT"]}; color: white; }}

        #Sidebar {{
            background: {t["CARD"]};
            border-right: 1px solid {t["BORDER"]};
        }}

        #H1 {{ font-size: 16pt; font-weight: 700; }}
        #H2 {{ font-size: 13pt; font-weight: 700; }}
        #Subtle {{ color: {t["SUB"]}; }}

        #Card {{
            background: {t["CARD"]};
            border: 1px solid {t["BORDER"]};
            border-radius: 12px;
        }}
        #CardTitle {{ color: {t["SUB"]}; font-size: 10pt; }}
        #CardValue {{ font-size: 20pt; font-weight: 700; }}

        #Panel {{
            background: {t["PANEL"]};
            border: 1px solid {t["BORDER"]};
            border-radius: 12px;
        }}
        #PanelTitle {{ font-size: 11pt; font-weight: 700; }}

        #BtnAccent {{
            background: {t["ACCENT"]};
            border: 0px;
            border-radius: 10px;
            padding: 10px 14px;
            color: white;
            font-weight: 600;
        }}
        #BtnAccent:hover {{ background: {t["ACCENT_2"]}; }}
        #BtnAccent:pressed {{ background: {t["ACCENT_2"]}; padding-top: 11px; }}

        #BtnGhost {{
            background: {t["PANEL"]};
            border: 1px solid {t["BORDER"]};
            border-radius: 10px;
            padding: 8px 12px;
            color: {t["TEXT"]};
        }}
        #BtnGhost:hover {{ background: {t["HOVER_BG"]}; }}
        #BtnGhost:pressed {{ background: {t["HOVER_BG"]}; padding-top: 9px; }}

        #BtnGhostDanger {{
            background: {t["PANEL"]};
            border: 1px solid {t["BORDER"]};
            border-radius: 10px;
            padding: 8px 12px;
            color: {t["RED"]};
            font-weight: 600;
        }}
        #BtnGhostDanger:hover {{ background: {t["HOVER_BG"]}; }}
        #BtnGhostDanger:pressed {{ background: {t["HOVER_BG"]}; padding-top: 9px; }}

        #SidebarButton {{
            background: transparent;
            border: 1px solid transparent;
            border-radius: 10px;
            padding: 10px 12px;
            text-align: left;
            color: {t["TEXT"]};
        }}
        #SidebarButton:hover {{
            background: {t["HOVER_BG"]};
            border: 1px solid {t["BORDER"]};
        }}
        #SidebarButton:pressed {{ background: {t["HOVER_BG"]}; }}
        #SidebarButton:checked {{
            background: {t["ACCENT"]};
            border: 1px solid {t["ACCENT"]};
            color: white;
            font-weight: 600;
        }}
        #SidebarButton[collapsed="true"] {{
            text-align: center;
            padding-left: 0px;
            padding-right: 0px;
        }}

        #SidebarGroupBody {{
            background: transparent;
            border: 0px;
        }}

        #SidebarSubButton {{
            background: transparent;
            border: 1px solid transparent;
            border-radius: 9px;
            padding: 7px 10px 7px 24px;
            text-align: left;
            color: {t["SUB"]};
            font-size: 9.5pt;
        }}
        #SidebarSubButton:hover {{
            background: {t["HOVER_BG"]};
            border: 1px solid {t["BORDER"]};
            color: {t["TEXT"]};
        }}
        #SidebarSubButton:checked {{
            background: {t["ACCENT"]};
            border: 1px solid {t["ACCENT"]};
            color: white;
            font-weight: 600;
        }}
        #SidebarSubButton[collapsed="true"] {{
            text-align: center;
            padding-left: 0px;
            padding-right: 0px;
        }}


        QTabWidget::pane {{
            border: 1px solid {t["BORDER"]};
            border-radius: 12px;
            background: {t["PANEL"]};
            top: -1px;
        }}
        QTabBar::tab {{
            background: {t["CARD"]};
            color: {t["SUB"]};
            border: 1px solid {t["BORDER"]};
            border-bottom: 0px;
            padding: 9px 14px;
            margin-right: 4px;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        }}
        QTabBar::tab:selected {{
            background: {t["ACCENT"]};
            color: white;
            font-weight: 600;
        }}
        QTabBar::tab:hover {{
            background: {t["HOVER_BG"]};
            color: {t["TEXT"]};
        }}

        QTableWidget {{
            background: {t["PANEL"]};
            alternate-background-color: {t["ALT_ROW"]};
            border: 1px solid {t["BORDER"]};
            border-radius: 10px;
            gridline-color: {t["BORDER"]};
            color: {t["TEXT"]};
        }}
        QTableCornerButton::section {{
            background: {t["CARD"]};
            border: 0px;
        }}
        QTableWidget::item {{
            padding: 6px;
            color: {t["TEXT"]};
            background: transparent;
        }}
        QTableWidget::item:selected {{
            background: {t["ACCENT"]};
            color: white;
        }}
        QHeaderView::section {{
            background: {t["CARD"]};
            color: {t["TEXT"]};
            padding: 8px;
            border: 0px;
            border-bottom: 1px solid {t["BORDER"]};
        }}

        QLineEdit, QComboBox {{
            background: {t["BG"]};
            border: 1px solid {t["BORDER"]};
            border-radius: 10px;
            padding: 10px 10px;
            color: {t["TEXT"]};
            selection-background-color: {t["ACCENT"]};
            selection-color: white;
        }}
        QLineEdit:focus, QComboBox:focus {{ border: 1px solid {t["ACCENT"]}; }}
        QComboBox QAbstractItemView {{
            background: {t["PANEL"]};
            color: {t["TEXT"]};
            selection-background-color: {t["ACCENT"]};
            selection-color: white;
            border: 1px solid {t["BORDER"]};
        }}

        #InlineBox {{ background: transparent; }}

        #LoadingOverlay {{ background: rgba(0, 0, 0, 0.35); }}
        #LoadingBox {{
            background: {t["CARD"]};
            border: 1px solid {t["BORDER"]};
            border-radius: 14px;
        }}
        #LoadingBox QLabel {{ font-size: 11pt; font-weight: 700; }}
        QProgressBar {{
            background: {t["BG"]};
            border: 1px solid {t["BORDER"]};
            border-radius: 6px;
            min-height: 10px;
        }}
        QProgressBar::chunk {{
            background: {t["ACCENT"]};
            border-radius: 6px;
        }}


        #HeroPanel {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {t["ACCENT"]}, stop:0.55 {t["CARD"]}, stop:1 {t["PANEL"]});
            border: 1px solid {t["BORDER"]};
            border-radius: 18px;
        }}
        #HeroEmoji {{
            font-size: 44pt;
            min-width: 76px;
            color: white;
        }}
        #HeroTitle {{
            font-size: 19pt;
            font-weight: 800;
            color: white;
        }}
        #HeroSubtitle {{
            color: {t["TEXT"]};
            font-size: 10pt;
        }}
        #Badge {{
            background: {t["CARD"]};
            border: 1px solid {t["BORDER"]};
            border-radius: 999px;
            padding: 7px 12px;
            color: {t["TEXT"]};
            font-weight: 600;
        }}
        #MetricBox {{
            background: rgba(0, 0, 0, 0.18);
            border: 1px solid {t["BORDER"]};
            border-radius: 14px;
        }}
        #MetricTitle {{
            color: {t["SUB"]};
            font-size: 9.5pt;
        }}
        #MetricValue {{
            color: {t["TEXT"]};
            font-size: 12pt;
            font-weight: 800;
        }}
        #MissionMiniCard {{
            background: {t["CARD"]};
            border: 1px solid {t["BORDER"]};
            border-radius: 14px;
        }}
        #MissionMiniCard[done="true"] {{
            background: {t["HOVER_BG"]};
            border: 1px solid {t["GREEN"]};
        }}
        #MissionTitle {{
            color: {t["TEXT"]};
            font-weight: 700;
        }}
        #MissionStatus {{
            color: {t["SUB"]};
            font-size: 9.5pt;
        }}
        #InfoLine {{
            background: {t["CARD"]};
            border: 1px solid {t["BORDER"]};
            border-radius: 12px;
            padding: 10px 12px;
            color: {t["TEXT"]};
        }}

        #ModalBox {{
            background: {t["PANEL"]};
            border: 1px solid {t["BORDER"]};
            border-radius: 12px;
        }}
    """
