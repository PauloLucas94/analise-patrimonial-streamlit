import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date
import re
from io import BytesIO
import base64
import os
from pathlib import Path

# Configuração da página
st.set_page_config(
    page_title="Análise de Patrimônio",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

class PatrimonioAnalyzer:
    def __init__(self):
        self.data = None
        self.processed = False
    
    def load_data_from_folder(self, folder_path='data'):
        """Carrega automaticamente todos os CSVs de uma pasta"""
        dataframes = []
        folder = Path(folder_path)
        
        if not folder.exists():
            st.warning(f"⚠️ Pasta '{folder_path}' não encontrada. Criando pasta...")
            folder.mkdir(exist_ok=True)
            return False
        
        csv_files = list(folder.glob('*.csv'))
        
        if not csv_files:
            st.warning(f"⚠️ Nenhum arquivo CSV encontrado em '{folder_path}'")
            return False
        
        st.info(f"📂 Carregando {len(csv_files)} arquivo(s) CSV da pasta '{folder_path}'...")
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file, encoding='utf-8')
                df['arquivo_origem'] = csv_file.name
                dataframes.append(df)
                st.success(f"✓ {csv_file.name}: {len(df)} registros carregados")
            except UnicodeDecodeError:
                # Tenta com outra codificação
                try:
                    df = pd.read_csv(csv_file, encoding='latin-1')
                    df['arquivo_origem'] = csv_file.name
                    dataframes.append(df)
                    st.success(f"✓ {csv_file.name}: {len(df)} registros carregados (latin-1)")
                except Exception as e:
                    st.error(f"✗ Erro ao carregar {csv_file.name}: {str(e)}")
            except Exception as e:
                st.error(f"✗ Erro ao carregar {csv_file.name}: {str(e)}")
        
        if dataframes:
            self.data = pd.concat(dataframes, ignore_index=True)
            return True
        return False
    
    def load_data_from_upload(self, uploaded_files):
        """Carrega dados dos arquivos CSV enviados via upload"""
        dataframes = []
        
        for uploaded_file in uploaded_files:
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
                df['arquivo_origem'] = uploaded_file.name
                dataframes.append(df)
                st.success(f"✓ {uploaded_file.name}: {len(df)} registros carregados")
            except Exception as e:
                st.error(f"✗ Erro ao carregar {uploaded_file.name}: {str(e)}")
        
        if dataframes:
            self.data = pd.concat(dataframes, ignore_index=True)
            return True
        return False
    
    def load_data_from_url(self, urls):
        """Carrega dados de URLs (GitHub, Google Drive, etc)"""
        dataframes = []
        
        for url in urls:
            try:
                # Ajusta URL do Google Drive se necessário
                if 'drive.google.com' in url:
                    file_id = url.split('/d/')[1].split('/')[0]
                    url = f'https://drive.google.com/uc?id={file_id}'
                
                df = pd.read_csv(url)
                df['arquivo_origem'] = f"URL_{len(dataframes)+1}"
                dataframes.append(df)
                st.success(f"✓ URL {len(dataframes)}: {len(df)} registros carregados")
            except Exception as e:
                st.error(f"✗ Erro ao carregar URL: {str(e)}")
        
        if dataframes:
            self.data = pd.concat(dataframes, ignore_index=True)
            return True
        return False
    
    def preprocess_data(self):
        """Preprocessa os dados"""
        if self.data is None:
            return False
        
        # Limpeza de colunas
        self.data.columns = self.data.columns.str.strip()
        
        # Conversão de datas
        if 'Data Incorporação' in self.data.columns:
            self.data['Data Incorporação'] = pd.to_datetime(self.data['Data Incorporação'], errors='coerce')
            self.data['Ano Incorporação'] = self.data['Data Incorporação'].dt.year
        
        # Conversão de similaridade
        if 'Percentagem de Similaridade (%)' in self.data.columns:
            self.data['Similaridade_Num'] = pd.to_numeric(
                self.data['Percentagem de Similaridade (%)'].str.replace('%', ''), 
                errors='coerce'
            )
        
        # Conversão de valores monetários
        if 'Valor Aquisição' in self.data.columns:
            self.data['Valor_Aquisicao_Num'] = pd.to_numeric(
                self.data['Valor Aquisição'].str.replace('R$', '').str.replace('.', '').str.replace(',', '.').str.strip(),
                errors='coerce'
            )
        
        if 'Valor Contábil' in self.data.columns:
            self.data['Valor_Contabil_Num'] = pd.to_numeric(
                self.data['Valor Contábil'].str.replace('R$', '').str.replace('.', '').str.replace(',', '.').str.strip(),
                errors='coerce'
            )
        
        # Conversão de vida útil
        if 'Vida' in self.data.columns:
            self.data['Vida_Num'] = pd.to_numeric(self.data['Vida'], errors='coerce')
        
        # Categorização
        if 'Justificativa de Reprova' in self.data.columns:
            self.data['Decisao'] = self.data['Justificativa de Reprova'].apply(self._categorizar_decisao)
            self.data['Categoria_Similaridade'] = self.data['Similaridade_Num'].apply(self._categorizar_similaridade)
        
        # Localização
        if 'Localização' in self.data.columns:
            self.data['Regiao'] = self.data['Localização'].apply(self._extrair_regiao)
        
        self.processed = True
        return True
    
    def _categorizar_decisao(self, justificativa):
        if pd.isna(justificativa):
            return "Sem Categoria"
        
        justificativa = str(justificativa).upper()
        
        if "RECLASSIFICAR" in justificativa:
            return "RECLASSIFICAR"
        elif "AVALIAR" in justificativa:
            return "AVALIAR"
        elif "MANTER" in justificativa:
            return "MANTER"
        else:
            return "OUTROS"
    
    def _categorizar_similaridade(self, similaridade):
        if pd.isna(similaridade):
            return "Sem Dados"
        
        if similaridade >= 70:
            return "Muito Alta (≥70%)"
        elif similaridade >= 50:
            return "Alta (50-69%)"
        elif similaridade >= 35:
            return "Moderada (35-49%)"
        else:
            return "Baixa (<35%)"
    
    def _extrair_regiao(self, localizacao):
        if pd.isna(localizacao):
            return "Não Informado"
        
        return str(localizacao).strip()
    
    def get_filtered_data(self, regiao_filter=None, decisao_filter=None, 
                         ano_min=None, ano_max=None, similaridade_min=None):
        """Retorna dados filtrados"""
        if not self.processed:
            return pd.DataFrame()
        
        filtered = self.data.copy()
        
        if regiao_filter and regiao_filter != "Todas":
            filtered = filtered[filtered['Regiao'] == regiao_filter]
        
        if decisao_filter and decisao_filter != "Todas":
            filtered = filtered[filtered['Decisao'] == decisao_filter]
        
        if ano_min is not None:
            filtered = filtered[filtered['Ano Incorporação'] >= ano_min]
        
        if ano_max is not None:
            filtered = filtered[filtered['Ano Incorporação'] <= ano_max]
        
        if similaridade_min is not None:
            filtered = filtered[filtered['Similaridade_Num'] >= similaridade_min]
        
        return filtered

# Funções de visualização
def create_decision_pie_chart(data):
    """Gráfico de pizza das decisões"""
    decisoes = data['Decisao'].value_counts()
    
    fig = px.pie(
        values=decisoes.values, 
        names=decisoes.index,
        title="Distribuição de Decisões",
        color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def create_similarity_histogram(data):
    """Histograma de similaridade"""
    fig = px.histogram(
        data, 
        x='Similaridade_Num',
        nbins=20,
        title="Distribuição de Similaridade (%)",
        labels={'Similaridade_Num': 'Similaridade (%)', 'count': 'Quantidade'}
    )
    
    fig.update_layout(showlegend=False)
    return fig

def create_regional_bar_chart(data):
    """Gráfico de barras por localização"""
    localizacao_counts = data['Regiao'].value_counts()
    
    fig = px.bar(
        x=localizacao_counts.index,
        y=localizacao_counts.values,
        title="Itens por Localização",
        labels={'x': 'Localização', 'y': 'Quantidade'}
    )
    
    fig.update_layout(
        showlegend=False,
        xaxis=dict(tickangle=45)
    )
    return fig

def create_similarity_box_plot(data):
    """Box plot de similaridade por decisão"""
    fig = px.box(
        data,
        x='Decisao',
        y='Similaridade_Num',
        title="Similaridade por Tipo de Decisão",
        labels={'Similaridade_Num': 'Similaridade (%)', 'Decisao': 'Decisão'}
    )
    
    return fig

def create_timeline_chart(data):
    """Gráfico temporal"""
    timeline = data.groupby(['Ano Incorporação', 'Decisao']).size().unstack(fill_value=0)
    
    fig = go.Figure()
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    
    for i, decisao in enumerate(timeline.columns):
        fig.add_trace(
            go.Scatter(
                x=timeline.index,
                y=timeline[decisao],
                mode='lines+markers',
                name=decisao,
                line=dict(color=colors[i % len(colors)])
            )
        )
    
    fig.update_layout(
        title="Timeline de Incorporações por Decisão",
        xaxis_title="Ano",
        yaxis_title="Quantidade",
        hovermode='x unified'
    )
    
    return fig

def create_strategic_metrics(data):
    """Métricas estratégicas"""
    total_itens = len(data)
    
    if total_itens == 0:
        return {}, {}
    
    # Contadores por decisão
    decisoes = data['Decisao'].value_counts()
    reclassificar = decisoes.get('RECLASSIFICAR', 0)
    avaliar = decisoes.get('AVALIAR', 0)
    manter = decisoes.get('MANTER', 0)
    
    # Estatísticas de similaridade
    similaridade_stats = data['Similaridade_Num'].describe()
    
    # Métricas principais
    metrics = {
        'total_itens': total_itens,
        'reclassificar': reclassificar,
        'avaliar': avaliar,
        'manter': manter,
        'percentual_reclassificar': (reclassificar / total_itens) * 100,
        'percentual_avaliar': (avaliar / total_itens) * 100,
        'similaridade_media': similaridade_stats.get('mean', 0),
        'alta_similaridade': len(data[data['Similaridade_Num'] >= 70])
    }
    
    # Análise regional
    regional_analysis = data.groupby('Regiao').agg({
        'Decisao': lambda x: (x == 'RECLASSIFICAR').sum(),
        'Similaridade_Num': 'mean'
    }).round(2)
    
    regional_analysis.columns = ['Itens_Reclassificar', 'Similaridade_Media']
    
    return metrics, regional_analysis

def export_to_excel(data):
    """Exporta dados para Excel"""
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Dados principais
        data.to_excel(writer, sheet_name='Dados_Completos', index=False)
        
        # Resumo por decisão
        decisao_summary = data.groupby('Decisao').agg({
            'Similaridade_Num': ['count', 'mean', 'min', 'max'],
            'Ano Incorporação': ['min', 'max']
        }).round(2)
        decisao_summary.to_excel(writer, sheet_name='Resumo_Decisoes')
        
        # Resumo regional
        regional_summary = data.groupby('Regiao').agg({
            'Decisao': lambda x: x.value_counts().to_dict(),
            'Similaridade_Num': ['count', 'mean']
        })
        regional_summary.to_excel(writer, sheet_name='Resumo_Regional')
    
    return output.getvalue()

def create_demo_data():
    """Cria dados de demonstração"""
    np.random.seed(42)
    n_samples = 1000
    
    sample_data = {
        'Localização': np.random.choice(['1.01 BRÁS', '1.02 VILA ALPINA', '2.01 SANTOS', 'SENAI SEDE', '3.01 TAUBATÉ'], n_samples),
        'Inventário': range(1000000, 1000000 + n_samples),
        'Denominação do Imobilizado': [f"EQUIPAMENTO TESTE {i}" for i in range(n_samples)],
        'Vida': np.random.choice([10, 15, 20, 25, 50], n_samples),
        'Valor Aquisição': [f"R$ {np.random.uniform(100, 50000):.2f}".replace('.', ',') for _ in range(n_samples)],
        'Valor Contábil': [f"R$ {np.random.uniform(0, 30000):.2f}".replace('.', ',') for _ in range(n_samples)],
        'Item Consumível Similar': [f"CONSUMÍVEL SIMILAR {i}" for i in range(n_samples)],
        'Percentagem de Similaridade (%)': [f"{np.random.uniform(20, 85):.1f}%" for _ in range(n_samples)],
        'Data Incorporação': pd.date_range('2010-01-01', '2025-01-01', periods=n_samples),
        'Justificativa de Reprova': np.random.choice([
            'RECLASSIFICAR: Alta similaridade (70%+)',
            'AVALIAR: Similaridade moderada (45%)',
            'MANTER: Similaridade baixa (25%)'
        ], n_samples, p=[0.25, 0.45, 0.3])
    }
    
    return pd.DataFrame(sample_data)

# Interface Streamlit
def main():
    st.title("📊 Sistema de Análise de Patrimônio")
    st.markdown("---")
    
    # Inicializar analyzer na sessão
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = PatrimonioAnalyzer()
    
    analyzer = st.session_state.analyzer
    
    # Sidebar para configurações de carregamento
    with st.sidebar:
        st.header("⚙️ Configuração de Dados")
        
        # Modo de carregamento
        load_mode = st.radio(
            "Modo de Carregamento:",
            ["🗂️ Pasta Local (Auto)", "📤 Upload Manual", "🔗 URLs Remotas", "🎯 Demonstração"],
            help="Escolha como carregar os dados"
        )
        
        st.markdown("---")
        
        # Carregamento baseado no modo selecionado
        if load_mode == "🗂️ Pasta Local (Auto)":
            st.info("📂 Carregamento automático da pasta 'data/'")
            
            folder_path = st.text_input("Caminho da pasta:", value="data")
            
            if st.button("🔄 Carregar Dados"):
                with st.spinner("Carregando arquivos..."):
                    if analyzer.load_data_from_folder(folder_path):
                        if analyzer.preprocess_data():
                            st.success(f"✓ {len(analyzer.data)} registros carregados!")
                        else:
                            st.error("Erro no processamento dos dados")
            
            # Auto-load na inicialização
            if not analyzer.processed and 'auto_loaded' not in st.session_state:
                with st.spinner("Carregando dados automaticamente..."):
                    if analyzer.load_data_from_folder(folder_path):
                        if analyzer.preprocess_data():
                            st.success(f"✓ {len(analyzer.data)} registros carregados automaticamente!")
                            st.session_state.auto_loaded = True
        
        elif load_mode == "📤 Upload Manual":
            uploaded_files = st.file_uploader(
                "Selecione os arquivos CSV",
                type=['csv'],
                accept_multiple_files=True,
                help="Você pode selecionar até 12 arquivos CSV"
            )
            
            if uploaded_files:
                if st.button("📥 Carregar Arquivos"):
                    with st.spinner("Carregando arquivos..."):
                        if analyzer.load_data_from_upload(uploaded_files):
                            if analyzer.preprocess_data():
                                st.success(f"✓ {len(analyzer.data)} registros carregados!")
                            else:
                                st.error("Erro no processamento dos dados")
        
        elif load_mode == "🔗 URLs Remotas":
            st.info("💡 Suporta GitHub Raw, Google Drive público, etc.")
            
            url_input = st.text_area(
                "URLs (uma por linha):",
                help="Cole as URLs dos arquivos CSV, uma por linha"
            )
            
            if st.button("🌐 Carregar de URLs"):
                urls = [url.strip() for url in url_input.split('\n') if url.strip()]
                if urls:
                    with st.spinner("Baixando arquivos..."):
                        if analyzer.load_data_from_url(urls):
                            if analyzer.preprocess_data():
                                st.success(f"✓ {len(analyzer.data)} registros carregados!")
                            else:
                                st.error("Erro no processamento dos dados")
        
        else:  # Demonstração
            if st.button("🎯 Gerar Dados de Demonstração"):
                with st.spinner("Criando dados de demonstração..."):
                    analyzer.data = create_demo_data()
                    analyzer.preprocess_data()
                    st.success("✓ Dados de demonstração carregados!")
    
    # Verificar se dados foram carregados
    if not analyzer.processed:
        st.info("👆 Configure o modo de carregamento na barra lateral para começar")
        
        # Instruções
        with st.expander("📖 Como usar cada modo"):
            st.markdown("""
            ### 🗂️ Pasta Local (Auto)
            - **Para Streamlit Cloud**: Crie uma pasta `data/` no seu repositório
            - Coloque seus arquivos CSV dentro dessa pasta
            - Os dados serão carregados automaticamente no deploy
            
            ### 📤 Upload Manual
            - Use para testes locais ou dados temporários
            - Arraste e solte seus CSVs
            
            ### 🔗 URLs Remotas
            - **GitHub**: Use URL raw (ex: `https://raw.githubusercontent.com/user/repo/main/data.csv`)
            - **Google Drive**: Compartilhe o arquivo publicamente e use o link
            - **Outros**: Qualquer URL pública de CSV
            
            ### 🎯 Demonstração
            - Gera 1000 registros de exemplo para testar a aplicação
            """)
        
        return
    
    # Filtros na sidebar
    with st.sidebar:
        st.markdown("---")
        st.header("🔧 Filtros")
        
        # Filtro de localização
        localizacoes = ["Todas"] + sorted(analyzer.data['Regiao'].unique().tolist())
        regiao_filter = st.selectbox("Localização", localizacoes)
        
        # Filtro de decisão
        decisoes = ["Todas"] + sorted(analyzer.data['Decisao'].unique().tolist())
        decisao_filter = st.selectbox("Decisão", decisoes)
        
        # Filtro de ano
        anos = analyzer.data['Ano Incorporação'].dropna()
        if len(anos) > 0:
            ano_min, ano_max = st.slider(
                "Período de Incorporação",
                int(anos.min()),
                int(anos.max()),
                (int(anos.min()), int(anos.max()))
            )
        else:
            ano_min, ano_max = None, None
        
        # Filtro de similaridade mínima
        similaridade_min = st.slider(
            "Similaridade Mínima (%)",
            0, 100, 0
        )
        
        # Aplicar filtros
        filtered_data = analyzer.get_filtered_data(
            regiao_filter, decisao_filter, ano_min, ano_max, similaridade_min
        )
    
    # Métricas principais
    st.header("📈 Resumo Executivo")
    
    metrics, regional_analysis = create_strategic_metrics(filtered_data)
    
    if metrics:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total de Itens",
                f"{metrics['total_itens']:,}",
                help="Número total de itens na análise"
            )
        
        with col2:
            st.metric(
                "Para Reclassificar",
                f"{metrics['reclassificar']:,}",
                f"{metrics['percentual_reclassificar']:.1f}%",
                help="Itens recomendados para reclassificação"
            )
        
        with col3:
            st.metric(
                "Para Avaliar",
                f"{metrics['avaliar']:,}",
                f"{metrics['percentual_avaliar']:.1f}%",
                help="Itens que necessitam avaliação adicional"
            )
        
        with col4:
            st.metric(
                "Similaridade Média",
                f"{metrics['similaridade_media']:.1f}%",
                help="Percentual médio de similaridade com consumíveis"
            )
    
    # Abas para diferentes análises
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Visão Geral", "🔍 Análise Detalhada", "🏢 Análise por Localização", "📋 Dados e Export"])
    
    with tab1:
        st.subheader("Visão Geral dos Dados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_pie = create_decision_pie_chart(filtered_data)
            st.plotly_chart(fig_pie, use_container_width=True)
            
            fig_hist = create_similarity_histogram(filtered_data)
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            fig_bar = create_regional_bar_chart(filtered_data)
            st.plotly_chart(fig_bar, use_container_width=True)
            
            fig_box = create_similarity_box_plot(filtered_data)
            st.plotly_chart(fig_box, use_container_width=True)
    
    with tab2:
        st.subheader("Análise Detalhada")
        
        fig_timeline = create_timeline_chart(filtered_data)
        st.plotly_chart(fig_timeline, use_container_width=True)
        
        st.subheader("⚠️ Itens de Alta Prioridade")
        
        alta_similaridade = filtered_data[filtered_data['Similaridade_Num'] >= 70]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**{len(alta_similaridade):,} itens** com similaridade ≥ 70%")
            
            if len(alta_similaridade) > 0:
                top_regioes = alta_similaridade['Regiao'].value_counts().head()
                st.write("**Localizações com mais itens de alta similaridade:**")
                for localizacao, count in top_regioes.items():
                    st.write(f"• {localizacao}: {count} itens")
        
        with col2:
            reclassificacao_imediata = filtered_data[filtered_data['Decisao'] == 'RECLASSIFICAR']
            st.warning(f"**{len(reclassificacao_imediata):,} itens** para reclassificação imediata")
            
            if len(reclassificacao_imediata) > 0:
                similaridade_media = reclassificacao_imediata['Similaridade_Num'].mean()
                st.write(f"**Similaridade média:** {similaridade_media:.1f}%")
    
    with tab3:
        st.subheader("Análise por Localização")
        
        if not regional_analysis.empty:
            st.write("**Resumo por Localização:**")
            
            regional_display = regional_analysis.copy()
            regional_display['Eficiência_Reclassificação'] = (
                regional_display['Itens_Reclassificar'] / 
                filtered_data.groupby('Regiao').size()
            ) * 100
            
            regional_display = regional_display.round(2)
            regional_display.columns = ['Itens p/ Reclassificar', 'Similaridade Média (%)', 'Eficiência (%)']
            
            st.dataframe(regional_display.sort_values('Eficiência (%)', ascending=False))
            
            fig = px.scatter(
                x=regional_display['Similaridade Média (%)'],
                y=regional_display['Eficiência (%)'],
                size=regional_display['Itens p/ Reclassificar'],
                hover_name=regional_display.index,
                title="Eficiência por Localização: Similaridade vs % Reclassificação",
                labels={
                    'x': 'Similaridade Média (%)',
                    'y': 'Eficiência na Reclassificação (%)'
                }
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.subheader("Dados e Exportação")
        
        st.write(f"**Mostrando {len(filtered_data):,} registros filtrados:**")
        
        show_columns = st.multiselect(
            "Selecione as colunas para exibir:",
            filtered_data.columns.tolist(),
            default=['Localização', 'Inventário', 'Denominação do Imobilizado', 'Item Consumível Similar', 'Decisao']
        )
        
        if show_columns:
            st.dataframe(filtered_data[show_columns])
        
        st.subheader("💾 Exportar Dados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv = filtered_data.to_csv(index=False)
            st.download_button(
                label="📄 Baixar CSV",
                data=csv,
                file_name=f"patrimonio_filtrado_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        
        with col2:
            excel_data = export_to_excel(filtered_data)
            st.download_button(
                label="📊 Baixar Excel",
                data=excel_data,
                file_name=f"patrimonio_analise_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    main()


# import streamlit as st
# import pandas as pd
# import numpy as np
# import plotly.express as px
# import plotly.graph_objects as go
# from plotly.subplots import make_subplots
# from datetime import datetime, date
# import re
# from io import BytesIO
# import base64
# import os
# from pathlib import Path

# # Configuração da página
# st.set_page_config(
#     page_title="Análise de Patrimônio",
#     page_icon="📊",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# class PatrimonioAnalyzer:
#     def __init__(self):
#         self.data = None
#         self.processed = False
    
#     def load_data_from_folder(self, folder_path='data'):
#         """Carrega automaticamente todos os CSVs de uma pasta"""
#         dataframes = []
#         folder = Path(folder_path)
        
#         if not folder.exists():
#             st.warning(f"⚠️ Pasta '{folder_path}' não encontrada. Criando pasta...")
#             folder.mkdir(exist_ok=True)
#             return False
        
#         csv_files = list(folder.glob('*.csv'))
        
#         if not csv_files:
#             st.warning(f"⚠️ Nenhum arquivo CSV encontrado em '{folder_path}'")
#             return False
        
#         st.info(f"📂 Carregando {len(csv_files)} arquivo(s) CSV da pasta '{folder_path}'...")
        
#         for csv_file in csv_files:
#             try:
#                 df = pd.read_csv(csv_file, encoding='utf-8')
#                 df['arquivo_origem'] = csv_file.name
#                 dataframes.append(df)
#                 st.success(f"✓ {csv_file.name}: {len(df)} registros carregados")
#             except UnicodeDecodeError:
#                 # Tenta com outra codificação
#                 try:
#                     df = pd.read_csv(csv_file, encoding='latin-1')
#                     df['arquivo_origem'] = csv_file.name
#                     dataframes.append(df)
#                     st.success(f"✓ {csv_file.name}: {len(df)} registros carregados (latin-1)")
#                 except Exception as e:
#                     st.error(f"✗ Erro ao carregar {csv_file.name}: {str(e)}")
#             except Exception as e:
#                 st.error(f"✗ Erro ao carregar {csv_file.name}: {str(e)}")
        
#         if dataframes:
#             self.data = pd.concat(dataframes, ignore_index=True)
#             return True
#         return False
    
#     def load_data_from_upload(self, uploaded_files):
#         """Carrega dados dos arquivos CSV enviados via upload"""
#         dataframes = []
        
#         for uploaded_file in uploaded_files:
#             try:
#                 df = pd.read_csv(uploaded_file, encoding='utf-8')
#                 df['arquivo_origem'] = uploaded_file.name
#                 dataframes.append(df)
#                 st.success(f"✓ {uploaded_file.name}: {len(df)} registros carregados")
#             except Exception as e:
#                 st.error(f"✗ Erro ao carregar {uploaded_file.name}: {str(e)}")
        
#         if dataframes:
#             self.data = pd.concat(dataframes, ignore_index=True)
#             return True
#         return False
    
#     def load_data_from_url(self, urls):
#         """Carrega dados de URLs (GitHub, Google Drive, etc)"""
#         dataframes = []
        
#         for url in urls:
#             try:
#                 # Ajusta URL do Google Drive se necessário
#                 if 'drive.google.com' in url:
#                     file_id = url.split('/d/')[1].split('/')[0]
#                     url = f'https://drive.google.com/uc?id={file_id}'
                
#                 df = pd.read_csv(url)
#                 df['arquivo_origem'] = f"URL_{len(dataframes)+1}"
#                 dataframes.append(df)
#                 st.success(f"✓ URL {len(dataframes)}: {len(df)} registros carregados")
#             except Exception as e:
#                 st.error(f"✗ Erro ao carregar URL: {str(e)}")
        
#         if dataframes:
#             self.data = pd.concat(dataframes, ignore_index=True)
#             return True
#         return False
    
#     def preprocess_data(self):
#         """Preprocessa os dados"""
#         if self.data is None:
#             return False
        
#         # Limpeza de colunas
#         self.data.columns = self.data.columns.str.strip()
        
#         # Conversão de datas
#         if 'Data Incorporação' in self.data.columns:
#             self.data['Data Incorporação'] = pd.to_datetime(self.data['Data Incorporação'], errors='coerce')
#             self.data['Ano Incorporação'] = self.data['Data Incorporação'].dt.year
        
#         # Conversão de similaridade
#         if 'Percentagem de Similaridade (%)' in self.data.columns:
#             self.data['Similaridade_Num'] = pd.to_numeric(
#                 self.data['Percentagem de Similaridade (%)'].str.replace('%', ''), 
#                 errors='coerce'
#             )
        
#         # Categorização
#         if 'Justificativa de Reprova' in self.data.columns:
#             self.data['Decisao'] = self.data['Justificativa de Reprova'].apply(self._categorizar_decisao)
#             self.data['Categoria_Similaridade'] = self.data['Similaridade_Num'].apply(self._categorizar_similaridade)
        
#         # Região
#         if 'Localização' in self.data.columns:
#             self.data['Regiao'] = self.data['Localização'].apply(self._extrair_regiao)
        
#         self.processed = True
#         return True
    
#     def _categorizar_decisao(self, justificativa):
#         if pd.isna(justificativa):
#             return "Sem Categoria"
        
#         justificativa = str(justificativa).upper()
        
#         if "RECLASSIFICAR" in justificativa:
#             return "RECLASSIFICAR"
#         elif "AVALIAR" in justificativa:
#             return "AVALIAR"
#         elif "MANTER" in justificativa:
#             return "MANTER"
#         else:
#             return "OUTROS"
    
#     def _categorizar_similaridade(self, similaridade):
#         if pd.isna(similaridade):
#             return "Sem Dados"
        
#         if similaridade >= 70:
#             return "Muito Alta (≥70%)"
#         elif similaridade >= 50:
#             return "Alta (50-69%)"
#         elif similaridade >= 35:
#             return "Moderada (35-49%)"
#         else:
#             return "Baixa (<35%)"
    
#     def _extrair_regiao(self, localizacao):
#         if pd.isna(localizacao):
#             return "Não Informado"
        
#         return str(localizacao).strip()
    
#     def get_filtered_data(self, regiao_filter=None, decisao_filter=None, 
#                          ano_min=None, ano_max=None, similaridade_min=None):
#         """Retorna dados filtrados"""
#         if not self.processed:
#             return pd.DataFrame()
        
#         filtered = self.data.copy()
        
#         if regiao_filter and regiao_filter != "Todas":
#             filtered = filtered[filtered['Regiao'] == regiao_filter]
        
#         if decisao_filter and decisao_filter != "Todas":
#             filtered = filtered[filtered['Decisao'] == decisao_filter]
        
#         if ano_min is not None:
#             filtered = filtered[filtered['Ano Incorporação'] >= ano_min]
        
#         if ano_max is not None:
#             filtered = filtered[filtered['Ano Incorporação'] <= ano_max]
        
#         if similaridade_min is not None:
#             filtered = filtered[filtered['Similaridade_Num'] >= similaridade_min]
        
#         return filtered

# # Funções de visualização (mantidas iguais)
# def create_decision_pie_chart(data):
#     """Gráfico de pizza das decisões"""
#     decisoes = data['Decisao'].value_counts()
    
#     fig = px.pie(
#         values=decisoes.values, 
#         names=decisoes.index,
#         title="Distribuição de Decisões",
#         color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
#     )
    
#     fig.update_traces(textposition='inside', textinfo='percent+label')
#     return fig

# def create_similarity_histogram(data):
#     """Histograma de similaridade"""
#     fig = px.histogram(
#         data, 
#         x='Similaridade_Num',
#         nbins=20,
#         title="Distribuição de Similaridade (%)",
#         labels={'Similaridade_Num': 'Similaridade (%)', 'count': 'Quantidade'}
#     )
    
#     fig.update_layout(showlegend=False)
#     return fig

# def create_regional_bar_chart(data):
#     """Gráfico de barras por localização"""
#     localizacao_counts = data['Regiao'].value_counts()
    
#     fig = px.bar(
#         x=localizacao_counts.index,
#         y=localizacao_counts.values,
#         title="Itens por Localização",
#         labels={'x': 'Localização', 'y': 'Quantidade'}
#     )
    
#     fig.update_layout(
#         showlegend=False,
#         xaxis=dict(tickangle=45)
#     )
#     return fig

# def create_similarity_box_plot(data):
#     """Box plot de similaridade por decisão"""
#     fig = px.box(
#         data,
#         x='Decisao',
#         y='Similaridade_Num',
#         title="Similaridade por Tipo de Decisão",
#         labels={'Similaridade_Num': 'Similaridade (%)', 'Decisao': 'Decisão'}
#     )
    
#     return fig

# def create_timeline_chart(data):
#     """Gráfico temporal"""
#     timeline = data.groupby(['Ano Incorporação', 'Decisao']).size().unstack(fill_value=0)
    
#     fig = go.Figure()
    
#     colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    
#     for i, decisao in enumerate(timeline.columns):
#         fig.add_trace(
#             go.Scatter(
#                 x=timeline.index,
#                 y=timeline[decisao],
#                 mode='lines+markers',
#                 name=decisao,
#                 line=dict(color=colors[i % len(colors)])
#             )
#         )
    
#     fig.update_layout(
#         title="Timeline de Incorporações por Decisão",
#         xaxis_title="Ano",
#         yaxis_title="Quantidade",
#         hovermode='x unified'
#     )
    
#     return fig

# def create_strategic_metrics(data):
#     """Métricas estratégicas"""
#     total_itens = len(data)
    
#     if total_itens == 0:
#         return {}, {}
    
#     # Contadores por decisão
#     decisoes = data['Decisao'].value_counts()
#     reclassificar = decisoes.get('RECLASSIFICAR', 0)
#     avaliar = decisoes.get('AVALIAR', 0)
#     manter = decisoes.get('MANTER', 0)
    
#     # Estatísticas de similaridade
#     similaridade_stats = data['Similaridade_Num'].describe()
    
#     # Métricas principais
#     metrics = {
#         'total_itens': total_itens,
#         'reclassificar': reclassificar,
#         'avaliar': avaliar,
#         'manter': manter,
#         'percentual_reclassificar': (reclassificar / total_itens) * 100,
#         'percentual_avaliar': (avaliar / total_itens) * 100,
#         'similaridade_media': similaridade_stats.get('mean', 0),
#         'alta_similaridade': len(data[data['Similaridade_Num'] >= 70])
#     }
    
#     # Análise regional
#     regional_analysis = data.groupby('Regiao').agg({
#         'Decisao': lambda x: (x == 'RECLASSIFICAR').sum(),
#         'Similaridade_Num': 'mean'
#     }).round(2)
    
#     regional_analysis.columns = ['Itens_Reclassificar', 'Similaridade_Media']
    
#     return metrics, regional_analysis

# def export_to_excel(data):
#     """Exporta dados para Excel"""
#     output = BytesIO()
    
#     with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
#         # Dados principais
#         data.to_excel(writer, sheet_name='Dados_Completos', index=False)
        
#         # Resumo por decisão
#         decisao_summary = data.groupby('Decisao').agg({
#             'Similaridade_Num': ['count', 'mean', 'min', 'max'],
#             'Ano Incorporação': ['min', 'max']
#         }).round(2)
#         decisao_summary.to_excel(writer, sheet_name='Resumo_Decisoes')
        
#         # Resumo regional
#         regional_summary = data.groupby('Regiao').agg({
#             'Decisao': lambda x: x.value_counts().to_dict(),
#             'Similaridade_Num': ['count', 'mean']
#         })
#         regional_summary.to_excel(writer, sheet_name='Resumo_Regional')
    
#     return output.getvalue()

# def create_demo_data():
#     """Cria dados de demonstração"""
#     np.random.seed(42)
#     n_samples = 1000
    
#     sample_data = {
#         'Localização': np.random.choice(['1.01 BRÁS', '1.02 VILA ALPINA', '2.01 SANTOS', 'SENAI SEDE', '3.01 TAUBATÉ'], n_samples),
#         'Inventário': range(1000000, 1000000 + n_samples),
#         'Denominação do Imobilizado': [f"EQUIPAMENTO TESTE {i}" for i in range(n_samples)],
#         'Item Consumível Similar': [f"CONSUMÍVEL SIMILAR {i}" for i in range(n_samples)],
#         'Percentagem de Similaridade (%)': [f"{np.random.uniform(20, 85):.1f}%" for _ in range(n_samples)],
#         'Data Incorporação': pd.date_range('2010-01-01', '2025-01-01', periods=n_samples),
#         'Justificativa de Reprova': np.random.choice([
#             'RECLASSIFICAR: Alta similaridade (70%+)',
#             'AVALIAR: Similaridade moderada (45%)',
#             'MANTER: Similaridade baixa (25%)'
#         ], n_samples, p=[0.25, 0.45, 0.3])
#     }
    
#     return pd.DataFrame(sample_data)

# # Interface Streamlit
# def main():
#     st.title("📊 Sistema de Análise de Patrimônio")
#     st.markdown("---")
    
#     # Inicializar analyzer na sessão
#     if 'analyzer' not in st.session_state:
#         st.session_state.analyzer = PatrimonioAnalyzer()
    
#     analyzer = st.session_state.analyzer
    
#     # Sidebar para configurações de carregamento
#     with st.sidebar:
#         st.header("⚙️ Configuração de Dados")
        
#         # Modo de carregamento
#         load_mode = st.radio(
#             "Modo de Carregamento:",
#             ["🗂️ Pasta Local (Auto)", "📤 Upload Manual", "🔗 URLs Remotas", "🎯 Demonstração"],
#             help="Escolha como carregar os dados"
#         )
        
#         st.markdown("---")
        
#         # Carregamento baseado no modo selecionado
#         if load_mode == "🗂️ Pasta Local (Auto)":
#             st.info("📂 Carregamento automático da pasta 'data/'")
            
#             folder_path = st.text_input("Caminho da pasta:", value="data")
            
#             if st.button("🔄 Carregar Dados"):
#                 with st.spinner("Carregando arquivos..."):
#                     if analyzer.load_data_from_folder(folder_path):
#                         if analyzer.preprocess_data():
#                             st.success(f"✓ {len(analyzer.data)} registros carregados!")
#                         else:
#                             st.error("Erro no processamento dos dados")
            
#             # Auto-load na inicialização
#             if not analyzer.processed and 'auto_loaded' not in st.session_state:
#                 with st.spinner("Carregando dados automaticamente..."):
#                     if analyzer.load_data_from_folder(folder_path):
#                         if analyzer.preprocess_data():
#                             st.success(f"✓ {len(analyzer.data)} registros carregados automaticamente!")
#                             st.session_state.auto_loaded = True
        
#         elif load_mode == "📤 Upload Manual":
#             uploaded_files = st.file_uploader(
#                 "Selecione os arquivos CSV",
#                 type=['csv'],
#                 accept_multiple_files=True,
#                 help="Você pode selecionar até 12 arquivos CSV"
#             )
            
#             if uploaded_files:
#                 if st.button("📥 Carregar Arquivos"):
#                     with st.spinner("Carregando arquivos..."):
#                         if analyzer.load_data_from_upload(uploaded_files):
#                             if analyzer.preprocess_data():
#                                 st.success(f"✓ {len(analyzer.data)} registros carregados!")
#                             else:
#                                 st.error("Erro no processamento dos dados")
        
#         elif load_mode == "🔗 URLs Remotas":
#             st.info("💡 Suporta GitHub Raw, Google Drive público, etc.")
            
#             url_input = st.text_area(
#                 "URLs (uma por linha):",
#                 help="Cole as URLs dos arquivos CSV, uma por linha"
#             )
            
#             if st.button("🌐 Carregar de URLs"):
#                 urls = [url.strip() for url in url_input.split('\n') if url.strip()]
#                 if urls:
#                     with st.spinner("Baixando arquivos..."):
#                         if analyzer.load_data_from_url(urls):
#                             if analyzer.preprocess_data():
#                                 st.success(f"✓ {len(analyzer.data)} registros carregados!")
#                             else:
#                                 st.error("Erro no processamento dos dados")
        
#         else:  # Demonstração
#             if st.button("🎯 Gerar Dados de Demonstração"):
#                 with st.spinner("Criando dados de demonstração..."):
#                     analyzer.data = create_demo_data()
#                     analyzer.preprocess_data()
#                     st.success("✓ Dados de demonstração carregados!")
    
#     # Verificar se dados foram carregados
#     if not analyzer.processed:
#         st.info("👆 Configure o modo de carregamento na barra lateral para começar")
        
#         # Instruções
#         with st.expander("📖 Como usar cada modo"):
#             st.markdown("""
#             ### 🗂️ Pasta Local (Auto)
#             - **Para Streamlit Cloud**: Crie uma pasta `data/` no seu repositório
#             - Coloque seus arquivos CSV dentro dessa pasta
#             - Os dados serão carregados automaticamente no deploy
            
#             ### 📤 Upload Manual
#             - Use para testes locais ou dados temporários
#             - Arraste e solte seus CSVs
            
#             ### 🔗 URLs Remotas
#             - **GitHub**: Use URL raw (ex: `https://raw.githubusercontent.com/user/repo/main/data.csv`)
#             - **Google Drive**: Compartilhe o arquivo publicamente e use o link
#             - **Outros**: Qualquer URL pública de CSV
            
#             ### 🎯 Demonstração
#             - Gera 1000 registros de exemplo para testar a aplicação
#             """)
        
#         return
    
#     # Resto da interface (mantido igual)
#     # Filtros na sidebar
#     with st.sidebar:
#         st.markdown("---")
#         st.header("🔧 Filtros")
        
#         # Filtro de localização
#         localizacoes = ["Todas"] + sorted(analyzer.data['Regiao'].unique().tolist())
#         regiao_filter = st.selectbox("Localização", localizacoes)
        
#         # Filtro de decisão
#         decisoes = ["Todas"] + sorted(analyzer.data['Decisao'].unique().tolist())
#         decisao_filter = st.selectbox("Decisão", decisoes)
        
#         # Filtro de ano
#         anos = analyzer.data['Ano Incorporação'].dropna()
#         if len(anos) > 0:
#             ano_min, ano_max = st.slider(
#                 "Período de Incorporação",
#                 int(anos.min()),
#                 int(anos.max()),
#                 (int(anos.min()), int(anos.max()))
#             )
#         else:
#             ano_min, ano_max = None, None
        
#         # Filtro de similaridade mínima
#         similaridade_min = st.slider(
#             "Similaridade Mínima (%)",
#             0, 100, 0
#         )
        
#         # Aplicar filtros
#         filtered_data = analyzer.get_filtered_data(
#             regiao_filter, decisao_filter, ano_min, ano_max, similaridade_min
#         )
    
#     # Métricas principais
#     st.header("📈 Resumo Executivo")
    
#     metrics, regional_analysis = create_strategic_metrics(filtered_data)
    
#     if metrics:
#         col1, col2, col3, col4 = st.columns(4)
        
#         with col1:
#             st.metric(
#                 "Total de Itens",
#                 f"{metrics['total_itens']:,}",
#                 help="Número total de itens na análise"
#             )
        
#         with col2:
#             st.metric(
#                 "Para Reclassificar",
#                 f"{metrics['reclassificar']:,}",
#                 f"{metrics['percentual_reclassificar']:.1f}%",
#                 help="Itens recomendados para reclassificação"
#             )
        
#         with col3:
#             st.metric(
#                 "Para Avaliar",
#                 f"{metrics['avaliar']:,}",
#                 f"{metrics['percentual_avaliar']:.1f}%",
#                 help="Itens que necessitam avaliação adicional"
#             )
        
#         with col4:
#             st.metric(
#                 "Similaridade Média",
#                 f"{metrics['similaridade_media']:.1f}%",
#                 help="Percentual médio de similaridade com consumíveis"
#             )
    
#     # Abas para diferentes análises
#     tab1, tab2, tab3, tab4 = st.tabs(["📊 Visão Geral", "🔍 Análise Detalhada", "🏢 Análise Regional", "📋 Dados e Export"])
    
#     with tab1:
#         st.subheader("Visão Geral dos Dados")
        
#         col1, col2 = st.columns(2)
        
#         with col1:
#             fig_pie = create_decision_pie_chart(filtered_data)
#             st.plotly_chart(fig_pie, use_container_width=True)
            
#             fig_hist = create_similarity_histogram(filtered_data)
#             st.plotly_chart(fig_hist, use_container_width=True)
        
#         with col2:
#             fig_bar = create_regional_bar_chart(filtered_data)
#             st.plotly_chart(fig_bar, use_container_width=True)
            
#             fig_box = create_similarity_box_plot(filtered_data)
#             st.plotly_chart(fig_box, use_container_width=True)
    
#     with tab2:
#         st.subheader("Análise Detalhada")
        
#         fig_timeline = create_timeline_chart(filtered_data)
#         st.plotly_chart(fig_timeline, use_container_width=True)
        
#         st.subheader("⚠️ Itens de Alta Prioridade")
        
#         alta_similaridade = filtered_data[filtered_data['Similaridade_Num'] >= 70]
        
#         col1, col2 = st.columns(2)
        
#         with col1:
#             st.info(f"**{len(alta_similaridade):,} itens** com similaridade ≥ 70%")
            
#             if len(alta_similaridade) > 0:
#                 top_regioes = alta_similaridade['Regiao'].value_counts().head()
#                 st.write("**Localizações com mais itens de alta similaridade:**")
#                 for localizacao, count in top_regioes.items():
#                     st.write(f"• {localizacao}: {count} itens")
        
#         with col2:
#             reclassificacao_imediata = filtered_data[filtered_data['Decisao'] == 'RECLASSIFICAR']
#             st.warning(f"**{len(reclassificacao_imediata):,} itens** para reclassificação imediata")
            
#             if len(reclassificacao_imediata) > 0:
#                 similaridade_media = reclassificacao_imediata['Similaridade_Num'].mean()
#                 st.write(f"**Similaridade média:** {similaridade_media:.1f}%")
    
#     with tab3:
#         st.subheader("Análise por Localização")
        
#         if not regional_analysis.empty:
#             st.write("**Resumo por Localização:**")
            
#             regional_display = regional_analysis.copy()
#             regional_display['Eficiência_Reclassificação'] = (
#                 regional_display['Itens_Reclassificar'] / 
#                 filtered_data.groupby('Regiao').size()
#             ) * 100
            
#             regional_display = regional_display.round(2)
#             regional_display.columns = ['Itens p/ Reclassificar', 'Similaridade Média (%)', 'Eficiência (%)']
            
#             st.dataframe(regional_display.sort_values('Eficiência (%)', ascending=False))
            
#             fig = px.scatter(
#                 x=regional_display['Similaridade Média (%)'],
#                 y=regional_display['Eficiência (%)'],
#                 size=regional_display['Itens p/ Reclassificar'],
#                 hover_name=regional_display.index,
#                 title="Eficiência por Localização: Similaridade vs % Reclassificação",
#                 labels={
#                     'x': 'Similaridade Média (%)',
#                     'y': 'Eficiência na Reclassificação (%)'
#                 }
#             )
            
#             st.plotly_chart(fig, use_container_width=True)
    
#     with tab4:
#         st.subheader("Dados e Exportação")
        
#         st.write(f"**Mostrando {len(filtered_data):,} registros filtrados:**")
        
#         show_columns = st.multiselect(
#             "Selecione as colunas para exibir:",
#             filtered_data.columns.tolist(),
#             default=['Localização', 'Denominação do Imobilizado', 'Similaridade_Num', 'Decisao']
#         )
        
#         if show_columns:
#             st.dataframe(filtered_data[show_columns])
        
#         st.subheader("💾 Exportar Dados")
        
#         col1, col2 = st.columns(2)
        
#         with col1:
#             csv = filtered_data.to_csv(index=False)
#             st.download_button(
#                 label="📄 Baixar CSV",
#                 data=csv,
#                 file_name=f"patrimonio_filtrado_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
#                 mime="text/csv"
#             )
        
#         with col2:
#             excel_data = export_to_excel(filtered_data)
#             st.download_button(
#                 label="📊 Baixar Excel",
#                 data=excel_data,
#                 file_name=f"patrimonio_analise_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
#                 mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#             )

# if __name__ == "__main__":
#     main()