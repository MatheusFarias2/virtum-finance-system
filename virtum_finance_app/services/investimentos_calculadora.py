from __future__ import annotations

from dataclasses import dataclass
from typing import Any

AVISO_SIMULACAO = "Simulação estimada. As taxas podem variar. Não é recomendação de investimento."


@dataclass(frozen=True)
class ResultadoInvestimento:
    nome: str
    valor_investido: float
    rendimento_bruto: float
    imposto_estimado: float
    rendimento_liquido: float
    valor_final_liquido: float
    rentabilidade_liquida_percentual: float
    diferenca_poupanca: float = 0.0
    serie_mensal: tuple[float, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "nome": self.nome,
            "valor_investido": self.valor_investido,
            "rendimento_bruto": self.rendimento_bruto,
            "imposto_estimado": self.imposto_estimado,
            "rendimento_liquido": self.rendimento_liquido,
            "valor_final_liquido": self.valor_final_liquido,
            "rentabilidade_liquida_percentual": self.rentabilidade_liquida_percentual,
            "diferenca_poupanca": self.diferenca_poupanca,
            "serie_mensal": list(self.serie_mensal),
        }


def _percentual_para_decimal(taxa_percentual: float) -> float:
    return float(taxa_percentual or 0) / 100.0


def calcular_taxa_mensal_composta(taxa_anual: float) -> float:
    taxa_decimal = _percentual_para_decimal(taxa_anual)
    if taxa_decimal <= -1:
        raise ValueError("A taxa anual não pode ser menor ou igual a -100%.")
    return (1.0 + taxa_decimal) ** (1.0 / 12.0) - 1.0


def calcular_ir_renda_fixa(rendimento: float, dias_aplicados: int) -> float:
    rendimento = max(float(rendimento or 0), 0.0)
    dias_aplicados = int(dias_aplicados or 0)

    if dias_aplicados <= 180:
        aliquota = 0.225
    elif dias_aplicados <= 360:
        aliquota = 0.20
    elif dias_aplicados <= 720:
        aliquota = 0.175
    else:
        aliquota = 0.15

    return rendimento * aliquota


def calcular_poupanca(
    valor_inicial: float,
    prazo_meses: int,
    taxa_selic_anual: float,
    taxa_tr_mensal: float,
) -> ResultadoInvestimento:
    valor_inicial = float(valor_inicial or 0)
    prazo_meses = max(int(prazo_meses or 0), 0)

    if valor_inicial <= 0:
        raise ValueError("Valor inicial precisa ser maior que zero.")

    taxa_tr = _percentual_para_decimal(taxa_tr_mensal)

    if float(taxa_selic_anual or 0) > 8.5:
        taxa_mensal = 0.005 + taxa_tr
    else:
        taxa_selic_mensal = calcular_taxa_mensal_composta(taxa_selic_anual)
        taxa_mensal = (taxa_selic_mensal * 0.70) + taxa_tr

    serie = [valor_inicial]
    saldo = valor_inicial
    for _ in range(prazo_meses):
        saldo *= 1.0 + taxa_mensal
        serie.append(saldo)

    rendimento_bruto = saldo - valor_inicial
    rentabilidade = (rendimento_bruto / valor_inicial * 100.0) if valor_inicial > 0 else 0.0
    return ResultadoInvestimento(
        nome="Poupança",
        valor_investido=valor_inicial,
        rendimento_bruto=rendimento_bruto,
        imposto_estimado=0.0,
        rendimento_liquido=rendimento_bruto,
        valor_final_liquido=saldo,
        rentabilidade_liquida_percentual=rentabilidade,
        serie_mensal=tuple(serie),
    )


def calcular_renda_fixa_cdi(
    valor_inicial: float,
    prazo_meses: int,
    taxa_cdi_anual: float,
    percentual_cdi: float,
    dias_aplicados: int | None = None,
    nome: str = "CDI",
) -> ResultadoInvestimento:
    valor_inicial = float(valor_inicial or 0)
    prazo_meses = max(int(prazo_meses or 0), 0)

    if valor_inicial <= 0:
        raise ValueError("Valor inicial precisa ser maior que zero.")

    dias = int(dias_aplicados if dias_aplicados is not None else prazo_meses * 30)
    taxa_cdi_mensal = calcular_taxa_mensal_composta(taxa_cdi_anual)
    taxa_mensal_produto = taxa_cdi_mensal * (float(percentual_cdi or 0) / 100.0)

    serie_bruta = [valor_inicial]
    saldo_bruto = valor_inicial
    for mes in range(1, prazo_meses + 1):
        saldo_bruto *= 1.0 + taxa_mensal_produto
        rendimento_parcial = max(saldo_bruto - valor_inicial, 0.0)
        dias_parciais = max(mes * 30, 1)
        imposto_parcial = calcular_ir_renda_fixa(rendimento_parcial, dias_parciais)
        serie_bruta.append(valor_inicial + rendimento_parcial - imposto_parcial)

    rendimento_bruto = saldo_bruto - valor_inicial
    imposto = calcular_ir_renda_fixa(rendimento_bruto, dias)
    rendimento_liquido = rendimento_bruto - imposto
    valor_final = valor_inicial + rendimento_liquido
    rentabilidade = (rendimento_liquido / valor_inicial * 100.0) if valor_inicial > 0 else 0.0

    return ResultadoInvestimento(
        nome=nome,
        valor_investido=valor_inicial,
        rendimento_bruto=rendimento_bruto,
        imposto_estimado=imposto,
        rendimento_liquido=rendimento_liquido,
        valor_final_liquido=valor_final,
        rentabilidade_liquida_percentual=rentabilidade,
        serie_mensal=tuple(serie_bruta),
    )


def comparar_investimentos(
    valor_inicial: float,
    prazo_meses: int,
    taxa_cdi_anual: float,
    taxa_selic_anual: float,
    taxa_tr_mensal: float,
    percentual_cdi_personalizado: float,
) -> dict[str, Any]:
    dias = int(max(prazo_meses, 0) * 30)

    poupanca = calcular_poupanca(valor_inicial, prazo_meses, taxa_selic_anual, taxa_tr_mensal)
    sicredinvest = calcular_renda_fixa_cdi(
        valor_inicial,
        prazo_meses,
        taxa_cdi_anual,
        100.0,
        dias,
        nome="Sicredinvest CDI100",
    )
    personalizado = calcular_renda_fixa_cdi(
        valor_inicial,
        prazo_meses,
        taxa_cdi_anual,
        percentual_cdi_personalizado,
        dias,
        nome=f"CDI Personalizado ({float(percentual_cdi_personalizado or 0):.0f}% do CDI)",
    )

    base_poupanca = poupanca.valor_final_liquido
    resultados = []
    for resultado in [poupanca, sicredinvest, personalizado]:
        resultados.append(
            ResultadoInvestimento(
                nome=resultado.nome,
                valor_investido=resultado.valor_investido,
                rendimento_bruto=resultado.rendimento_bruto,
                imposto_estimado=resultado.imposto_estimado,
                rendimento_liquido=resultado.rendimento_liquido,
                valor_final_liquido=resultado.valor_final_liquido,
                rentabilidade_liquida_percentual=resultado.rentabilidade_liquida_percentual,
                diferenca_poupanca=resultado.valor_final_liquido - base_poupanca,
                serie_mensal=resultado.serie_mensal,
            )
        )

    melhor = max(resultados, key=lambda item: item.valor_final_liquido)
    return {
        "aviso": AVISO_SIMULACAO,
        "melhor_resultado": melhor.nome,
        "resultados": [resultado.as_dict() for resultado in resultados],
    }
