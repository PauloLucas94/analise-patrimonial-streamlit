import pandas as pd
from pathlib import Path
import sys

def consolidar_csvs(pasta_origem='data', arquivo_saida='dados_consolidados.csv'):
    """
    Consolida todos os CSVs de uma pasta em um único arquivo
    """
    pasta = Path(pasta_origem)
    
    if not pasta.exists():
        print(f"❌ Pasta '{pasta_origem}' não encontrada!")
        return False
    
    csv_files = sorted(pasta.glob('*.csv'))
    
    if not csv_files:
        print(f"❌ Nenhum CSV encontrado em '{pasta_origem}'")
        return False
    
    print(f"📂 Encontrados {len(csv_files)} arquivos CSV")
    print("-" * 50)
    
    dataframes = []
    total_linhas = 0
    
    for idx, csv_file in enumerate(csv_files, 1):
        try:
            print(f"[{idx}/{len(csv_files)}] Lendo {csv_file.name}...", end=' ')
            
            # Tenta UTF-8 primeiro
            try:
                df = pd.read_csv(csv_file, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(csv_file, encoding='latin-1')
            
            # Adiciona coluna de origem
            df['arquivo_origem'] = csv_file.name
            
            dataframes.append(df)
            total_linhas += len(df)
            
            print(f"✓ {len(df):,} linhas")
            
        except Exception as e:
            print(f"❌ ERRO: {str(e)}")
            continue
    
    if not dataframes:
        print("❌ Nenhum arquivo foi carregado com sucesso!")
        return False
    
    print("-" * 50)
    print(f"🔄 Consolidando {total_linhas:,} linhas...")
    
    # Concatena todos os dataframes
    dados_consolidados = pd.concat(dataframes, ignore_index=True)
    
    # Salva o arquivo consolidado
    print(f"💾 Salvando em '{arquivo_saida}'...")
    dados_consolidados.to_csv(arquivo_saida, index=False, encoding='utf-8')
    
    # Informações finais
    tamanho_mb = Path(arquivo_saida).stat().st_size / 1024 / 1024
    
    print("=" * 50)
    print("✅ CONSOLIDAÇÃO CONCLUÍDA!")
    print(f"📊 Total de registros: {len(dados_consolidados):,}")
    print(f"📋 Colunas: {len(dados_consolidados.columns)}")
    print(f"💾 Tamanho do arquivo: {tamanho_mb:.2f} MB")
    print(f"📁 Arquivo salvo: {arquivo_saida}")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    # Executa a consolidação
    sucesso = consolidar_csvs(
        pasta_origem='data',
        arquivo_saida='patrimonio_completo.csv'
    )
    
    if sucesso:
        print("\n🎯 Próximos passos:")
        print("1. Suba 'patrimonio_completo.csv' no Google Drive")
        print("2. Compartilhe publicamente e pegue o link")
        print("3. Use a URL no modo 'URLs Remotas' do seu app")
    else:
        sys.exit(1)