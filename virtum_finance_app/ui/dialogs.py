from __future__ import annotations

from datetime import date, datetime

from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)

from ..constants import CATEGORIAS, FONTES_RECEITA, LIQUIDEZ_INVESTIMENTO, TIPOS_INVESTIMENTO
from ..db import aplicar_fixos_automaticos, conectar, excluir_investimento, excluir_meta_financeira, excluir_orcamento_categoria, excluir_receita_extra, obter_investimento, obter_meta_financeira, obter_orcamento, obter_receita_extra, obter_salario
from ..utils import br_date, iso_date, msg_err, msg_yesno, money, parse_money
from .widgets import FormDialog


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
        for key, label in self._map.items():
            self.cmb.addItem(label, key)

        for index in range(self.cmb.count()):
            if self.cmb.itemData(index) == current:
                self.cmb.setCurrentIndex(index)
                break

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
        self.input.setText(f"{obter_salario():.2f}".replace(".", ","))

        self.lay.addWidget(title)
        self.lay.addWidget(desc)
        self.lay.addWidget(self.input)

    def get_value(self):
        valor = parse_money(self.input.text())
        if valor < 0:
            raise ValueError("Salário não pode ser negativo.")
        return valor


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
        with conectar() as conn:
            cur = conn.cursor()
            cur.execute("SELECT categoria, valor, descricao, data FROM gastos WHERE id=?", (self.expense_id,))
            row = cur.fetchone()

        if not row:
            return

        categoria, valor, descricao, data_iso = row
        if categoria in CATEGORIAS:
            self.cmb_cat.setCurrentText(categoria)
        self.inp_val.setText(f"{float(valor or 0):.2f}".replace(".", ","))
        self.inp_desc.setText(descricao or "")
        self.inp_date.setText(br_date(data_iso))

    def _delete(self):
        if not msg_yesno(self, "Confirmar", f"Deletar gasto #{self.expense_id}?"):
            return
        with conectar() as conn:
            conn.execute("DELETE FROM gastos WHERE id=?", (self.expense_id,))
        self.done(2)

    def get_payload(self):
        categoria = self.cmb_cat.currentText()
        valor = parse_money(self.inp_val.text())
        if valor <= 0:
            raise ValueError("Valor precisa ser maior que zero.")
        data_iso = iso_date(self.inp_date.text())
        descricao = self.inp_desc.text().strip()
        return categoria, valor, descricao, data_iso


class IncomeDialog(FormDialog):
    def __init__(self, parent=None, receita_id=None):
        super().__init__("Entrada extra" if receita_id is None else f"Editar entrada #{receita_id}", parent)
        self.receita_id = receita_id
        self.resize(540, 420)

        titulo = QLabel("Entrada extra de dinheiro")
        titulo.setObjectName("PanelTitle")
        descricao = QLabel("Cadastre receitas avulsas além do salário, como freela, venda, bônus, Pix recebido ou reembolso.")
        descricao.setObjectName("Subtle")
        descricao.setWordWrap(True)

        self.cmb_fonte = QComboBox()
        self.cmb_fonte.addItems(FONTES_RECEITA)

        self.inp_valor = QLineEdit()
        self.inp_valor.setPlaceholderText("Ex: 250,00")

        self.inp_data = QLineEdit()
        self.inp_data.setPlaceholderText("DD/MM/AAAA")
        self.inp_data.setText(date.today().strftime("%d/%m/%Y"))

        self.inp_descricao = QLineEdit()
        self.inp_descricao.setPlaceholderText("Descrição opcional")

        self.lay.addWidget(titulo)
        self.lay.addWidget(descricao)
        self.lay.addWidget(QLabel("Fonte"))
        self.lay.addWidget(self.cmb_fonte)
        self.lay.addWidget(QLabel("Valor (R$)"))
        self.lay.addWidget(self.inp_valor)
        self.lay.addWidget(QLabel("Data"))
        self.lay.addWidget(self.inp_data)
        self.lay.addWidget(QLabel("Descrição"))
        self.lay.addWidget(self.inp_descricao)

        if self.receita_id is not None:
            self._load()
            self.btn_delete = QPushButton("Deletar")
            self.btn_delete.setObjectName("BtnGhostDanger")
            self.btn_delete.clicked.connect(self._delete)
            self.actions.insertWidget(0, self.btn_delete)

    def _load(self):
        receita = obter_receita_extra(int(self.receita_id))
        if not receita:
            return
        fonte = str(receita.get("fonte") or "Outros")
        if fonte in FONTES_RECEITA:
            self.cmb_fonte.setCurrentText(fonte)
        self.inp_valor.setText(f'{float(receita.get("valor") or 0):.2f}'.replace(".", ","))
        data_iso = str(receita.get("data") or "")
        if data_iso:
            self.inp_data.setText(br_date(data_iso))
        self.inp_descricao.setText(str(receita.get("descricao") or ""))

    def _delete(self):
        if not msg_yesno(self, "Confirmar", f"Deletar entrada #{self.receita_id}?"):
            return
        excluir_receita_extra(int(self.receita_id))
        self.done(2)

    def get_payload(self):
        fonte = self.cmb_fonte.currentText()
        valor = parse_money(self.inp_valor.text())
        if valor <= 0:
            raise ValueError("Valor precisa ser maior que zero.")
        data_iso = iso_date(self.inp_data.text())
        descricao = self.inp_descricao.text().strip()
        return fonte, valor, descricao, data_iso


class FixosDialog(FormDialog):
    def __init__(self, parent=None):
        super().__init__("Gastos fixos", parent)
        self.resize(720, 520)

        self.btn_ok.setText("Fechar")
        self.btn_ok.clicked.disconnect()
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.hide()

        title = QLabel("Fixos (recorrentes)")
        title.setObjectName("PanelTitle")
        desc = QLabel("Eles entram automaticamente no mês atual sem duplicar.")
        desc.setObjectName("Subtle")
        self.lay.addWidget(title)
        self.lay.addWidget(desc)

        form = QFrame()
        form.setObjectName("InlineBox")
        form_layout = QGridLayout(form)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setHorizontalSpacing(10)
        form_layout.setVerticalSpacing(8)

        self.cmb_cat = QComboBox()
        self.cmb_cat.addItems(CATEGORIAS)

        self.inp_val = QLineEdit()
        self.inp_val.setPlaceholderText("Valor (ex: 199,90)")

        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("Descrição (opcional)")

        self.btn_add = QPushButton("+ Adicionar fixo")
        self.btn_add.setObjectName("BtnAccent")
        self.btn_add.clicked.connect(self.add_fixo)

        form_layout.addWidget(QLabel("Categoria"), 0, 0)
        form_layout.addWidget(self.cmb_cat, 1, 0)
        form_layout.addWidget(QLabel("Valor (R$)"), 0, 1)
        form_layout.addWidget(self.inp_val, 1, 1)
        form_layout.addWidget(QLabel("Descrição"), 0, 2)
        form_layout.addWidget(self.inp_desc, 1, 2)
        form_layout.addWidget(self.btn_add, 2, 0, 1, 3)
        self.lay.addWidget(form)

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

        actions = QHBoxLayout()
        self.btn_toggle = QPushButton("Ativar / Pausar")
        self.btn_toggle.setObjectName("BtnGhost")
        self.btn_toggle.clicked.connect(self.toggle_ativo)

        self.btn_del = QPushButton("Deletar")
        self.btn_del.setObjectName("BtnGhostDanger")
        self.btn_del.clicked.connect(self.delete_fixo)

        actions.addWidget(self.btn_toggle)
        actions.addWidget(self.btn_del)
        actions.addStretch(1)
        self.lay.addLayout(actions)

        self.load_fixos()

    def load_fixos(self):
        with conectar() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, categoria, valor, ativo FROM fixos ORDER BY id DESC")
            rows = cur.fetchall()

        self.table.setRowCount(0)
        for fixo_id, categoria, valor, ativo in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(fixo_id)))
            self.table.setItem(row, 1, QTableWidgetItem(categoria or "Outros"))
            self.table.setItem(row, 2, QTableWidgetItem(money(float(valor or 0))))
            self.table.setItem(row, 3, QTableWidgetItem("Sim" if int(ativo or 0) == 1 else "Não"))

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if not item:
            return None
        try:
            return int(item.text())
        except ValueError:
            return None

    def add_fixo(self):
        try:
            valor = parse_money(self.inp_val.text())
            if valor <= 0:
                raise ValueError
        except Exception:
            msg_err(self, "Erro", "Valor inválido. Use algo como 199,90.")
            return

        categoria = self.cmb_cat.currentText()
        descricao = self.inp_desc.text().strip()

        with conectar() as conn:
            conn.execute(
                "INSERT INTO fixos (categoria, valor, descricao, ativo) VALUES (?, ?, ?, 1)",
                (categoria, valor, descricao),
            )

        aplicar_fixos_automaticos()
        self.inp_val.clear()
        self.inp_desc.clear()
        self.load_fixos()

    def toggle_ativo(self):
        fixo_id = self._selected_id()
        if fixo_id is None:
            msg_err(self, "Ativar/Pausar", "Selecione um fixo na lista.")
            return

        with conectar() as conn:
            cur = conn.cursor()
            cur.execute("SELECT ativo FROM fixos WHERE id=?", (fixo_id,))
            row = cur.fetchone()
            if not row:
                return
            novo = 0 if int(row[0] or 0) == 1 else 1
            cur.execute("UPDATE fixos SET ativo=? WHERE id=?", (novo, fixo_id))

        aplicar_fixos_automaticos()
        self.load_fixos()

    def delete_fixo(self):
        fixo_id = self._selected_id()
        if fixo_id is None:
            msg_err(self, "Deletar", "Selecione um fixo na lista.")
            return
        if not msg_yesno(self, "Confirmar", f"Deletar fixo #{fixo_id}?"):
            return

        with conectar() as conn:
            conn.execute("DELETE FROM fixos WHERE id=?", (fixo_id,))

        self.load_fixos()

class InvestmentDialog(FormDialog):
    def __init__(self, parent=None, investimento_id=None):
        super().__init__("Investir" if investimento_id is None else f"Editar investimento #{investimento_id}", parent)
        self.investimento_id = investimento_id
        self.resize(720, 680)

        titulo = QLabel("Cadastro de investimento")
        titulo.setObjectName("PanelTitle")
        aviso = QLabel("Simulação estimada. As taxas podem variar. Não é recomendação de investimento.")
        aviso.setObjectName("Subtle")
        aviso.setWordWrap(True)
        self.lay.addWidget(titulo)
        self.lay.addWidget(aviso)

        form = QFrame()
        form.setObjectName("InlineBox")
        grid = QGridLayout(form)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        self.inp_nome = QLineEdit()
        self.inp_nome.setPlaceholderText("Ex: Reserva Sicredi, Poupança emergência")

        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(TIPOS_INVESTIMENTO)

        self.inp_valor = QLineEdit()
        self.inp_valor.setPlaceholderText("Ex: 1000,00")

        self.inp_data = QLineEdit()
        self.inp_data.setPlaceholderText("DD/MM/AAAA")
        self.inp_data.setText(date.today().strftime("%d/%m/%Y"))

        self.inp_prazo = QLineEdit()
        self.inp_prazo.setPlaceholderText("Ex: 12")
        self.inp_prazo.setText("12")

        self.inp_percentual_cdi = QLineEdit()
        self.inp_percentual_cdi.setPlaceholderText("Ex: 100")
        self.inp_percentual_cdi.setText("100")

        self.inp_cdi = QLineEdit()
        self.inp_cdi.setPlaceholderText("Ex: 10,65")

        self.inp_selic = QLineEdit()
        self.inp_selic.setPlaceholderText("Ex: 10,50")

        self.inp_tr = QLineEdit()
        self.inp_tr.setPlaceholderText("Ex: 0,00")
        self.inp_tr.setText("0")

        self.inp_carencia = QLineEdit()
        self.inp_carencia.setPlaceholderText("Ex: 30")
        self.inp_carencia.setText("30")

        self.cmb_liquidez = QComboBox()
        self.cmb_liquidez.addItems(LIQUIDEZ_INVESTIMENTO)

        self.inp_obs = QLineEdit()
        self.inp_obs.setPlaceholderText("Observações opcionais")

        grid.addWidget(QLabel("Nome"), 0, 0)
        grid.addWidget(self.inp_nome, 1, 0)
        grid.addWidget(QLabel("Tipo"), 0, 1)
        grid.addWidget(self.cmb_tipo, 1, 1)

        grid.addWidget(QLabel("Valor aplicado (R$)"), 2, 0)
        grid.addWidget(self.inp_valor, 3, 0)
        grid.addWidget(QLabel("Data da aplicação"), 2, 1)
        grid.addWidget(self.inp_data, 3, 1)

        grid.addWidget(QLabel("Prazo (meses)"), 4, 0)
        grid.addWidget(self.inp_prazo, 5, 0)
        grid.addWidget(QLabel("% do CDI"), 4, 1)
        grid.addWidget(self.inp_percentual_cdi, 5, 1)

        grid.addWidget(QLabel("CDI anual estimado (%)"), 6, 0)
        grid.addWidget(self.inp_cdi, 7, 0)
        grid.addWidget(QLabel("Selic anual estimada (%)"), 6, 1)
        grid.addWidget(self.inp_selic, 7, 1)

        grid.addWidget(QLabel("TR mensal estimada (%)"), 8, 0)
        grid.addWidget(self.inp_tr, 9, 0)
        grid.addWidget(QLabel("Carência (dias)"), 8, 1)
        grid.addWidget(self.inp_carencia, 9, 1)

        grid.addWidget(QLabel("Liquidez"), 10, 0)
        grid.addWidget(self.cmb_liquidez, 11, 0)
        grid.addWidget(QLabel("Observações"), 10, 1)
        grid.addWidget(self.inp_obs, 11, 1)

        self.chk_abater_saldo = QCheckBox("Abater este investimento do saldo mensal")
        self.chk_abater_saldo.setChecked(True)
        self.chk_abater_saldo.setToolTip(
            "Quando marcado, o valor aplicado entra como saída do mês na categoria Investimentos."
        )
        grid.addWidget(self.chk_abater_saldo, 12, 0, 1, 2)

        info = QLabel("Marcado: o valor aplicado aparece no Dashboard, reduz o saldo e entra no fechamento do mês.")
        info.setObjectName("Subtle")
        info.setWordWrap(True)
        grid.addWidget(info, 13, 0, 1, 2)

        self.lay.addWidget(form)

        if self.investimento_id is not None:
            self._load()
            self.btn_del = QPushButton("Deletar")
            self.btn_del.setObjectName("BtnGhostDanger")
            self.btn_del.clicked.connect(self._delete)
            self.actions.insertWidget(0, self.btn_del)

    def _load(self):
        row = obter_investimento(int(self.investimento_id))
        if not row:
            return

        self.inp_nome.setText(str(row.get("nome") or ""))
        tipo = str(row.get("tipo") or "Outro")
        if tipo in TIPOS_INVESTIMENTO:
            self.cmb_tipo.setCurrentText(tipo)
        self.inp_valor.setText(f'{float(row.get("valor_aplicado") or 0):.2f}'.replace(".", ","))
        data_iso = str(row.get("data_aplicacao") or "")
        if data_iso:
            self.inp_data.setText(br_date(data_iso))
        self.inp_prazo.setText(str(int(row.get("prazo_meses") or 1)))
        self.inp_percentual_cdi.setText(f'{float(row.get("percentual_cdi") or 0):.2f}'.replace(".", ","))
        self.inp_cdi.setText(f'{float(row.get("taxa_cdi_anual") or 0):.2f}'.replace(".", ","))
        self.inp_selic.setText(f'{float(row.get("taxa_selic_anual") or 0):.2f}'.replace(".", ","))
        self.inp_tr.setText(f'{float(row.get("taxa_tr_mensal") or 0):.2f}'.replace(".", ","))
        self.inp_carencia.setText(str(int(row.get("carencia_dias") or 0)))
        liquidez = str(row.get("liquidez") or "Diária")
        if liquidez in LIQUIDEZ_INVESTIMENTO:
            self.cmb_liquidez.setCurrentText(liquidez)
        self.inp_obs.setText(str(row.get("observacoes") or ""))
        self.chk_abater_saldo.setChecked(bool(row.get("abater_saldo")))

    def _delete(self):
        if not msg_yesno(
            self,
            "Confirmar",
            f"Deletar investimento #{self.investimento_id}?\n\nSe ele estiver abatendo saldo, o lançamento vinculado também será removido.",
        ):
            return
        excluir_investimento(int(self.investimento_id))
        self.done(2)

    def get_payload(self):
        nome = self.inp_nome.text().strip()
        if not nome:
            raise ValueError("Nome obrigatório.")

        tipo = self.cmb_tipo.currentText()
        valor_aplicado = parse_money(self.inp_valor.text())
        if valor_aplicado <= 0:
            raise ValueError("Valor aplicado precisa ser maior que zero.")

        data_aplicacao = iso_date(self.inp_data.text())

        prazo_meses = int((self.inp_prazo.text() or "0").strip())
        if prazo_meses <= 0:
            raise ValueError("Prazo precisa ser maior que zero.")

        percentual_cdi = parse_money(self.inp_percentual_cdi.text() or "0")
        taxa_cdi_anual = parse_money(self.inp_cdi.text() or "0")
        taxa_selic_anual = parse_money(self.inp_selic.text() or "0")
        taxa_tr_mensal = parse_money(self.inp_tr.text() or "0")
        carencia_dias = int((self.inp_carencia.text() or "0").strip())
        if carencia_dias < 0:
            raise ValueError("Carência não pode ser negativa.")

        liquidez = self.cmb_liquidez.currentText()
        observacoes = self.inp_obs.text().strip()
        abater_saldo = self.chk_abater_saldo.isChecked()

        return (
            nome,
            tipo,
            valor_aplicado,
            data_aplicacao,
            prazo_meses,
            percentual_cdi,
            taxa_cdi_anual,
            taxa_selic_anual,
            taxa_tr_mensal,
            carencia_dias,
            liquidez,
            observacoes,
            abater_saldo,
        )


class BudgetDialog(FormDialog):
    def __init__(self, parent=None, orcamento_id=None, mes_atual=None):
        super().__init__("Orçamento" if orcamento_id is None else f"Editar orçamento #{orcamento_id}", parent)
        self.orcamento_id = orcamento_id
        self.resize(560, 360)

        titulo = QLabel("Orçamento por categoria")
        titulo.setObjectName("PanelTitle")
        descricao = QLabel("Defina quanto você quer gastar em uma categoria dentro de um mês.")
        descricao.setObjectName("Subtle")
        descricao.setWordWrap(True)

        self.inp_mes = QLineEdit()
        self.inp_mes.setPlaceholderText("AAAA-MM")
        self.inp_mes.setText(mes_atual or date.today().strftime("%Y-%m"))

        self.cmb_categoria = QComboBox()
        self.cmb_categoria.addItems(CATEGORIAS)

        self.inp_limite = QLineEdit()
        self.inp_limite.setPlaceholderText("Ex: 600,00")

        self.inp_observacoes = QLineEdit()
        self.inp_observacoes.setPlaceholderText("Observação opcional")

        self.lay.addWidget(titulo)
        self.lay.addWidget(descricao)
        self.lay.addWidget(QLabel("Mês"))
        self.lay.addWidget(self.inp_mes)
        self.lay.addWidget(QLabel("Categoria"))
        self.lay.addWidget(self.cmb_categoria)
        self.lay.addWidget(QLabel("Limite mensal (R$)"))
        self.lay.addWidget(self.inp_limite)
        self.lay.addWidget(QLabel("Observações"))
        self.lay.addWidget(self.inp_observacoes)

        if self.orcamento_id is not None:
            self._load()
            self.btn_delete = QPushButton("Deletar")
            self.btn_delete.setObjectName("BtnGhostDanger")
            self.btn_delete.clicked.connect(self._delete)
            self.actions.insertWidget(0, self.btn_delete)

    def _load(self):
        orcamento = obter_orcamento(int(self.orcamento_id))
        if not orcamento:
            return
        self.inp_mes.setText(str(orcamento.get("mes") or date.today().strftime("%Y-%m")))
        categoria = str(orcamento.get("categoria") or "Outros")
        if categoria in CATEGORIAS:
            self.cmb_categoria.setCurrentText(categoria)
        self.inp_limite.setText(f'{float(orcamento.get("limite") or 0):.2f}'.replace(".", ","))
        self.inp_observacoes.setText(str(orcamento.get("observacoes") or ""))

    def _delete(self):
        if not msg_yesno(self, "Confirmar", f"Deletar orçamento #{self.orcamento_id}?"):
            return
        excluir_orcamento_categoria(int(self.orcamento_id))
        self.done(2)

    def get_payload(self):
        mes = self.inp_mes.text().strip()
        datetime.strptime(mes + "-01", "%Y-%m-%d")

        categoria = self.cmb_categoria.currentText()
        limite = parse_money(self.inp_limite.text())
        if limite <= 0:
            raise ValueError("Limite precisa ser maior que zero.")

        observacoes = self.inp_observacoes.text().strip()
        return mes, categoria, limite, observacoes


class GoalDialog(FormDialog):
    def __init__(self, parent=None, meta_id=None):
        super().__init__("Meta financeira" if meta_id is None else f"Editar meta #{meta_id}", parent)
        self.meta_id = meta_id
        self.resize(620, 520)

        titulo = QLabel("Meta financeira")
        titulo.setObjectName("PanelTitle")
        descricao = QLabel("Use para acompanhar reserva, viagem, hardware, estudos ou qualquer objetivo financeiro.")
        descricao.setObjectName("Subtle")
        descricao.setWordWrap(True)

        self.inp_nome = QLineEdit()
        self.inp_nome.setPlaceholderText("Ex: Reserva de emergência")

        self.cmb_categoria = QComboBox()
        self.cmb_categoria.addItems(["Reserva", "Compra", "Viagem", "Estudos", "Investimentos", "Outros"])

        self.inp_valor_alvo = QLineEdit()
        self.inp_valor_alvo.setPlaceholderText("Ex: 5000,00")

        self.inp_valor_atual = QLineEdit()
        self.inp_valor_atual.setPlaceholderText("Ex: 750,00")
        self.inp_valor_atual.setText("0")

        self.inp_data_limite = QLineEdit()
        self.inp_data_limite.setPlaceholderText("DD/MM/AAAA (opcional)")

        self.inp_observacoes = QLineEdit()
        self.inp_observacoes.setPlaceholderText("Observação opcional")

        self.chk_concluida = QCheckBox("Marcar como concluída")

        self.lay.addWidget(titulo)
        self.lay.addWidget(descricao)
        self.lay.addWidget(QLabel("Nome"))
        self.lay.addWidget(self.inp_nome)
        self.lay.addWidget(QLabel("Categoria"))
        self.lay.addWidget(self.cmb_categoria)
        self.lay.addWidget(QLabel("Valor alvo (R$)"))
        self.lay.addWidget(self.inp_valor_alvo)
        self.lay.addWidget(QLabel("Valor atual guardado (R$)"))
        self.lay.addWidget(self.inp_valor_atual)
        self.lay.addWidget(QLabel("Data limite"))
        self.lay.addWidget(self.inp_data_limite)
        self.lay.addWidget(QLabel("Observações"))
        self.lay.addWidget(self.inp_observacoes)
        self.lay.addWidget(self.chk_concluida)

        if self.meta_id is not None:
            self._load()
            self.btn_delete = QPushButton("Deletar")
            self.btn_delete.setObjectName("BtnGhostDanger")
            self.btn_delete.clicked.connect(self._delete)
            self.actions.insertWidget(0, self.btn_delete)

    def _load(self):
        meta = obter_meta_financeira(int(self.meta_id))
        if not meta:
            return

        self.inp_nome.setText(str(meta.get("nome") or ""))
        categoria = str(meta.get("categoria") or "Outros")
        if categoria in [self.cmb_categoria.itemText(index) for index in range(self.cmb_categoria.count())]:
            self.cmb_categoria.setCurrentText(categoria)
        self.inp_valor_alvo.setText(f'{float(meta.get("valor_alvo") or 0):.2f}'.replace(".", ","))
        self.inp_valor_atual.setText(f'{float(meta.get("valor_atual") or 0):.2f}'.replace(".", ","))
        data_limite = str(meta.get("data_limite") or "")
        if data_limite:
            self.inp_data_limite.setText(br_date(data_limite))
        self.inp_observacoes.setText(str(meta.get("observacoes") or ""))
        self.chk_concluida.setChecked(bool(meta.get("concluida")))

    def _delete(self):
        if not msg_yesno(self, "Confirmar", f"Deletar meta #{self.meta_id}?"):
            return
        excluir_meta_financeira(int(self.meta_id))
        self.done(2)

    def get_payload(self):
        nome = self.inp_nome.text().strip()
        if not nome:
            raise ValueError("Nome obrigatório.")

        categoria = self.cmb_categoria.currentText()
        valor_alvo = parse_money(self.inp_valor_alvo.text())
        valor_atual = parse_money(self.inp_valor_atual.text() or "0")
        if valor_alvo <= 0:
            raise ValueError("Valor alvo precisa ser maior que zero.")
        if valor_atual < 0:
            raise ValueError("Valor atual não pode ser negativo.")

        data_limite_texto = self.inp_data_limite.text().strip()
        data_limite = iso_date(data_limite_texto) if data_limite_texto else ""
        observacoes = self.inp_observacoes.text().strip()
        concluida = self.chk_concluida.isChecked() or valor_atual >= valor_alvo
        return nome, categoria, valor_alvo, valor_atual, data_limite, observacoes, concluida

