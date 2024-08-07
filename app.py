import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
import matplotlib.pyplot as plt
import seaborn as sns
import io
from PIL import Image
import requests
from dotenv import load_dotenv
import os
from utils import get_csv_export_url, load_data

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()
api_key = os.getenv("NNEURAL_API_KEY")
fixed_user_email = os.getenv("FIXED_USER_EMAIL")
fixed_user_password = os.getenv("FIXED_USER_PASSWORD")
api_base_url = os.getenv("API_BASE_URL")

def authenticate():
    url = f"{api_base_url}/login"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "email": fixed_user_email,
        "password": fixed_user_password
    }

    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise Exception(f"Erro na autenticação: {response.status_code}, {response.text}")

def send_prompt_to_nneural(api_key, prompt, data, chart_info, token):
    url = f"{api_base_url}/chat"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt,
        "data": data.to_dict(orient='records'),
        "chart_info": chart_info
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json().get("response")
    else:
        raise Exception(f"Erro na solicitação: {response.status_code}, {response.text}")

def format_response(template, analysis):
    if template == "Template 1":
        return f"""
        <div style='font-family: Arial, sans-serif; padding: 20px;' id='analysis'>
            <h1 style='text-align: center;'>Relatório de Análise de Dados</h1>
            <h2>Resumo da Análise</h2>
            <p>{analysis}</p>
        </div>
        """
    elif template == "Template 2":
        return f"""
        <div style='font-family: Arial, sans-serif; padding: 20px;' id='analysis'>
            <h1 style='text-align: center;'>Data Analysis Report</h1>
            <h3>Analysis Summary</h3>
            <p>{analysis}</p>
        </div>
        """
    else:
        return f"""
        <div style='font-family: Arial, sans-serif; padding: 20px;' id='analysis'>
            <h1 style='text-align: center;'>Report</h1>
            <p>{analysis}</p>
        </div>
        """

def app():
    st.set_page_config(page_title="dataGPT v2.6", page_icon="images/favicon.ico", layout="wide", initial_sidebar_state="expanded")

    hide_streamlit_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                header {visibility: hidden;}
                </style>
                """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    selected_network = "NNeural.io"

    if api_key:
        st.sidebar.success(f"Usando a rede neural {selected_network} para análises.")

    logo = Image.open("images/dataGPT4-480x480.png")
    st.image(logo, width=128, use_column_width=False)

    st.title("dataGPT v2.6 - Gratuito e de código aberto")
    st.markdown("""
    ## Descrição
    O dataGPT v2.6 permite visualizar dados compartilhados via Google Drive. 
    Você pode inserir um link de compartilhamento de um arquivo Google Sheets, 
    escolher as colunas para os eixos X e Y de um gráfico, e visualizar os dados e o gráfico interativamente.
    Além disso, você pode utilizar inteligência artificial para analisar os gráficos gerados.

    ### Como usar:
    1 - Insira o link do arquivo Google Sheets compartilhado.
    2 - Selecione as colunas para os eixos X e Y do gráfico.
    3 - Visualize os dados carregados e o gráfico gerado.
    4 - Baixe o gráfico gerado como um arquivo HTML.
    5 - Solicite a analise da Inteligência Artificial.            
    """)

    st.sidebar.header('Link do Google Drive')
    google_drive_link = st.sidebar.text_input("Cole o link do arquivo no Google Drive")

    if google_drive_link:
        try:
            data = load_data(google_drive_link)
            st.write("Dados Carregados:")
            st.dataframe(data)

            st.sidebar.header('Filtros')
            columns = data.columns.tolist()
            filters = {}

            for column in columns:
                unique_values = data[column].unique().tolist()
                with st.sidebar.expander(f'Filtros para {column}', expanded=False):
                    selected_values = st.multiselect(f'Selecione valores para {column}', unique_values, default=unique_values)
                    filters[column] = selected_values

            for column, selected_values in filters.items():
                data = data[data[column].isin(selected_values)]

            st.sidebar.header('Configuração do Gráfico')
            x_axis_col = st.sidebar.selectbox("Selecione a coluna para o eixo X", data.columns)
            y_axis_col = st.sidebar.selectbox("Selecione a coluna para o eixo Y", data.columns)

            show_totals = st.sidebar.checkbox("Mostrar total acima das colunas", value=False)
            chart_type = st.sidebar.selectbox("Selecione o tipo de gráfico", ['Linha', 'Barra', 'Dispersão', 'Histograma', 'Boxplot', 'Heatmap', 'Áreas', 'Violino'])

            st.sidebar.header('Personalização do Gráfico')
            title = st.sidebar.text_input("Título do Gráfico", value=f"Gráfico de {x_axis_col} vs {y_axis_col}")
            x_axis_label = st.sidebar.text_input("Label do Eixo X", value=x_axis_col)
            y_axis_label = st.sidebar.text_input("Label do Eixo Y", value=y_axis_col)
            color = st.sidebar.color_picker("Escolha uma cor", value='#1f77b4')

            if x_axis_col and y_axis_col:
                if chart_type == 'Linha':
                    fig = px.line(data, x=x_axis_col, y=y_axis_col, title=title, labels={x_axis_col: x_axis_label, y_axis_col: y_axis_label}, color_discrete_sequence=[color])
                    if show_totals:
                        fig.update_traces(texttemplate='%{y}', textposition='top center')
                    st.plotly_chart(fig, use_container_width=True)
                elif chart_type == 'Barra':
                    fig = px.bar(data, x=x_axis_col, y=y_axis_col, title=title, labels={x_axis_col: x_axis_label, y_axis_col: y_axis_label}, color_discrete_sequence=[color])
                    if show_totals:
                        fig.update_traces(texttemplate='%{y}', textposition='outside')
                    st.plotly_chart(fig, use_container_width=True)
                elif chart_type == 'Dispersão':
                    fig = px.scatter(data, x=x_axis_col, y=y_axis_col, title=title, labels={x_axis_col: x_axis_label, y_axis_col: y_axis_label}, color_discrete_sequence=[color])
                    if show_totals:
                        fig.update_traces(texttemplate='%{y}', textposition='top center')
                    st.plotly_chart(fig, use_container_width=True)
                elif chart_type == 'Histograma':
                    fig, ax = plt.subplots()
                    ax.hist(data[y_axis_col], bins=30, color=color)
                    ax.set_title(title)
                    ax.set_xlabel(x_axis_label)
                    ax.set_ylabel(y_axis_label)
                    if show_totals:
                        totals = data[y_axis_col].value_counts()
                        for i, v in enumerate(totals):
                            ax.text(i, v + 0.5, str(v), ha='center')
                    st.pyplot(fig)
                elif chart_type == 'Boxplot':
                    fig, ax = plt.subplots()
                    sns.boxplot(x=data[x_axis_col], y=data[y_axis_col], ax=ax, color=color)
                    ax.set_title(title)
                    ax.set_xlabel(x_axis_label)
                    ax.set_ylabel(y_axis_label)
                    st.pyplot(fig)
                elif chart_type == 'Heatmap':
                    fig, ax = plt.subplots()
                    sns.heatmap(data.corr(), annot=True, cmap='coolwarm', ax=ax)
                    ax.set_title(title)
                    st.pyplot(fig)
                elif chart_type == 'Áreas':
                    fig = px.area(data, x=x_axis_col, y=y_axis_col, title=title, labels={x_axis_col: x_axis_label, y_axis_col: y_axis_label}, color_discrete_sequence=[color])
                    if show_totals:
                        fig.update_traces(texttemplate='%{y}', textposition='top center')
                    st.plotly_chart(fig, use_container_width=True)
                elif chart_type == 'Violino':
                    fig, ax = plt.subplots()
                    sns.violinplot(x=data[x_axis_col], y=data[y_axis_col], ax=ax, color=color)
                    ax.set_title(title)
                    ax.set_xlabel(x_axis_label)
                    ax.set_ylabel(y_axis_label)
                    st.pyplot(fig)

                if chart_type in ['Linha', 'Barra', 'Dispersão', 'Áreas']:
                    buffer = io.StringIO()
                    pio.write_html(fig, buffer)
                    html_bytes = buffer.getvalue().encode()

                    st.download_button(
                        label="Baixar Gráfico como HTML",
                        data=html_bytes,
                        file_name='grafico.html',
                        mime='text/html'
                    )

                csv = data.to_csv(index=False)
                st.download_button(
                    label="Baixar Dados Filtrados como CSV",
                    data=csv,
                    file_name='dados_filtrados.csv',
                    mime='text/csv'
                )

                st.sidebar.header('Configuração do Relatório')
                templates = ["Template 1", "Template 2"]
                selected_template = st.sidebar.selectbox("Selecione o template do relatório", templates)

                if st.button("Analisar Dados com IA"):
                    with st.spinner('Analisando dados...'):
                        prompt = f"Analisar os dados de {x_axis_col} vs {y_axis_col} com o título {title}."
                        
                        chart_info = {
                            "chart_type": chart_type,
                            "title": title,
                            "x_axis_label": x_axis_label,
                            "y_axis_label": y_axis_label,
                            "color": color,
                            "show_totals": show_totals
                        }
                        
                        try:
                            token = authenticate()  # Autentica e obtém o token
                            analysis = send_prompt_to_nneural(api_key, prompt, data, chart_info, token)
                            st.subheader("Análise da IA")
                            formatted_analysis = format_response(selected_template, analysis)
                            st.markdown(f"<div style='border: 1px solid black; padding: 20px;' id='analysis-container'>{formatted_analysis}</div>", unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"Erro ao analisar dados: {e}")

        except Exception as e:
            st.error(f"Erro ao carregar os dados: {e}")
    else:
        st.info("Por favor, insira o link do Google Drive para carregar os dados.")

if __name__ == "__main__":
    app()
