# 🚀 Guia Completo de Deploy no Streamlit Cloud

## 📊 Visão Geral

Este guia mostra **3 formas diferentes** de carregar dados automaticamente no Streamlit Cloud.

---

## 🎯 Método 1: Pasta Local (Arquivos pequenos < 100MB)

### ✅ Melhor para:
- Arquivos CSV pequenos e médios
- Dados que não mudam frequentemente
- Simplicidade máxima

### 📁 Estrutura do Projeto:

```
meu-projeto/
├── app.py                 # Código principal
├── requirements.txt       # Dependências
├── .gitignore            # (opcional)
└── data/                 # ← Seus CSVs aqui
    ├── patrimonio1.csv
    ├── patrimonio2.csv
    └── patrimonio3.csv
```

### 🔧 Passos:

1. **Criar estrutura de pastas:**
```bash
mkdir data
cp seus_arquivos/*.csv data/
```

2. **Criar `.gitignore` (opcional, se arquivos muito grandes):**
```
# .gitignore
*.pyc
__pycache__/
.DS_Store
```

3. **Criar `requirements.txt`:**
```
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.17.0
openpyxl>=3.1.0
xlsxwriter>=3.1.0
```

4. **Fazer commit:**
```bash
git add .
git commit -m "Deploy inicial com dados"
git push origin main
```

5. **No Streamlit Cloud:**
   - Acesse: https://share.streamlit.io
   - Conecte seu repositório GitHub
   - A app carregará automaticamente da pasta `data/`

---

## 🌐 Método 2: URLs Remotas (RECOMENDADO para arquivos grandes)

### ✅ Melhor para:
- Arquivos > 100MB
- Dados que mudam periodicamente
- Múltiplas fontes de dados
- Não sobrecarregar o repositório Git

### 📁 Estrutura do Projeto:

```
meu-projeto/
├── app.py
├── config.py             # ← Configuração de URLs
├── requirements.txt
└── README.md
```

### 🔧 Passos:

#### A) Usando GitHub (arquivos até 100MB)

1. **Criar repositório separado para dados** (opcional mas recomendado):
```
dados-patrimonio/
└── csvs/
    ├── arquivo1.csv
    ├── arquivo2.csv
    └── arquivo3.csv
```

2. **Obter URLs raw do GitHub:**
   - Navegue até o arquivo no GitHub
   - Clique em "Raw"
   - Copie a URL (formato: `https://raw.githubusercontent.com/usuario/repo/main/csvs/arquivo1.csv`)

3. **Configurar `config.py`:**
```python
CSV_URLS = [
    "https://raw.githubusercontent.com/usuario/dados-patrimonio/main/csvs/arquivo1.csv",
    "https://raw.githubusercontent.com/usuario/dados-patrimonio/main/csvs/arquivo2.csv",
]

AUTO_LOAD = True
CACHE_DURATION = 3600
```

#### B) Usando Google Drive (qualquer tamanho)

1. **Preparar arquivos no Google Drive:**
   - Faça upload dos CSVs para o Google Drive
   - Clique com botão direito no arquivo
   - Selecione "Compartilhar"
   - Altere para "Qualquer pessoa com o link"
   - Copie o link

2. **Extrair ID do arquivo:**
   - URL original: `https://drive.google.com/file/d/1ABC123XYZ789/view?usp=sharing`
   - ID: `1ABC123XYZ789`

3. **Configurar `config.py`:**
```python
GOOGLE_DRIVE_FILES = [
    "https://drive.google.com/file/d/1ABC123XYZ789/view",
    "https://drive.google.com/file/d/1DEF456UVW012/view",
]

DATA_URLS = GOOGLE_DRIVE_FILES
AUTO_LOAD = True
CACHE_DURATION = 3600
```

#### C) Usando Dropbox

1. **Preparar no Dropbox:**
   - Faça upload dos arquivos
   - Clique em "Compartilhar"
   - Crie link público
   - **IMPORTANTE**: Mude `dl=0` para `dl=1` no final da URL

2. **Configurar `config.py`:**
```python
DROPBOX_FILES = [
    "https://www.dropbox.com/s/codigo123/arquivo1.csv?dl=1",
    "https://www.dropbox.com/s/codigo456/arquivo2.csv?dl=1",
]

DATA_URLS = DROPBOX_FILES
AUTO_LOAD = True
```

---

## 🔐 Método 3: Streamlit Secrets (Dados Sensíveis)

### ✅ Melhor para:
- URLs privadas/sensíveis
- Credenciais de acesso
- Máxima segurança

### 🔧 Passos:

1. **No Streamlit Cloud:**
   - Vá em Settings → Secrets
   - Adicione as URLs:

```toml
[data]
csv_urls = [
    "https://storage.example.com/private/arquivo1.csv?token=abc123",
    "https://storage.example.com/private/arquivo2.csv?token=xyz789"
]
```

2. **Modificar código para ler secrets:**
```python
# No início do app.py
try:
    DATA_URLS = st.secrets["data"]["csv_urls"]
except:
    DATA_URLS = []
```

---

## 🎛️ Configurações Avançadas

### Cache para Performance

Adicione caching para evitar recarregar dados a cada interação:

```python
@st.cache_data(ttl=3600)  # Cache por 1 hora
def load_cached_data(urls):
    analyzer = PatrimonioAnalyzer()
    analyzer.load_data_from_url(urls)
    analyzer.preprocess_data()
    return analyzer.data
```

### Atualização Automática

Para dados que mudam frequentemente, configure refresh automático:

```python
# config.py
AUTO_LOAD = True
CACHE_DURATION = 1800  # 30 minutos
AUTO_REFRESH = True
```

---

## 🐛 Troubleshooting

### Problema: "FileNotFoundError: data/"
**Solução**: Certifique-se que a pasta `data/` está commitada no Git
```bash
git add data/
git commit -m "Adiciona pasta data"
```

### Problema: "403 Forbidden" ao carregar do Google Drive
**Solução**: Verifique se o arquivo está configurado como "Qualquer pessoa com o link"

### Problema: Dados não carregam automaticamente
**Solução**: Verifique se `AUTO_LOAD = True` no `config.py`

### Problema: Arquivos muito grandes (> 1GB)
**Solução**: 
- Use Google Drive ou serviço de cloud storage
- Considere comprimir os arquivos
- Divida em arquivos menores

### Problema: Encoding errado (caracteres estranhos)
**Solução**: O código já tenta utf-8 e latin-1 automaticamente. Se persistir:
```python
df = pd.read_csv(file, encoding='cp1252')  # Windows
# ou
df = pd.read_csv(file, encoding='iso-8859-1')  # Latin
```

---

## 📈 Melhores Práticas

### ✅ DO:
- Use URLs para arquivos grandes (>100MB)
- Configure cache adequado
- Mantenha dados separados do código
- Use `.gitignore` para arquivos locais grandes
- Documente as fontes dos dados

### ❌ DON'T:
- Não commite arquivos > 100MB no Git
- Não hardcode credenciais no código
- Não desabilite cache sem necessidade
- Não ignore tratamento de erros

---

## 🚦 Checklist de Deploy

- [ ] Escolher método de carregamento adequado
- [ ] Criar `requirements.txt` com todas dependências
- [ ] Testar localmente: `streamlit run app.py`
- [ ] Verificar encoding dos CSVs
- [ ] Configurar URLs ou pasta `data/`
- [ ] Fazer commit e push
- [ ] Conectar no Streamlit Cloud
- [ ] Testar carregamento automático
- [ ] Verificar logs de erro no dashboard
- [ ] Configurar cache apropriado

---

## 📞 Suporte

- **Streamlit Docs**: https://docs.streamlit.io
- **Community Forum**: https://discuss.streamlit.io
- **GitHub Issues**: Crie issue no seu repositório

---

## 🎓 Exemplo Completo

### Estrutura Final Recomendada:

```
patrimonio-app/
│
├── app.py                      # Aplicação principal
├── config.py                   # Configurações (URLs, etc)
├── requirements.txt            # Dependências Python
├── README.md                   # Documentação do projeto
├── DEPLOY_GUIDE.md            # Este guia
│
├── .gitignore                 # Ignorar arquivos desnecessários
│
└── data/                      # (Opcional) CSVs locais
    └── .gitkeep               # Manter pasta vazia no Git
```

### `.gitignore` sugerido:
```
# Python
__pycache__/
*.py[cod]
*$py.class
.Python

# Streamlit
.streamlit/

# Data (se usar URLs)
data/*.csv
!data/.gitkeep

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
```

---

## 🎉 Pronto!

Sua aplicação agora está configurada para carregar dados automaticamente no Streamlit Cloud!

**URL típica**: `https://usuario-patrimonio-app.streamlit.app`