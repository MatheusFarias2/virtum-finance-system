from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QEasingCurve, QParallelAnimationGroup, QPropertyAnimation, QSize, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..constants import PALETAS
from ..db import (
    aplicar_fixos_automaticos,
    atualizar_investimento,
    atualizar_orcamento_categoria,
    atualizar_meta_financeira,
    atualizar_receita_extra,
    conectar,
    criar_investimento,
    criar_meta_financeira,
    criar_receita_extra,
    gerar_relatorio_mensal,
    listar_gastos_do_mes,
    listar_investimentos,
    migrar_banco,
    obter_salario,
    obter_tema,
    resumo_investimentos,
    resumo_metas_financeiras,
    resumo_gamificacao,
    resumo_receitas_do_mes,
    resumo_orcamentos_do_mes,
    salvar_fechamento,
    salvar_orcamento_categoria,
    salvar_salario,
    salvar_simulacao_investimentos,
    salvar_tema,
    total_gastos_do_mes,
    total_receitas_extras_do_mes,
)
from ..themes import build_stylesheet
from ..utils import br_date, money, msg_err, msg_yesno
from .dialogs import BudgetDialog, ExpenseDialog, FixosDialog, GoalDialog, IncomeDialog, InvestmentDialog, SalaryDialog, ThemeDialog
from .pages import BudgetsPage, DashboardPage, ExpensesPage, FechamentosPage, GamificationPage, GoalsPage, GraphPage, HistoryPage, IncomePage, InvestmentsPage, MonthlyReportPage
from .widgets import AnimatedStackedWidget, LoadingOverlay, SidebarButton
from ..services.investimentos_calculadora import comparar_investimentos


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        migrar_banco()
        aplicar_fixos_automaticos()
        self.theme_key = obter_tema()

        self.setWindowTitle("Virtum Finance")
        self.resize(1100, 720)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar_expanded = 240
        self.sidebar_collapsed = 72
        self.sidebar_is_collapsed = False

        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setMinimumWidth(self.sidebar_collapsed)
        self.sidebar.setMaximumWidth(self.sidebar_expanded)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(12, 12, 12, 12)
        sidebar_layout.setSpacing(10)

        top = QHBoxLayout()
        self.btn_toggle = QPushButton("☰")
        self.btn_toggle.setObjectName("BtnGhost")
        self.btn_toggle.setFixedSize(QSize(38, 38))
        self.btn_toggle.clicked.connect(self.toggle_sidebar)
        top.addWidget(self.btn_toggle)
        top.addStretch(1)
        sidebar_layout.addLayout(top)

        self.lbl_brand = QLabel("Virtum Finance")
        self.lbl_brand.setObjectName("H1")
        self.lbl_sub = QLabel("controle + sistema")
        self.lbl_sub.setObjectName("Subtle")
        sidebar_layout.addWidget(self.lbl_brand)
        sidebar_layout.addWidget(self.lbl_sub)
        sidebar_layout.addSpacing(4)

        self._build_sidebar(sidebar_layout)

        layout.addWidget(self.sidebar)

        self.stack = AnimatedStackedWidget()
        layout.addWidget(self.stack, 1)

        self.loading = LoadingOverlay(root)

        self.page_dash = DashboardPage()
        self.page_expenses = ExpensesPage()
        self.page_gamification = GamificationPage()
        self.page_graph = GraphPage()
        self.page_budgets = BudgetsPage()
        self.page_goals = GoalsPage()
        self.page_hist = HistoryPage()
        self.page_income = IncomePage()
        self.page_invest = InvestmentsPage()
        self.page_report = MonthlyReportPage()
        self.page_fech = FechamentosPage()

        self.stack.addWidget(self.page_dash)
        self.stack.addWidget(self.page_expenses)
        self.stack.addWidget(self.page_gamification)
        self.stack.addWidget(self.page_graph)
        self.stack.addWidget(self.page_budgets)
        self.stack.addWidget(self.page_goals)
        self.stack.addWidget(self.page_hist)
        self.stack.addWidget(self.page_income)
        self.stack.addWidget(self.page_invest)
        self.stack.addWidget(self.page_report)
        self.stack.addWidget(self.page_fech)

        self.btn_dash.setChecked(True)
        self.stack.setCurrentWidget(self.page_dash)

        self.page_dash.btn_new.clicked.connect(self.new_expense)
        self.page_dash.btn_income.clicked.connect(self.new_income)
        self.page_dash.btn_invest.clicked.connect(self.new_investment)
        self.page_dash.btn_close_month.clicked.connect(self.close_month)
        self.page_dash.btn_gastos.clicked.connect(self.open_expenses)
        self.page_dash.btn_report.clicked.connect(self.open_report)
        self.page_dash.btn_graph.clicked.connect(self.open_graph)
        self.page_expenses.btn_new.clicked.connect(self.new_expense)
        self.page_expenses.table.cellDoubleClicked.connect(self.edit_selected_expense)
        self.page_budgets.btn_new.clicked.connect(self.new_budget)
        self.page_budgets.table.cellDoubleClicked.connect(self.edit_selected_budget)
        self.page_goals.btn_new.clicked.connect(self.new_goal)
        self.page_goals.table.cellDoubleClicked.connect(self.edit_selected_goal)
        self.page_hist.btn_delete.clicked.connect(self.delete_selected_closure)
        self.page_income.btn_new.clicked.connect(self.new_income)
        self.page_income.table.cellDoubleClicked.connect(self.edit_selected_income)
        self.page_invest.btn_new.clicked.connect(self.new_investment)
        self.page_invest.table.cellDoubleClicked.connect(self.edit_selected_investment)
        self.page_invest.btn_compare.clicked.connect(self.compare_investments)
        self.page_fech.btn_close_month.clicked.connect(self.close_month)
        self.page_fech.btn_graph.clicked.connect(self.open_graph)

        self._build_sidebar_animation()

        self.apply_styles()
        self.refresh_all()


    def _build_sidebar(self, sidebar_layout: QVBoxLayout):
        self._nav_buttons = []
        self._group_buttons = []
        self._sidebar_buttons = []
        self._button_to_group = {}
        self._group_bodies = {}
        self._open_group_key = None

        self.btn_dash = SidebarButton("🏠", "Dashboard")
        self._add_sidebar_button(sidebar_layout, self.btn_dash)

        self.btn_movimentacoes = SidebarButton("💸", "Movimentações")
        self.btn_expenses = SidebarButton("💳", "Gastos", sub=True)
        self.btn_income = SidebarButton("➕", "Entradas", sub=True)
        self.btn_invest = SidebarButton("📈", "Investimentos", sub=True)
        self.btn_fixos = SidebarButton("📌", "Fixos", sub=True)
        self._add_sidebar_group(
            sidebar_layout,
            "movimentacoes",
            self.btn_movimentacoes,
            [self.btn_expenses, self.btn_income, self.btn_invest, self.btn_fixos],
        )

        self.btn_planejamento = SidebarButton("🎯", "Planejamento")
        self.btn_budgets = SidebarButton("📊", "Orçamentos", sub=True)
        self.btn_goals = SidebarButton("🏆", "Metas", sub=True)
        self._add_sidebar_group(
            sidebar_layout,
            "planejamento",
            self.btn_planejamento,
            [self.btn_budgets, self.btn_goals],
        )

        self.btn_analises = SidebarButton("📈", "Análises")
        self.btn_report = SidebarButton("🧾", "Relatório", sub=True)
        self.btn_graph = SidebarButton("📉", "Gráfico mensal", sub=True)
        self.btn_hist = SidebarButton("🗓️", "Histórico", sub=True)
        self.btn_fech = SidebarButton("📅", "Fechamentos", sub=True)
        self._add_sidebar_group(
            sidebar_layout,
            "analises",
            self.btn_analises,
            [self.btn_report, self.btn_graph, self.btn_hist, self.btn_fech],
        )

        self.btn_gamification = SidebarButton("🎮", "Gamificação")
        self._add_sidebar_button(sidebar_layout, self.btn_gamification)

        sidebar_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.btn_configuracoes = SidebarButton("⚙️", "Configurações")
        self.btn_salary = SidebarButton("💰", "Salário", sub=True)
        self.btn_theme = SidebarButton("🎨", "Tema", sub=True)
        self._add_sidebar_group(
            sidebar_layout,
            "configuracoes",
            self.btn_configuracoes,
            [self.btn_salary, self.btn_theme],
        )

        self.btn_help = SidebarButton("❓", "Ajuda")
        self.btn_help.setCheckable(False)
        self.btn_help.clicked.connect(self.show_features)
        sidebar_layout.addWidget(self.btn_help)
        self._sidebar_buttons.append(self.btn_help)

    def _add_sidebar_button(self, sidebar_layout: QVBoxLayout, button: SidebarButton):
        button.clicked.connect(self.on_sidebar_clicked)
        sidebar_layout.addWidget(button)
        self._nav_buttons.append(button)
        self._sidebar_buttons.append(button)

    def _add_sidebar_group(self, sidebar_layout: QVBoxLayout, group_key: str, header_button: SidebarButton, buttons: list[SidebarButton]):
        header_button.clicked.connect(lambda checked=False, key=group_key: self.toggle_sidebar_group(key))
        sidebar_layout.addWidget(header_button)
        self._group_buttons.append(header_button)
        self._sidebar_buttons.append(header_button)

        body = QFrame()
        body.setObjectName("SidebarGroupBody")
        body.setVisible(False)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 4)
        body_layout.setSpacing(4)

        for button in buttons:
            button.clicked.connect(self.on_sidebar_clicked)
            body_layout.addWidget(button)
            self._nav_buttons.append(button)
            self._sidebar_buttons.append(button)
            self._button_to_group[button] = group_key

        sidebar_layout.addWidget(body)
        self._group_bodies[group_key] = {"button": header_button, "body": body, "items": buttons}

    def toggle_sidebar_group(self, group_key: str):
        if self.sidebar_is_collapsed:
            self.toggle_sidebar()
            self._set_sidebar_group(group_key)
            return

        is_open = self._open_group_key == group_key
        self._set_sidebar_group(None if is_open else group_key)

    def _set_sidebar_group(self, group_key: str | None):
        self._open_group_key = group_key
        for key, data in self._group_bodies.items():
            opened = key == group_key and not self.sidebar_is_collapsed
            data["body"].setVisible(opened)
            data["button"].setChecked(opened)

    def _select_sidebar_button(self, button: SidebarButton):
        for item in self._nav_buttons:
            item.setChecked(item is button)

        group_key = self._button_to_group.get(button)
        self._set_sidebar_group(group_key)

    def _build_sidebar_animation(self):
        self.anim_group = QParallelAnimationGroup(self)

        self.anim_max = QPropertyAnimation(self.sidebar, b"maximumWidth", self)
        self.anim_max.setEasingCurve(QEasingCurve.OutCubic)
        self.anim_max.setDuration(220)

        self.anim_min = QPropertyAnimation(self.sidebar, b"minimumWidth", self)
        self.anim_min.setEasingCurve(QEasingCurve.OutCubic)
        self.anim_min.setDuration(220)

        self.anim_group.addAnimation(self.anim_max)
        self.anim_group.addAnimation(self.anim_min)

    def apply_styles(self):
        self.setStyleSheet(build_stylesheet(getattr(self, "theme_key", "original")))
        theme = PALETAS.get(getattr(self, "theme_key", "original"), PALETAS["original"])
        self.page_graph.set_theme(theme)
        self.page_invest.set_theme(theme)

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
        for button in self._sidebar_buttons:
            button.set_collapsed(collapsed)
        self._set_sidebar_group(self._open_group_key)

    def on_sidebar_clicked(self):
        button = self.sender()
        group_key = self._button_to_group.get(button)

        if button is self.btn_salary:
            self._set_sidebar_group(group_key)
            button.setChecked(False)
            self.edit_salary()
            return

        if button is self.btn_fixos:
            self._set_sidebar_group(group_key)
            button.setChecked(False)
            self.edit_fixos()
            return

        if button is self.btn_theme:
            self._set_sidebar_group(group_key)
            button.setChecked(False)
            self.edit_theme()
            return

        self._select_sidebar_button(button)

        if button is self.btn_dash:
            self.stack.set_current_widget_animated(self.page_dash, direction=-1)
        elif button is self.btn_expenses:
            self.stack.set_current_widget_animated(self.page_expenses, direction=1)
        elif button is self.btn_income:
            self.stack.set_current_widget_animated(self.page_income, direction=1)
        elif button is self.btn_invest:
            self.stack.set_current_widget_animated(self.page_invest, direction=1)
        elif button is self.btn_budgets:
            self.stack.set_current_widget_animated(self.page_budgets, direction=1)
        elif button is self.btn_goals:
            self.stack.set_current_widget_animated(self.page_goals, direction=1)
        elif button is self.btn_report:
            self.stack.set_current_widget_animated(self.page_report, direction=1)
        elif button is self.btn_graph:
            self.stack.set_current_widget_animated(self.page_graph, direction=1)
        elif button is self.btn_hist:
            self.stack.set_current_widget_animated(self.page_hist, direction=1)
        elif button is self.btn_fech:
            self.stack.set_current_widget_animated(self.page_fech, direction=1)
        elif button is self.btn_gamification:
            self.stack.set_current_widget_animated(self.page_gamification, direction=1)

        self.refresh_all()

    def _run_with_loading(self, callback, text="Carregando…"):
        shown = {"value": False}

        def show_overlay():
            shown["value"] = True
            self.loading.show_over(text)

        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(show_overlay)
        timer.start(160)

        try:
            callback()
        finally:
            timer.stop()
            if shown["value"]:
                self.loading.hide_over()

    def refresh_all(self):
        def work():
            aplicar_fixos_automaticos()
            self.refresh_dashboard()
            self.refresh_expenses()
            self.refresh_gamification()
            self.refresh_history()
            self.refresh_graph()
            self.refresh_budgets()
            self.refresh_goals()
            self.refresh_income()
            self.refresh_fechamentos()
            self.refresh_investments()
            self.refresh_report()

        self._run_with_loading(work, text="Atualizando…")

    def refresh_dashboard(self):
        hoje = datetime.now()
        self.page_dash.lbl_today.setText(f"Hoje: {hoje:%d/%m/%Y} • {hoje.strftime('%Y-%m')}")

        mes = hoje.strftime("%Y-%m")
        rows = listar_gastos_do_mes(mes)
        total = sum(float(row[2]) for row in rows)
        salario = obter_salario()
        receitas_extra = total_receitas_extras_do_mes(mes)
        receita_total = salario + receitas_extra
        saldo = receita_total - total

        gastos_por_categoria: dict[str, float] = {}
        for _, categoria, valor, _ in rows:
            gastos_por_categoria[str(categoria or "Outros")] = gastos_por_categoria.get(str(categoria or "Outros"), 0.0) + float(valor or 0)

        maior_categoria = ""
        maior_categoria_total = 0.0
        if gastos_por_categoria:
            maior_categoria, maior_categoria_total = max(gastos_por_categoria.items(), key=lambda item: item[1])

        resumo_investido = resumo_investimentos()
        resumo_orcamento = resumo_orcamentos_do_mes(mes)
        resumo_metas = resumo_metas_financeiras()
        resumo_virtum = resumo_gamificacao(mes, recalcular=True)

        self.page_dash.set_summary({
            "saldo": saldo,
            "total_gastos": total,
            "receitas_extra": receitas_extra,
            "total_investido": float(resumo_investido.get("total_aplicado", 0) or 0),
            "saldo_orcamento": float(resumo_orcamento.get("saldo_orcamento", 0) or 0),
            "metas_quantidade": int(resumo_metas.get("quantidade", 0) or 0),
            "metas_concluidas": int(resumo_metas.get("concluidas", 0) or 0),
            "maior_categoria": maior_categoria,
            "maior_categoria_total": maior_categoria_total,
            "nivel": int(resumo_virtum.get("nivel", 1) or 1),
            "titulo": str(resumo_virtum.get("titulo", "Aprendiz Virtum") or "Aprendiz Virtum"),
            "rank_atual": resumo_virtum.get("rank_atual") or {},
            "rank_proximo": resumo_virtum.get("rank_proximo") or {},
            "xp_nivel_atual": int(resumo_virtum.get("xp_nivel_atual", 0) or 0),
            "xp_proximo_nivel": int(resumo_virtum.get("xp_proximo_nivel", 250) or 250),
            "progresso_nivel": float(resumo_virtum.get("progresso_nivel", 0) or 0),
        })

    def refresh_expenses(self):
        mes = datetime.now().strftime("%Y-%m")
        rows = listar_gastos_do_mes(mes)
        total = sum(float(row[2]) for row in rows)
        self.page_expenses.set_overview(mes, total, len(rows))

        table = self.page_expenses.table
        table.setRowCount(0)
        for gasto_id, categoria, valor, data_iso in rows:
            row_index = table.rowCount()
            table.insertRow(row_index)
            table.setItem(row_index, 0, QTableWidgetItem(str(gasto_id)))
            table.setItem(row_index, 1, QTableWidgetItem(categoria))
            table.setItem(row_index, 2, QTableWidgetItem(money(valor)))
            table.setItem(row_index, 3, QTableWidgetItem(br_date(data_iso)))

    def refresh_gamification(self):
        mes_atual = datetime.now().strftime("%Y-%m")
        self.page_gamification.set_data(resumo_gamificacao(mes_atual, recalcular=True))

    def refresh_history(self):
        with conectar() as conn:
            cur = conn.cursor()
            cur.execute("SELECT mes, total, receita_total, saldo FROM resumo ORDER BY mes DESC")
            rows = cur.fetchall()

        soma = sum(float(row[1] or 0) for row in rows)
        self.page_hist.lbl_sum.setText(f"Somatório de saídas: {money(soma)}")

        table = self.page_hist.table
        table.setRowCount(0)
        for mes, total, receita_total, saldo in rows:
            row_index = table.rowCount()
            table.insertRow(row_index)
            table.setItem(row_index, 0, QTableWidgetItem(str(mes)))
            table.setItem(row_index, 1, QTableWidgetItem(money(float(total or 0))))
            table.setItem(row_index, 2, QTableWidgetItem(money(float(receita_total or 0))))
            table.setItem(row_index, 3, QTableWidgetItem(money(float(saldo or 0))))


    def refresh_graph(self):
        with conectar() as conn:
            cur = conn.cursor()
            cur.execute("SELECT mes, total FROM resumo ORDER BY mes ASC")
            rows = cur.fetchall()

        meses = [str(row[0]) for row in rows]
        totais = [float(row[1] or 0) for row in rows]
        theme = PALETAS.get(getattr(self, "theme_key", "original"), PALETAS["original"])
        self.page_graph.set_theme(theme)
        self.page_invest.set_theme(theme)
        self.page_graph.set_data(meses, totais, salary=obter_salario(), theme=theme)

    def refresh_budgets(self):
        mes_atual = datetime.now().strftime("%Y-%m")
        self.page_budgets.set_data(resumo_orcamentos_do_mes(mes_atual))

    def refresh_goals(self):
        self.page_goals.set_data(resumo_metas_financeiras())

    def refresh_income(self):
        mes_atual = datetime.now().strftime("%Y-%m")
        self.page_income.set_data(resumo_receitas_do_mes(mes_atual))

    def refresh_report(self):
        mes_atual = datetime.now().strftime("%Y-%m")
        self.page_report.set_data(gerar_relatorio_mensal(mes_atual))

    def refresh_fechamentos(self):
        mes_atual = datetime.now().strftime("%Y-%m")
        total_mes = total_gastos_do_mes(mes_atual)
        salario = obter_salario()
        receitas_extra = total_receitas_extras_do_mes(mes_atual)
        self.page_fech.set_month_summary(mes_atual, total_mes, salario, receitas_extra)

        with conectar() as conn:
            cur = conn.cursor()
            cur.execute("SELECT mes, total, receita_total, saldo FROM resumo ORDER BY mes DESC LIMIT 24")
            rows = cur.fetchall()

        table = self.page_fech.table
        table.setRowCount(0)
        for mes, total, receita_total, saldo in rows:
            row_index = table.rowCount()
            table.insertRow(row_index)
            table.setItem(row_index, 0, QTableWidgetItem(str(mes)))
            table.setItem(row_index, 1, QTableWidgetItem(money(float(total or 0))))
            table.setItem(row_index, 2, QTableWidgetItem(money(float(receita_total or 0))))
            table.setItem(row_index, 3, QTableWidgetItem(money(float(saldo or 0))))

    def refresh_investments(self):
        resumo = resumo_investimentos()
        self.page_invest.set_overview(resumo)

        table = self.page_invest.table
        table.setRowCount(0)
        for investimento in listar_investimentos():
            resultado_item = float(investimento.get("valor_atual", 0) or 0) - float(investimento.get("valor_aplicado", 0) or 0)
            row_index = table.rowCount()
            table.insertRow(row_index)
            table.setItem(row_index, 0, QTableWidgetItem(str(investimento.get("id"))))
            table.setItem(row_index, 1, QTableWidgetItem(str(investimento.get("nome") or "")))
            table.setItem(row_index, 2, QTableWidgetItem(str(investimento.get("tipo") or "Outro")))
            table.setItem(row_index, 3, QTableWidgetItem(money(float(investimento.get("valor_aplicado", 0) or 0))))
            table.setItem(row_index, 4, QTableWidgetItem(money(float(investimento.get("valor_atual", 0) or 0))))
            table.setItem(row_index, 5, QTableWidgetItem(money(resultado_item)))
            table.setItem(row_index, 6, QTableWidgetItem(str(int(investimento.get("prazo_meses", 0) or 0))))
            table.setItem(row_index, 7, QTableWidgetItem(f'{float(investimento.get("percentual_cdi", 0) or 0):.2f}%'.replace(".", ",")))
            table.setItem(row_index, 8, QTableWidgetItem("Sim" if int(investimento.get("abater_saldo", 0) or 0) == 1 else "Não"))
            data_iso = str(investimento.get("data_aplicacao") or "")
            table.setItem(row_index, 9, QTableWidgetItem(br_date(data_iso) if data_iso else "—"))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "loading") and self.loading:
            self.loading.setGeometry(self.centralWidget().rect())

    def show_features(self):
        text = (
            "• Dashboard: visão rápida com cards, resumo do mês e progresso Virtum\n"
            "• Gastos: lista completa das saídas do mês, com edição por duplo clique\n"
            "• Entradas: receitas extras separadas do salário\n"
            "• Orçamentos: limite mensal por categoria\n"
            "• Metas: objetivos financeiros com progresso\n"
            "• Investimentos: controla patrimônio e pode abater o valor aplicado do saldo\n"
            "• Relatório: análise mensal automática\n"
            "• Fechamentos: salva ou regrava total, entradas e saldo no histórico\n"
            "• Gamificação: níveis, XP, missões e conquistas"
        )
        QMessageBox.information(self, "Funcionalidades", text)

    def open_expenses(self):
        self._select_sidebar_button(self.btn_expenses)
        self.stack.set_current_widget_animated(self.page_expenses, direction=1)
        self.refresh_expenses()

    def open_gamification(self):
        self._select_sidebar_button(self.btn_gamification)
        self.stack.set_current_widget_animated(self.page_gamification, direction=1)
        self.refresh_gamification()

    def open_budgets(self):
        self._select_sidebar_button(self.btn_budgets)
        self.stack.set_current_widget_animated(self.page_budgets, direction=1)
        self.refresh_budgets()

    def open_goals(self):
        self._select_sidebar_button(self.btn_goals)
        self.stack.set_current_widget_animated(self.page_goals, direction=1)
        self.refresh_goals()

    def open_income(self):
        self._select_sidebar_button(self.btn_income)
        self.stack.set_current_widget_animated(self.page_income, direction=1)
        self.refresh_income()

    def open_investments(self):
        self._select_sidebar_button(self.btn_invest)
        self.stack.set_current_widget_animated(self.page_invest, direction=1)
        self.refresh_investments()

    def open_report(self):
        self._select_sidebar_button(self.btn_report)
        self.stack.set_current_widget_animated(self.page_report, direction=1)
        self.refresh_report()

    def edit_salary(self):
        dialog = SalaryDialog(self)
        if dialog.exec() == QDialog.Accepted:
            try:
                valor = dialog.get_value()
            except Exception:
                msg_err(self, "Erro", "Salário inválido.")
                return
            salvar_salario(valor)
            self.refresh_all()

    def edit_fixos(self):
        dialog = FixosDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_all()

    def edit_theme(self):
        dialog = ThemeDialog(self, current=getattr(self, "theme_key", "original"))
        if dialog.exec() == QDialog.Accepted:
            key = dialog.get_key()
            self.theme_key = key
            salvar_tema(key)
            self.apply_styles()
            self.apply_sidebar_mode()
            self.refresh_all()

    def close_month(self):
        aplicar_fixos_automaticos()
        mes = datetime.now().strftime("%Y-%m")
        total = total_gastos_do_mes(mes)
        salario = obter_salario()
        receitas_extra = total_receitas_extras_do_mes(mes)
        receita_total = salario + receitas_extra
        saldo = receita_total - total

        if not msg_yesno(
            self,
            "Fechar mês",
            f"Mês: {mes}\n\nEntradas: {money(receita_total)}\nSaídas: {money(total)}\nSaldo: {money(saldo)}\n\nDeseja salvar/regravar este fechamento?",
        ):
            return

        try:
            medalha = salvar_fechamento(mes, total, saldo, receitas_extra, receita_total)
        except Exception as erro:
            msg_err(self, "Erro", f"Não foi possível salvar o fechamento.\n\n{erro}")
            return

        if medalha:
            texto_medalha = (
                f"\n\nMedalha do mês: {medalha.get('emoji', '')} {medalha.get('nome', 'Medalha mensal')}"
                f"\nBônus: +{int(medalha.get('xp_bonus', 0) or 0)} XP"
            )
        else:
            texto_medalha = ""

        QMessageBox.information(self, "Fechado!", f"Fechamento de {mes} salvo com sucesso.{texto_medalha}")
        self.refresh_all()

    def new_expense(self):
        dialog = ExpenseDialog(self, expense_id=None)
        if dialog.exec() == QDialog.Accepted:
            try:
                categoria, valor, descricao, data_iso = dialog.get_payload()
            except Exception:
                msg_err(self, "Erro", "Dados inválidos. Valor e data precisam estar corretos.")
                return

            with conectar() as conn:
                conn.execute(
                    "INSERT INTO gastos (categoria, valor, descricao, data) VALUES (?, ?, ?, ?)",
                    (categoria, valor, descricao, data_iso),
                )
            self.refresh_all()

    def edit_selected_expense(self, row, col):
        table = self.page_expenses.table
        item = table.item(row, 0)
        if not item:
            return

        try:
            expense_id = int(item.text())
        except ValueError:
            return

        dialog = ExpenseDialog(self, expense_id=expense_id)
        result = dialog.exec()
        if result == 2:
            self.refresh_all()
            return

        if result == QDialog.Accepted:
            try:
                categoria, valor, descricao, data_iso = dialog.get_payload()
            except Exception:
                msg_err(self, "Erro", "Dados inválidos.")
                return

            with conectar() as conn:
                conn.execute(
                    """
                    UPDATE gastos
                    SET categoria=?, valor=?, descricao=?, data=?
                    WHERE id=?
                    """,
                    (categoria, valor, descricao, data_iso, expense_id),
                )
            self.refresh_all()

    def new_budget(self):
        mes_atual = datetime.now().strftime("%Y-%m")
        dialog = BudgetDialog(self, orcamento_id=None, mes_atual=mes_atual)
        if dialog.exec() == QDialog.Accepted:
            try:
                mes, categoria, limite, observacoes = dialog.get_payload()
            except Exception:
                msg_err(self, "Erro", "Dados inválidos. Confira mês, categoria e limite.")
                return

            salvar_orcamento_categoria(mes, categoria, limite, observacoes)
            self.refresh_all()

    def edit_selected_budget(self, row, col):
        table = self.page_budgets.table
        item = table.item(row, 0)
        if not item:
            return

        try:
            orcamento_id = int(item.text())
        except ValueError:
            return

        dialog = BudgetDialog(self, orcamento_id=orcamento_id)
        result = dialog.exec()
        if result == 2:
            self.refresh_all()
            return

        if result == QDialog.Accepted:
            try:
                mes, categoria, limite, observacoes = dialog.get_payload()
            except Exception:
                msg_err(self, "Erro", "Dados inválidos. Confira mês, categoria e limite.")
                return

            atualizar_orcamento_categoria(orcamento_id, mes, categoria, limite, observacoes)
            self.refresh_all()

    def new_goal(self):
        dialog = GoalDialog(self, meta_id=None)
        if dialog.exec() == QDialog.Accepted:
            try:
                payload = dialog.get_payload()
            except Exception:
                msg_err(self, "Erro", "Dados inválidos. Confira nome, valores e data limite.")
                return

            criar_meta_financeira(*payload)
            self.refresh_all()

    def edit_selected_goal(self, row, col):
        table = self.page_goals.table
        item = table.item(row, 0)
        if not item:
            return

        try:
            meta_id = int(item.text())
        except ValueError:
            return

        dialog = GoalDialog(self, meta_id=meta_id)
        result = dialog.exec()
        if result == 2:
            self.refresh_all()
            return

        if result == QDialog.Accepted:
            try:
                payload = dialog.get_payload()
            except Exception:
                msg_err(self, "Erro", "Dados inválidos. Confira nome, valores e data limite.")
                return

            atualizar_meta_financeira(meta_id, *payload)
            self.refresh_all()

    def new_income(self):
        dialog = IncomeDialog(self, receita_id=None)
        if dialog.exec() == QDialog.Accepted:
            try:
                fonte, valor, descricao, data_iso = dialog.get_payload()
            except Exception:
                msg_err(self, "Erro", "Dados inválidos. Confira fonte, valor e data.")
                return

            criar_receita_extra(fonte, valor, descricao, data_iso)
            self.refresh_all()

    def edit_selected_income(self, row, col):
        table = self.page_income.table
        item = table.item(row, 0)
        if not item:
            return

        try:
            receita_id = int(item.text())
        except ValueError:
            return

        dialog = IncomeDialog(self, receita_id=receita_id)
        result = dialog.exec()
        if result == 2:
            self.refresh_all()
            return

        if result == QDialog.Accepted:
            try:
                fonte, valor, descricao, data_iso = dialog.get_payload()
            except Exception:
                msg_err(self, "Erro", "Dados inválidos. Confira fonte, valor e data.")
                return

            atualizar_receita_extra(receita_id, fonte, valor, descricao, data_iso)
            self.refresh_all()

    def new_investment(self):
        dialog = InvestmentDialog(self, investimento_id=None)
        if dialog.exec() == QDialog.Accepted:
            try:
                payload = dialog.get_payload()
            except Exception:
                msg_err(self, "Erro", "Dados inválidos. Confira nome, valores, taxas, prazo e data.")
                return

            criar_investimento(*payload)
            self.refresh_all()

    def edit_selected_investment(self, row, col):
        table = self.page_invest.table
        item = table.item(row, 0)
        if not item:
            return

        try:
            investimento_id = int(item.text())
        except ValueError:
            return

        dialog = InvestmentDialog(self, investimento_id=investimento_id)
        result = dialog.exec()
        if result == 2:
            self.refresh_all()
            return

        if result == QDialog.Accepted:
            try:
                payload = dialog.get_payload()
            except Exception:
                msg_err(self, "Erro", "Dados inválidos. Confira nome, valores, taxas, prazo e data.")
                return

            atualizar_investimento(investimento_id, *payload)
            self.refresh_all()

    def compare_investments(self):
        try:
            valor, prazo, cdi, selic, tr, percentual = self.page_invest.get_simulator_payload()
            comparativo = comparar_investimentos(valor, prazo, cdi, selic, tr, percentual)
            salvar_simulacao_investimentos(valor, prazo, cdi, selic, tr, percentual, comparativo)
        except Exception as erro:
            msg_err(self, "Simulador", f"Não foi possível calcular a simulação.\n\n{erro}")
            return

        self.page_invest.set_simulation_results(comparativo)
        self.page_invest.tabs.setCurrentIndex(3)

    def open_graph(self):
        self._select_sidebar_button(self.btn_graph)
        self.stack.set_current_widget_animated(self.page_graph, direction=1)
        self.refresh_graph()
        self.refresh_fechamentos()

    def delete_selected_closure(self):
        table = self.page_hist.table
        row = table.currentRow()
        if row < 0:
            msg_err(self, "Apagar", "Selecione um mês no histórico.")
            return

        item = table.item(row, 0)
        if not item:
            return
        mes = item.text()

        if not msg_yesno(self, "Confirmar", f"Apagar fechamento de {mes}? Isso remove do gráfico também."):
            return

        with conectar() as conn:
            conn.execute("DELETE FROM resumo WHERE mes=?", (mes,))
        self.refresh_all()
