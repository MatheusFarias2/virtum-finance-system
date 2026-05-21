from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import QMessageBox


def money(valor: float) -> str:
    texto = f"R$ {float(valor):,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def parse_money(texto: str) -> float:
    value = (texto or "").strip().replace("R$", "").replace(" ", "")
    if not value:
        raise ValueError("Valor vazio.")

    if "," in value and "." in value:
        value = value.replace(".", "").replace(",", ".")
    else:
        value = value.replace(",", ".")

    return float(value)


def br_date(iso: str) -> str:
    return datetime.strptime(iso, "%Y-%m-%d").strftime("%d/%m/%Y")


def iso_date(br: str) -> str:
    return datetime.strptime((br or "").strip(), "%d/%m/%Y").date().isoformat()


def msg_err(parent, title, text):
    QMessageBox.critical(parent, title, text)


def msg_yesno(parent, title, text) -> bool:
    return QMessageBox.question(parent, title, text, QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes
