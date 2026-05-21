from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QParallelAnimationGroup, QPoint, QPropertyAnimation, Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..themes import get_theme


class Card(QFrame):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        self.lbl_title = QLabel(title)
        self.lbl_title.setObjectName("CardTitle")
        self.lbl_value = QLabel("—")
        self.lbl_value.setObjectName("CardValue")

        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value)

    def set_value(self, text: str, positive=None):
        self.lbl_value.setText(text)
        if positive is None:
            self.lbl_value.setStyleSheet("")
            return

        theme_key = getattr(self.window(), "theme_key", "original")
        theme = get_theme(theme_key)
        self.lbl_value.setStyleSheet(f"color: {theme['GREEN'] if positive else theme['RED']};")


class SidebarButton(QPushButton):
    def __init__(self, icon_text: str, label: str, parent=None, *, sub: bool = False):
        super().__init__(f"{icon_text}  {label}", parent)
        self.icon_text = icon_text
        self.full_label = label
        self.is_sub_button = bool(sub)
        self.setObjectName("SidebarSubButton" if sub else "SidebarButton")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(34 if sub else 40)
        self.setCheckable(True)
        self.setProperty("collapsed", False)
        self.setToolTip(label)

    def set_collapsed(self, collapsed: bool):
        self.setProperty("collapsed", bool(collapsed))
        if collapsed:
            self.setText(self.icon_text)
            self.setToolTip(self.full_label)
        else:
            self.setText(f"{self.icon_text}  {self.full_label}")
            self.setToolTip("")

        self.style().unpolish(self)
        self.style().polish(self)


class AnimatedStackedWidget(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._animation_group = None
        self._animation_running = False

    def set_current_widget_animated(self, widget: QWidget, direction: int = 1):
        if widget is None:
            return
        if self._animation_running:
            super().setCurrentWidget(widget)
            return
        if widget is self.currentWidget():
            return

        old_widget = self.currentWidget()
        new_widget = widget

        super().setCurrentWidget(new_widget)
        new_widget.raise_()

        if old_widget is None:
            return

        old_effect = QGraphicsOpacityEffect(old_widget)
        new_effect = QGraphicsOpacityEffect(new_widget)
        old_widget.setGraphicsEffect(old_effect)
        new_widget.setGraphicsEffect(new_effect)
        old_effect.setOpacity(1.0)
        new_effect.setOpacity(0.0)

        offset = 24 * (1 if direction >= 0 else -1)
        end_position = new_widget.pos()
        start_position = end_position + QPoint(offset, 0)
        new_widget.move(start_position)

        animation_new_opacity = QPropertyAnimation(new_effect, b"opacity", self)
        animation_new_opacity.setDuration(180)
        animation_new_opacity.setStartValue(0.0)
        animation_new_opacity.setEndValue(1.0)
        animation_new_opacity.setEasingCurve(QEasingCurve.OutCubic)

        animation_old_opacity = QPropertyAnimation(old_effect, b"opacity", self)
        animation_old_opacity.setDuration(160)
        animation_old_opacity.setStartValue(1.0)
        animation_old_opacity.setEndValue(0.0)
        animation_old_opacity.setEasingCurve(QEasingCurve.OutCubic)

        animation_position = QPropertyAnimation(new_widget, b"pos", self)
        animation_position.setDuration(200)
        animation_position.setStartValue(start_position)
        animation_position.setEndValue(end_position)
        animation_position.setEasingCurve(QEasingCurve.OutCubic)

        group = QParallelAnimationGroup(self)
        group.addAnimation(animation_new_opacity)
        group.addAnimation(animation_old_opacity)
        group.addAnimation(animation_position)
        self._animation_group = group
        self._animation_running = True

        def cleanup():
            old_widget.setGraphicsEffect(None)
            new_widget.setGraphicsEffect(None)
            new_widget.move(end_position)
            self._animation_running = False
            self._animation_group = None

        group.finished.connect(cleanup)
        group.start()


class LoadingOverlay(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("LoadingOverlay")
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setVisible(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(1)

        box = QFrame()
        box.setObjectName("LoadingBox")
        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(18, 14, 18, 14)
        box_layout.setSpacing(10)

        self.lbl = QLabel("Carregando…")
        self.lbl.setAlignment(Qt.AlignCenter)

        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        self.bar.setRange(0, 0)

        box_layout.addWidget(self.lbl)
        box_layout.addWidget(self.bar)

        wrap = QHBoxLayout()
        wrap.addStretch(1)
        wrap.addWidget(box)
        wrap.addStretch(1)

        layout.addLayout(wrap)
        layout.addStretch(1)

    def show_over(self, text: str = "Carregando…"):
        self.lbl.setText(text)
        if self.parentWidget() is not None:
            self.setGeometry(self.parentWidget().rect())
        self.raise_()
        self.setVisible(True)
        QApplication.processEvents()

    def hide_over(self):
        self.setVisible(False)


class FormDialog(QDialog):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setObjectName("Modal")
        self.setModal(True)
        self.resize(520, 420)

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(16, 16, 16, 16)
        self.root.setSpacing(12)

        self.box = QFrame()
        self.box.setObjectName("ModalBox")
        self.root.addWidget(self.box)

        self.lay = QVBoxLayout(self.box)
        self.lay.setContentsMargins(14, 14, 14, 14)
        self.lay.setSpacing(10)

        self.actions = QHBoxLayout()
        self.actions.addStretch(1)
        self.root.addLayout(self.actions)

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setObjectName("BtnGhost")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_ok = QPushButton("Salvar")
        self.btn_ok.setObjectName("BtnAccent")
        self.btn_ok.clicked.connect(self.accept)

        self.actions.addWidget(self.btn_cancel)
        self.actions.addWidget(self.btn_ok)
