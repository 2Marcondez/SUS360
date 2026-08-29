import os
import pandas as pd
import oracledb
import sqlalchemy 
from sqlalchemy import create_engine
from dotenv import load_dotenv

# =====================================================================
# 1. SUAS CREDENCIAIS DO AUTONOMOUS DATABASE
# =====================================================================

load_dotenv()

USER = os.getenv("USER")
PW = os.getenv("PW")
DSN = os.getenv("DSN")
WALLET = os.getenv("WALLET")

# Caminho dinâmico e absoluto da Wallet
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
caminho_wallet = os.path.join(diretorio_atual, "wallet_cloud")

# =====================================================================
# 2. CONFIGURANDO O MOTOR 
# =====================================================================
def get_connection():
    return oracledb.connect(
        user=USER,
        password=PW,
        dsn=DSN,
        config_dir=caminho_wallet,
        wallet_location=caminho_wallet,
        wallet_password=WALLET
    )

print("Conectando ao banco de dados Oracle...")
engine = create_engine('oracle+oracledb://', creator=get_connection)

# =====================================================================
# 3. LOAD
# =====================================================================
arquivos = {
    "bronze_hospital": "bronze_hospital_2022_2025.csv",
    "silver_hospital": "silver_hospital_2022_2025.csv",
    "gold_hospital": "gold_hospital_clusters_2022_2025.csv"
}

print("Iniciando a ingestão\n")

for nome_tabela, nome_arquivo in arquivos.items():
    caminho_dados = os.path.join(diretorio_atual, "dados", nome_arquivo)
    
    print(f"Lendo o arquivo local: {nome_arquivo}...")
    df = pd.read_csv(caminho_dados)
    
    tipos_dinamicos = {
        coluna: sqlalchemy.types.Numeric(precision=18, scale=8) 
        for coluna, tipo in df.dtypes.items() if 'float' in str(tipo).lower()
    }
    
    print(f"Enviando {len(df)} registros para a tabela {nome_tabela}...")
    df.to_sql(
        name=nome_tabela,
        con=engine,
        if_exists='replace',
        index=False,
        dtype=tipos_dinamicos 
    )
    print(f"✅ Tabela {nome_tabela} carregada com sucesso!\n")

print("Todas as camadas já estão na Oracle!")