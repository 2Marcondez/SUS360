# 🏥 SUS360 - Plataforma de Pressão Hospitalar e Clusterização

Este repositório contém a arquitetura completa de **Engenharia de Dados, Machine Learning e Visualização** do projeto **SUS360**, desenvolvido para o Challenge FIAP + Oracle.

Através da extração de dados públicos, cruzamento com APIs do CNES, persistência no **Oracle Autonomous Database** e aplicação de algoritmos de Clusterização (Scikit-Learn), o sistema classifica automaticamente o perfil operacional de cada hospital e a calcula a pressão hospitalar, visando apoiar a tomada de decisão estratégica das Secretarias de Saúde.

---

## 🚀 Tecnologias Utilizadas

| Tecnologia | Função |
|---|---|
| **Oracle Autonomous Database** | Banco de dados relacional em nuvem utilizado para persistência segura das camadas |
| **Python (Pandas)** | Orquestração do pipeline de ETL, tratamentos, requests na API do CNES, carga no banco de dados Oracle |
| **Scikit-Learn** | Framework de Machine Learning utilizado para o escalonamento numérico (`StandardScaler`) e treinamento do modelo de agrupamento (`K-Means`) |
| **Streamlit & Plotly** | Front-end e visualização, responsáveis por renderizar o dashboard |

---

## 🏛️ Arquitetura de Dados 

O fluxo de dados foi estruturado utilizando a **Arquitetura Medalhão**, garantindo governança, performance e escalabilidade:

### 🥉 Camada Bronze — `data_extract.py`
Ingestão bruta dos dados diretamente das fontes, mantendo a fidelidade original.

### 🥈 Camada Silver — `data_enrichment.py`
Limpeza de anomalias (outliers) e enriquecimento via consumo da API REST do CNES, adicionando coordenadas geográficas (Lat/Lon), nome fantasia e esfera administrativa.

### 🥇 Camada Gold — `data_clustering.py` & `data_to_oracle.py`
Tabela analítica definitiva agregada na granularidade de hospital/mês, enriquecida com os rótulos de clusterização e persistida no Oracle Database.

---

## 🤖 Clusterização 

Para evitar a comparação imprecisa entre UPAs de rotatividade diária e hospitais de alta complexidade, o SUS360 aplica o algoritmo **K-Means** operando em quatro etapas:

1. **Engenharia de Features**
   Agregação anual de quatro variáveis-chave por hospital: `total_leitos`, `total_internacoes`, `permanencia_media_dias` e `taxa_ocupacao`.

2. **Padronização Escalar**
   Como as métricas possuem grandezas numéricas distantes, aplicamos o `StandardScaler` para normalizar as distribuições, garantindo que o algoritmo calcule as distâncias corretamente.

3. **Descoberta de Centróides**
   O modelo matematicamente divide os estabelecimentos em **5 perfis operacionais**:

   | Perfil | Descrição |
   |---|---|
   | **Baixa Ocupação** | Capacidade ociosa, atuando como "válvula de escape" para a rede |
   | **Equilibrado** | Hospitais com gestão eficiente que operam dentro do limite seguro |
   | **Sobrecarregado** | Unidades operando acima da capacidade, exigindo atenção gerencial |
   | **Gargalo Crítico (Gigantes)** | Maiores complexos hospitalares, com alto volume, tratamentos complexos e superlotação estrutural |
   | **Longa Permanência (Crônicos e Psiquiatria)** | Clínicas com permanência mais longas, reabilitação ou tratamento de crônicos |

4. **Diagnóstico de Anomalias**
   O modelo validou sua eficácia matemática ao isolar automaticamente um cluster de **Longa Permanência** (média > 60 dias).

---

## ⚙️ Como Configurar e Executar (Setup)

### 1. Autenticação

O pipeline extrai dados primários do BigQuery e no fim da pipeline os envia para a Oracle.

```bash
# Instale o Google Cloud CLI e rode o comando abaixo:

gcloud auth application-default login

#Crie um arquivo .env e coloque suas credenciais

# Google Cloud
PROJECT_ID=" "

# Oracle Database (Mapeado para o futuro)
USER = " "
PW = " "
DSN = " "
WALLET = " "
```

### 2. Instalação de Dependências

Certifique-se de ter o Python instalado e instale as bibliotecas necessárias:

```bash
pip install pandas sqlalchemy oracledb requests scikit-learn plotly streamlit python-dotenv
```

### 3. Execução da Esteira (Pipeline)

Para processar os dados e iniciar o dashboard, execute os scripts:

```bash
python data_extract.py       # Extração da base Bronze
python data_enrichment.py    # Tratamento e base Silver (Enriquecida)
python data_clustering.py    # Clusterização e base Gold
python data_to_oracle.py     # Carga dos dados tratados no Oracle Database

#Ou é possivel rodar a pipeline por completo
python run_pipeline.py 
```
### 4. Execução do Dashboard 

```bash
streamlit run app.py         # Inicia o Dashboard SUS360
```
---

## 📊 Dicionário de Dados (Camada Gold)

O arquivo final `gold_hospital_clusters_2022_2025.csv`, consumido diretamente pelo dashboard, possui a seguinte estrutura:

| Coluna | Descrição |
|---|---|
| `ano` / `mes` | Período de competência da internação |
| `sigla_uf` | Estado do estabelecimento (SP, RJ, MG) |
| `nome_fantasia` | Nome oficial da unidade de saúde (API CNES) |
| `id_estabelecimento_cnes` | Chave primária do hospital no cadastro do MS |
| `latitude` / `longitude` | Coordenadas Y/X para o mapa de pressão espacial |
| `total_internacoes` | Quantidade de Autorizações de Internação Hospitalar (AIH) |
| `total_leitos` | Total de leitos físicos ativos no mês |
| `permanencia_media_dias` | Média de dias que o paciente ocupou o leito |
| `descricao_esfera_administrativa` | Natureza da gestão (Estadual, Municipal, Privada, etc.) |
| `taxa_ocupacao` | KPI calculado: `(Internações x Permanência) / (Leitos x 30)` |
| `Cluster` | Tradução executiva do Cluster baseada no comportamento matemático |

---

## 🔮 Roadmap e Próximos Passos 

A evolução arquitetural mapeada para o projeto envolve a construção de um **Drill-Down Diagnóstico (Nível Procedimento)**.

Atualmente, o grão da base Gold está consolidado por **Hospital/Mês** para viabilizar a predição macro. A próxima versão da pipeline fará a ingestão da variável `id_procedimento_principal` no BigQuery, cruzando-a com o dicionário de dados (Tabela SUS).

Isso permitirá que a Secretaria de Saúde selecione um **"Gargalo Crítico"** no mapa e visualize exatamente qual doença ou procedimento está motivando o colapso e a alta permanência daquela unidade.