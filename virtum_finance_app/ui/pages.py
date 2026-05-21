from __future__ import annotations

from PySide6.QtCore import QMargins, Qt
from PySide6.QtGui import QCursor, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTabWidget,
    QLineEdit,
    QProgressBar,
    QToolTip,
    QComboBox,
    QVBoxLayout,
    QWidget,
)

HAS_CHARTS = True
try:
    from PySide6.QtCharts import (
        QBarCategoryAxis,
        QBarSeries,
        QBarSet,
        QChart,
        QChartView,
        QLineSeries,
        QValueAxis,
    )
except Exception:
    HAS_CHARTS = False

from ..constants import PALETAS
from ..utils import money
from .widgets import Card


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 18)
        root.setSpacing(14)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Painel inicial")
        title.setObjectName("H2")
        self.lbl_today = QLabel("Hoje: —")
        self.lbl_today.setObjectName("Subtle")
        title_box.addWidget(title)
        title_box.addWidget(self.lbl_today)
        header.addLayout(title_box)
        header.addStretch(1)
        root.addLayout(header)

        cards = QGridLayout()
        cards.setHorizontalSpacing(10)
        cards.setVerticalSpacing(10)

        self.card_saldo = Card("Saldo atual")
        self.card_gastos = Card("Saídas do mês")
        self.card_receitas = Card("Entradas extras")
        self.card_investido = Card("Investido")
        self.card_virtum = Card("Nível Virtum")

        cards.addWidget(self.card_saldo, 0, 0)
        cards.addWidget(self.card_gastos, 0, 1)
        cards.addWidget(self.card_receitas, 0, 2)
        cards.addWidget(self.card_investido, 0, 3)
        cards.addWidget(self.card_virtum, 1, 0, 1, 4)
        root.addLayout(cards)

        body = QHBoxLayout()
        body.setSpacing(12)

        summary_panel = QFrame()
        summary_panel.setObjectName("Panel")
        summary_layout = QVBoxLayout(summary_panel)
        summary_layout.setContentsMargins(14, 14, 14, 14)
        summary_layout.setSpacing(10)

        summary_title = QLabel("Resumo do mês")
        summary_title.setObjectName("PanelTitle")
        summary_layout.addWidget(summary_title)

        self.lbl_status = QLabel("—")
        self.lbl_status.setObjectName("H2")
        self.lbl_status.setWordWrap(True)
        summary_layout.addWidget(self.lbl_status)

        self.lbl_insight = QLabel("—")
        self.lbl_insight.setObjectName("Subtle")
        self.lbl_insight.setWordWrap(True)
        summary_layout.addWidget(self.lbl_insight)

        self.lbl_budget = QLabel("—")
        self.lbl_budget.setObjectName("Subtle")
        self.lbl_budget.setWordWrap(True)
        summary_layout.addWidget(self.lbl_budget)

        self.lbl_goals = QLabel("—")
        self.lbl_goals.setObjectName("Subtle")
        self.lbl_goals.setWordWrap(True)
        summary_layout.addWidget(self.lbl_goals)

        xp_title = QLabel("Progresso Virtum")
        xp_title.setObjectName("PanelTitle")
        summary_layout.addSpacing(6)
        summary_layout.addWidget(xp_title)

        self.lbl_xp = QLabel("—")
        self.lbl_xp.setObjectName("Subtle")
        summary_layout.addWidget(self.lbl_xp)

        self.progress_xp = QProgressBar()
        self.progress_xp.setRange(0, 100)
        self.progress_xp.setTextVisible(True)
        summary_layout.addWidget(self.progress_xp)

        summary_layout.addStretch(1)
        body.addWidget(summary_panel, 3)

        actions_panel = QFrame()
        actions_panel.setObjectName("Panel")
        actions_layout = QVBoxLayout(actions_panel)
        actions_layout.setContentsMargins(14, 14, 14, 14)
        actions_layout.setSpacing(10)

        actions_title = QLabel("Ações rápidas")
        actions_title.setObjectName("PanelTitle")
        actions_layout.addWidget(actions_title)

        self.btn_new = QPushButton("+ Novo gasto")
        self.btn_new.setObjectName("BtnAccent")
        actions_layout.addWidget(self.btn_new)

        self.btn_income = QPushButton("+ Nova entrada")
        self.btn_income.setObjectName("BtnGhost")
        actions_layout.addWidget(self.btn_income)

        self.btn_invest = QPushButton("📈 Investir")
        self.btn_invest.setObjectName("BtnGhost")
        actions_layout.addWidget(self.btn_invest)

        self.btn_close_month = QPushButton("📅 Fechar mês")
        self.btn_close_month.setObjectName("BtnGhost")
        actions_layout.addWidget(self.btn_close_month)

        self.btn_gastos = QPushButton("Ver gastos")
        self.btn_gastos.setObjectName("BtnGhost")
        actions_layout.addWidget(self.btn_gastos)

        self.btn_report = QPushButton("Ver relatório")
        self.btn_report.setObjectName("BtnGhost")
        actions_layout.addWidget(self.btn_report)

        self.btn_graph = QPushButton("Ver gráfico")
        self.btn_graph.setObjectName("BtnGhost")
        actions_layout.addWidget(self.btn_graph)

        actions_layout.addStretch(1)
        body.addWidget(actions_panel, 1)

        root.addLayout(body, 1)

    def set_summary(self, resumo: dict):
        saldo = float(resumo.get("saldo", 0) or 0)
        total_gastos = float(resumo.get("total_gastos", 0) or 0)
        receitas_extra = float(resumo.get("receitas_extra", 0) or 0)
        total_investido = float(resumo.get("total_investido", 0) or 0)
        nivel = int(resumo.get("nivel", 1) or 1)
        titulo = str(resumo.get("titulo", "Aprendiz Virtum") or "Aprendiz Virtum")
        rank_atual = resumo.get("rank_atual") or {}
        rank_nome = str(rank_atual.get("nome", titulo) or titulo)
        rank_emoji = str(rank_atual.get("emoji", "") or "")
        xp_atual = int(resumo.get("xp_nivel_atual", 0) or 0)
        xp_proximo = int(resumo.get("xp_proximo_nivel", 250) or 250)
        progresso = float(resumo.get("progresso_nivel", 0) or 0)
        saldo_orcamento = float(resumo.get("saldo_orcamento", 0) or 0)
        metas_quantidade = int(resumo.get("metas_quantidade", 0) or 0)
        metas_concluidas = int(resumo.get("metas_concluidas", 0) or 0)
        maior_categoria = str(resumo.get("maior_categoria", "") or "")
        maior_categoria_total = float(resumo.get("maior_categoria_total", 0) or 0)

        self.card_saldo.set_value(money(saldo), positive=(saldo >= 0))
        self.card_gastos.set_value(money(total_gastos), positive=(total_gastos == 0))
        self.card_receitas.set_value(money(receitas_extra), positive=(receitas_extra > 0))
        self.card_investido.set_value(money(total_investido), positive=(total_investido > 0))
        self.card_virtum.set_value(f"{rank_emoji} {rank_nome} • Nv. {nivel}", positive=True)

        if saldo >= 0:
            self.lbl_status.setText("Você está no positivo este mês.")
        else:
            self.lbl_status.setText("Seu saldo está negativo este mês.")

        if maior_categoria:
            self.lbl_insight.setText(f"Maior gasto: {maior_categoria} ({money(maior_categoria_total)}).")
        elif total_gastos > 0:
            self.lbl_insight.setText("Você já possui saídas registradas este mês.")
        else:
            self.lbl_insight.setText("Nenhum gasto registrado neste mês ainda.")

        if saldo_orcamento > 0:
            self.lbl_budget.setText(f"Livre no orçamento: {money(saldo_orcamento)}.")
        elif saldo_orcamento < 0:
            self.lbl_budget.setText(f"Orçamento ultrapassado em {money(abs(saldo_orcamento))}.")
        else:
            self.lbl_budget.setText("Nenhum orçamento livre calculado para este mês.")

        if metas_quantidade > 0:
            self.lbl_goals.setText(f"Metas: {metas_concluidas}/{metas_quantidade} concluídas ou completas.")
        else:
            self.lbl_goals.setText("Nenhuma meta criada ainda.")

        rank_proximo = resumo.get("rank_proximo") or {}
        if rank_proximo:
            self.lbl_xp.setText(f"XP: {xp_atual}/{xp_proximo} • Próximo rank: {rank_proximo.get('emoji', '')} {rank_proximo.get('nome', '')}")
        else:
            self.lbl_xp.setText(f"XP: {xp_atual}/{xp_proximo} • Rank máximo alcançado")
        self.progress_xp.setValue(max(0, min(int(progresso), 100)))
        self.progress_xp.setFormat(f"{progresso:.0f}%")


class ExpensesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 18)
        root.setSpacing(12)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Gastos")
        title.setObjectName("H2")
        self.lbl_month = QLabel("Mês: —")
        self.lbl_month.setObjectName("Subtle")
        title_box.addWidget(title)
        title_box.addWidget(self.lbl_month)
        header.addLayout(title_box)
        header.addStretch(1)

        self.btn_new = QPushButton("+ Novo gasto")
        self.btn_new.setObjectName("BtnAccent")
        header.addWidget(self.btn_new)
        root.addLayout(header)

        cards = QGridLayout()
        cards.setHorizontalSpacing(10)
        cards.setVerticalSpacing(10)
        self.card_total = Card("Total do mês")
        self.card_count = Card("Lançamentos")
        self.card_average = Card("Média por gasto")
        cards.addWidget(self.card_total, 0, 0)
        cards.addWidget(self.card_count, 0, 1)
        cards.addWidget(self.card_average, 0, 2)
        root.addLayout(cards)

        panel = QFrame()
        panel.setObjectName("Panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(12, 12, 12, 12)
        panel_layout.setSpacing(10)

        hint = QLabel("Duplo clique para editar ou apagar um gasto.")
        hint.setObjectName("Subtle")
        panel_layout.addWidget(hint)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Categoria", "Valor", "Data"])
        self._setup_table(self.table)
        panel_layout.addWidget(self.table)
        root.addWidget(panel)

    def _setup_table(self, table: QTableWidget):
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)

    def set_overview(self, mes: str, total: float, quantidade: int):
        media = (float(total) / quantidade) if quantidade else 0.0
        self.lbl_month.setText(f"Mês: {mes}")
        self.card_total.set_value(money(float(total)))
        self.card_count.set_value(str(int(quantidade)))
        self.card_average.set_value(money(media))


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
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(12, 12, 12, 12)
        panel_layout.setSpacing(10)

        controls = QHBoxLayout()
        hint = QLabel("Selecione um mês e use “Apagar fechamento” se precisar corrigir.")
        hint.setObjectName("Subtle")
        controls.addWidget(hint)
        controls.addStretch(1)

        self.btn_delete = QPushButton("🗑️ Apagar fechamento")
        self.btn_delete.setObjectName("BtnGhostDanger")
        controls.addWidget(self.btn_delete)
        panel_layout.addLayout(controls)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Mês", "Saídas", "Entradas", "Saldo"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        panel_layout.addWidget(self.table)

        root.addWidget(panel)


class IncomePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 18)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Entradas extras")
        title.setObjectName("H2")
        header.addWidget(title)
        header.addStretch(1)

        self.lbl_month = QLabel("Mês: —")
        self.lbl_month.setObjectName("Subtle")
        header.addWidget(self.lbl_month)

        self.btn_new = QPushButton("+ Nova entrada")
        self.btn_new.setObjectName("BtnAccent")
        header.addWidget(self.btn_new)
        root.addLayout(header)

        cards = QGridLayout()
        cards.setHorizontalSpacing(10)
        cards.setVerticalSpacing(10)
        self.card_salary = Card("Salário base")
        self.card_extra = Card("Entradas extras")
        self.card_total = Card("Receita total")
        self.card_count = Card("Lançamentos")
        cards.addWidget(self.card_salary, 0, 0)
        cards.addWidget(self.card_extra, 0, 1)
        cards.addWidget(self.card_total, 0, 2)
        cards.addWidget(self.card_count, 0, 3)
        root.addLayout(cards)

        panel = QFrame()
        panel.setObjectName("Panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(12, 12, 12, 12)
        panel_layout.setSpacing(10)

        hint = QLabel("Cadastre receitas avulsas como freela, venda, bônus, Pix recebido ou reembolso. Elas entram no saldo e no fechamento do mês.")
        hint.setObjectName("Subtle")
        hint.setWordWrap(True)
        panel_layout.addWidget(hint)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Fonte", "Valor", "Data", "Descrição"])
        self._setup_table(self.table)
        panel_layout.addWidget(self.table)
        root.addWidget(panel)

    def _setup_table(self, table: QTableWidget):
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)

    def set_data(self, resumo: dict):
        from PySide6.QtWidgets import QTableWidgetItem
        from ..utils import br_date

        self.lbl_month.setText(f'Mês: {resumo.get("mes", "—")}')
        salario = float(resumo.get("salario", 0) or 0)
        total_extra = float(resumo.get("total_extra", 0) or 0)
        receita_total = float(resumo.get("receita_total", 0) or 0)
        quantidade = int(resumo.get("quantidade", 0) or 0)

        self.card_salary.set_value(money(salario))
        self.card_extra.set_value(money(total_extra), positive=(total_extra > 0))
        self.card_total.set_value(money(receita_total), positive=(receita_total > 0))
        self.card_count.set_value(str(quantidade))

        self.table.setRowCount(0)
        for receita in resumo.get("linhas", []) or []:
            row_index = self.table.rowCount()
            self.table.insertRow(row_index)
            data_iso = str(receita.get("data") or "")
            self.table.setItem(row_index, 0, QTableWidgetItem(str(receita.get("id", ""))))
            self.table.setItem(row_index, 1, QTableWidgetItem(str(receita.get("fonte", "Outros"))))
            self.table.setItem(row_index, 2, QTableWidgetItem(money(float(receita.get("valor", 0) or 0))))
            self.table.setItem(row_index, 3, QTableWidgetItem(br_date(data_iso) if data_iso else "—"))
            self.table.setItem(row_index, 4, QTableWidgetItem(str(receita.get("descricao", "") or "")))


class MonthlyReportPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 18)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Relatório mensal inteligente")
        title.setObjectName("H2")
        header.addWidget(title)
        header.addStretch(1)

        self.lbl_month = QLabel("Mês: —")
        self.lbl_month.setObjectName("Subtle")
        header.addWidget(self.lbl_month)
        root.addLayout(header)

        cards = QGridLayout()
        cards.setHorizontalSpacing(10)
        cards.setVerticalSpacing(10)
        self.card_receita = Card("Receita total")
        self.card_saidas = Card("Saídas")
        self.card_saldo = Card("Saldo")
        self.card_status = Card("Status")
        cards.addWidget(self.card_receita, 0, 0)
        cards.addWidget(self.card_saidas, 0, 1)
        cards.addWidget(self.card_saldo, 0, 2)
        cards.addWidget(self.card_status, 0, 3)
        root.addLayout(cards)

        panel = QFrame()
        panel.setObjectName("Panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(12, 12, 12, 12)
        panel_layout.setSpacing(10)

        title_report = QLabel("Análise automática")
        title_report.setObjectName("PanelTitle")
        self.lbl_report = QLabel("—")
        self.lbl_report.setObjectName("Subtle")
        self.lbl_report.setWordWrap(True)
        self.lbl_report.setTextInteractionFlags(Qt.TextSelectableByMouse)

        panel_layout.addWidget(title_report)
        panel_layout.addWidget(self.lbl_report)
        root.addWidget(panel)

        category_panel = QFrame()
        category_panel.setObjectName("Panel")
        category_layout = QVBoxLayout(category_panel)
        category_layout.setContentsMargins(12, 12, 12, 12)
        category_layout.setSpacing(10)
        category_title = QLabel("Categorias do mês")
        category_title.setObjectName("PanelTitle")
        category_layout.addWidget(category_title)

        self.table_categories = QTableWidget(0, 2)
        self.table_categories.setHorizontalHeaderLabels(["Categoria", "Total"])
        self._setup_table(self.table_categories)
        category_layout.addWidget(self.table_categories)
        root.addWidget(category_panel)

    def _setup_table(self, table: QTableWidget):
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)

    def set_data(self, relatorio: dict):
        from PySide6.QtWidgets import QTableWidgetItem

        self.lbl_month.setText(f'Mês: {relatorio.get("mes", "—")}')
        receita = float(relatorio.get("receita_total", 0) or 0)
        saidas = float(relatorio.get("saidas", 0) or 0)
        saldo = float(relatorio.get("saldo", 0) or 0)
        status = str(relatorio.get("status", "—") or "—")

        self.card_receita.set_value(money(receita), positive=(receita > 0))
        self.card_saidas.set_value(money(saidas), positive=False if receita > 0 and saidas > receita else None)
        self.card_saldo.set_value(money(saldo), positive=(saldo >= 0))
        self.card_status.set_value(status, positive=(saldo >= 0))
        self.lbl_report.setText(str(relatorio.get("texto", "—") or "—"))

        categorias = relatorio.get("categorias", {}) or {}
        self.table_categories.setRowCount(0)
        for categoria, valor in categorias.items():
            row_index = self.table_categories.rowCount()
            self.table_categories.insertRow(row_index)
            self.table_categories.setItem(row_index, 0, QTableWidgetItem(str(categoria)))
            self.table_categories.setItem(row_index, 1, QTableWidgetItem(money(float(valor or 0))))


class GraphPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme = PALETAS.get("original", {})
        self._last_data = {"meses": [], "totais": [], "salary": None}

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 18)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Gráfico mensal")
        title.setObjectName("H2")
        header.addWidget(title)
        header.addStretch(1)

        self.lbl_hint = QLabel("Baseado nos fechamentos salvos.")
        self.lbl_hint.setObjectName("Subtle")
        header.addWidget(self.lbl_hint)
        root.addLayout(header)

        panel = QFrame()
        panel.setObjectName("Panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(12, 12, 12, 12)
        panel_layout.setSpacing(10)

        if HAS_CHARTS:
            self.chart = QChart()
            self.chart.setBackgroundVisible(False)
            self.chart.setPlotAreaBackgroundVisible(False)
            self.chart.setMargins(QMargins(0, 0, 0, 0))
            self.chart.layout().setContentsMargins(0, 0, 0, 0)
            self.chart.setAnimationOptions(QChart.SeriesAnimations)
            self.chart.legend().setVisible(True)
            self.chart.legend().setAlignment(Qt.AlignBottom)

            self.view = QChartView(self.chart)
            self.view.setRenderHint(QPainter.Antialiasing, True)
            self.view.setObjectName("VirtumChartView")
            panel_layout.addWidget(self.view)
        else:
            label = QLabel(
                "QtCharts não está disponível.\n\n"
                "Tente instalar com:\n  pip install PySide6-Addons\n"
                "ou reinstale o PySide6."
            )
            label.setObjectName("Subtle")
            label.setAlignment(Qt.AlignCenter)
            panel_layout.addWidget(label)

        root.addWidget(panel)

    def set_theme(self, theme: dict):
        self._theme = theme or PALETAS.get("original", {})
        if self._last_data["meses"]:
            self.set_data(self._last_data["meses"], self._last_data["totais"], self._last_data["salary"], self._theme)

    def set_data(self, meses, totais, salary=None, theme=None):
        if not HAS_CHARTS:
            return

        selected_theme = theme or self._theme or PALETAS.get("original", {})
        meses = list(meses or [])
        totais = [float(valor or 0) for valor in (totais or [])]
        self._last_data = {"meses": meses, "totais": totais, "salary": salary}

        self.chart.removeAllSeries()
        for axis in list(self.chart.axes()):
            self.chart.removeAxis(axis)

        barset = QBarSet("Saídas")
        for valor in totais:
            barset.append(float(valor))
        barset.setColor(selected_theme.get("ACCENT", "#6C63FF"))
        barset.setBorderColor(selected_theme.get("ACCENT_2", selected_theme.get("ACCENT", "#6C63FF")))
        try:
            barset.setLabelColor(selected_theme.get("TEXT", "#E6E6E6"))
        except Exception:
            pass

        def on_hover(status, index):
            if not status:
                QToolTip.hideText()
                return
            if 0 <= index < len(meses) and 0 <= index < len(totais):
                QToolTip.showText(QCursor.pos(), f"{meses[index]}\nSaídas: {money(totais[index])}")

        try:
            barset.hovered.connect(on_hover)
        except Exception:
            pass

        series = QBarSeries()
        series.setLabelsVisible(False)
        series.append(barset)
        self.chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(meses)
        axis_x.setLabelsColor(selected_theme.get("SUB", "#9AA0A6"))
        axis_x.setGridLineVisible(False)
        axis_x.setLinePenColor(selected_theme.get("BORDER", "#232A3A"))

        axis_y = QValueAxis()
        axis_y.setLabelsColor(selected_theme.get("SUB", "#9AA0A6"))
        axis_y.setGridLineVisible(True)
        axis_y.setGridLineColor(selected_theme.get("BORDER", "#232A3A"))
        axis_y.setLinePenColor(selected_theme.get("BORDER", "#232A3A"))

        max_y = max([1.0] + totais)
        if salary is not None:
            max_y = max(max_y, float(salary or 0))
        axis_y.setMin(0)
        axis_y.setMax(max_y * 1.25)

        self.chart.addAxis(axis_x, Qt.AlignBottom)
        self.chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

        if salary is not None and len(meses) > 0:
            line = QLineSeries()
            line.setName("Salário")
            for index in range(len(meses)):
                line.append(index, float(salary or 0))

            pen = QPen()
            pen.setWidth(2)
            pen.setColor(selected_theme.get("GREEN", "#35D07F"))
            line.setPen(pen)

            self.chart.addSeries(line)
            line.attachAxis(axis_x)
            line.attachAxis(axis_y)

        try:
            self.chart.legend().setLabelColor(selected_theme.get("SUB", "#9AA0A6"))
        except Exception:
            pass
        self.chart.setTitle("")


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
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(12, 12, 12, 12)
        panel_layout.setSpacing(10)

        self.lbl_info = QLabel("—")
        self.lbl_info.setObjectName("Subtle")
        panel_layout.addWidget(self.lbl_info)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Mês", "Saídas", "Entradas", "Saldo"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        panel_layout.addWidget(self.table)

        root.addWidget(panel)

    def set_month_summary(self, mes: str, total: float, salario: float, receitas_extra: float = 0.0):
        receita_total = salario + receitas_extra
        saldo = receita_total - total
        self.lbl_info.setText(
            f"Mês atual: {mes}  •  Entradas: {money(receita_total)}  •  Saídas: {money(total)}  •  Saldo: {money(saldo)}"
        )

class InvestmentEvolutionChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme = PALETAS.get("original", {})
        self._last_series = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if HAS_CHARTS:
            self.chart = QChart()
            self.chart.setBackgroundVisible(False)
            self.chart.setPlotAreaBackgroundVisible(False)
            self.chart.setMargins(QMargins(0, 0, 0, 0))
            self.chart.layout().setContentsMargins(0, 0, 0, 0)
            self.chart.legend().setVisible(True)
            self.chart.legend().setAlignment(Qt.AlignBottom)

            self.view = QChartView(self.chart)
            self.view.setRenderHint(QPainter.Antialiasing, True)
            self.view.setObjectName("VirtumChartView")
            layout.addWidget(self.view)
        else:
            label = QLabel("QtCharts não está disponível para exibir o gráfico de evolução.")
            label.setObjectName("Subtle")
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)

    def set_theme(self, theme: dict):
        self._theme = theme or PALETAS.get("original", {})
        if self._last_series:
            self.set_data(self._last_series, self._theme)

    def set_data(self, series_map: dict[str, list[float]], theme=None):
        self._last_series = series_map or {}
        if not HAS_CHARTS:
            return

        selected_theme = theme or self._theme or PALETAS.get("original", {})
        self.chart.removeAllSeries()
        for axis in list(self.chart.axes()):
            self.chart.removeAxis(axis)

        axis_x = QValueAxis()
        axis_x.setTitleText("Meses")
        axis_x.setLabelsColor(selected_theme.get("SUB", "#9AA0A6"))
        axis_x.setGridLineColor(selected_theme.get("BORDER", "#232A3A"))
        axis_x.setLinePenColor(selected_theme.get("BORDER", "#232A3A"))
        axis_x.setLabelFormat("%d")

        axis_y = QValueAxis()
        axis_y.setTitleText("Valor líquido")
        axis_y.setLabelsColor(selected_theme.get("SUB", "#9AA0A6"))
        axis_y.setGridLineColor(selected_theme.get("BORDER", "#232A3A"))
        axis_y.setLinePenColor(selected_theme.get("BORDER", "#232A3A"))

        max_len = 0
        valores = []
        cores = [
            selected_theme.get("ACCENT", "#6C63FF"),
            selected_theme.get("GREEN", "#35D07F"),
            selected_theme.get("RED", "#FF4D4D"),
        ]

        for index, (nome, serie) in enumerate((series_map or {}).items()):
            linha = QLineSeries()
            linha.setName(nome)
            pen = QPen()
            pen.setWidth(2)
            pen.setColor(cores[index % len(cores)])
            linha.setPen(pen)

            for mes, valor in enumerate(serie or []):
                valor_float = float(valor or 0)
                linha.append(mes, valor_float)
                valores.append(valor_float)
            max_len = max(max_len, len(serie or []))
            self.chart.addSeries(linha)

        max_valor = max([1.0] + valores)
        min_valor = min([0.0] + valores)
        axis_x.setRange(0, max(max_len - 1, 1))
        axis_y.setRange(min_valor, max_valor * 1.10)

        self.chart.addAxis(axis_x, Qt.AlignBottom)
        self.chart.addAxis(axis_y, Qt.AlignLeft)
        for serie in self.chart.series():
            serie.attachAxis(axis_x)
            serie.attachAxis(axis_y)

        try:
            self.chart.legend().setLabelColor(selected_theme.get("SUB", "#9AA0A6"))
        except Exception:
            pass
        self.chart.setTitle("")


class InvestmentsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme = PALETAS.get("original", {})

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 18)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Investimentos")
        title.setObjectName("H2")
        header.addWidget(title)
        header.addStretch(1)

        self.btn_new = QPushButton("💸 Investir")
        self.btn_new.setObjectName("BtnAccent")
        header.addWidget(self.btn_new)
        root.addLayout(header)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("VirtumTabs")
        root.addWidget(self.tabs)

        self._build_overview_tab()
        self._build_simulator_tab()
        self._build_my_investments_tab()
        self._build_comparativo_tab()

    def _build_overview_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(12)

        cards = QGridLayout()
        cards.setHorizontalSpacing(10)
        cards.setVerticalSpacing(10)

        self.card_investido = Card("Total aplicado")
        self.card_resultado = Card("Rendimento estimado")
        self.card_quantidade = Card("Investimentos cadastrados")
        self.card_melhor = Card("Melhor estimado")

        cards.addWidget(self.card_investido, 0, 0)
        cards.addWidget(self.card_resultado, 0, 1)
        cards.addWidget(self.card_quantidade, 0, 2)
        cards.addWidget(self.card_melhor, 0, 3)
        layout.addLayout(cards)

        panel = QFrame()
        panel.setObjectName("Panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(12, 12, 12, 12)
        panel_layout.setSpacing(10)

        title = QLabel("Distribuição por tipo")
        title.setObjectName("PanelTitle")
        self.lbl_distribuicao = QLabel("—")
        self.lbl_distribuicao.setObjectName("Subtle")
        self.lbl_distribuicao.setWordWrap(True)

        aviso = QLabel("Simulação estimada. As taxas podem variar. Não é recomendação de investimento.")
        aviso.setObjectName("Subtle")
        aviso.setWordWrap(True)

        panel_layout.addWidget(title)
        panel_layout.addWidget(self.lbl_distribuicao)
        panel_layout.addWidget(aviso)
        layout.addWidget(panel)

        self.tabs.addTab(page, "Visão geral")

    def _build_simulator_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(12)

        form = QFrame()
        form.setObjectName("Panel")
        grid = QGridLayout(form)
        grid.setContentsMargins(12, 12, 12, 12)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        self.inp_sim_valor = QLineEdit()
        self.inp_sim_valor.setPlaceholderText("Ex: 1000,00")
        self.inp_sim_prazo = QLineEdit()
        self.inp_sim_prazo.setPlaceholderText("Ex: 12")
        self.inp_sim_prazo.setText("12")
        self.inp_sim_cdi = QLineEdit()
        self.inp_sim_cdi.setPlaceholderText("Ex: 10,65")
        self.inp_sim_selic = QLineEdit()
        self.inp_sim_selic.setPlaceholderText("Ex: 10,50")
        self.inp_sim_tr = QLineEdit()
        self.inp_sim_tr.setPlaceholderText("Ex: 0,00")
        self.inp_sim_tr.setText("0")
        self.inp_sim_percentual = QLineEdit()
        self.inp_sim_percentual.setPlaceholderText("Ex: 105")
        self.inp_sim_percentual.setText("100")

        self.btn_compare = QPushButton("Comparar simulação")
        self.btn_compare.setObjectName("BtnAccent")

        grid.addWidget(QLabel("Valor inicial (R$)"), 0, 0)
        grid.addWidget(self.inp_sim_valor, 1, 0)
        grid.addWidget(QLabel("Prazo (meses)"), 0, 1)
        grid.addWidget(self.inp_sim_prazo, 1, 1)
        grid.addWidget(QLabel("CDI anual estimado (%)"), 2, 0)
        grid.addWidget(self.inp_sim_cdi, 3, 0)
        grid.addWidget(QLabel("Selic anual estimada (%)"), 2, 1)
        grid.addWidget(self.inp_sim_selic, 3, 1)
        grid.addWidget(QLabel("TR mensal estimada (%)"), 4, 0)
        grid.addWidget(self.inp_sim_tr, 5, 0)
        grid.addWidget(QLabel("CDI personalizado (%)"), 4, 1)
        grid.addWidget(self.inp_sim_percentual, 5, 1)
        grid.addWidget(self.btn_compare, 6, 0, 1, 2)
        layout.addWidget(form)

        result_cards = QGridLayout()
        result_cards.setHorizontalSpacing(10)
        result_cards.setVerticalSpacing(10)
        self.card_sim_investido = Card("Valor investido")
        self.card_sim_liquido = Card("Maior valor final")
        self.card_sim_melhor = Card("Maior rendimento estimado nesta simulação")
        self.card_sim_aviso = Card("Aviso")
        self.card_sim_aviso.set_value("Simulação estimada")
        result_cards.addWidget(self.card_sim_investido, 0, 0)
        result_cards.addWidget(self.card_sim_liquido, 0, 1)
        result_cards.addWidget(self.card_sim_melhor, 0, 2)
        result_cards.addWidget(self.card_sim_aviso, 0, 3)
        layout.addLayout(result_cards)

        self.sim_table = QTableWidget(0, 8)
        self.sim_table.setHorizontalHeaderLabels([
            "Opção", "Investido", "Bruto", "IR", "Líquido", "Final", "Rentabilidade", "Dif. Poupança"
        ])
        self._setup_table(self.sim_table)
        layout.addWidget(self.sim_table)

        self.tabs.addTab(page, "Simulador")

    def _build_my_investments_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(12)

        panel = QFrame()
        panel.setObjectName("Panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(12, 12, 12, 12)
        panel_layout.setSpacing(10)

        hint = QLabel("Duplo clique para editar. Quando marcado, o investimento reduz o saldo e entra no fechamento.")
        hint.setObjectName("Subtle")
        hint.setWordWrap(True)
        panel_layout.addWidget(hint)

        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nome", "Tipo", "Aplicado", "Atual estimado", "Resultado", "Prazo", "% CDI", "Abate saldo", "Data"
        ])
        self._setup_table(self.table)
        panel_layout.addWidget(self.table)
        layout.addWidget(panel)

        self.tabs.addTab(page, "Meus investimentos")

    def _build_comparativo_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(12)

        panel = QFrame()
        panel.setObjectName("Panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(12, 12, 12, 12)
        panel_layout.setSpacing(10)

        title = QLabel("Evolução patrimonial mês a mês")
        title.setObjectName("PanelTitle")
        self.lbl_comparativo_hint = QLabel("Rode uma simulação para preencher o gráfico e a tabela comparativa.")
        self.lbl_comparativo_hint.setObjectName("Subtle")
        self.lbl_comparativo_hint.setWordWrap(True)

        self.comp_table = QTableWidget(0, 8)
        self.comp_table.setHorizontalHeaderLabels([
            "Opção", "Investido", "Bruto", "IR", "Líquido", "Final", "Rentabilidade", "Dif. Poupança"
        ])
        self._setup_table(self.comp_table)

        self.evolution_chart = InvestmentEvolutionChart()
        self.evolution_chart.setMinimumHeight(260)

        panel_layout.addWidget(title)
        panel_layout.addWidget(self.lbl_comparativo_hint)
        panel_layout.addWidget(self.evolution_chart)
        panel_layout.addWidget(self.comp_table)
        layout.addWidget(panel)

        self.tabs.addTab(page, "Comparativo")

    def _setup_table(self, table: QTableWidget):
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        for index in range(table.columnCount()):
            if index in (1, 2):
                table.horizontalHeader().setSectionResizeMode(index, QHeaderView.Stretch)
            else:
                table.horizontalHeader().setSectionResizeMode(index, QHeaderView.ResizeToContents)

    def set_theme(self, theme: dict):
        self._theme = theme or PALETAS.get("original", {})
        self.evolution_chart.set_theme(self._theme)

    def get_simulator_payload(self):
        from ..utils import parse_money

        valor = parse_money(self.inp_sim_valor.text())
        prazo = int((self.inp_sim_prazo.text() or "0").strip())
        cdi = parse_money(self.inp_sim_cdi.text() or "0")
        selic = parse_money(self.inp_sim_selic.text() or "0")
        tr = parse_money(self.inp_sim_tr.text() or "0")
        percentual = parse_money(self.inp_sim_percentual.text() or "0")

        if valor <= 0:
            raise ValueError("Valor inicial precisa ser maior que zero.")
        if prazo <= 0:
            raise ValueError("Prazo precisa ser maior que zero.")

        return valor, prazo, cdi, selic, tr, percentual

    def set_overview(self, resumo: dict):
        total = float(resumo.get("total_aplicado", 0) or 0)
        rendimento = float(resumo.get("rendimento_estimado", 0) or 0)
        quantidade = int(resumo.get("quantidade", 0) or 0)
        melhor = str(resumo.get("melhor_investimento_estimado", "—") or "—")
        distribuicao = resumo.get("distribuicao_por_tipo", {}) or {}

        self.card_investido.set_value(money(total))
        self.card_resultado.set_value(money(rendimento), positive=(rendimento >= 0))
        self.card_quantidade.set_value(str(quantidade))
        self.card_melhor.set_value(melhor)

        if distribuicao:
            partes = [f"{tipo}: {money(valor)}" for tipo, valor in sorted(distribuicao.items())]
            self.lbl_distribuicao.setText(" • ".join(partes))
        else:
            self.lbl_distribuicao.setText("Nenhum investimento cadastrado ainda.")

    def set_simulation_results(self, comparativo: dict):
        from PySide6.QtWidgets import QTableWidgetItem

        resultados = comparativo.get("resultados", []) or []
        melhor = str(comparativo.get("melhor_resultado", "—") or "—")
        melhor_item = next((item for item in resultados if item.get("nome") == melhor), None)

        if melhor_item:
            self.card_sim_investido.set_value(money(float(melhor_item.get("valor_investido", 0) or 0)))
            self.card_sim_liquido.set_value(money(float(melhor_item.get("valor_final_liquido", 0) or 0)), positive=True)
            self.card_sim_melhor.set_value(melhor)
        self.card_sim_aviso.set_value("Estimativa, não recomendação")

        def fill(table: QTableWidget):
            table.setRowCount(0)
            for item in resultados:
                row = table.rowCount()
                table.insertRow(row)
                nome = str(item.get("nome", "—"))
                table.setItem(row, 0, QTableWidgetItem(nome))
                table.setItem(row, 1, QTableWidgetItem(money(float(item.get("valor_investido", 0) or 0))))
                table.setItem(row, 2, QTableWidgetItem(money(float(item.get("rendimento_bruto", 0) or 0))))
                table.setItem(row, 3, QTableWidgetItem(money(float(item.get("imposto_estimado", 0) or 0))))
                table.setItem(row, 4, QTableWidgetItem(money(float(item.get("rendimento_liquido", 0) or 0))))
                table.setItem(row, 5, QTableWidgetItem(money(float(item.get("valor_final_liquido", 0) or 0))))
                table.setItem(row, 6, QTableWidgetItem(f'{float(item.get("rentabilidade_liquida_percentual", 0) or 0):.2f}%'.replace(".", ",")))
                table.setItem(row, 7, QTableWidgetItem(money(float(item.get("diferenca_poupanca", 0) or 0))))

        fill(self.sim_table)
        fill(self.comp_table)

        series_map = {str(item.get("nome", "—")): list(item.get("serie_mensal", []) or []) for item in resultados}
        self.evolution_chart.set_data(series_map, self._theme)
        self.lbl_comparativo_hint.setText("Maior rendimento estimado nesta simulação: " + melhor)


class BudgetsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 18)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Orçamentos por categoria")
        title.setObjectName("H2")
        header.addWidget(title)
        header.addStretch(1)

        self.lbl_month = QLabel("Mês: —")
        self.lbl_month.setObjectName("Subtle")
        header.addWidget(self.lbl_month)

        self.btn_new = QPushButton("+ Definir orçamento")
        self.btn_new.setObjectName("BtnAccent")
        header.addWidget(self.btn_new)
        root.addLayout(header)

        cards = QGridLayout()
        cards.setHorizontalSpacing(10)
        cards.setVerticalSpacing(10)
        self.card_total = Card("Total orçado")
        self.card_used = Card("Usado no orçamento")
        self.card_free = Card("Livre")
        self.card_outside = Card("Fora do orçamento")
        cards.addWidget(self.card_total, 0, 0)
        cards.addWidget(self.card_used, 0, 1)
        cards.addWidget(self.card_free, 0, 2)
        cards.addWidget(self.card_outside, 0, 3)
        root.addLayout(cards)

        panel = QFrame()
        panel.setObjectName("Panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(12, 12, 12, 12)
        panel_layout.setSpacing(10)

        hint = QLabel("Defina um limite mensal por categoria. O app compara automaticamente com os gastos lançados no mês.")
        hint.setObjectName("Subtle")
        hint.setWordWrap(True)
        panel_layout.addWidget(hint)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["ID", "Categoria", "Limite", "Usado", "Livre", "Uso", "Status"])
        self._setup_table(self.table)
        panel_layout.addWidget(self.table)
        root.addWidget(panel)

    def _setup_table(self, table: QTableWidget):
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        for column_index in range(2, table.columnCount()):
            table.horizontalHeader().setSectionResizeMode(column_index, QHeaderView.ResizeToContents)

    def set_data(self, resumo: dict):
        from PySide6.QtWidgets import QTableWidgetItem

        self.lbl_month.setText(f'Mês: {resumo.get("mes", "—")}')
        total_orcado = float(resumo.get("total_orcado", 0) or 0)
        total_usado = float(resumo.get("total_usado_orcado", 0) or 0)
        saldo_orcamento = float(resumo.get("saldo_orcamento", 0) or 0)
        total_fora = float(resumo.get("total_fora_orcamento", 0) or 0)

        self.card_total.set_value(money(total_orcado))
        self.card_used.set_value(money(total_usado), positive=(total_usado <= total_orcado or total_orcado == 0))
        self.card_free.set_value(money(saldo_orcamento), positive=(saldo_orcamento >= 0))
        self.card_outside.set_value(money(total_fora), positive=(total_fora == 0))

        self.table.setRowCount(0)
        for linha in resumo.get("linhas", []) or []:
            row_index = self.table.rowCount()
            self.table.insertRow(row_index)

            percentual = float(linha.get("percentual", 0) or 0)
            progress_bar = QProgressBar()
            progress_bar.setRange(0, 100)
            progress_bar.setValue(max(0, min(int(percentual), 100)))
            progress_bar.setFormat(f"{percentual:.0f}%")
            progress_bar.setTextVisible(True)

            self.table.setItem(row_index, 0, QTableWidgetItem(str(linha.get("id", ""))))
            self.table.setItem(row_index, 1, QTableWidgetItem(str(linha.get("categoria", "Outros"))))
            self.table.setItem(row_index, 2, QTableWidgetItem(money(float(linha.get("limite", 0) or 0))))
            self.table.setItem(row_index, 3, QTableWidgetItem(money(float(linha.get("usado", 0) or 0))))
            self.table.setItem(row_index, 4, QTableWidgetItem(money(float(linha.get("livre", 0) or 0))))
            self.table.setCellWidget(row_index, 5, progress_bar)
            self.table.setItem(row_index, 6, QTableWidgetItem(str(linha.get("status", "—"))))


class GoalsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 18)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Metas financeiras")
        title.setObjectName("H2")
        header.addWidget(title)
        header.addStretch(1)

        self.btn_new = QPushButton("+ Nova meta")
        self.btn_new.setObjectName("BtnAccent")
        header.addWidget(self.btn_new)
        root.addLayout(header)

        cards = QGridLayout()
        cards.setHorizontalSpacing(10)
        cards.setVerticalSpacing(10)
        self.card_current = Card("Guardado")
        self.card_target = Card("Objetivo total")
        self.card_missing = Card("Falta")
        self.card_done = Card("Concluídas")
        cards.addWidget(self.card_current, 0, 0)
        cards.addWidget(self.card_target, 0, 1)
        cards.addWidget(self.card_missing, 0, 2)
        cards.addWidget(self.card_done, 0, 3)
        root.addLayout(cards)

        panel = QFrame()
        panel.setObjectName("Panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(12, 12, 12, 12)
        panel_layout.setSpacing(10)

        hint = QLabel("Duplo clique para editar. Use metas para reserva de emergência, hardware, viagem ou qualquer objetivo pessoal.")
        hint.setObjectName("Subtle")
        hint.setWordWrap(True)
        panel_layout.addWidget(hint)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["ID", "Meta", "Categoria", "Atual", "Alvo", "Progresso", "Data limite", "Status"])
        self._setup_table(self.table)
        panel_layout.addWidget(self.table)
        root.addWidget(panel)

    def _setup_table(self, table: QTableWidget):
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        for column_index in range(2, table.columnCount()):
            table.horizontalHeader().setSectionResizeMode(column_index, QHeaderView.ResizeToContents)

    def set_data(self, resumo: dict):
        from PySide6.QtWidgets import QTableWidgetItem
        from ..utils import br_date

        total_atual = float(resumo.get("total_atual", 0) or 0)
        total_alvo = float(resumo.get("total_alvo", 0) or 0)
        faltante = float(resumo.get("faltante", 0) or 0)
        concluidas = int(resumo.get("concluidas", 0) or 0)
        quantidade = int(resumo.get("quantidade", 0) or 0)

        self.card_current.set_value(money(total_atual), positive=True)
        self.card_target.set_value(money(total_alvo))
        self.card_missing.set_value(money(faltante), positive=(faltante == 0 and total_alvo > 0))
        self.card_done.set_value(f"{concluidas}/{quantidade}", positive=(quantidade > 0 and concluidas == quantidade))

        self.table.setRowCount(0)
        for meta in resumo.get("linhas", []) or []:
            row_index = self.table.rowCount()
            self.table.insertRow(row_index)

            valor_atual = float(meta.get("valor_atual", 0) or 0)
            valor_alvo = float(meta.get("valor_alvo", 0) or 0)
            percentual = (valor_atual / valor_alvo * 100.0) if valor_alvo > 0 else 0.0
            concluida = int(meta.get("concluida", 0) or 0) == 1 or percentual >= 100
            data_limite = str(meta.get("data_limite", "") or "")

            progress_bar = QProgressBar()
            progress_bar.setRange(0, 100)
            progress_bar.setValue(max(0, min(int(percentual), 100)))
            progress_bar.setFormat(f"{percentual:.0f}%")
            progress_bar.setTextVisible(True)

            self.table.setItem(row_index, 0, QTableWidgetItem(str(meta.get("id", ""))))
            self.table.setItem(row_index, 1, QTableWidgetItem(str(meta.get("nome", ""))))
            self.table.setItem(row_index, 2, QTableWidgetItem(str(meta.get("categoria", "Outro"))))
            self.table.setItem(row_index, 3, QTableWidgetItem(money(valor_atual)))
            self.table.setItem(row_index, 4, QTableWidgetItem(money(valor_alvo)))
            self.table.setCellWidget(row_index, 5, progress_bar)
            self.table.setItem(row_index, 6, QTableWidgetItem(br_date(data_limite) if data_limite else "—"))
            self.table.setItem(row_index, 7, QTableWidgetItem("Concluída" if concluida else "Em andamento"))

class GamificationPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 18)
        root.setSpacing(12)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("Gamificação Virtum")
        title.setObjectName("H2")
        subtitle = QLabel("Evolução financeira, missões e recompensas do seu mês.")
        subtitle.setObjectName("Subtle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch(1)

        self.lbl_month = QLabel("Mês: —")
        self.lbl_month.setObjectName("Badge")
        header.addWidget(self.lbl_month)
        root.addLayout(header)

        hero = QFrame()
        hero.setObjectName("HeroPanel")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(18, 16, 18, 16)
        hero_layout.setSpacing(16)

        self.lbl_rank_emoji = QLabel("🌱")
        self.lbl_rank_emoji.setObjectName("HeroEmoji")
        self.lbl_rank_emoji.setAlignment(Qt.AlignCenter)
        hero_layout.addWidget(self.lbl_rank_emoji)

        hero_info = QVBoxLayout()
        hero_info.setSpacing(6)
        self.lbl_rank_name = QLabel("Aprendiz Financeiro")
        self.lbl_rank_name.setObjectName("HeroTitle")
        self.lbl_rank_description = QLabel("Comece registrando movimentações e fechando o mês com clareza.")
        self.lbl_rank_description.setObjectName("HeroSubtitle")
        self.lbl_rank_description.setWordWrap(True)
        self.lbl_xp_level = QLabel("—")
        self.lbl_xp_level.setObjectName("HeroSubtitle")

        self.progress_level = QProgressBar()
        self.progress_level.setRange(0, 100)
        self.progress_level.setTextVisible(True)

        hero_info.addWidget(self.lbl_rank_name)
        hero_info.addWidget(self.lbl_rank_description)
        hero_info.addWidget(self.lbl_xp_level)
        hero_info.addWidget(self.progress_level)
        hero_layout.addLayout(hero_info, 4)

        metrics = QGridLayout()
        metrics.setHorizontalSpacing(10)
        metrics.setVerticalSpacing(10)
        self.metric_level_box, self.metric_level_title, self.metric_level_value = self._metric_box("Nível", "—")
        self.metric_xp_box, self.metric_xp_title, self.metric_xp_value = self._metric_box("XP total", "—")
        self.metric_next_box, self.metric_next_title, self.metric_next_value = self._metric_box("Próximo rank", "—")
        self.metric_medal_box, self.metric_medal_title, self.metric_medal_value = self._metric_box("Medalha do mês", "—")
        metrics.addWidget(self.metric_level_box, 0, 0)
        metrics.addWidget(self.metric_xp_box, 0, 1)
        metrics.addWidget(self.metric_next_box, 1, 0)
        metrics.addWidget(self.metric_medal_box, 1, 1)
        hero_layout.addLayout(metrics, 3)
        root.addWidget(hero)

        overview = QHBoxLayout()
        overview.setSpacing(12)

        journey_panel = QFrame()
        journey_panel.setObjectName("Panel")
        journey_layout = QVBoxLayout(journey_panel)
        journey_layout.setContentsMargins(14, 14, 14, 14)
        journey_layout.setSpacing(10)

        journey_header = QHBoxLayout()
        journey_title = QLabel("Jornada do mês")
        journey_title.setObjectName("PanelTitle")
        journey_header.addWidget(journey_title)
        journey_header.addStretch(1)
        self.lbl_mission_summary = QLabel("—")
        self.lbl_mission_summary.setObjectName("Subtle")
        journey_header.addWidget(self.lbl_mission_summary)
        journey_layout.addLayout(journey_header)

        self.mission_grid = QGridLayout()
        self.mission_grid.setHorizontalSpacing(10)
        self.mission_grid.setVerticalSpacing(10)
        self.mission_cards = []
        for index in range(5):
            mission_card, mission_title, mission_status, mission_progress = self._mission_card()
            self.mission_cards.append(
                {
                    "card": mission_card,
                    "title": mission_title,
                    "status": mission_status,
                    "progress": mission_progress,
                }
            )
            self.mission_grid.addWidget(mission_card, index // 2, index % 2)
        journey_layout.addLayout(self.mission_grid)
        overview.addWidget(journey_panel, 5)

        summary_panel = QFrame()
        summary_panel.setObjectName("Panel")
        summary_layout = QVBoxLayout(summary_panel)
        summary_layout.setContentsMargins(14, 14, 14, 14)
        summary_layout.setSpacing(10)

        summary_title = QLabel("Resumo rápido")
        summary_title.setObjectName("PanelTitle")
        summary_layout.addWidget(summary_title)

        self.lbl_quick_achievements = QLabel("—")
        self.lbl_quick_achievements.setObjectName("InfoLine")
        self.lbl_quick_achievements.setWordWrap(True)
        self.lbl_quick_medals = QLabel("—")
        self.lbl_quick_medals.setObjectName("InfoLine")
        self.lbl_quick_medals.setWordWrap(True)
        self.lbl_quick_tip = QLabel("—")
        self.lbl_quick_tip.setObjectName("InfoLine")
        self.lbl_quick_tip.setWordWrap(True)

        summary_layout.addWidget(self.lbl_quick_achievements)
        summary_layout.addWidget(self.lbl_quick_medals)
        summary_layout.addWidget(self.lbl_quick_tip)
        summary_layout.addStretch(1)
        overview.addWidget(summary_panel, 2)

        root.addLayout(overview)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("GamificationTabs")

        self.table_missions = QTableWidget(0, 5)
        self.table_missions.setHorizontalHeaderLabels(["Missão", "Progresso", "XP", "Status", "Barra"])
        self._setup_table(self.table_missions)
        self.tabs.addTab(self._tab_page(self.table_missions), "Missões")

        self.table_medals = QTableWidget(0, 4)
        self.table_medals.setHorizontalHeaderLabels(["Mês", "Medalha", "Bônus", "Critérios"])
        self._setup_table(self.table_medals)
        self.tabs.addTab(self._tab_page(self.table_medals), "Medalhas")

        self.table_ranks = QTableWidget(0, 4)
        self.table_ranks.setHorizontalHeaderLabels(["Status", "Rank", "Nível", "Descrição"])
        self._setup_table(self.table_ranks)
        self.tabs.addTab(self._tab_page(self.table_ranks), "Ranks")

        self.table_achievements = QTableWidget(0, 4)
        self.table_achievements.setHorizontalHeaderLabels(["Status", "Conquista", "Bônus", "Descrição"])
        self._setup_table(self.table_achievements)
        self.tabs.addTab(self._tab_page(self.table_achievements), "Conquistas")

        self.table_events = QTableWidget(0, 3)
        self.table_events.setHorizontalHeaderLabels(["Tipo", "XP", "Descrição"])
        self._setup_table(self.table_events)
        self.tabs.addTab(self._tab_page(self.table_events), "Histórico XP")

        root.addWidget(self.tabs, 1)

    def _metric_box(self, title: str, value: str):
        box = QFrame()
        box.setObjectName("MetricBox")
        layout = QVBoxLayout(box)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        lbl_title = QLabel(title)
        lbl_title.setObjectName("MetricTitle")
        lbl_value = QLabel(value)
        lbl_value.setObjectName("MetricValue")
        lbl_value.setWordWrap(True)

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_value)
        return box, lbl_title, lbl_value

    def _mission_card(self):
        card = QFrame()
        card.setObjectName("MissionMiniCard")
        card.setProperty("done", False)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        title = QLabel("—")
        title.setObjectName("MissionTitle")
        title.setWordWrap(True)
        status = QLabel("—")
        status.setObjectName("MissionStatus")
        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setTextVisible(True)

        layout.addWidget(title)
        layout.addWidget(status)
        layout.addWidget(progress)
        return card, title, status, progress

    def _tab_page(self, widget: QWidget):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        layout.addWidget(widget)
        return page

    def _setup_table(self, table: QTableWidget):
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        for column_index in range(2, table.columnCount()):
            table.horizontalHeader().setSectionResizeMode(column_index, QHeaderView.Stretch)

    def _refresh_dynamic_property(self, widget: QWidget):
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def set_data(self, resumo: dict):
        from PySide6.QtWidgets import QTableWidgetItem

        self.lbl_month.setText(f'Mês: {resumo.get("mes", "—")}')
        nivel = int(resumo.get("nivel", 1) or 1)
        titulo = str(resumo.get("titulo", "Aprendiz Virtum") or "Aprendiz Virtum")
        xp_total = int(resumo.get("xp_total", 0) or 0)
        xp_atual = int(resumo.get("xp_nivel_atual", 0) or 0)
        xp_proximo = int(resumo.get("xp_proximo_nivel", 250) or 250)
        progresso = float(resumo.get("progresso_nivel", 0) or 0)
        conquistas_total = int(resumo.get("conquistas_total", 0) or 0)
        conquistas_desbloqueadas = int(resumo.get("conquistas_desbloqueadas", 0) or 0)
        medalhas_total = int(resumo.get("medalhas_total", 0) or 0)
        medalhas_diamante = int(resumo.get("medalhas_diamante", 0) or 0)
        medalha_mes = resumo.get("medalha_mes") or {}
        rank_atual = resumo.get("rank_atual") or {}
        rank_proximo = resumo.get("rank_proximo") or {}
        rank_progresso = float(resumo.get("rank_progresso", 0) or 0)
        niveis_para_proximo = int(resumo.get("rank_niveis_para_proximo", 0) or 0)
        missoes = resumo.get("missoes", []) or []

        rank_emoji = rank_atual.get("emoji", "🌱") or "🌱"
        rank_nome = rank_atual.get("nome", "Aprendiz Financeiro") or "Aprendiz Financeiro"
        rank_descricao = rank_atual.get("descricao", "Comece registrando movimentações e fechando o mês com clareza.") or ""

        self.lbl_rank_emoji.setText(rank_emoji)
        self.lbl_rank_name.setText(f"{rank_emoji} {rank_nome}")
        self.lbl_rank_description.setText(rank_descricao)
        self.lbl_xp_level.setText(f"Nv. {nivel} • {titulo} • {xp_atual}/{xp_proximo} XP para o próximo nível")
        self.progress_level.setValue(max(0, min(int(progresso), 100)))
        self.progress_level.setFormat(f"{progresso:.0f}%")

        self.metric_level_value.setText(f"Nv. {nivel}")
        self.metric_xp_value.setText(f"{xp_total} XP")
        if rank_proximo:
            self.metric_next_value.setText(f'{rank_proximo.get("emoji", "")} {rank_proximo.get("nome", "")}\nfaltam {niveis_para_proximo} nível(is)')
        else:
            self.metric_next_value.setText("Rank máximo")
        if medalha_mes:
            self.metric_medal_value.setText(f'{medalha_mes.get("emoji", "")} {medalha_mes.get("nome", "Medalha mensal")}')
        else:
            self.metric_medal_value.setText("Ainda não fechado")

        concluidas = sum(1 for missao in missoes if str(missao.get("status", "")).lower().startswith("concl"))
        self.lbl_mission_summary.setText(f"{concluidas}/{len(missoes)} concluídas")
        self.lbl_quick_achievements.setText(f"🏆 Conquistas: {conquistas_desbloqueadas}/{conquistas_total} desbloqueadas")
        self.lbl_quick_medals.setText(f"🏅 Medalhas: {medalhas_total} no histórico • {medalhas_diamante} diamante")
        if rank_proximo:
            self.lbl_quick_tip.setText(
                f"🎯 Próximo marco: {rank_proximo.get('emoji', '')} {rank_proximo.get('nome', '')}. "
                f"Progresso de rank: {rank_progresso:.0f}%."
            )
        else:
            self.lbl_quick_tip.setText("👑 Você alcançou o maior rank financeiro do Virtum.")

        for index, card_data in enumerate(self.mission_cards):
            if index >= len(missoes):
                card_data["card"].hide()
                continue

            missao = missoes[index]
            card_data["card"].show()
            progresso_atual = int(missao.get("progresso", 0) or 0)
            alvo = int(missao.get("alvo", 1) or 1)
            percentual = (progresso_atual / alvo * 100.0) if alvo > 0 else 0.0
            concluida = str(missao.get("status", "")).lower().startswith("concl")

            card_data["title"].setText(str(missao.get("nome", "")))
            card_data["status"].setText(("✅ Concluída" if concluida else "○ Em andamento") + f" • +{int(missao.get('xp', 0) or 0)} XP")
            card_data["progress"].setValue(max(0, min(int(percentual), 100)))
            card_data["progress"].setFormat(f"{progresso_atual}/{alvo}")
            card_data["card"].setProperty("done", concluida)
            self._refresh_dynamic_property(card_data["card"])

        self.table_missions.setRowCount(0)
        for missao in missoes:
            row_index = self.table_missions.rowCount()
            self.table_missions.insertRow(row_index)
            progresso_atual = int(missao.get("progresso", 0) or 0)
            alvo = int(missao.get("alvo", 1) or 1)
            percentual = (progresso_atual / alvo * 100.0) if alvo > 0 else 0.0
            progress_bar = QProgressBar()
            progress_bar.setRange(0, 100)
            progress_bar.setValue(max(0, min(int(percentual), 100)))
            progress_bar.setFormat(f"{percentual:.0f}%")
            progress_bar.setTextVisible(True)

            self.table_missions.setItem(row_index, 0, QTableWidgetItem(str(missao.get("nome", ""))))
            self.table_missions.setItem(row_index, 1, QTableWidgetItem(f"{progresso_atual}/{alvo}"))
            self.table_missions.setItem(row_index, 2, QTableWidgetItem(f'+{int(missao.get("xp", 0) or 0)} XP'))
            self.table_missions.setItem(row_index, 3, QTableWidgetItem(str(missao.get("status", "—"))))
            self.table_missions.setCellWidget(row_index, 4, progress_bar)

        self.table_medals.setRowCount(0)
        for medalha in resumo.get("medalhas", []) or []:
            row_index = self.table_medals.rowCount()
            self.table_medals.insertRow(row_index)
            self.table_medals.setItem(row_index, 0, QTableWidgetItem(str(medalha.get("mes", ""))))
            self.table_medals.setItem(row_index, 1, QTableWidgetItem(f'{medalha.get("emoji", "")} {medalha.get("nome", "")}'))
            self.table_medals.setItem(row_index, 2, QTableWidgetItem(f'+{int(medalha.get("xp_bonus", 0) or 0)} XP'))
            self.table_medals.setItem(row_index, 3, QTableWidgetItem(str(medalha.get("criterios", ""))))

        self.table_ranks.setRowCount(0)
        for rank in resumo.get("ranks", []) or []:
            row_index = self.table_ranks.rowCount()
            self.table_ranks.insertRow(row_index)
            if rank.get("atual"):
                status = "⭐ Atual"
            elif rank.get("desbloqueado"):
                status = "✅"
            else:
                status = "🔒"
            self.table_ranks.setItem(row_index, 0, QTableWidgetItem(status))
            self.table_ranks.setItem(row_index, 1, QTableWidgetItem(f'{rank.get("emoji", "")} {rank.get("nome", "")}'))
            self.table_ranks.setItem(row_index, 2, QTableWidgetItem(f'Nv. {int(rank.get("nivel_minimo", 1) or 1)}'))
            self.table_ranks.setItem(row_index, 3, QTableWidgetItem(str(rank.get("descricao", ""))))

        self.table_achievements.setRowCount(0)
        for conquista in resumo.get("conquistas", []) or []:
            row_index = self.table_achievements.rowCount()
            self.table_achievements.insertRow(row_index)
            desbloqueada = int(conquista.get("desbloqueada", 0) or 0) == 1
            self.table_achievements.setItem(row_index, 0, QTableWidgetItem("✅" if desbloqueada else "🔒"))
            self.table_achievements.setItem(row_index, 1, QTableWidgetItem(str(conquista.get("nome", ""))))
            self.table_achievements.setItem(row_index, 2, QTableWidgetItem(f'+{int(conquista.get("xp_bonus", 0) or 0)} XP'))
            self.table_achievements.setItem(row_index, 3, QTableWidgetItem(str(conquista.get("descricao", ""))))

        self.table_events.setRowCount(0)
        for evento in resumo.get("eventos", []) or []:
            row_index = self.table_events.rowCount()
            self.table_events.insertRow(row_index)
            self.table_events.setItem(row_index, 0, QTableWidgetItem(str(evento.get("tipo", ""))))
            self.table_events.setItem(row_index, 1, QTableWidgetItem(f'+{int(evento.get("xp", 0) or 0)} XP'))
            self.table_events.setItem(row_index, 2, QTableWidgetItem(str(evento.get("descricao", ""))))
