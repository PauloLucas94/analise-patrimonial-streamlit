# config.py
# Configure aqui as URLs dos seus arquivos CSV

# Opção 1: URLs públicas diretas
CSV_URLS = [
    "https://raw.githubusercontent.com/usuario/repo/main/data/arquivo1.csv",
    "https://raw.githubusercontent.com/usuario/repo/main/data/arquivo2.csv",
    # Adicione mais URLs conforme necessário
]

# Opção 2: Google Drive (tornar link público)
# Passo 1: No Google Drive, clique com botão direito > Compartilhar > Alterar para "Qualquer pessoa com o link"
# Passo 2: Copie o ID do arquivo da URL (https://drive.google.com/file/d/SEU_ID_AQUI/view)
# Passo 3: Use o formato abaixo
GOOGLE_DRIVE_FILES = [
    "https://drive.google.com/uc?id=SEU_ID_ARQUIVO_1",
    "https://drive.google.com/uc?id=SEU_ID_ARQUIVO_2",
]

# Opção 3: Dropbox
DROPBOX_FILES = [
    "https://www.dropbox.com/s/codigo123/arquivo1.csv?dl=1",  # Note o ?dl=1 no final
    "https://www.dropbox.com/s/codigo456/arquivo2.csv?dl=1",
]

# Escolha qual usar (descomente apenas uma opção)
DATA_URLS = CSV_URLS
# DATA_URLS = GOOGLE_DRIVE_FILES
# DATA_URLS = DROPBOX_FILES

# Configurações adicionais
AUTO_LOAD = True  # Carregar automaticamente na inicialização
CACHE_DURATION = 3600  # Cache em segundos (1 hora)