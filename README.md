<div align="center">

# 💜 Virtum Finance

### Organização financeira pessoal com visual moderno, gamificação e controle mensal.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-Qt-41CD52?style=for-the-badge&logo=qt&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Local-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Desktop](https://img.shields.io/badge/Desktop-Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white)
![Status](https://img.shields.io/badge/Status-Em%20evolução-6C63FF?style=for-the-badge)

</div>

---

## 📌 Sobre o projeto

**Virtum Finance** é um aplicativo desktop de organização financeira pessoal feito em **Python + PySide6 + SQLite**.

O objetivo do projeto é ir além de uma tabela de gastos: o app organiza entradas, saídas, investimentos, metas, orçamentos e fechamentos mensais com uma experiência visual mais limpa, moderna e gamificada.

A proposta é simples: transformar o controle financeiro em uma jornada de evolução pessoal.

---

## ✨ Destaques

- 🎨 Interface moderna com tema visual estilo Virtum.
- 🏠 Dashboard limpo com visão rápida do mês.
- 💸 Controle de gastos e entradas extras.
- 📌 Gastos fixos recorrentes com aplicação automática.
- 🎯 Orçamentos por categoria.
- 🏆 Metas financeiras com progresso.
- 📈 Módulo de investimentos e simulação.
- 📊 Relatórios e gráficos mensais.
- 📅 Fechamento mensal com histórico.
- 🎮 Gamificação com XP, níveis, ranks, medalhas e missões mensais.
- 🧭 Sidebar agrupada para reduzir excesso visual.
- 🗃️ Banco SQLite local com migração automática.
- 📦 Preparado para empacotamento com PyInstaller.

---

## 🖼️ Prévia visual

> Adicione aqui prints do sistema quando subir no GitHub.

```md
assets/screenshots/dashboard.png
assets/screenshots/gamificacao.png
assets/screenshots/investimentos.png
```

Sugestão de organização:

| Dashboard | Gamificação | Investimentos |
|---|---|---|
| ![Dashboard](assets/screenshots/dashboard.png) | ![Gamificação](assets/screenshots/gamificacao.png) | ![Investimentos](assets/screenshots/investimentos.png) |

---

## 🧩 Funcionalidades

### 🏠 Dashboard

A tela inicial mostra apenas o essencial:

- saldo atual;
- saídas do mês;
- entradas extras;
- total investido;
- nível/rank Virtum;
- resumo rápido do mês;
- ações rápidas.

---

### 💸 Movimentações

Área dedicada aos registros financeiros do mês:

- cadastro de gastos;
- edição e exclusão por duplo clique;
- entradas extras;
- investimentos;
- gastos fixos recorrentes;
- aplicação automática de fixos sem duplicação no mesmo mês.

---

### 🎯 Planejamento

Ferramentas para controle e evolução financeira:

- orçamentos por categoria;
- cálculo de limite usado;
- alerta de orçamento ultrapassado;
- metas financeiras;
- progresso visual das metas;
- status de meta ativa ou concluída.

---

### 📊 Análises

Recursos para acompanhar o desempenho financeiro:

- relatório mensal inteligente;
- gráfico mensal;
- histórico de fechamentos;
- regravação de fechamento;
- exclusão de fechamento;
- comparação com meses anteriores.

---

### 📈 Investimentos

Módulo para registrar aplicações e simular cenários:

- cadastro de investimentos;
- tipo de investimento;
- valor aplicado;
- prazo;
- liquidez;
- carência;
- simulação de rendimento;
- comparação entre poupança, CDI personalizado e Sicredinvest CDI100;
- opção de abater investimento do saldo mensal.

> As simulações são estimativas e não representam recomendação de investimento.

---

### 🎮 Gamificação Virtum

A gamificação transforma o uso do app em progresso visual.

O sistema possui:

- XP;
- níveis;
- títulos;
- ranks financeiros;
- missões mensais;
- medalhas mensais;
- conquistas;
- histórico de atividades que geraram XP.

#### 🏅 Medalhas mensais

As medalhas são geradas no fechamento do mês:

| Medalha | Critério |
|---|---|
| 🥉 Bronze | fechamento mensal salvo |
| 🥈 Prata | fechamento com saldo positivo |
| 🥇 Ouro | saldo positivo e orçamentos dentro do limite |
| 💎 Diamante | saldo positivo, orçamentos dentro do limite e investimento registrado |

#### 🧭 Ranks financeiros

| Rank | Nível necessário |
|---|---:|
| 🌱 Aprendiz Financeiro | 1 |
| 📘 Organizador Financeiro | 3 |
| 🛡️ Controlador de Gastos | 5 |
| 🎯 Planejador Estratégico | 8 |
| 📈 Investidor Iniciante | 11 |
| 💠 Guardião do Saldo | 15 |
| 👑 Mestre Virtum | 20 |

#### ✅ Missões mensais

Exemplos de missões:

- registrar 5 gastos no mês;
- registrar 10 movimentações;
- criar orçamento do mês;
- manter saldo positivo;
- investir ou alimentar uma meta;
- fechar o mês;
- respeitar os orçamentos.

---

## 🧠 Cálculo financeiro principal

O saldo mensal considera salário, entradas extras e saídas:

```text
saldo = salário + entradas extras - saídas
```

Quando um investimento é marcado para abater do saldo, ele também entra como saída do mês.

---

## 🧭 Navegação atual

A sidebar foi organizada em grupos para evitar excesso de botões visíveis:

```text
Dashboard

Movimentações
  ├─ Gastos
  ├─ Entradas
  ├─ Investimentos
  └─ Fixos

Planejamento
  ├─ Orçamentos
  └─ Metas

Análises
  ├─ Relatório
  ├─ Gráfico mensal
  ├─ Histórico
  └─ Fechamentos

Gamificação

Configurações
  ├─ Salário
  └─ Tema

Ajuda
```

---

## 🛠️ Tecnologias utilizadas

| Tecnologia | Uso |
|---|---|
| Python 3.11+ | linguagem principal |
| PySide6 | interface gráfica desktop |
| QtCharts | gráficos mensais |
| SQLite | banco local |
| PyInstaller | geração de executável Windows |

---

## 📁 Estrutura do projeto

```text
virtum_finance/
├─ virtum_finance.py
├─ requirements.txt
├─ build_virtum_finance.bat
├─ VirtumFinance.spec
├─ gastos.db
├─ README.md
└─ virtum_finance_app/
   ├─ constants.py
   ├─ db.py
   ├─ themes.py
   ├─ utils.py
   ├─ services/
   │  └─ investimentos_calculadora.py
   └─ ui/
      ├─ dialogs.py
      ├─ main_window.py
      ├─ pages.py
      └─ widgets.py
```

---

## 🚀 Como executar

### 1. Clone o repositório

```bash
git clone https://github.com/SEU-USUARIO/virtum-finance.git
cd virtum-finance
```

### 2. Crie um ambiente virtual

```bash
python -m venv .venv
```

### 3. Ative o ambiente virtual

No Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

No CMD:

```bat
.venv\Scripts\activate.bat
```

### 4. Instale as dependências

```bash
pip install -r requirements.txt
```

### 5. Execute o sistema

```bash
python virtum_finance.py
```

---

## 📦 Gerar executável Windows

Execute:

```bat
build_virtum_finance.bat
```

O executável será gerado na pasta de saída do PyInstaller.

---

## 🗃️ Banco de dados

O Virtum Finance usa **SQLite local**.

A migração automática cria e atualiza as tabelas necessárias sem apagar dados antigos.

Principais tabelas:

- `gastos`
- `receitas_extras`
- `fixos`
- `fixos_aplicados`
- `resumo`
- `investimentos`
- `orcamentos_categoria`
- `metas_financeiras`
- `gamificacao_perfil`
- `gamificacao_eventos`
- `gamificacao_conquistas`
- `medalhas_mensais`
- `missoes_mensais`

---

## 🔐 Privacidade

Os dados ficam salvos localmente no arquivo `gastos.db`.

O app não depende de internet para funcionar e não envia dados financeiros para servidores externos.

---

## 🧪 Status do projeto

O projeto está em evolução contínua.

Versão atual organizada com:

- dashboard clean;
- sidebar agrupada;
- gamificação visual;
- menu superior antigo removido;
- sistema de ranks financeiros;
- missões mensais;
- medalhas mensais.

---

## 🗺️ Próximas melhorias possíveis

- backup automático do banco;
- exportação de relatório em PDF;
- tela de configurações avançadas;
- filtros por mês e categoria em todas as listagens;
- sistema de notificações internas;
- tela de perfil do usuário;
- melhoria visual dos gráficos;
- instalador Windows completo.

---

## 👤 Autor

Desenvolvido por **Matheus Gabriel Farias**.

Projeto pessoal do ecossistema **Virtum**.

---

<div align="center">

### Virtum Finance

**Controle financeiro com clareza, progresso e evolução.**

</div>
