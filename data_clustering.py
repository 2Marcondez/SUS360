import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# Load
df = pd.read_csv("dados/silver_hospital_2022_2025.csv")
df = df[df['total_leitos'] > 0].copy()

# Calcula a Taxa de Ocupação e limita os outliers extremos
df['taxa_ocupacao'] = (df['total_internacoes'] * df['permanencia_media_dias']) / (df['total_leitos'] * 30)
df['taxa_ocupacao'] = df['taxa_ocupacao'].clip(upper=2.0)

# Consolida o "Perfil Anual"
perfil_hospital = df.groupby(['id_estabelecimento_cnes', 'nome_fantasia']).agg({
    'total_leitos': 'max',                   
    'total_internacoes': 'mean',             
    'permanencia_media_dias': 'mean',        
    'taxa_ocupacao': 'mean'                  
}).reset_index()

features = ['total_leitos', 'total_internacoes', 'permanencia_media_dias', 'taxa_ocupacao']
X = perfil_hospital[features]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
perfil_hospital['Cluster'] = kmeans.fit_predict(X_scaled)

# =====================================================================
# RESUMO E DIAGNÓSTICO DOS CLUSTERS 
# =====================================================================
resumo = perfil_hospital.groupby('Cluster')[features].mean().round(2)
resumo['qtd_hospitais'] = perfil_hospital['Cluster'].value_counts()

print("\n" + "="*60)
print(" MÉDIAS REAIS DOS CLUSTERS ENCONTRADOS PELO K-MEANS ")
print("="*60)
print(resumo)
print("="*60 + "\n")

# # =====================================================================
# # MAPEAMENTO DINÂMICO COM DEBUG
# # =====================================================================
# print(" DUBUGGING:")

# # A. Clínicas
# id_clinica = resumo['permanencia_media_dias'].idxmin()
# print(f" -> CLÍNICA escolhida: Cluster {id_clinica} (Menor permanência: {resumo.loc[id_clinica, 'permanencia_media_dias']} dias)")
# restante = resumo.drop(id_clinica)

# # B. Baixa Ocupação
# id_baixa = restante['taxa_ocupacao'].idxmin()
# print(f" -> BAIXA OCUPAÇÃO escolhida: Cluster {id_baixa} (Menor taxa: {restante.loc[id_baixa, 'taxa_ocupacao'] * 100:.1f}%)")
# restante = restante.drop(id_baixa)

# # C. Sobrecarregado
# id_sobrecarregado = restante['taxa_ocupacao'].idxmax()
# print(f" -> SOBRECARREGADO escolhido: Cluster {id_sobrecarregado} (Maior taxa: {restante.loc[id_sobrecarregado, 'taxa_ocupacao'] * 100:.1f}%)")
# restante = restante.drop(id_sobrecarregado)

# # D. Alta Rotatividade
# id_alta_rotatividade = restante['permanencia_media_dias'].idxmin()
# print(f" -> ALTA ROTATIVIDADE escolhida: Cluster {id_alta_rotatividade} (Menor permanência dos que sobraram: {restante.loc[id_alta_rotatividade, 'permanencia_media_dias']} dias)")

# # E. Equilibrado
# id_equilibrado = restante.drop(id_alta_rotatividade).index[0]
# print(f" -> EQUILIBRADO escolhido: Cluster {id_equilibrado} (Foi o que sobrou no final)")

# =====================================================================
# MAPEAMENTO DEFINITIVO 
# =====================================================================
mapa_perfis = {
    0: "Baixa Ocupação",
    4: "Equilibrado",
    1: "Sobrecarregado",
    3: "Gargalo Crítico", 
    2: "Longa Permanência (Crônicos e Psiquiatria)" 
}

print("\n✅ MAPA FINAL:")
for k, v in mapa_perfis.items():
    print(f"Cluster {k} -> {v}")

# =====================================================================
# GERAÇÃO DA CAMADA GOLD
# =====================================================================
df_clusters = perfil_hospital[['id_estabelecimento_cnes', 'Cluster']]
df_gold = pd.merge(df, df_clusters, on='id_estabelecimento_cnes', how='left')

df_gold['Cluster'] = df_gold['Cluster'].map(mapa_perfis)

df_gold.to_csv("dados/gold_hospital_clusters_2022_2025.csv", index=False)
print("\n✅ Base Gold gerada com sucesso: dados/gold_hospital_clusters_2022_2025.csv")