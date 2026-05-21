import sys
import sqlite3
from datetime import date, datetime

from PySide6.QtCore import Qt, QEasingCurve, QPropertyAnimation, QSize, QParallelAnimationGroup
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QLineEdit, QComboBox, QMessageBox, QSpacerItem,
    QSizePolicy, QStackedWidget, QAbstractItemView
)

# QtCharts pode não vir em algumas instalações. Tentamos importar.
HAS_CHARTS = True
try:
    from PySide6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
except Exception:
    HAS_CHARTS = False

# ======================
# TEMA
# ======================
BG = "#0F1115"
PANEL = "#121723"
CARD = "#161A22"
BORDER = "#232A3A"

ACCENT = "#6C63FF"
ACCENT_2 = "#5B54F0"
HOVER_BG = "#1A2233"

TEXT = "#E6E6E6"
SUB = "#9AA0A6"
GREEN = "#35D07F"
RED = "#FF4D4D"

CATEGORIAS = ["Alimentação", "Transporte", "Contas", "Lazer", "Saúde", "Outros"]


# ======================
# PALETAS (temas)
# ======================
PALETAS = {
    "original": {
        "BG": "#0F1115", "PANEL": "#121723", "CARD": "#161A22", "BORDER": "#232A3A",
        "ACCENT": "#6C63FF", "ACCENT_2": "#5B54F0", "HOVER_BG": "#1A2233",
        "TEXT": "#E6E6E6", "SUB": "#9AA0A6", "GREEN": "#35D07F", "RED": "#FF4D4D",
        "ALT_ROW": "#151C2B",
    },
    "rosa_branco": {
        "BG": "#FFF7FB", "PANEL": "#FFFFFF", "CARD": "#FFFFFF", "BORDER": "#F1D7E6",
        "ACCENT": "#E84AA6", "ACCENT_2": "#D93A95", "HOVER_BG": "#FFE7F3",
        "TEXT": "#2B1E2A", "SUB": "#7B6273", "GREEN": "#1E9E68", "RED": "#D94141",
        "ALT_ROW": "#FFF1F8",
    },
    "azul_noite": {
        "BG": "#0B1020", "PANEL": "#111A33", "CARD": "#141F3D", "BORDER": "#24335E",
        "ACCENT": "#4DA3FF", "ACCENT_2": "#2F8BFF", "HOVER_BG": "#1B2A52",
        "TEXT": "#EAF2FF", "SUB": "#9CB0D1", "GREEN": "#35D07F", "RED": "#FF5C5C",
        "ALT_ROW": "#0F1730",
    },
    "verde_musgo": {
        "BG": "#0E1412", "PANEL": "#121A16", "CARD": "#16221B", "BORDER": "#24362B",
        "ACCENT": "#48C78E", "ACCENT_2": "#39B27B", "HOVER_BG": "#1B2A22",
        "TEXT": "#E7F4ED", "SUB": "#9BB2A7", "GREEN": "#48C78E", "RED": "#FF6B6B",
        "ALT_ROW": "#101A16",
    },
    "laranja_creme": {
        "BG": "#FFF8F0", "PANEL": "#FFFFFF", "CARD": "#FFFFFF", "BORDER": "#F0D6C0",
        "ACCENT": "#F28C28", "ACCENT_2": "#E07B18", "HOVER_BG": "#FFE9D4",
        "TEXT": "#2A2017", "SUB": "#7A6656", "GREEN": "#1E9E68", "RED": "#D94141",
        "ALT_ROW": "#FFF1E4",
    },
    "cinza_lavanda": {
        "BG": "#F5F6FA", "PANEL": "#FFFFFF", "CARD": "#FFFFFF", "BORDER": "#DADDEA",
        "ACCENT": "#6C63FF", "ACCENT_2": "#5B54F0", "HOVER_BG": "#EFF0FF",
        "TEXT": "#1D2130", "SUB": "#6A7287", "GREEN": "#1E9E68", "RED": "#D94141",
        "ALT_ROW": "#F3F4FF",
    },
}


# ======================
# BANCO
# ======================
DB_PATH = "gastos.db"

def conectar():
    return sqlite3.connect(DB_PATH)

def migrar_banco():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS gastos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        categoria TEXT,
        valor REAL,
        descricao TEXT,
        data TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS config (
        id INTEGER PRIMARY KEY,
        salario REAL DEFAULT 0,
        ultimo_mes TEXT DEFAULT ''
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fixos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        categoria TEXT,
        valor REAL,
        descricao TEXT,
        ativo INTEGER DEFAULT 1
    )
    """)

    # registra quais fixos já foram aplicados em cada mês (permite reexecutar sem duplicar)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS fixos_aplicados (
        mes TEXT NOT NULL,
        fixo_id INTEGER NOT NULL,
        PRIMARY KEY (mes, fixo_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS resumo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mes TEXT,
        total REAL,
        saldo REAL
    )
    """)

    # garante unicidade do mês mesmo em bancos antigos
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_resumo_mes ON resumo(mes)")

    cur.execute("INSERT OR IGNORE INTO config (id, salario, ultimo_mes) VALUES (1, 0, '')")

    # coluna tema (paleta)
    cur.execute("PRAGMA table_info(config)")
    cols = [c[1] for c in cur.fetchall()]
    if "tema" not in cols:
        cur.execute("ALTER TABLE config ADD COLUMN tema TEXT DEFAULT 'original'")
        cur.execute("UPDATE config SET tema='original' WHERE tema IS NULL OR tema=''")

    conn.commit()
    conn.close()

def obter_salario():
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT salario FROM config WHERE id=1")
    v = cur.fetchone()[0] or 0
    conn.close()
    return float(v)

def salvar_salario(v: float):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("UPDATE config SET salario=? WHERE id=1", (v,))
    conn.commit()
    conn.close()


def obter_tema() -> str:
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT tema FROM config WHERE id=1")
    row = cur.fetchone()
    conn.close()
    return (row[0] if row and row[0] else "original")

def salvar_tema(nome: str):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("UPDATE config SET tema=? WHERE id=1", (nome,))
    conn.commit()
    conn.close()

def aplicar_fixos_automaticos():
    """
    Aplica gastos fixos no mês atual SEM duplicar.
    - Pode ser executado quantas vezes quiser.
    - Se você criar um fixo no meio do mês, ele será aplicado na hora (na próxima execução).
    """
    hoje_mes = date.today().strftime("%Y-%m")

    conn = conectar()
    cur = conn.cursor()

    # garante migração mínima (para bancos antigos)
    try:
        cur.execute("SELECT ultimo_mes FROM config WHERE id=1")
        row = cur.fetchone()
        _ = (row[0] if row else "")
    except sqlite3.OperationalError:
        conn.close()
        migrar_banco()
        conn = conectar()
        cur = conn.cursor()

    # pega fixos ativos (com id)
    cur.execute("SELECT id, categoria, valor, descricao FROM fixos WHERE ativo=1")
    fixos = cur.fetchall()

    aplicados = 0
    for fid, cat, val, desc in fixos:
        # já aplicado neste mês?
        cur.execute("SELECT 1 FROM fixos_aplicados WHERE mes=? AND fixo_id=? LIMIT 1", (hoje_mes, fid))
        if cur.fetchone():
            continue

        try:
            valor = float(val)
        except Exception:
            valor = 0.0

        # lança como gasto no dia 01 do mês
        cur.execute(
            "INSERT INTO gastos (categoria, valor, descricao, data) VALUES (?,?,?,?)",
            (cat, valor, (desc or ""), f"{hoje_mes}-01")
        )
        # marca como aplicado
        cur.execute("INSERT OR IGNORE INTO fixos_aplicados (mes, fixo_id) VALUES (?,?)", (hoje_mes, fid))
        aplicados += 1

    # ainda mantemos ultimo_mes só como referência visual (não é mais o "bloqueio")
    cur.execute("UPDATE config SET ultimo_mes=? WHERE id=1", (hoje_mes,))

    conn.commit()
    conn.close()

# ======================
# UI HELPERS
# ======================
def money(v: float) -> str:
    return f"R$ {v:.2f}"

def br_date(iso: str) -> str:
    return datetime.strptime(iso, "%Y-%m-%d").strftime("%d/%m/%Y")

def iso_date(br: str) -> str:
    return datetime.strptime(br, "%d/%m/%Y").date().isoformat()

def msg_err(parent, title, text):
    QMessageBox.critical(parent, title, text)

def msg_yesno(parent, title, text) -> bool:
    return QMessageBox.question(parent, title, text, QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes

# ======================
# WIDGETS
# ======================
class Card(QFrame):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(6)

        self.lbl_title = QLabel(title)
        self.lbl_title.setObjectName("CardTitle")
        self.lbl_value = QLabel("—")
        self.lbl_value.setObjectName("CardValue")

        lay.addWidget(self.lbl_title)
        lay.addWidget(self.lbl_value)

    def set_value(self, text: str, positive=None):
        self.lbl_value.setText(text)
        if positive is None:
            self.lbl_value.setStyleSheet("")
        else:
            self.lbl_value.setStyleSheet(f"color: {GREEN if positive else RED};")

class SidebarButton(QPushButton):
    def __init__(self, icon_text: str, label: str, parent=None):
        super().__init__(f"{icon_text}  {label}", parent)
        self.icon_text = icon_text
        self.full_label = label
        self.setObjectName("SidebarButton")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(40)
        self.setCheckable(True)
        self.setProperty("collapsed", False)

    def set_collapsed(self, collapsed: bool):
        self.setProperty("collapsed", bool(collapsed))
        if collapsed:
            self.setText(self.icon_text)
        else:
            self.setText(f"{self.icon_text}  {self.full_label}")
        # força refresh do QSS sem "acumular" styleSheet
        self.style().unpolish(self)
        self.style().polish(self)

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

# ======================
# PÁGINAS
# ======================
class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 18)
        root.setSpacing(14)

        # header
        header = QHBoxLayout()
        self.lbl_today = QLabel("Hoje: —")
        self.lbl_today.setObjectName("Subtle")
        header.addWidget(self.lbl_today)
        header.addStretch(1)

        self.btn_new = QPushButton("+ Novo gasto")
        self.btn_new.setObjectName("BtnAccent")
        header.addWidget(self.btn_new)

        root.addLayout(header)

        # cards
        cards = QGridLayout()
        cards.setHorizontalSpacing(10)
        cards.setVerticalSpacing(10)

        self.card_gastos = Card("Gastos do mês")
        self.card_salario = Card("Salário")
        self.card_saldo = Card("Saldo")

        cards.addWidget(self.card_gastos, 0, 0)
        cards.addWidget(self.card_salario, 0, 1)
        cards.addWidget(self.card_saldo, 0, 2)

        root.addLayout(cards)

        # body
        body = QHBoxLayout()
        body.setSpacing(12)

        # table panel
        left = QFrame()
        left.setObjectName("Panel")
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(12, 12, 12, 12)
        left_l.setSpacing(10)

        row = QHBoxLayout()
        lbl = QLabel("Gastos do mês")
        lbl.setObjectName("PanelTitle")
        row.addWidget(lbl)
        row.addStretch(1)
        hint = QLabel("Duplo clique: editar")
        hint.setObjectName("Subtle")
        row.addWidget(hint)
        left_l.addLayout(row)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Categoria", "Valor", "Data"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        left_l.addWidget(self.table)

        body.addWidget(left, 3)

        # right panel (fechamentos)
        right = QFrame()
        right.setObjectName("Panel")
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(12, 12, 12, 12)
        right_l.setSpacing(10)

        top = QHBoxLayout()
        t = QLabel("Fechamentos recentes")
        t.setObjectName("PanelTitle")
        top.addWidget(t)
        top.addStretch(1)

        self.btn_graph = QPushButton("📊 Ver gráfico")
        self.btn_graph.setObjectName("BtnGhost")
        top.addWidget(self.btn_graph)

        right_l.addLayout(top)

        self.table_resumo = QTableWidget(0, 3)
        self.table_resumo.setHorizontalHeaderLabels(["Mês", "Total", "Saldo"])
        self.table_resumo.verticalHeader().setVisible(False)
        self.table_resumo.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_resumo.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_resumo.setAlternatingRowColors(True)
        self.table_resumo.setShowGrid(False)
        self.table_resumo.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_resumo.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_resumo.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        right_l.addWidget(self.table_resumo)

        body.addWidget(right, 2)

        root.addLayout(body)

class HistoryPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 18)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Histórico de fechamentos")
        title.setObjectName("H2")
        header.addWidget(title)
        header.addStretch(1)

        self.lbl_sum = QLabel("Somatório: —")
        self.lbl_sum.setObjectName("Subtle")
        header.addWidget(self.lbl_sum)

        root.addLayout(header)

        panel = QFrame()
        panel.setObjectName("Panel")
        p = QVBoxLayout(panel)
        p.setContentsMargins(12, 12, 12, 12)
        p.setSpacing(10)

        row = QHBoxLayout()
        hint = QLabel("Selecione um mês e use “Apagar fechamento” se precisar corrigir.")
        hint.setObjectName("Subtle")
        row.addWidget(hint)
        row.addStretch(1)

        self.btn_delete = QPushButton("🗑️ Apagar fechamento")
        self.btn_delete.setObjectName("BtnGhostDanger")
        row.addWidget(self.btn_delete)

        p.addLayout(row)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Mês", "Total", "Saldo"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        p.addWidget(self.table)
        root.addWidget(panel)

class GraphPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 18)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Gráfico mensal")
        title.setObjectName("H2")
        header.addWidget(title)
        header.addStretch(1)

        self.lbl_hint = QLabel("Baseado nos fechamentos (Fechar mês).")
        self.lbl_hint.setObjectName("Subtle")
        header.addWidget(self.lbl_hint)

        root.addLayout(header)

        panel = QFrame()
        panel.setObjectName("Panel")
        p = QVBoxLayout(panel)
        p.setContentsMargins(12, 12, 12, 12)
        p.setSpacing(10)

        if HAS_CHARTS:
            self.chart = QChart()
            self.chart.setBackgroundVisible(False)
            self.chart.setPlotAreaBackgroundVisible(False)
            self.chart.legend().setVisible(False)

            self.view = QChartView(self.chart)
            p.addWidget(self.view)
        else:
            lbl = QLabel(
                "QtCharts não está disponível.\n\n"
                "Tente:\n  pip install PySide6-Addons\n"
                "ou reinstale o PySide6."
            )
            lbl.setObjectName("Subtle")
            lbl.setAlignment(Qt.AlignCenter)
            p.addWidget(lbl)

        root.addWidget(panel)

    def set_data(self, meses, totais):
        if not HAS_CHARTS:
            return

        self.chart.removeAllSeries()

        barset = QBarSet("Gastos")
        for t in totais:
            barset.append(float(t))

        series = QBarSeries()
        series.append(barset)
        self.chart.addSeries(series)

        axisX = QBarCategoryAxis()
        axisX.append(meses)

        axisY = QValueAxis()
        axisY.setMin(0)
        axisY.setMax(max([1.0] + [float(x) for x in totais]) * 1.2)

        self.chart.setAxisX(axisX, series)
        self.chart.setAxisY(axisY, series)


class FechamentosPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 18)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Fechamentos")
        title.setObjectName("H2")
        header.addWidget(title)
        header.addStretch(1)

        self.btn_close_month = QPushButton("📅 Fechar mês")
        self.btn_close_month.setObjectName("BtnAccent")
        header.addWidget(self.btn_close_month)

        self.btn_graph = QPushButton("📊 Abrir gráfico")
        self.btn_graph.setObjectName("BtnGhost")
        header.addWidget(self.btn_graph)

        root.addLayout(header)

        panel = QFrame()
        panel.setObjectName("Panel")
        p = QVBoxLayout(panel)
        p.setContentsMargins(12, 12, 12, 12)
        p.setSpacing(10)

        self.lbl_info = QLabel("—")
        self.lbl_info.setObjectName("Subtle")
        p.addWidget(self.lbl_info)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Mês", "Total", "Saldo"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        p.addWidget(self.table)

        root.addWidget(panel)

    def set_month_summary(self, mes: str, total: float, salario: float):
        saldo = salario - total
        self.lbl_info.setText(f"Mês atual: {mes}  •  Gastos: {money(total)}  •  Saldo: {money(saldo)}")




# ======================
# MODAIS
# ======================

class ThemeDialog(FormDialog):
    def __init__(self, parent=None, current="original"):
        super().__init__("Tema (paleta)", parent)
        self.resize(520, 260)
        self.btn_ok.setText("Aplicar")

        title = QLabel("Escolha uma paleta")
        title.setObjectName("PanelTitle")
        desc = QLabel("Você pode trocar quando quiser. O tema fica salvo.")
        desc.setObjectName("Subtle")

        self.cmb = QComboBox()
        self._map = {
            "original": "Original (Escuro roxo)",
            "rosa_branco": "Rosa + Branco (Claro)",
            "azul_noite": "Azul Noite (Escuro)",
            "verde_musgo": "Verde Musgo (Escuro)",
            "laranja_creme": "Laranja Creme (Claro)",
            "cinza_lavanda": "Cinza Lavanda (Claro)",
        }
        for k, label in self._map.items():
            self.cmb.addItem(label, k)

        idx = 0
        for i in range(self.cmb.count()):
            if self.cmb.itemData(i) == current:
                idx = i
                break
        self.cmb.setCurrentIndex(idx)

        self.lay.addWidget(title)
        self.lay.addWidget(desc)
        self.lay.addWidget(self.cmb)

    def get_key(self):
        return self.cmb.currentData()

class SalaryDialog(FormDialog):

    def __init__(self, parent=None):
        super().__init__("Salário", parent)
        self.resize(520, 260)

        title = QLabel("Salário mensal")
        title.setObjectName("PanelTitle")
        desc = QLabel("Use ponto ou vírgula. Ex: 2500,50")
        desc.setObjectName("Subtle")

        self.input = QLineEdit()
        self.input.setPlaceholderText("0,00")
        self.input.setText(f"{obter_salario():.2f}")

        self.lay.addWidget(title)
        self.lay.addWidget(desc)
        self.lay.addWidget(self.input)

    def get_value(self):
        return float(self.input.text().replace(",", "."))

class ExpenseDialog(FormDialog):
    def __init__(self, parent=None, expense_id=None):
        super().__init__("Gasto" if expense_id is None else f"Editar gasto #{expense_id}", parent)
        self.expense_id = expense_id

        self.cmb_cat = QComboBox()
        self.cmb_cat.addItems(CATEGORIAS)

        self.inp_val = QLineEdit()
        self.inp_val.setPlaceholderText("Ex: 39,90")

        self.inp_date = QLineEdit()
        self.inp_date.setPlaceholderText("DD/MM/AAAA")
        self.inp_date.setText(date.today().strftime("%d/%m/%Y"))

        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("Opcional")

        self.lay.addWidget(QLabel("Categoria"))
        self.lay.addWidget(self.cmb_cat)
        self.lay.addWidget(QLabel("Valor (R$)"))
        self.lay.addWidget(self.inp_val)
        self.lay.addWidget(QLabel("Data (DD/MM/AAAA)"))
        self.lay.addWidget(self.inp_date)
        self.lay.addWidget(QLabel("Descrição (opcional)"))
        self.lay.addWidget(self.inp_desc)

        if self.expense_id is not None:
            self._load()

            self.btn_del = QPushButton("Deletar")
            self.btn_del.setObjectName("BtnGhostDanger")
            self.btn_del.clicked.connect(self._delete)
            self.actions.insertWidget(0, self.btn_del)

    def _load(self):
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT categoria, valor, descricao, data FROM gastos WHERE id=?", (self.expense_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return
        cat, val, desc, dt = row
        if cat in CATEGORIAS:
            self.cmb_cat.setCurrentText(cat)
        self.inp_val.setText(f"{float(val):.2f}")
        self.inp_desc.setText(desc or "")
        self.inp_date.setText(br_date(dt))

    def _delete(self):
        if not msg_yesno(self, "Confirmar", f"Deletar gasto #{self.expense_id}?"):
            return
        conn = conectar()
        cur = conn.cursor()
        cur.execute("DELETE FROM gastos WHERE id=?", (self.expense_id,))
        conn.commit()
        conn.close()
        self.done(2)

    def get_payload(self):
        cat = self.cmb_cat.currentText()
        val = float(self.inp_val.text().replace(",", "."))
        dt = iso_date(self.inp_date.text())
        desc = self.inp_desc.text().strip()
        return cat, val, desc, dt

class FixosDialog(FormDialog):
    """
    Gerenciador de gastos fixos.
    - Adicionar
    - Ativar/Pausar
    - Deletar
    """
    def __init__(self, parent=None):
        super().__init__("Gastos fixos", parent)
        self.resize(720, 520)

        # Troca os botões padrão do FormDialog (Salvar/Cancelar) por "Fechar"
        self.btn_ok.setText("Fechar")
        self.btn_ok.clicked.disconnect()
        self.btn_ok.clicked.connect(self.accept)

        self.btn_cancel.hide()

        title = QLabel("Fixos (recorrentes)")
        title.setObjectName("PanelTitle")
        desc = QLabel("Eles são lançados automaticamente no início de cada mês.")
        desc.setObjectName("Subtle")
        self.lay.addWidget(title)
        self.lay.addWidget(desc)

        # Form add
        form = QFrame()
        form.setObjectName("InlineBox")
        f = QGridLayout(form)
        f.setContentsMargins(0, 0, 0, 0)
        f.setHorizontalSpacing(10)
        f.setVerticalSpacing(8)

        self.cmb_cat = QComboBox()
        self.cmb_cat.addItems(CATEGORIAS)

        self.inp_val = QLineEdit()
        self.inp_val.setPlaceholderText("Valor (ex: 199,90)")

        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("Descrição (opcional)")

        self.btn_add = QPushButton("+ Adicionar fixo")
        self.btn_add.setObjectName("BtnAccent")
        self.btn_add.clicked.connect(self.add_fixo)

        f.addWidget(QLabel("Categoria"), 0, 0)
        f.addWidget(self.cmb_cat, 1, 0)
        f.addWidget(QLabel("Valor (R$)"), 0, 1)
        f.addWidget(self.inp_val, 1, 1)
        f.addWidget(QLabel("Descrição"), 0, 2)
        f.addWidget(self.inp_desc, 1, 2)
        f.addWidget(self.btn_add, 2, 0, 1, 3)

        self.lay.addWidget(form)

        # Table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Categoria", "Valor", "Ativo"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.lay.addWidget(self.table)

        # Actions row
        act = QHBoxLayout()
        self.btn_toggle = QPushButton("Ativar / Pausar")
        self.btn_toggle.setObjectName("BtnGhost")
        self.btn_toggle.clicked.connect(self.toggle_ativo)

        self.btn_del = QPushButton("Deletar")
        self.btn_del.setObjectName("BtnGhostDanger")
        self.btn_del.clicked.connect(self.delete_fixo)

        act.addWidget(self.btn_toggle)
        act.addWidget(self.btn_del)
        act.addStretch(1)
        self.lay.addLayout(act)

        self.load_fixos()

    def load_fixos(self):
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT id, categoria, valor, ativo FROM fixos ORDER BY id DESC")
        rows = cur.fetchall()
        conn.close()

        self.table.setRowCount(0)
        for fid, cat, val, ativo in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(fid)))
            self.table.setItem(r, 1, QTableWidgetItem(cat))
            self.table.setItem(r, 2, QTableWidgetItem(money(float(val))))
            self.table.setItem(r, 3, QTableWidgetItem("Sim" if int(ativo) == 1 else "Não"))

    def _selected_id(self):
        r = self.table.currentRow()
        if r < 0:
            return None
        item = self.table.item(r, 0)
        if not item:
            return None
        try:
            return int(item.text())
        except Exception:
            return None

    def add_fixo(self):
        try:
            val = float(self.inp_val.text().replace(",", "."))
        except Exception:
            msg_err(self, "Erro", "Valor inválido.")
            return

        cat = self.cmb_cat.currentText()
        desc = self.inp_desc.text().strip()

        conn = conectar()
        cur = conn.cursor()
        cur.execute("INSERT INTO fixos (categoria, valor, descricao, ativo) VALUES (?,?,?,1)", (cat, val, desc))
        conn.commit()
        conn.close()

        # aplica no mês atual sem duplicar
        aplicar_fixos_automaticos()

        self.inp_val.clear()
        self.inp_desc.clear()
        self.load_fixos()

    def toggle_ativo(self):
        fid = self._selected_id()
        if fid is None:
            msg_err(self, "Ativar/Pausar", "Selecione um fixo na lista.")
            return

        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT ativo FROM fixos WHERE id=?", (fid,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return
        atual = int(row[0] or 0)
        novo = 0 if atual == 1 else 1
        cur.execute("UPDATE fixos SET ativo=? WHERE id=?", (novo, fid))
        conn.commit()
        conn.close()
        self.load_fixos()

    def delete_fixo(self):
        fid = self._selected_id()
        if fid is None:
            msg_err(self, "Deletar", "Selecione um fixo na lista.")
            return
        if not msg_yesno(self, "Confirmar", f"Deletar fixo #{fid}?"):
            return
        conn = conectar()
        cur = conn.cursor()
        cur.execute("DELETE FROM fixos WHERE id=?", (fid,))
        conn.commit()
        conn.close()
        self.load_fixos()


# ======================
# MAIN WINDOW
# ======================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        migrar_banco()
        aplicar_fixos_automaticos()
        self.theme_key = obter_tema()

        self.setWindowTitle("Virtum Finance")
        self.resize(1100, 720)

        # Root
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        self.sidebar_expanded = 240
        self.sidebar_collapsed = 72
        self.sidebar_is_collapsed = False

        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        # IMPORTANTE: o minimumWidth precisa permitir encolher
        self.sidebar.setMinimumWidth(self.sidebar_collapsed)
        self.sidebar.setMaximumWidth(self.sidebar_expanded)

        s = QVBoxLayout(self.sidebar)
        s.setContentsMargins(12, 12, 12, 12)
        s.setSpacing(10)

        top = QHBoxLayout()
        self.btn_toggle = QPushButton("☰")
        self.btn_toggle.setObjectName("BtnGhost")
        self.btn_toggle.setFixedSize(QSize(38, 38))
        self.btn_toggle.clicked.connect(self.toggle_sidebar)
        top.addWidget(self.btn_toggle)
        top.addStretch(1)
        s.addLayout(top)

        self.lbl_brand = QLabel("Virtum Finance")
        self.lbl_brand.setObjectName("H1")
        self.lbl_sub = QLabel("controle + sistema")
        self.lbl_sub.setObjectName("Subtle")
        s.addWidget(self.lbl_brand)
        s.addWidget(self.lbl_sub)

        s.addSpacing(4)

        self.btn_dash = SidebarButton("🏠", "Dashboard")
        self.btn_graph = SidebarButton("📊", "Gráfico mensal")
        self.btn_hist = SidebarButton("🗓️", "Histórico")
        self.btn_salary = SidebarButton("💰", "Salário")
        self.btn_fixos = SidebarButton("📌", "Fixos")
        self.btn_fech = SidebarButton("📅", "Fechamentos")
        self.btn_theme = SidebarButton("🎨", "Tema")

        for b in [self.btn_dash, self.btn_graph, self.btn_hist, self.btn_salary, self.btn_fixos, self.btn_fech, self.btn_theme]:
            b.clicked.connect(self.on_sidebar_clicked)
            s.addWidget(b)

        s.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.btn_help = SidebarButton("❓", "Funcionalidades")
        self.btn_help.clicked.connect(self.show_features)
        s.addWidget(self.btn_help)

        layout.addWidget(self.sidebar)

        # Content stack
        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)

        self.page_dash = DashboardPage()
        self.page_hist = HistoryPage()
        self.page_graph = GraphPage()
        self.page_fech = FechamentosPage()

        self.stack.addWidget(self.page_dash)
        self.stack.addWidget(self.page_graph)
        self.stack.addWidget(self.page_hist)
        self.stack.addWidget(self.page_fech)

        # default
        self.btn_dash.setChecked(True)
        self.stack.setCurrentWidget(self.page_dash)

        # actions
        self.page_dash.btn_new.clicked.connect(self.new_expense)
        self.page_dash.table.cellDoubleClicked.connect(self.edit_selected_expense)
        self.page_dash.btn_graph.clicked.connect(self.open_graph)

        self.page_hist.btn_delete.clicked.connect(self.delete_selected_closure)

        self.page_fech.btn_close_month.clicked.connect(self.close_month)
        self.page_fech.btn_graph.clicked.connect(self.open_graph)

        # menu (opcional)
        men = self.menuBar()
        act_sal = QAction("Salário", self)
        act_sal.triggered.connect(self.edit_salary)
        men.addAction(act_sal)

        act_fix = QAction("Fixos", self)
        act_fix.triggered.connect(self.edit_fixos)
        men.addAction(act_fix)

        act_fech = QAction("Fechar mês", self)
        act_fech.triggered.connect(self.close_month)
        men.addAction(act_fech)

        act_theme = QAction("Tema", self)
        act_theme.triggered.connect(self.edit_theme)
        men.addAction(act_theme)

        # animations (min e max juntos)
        self.anim_group = QParallelAnimationGroup(self)

        self.anim_max = QPropertyAnimation(self.sidebar, b"maximumWidth", self)
        self.anim_max.setEasingCurve(QEasingCurve.OutCubic)
        self.anim_max.setDuration(220)

        self.anim_min = QPropertyAnimation(self.sidebar, b"minimumWidth", self)
        self.anim_min.setEasingCurve(QEasingCurve.OutCubic)
        self.anim_min.setDuration(220)

        self.anim_group.addAnimation(self.anim_max)
        self.anim_group.addAnimation(self.anim_min)

        self.apply_styles()
        self.refresh_all()

    def apply_styles(self):
        t = PALETAS.get(getattr(self, "theme_key", "original"), PALETAS["original"])
        self.setStyleSheet(f"""
            QMainWindow {{ background: {t["BG"]}; }}
            QWidget {{ color: {t["TEXT"]}; font-family: "Segoe UI"; font-size: 10pt; }}
            QDialog {{ background: {t["BG"]}; }}

            QToolTip {{
                background: {t["CARD"]};
                color: {t["TEXT"]};
                border: 1px solid {t["BORDER"]};
                padding: 6px;
            }}

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
            }}
            #BtnAccent:hover {{ background: {t["ACCENT_2"]}; }}

            #BtnGhost {{
                background: {t["PANEL"]};
                border: 1px solid {t["BORDER"]};
                border-radius: 10px;
                padding: 8px 12px;
            }}
            #BtnGhost:hover {{ background: {t["HOVER_BG"]}; }}

            #BtnGhostDanger {{
                background: {t["PANEL"]};
                border: 1px solid {t["BORDER"]};
                border-radius: 10px;
                padding: 8px 12px;
                color: {t["RED"]};
            }}
            #BtnGhostDanger:hover {{ background: {t["HOVER_BG"]}; }}

            #SidebarButton {{
                background: transparent;
                border: 1px solid transparent;
                border-radius: 10px;
                padding: 10px 12px;
                text-align: left;
            }}
            #SidebarButton:hover {{
                background: {t["HOVER_BG"]};
                border: 1px solid {t["BORDER"]};
            }}
            #SidebarButton:checked {{
                background: {t["ACCENT"]};
                border: 1px solid {t["ACCENT"]};
            }}
            #SidebarButton[collapsed="true"] {{
                text-align: center;
                padding-left: 0px;
                padding-right: 0px;
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
            }}
            QComboBox QAbstractItemView {{
                background: {t["PANEL"]};
                color: {t["TEXT"]};
                selection-background-color: {t["ACCENT"]};
                selection-color: white;
                border: 1px solid {t["BORDER"]};
            }}

            #InlineBox {{
                background: transparent;
            }}

            #ModalBox {{
                background: {t["PANEL"]};
                border: 1px solid {t["BORDER"]};
                border-radius: 12px;
            }}
        """)


    # ---------- sidebar ----------
    def toggle_sidebar(self):
        self.anim_group.stop()
        start = self.sidebar.width()
        end = self.sidebar_collapsed if not self.sidebar_is_collapsed else self.sidebar_expanded
        self.sidebar_is_collapsed = not self.sidebar_is_collapsed

        self.anim_max.setStartValue(start)
        self.anim_max.setEndValue(end)
        self.anim_min.setStartValue(start)
        self.anim_min.setEndValue(end)

        self.anim_group.start()
        self.apply_sidebar_mode()

    def apply_sidebar_mode(self):
        collapsed = self.sidebar_is_collapsed
        self.lbl_brand.setVisible(not collapsed)
        self.lbl_sub.setVisible(not collapsed)
        for b in [self.btn_dash, self.btn_graph, self.btn_hist, self.btn_salary, self.btn_fixos, self.btn_fech, self.btn_theme, self.btn_help]:
            b.set_collapsed(collapsed)

    def on_sidebar_clicked(self):
        btn = self.sender()
        for b in [self.btn_dash, self.btn_graph, self.btn_hist, self.btn_salary, self.btn_fixos, self.btn_fech, self.btn_theme]:
            if b is not btn:
                b.setChecked(False)

        if btn is self.btn_dash:
            self.stack.setCurrentWidget(self.page_dash)
        elif btn is self.btn_graph:
            self.stack.setCurrentWidget(self.page_graph)
        elif btn is self.btn_hist:
            self.stack.setCurrentWidget(self.page_hist)
        elif btn is self.btn_salary:
            btn.setChecked(False)
            self.edit_salary()
            return
        elif btn is self.btn_fixos:
            btn.setChecked(False)
            self.edit_fixos()
            return
        elif btn is self.btn_fech:
            self.stack.setCurrentWidget(self.page_fech)
        elif btn is self.btn_theme:
            btn.setChecked(False)
            self.edit_theme()
            return

        self.refresh_all()

    # ---------- data load ----------
    def refresh_all(self):
        aplicar_fixos_automaticos()
        self.refresh_dashboard()
        self.refresh_history()
        self.refresh_graph()
        self.refresh_fechamentos()

    def refresh_dashboard(self):
        hoje = datetime.now()
        self.page_dash.lbl_today.setText(f"Hoje: {hoje:%d/%m/%Y} • {hoje.strftime('%Y-%m')}")

        mes = datetime.now().strftime("%Y-%m")
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT id, categoria, valor, data FROM gastos WHERE data LIKE ? ORDER BY data DESC, id DESC", (f"{mes}%",))
        rows = cur.fetchall()
        conn.close()

        total = sum(float(r[2]) for r in rows)
        sal = obter_salario()
        saldo = sal - total

        self.page_dash.card_gastos.set_value(money(total))
        self.page_dash.card_salario.set_value(money(sal))
        self.page_dash.card_saldo.set_value(money(saldo), positive=(saldo >= 0))

        t = self.page_dash.table
        t.setRowCount(0)
        for rid, cat, val, dt in rows:
            rowi = t.rowCount()
            t.insertRow(rowi)
            t.setItem(rowi, 0, QTableWidgetItem(str(rid)))
            t.setItem(rowi, 1, QTableWidgetItem(cat))
            t.setItem(rowi, 2, QTableWidgetItem(money(float(val))))
            t.setItem(rowi, 3, QTableWidgetItem(br_date(dt)))

    def refresh_history(self):
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT mes, total, saldo FROM resumo ORDER BY mes DESC")
        rows = cur.fetchall()
        conn.close()

        soma = sum(float(r[1]) for r in rows)
        self.page_hist.lbl_sum.setText(f"Somatório: {money(soma)}")

        t = self.page_hist.table
        t.setRowCount(0)
        for mes, total, saldo in rows:
            rowi = t.rowCount()
            t.insertRow(rowi)
            t.setItem(rowi, 0, QTableWidgetItem(mes))
            t.setItem(rowi, 1, QTableWidgetItem(money(float(total))))
            t.setItem(rowi, 2, QTableWidgetItem(money(float(saldo))))

        tr = self.page_dash.table_resumo
        tr.setRowCount(0)
        for mes, total, saldo in rows[:8]:
            rowi = tr.rowCount()
            tr.insertRow(rowi)
            tr.setItem(rowi, 0, QTableWidgetItem(mes))
            tr.setItem(rowi, 1, QTableWidgetItem(money(float(total))))
            tr.setItem(rowi, 2, QTableWidgetItem(money(float(saldo))))

    def refresh_graph(self):
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT mes, total FROM resumo ORDER BY mes ASC")
        rows = cur.fetchall()
        conn.close()

        meses = [r[0] for r in rows]
        totais = [float(r[1]) for r in rows]
        self.page_graph.set_data(meses, totais)


    def refresh_fechamentos(self):
        mes = datetime.now().strftime("%Y-%m")
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT SUM(valor) FROM gastos WHERE data LIKE ?", (f"{mes}%",))
        total_mes = float(cur.fetchone()[0] or 0)
        conn.close()

        salario = obter_salario()
        self.page_fech.set_month_summary(mes, total_mes, salario)

        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT mes, total, saldo FROM resumo ORDER BY mes DESC LIMIT 24")
        rows = cur.fetchall()
        conn.close()

        t = self.page_fech.table
        t.setRowCount(0)
        for mesx, total, saldo in rows:
            r = t.rowCount()
            t.insertRow(r)
            t.setItem(r, 0, QTableWidgetItem(mesx))
            t.setItem(r, 1, QTableWidgetItem(money(float(total))))
            t.setItem(r, 2, QTableWidgetItem(money(float(saldo))))

    # ---------- actions ----------
    def show_features(self):
        text = (
            "• Salário: define a base do seu saldo\n"
            "• Novo gasto: adiciona um gasto no mês atual\n"
            "• Duplo clique na tabela: edita/deleta gasto\n"
            "• Fechar mês: salva total e saldo no histórico\n"
            "• Gráfico mensal: mostra os fechamentos em barras\n"
            "• Histórico: lista fechamentos e permite apagar"
        )
        QMessageBox.information(self, "Funcionalidades", text)

    def edit_salary(self):
        dlg = SalaryDialog(self)
        if dlg.exec() == QDialog.Accepted:
            try:
                v = dlg.get_value()
            except Exception:
                msg_err(self, "Erro", "Salário inválido.")
                return
            salvar_salario(v)
            self.refresh_all()


    def edit_fixos(self):
        dlg = FixosDialog(self)
        if dlg.exec() == QDialog.Accepted:
            # Após mexer nos fixos, aplica se virou mês e atualiza dashboard
            self.refresh_all()


    def edit_theme(self):
        dlg = ThemeDialog(self, current=getattr(self, "theme_key", "original"))
        if dlg.exec() == QDialog.Accepted:
            key = dlg.get_key()
            self.theme_key = key
            salvar_tema(key)
            self.apply_styles()
            self.apply_sidebar_mode()
            self.refresh_all()


    def close_month(self):
        aplicar_fixos_automaticos()
        mes = datetime.now().strftime("%Y-%m")

        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute(
                "SELECT SUM(valor) FROM gastos WHERE data LIKE ?",
                (f"{mes}%",)
            )
            total = float(cur.fetchone()[0] or 0)
            conn.close()
        except Exception as e:
            msg_err(self, "Erro", f"Falha ao calcular gastos do mês.\n\n{e}")
            return

        salario = obter_salario()
        saldo = salario - total

        if not msg_yesno(
            self,
            "Fechar mês",
            f"Mês: {mes}\n\nGastos: {money(total)}\nSaldo: {money(saldo)}\n\nDeseja fechar o mês?"
        ):
            return

        try:
            conn = conectar()
            cur = conn.cursor()

            try:
                cur.execute("""
                    INSERT INTO resumo (mes, total, saldo)
                    VALUES (?, ?, ?)
                    ON CONFLICT(mes)
                    DO UPDATE SET total=excluded.total, saldo=excluded.saldo
                """, (mes, total, saldo))
            except sqlite3.OperationalError:
                cur.execute(
                    "INSERT OR REPLACE INTO resumo (mes, total, saldo) VALUES (?, ?, ?)",
                    (mes, total, saldo)
                )

            conn.commit()
            conn.close()

            QMessageBox.information(
                self,
                "Fechado!",
                f"Fechamento de {mes} salvo com sucesso."
            )
            self.refresh_all()

        except Exception as e:
            msg_err(self, "Erro", f"Não foi possível salvar o fechamento.\n\n{e}")


    def new_expense(self):
        dlg = ExpenseDialog(self, expense_id=None)
        if dlg.exec() == QDialog.Accepted:
            try:
                cat, val, desc, dt = dlg.get_payload()
            except Exception:
                msg_err(self, "Erro", "Dados inválidos. Valor e data precisam estar corretos.")
                return

            conn = conectar()
            cur = conn.cursor()
            cur.execute("INSERT INTO gastos (categoria, valor, descricao, data) VALUES (?,?,?,?)", (cat, val, desc, dt))
            conn.commit()
            conn.close()
            self.refresh_all()

    def edit_selected_expense(self, row, col):
        t = self.page_dash.table
        item = t.item(row, 0)
        if not item:
            return
        expense_id = int(item.text())
        dlg = ExpenseDialog(self, expense_id=expense_id)
        res = dlg.exec()
        if res == 2:
            self.refresh_all()
            return
        if res == QDialog.Accepted:
            try:
                cat, val, desc, dt = dlg.get_payload()
            except Exception:
                msg_err(self, "Erro", "Dados inválidos.")
                return

            conn = conectar()
            cur = conn.cursor()
            cur.execute("""
                UPDATE gastos
                SET categoria=?, valor=?, descricao=?, data=?
                WHERE id=?
            """, (cat, val, desc, dt, expense_id))
            conn.commit()
            conn.close()
            self.refresh_all()

    def open_graph(self):
        self.btn_graph.setChecked(True)
        self.btn_dash.setChecked(False)
        self.btn_hist.setChecked(False)
        self.stack.setCurrentWidget(self.page_graph)
        self.refresh_graph()
        self.refresh_fechamentos()

    def delete_selected_closure(self):
        t = self.page_hist.table
        row = t.currentRow()
        if row < 0:
            msg_err(self, "Apagar", "Selecione um mês no histórico.")
            return
        mes = t.item(row, 0).text()
        if not msg_yesno(self, "Confirmar", f"Apagar fechamento de {mes}? Isso remove do gráfico também."):
            return

        conn = conectar()
        cur = conn.cursor()
        cur.execute("DELETE FROM resumo WHERE mes=?", (mes,))
        conn.commit()
        conn.close()
        self.refresh_all()

# ======================
# RUN
# ======================
def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
