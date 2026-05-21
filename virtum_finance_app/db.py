from __future__ import annotations

import json
import os
import sqlite3
import sys
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Iterator, Any

from .services.investimentos_calculadora import calcular_poupanca, calcular_renda_fixa_cdi


def get_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(sys.argv[0]).resolve().parent


def get_db_path() -> Path:
    override = os.environ.get("VIRTUM_FINANCE_DB")
    if override:
        return Path(override).expanduser().resolve()
    return get_app_dir() / "gastos.db"


DB_PATH = get_db_path()


def _money_text(valor: float) -> str:
    texto = f"R$ {float(valor):,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


@contextmanager
def conectar() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 15000")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _table_columns(cur: sqlite3.Cursor, table_name: str) -> set[str]:
    cur.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cur.fetchall()}


def _add_column_if_missing(cur: sqlite3.Cursor, table_name: str, column_name: str, column_sql: str) -> None:
    if column_name not in _table_columns(cur, table_name):
        cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}")


def _ensure_resumo_unique_index(cur: sqlite3.Cursor) -> None:
    cur.execute("DELETE FROM resumo WHERE mes IS NULL OR mes = ''")
    cur.execute(
        """
        DELETE FROM resumo
        WHERE id NOT IN (
            SELECT MAX(id)
            FROM resumo
            GROUP BY mes
        )
        """
    )
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_resumo_mes ON resumo(mes)")


def migrar_banco() -> None:
    with conectar() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                categoria TEXT NOT NULL DEFAULT 'Outros',
                valor REAL NOT NULL DEFAULT 0,
                descricao TEXT DEFAULT '',
                data TEXT NOT NULL
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY,
                salario REAL DEFAULT 0,
                ultimo_mes TEXT DEFAULT '',
                tema TEXT DEFAULT 'original'
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS fixos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                categoria TEXT NOT NULL DEFAULT 'Outros',
                valor REAL NOT NULL DEFAULT 0,
                descricao TEXT DEFAULT '',
                ativo INTEGER DEFAULT 1
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS fixos_aplicados (
                mes TEXT NOT NULL,
                fixo_id INTEGER NOT NULL,
                gasto_id INTEGER,
                PRIMARY KEY (mes, fixo_id)
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS resumo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mes TEXT NOT NULL,
                total REAL NOT NULL DEFAULT 0,
                saldo REAL NOT NULL DEFAULT 0,
                receita_extra REAL NOT NULL DEFAULT 0,
                receita_total REAL NOT NULL DEFAULT 0,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS receitas_extras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fonte TEXT NOT NULL DEFAULT 'Outros',
                valor REAL NOT NULL DEFAULT 0,
                descricao TEXT DEFAULT '',
                data TEXT NOT NULL DEFAULT '',
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS investimentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL DEFAULT '',
                tipo TEXT NOT NULL DEFAULT 'Outro',
                valor_aplicado REAL NOT NULL DEFAULT 0,
                data_aplicacao TEXT NOT NULL DEFAULT '',
                prazo_meses INTEGER NOT NULL DEFAULT 1,
                percentual_cdi REAL NOT NULL DEFAULT 100,
                taxa_cdi_anual REAL NOT NULL DEFAULT 0,
                taxa_selic_anual REAL NOT NULL DEFAULT 0,
                taxa_tr_mensal REAL NOT NULL DEFAULT 0,
                carencia_dias INTEGER NOT NULL DEFAULT 0,
                liquidez TEXT NOT NULL DEFAULT 'Diária',
                observacoes TEXT DEFAULT '',
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
                valor_atual REAL NOT NULL DEFAULT 0,
                abater_saldo INTEGER NOT NULL DEFAULT 1,
                gasto_id INTEGER,
                valor_investido REAL NOT NULL DEFAULT 0,
                data TEXT DEFAULT '',
                descricao TEXT DEFAULT ''
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS simulacoes_investimentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                valor_inicial REAL NOT NULL DEFAULT 0,
                prazo_meses INTEGER NOT NULL DEFAULT 0,
                taxa_cdi_anual REAL NOT NULL DEFAULT 0,
                taxa_selic_anual REAL NOT NULL DEFAULT 0,
                taxa_tr_mensal REAL NOT NULL DEFAULT 0,
                percentual_cdi_personalizado REAL NOT NULL DEFAULT 100,
                resultado_poupanca TEXT DEFAULT '',
                resultado_sicredinvest TEXT DEFAULT '',
                resultado_cdi_personalizado TEXT DEFAULT '',
                melhor_resultado TEXT DEFAULT '',
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        for table_name, columns in {
            "gastos": [
                ("categoria", "categoria TEXT NOT NULL DEFAULT 'Outros'"),
                ("valor", "valor REAL NOT NULL DEFAULT 0"),
                ("descricao", "descricao TEXT DEFAULT ''"),
                ("data", "data TEXT NOT NULL DEFAULT ''"),
            ],
            "config": [
                ("salario", "salario REAL DEFAULT 0"),
                ("ultimo_mes", "ultimo_mes TEXT DEFAULT ''"),
                ("tema", "tema TEXT DEFAULT 'original'"),
            ],
            "fixos": [
                ("categoria", "categoria TEXT NOT NULL DEFAULT 'Outros'"),
                ("valor", "valor REAL NOT NULL DEFAULT 0"),
                ("descricao", "descricao TEXT DEFAULT ''"),
                ("ativo", "ativo INTEGER DEFAULT 1"),
            ],
            "fixos_aplicados": [("gasto_id", "gasto_id INTEGER")],
            "resumo": [
                ("total", "total REAL NOT NULL DEFAULT 0"),
                ("saldo", "saldo REAL NOT NULL DEFAULT 0"),
                ("receita_extra", "receita_extra REAL NOT NULL DEFAULT 0"),
                ("receita_total", "receita_total REAL NOT NULL DEFAULT 0"),
                ("criado_em", "criado_em TEXT DEFAULT CURRENT_TIMESTAMP"),
                ("atualizado_em", "atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP"),
            ],
            "receitas_extras": [
                ("fonte", "fonte TEXT NOT NULL DEFAULT 'Outros'"),
                ("valor", "valor REAL NOT NULL DEFAULT 0"),
                ("descricao", "descricao TEXT DEFAULT ''"),
                ("data", "data TEXT NOT NULL DEFAULT ''"),
                ("criado_em", "criado_em TEXT DEFAULT CURRENT_TIMESTAMP"),
                ("atualizado_em", "atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP"),
            ],
            "investimentos": [
                ("nome", "nome TEXT NOT NULL DEFAULT ''"),
                ("tipo", "tipo TEXT NOT NULL DEFAULT 'Outro'"),
                ("valor_aplicado", "valor_aplicado REAL NOT NULL DEFAULT 0"),
                ("data_aplicacao", "data_aplicacao TEXT NOT NULL DEFAULT ''"),
                ("prazo_meses", "prazo_meses INTEGER NOT NULL DEFAULT 1"),
                ("percentual_cdi", "percentual_cdi REAL NOT NULL DEFAULT 100"),
                ("taxa_cdi_anual", "taxa_cdi_anual REAL NOT NULL DEFAULT 0"),
                ("taxa_selic_anual", "taxa_selic_anual REAL NOT NULL DEFAULT 0"),
                ("taxa_tr_mensal", "taxa_tr_mensal REAL NOT NULL DEFAULT 0"),
                ("carencia_dias", "carencia_dias INTEGER NOT NULL DEFAULT 0"),
                ("liquidez", "liquidez TEXT NOT NULL DEFAULT 'Diária'"),
                ("observacoes", "observacoes TEXT DEFAULT ''"),
                ("criado_em", "criado_em TEXT DEFAULT CURRENT_TIMESTAMP"),
                ("valor_atual", "valor_atual REAL NOT NULL DEFAULT 0"),
                ("abater_saldo", "abater_saldo INTEGER NOT NULL DEFAULT 1"),
                ("gasto_id", "gasto_id INTEGER"),
                ("valor_investido", "valor_investido REAL NOT NULL DEFAULT 0"),
                ("data", "data TEXT DEFAULT ''"),
                ("descricao", "descricao TEXT DEFAULT ''"),
            ],
            "simulacoes_investimentos": [
                ("valor_inicial", "valor_inicial REAL NOT NULL DEFAULT 0"),
                ("prazo_meses", "prazo_meses INTEGER NOT NULL DEFAULT 0"),
                ("taxa_cdi_anual", "taxa_cdi_anual REAL NOT NULL DEFAULT 0"),
                ("taxa_selic_anual", "taxa_selic_anual REAL NOT NULL DEFAULT 0"),
                ("taxa_tr_mensal", "taxa_tr_mensal REAL NOT NULL DEFAULT 0"),
                ("percentual_cdi_personalizado", "percentual_cdi_personalizado REAL NOT NULL DEFAULT 100"),
                ("resultado_poupanca", "resultado_poupanca TEXT DEFAULT ''"),
                ("resultado_sicredinvest", "resultado_sicredinvest TEXT DEFAULT ''"),
                ("resultado_cdi_personalizado", "resultado_cdi_personalizado TEXT DEFAULT ''"),
                ("melhor_resultado", "melhor_resultado TEXT DEFAULT ''"),
                ("criado_em", "criado_em TEXT DEFAULT CURRENT_TIMESTAMP"),
            ],
        }.items():
            for column_name, column_sql in columns:
                _add_column_if_missing(cur, table_name, column_name, column_sql)

        cur.execute("INSERT OR IGNORE INTO config (id, salario, ultimo_mes, tema) VALUES (1, 0, '', 'original')")
        cur.execute("UPDATE config SET tema='original' WHERE id=1 AND (tema IS NULL OR tema='')")
        cur.execute("UPDATE config SET salario=0 WHERE id=1 AND salario IS NULL")
        cur.execute(
            """
            UPDATE resumo
            SET receita_total = COALESCE(total, 0) + COALESCE(saldo, 0)
            WHERE COALESCE(receita_total, 0) = 0
              AND COALESCE(total, 0) + COALESCE(saldo, 0) > 0
            """
        )

        cur.execute(
            """
            UPDATE investimentos
            SET valor_aplicado = CASE WHEN valor_aplicado IS NULL OR valor_aplicado = 0 THEN COALESCE(valor_investido, 0) ELSE valor_aplicado END,
                valor_investido = CASE WHEN valor_investido IS NULL OR valor_investido = 0 THEN COALESCE(valor_aplicado, 0) ELSE valor_investido END,
                data_aplicacao = CASE WHEN data_aplicacao IS NULL OR data_aplicacao = '' THEN COALESCE(data, '') ELSE data_aplicacao END,
                data = CASE WHEN data IS NULL OR data = '' THEN COALESCE(data_aplicacao, '') ELSE data END,
                observacoes = CASE WHEN observacoes IS NULL OR observacoes = '' THEN COALESCE(descricao, '') ELSE observacoes END,
                descricao = CASE WHEN descricao IS NULL OR descricao = '' THEN COALESCE(observacoes, '') ELSE descricao END,
                tipo = CASE WHEN tipo IS NULL OR tipo = '' THEN 'Outro' ELSE tipo END,
                liquidez = CASE WHEN liquidez IS NULL OR liquidez = '' THEN 'Diária' ELSE liquidez END
            """
        )


        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS orcamentos_categoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mes TEXT NOT NULL,
                categoria TEXT NOT NULL DEFAULT 'Outros',
                limite REAL NOT NULL DEFAULT 0,
                observacoes TEXT DEFAULT '',
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (mes, categoria)
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS metas_financeiras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL DEFAULT '',
                categoria TEXT NOT NULL DEFAULT 'Outro',
                valor_alvo REAL NOT NULL DEFAULT 0,
                valor_atual REAL NOT NULL DEFAULT 0,
                data_limite TEXT DEFAULT '',
                observacoes TEXT DEFAULT '',
                concluida INTEGER NOT NULL DEFAULT 0,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        for table_name, columns in {
            "orcamentos_categoria": [
                ("mes", "mes TEXT NOT NULL DEFAULT ''"),
                ("categoria", "categoria TEXT NOT NULL DEFAULT 'Outros'"),
                ("limite", "limite REAL NOT NULL DEFAULT 0"),
                ("observacoes", "observacoes TEXT DEFAULT ''"),
                ("criado_em", "criado_em TEXT DEFAULT CURRENT_TIMESTAMP"),
                ("atualizado_em", "atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP"),
            ],
            "metas_financeiras": [
                ("nome", "nome TEXT NOT NULL DEFAULT ''"),
                ("categoria", "categoria TEXT NOT NULL DEFAULT 'Outro'"),
                ("valor_alvo", "valor_alvo REAL NOT NULL DEFAULT 0"),
                ("valor_atual", "valor_atual REAL NOT NULL DEFAULT 0"),
                ("data_limite", "data_limite TEXT DEFAULT ''"),
                ("observacoes", "observacoes TEXT DEFAULT ''"),
                ("concluida", "concluida INTEGER NOT NULL DEFAULT 0"),
                ("criado_em", "criado_em TEXT DEFAULT CURRENT_TIMESTAMP"),
                ("atualizado_em", "atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP"),
            ],
        }.items():
            for column_name, column_sql in columns:
                _add_column_if_missing(cur, table_name, column_name, column_sql)



        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS gamificacao_perfil (
                id INTEGER PRIMARY KEY,
                xp_total INTEGER NOT NULL DEFAULT 0,
                nivel INTEGER NOT NULL DEFAULT 1,
                titulo TEXT NOT NULL DEFAULT 'Aprendiz Virtum',
                xp_nivel_atual INTEGER NOT NULL DEFAULT 0,
                xp_proximo_nivel INTEGER NOT NULL DEFAULT 250,
                rank_codigo TEXT NOT NULL DEFAULT 'aprendiz_financeiro',
                rank_nome TEXT NOT NULL DEFAULT 'Aprendiz Financeiro',
                rank_emoji TEXT NOT NULL DEFAULT '🌱',
                rank_descricao TEXT DEFAULT '',
                atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        for column_name, column_sql in [
            ("rank_codigo", "rank_codigo TEXT NOT NULL DEFAULT 'aprendiz_financeiro'"),
            ("rank_nome", "rank_nome TEXT NOT NULL DEFAULT 'Aprendiz Financeiro'"),
            ("rank_emoji", "rank_emoji TEXT NOT NULL DEFAULT '🌱'"),
            ("rank_descricao", "rank_descricao TEXT DEFAULT ''"),
        ]:
            _add_column_if_missing(cur, "gamificacao_perfil", column_name, column_sql)

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS gamificacao_eventos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chave TEXT NOT NULL UNIQUE,
                tipo TEXT NOT NULL DEFAULT '',
                referencia TEXT DEFAULT '',
                xp INTEGER NOT NULL DEFAULT 0,
                descricao TEXT DEFAULT '',
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS gamificacao_conquistas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chave TEXT NOT NULL UNIQUE,
                nome TEXT NOT NULL DEFAULT '',
                descricao TEXT DEFAULT '',
                xp_bonus INTEGER NOT NULL DEFAULT 0,
                desbloqueada INTEGER NOT NULL DEFAULT 0,
                desbloqueada_em TEXT DEFAULT ''
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS medalhas_mensais (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mes TEXT NOT NULL UNIQUE,
                codigo TEXT NOT NULL DEFAULT 'bronze',
                nome TEXT NOT NULL DEFAULT 'Medalha Bronze',
                emoji TEXT NOT NULL DEFAULT '🥉',
                xp_bonus INTEGER NOT NULL DEFAULT 40,
                criterios TEXT DEFAULT '',
                saldo REAL NOT NULL DEFAULT 0,
                total_gastos REAL NOT NULL DEFAULT 0,
                receita_total REAL NOT NULL DEFAULT 0,
                orcamentos_dentro INTEGER NOT NULL DEFAULT 0,
                investiu_no_mes INTEGER NOT NULL DEFAULT 0,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        for column_name, column_sql in [
            ("mes", "mes TEXT NOT NULL DEFAULT ''"),
            ("codigo", "codigo TEXT NOT NULL DEFAULT 'bronze'"),
            ("nome", "nome TEXT NOT NULL DEFAULT 'Medalha Bronze'"),
            ("emoji", "emoji TEXT NOT NULL DEFAULT '🥉'"),
            ("xp_bonus", "xp_bonus INTEGER NOT NULL DEFAULT 40"),
            ("criterios", "criterios TEXT DEFAULT ''"),
            ("saldo", "saldo REAL NOT NULL DEFAULT 0"),
            ("total_gastos", "total_gastos REAL NOT NULL DEFAULT 0"),
            ("receita_total", "receita_total REAL NOT NULL DEFAULT 0"),
            ("orcamentos_dentro", "orcamentos_dentro INTEGER NOT NULL DEFAULT 0"),
            ("investiu_no_mes", "investiu_no_mes INTEGER NOT NULL DEFAULT 0"),
            ("criado_em", "criado_em TEXT DEFAULT CURRENT_TIMESTAMP"),
            ("atualizado_em", "atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP"),
        ]:
            _add_column_if_missing(cur, "medalhas_mensais", column_name, column_sql)

        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_orcamentos_mes_categoria ON orcamentos_categoria(mes, categoria)")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_medalhas_mensais_mes ON medalhas_mensais(mes)")

        _ensure_resumo_unique_index(cur)


def obter_salario() -> float:
    migrar_banco()
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute("SELECT salario FROM config WHERE id=1")
        row = cur.fetchone()
    return float(row[0] or 0) if row else 0.0


def salvar_salario(valor: float) -> None:
    migrar_banco()
    with conectar() as conn:
        conn.execute("UPDATE config SET salario=? WHERE id=1", (float(valor),))


def obter_tema() -> str:
    migrar_banco()
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute("SELECT tema FROM config WHERE id=1")
        row = cur.fetchone()
    return row[0] if row and row[0] else "original"


def salvar_tema(nome: str) -> None:
    migrar_banco()
    with conectar() as conn:
        conn.execute("UPDATE config SET tema=? WHERE id=1", (nome,))


def aplicar_fixos_automaticos(mes: str | None = None) -> int:
    migrar_banco()
    mes_atual = mes or date.today().strftime("%Y-%m")
    aplicados = 0

    with conectar() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, categoria, valor, descricao FROM fixos WHERE ativo=1 ORDER BY id ASC")
        fixos = cur.fetchall()

        for fixo_id, categoria, valor, descricao in fixos:
            cur.execute(
                "SELECT 1 FROM fixos_aplicados WHERE mes=? AND fixo_id=? LIMIT 1",
                (mes_atual, fixo_id),
            )
            if cur.fetchone():
                continue

            valor_float = float(valor or 0)
            cur.execute(
                "INSERT INTO gastos (categoria, valor, descricao, data) VALUES (?, ?, ?, ?)",
                (categoria or "Outros", valor_float, descricao or "", f"{mes_atual}-01"),
            )
            gasto_id = cur.lastrowid
            cur.execute(
                "INSERT OR IGNORE INTO fixos_aplicados (mes, fixo_id, gasto_id) VALUES (?, ?, ?)",
                (mes_atual, fixo_id, gasto_id),
            )
            aplicados += 1

        cur.execute("UPDATE config SET ultimo_mes=? WHERE id=1", (mes_atual,))

    return aplicados


def listar_gastos_do_mes(mes: str) -> list[tuple[int, str, float, str]]:
    migrar_banco()
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, categoria, valor, data FROM gastos WHERE data LIKE ? ORDER BY data DESC, id DESC",
            (f"{mes}%",),
        )
        rows = cur.fetchall()
    return [(int(r[0]), str(r[1]), float(r[2] or 0), str(r[3])) for r in rows]


def total_gastos_do_mes(mes: str) -> float:
    migrar_banco()
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(SUM(valor), 0) FROM gastos WHERE data LIKE ?", (f"{mes}%",))
        row = cur.fetchone()
    return float(row[0] or 0)


def _dados_medalha(codigo: str) -> dict[str, Any]:
    mapa = {
        "bronze": {
            "nome": "Medalha Bronze",
            "emoji": "🥉",
            "xp_bonus": 40,
            "criterios": "Fechamento mensal salvo.",
        },
        "prata": {
            "nome": "Medalha Prata",
            "emoji": "🥈",
            "xp_bonus": 80,
            "criterios": "Fechamento salvo com saldo positivo.",
        },
        "ouro": {
            "nome": "Medalha Ouro",
            "emoji": "🥇",
            "xp_bonus": 120,
            "criterios": "Saldo positivo e todos os orçamentos do mês dentro do limite.",
        },
        "diamante": {
            "nome": "Medalha Diamante",
            "emoji": "💎",
            "xp_bonus": 180,
            "criterios": "Saldo positivo, orçamentos dentro do limite e investimento registrado no mês.",
        },
    }
    return mapa.get(codigo, mapa["bronze"])


def _orcamentos_do_mes_estao_dentro(cur: sqlite3.Cursor, mes: str) -> bool:
    cur.execute("SELECT categoria, limite FROM orcamentos_categoria WHERE mes=?", (mes,))
    orcamentos = cur.fetchall()
    if not orcamentos:
        return False

    for categoria, limite in orcamentos:
        cur.execute(
            "SELECT COALESCE(SUM(valor), 0) FROM gastos WHERE data LIKE ? AND categoria=?",
            (f"{mes}%", categoria),
        )
        usado = float(cur.fetchone()[0] or 0)
        if usado > float(limite or 0):
            return False
    return True


def _investiu_no_mes(cur: sqlite3.Cursor, mes: str) -> bool:
    cur.execute(
        """
        SELECT COUNT(*)
        FROM investimentos
        WHERE data_aplicacao LIKE ? OR data LIKE ?
        """,
        (f"{mes}%", f"{mes}%"),
    )
    return int(cur.fetchone()[0] or 0) > 0


def _registrar_medalha_mensal(
    cur: sqlite3.Cursor,
    mes: str,
    total_gastos: float,
    saldo: float,
    receita_total: float,
) -> dict[str, Any]:
    orcamentos_dentro = _orcamentos_do_mes_estao_dentro(cur, mes)
    investiu_mes = _investiu_no_mes(cur, mes)

    if float(saldo or 0) >= 0 and orcamentos_dentro and investiu_mes:
        codigo = "diamante"
    elif float(saldo or 0) >= 0 and orcamentos_dentro:
        codigo = "ouro"
    elif float(saldo or 0) >= 0:
        codigo = "prata"
    else:
        codigo = "bronze"

    dados = _dados_medalha(codigo)
    cur.execute(
        """
        INSERT INTO medalhas_mensais
            (mes, codigo, nome, emoji, xp_bonus, criterios, saldo, total_gastos, receita_total,
             orcamentos_dentro, investiu_no_mes, atualizado_em)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(mes)
        DO UPDATE SET
            codigo=excluded.codigo,
            nome=excluded.nome,
            emoji=excluded.emoji,
            xp_bonus=excluded.xp_bonus,
            criterios=excluded.criterios,
            saldo=excluded.saldo,
            total_gastos=excluded.total_gastos,
            receita_total=excluded.receita_total,
            orcamentos_dentro=excluded.orcamentos_dentro,
            investiu_no_mes=excluded.investiu_no_mes,
            atualizado_em=CURRENT_TIMESTAMP
        """,
        (
            mes,
            codigo,
            dados["nome"],
            dados["emoji"],
            int(dados["xp_bonus"]),
            dados["criterios"],
            float(saldo or 0),
            float(total_gastos or 0),
            float(receita_total or 0),
            1 if orcamentos_dentro else 0,
            1 if investiu_mes else 0,
        ),
    )

    return {
        "mes": mes,
        "codigo": codigo,
        "nome": dados["nome"],
        "emoji": dados["emoji"],
        "xp_bonus": int(dados["xp_bonus"]),
        "criterios": dados["criterios"],
        "saldo": float(saldo or 0),
        "total_gastos": float(total_gastos or 0),
        "receita_total": float(receita_total or 0),
        "orcamentos_dentro": orcamentos_dentro,
        "investiu_no_mes": investiu_mes,
    }


def salvar_fechamento(
    mes: str,
    total: float,
    saldo: float,
    receita_extra: float = 0.0,
    receita_total: float | None = None,
) -> dict[str, Any]:
    migrar_banco()
    receita_extra_float = float(receita_extra or 0)
    receita_total_float = float(receita_total if receita_total is not None else obter_salario() + receita_extra_float)
    medalha = None

    with conectar() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO resumo (mes, total, saldo, receita_extra, receita_total, atualizado_em)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(mes)
                DO UPDATE SET
                    total=excluded.total,
                    saldo=excluded.saldo,
                    receita_extra=excluded.receita_extra,
                    receita_total=excluded.receita_total,
                    atualizado_em=CURRENT_TIMESTAMP
                """,
                (mes, float(total), float(saldo), receita_extra_float, receita_total_float),
            )
        except sqlite3.OperationalError:
            cur.execute("DELETE FROM resumo WHERE mes=?", (mes,))
            cur.execute(
                """
                INSERT INTO resumo (mes, total, saldo, receita_extra, receita_total)
                VALUES (?, ?, ?, ?, ?)
                """,
                (mes, float(total), float(saldo), receita_extra_float, receita_total_float),
            )

        medalha = _registrar_medalha_mensal(cur, mes, float(total), float(saldo), receita_total_float)

    return medalha or {}


def _descricao_gasto_investimento(nome: str, tipo: str, observacoes: str) -> str:
    partes = [f"Investimento: {nome}".strip()]
    if tipo:
        partes.append(f"Tipo: {tipo}")
    if observacoes:
        partes.append(observacoes.strip())
    return " | ".join(partes)


def _criar_gasto_para_investimento(
    cur: sqlite3.Cursor,
    nome: str,
    tipo: str,
    valor_aplicado: float,
    data_aplicacao: str,
    observacoes: str,
) -> int:
    cur.execute(
        "INSERT INTO gastos (categoria, valor, descricao, data) VALUES (?, ?, ?, ?)",
        (
            "Investimentos",
            float(valor_aplicado),
            _descricao_gasto_investimento(nome, tipo, observacoes),
            data_aplicacao,
        ),
    )
    return int(cur.lastrowid)


def _atualizar_gasto_de_investimento(
    cur: sqlite3.Cursor,
    gasto_id: int,
    nome: str,
    tipo: str,
    valor_aplicado: float,
    data_aplicacao: str,
    observacoes: str,
) -> bool:
    cur.execute(
        """
        UPDATE gastos
        SET categoria=?, valor=?, descricao=?, data=?
        WHERE id=?
        """,
        (
            "Investimentos",
            float(valor_aplicado),
            _descricao_gasto_investimento(nome, tipo, observacoes),
            data_aplicacao,
            int(gasto_id),
        ),
    )
    return cur.rowcount > 0


def _estimar_valor_atual(
    tipo: str,
    valor_aplicado: float,
    prazo_meses: int,
    percentual_cdi: float,
    taxa_cdi_anual: float,
    taxa_selic_anual: float,
    taxa_tr_mensal: float,
) -> float:
    try:
        if tipo == "Poupança":
            return calcular_poupanca(valor_aplicado, prazo_meses, taxa_selic_anual, taxa_tr_mensal).valor_final_liquido
        if tipo == "Sicredinvest CDI100":
            return calcular_renda_fixa_cdi(valor_aplicado, prazo_meses, taxa_cdi_anual, 100, prazo_meses * 30, "Sicredinvest CDI100").valor_final_liquido
        if tipo == "CDI Personalizado":
            return calcular_renda_fixa_cdi(valor_aplicado, prazo_meses, taxa_cdi_anual, percentual_cdi, prazo_meses * 30, "CDI Personalizado").valor_final_liquido
    except Exception:
        pass
    return float(valor_aplicado or 0)


def listar_investimentos() -> list[dict[str, Any]]:
    migrar_banco()
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                id, nome, tipo, valor_aplicado, data_aplicacao, prazo_meses,
                percentual_cdi, taxa_cdi_anual, taxa_selic_anual, taxa_tr_mensal,
                carencia_dias, liquidez, observacoes, criado_em, valor_atual,
                abater_saldo, gasto_id
            FROM investimentos
            ORDER BY data_aplicacao DESC, id DESC
            """
        )
        rows = cur.fetchall()

    keys = [
        "id", "nome", "tipo", "valor_aplicado", "data_aplicacao", "prazo_meses",
        "percentual_cdi", "taxa_cdi_anual", "taxa_selic_anual", "taxa_tr_mensal",
        "carencia_dias", "liquidez", "observacoes", "criado_em", "valor_atual",
        "abater_saldo", "gasto_id",
    ]
    investimentos = []
    for row in rows:
        item = dict(zip(keys, row))
        item["id"] = int(item["id"])
        item["valor_aplicado"] = float(item["valor_aplicado"] or 0)
        item["valor_atual"] = float(item["valor_atual"] or 0)
        item["prazo_meses"] = int(item["prazo_meses"] or 0)
        item["percentual_cdi"] = float(item["percentual_cdi"] or 0)
        item["taxa_cdi_anual"] = float(item["taxa_cdi_anual"] or 0)
        item["taxa_selic_anual"] = float(item["taxa_selic_anual"] or 0)
        item["taxa_tr_mensal"] = float(item["taxa_tr_mensal"] or 0)
        item["carencia_dias"] = int(item["carencia_dias"] or 0)
        item["abater_saldo"] = int(item["abater_saldo"] or 0)
        item["gasto_id"] = int(item["gasto_id"]) if item["gasto_id"] is not None else None
        investimentos.append(item)
    return investimentos


def obter_investimento(investimento_id: int) -> dict[str, Any] | None:
    for investimento in listar_investimentos():
        if int(investimento["id"]) == int(investimento_id):
            return investimento
    return None


def criar_investimento(
    nome: str,
    tipo: str,
    valor_aplicado: float,
    data_aplicacao: str,
    prazo_meses: int,
    percentual_cdi: float,
    taxa_cdi_anual: float,
    taxa_selic_anual: float,
    taxa_tr_mensal: float,
    carencia_dias: int,
    liquidez: str,
    observacoes: str,
    abater_saldo: bool = True,
) -> None:
    migrar_banco()
    valor_atual = _estimar_valor_atual(tipo, valor_aplicado, prazo_meses, percentual_cdi, taxa_cdi_anual, taxa_selic_anual, taxa_tr_mensal)

    with conectar() as conn:
        cur = conn.cursor()
        gasto_id = None
        if abater_saldo:
            gasto_id = _criar_gasto_para_investimento(cur, nome, tipo, valor_aplicado, data_aplicacao, observacoes)

        cur.execute(
            """
            INSERT INTO investimentos
                (
                    nome, tipo, valor_aplicado, data_aplicacao, prazo_meses,
                    percentual_cdi, taxa_cdi_anual, taxa_selic_anual, taxa_tr_mensal,
                    carencia_dias, liquidez, observacoes, valor_atual, abater_saldo,
                    gasto_id, valor_investido, data, descricao
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nome,
                tipo,
                float(valor_aplicado),
                data_aplicacao,
                int(prazo_meses),
                float(percentual_cdi),
                float(taxa_cdi_anual),
                float(taxa_selic_anual),
                float(taxa_tr_mensal),
                int(carencia_dias),
                liquidez,
                observacoes,
                float(valor_atual),
                1 if abater_saldo else 0,
                gasto_id,
                float(valor_aplicado),
                data_aplicacao,
                observacoes,
            ),
        )


def atualizar_investimento(
    investimento_id: int,
    nome: str,
    tipo: str,
    valor_aplicado: float,
    data_aplicacao: str,
    prazo_meses: int,
    percentual_cdi: float,
    taxa_cdi_anual: float,
    taxa_selic_anual: float,
    taxa_tr_mensal: float,
    carencia_dias: int,
    liquidez: str,
    observacoes: str,
    abater_saldo: bool = True,
) -> None:
    migrar_banco()
    valor_atual = _estimar_valor_atual(tipo, valor_aplicado, prazo_meses, percentual_cdi, taxa_cdi_anual, taxa_selic_anual, taxa_tr_mensal)

    with conectar() as conn:
        cur = conn.cursor()
        cur.execute("SELECT gasto_id FROM investimentos WHERE id=?", (int(investimento_id),))
        row = cur.fetchone()
        gasto_id = int(row[0]) if row and row[0] is not None else None

        if abater_saldo:
            if gasto_id is None:
                gasto_id = _criar_gasto_para_investimento(cur, nome, tipo, valor_aplicado, data_aplicacao, observacoes)
            else:
                atualizado = _atualizar_gasto_de_investimento(cur, gasto_id, nome, tipo, valor_aplicado, data_aplicacao, observacoes)
                if not atualizado:
                    gasto_id = _criar_gasto_para_investimento(cur, nome, tipo, valor_aplicado, data_aplicacao, observacoes)
        else:
            if gasto_id is not None:
                cur.execute("DELETE FROM gastos WHERE id=?", (gasto_id,))
            gasto_id = None

        cur.execute(
            """
            UPDATE investimentos
            SET
                nome=?, tipo=?, valor_aplicado=?, data_aplicacao=?, prazo_meses=?,
                percentual_cdi=?, taxa_cdi_anual=?, taxa_selic_anual=?, taxa_tr_mensal=?,
                carencia_dias=?, liquidez=?, observacoes=?, valor_atual=?, abater_saldo=?,
                gasto_id=?, valor_investido=?, data=?, descricao=?
            WHERE id=?
            """,
            (
                nome,
                tipo,
                float(valor_aplicado),
                data_aplicacao,
                int(prazo_meses),
                float(percentual_cdi),
                float(taxa_cdi_anual),
                float(taxa_selic_anual),
                float(taxa_tr_mensal),
                int(carencia_dias),
                liquidez,
                observacoes,
                float(valor_atual),
                1 if abater_saldo else 0,
                gasto_id,
                float(valor_aplicado),
                data_aplicacao,
                observacoes,
                int(investimento_id),
            ),
        )


def excluir_investimento(investimento_id: int) -> None:
    migrar_banco()
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute("SELECT gasto_id FROM investimentos WHERE id=?", (int(investimento_id),))
        row = cur.fetchone()
        if row and row[0] is not None:
            cur.execute("DELETE FROM gastos WHERE id=?", (int(row[0]),))
        cur.execute("DELETE FROM investimentos WHERE id=?", (int(investimento_id),))


def resumo_investimentos() -> dict[str, Any]:
    investimentos = listar_investimentos()
    total_aplicado = sum(float(item["valor_aplicado"] or 0) for item in investimentos)
    total_atual = sum(float(item["valor_atual"] or 0) for item in investimentos)
    rendimento_estimado = total_atual - total_aplicado
    rentabilidade = (rendimento_estimado / total_aplicado * 100.0) if total_aplicado > 0 else 0.0

    por_tipo: dict[str, float] = {}
    melhor_nome = "—"
    melhor_resultado = None
    for item in investimentos:
        tipo = str(item["tipo"] or "Outro")
        por_tipo[tipo] = por_tipo.get(tipo, 0.0) + float(item["valor_aplicado"] or 0)
        resultado = float(item["valor_atual"] or 0) - float(item["valor_aplicado"] or 0)
        if melhor_resultado is None or resultado > melhor_resultado:
            melhor_resultado = resultado
            melhor_nome = str(item["nome"] or "—")

    return {
        "total_aplicado": total_aplicado,
        "total_atual": total_atual,
        "rendimento_estimado": rendimento_estimado,
        "rentabilidade_percentual": rentabilidade,
        "quantidade": len(investimentos),
        "melhor_investimento_estimado": melhor_nome,
        "distribuicao_por_tipo": por_tipo,
    }


def salvar_simulacao_investimentos(
    valor_inicial: float,
    prazo_meses: int,
    taxa_cdi_anual: float,
    taxa_selic_anual: float,
    taxa_tr_mensal: float,
    percentual_cdi_personalizado: float,
    comparativo: dict[str, Any],
) -> None:
    migrar_banco()
    resultados = {resultado["nome"]: resultado for resultado in comparativo.get("resultados", [])}

    with conectar() as conn:
        conn.execute(
            """
            INSERT INTO simulacoes_investimentos
                (
                    valor_inicial, prazo_meses, taxa_cdi_anual, taxa_selic_anual,
                    taxa_tr_mensal, percentual_cdi_personalizado, resultado_poupanca,
                    resultado_sicredinvest, resultado_cdi_personalizado, melhor_resultado
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                float(valor_inicial),
                int(prazo_meses),
                float(taxa_cdi_anual),
                float(taxa_selic_anual),
                float(taxa_tr_mensal),
                float(percentual_cdi_personalizado),
                json.dumps(resultados.get("Poupança", {}), ensure_ascii=False),
                json.dumps(resultados.get("Sicredinvest CDI100", {}), ensure_ascii=False),
                json.dumps(next((r for r in comparativo.get("resultados", []) if str(r.get("nome", "")).startswith("CDI Personalizado")), {}), ensure_ascii=False),
                str(comparativo.get("melhor_resultado", "")),
            ),
        )


def total_investido_abate_saldo_do_mes(mes: str) -> float:
    migrar_banco()
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COALESCE(SUM(valor_aplicado), 0)
            FROM investimentos
            WHERE abater_saldo=1 AND data_aplicacao LIKE ?
            """,
            (f"{mes}%",),
        )
        row = cur.fetchone()
    return float(row[0] or 0) if row else 0.0


def criar_receita_extra(fonte: str, valor: float, descricao: str, data_iso: str) -> None:
    migrar_banco()
    with conectar() as conn:
        conn.execute(
            """
            INSERT INTO receitas_extras (fonte, valor, descricao, data, atualizado_em)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (fonte or "Outros", float(valor), descricao or "", data_iso),
        )


def atualizar_receita_extra(receita_id: int, fonte: str, valor: float, descricao: str, data_iso: str) -> None:
    migrar_banco()
    with conectar() as conn:
        conn.execute(
            """
            UPDATE receitas_extras
            SET fonte=?, valor=?, descricao=?, data=?, atualizado_em=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (fonte or "Outros", float(valor), descricao or "", data_iso, int(receita_id)),
        )


def excluir_receita_extra(receita_id: int) -> None:
    migrar_banco()
    with conectar() as conn:
        conn.execute("DELETE FROM receitas_extras WHERE id=?", (int(receita_id),))


def obter_receita_extra(receita_id: int) -> dict[str, Any] | None:
    migrar_banco()
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, fonte, valor, descricao, data
            FROM receitas_extras
            WHERE id=?
            """,
            (int(receita_id),),
        )
        row = cur.fetchone()

    if not row:
        return None
    return {
        "id": int(row[0]),
        "fonte": str(row[1] or "Outros"),
        "valor": float(row[2] or 0),
        "descricao": str(row[3] or ""),
        "data": str(row[4] or ""),
    }


def listar_receitas_do_mes(mes: str) -> list[dict[str, Any]]:
    migrar_banco()
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, fonte, valor, descricao, data
            FROM receitas_extras
            WHERE data LIKE ?
            ORDER BY data DESC, id DESC
            """,
            (f"{mes}%",),
        )
        rows = cur.fetchall()

    return [
        {
            "id": int(row[0]),
            "fonte": str(row[1] or "Outros"),
            "valor": float(row[2] or 0),
            "descricao": str(row[3] or ""),
            "data": str(row[4] or ""),
        }
        for row in rows
    ]


def total_receitas_extras_do_mes(mes: str) -> float:
    migrar_banco()
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(SUM(valor), 0) FROM receitas_extras WHERE data LIKE ?", (f"{mes}%",))
        row = cur.fetchone()
    return float(row[0] or 0) if row else 0.0


def resumo_receitas_do_mes(mes: str) -> dict[str, Any]:
    receitas = listar_receitas_do_mes(mes)
    total_extra = sum(float(item.get("valor", 0) or 0) for item in receitas)
    maior = max(receitas, key=lambda item: float(item.get("valor", 0) or 0), default=None)

    por_fonte: dict[str, float] = {}
    for receita in receitas:
        fonte = str(receita.get("fonte") or "Outros")
        por_fonte[fonte] = por_fonte.get(fonte, 0.0) + float(receita.get("valor", 0) or 0)

    salario = obter_salario()
    return {
        "mes": mes,
        "salario": salario,
        "total_extra": total_extra,
        "receita_total": salario + total_extra,
        "quantidade": len(receitas),
        "maior_entrada": maior,
        "por_fonte": por_fonte,
        "linhas": receitas,
    }


def gastos_por_categoria_do_mes(mes: str) -> dict[str, float]:
    migrar_banco()
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT categoria, COALESCE(SUM(valor), 0)
            FROM gastos
            WHERE data LIKE ?
            GROUP BY categoria
            ORDER BY COALESCE(SUM(valor), 0) DESC
            """,
            (f"{mes}%",),
        )
        rows = cur.fetchall()
    return {str(row[0] or "Outros"): float(row[1] or 0) for row in rows}


def gerar_relatorio_mensal(mes: str) -> dict[str, Any]:
    migrar_banco()
    salario = obter_salario()
    receitas_extra = total_receitas_extras_do_mes(mes)
    receita_total = salario + receitas_extra
    saidas = total_gastos_do_mes(mes)
    saldo = receita_total - saidas
    percentual_gasto = (saidas / receita_total * 100.0) if receita_total > 0 else 0.0

    categorias = gastos_por_categoria_do_mes(mes)
    maior_categoria, maior_valor = ("—", 0.0)
    if categorias:
        maior_categoria, maior_valor = next(iter(categorias.items()))

    resumo_orcamento = resumo_orcamentos_do_mes(mes)
    resumo_metas = resumo_metas_financeiras()
    resumo_investido = resumo_investimentos()
    investido_mes = total_investido_abate_saldo_do_mes(mes)

    mes_anterior = None
    comparacao_total = None
    comparacao_saldo = None
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT mes, total, saldo
            FROM resumo
            WHERE mes < ?
            ORDER BY mes DESC
            LIMIT 1
            """,
            (mes,),
        )
        row = cur.fetchone()
        if row:
            mes_anterior = str(row[0])
            comparacao_total = saidas - float(row[1] or 0)
            comparacao_saldo = saldo - float(row[2] or 0)

    if saldo >= 0 and percentual_gasto <= 70:
        status = "Excelente controle"
    elif saldo >= 0:
        status = "Saldo positivo"
    else:
        status = "Atenção ao saldo"

    percentual_texto = f"{percentual_gasto:.1f}".replace(".", ",")

    analises = []
    analises.append(f"Receita total do mês: {_money_text(receita_total)} ({_money_text(salario)} de salário + {_money_text(receitas_extra)} em entradas extras).")
    analises.append(f"Saídas do mês: {_money_text(saidas)}. Isso representa {percentual_texto}% da receita total.")
    analises.append(f"Saldo projetado do mês: {_money_text(saldo)}.")

    if maior_categoria != "—":
        analises.append(f"Maior categoria de saída: {maior_categoria}, com {_money_text(maior_valor)}.")
    else:
        analises.append("Ainda não existem saídas lançadas neste mês.")

    saldo_orcamento = float(resumo_orcamento.get("saldo_orcamento", 0) or 0)
    total_orcado = float(resumo_orcamento.get("total_orcado", 0) or 0)
    if total_orcado > 0:
        if saldo_orcamento >= 0:
            analises.append(f"Orçamentos: ainda existem {_money_text(saldo_orcamento)} livres nas categorias configuradas.")
        else:
            analises.append(f"Orçamentos: categorias configuradas ultrapassaram {_money_text(abs(saldo_orcamento))}.")
    else:
        analises.append("Nenhum orçamento foi definido para este mês ainda.")

    if investido_mes > 0:
        analises.append(f"Investimentos do mês: {_money_text(investido_mes)} abatidos do saldo e considerados no fechamento.")
    else:
        analises.append("Nenhum investimento abatido do saldo foi lançado neste mês.")

    quantidade_metas = int(resumo_metas.get("quantidade", 0) or 0)
    if quantidade_metas > 0:
        percentual_metas = f"{float(resumo_metas.get('percentual', 0) or 0):.1f}".replace(".", ",")
        analises.append(
            f"Metas: {resumo_metas.get('concluidas', 0)}/{quantidade_metas} concluídas, com progresso geral de {percentual_metas}%."
        )
    else:
        analises.append("Nenhuma meta financeira cadastrada ainda.")

    if mes_anterior is not None and comparacao_total is not None and comparacao_saldo is not None:
        direcao_gasto = "aumentaram" if comparacao_total > 0 else "diminuíram"
        direcao_saldo = "melhorou" if comparacao_saldo > 0 else "piorou"
        analises.append(f"Comparado ao fechamento de {mes_anterior}, as saídas {direcao_gasto} {_money_text(abs(comparacao_total))} e o saldo {direcao_saldo} {_money_text(abs(comparacao_saldo))}.")
    else:
        analises.append("Sem fechamento anterior para comparação automática.")

    recomendacoes = []
    if saldo < 0:
        recomendacoes.append("Prioridade: reduzir saídas variáveis ou pausar gastos não essenciais até recuperar saldo positivo.")
    elif percentual_gasto > 85:
        recomendacoes.append("Atenção: a maior parte da receita já foi comprometida. Vale revisar lazer, delivery e compras parceladas.")
    elif percentual_gasto < 60 and receita_total > 0:
        recomendacoes.append("Boa margem: existe espaço para reforçar uma meta ou investimento sem pressionar o mês.")
    else:
        recomendacoes.append("Mantenha o acompanhamento semanal para evitar surpresas no fechamento.")

    if float(resumo_orcamento.get("total_fora_orcamento", 0) or 0) > 0:
        recomendacoes.append("Crie orçamento para categorias que ainda estão fora do planejamento.")
    if quantidade_metas == 0:
        recomendacoes.append("Cadastre pelo menos uma meta para dar sentido de progresso ao sistema Virtum.")

    texto = "\n".join(["Análise do mês:", *[f"• {item}" for item in analises], "", "Recomendações:", *[f"• {item}" for item in recomendacoes]])

    return {
        "mes": mes,
        "status": status,
        "salario": salario,
        "receitas_extra": receitas_extra,
        "receita_total": receita_total,
        "saidas": saidas,
        "saldo": saldo,
        "percentual_gasto": percentual_gasto,
        "maior_categoria": maior_categoria,
        "maior_categoria_valor": maior_valor,
        "investido_mes": investido_mes,
        "patrimonio_investido": float(resumo_investido.get("total_aplicado", 0) or 0),
        "texto": texto,
        "categorias": categorias,
        "orcamento": resumo_orcamento,
        "metas": resumo_metas,
    }


def salvar_orcamento_categoria(mes: str, categoria: str, limite: float, observacoes: str = "") -> None:
    migrar_banco()
    with conectar() as conn:
        conn.execute(
            """
            INSERT INTO orcamentos_categoria (mes, categoria, limite, observacoes, atualizado_em)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(mes, categoria)
            DO UPDATE SET
                limite=excluded.limite,
                observacoes=excluded.observacoes,
                atualizado_em=CURRENT_TIMESTAMP
            """,
            (mes, categoria, float(limite), observacoes or ""),
        )


def atualizar_orcamento_categoria(orcamento_id: int, mes: str, categoria: str, limite: float, observacoes: str = "") -> None:
    migrar_banco()
    with conectar() as conn:
        conn.execute("DELETE FROM orcamentos_categoria WHERE id=?", (int(orcamento_id),))
        conn.execute(
            """
            INSERT INTO orcamentos_categoria (mes, categoria, limite, observacoes, atualizado_em)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(mes, categoria)
            DO UPDATE SET
                limite=excluded.limite,
                observacoes=excluded.observacoes,
                atualizado_em=CURRENT_TIMESTAMP
            """,
            (mes, categoria, float(limite), observacoes or ""),
        )


def listar_orcamentos_do_mes(mes: str) -> list[dict[str, Any]]:
    migrar_banco()
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, mes, categoria, limite, observacoes
            FROM orcamentos_categoria
            WHERE mes=?
            ORDER BY categoria ASC
            """,
            (mes,),
        )
        rows = cur.fetchall()

    return [
        {
            "id": int(row[0]),
            "mes": str(row[1]),
            "categoria": str(row[2] or "Outros"),
            "limite": float(row[3] or 0),
            "observacoes": str(row[4] or ""),
        }
        for row in rows
    ]


def obter_orcamento(orcamento_id: int) -> dict[str, Any] | None:
    migrar_banco()
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, mes, categoria, limite, observacoes
            FROM orcamentos_categoria
            WHERE id=?
            """,
            (int(orcamento_id),),
        )
        row = cur.fetchone()

    if not row:
        return None
    return {
        "id": int(row[0]),
        "mes": str(row[1]),
        "categoria": str(row[2] or "Outros"),
        "limite": float(row[3] or 0),
        "observacoes": str(row[4] or ""),
    }


def excluir_orcamento_categoria(orcamento_id: int) -> None:
    migrar_banco()
    with conectar() as conn:
        conn.execute("DELETE FROM orcamentos_categoria WHERE id=?", (int(orcamento_id),))


def resumo_orcamentos_do_mes(mes: str) -> dict[str, Any]:
    migrar_banco()
    orcamentos = listar_orcamentos_do_mes(mes)

    with conectar() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT categoria, COALESCE(SUM(valor), 0)
            FROM gastos
            WHERE data LIKE ?
            GROUP BY categoria
            """,
            (f"{mes}%",),
        )
        gastos_por_categoria = {str(row[0] or "Outros"): float(row[1] or 0) for row in cur.fetchall()}

    linhas = []
    total_orcado = 0.0
    total_usado_orcado = 0.0

    for orcamento in orcamentos:
        limite = float(orcamento["limite"] or 0)
        usado = float(gastos_por_categoria.get(orcamento["categoria"], 0.0))
        livre = limite - usado
        percentual = (usado / limite * 100.0) if limite > 0 else 0.0
        status = "Dentro" if livre >= 0 else "Ultrapassou"

        total_orcado += limite
        total_usado_orcado += usado

        linhas.append({
            **orcamento,
            "usado": usado,
            "livre": livre,
            "percentual": percentual,
            "status": status,
        })

    categorias_orcadas = {item["categoria"] for item in orcamentos}
    total_fora_orcamento = sum(
        valor for categoria, valor in gastos_por_categoria.items()
        if categoria not in categorias_orcadas
    )

    return {
        "mes": mes,
        "total_orcado": total_orcado,
        "total_usado_orcado": total_usado_orcado,
        "saldo_orcamento": total_orcado - total_usado_orcado,
        "total_fora_orcamento": total_fora_orcamento,
        "quantidade": len(orcamentos),
        "linhas": linhas,
    }


def criar_meta_financeira(
    nome: str,
    categoria: str,
    valor_alvo: float,
    valor_atual: float,
    data_limite: str,
    observacoes: str,
    concluida: bool = False,
) -> None:
    migrar_banco()
    with conectar() as conn:
        conn.execute(
            """
            INSERT INTO metas_financeiras
                (nome, categoria, valor_alvo, valor_atual, data_limite, observacoes, concluida, atualizado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                nome,
                categoria,
                float(valor_alvo),
                float(valor_atual),
                data_limite or "",
                observacoes or "",
                1 if concluida else 0,
            ),
        )


def listar_metas_financeiras() -> list[dict[str, Any]]:
    migrar_banco()
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, nome, categoria, valor_alvo, valor_atual, data_limite, observacoes, concluida
            FROM metas_financeiras
            ORDER BY concluida ASC, id DESC
            """
        )
        rows = cur.fetchall()

    metas = []
    for row in rows:
        metas.append({
            "id": int(row[0]),
            "nome": str(row[1] or ""),
            "categoria": str(row[2] or "Outro"),
            "valor_alvo": float(row[3] or 0),
            "valor_atual": float(row[4] or 0),
            "data_limite": str(row[5] or ""),
            "observacoes": str(row[6] or ""),
            "concluida": int(row[7] or 0),
        })
    return metas


def obter_meta_financeira(meta_id: int) -> dict[str, Any] | None:
    for meta in listar_metas_financeiras():
        if int(meta["id"]) == int(meta_id):
            return meta
    return None


def atualizar_meta_financeira(
    meta_id: int,
    nome: str,
    categoria: str,
    valor_alvo: float,
    valor_atual: float,
    data_limite: str,
    observacoes: str,
    concluida: bool = False,
) -> None:
    migrar_banco()
    with conectar() as conn:
        conn.execute(
            """
            UPDATE metas_financeiras
            SET nome=?, categoria=?, valor_alvo=?, valor_atual=?, data_limite=?, observacoes=?, concluida=?, atualizado_em=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (
                nome,
                categoria,
                float(valor_alvo),
                float(valor_atual),
                data_limite or "",
                observacoes or "",
                1 if concluida else 0,
                int(meta_id),
            ),
        )


def excluir_meta_financeira(meta_id: int) -> None:
    migrar_banco()
    with conectar() as conn:
        conn.execute("DELETE FROM metas_financeiras WHERE id=?", (int(meta_id),))


def resumo_metas_financeiras() -> dict[str, Any]:
    metas = listar_metas_financeiras()
    total_alvo = sum(float(meta["valor_alvo"] or 0) for meta in metas)
    total_atual = sum(float(meta["valor_atual"] or 0) for meta in metas)
    percentual = (total_atual / total_alvo * 100.0) if total_alvo > 0 else 0.0
    concluidas = sum(1 for meta in metas if int(meta.get("concluida", 0)) == 1 or float(meta.get("valor_atual", 0) or 0) >= float(meta.get("valor_alvo", 0) or 0) > 0)

    return {
        "total_alvo": total_alvo,
        "total_atual": total_atual,
        "faltante": max(total_alvo - total_atual, 0.0),
        "percentual": percentual,
        "quantidade": len(metas),
        "concluidas": concluidas,
        "linhas": metas,
    }

def listar_medalhas_mensais(limit: int = 12) -> list[dict[str, Any]]:
    migrar_banco()
    with conectar() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT mes, codigo, nome, emoji, xp_bonus, criterios, saldo, total_gastos, receita_total,
                   orcamentos_dentro, investiu_no_mes, atualizado_em
            FROM medalhas_mensais
            ORDER BY mes DESC
            LIMIT ?
            """,
            (int(limit),),
        )
        rows = cur.fetchall()

    return [
        {
            "mes": str(row[0] or ""),
            "codigo": str(row[1] or "bronze"),
            "nome": str(row[2] or "Medalha Bronze"),
            "emoji": str(row[3] or "🥉"),
            "xp_bonus": int(row[4] or 0),
            "criterios": str(row[5] or ""),
            "saldo": float(row[6] or 0),
            "total_gastos": float(row[7] or 0),
            "receita_total": float(row[8] or 0),
            "orcamentos_dentro": int(row[9] or 0),
            "investiu_no_mes": int(row[10] or 0),
            "atualizado_em": str(row[11] or ""),
        }
        for row in rows
    ]


# ======================
# GAMIFICAÇÃO VIRTUM
# ======================

XP_POR_NIVEL = 250

RANKS_FINANCEIROS = [
    {
        "codigo": "aprendiz_financeiro",
        "nome": "Aprendiz Financeiro",
        "emoji": "🌱",
        "nivel_minimo": 1,
        "descricao": "Começou a organizar a vida financeira e registrar movimentações.",
    },
    {
        "codigo": "organizador_financeiro",
        "nome": "Organizador Financeiro",
        "emoji": "📘",
        "nivel_minimo": 3,
        "descricao": "Já mantém registros, acompanha entradas e entende o fluxo do mês.",
    },
    {
        "codigo": "controlador_de_gastos",
        "nome": "Controlador de Gastos",
        "emoji": "🛡️",
        "nivel_minimo": 5,
        "descricao": "Controla saídas, usa orçamentos e reduz decisões no impulso.",
    },
    {
        "codigo": "planejador_estrategico",
        "nome": "Planejador Estratégico",
        "emoji": "🎯",
        "nivel_minimo": 8,
        "descricao": "Usa metas, orçamentos e fechamentos para planejar o próximo ciclo.",
    },
    {
        "codigo": "investidor_iniciante",
        "nome": "Investidor Iniciante",
        "emoji": "📈",
        "nivel_minimo": 11,
        "descricao": "Começou a transformar saldo em patrimônio e acompanhar aplicações.",
    },
    {
        "codigo": "guardiao_do_saldo",
        "nome": "Guardião do Saldo",
        "emoji": "💠",
        "nivel_minimo": 15,
        "descricao": "Construiu consistência, fecha meses melhores e protege o orçamento.",
    },
    {
        "codigo": "mestre_virtum",
        "nome": "Mestre Virtum",
        "emoji": "👑",
        "nivel_minimo": 20,
        "descricao": "Domina o ciclo financeiro pessoal com clareza, disciplina e evolução.",
    },
]


def _titulo_por_nivel(nivel: int) -> str:
    if nivel >= 20:
        return "Mestre Virtum"
    if nivel >= 15:
        return "Guardião do Saldo"
    if nivel >= 11:
        return "Investidor em Evolução"
    if nivel >= 8:
        return "Estrategista Financeiro"
    if nivel >= 5:
        return "Controlador de Gastos"
    if nivel >= 3:
        return "Organizador Financeiro"
    return "Aprendiz Virtum"


def _calcular_nivel(xp_total: int) -> tuple[int, int, int, str]:
    xp_total = max(int(xp_total or 0), 0)
    nivel = max(1, xp_total // XP_POR_NIVEL + 1)
    xp_nivel_atual = xp_total % XP_POR_NIVEL
    xp_proximo_nivel = XP_POR_NIVEL
    return nivel, xp_nivel_atual, xp_proximo_nivel, _titulo_por_nivel(nivel)


def _rank_financeiro_por_nivel(nivel: int) -> dict[str, Any]:
    nivel = max(int(nivel or 1), 1)
    ranks = [dict(rank) for rank in RANKS_FINANCEIROS]
    atual = ranks[0]
    for rank in ranks:
        if nivel >= int(rank["nivel_minimo"]):
            atual = rank
        else:
            break

    proximo = next((rank for rank in ranks if int(rank["nivel_minimo"]) > nivel), None)
    if proximo:
        inicio = int(atual["nivel_minimo"])
        fim = int(proximo["nivel_minimo"])
        progresso = ((nivel - inicio) / max(fim - inicio, 1)) * 100.0
        niveis_para_proximo = max(fim - nivel, 0)
    else:
        progresso = 100.0
        niveis_para_proximo = 0

    trilha = []
    for rank in ranks:
        item = dict(rank)
        item["desbloqueado"] = nivel >= int(item["nivel_minimo"])
        item["atual"] = item["codigo"] == atual["codigo"]
        trilha.append(item)

    return {
        "atual": dict(atual),
        "proximo": dict(proximo) if proximo else None,
        "progresso": max(0.0, min(progresso, 100.0)),
        "niveis_para_proximo": niveis_para_proximo,
        "trilha": trilha,
    }


def _registrar_evento_gamificacao(
    cur: sqlite3.Cursor,
    chave: str,
    tipo: str,
    referencia: str,
    xp: int,
    descricao: str,
) -> None:
    cur.execute(
        """
        INSERT OR IGNORE INTO gamificacao_eventos (chave, tipo, referencia, xp, descricao)
        VALUES (?, ?, ?, ?, ?)
        """,
        (chave, tipo, referencia, int(xp), descricao),
    )


def _registrar_conquista_gamificacao(
    cur: sqlite3.Cursor,
    chave: str,
    nome: str,
    descricao: str,
    xp_bonus: int,
    desbloqueada: bool,
) -> None:
    cur.execute(
        """
        INSERT INTO gamificacao_conquistas
            (chave, nome, descricao, xp_bonus, desbloqueada, desbloqueada_em)
        VALUES (?, ?, ?, ?, ?, CASE WHEN ? = 1 THEN CURRENT_TIMESTAMP ELSE '' END)
        ON CONFLICT(chave)
        DO UPDATE SET
            nome=excluded.nome,
            descricao=excluded.descricao,
            xp_bonus=excluded.xp_bonus,
            desbloqueada=excluded.desbloqueada,
            desbloqueada_em=CASE
                WHEN excluded.desbloqueada = 1 AND gamificacao_conquistas.desbloqueada_em = '' THEN CURRENT_TIMESTAMP
                WHEN excluded.desbloqueada = 0 THEN ''
                ELSE gamificacao_conquistas.desbloqueada_em
            END
        """,
        (chave, nome, descricao, int(xp_bonus), 1 if desbloqueada else 0, 1 if desbloqueada else 0),
    )


def recalcular_gamificacao(mes: str | None = None) -> dict[str, Any]:
    migrar_banco()
    mes_atual = mes or date.today().strftime("%Y-%m")

    with conectar() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM gamificacao_eventos")

        # Ações base
        cur.execute("SELECT id, categoria, valor, data FROM gastos ORDER BY id ASC")
        gastos = cur.fetchall()
        for gasto_id, categoria, valor, data_iso in gastos:
            _registrar_evento_gamificacao(
                cur,
                f"gasto:{gasto_id}",
                "Gasto",
                str(gasto_id),
                5,
                f"Registrou saída em {categoria or 'Outros'} no valor de {_money_text(float(valor or 0))}.",
            )

        cur.execute("SELECT id, fonte, valor, data FROM receitas_extras ORDER BY id ASC")
        receitas = cur.fetchall()
        for receita_id, fonte, valor, data_iso in receitas:
            _registrar_evento_gamificacao(
                cur,
                f"receita:{receita_id}",
                "Entrada",
                str(receita_id),
                8,
                f"Registrou entrada extra de {fonte or 'Outros'} no valor de {_money_text(float(valor or 0))}.",
            )

        cur.execute("SELECT id, nome, valor_aplicado FROM investimentos ORDER BY id ASC")
        investimentos = cur.fetchall()
        for investimento_id, nome, valor_aplicado in investimentos:
            _registrar_evento_gamificacao(
                cur,
                f"investimento:{investimento_id}",
                "Investimento",
                str(investimento_id),
                50,
                f"Aplicou {_money_text(float(valor_aplicado or 0))} em {nome or 'investimento'}.",
            )

        cur.execute("SELECT id, categoria, limite, mes FROM orcamentos_categoria ORDER BY id ASC")
        orcamentos = cur.fetchall()
        for orcamento_id, categoria, limite, mes_orcamento in orcamentos:
            _registrar_evento_gamificacao(
                cur,
                f"orcamento:{orcamento_id}",
                "Orçamento",
                str(orcamento_id),
                20,
                f"Definiu orçamento de {_money_text(float(limite or 0))} para {categoria or 'categoria'} em {mes_orcamento or 'mês'}.",
            )

        cur.execute("SELECT id, nome, valor_atual, valor_alvo, concluida FROM metas_financeiras ORDER BY id ASC")
        metas = cur.fetchall()
        for meta_id, nome, valor_atual, valor_alvo, concluida in metas:
            _registrar_evento_gamificacao(
                cur,
                f"meta:{meta_id}",
                "Meta",
                str(meta_id),
                20,
                f"Criou ou acompanhou a meta {nome or 'financeira'}.",
            )
            if int(concluida or 0) == 1 or (float(valor_alvo or 0) > 0 and float(valor_atual or 0) >= float(valor_alvo or 0)):
                _registrar_evento_gamificacao(
                    cur,
                    f"meta_concluida:{meta_id}",
                    "Meta concluída",
                    str(meta_id),
                    100,
                    f"Concluiu a meta {nome or 'financeira'}.",
                )

        cur.execute("SELECT mes, total, saldo FROM resumo ORDER BY mes ASC")
        fechamentos = cur.fetchall()
        for mes_fechado, total, saldo in fechamentos:
            _registrar_evento_gamificacao(
                cur,
                f"fechamento:{mes_fechado}",
                "Fechamento",
                str(mes_fechado),
                30,
                f"Fechou o mês {mes_fechado} com saídas de {_money_text(float(total or 0))}.",
            )
            if float(saldo or 0) >= 0:
                _registrar_evento_gamificacao(
                    cur,
                    f"saldo_positivo:{mes_fechado}",
                    "Saldo positivo",
                    str(mes_fechado),
                    80,
                    f"Manteve saldo positivo no fechamento de {mes_fechado}.",
                )

        cur.execute("SELECT mes, nome, emoji, xp_bonus, criterios FROM medalhas_mensais ORDER BY mes ASC")
        medalhas = cur.fetchall()
        for mes_medalha, nome_medalha, emoji_medalha, xp_bonus, criterios in medalhas:
            _registrar_evento_gamificacao(
                cur,
                f"medalha:{mes_medalha}",
                "Medalha mensal",
                str(mes_medalha),
                int(xp_bonus or 0),
                f"{emoji_medalha or ''} {nome_medalha or 'Medalha mensal'} em {mes_medalha}: {criterios or ''}",
            )

        # Conquistas fixas
        quantidade_gastos = len(gastos)
        quantidade_receitas = len(receitas)
        quantidade_investimentos = len(investimentos)
        quantidade_orcamentos = len(orcamentos)
        quantidade_metas = len(metas)
        quantidade_metas_concluidas = sum(
            1
            for _, _, valor_atual, valor_alvo, concluida in metas
            if int(concluida or 0) == 1 or (float(valor_alvo or 0) > 0 and float(valor_atual or 0) >= float(valor_alvo or 0))
        )
        quantidade_fechamentos = len(fechamentos)
        quantidade_fechamentos_positivos = sum(1 for _, _, saldo in fechamentos if float(saldo or 0) >= 0)
        quantidade_medalhas = len(medalhas)
        quantidade_medalhas_ouro = sum(1 for _, nome_medalha, _, _, _ in medalhas if "Ouro" in str(nome_medalha or ""))
        quantidade_medalhas_diamante = sum(1 for _, nome_medalha, _, _, _ in medalhas if "Diamante" in str(nome_medalha or ""))

        cur.execute(
            """
            SELECT COUNT(*)
            FROM orcamentos_categoria
            WHERE mes=?
            """,
            (mes_atual,),
        )
        orcamentos_mes = int(cur.fetchone()[0] or 0)

        cur.execute(
            """
            SELECT categoria, limite
            FROM orcamentos_categoria
            WHERE mes=?
            """,
            (mes_atual,),
        )
        orcamentos_linhas = cur.fetchall()
        todos_orcamentos_dentro = bool(orcamentos_linhas)
        for categoria, limite in orcamentos_linhas:
            cur.execute(
                "SELECT COALESCE(SUM(valor), 0) FROM gastos WHERE data LIKE ? AND categoria=?",
                (f"{mes_atual}%", categoria),
            )
            usado = float(cur.fetchone()[0] or 0)
            if usado > float(limite or 0):
                todos_orcamentos_dentro = False
                break

        conquistas = [
            ("primeiro_gasto", "Primeiro passo", "Registrou o primeiro gasto.", 30, quantidade_gastos >= 1),
            ("dez_gastos", "Rastreador atento", "Registrou pelo menos 10 gastos.", 60, quantidade_gastos >= 10),
            ("primeira_entrada", "Receita registrada", "Registrou a primeira entrada extra.", 40, quantidade_receitas >= 1),
            ("primeiro_orcamento", "Planejador", "Criou o primeiro orçamento por categoria.", 60, quantidade_orcamentos >= 1),
            ("orcamento_disciplinado", "Orçamento disciplinado", "Manteve os orçamentos do mês dentro do limite.", 100, todos_orcamentos_dentro),
            ("primeira_meta", "Objetivo definido", "Criou a primeira meta financeira.", 80, quantidade_metas >= 1),
            ("meta_concluida", "Meta conquistada", "Concluiu pelo menos uma meta financeira.", 120, quantidade_metas_concluidas >= 1),
            ("primeiro_investimento", "Investidor iniciante", "Registrou o primeiro investimento.", 100, quantidade_investimentos >= 1),
            ("primeiro_fechamento", "Ciclo fechado", "Salvou o primeiro fechamento mensal.", 80, quantidade_fechamentos >= 1),
            ("saldo_positivo", "Mês no verde", "Fechou pelo menos um mês com saldo positivo.", 100, quantidade_fechamentos_positivos >= 1),
            ("tres_fechamentos", "Consistência", "Salvou pelo menos 3 fechamentos mensais.", 150, quantidade_fechamentos >= 3),
            ("primeira_medalha", "Primeira medalha", "Recebeu a primeira medalha mensal no fechamento.", 80, quantidade_medalhas >= 1),
            ("medalha_ouro", "Fechamento de ouro", "Recebeu pelo menos uma Medalha Ouro.", 140, quantidade_medalhas_ouro >= 1),
            ("medalha_diamante", "Fechamento diamante", "Recebeu pelo menos uma Medalha Diamante.", 220, quantidade_medalhas_diamante >= 1),
            ("tres_medalhas", "Colecionador Virtum", "Acumulou pelo menos 3 medalhas mensais.", 180, quantidade_medalhas >= 3),
        ]
        for conquista in conquistas:
            _registrar_conquista_gamificacao(cur, *conquista)

        cur.execute("SELECT COALESCE(SUM(xp), 0) FROM gamificacao_eventos")
        xp_eventos = int(cur.fetchone()[0] or 0)
        cur.execute("SELECT COALESCE(SUM(xp_bonus), 0) FROM gamificacao_conquistas WHERE desbloqueada=1")
        xp_conquistas = int(cur.fetchone()[0] or 0)
        xp_total = xp_eventos + xp_conquistas
        nivel, xp_nivel_atual, xp_proximo_nivel, titulo = _calcular_nivel(xp_total)

        rank_info = _rank_financeiro_por_nivel(nivel)
        rank_atual = rank_info["atual"]

        cur.execute(
            """
            INSERT INTO gamificacao_perfil
                (id, xp_total, nivel, titulo, xp_nivel_atual, xp_proximo_nivel,
                 rank_codigo, rank_nome, rank_emoji, rank_descricao, atualizado_em)
            VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id)
            DO UPDATE SET
                xp_total=excluded.xp_total,
                nivel=excluded.nivel,
                titulo=excluded.titulo,
                xp_nivel_atual=excluded.xp_nivel_atual,
                xp_proximo_nivel=excluded.xp_proximo_nivel,
                rank_codigo=excluded.rank_codigo,
                rank_nome=excluded.rank_nome,
                rank_emoji=excluded.rank_emoji,
                rank_descricao=excluded.rank_descricao,
                atualizado_em=CURRENT_TIMESTAMP
            """,
            (
                xp_total,
                nivel,
                titulo,
                xp_nivel_atual,
                xp_proximo_nivel,
                str(rank_atual.get("codigo", "aprendiz_financeiro")),
                str(rank_atual.get("nome", "Aprendiz Financeiro")),
                str(rank_atual.get("emoji", "🌱")),
                str(rank_atual.get("descricao", "")),
            ),
        )

    return resumo_gamificacao(mes_atual, recalcular=False)


def resumo_gamificacao(mes: str | None = None, recalcular: bool = True) -> dict[str, Any]:
    if recalcular:
        return recalcular_gamificacao(mes)

    migrar_banco()
    mes_atual = mes or date.today().strftime("%Y-%m")

    with conectar() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT xp_total, nivel, titulo, xp_nivel_atual, xp_proximo_nivel,
                   rank_codigo, rank_nome, rank_emoji, rank_descricao
            FROM gamificacao_perfil
            WHERE id=1
            """
        )
        row = cur.fetchone()
        if not row:
            xp_total = 0
            nivel, xp_nivel_atual, xp_proximo_nivel, titulo = _calcular_nivel(0)
        else:
            xp_total = int(row[0] or 0)
            nivel = int(row[1] or 1)
            titulo = str(row[2] or _titulo_por_nivel(nivel))
            xp_nivel_atual = int(row[3] or 0)
            xp_proximo_nivel = int(row[4] or XP_POR_NIVEL)

        rank_info = _rank_financeiro_por_nivel(nivel)
        rank_atual = rank_info["atual"]
        rank_proximo = rank_info["proximo"]
        ranks = rank_info["trilha"]

        cur.execute(
            """
            SELECT chave, nome, descricao, xp_bonus, desbloqueada
            FROM gamificacao_conquistas
            ORDER BY desbloqueada DESC, id ASC
            """
        )
        conquistas = [
            {
                "chave": str(item[0]),
                "nome": str(item[1]),
                "descricao": str(item[2] or ""),
                "xp_bonus": int(item[3] or 0),
                "desbloqueada": int(item[4] or 0),
            }
            for item in cur.fetchall()
        ]

        cur.execute(
            """
            SELECT tipo, referencia, xp, descricao, criado_em
            FROM gamificacao_eventos
            ORDER BY id DESC
            LIMIT 12
            """
        )
        eventos = [
            {
                "tipo": str(item[0] or ""),
                "referencia": str(item[1] or ""),
                "xp": int(item[2] or 0),
                "descricao": str(item[3] or ""),
                "criado_em": str(item[4] or ""),
            }
            for item in cur.fetchall()
        ]

        cur.execute("SELECT COUNT(*) FROM gastos WHERE data LIKE ?", (f"{mes_atual}%",))
        gastos_mes = int(cur.fetchone()[0] or 0)
        cur.execute("SELECT COUNT(*) FROM orcamentos_categoria WHERE mes=?", (mes_atual,))
        orcamentos_mes = int(cur.fetchone()[0] or 0)
        cur.execute("SELECT COUNT(*) FROM resumo WHERE mes=?", (mes_atual,))
        fechamento_mes = int(cur.fetchone()[0] or 0)
        cur.execute(
            """
            SELECT mes, codigo, nome, emoji, xp_bonus, criterios, saldo, total_gastos, receita_total,
                   orcamentos_dentro, investiu_no_mes, atualizado_em
            FROM medalhas_mensais
            ORDER BY mes DESC
            LIMIT 12
            """
        )
        medalhas_rows = cur.fetchall()
        medalhas = [
            {
                "mes": str(row[0] or ""),
                "codigo": str(row[1] or "bronze"),
                "nome": str(row[2] or "Medalha Bronze"),
                "emoji": str(row[3] or "🥉"),
                "xp_bonus": int(row[4] or 0),
                "criterios": str(row[5] or ""),
                "saldo": float(row[6] or 0),
                "total_gastos": float(row[7] or 0),
                "receita_total": float(row[8] or 0),
                "orcamentos_dentro": int(row[9] or 0),
                "investiu_no_mes": int(row[10] or 0),
                "atualizado_em": str(row[11] or ""),
            }
            for row in medalhas_rows
        ]
        medalha_mes = next((item for item in medalhas if item.get("mes") == mes_atual), None)
        cur.execute("SELECT COALESCE(SUM(valor), 0) FROM gastos WHERE data LIKE ?", (f"{mes_atual}%",))
        total_gastos_mes = float(cur.fetchone()[0] or 0)
        cur.execute("SELECT COALESCE(SUM(valor), 0) FROM receitas_extras WHERE data LIKE ?", (f"{mes_atual}%",))
        receitas_mes = float(cur.fetchone()[0] or 0)
        cur.execute("SELECT salario FROM config WHERE id=1")
        salario = float((cur.fetchone() or [0])[0] or 0)
        saldo_mes = salario + receitas_mes - total_gastos_mes
        cur.execute("SELECT COUNT(*) FROM investimentos WHERE data_aplicacao LIKE ?", (f"{mes_atual}%",))
        investimentos_mes = int(cur.fetchone()[0] or 0)
        cur.execute("SELECT COUNT(*) FROM metas_financeiras WHERE valor_atual > 0 OR concluida=1")
        metas_movimentadas = int(cur.fetchone()[0] or 0)

    progresso_nivel = (xp_nivel_atual / xp_proximo_nivel * 100.0) if xp_proximo_nivel > 0 else 0.0
    conquistas_desbloqueadas = sum(1 for item in conquistas if int(item.get("desbloqueada", 0)) == 1)

    missoes = [
        {
            "nome": "Registrar 5 gastos no mês",
            "progresso": min(gastos_mes, 5),
            "alvo": 5,
            "xp": 25,
            "status": "Concluída" if gastos_mes >= 5 else "Em andamento",
        },
        {
            "nome": "Criar orçamento do mês",
            "progresso": min(orcamentos_mes, 1),
            "alvo": 1,
            "xp": 20,
            "status": "Concluída" if orcamentos_mes >= 1 else "Em andamento",
        },
        {
            "nome": "Fechar o mês",
            "progresso": min(fechamento_mes, 1),
            "alvo": 1,
            "xp": 30,
            "status": "Concluída" if fechamento_mes >= 1 else "Em andamento",
        },
        {
            "nome": "Manter saldo positivo",
            "progresso": 1 if saldo_mes >= 0 and (total_gastos_mes > 0 or receitas_mes > 0 or salario > 0) else 0,
            "alvo": 1,
            "xp": 80,
            "status": "Concluída" if saldo_mes >= 0 and (total_gastos_mes > 0 or receitas_mes > 0 or salario > 0) else "Em andamento",
        },
        {
            "nome": "Investir ou alimentar uma meta",
            "progresso": 1 if investimentos_mes > 0 or metas_movimentadas > 0 else 0,
            "alvo": 1,
            "xp": 50,
            "status": "Concluída" if investimentos_mes > 0 or metas_movimentadas > 0 else "Em andamento",
        },
    ]

    return {
        "mes": mes_atual,
        "xp_total": xp_total,
        "nivel": nivel,
        "titulo": titulo,
        "xp_nivel_atual": xp_nivel_atual,
        "xp_proximo_nivel": xp_proximo_nivel,
        "progresso_nivel": progresso_nivel,
        "rank_atual": rank_atual,
        "rank_proximo": rank_proximo,
        "rank_progresso": float(rank_info.get("progresso", 0) or 0),
        "rank_niveis_para_proximo": int(rank_info.get("niveis_para_proximo", 0) or 0),
        "ranks": ranks,
        "conquistas_total": len(conquistas),
        "conquistas_desbloqueadas": conquistas_desbloqueadas,
        "conquistas": conquistas,
        "eventos": eventos,
        "missoes": missoes,
        "medalhas": medalhas,
        "medalha_mes": medalha_mes,
        "medalhas_total": len(medalhas),
        "medalhas_diamante": sum(1 for item in medalhas if item.get("codigo") == "diamante"),
    }

