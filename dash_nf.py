import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly_express as px

from datetime import datetime, timedelta
from streamlit_option_menu import option_menu
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Processo Seletivo Nova Futura",
    layout="wide",
)

with st.sidebar:
    menu = option_menu(
        None,
        [
            "Parte I",
            "Parte II",
            "Parte III",
        ],
        key="menu",
        orientation="vertical",
        styles={
            "container": {"background-color": "#F0F0F0"},
        },
    )

df_cliente = pd.read_csv("dim_cliente.csv", sep=";", index_col=0)
dict_clientes = df_cliente.to_dict("index")

df_produto = pd.read_csv("dim_produto.csv", sep=";", index_col=0)
dict_produto = df_produto.to_dict("index")

df_investimento = pd.read_csv("fato_investimento.csv", sep=";", index_col=0)


# Definições Parte I
def converter_excel_data(excel_number: int) -> datetime:
    """Conveter a conveção do excel de datas, com base 1900/1/1 = 1, para objeto datetime"""
    base = datetime(1900, 1, 1)
    dias = timedelta(days=excel_number)
    return base + dias


def get_client(ID_Client=int) -> str:
    id = dict_clientes.get(ID_Client)
    return id["Nome_Cliente"]


def get_city(ID_Client=int) -> str:
    id = dict_clientes.get(ID_Client)
    return id["Cidade"]


def get_product(ID_Product=int) -> str:
    id = dict_produto.get(ID_Product)
    return id["Produto"]


def get_category(ID_Product=int) -> str:
    id = dict_produto.get(ID_Product)
    return id["Categoria"]


def classes(investment: float) -> str:
    if investment <= 10000:
        return "Bronze"
    elif investment > 10000 and investment <= 50000:
        return "Prata"
    else:
        return "Ouro"


df_investimento["Data_Investimento"] = df_investimento["Data_Investimento"].apply(
    converter_excel_data
)
df_investimento["Nome_Cliente"] = df_investimento["ID_Cliente"].apply(get_client)
df_investimento["Nome_Produto"] = df_investimento["ID_Produto"].apply(get_product)
df_investimento["Cidade"] = df_investimento["ID_Cliente"].apply(get_city)
df_investimento["Categoria"] = df_investimento["ID_Produto"].apply(get_category)
df_investimento["Mes_Investimento"] = df_investimento["Data_Investimento"].dt.strftime(
    "%Y-%m"
)
# Criação do Dataframe de consolidação mensal
df1 = pd.pivot_table(
    df_investimento,
    index=df_investimento["Mes_Investimento"],
    values=["Valor_Investido", "ID_Cliente"],
    aggfunc={"Valor_Investido": ["sum", "mean"], "ID_Cliente": "count"},
).round(2)

# Criação do Dataframe de consolidação por Produto
df2 = pd.DataFrame(
    df_investimento.groupby("Nome_Produto")["Valor_Investido"].sum().round(2)
).sort_values("Valor_Investido", ascending=False)

# Criação do Dataframe de consolidação por Cliente
df3 = pd.DataFrame(
    df_investimento.groupby("Nome_Cliente")["Valor_Investido"].sum().round(2)
).sort_values("Valor_Investido", ascending=False)

df3["Classificação"] = df3["Valor_Investido"].apply(classes)

if menu == "Parte I":
    st.header("Dataframes")
    cols = st.columns(3)
    with cols[0]:
        st.header("Consolidação por Mês")
        st.dataframe(df1, use_container_width=True)

    with cols[1]:
        st.header("Consolidação por Produto")
        st.dataframe(df2, use_container_width=True)

    with cols[2]:
        st.header("Consolidação por Cliente")
        st.dataframe(df3, use_container_width=True)

elif menu == "Parte II":

    # Definições genéricas
    def formatar_legend() -> dict:
        legend = dict(
            orientation="h", yanchor="middle", xanchor="left", x=-0.077, y=1.05
        )
        return legend

    def formatar_margin() -> dict:
        margin = dict(l=0, r=0, t=90, b=0)
        return margin

    # Definições dos gráficos
    def load_graph_invest_por_mes() -> go.Figure:
        graph1 = make_subplots(specs=[[{"secondary_y": True}]])

        y1 = df1["Valor_Investido"]["sum"].values
        y2 = df1["Valor_Investido"]["sum"].pct_change().fillna(0) * 100

        graph1.add_trace(go.Bar(x=df1.index, y=y1, name="Volume (R$)"))

        graph1.add_trace(
            go.Scatter(
                y=y2,
                x=df1.index,
                marker=dict(size=5, color="blue"),
                name="Variação Percentual",
            ),
            secondary_y=True,
        )

        graph1.update_layout(
            title="Evolução Dos Investimemtos por Mês e sua Variação (%)",
            yaxis=dict(title="Volume (R$)"),
            yaxis2=dict(
                title="Var (%)",
                side="right",
            ),
            legend=formatar_legend(),
            margin=formatar_margin(),
            colorway=px.colors.sequential.Emrld,
        )

        return graph1

    def load_graph_cliente_classes() -> go.Figure:
        graph2 = go.Figure()

        graph2.add_trace(
            go.Pie(
                labels=df3["Classificação"],
                values=df3["Valor_Investido"],
            )
        )

        graph2.update_layout(
            xaxis_tickangle=20,
            title="Concetração por Classifiação de Cliente",
            legend=formatar_legend(),
            margin=formatar_margin(),
            colorway=px.colors.sequential.Emrld,
        )

        return graph2

    def load_maptree_category_product():
        fig = px.treemap(
            data_frame=df_investimento,
            path=["Categoria", "Nome_Produto"],
            values="Valor_Investido",
            color_discrete_sequence=px.colors.sequential.Emrld,
            title="Concetração de Investimento por Categoria e Produto",
        )

        return fig

    def load_graph_cidade_produto() -> go.Figure:

        df_grouped = df_investimento.groupby(
            ["Cidade", "Categoria"], as_index=False
        ).sum(numeric_only=True)

        categorias = df_grouped["Categoria"].unique()

        traces = []
        for categoria in categorias:
            categoria_data = df_grouped[df_grouped["Categoria"] == categoria]
            traces.append(
                go.Bar(
                    name=categoria,
                    x=categoria_data["Cidade"],
                    y=categoria_data["Valor_Investido"],
                )
            )
        fig = go.Figure(data=traces)

        fig.update_layout(
            barmode="group",
            title="Investimentos por Cidade e Categoria de Ativos",
            xaxis_title="Cidade",
            yaxis_title="Valor Investido",
            margin=formatar_margin(),
            legend=formatar_legend(),
            colorway=px.colors.sequential.Emrld,
        )

        return fig

    def load_graph_produto_por_mes() -> go.Figure:

        df_grouped = (
            df_investimento.groupby(
                ["Nome_Produto", "Mes_Investimento"], as_index=False
            )
            .sum(numeric_only=True)
            .set_index("Mes_Investimento")
        )

        produtos = df_grouped["Nome_Produto"].unique()

        traces = []
        for produto in produtos:
            categoria_data = df_grouped[df_grouped["Nome_Produto"] == produto]
            traces.append(
                go.Bar(
                    name=produto,
                    x=categoria_data.index,
                    y=categoria_data["Valor_Investido"],
                )
            )

        graph5 = go.Figure(data=traces)

        graph5.update_layout(
            barmode="stack",
            title="Volume de Investimentos Mensal por Produto",
            yaxis_title="Volume (R$)",
            margin=formatar_margin(),
            legend=formatar_legend(),
            colorway=px.colors.sequential.Emrld,
        )

        return graph5

    # Estrutura da página
    cols1 = st.columns(3)

    with cols1[0]:
        st.plotly_chart(load_graph_invest_por_mes())
    with cols1[1]:
        st.plotly_chart(load_graph_cliente_classes())
    with cols1[2]:
        st.plotly_chart(load_graph_produto_por_mes())

    cols2 = st.columns(2)

    with cols2[0]:
        st.plotly_chart(load_maptree_category_product())
    with cols2[1]:
        st.plotly_chart(load_graph_cidade_produto())

elif menu == "Parte III":
    st.header("Análise dos Resultados")
    st.markdown(
        """
        **Analisando os dados**, é possível observar um **aumento significativo no volume de investimentos** no mês de **fevereiro**, com um aumento de **120%**.  

        - Esse comportamento pode ser atribuído a diversos fatores, sendo um deles o **planejamento financeiro das pessoas** no início do ano, que tende a ser mais levado a sério. No começo de um novo ciclo, muitas pessoas aproveitam para organizar suas finanças, definir metas de poupança e investir recursos de forma mais estruturada.  
        - Outro fator que pode ter contribuído é a **projeção de aumento da taxa de juros**, comum no período. Quando o mercado antecipa um cenário de alta nos juros, os investimentos em renda fixa, como CDBs, LCIs ou Tesouro Direto, tornam-se mais atrativos devido à perspectiva de maior rentabilidade.  
        - Além disso, a proximidade do início do ano pode coincidir com **pagamentos de bônus corporativos ou restituições financeiras**, o que disponibiliza mais recursos para serem alocados em investimentos.  

        Portanto, essa combinação de **fatores comportamentais e macroeconômicos** ajuda a explicar o aumento expressivo no volume de investimentos em fevereiro.
        """
    )

    st.markdown(
        """
        **Analisando os dados**, é possível perceber um **aumento significativo no volume de investimentos** no mês de **fevereiro**.  

        - Esse comportamento pode estar relacionado ao **planejamento financeiro pessoal**, que costuma ser mais rigoroso no início do ano. Muitas pessoas utilizam esse período para traçar metas financeiras, como aumentar investimentos ou poupança.  
        - Além disso, o período pode ter sido influenciado por fatores macroeconômicos, como a **projeção de alta na taxa de juros**. Quando os investidores percebem um aumento na taxa como tendência, há um movimento de realocar recursos para aplicações mais vantajosas, como renda fixa, que se tornam mais atrativas nesses cenários.  
        - Outro ponto a considerar é o impacto de possíveis **bonificações de início de ano**, como pagamento de bônus corporativos ou rendimentos extras, que podem ter sido direcionados para investimentos.  

        Essa combinação de fatores, tanto comportamentais quanto econômicos, ajuda a explicar o aumento observado nesse período.
        """
    )

    st.markdown(
        """
        **De todos os produtos destacados**, o **LCI (Letra de Crédito Imobiliário)** se destacou como o investimento com maior volume de aportes no período analisado, ficando muito à frente dos demais produtos.  

        - Esse comportamento pode ser atribuído a diversos fatores, sendo o principal o **aumento das taxas oferecidas por esse ativo**, que se tornou mais competitivo no mercado durante o período. Esse aumento está diretamente relacionado ao **aquecimento do mercado imobiliário**, que impulsionou a demanda por crédito e, consequentemente, a emissão de LCIs.  
        - Outro fator de grande influência é a **isenção de imposto de renda para pessoas físicas**, característica desse tipo de investimento. Essa vantagem fiscal torna o retorno líquido do LCI ainda mais atrativo em comparação a outros produtos financeiros, especialmente em cenários de taxas de juros elevadas.  
        - Além disso, o LCI combina características de **segurança e rendimento**, já que é garantido pelo FGC (Fundo Garantidor de Créditos) até o limite estabelecido, o que proporciona maior confiança para os investidores de perfil conservador.  

        Esses aspectos fizeram do LCI a escolha preferida durante o período analisado, consolidando sua posição como um ativo de destaque no portfólio de muitos investidores.
        """
    )
