import os
import pandas as pd
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()
PROJECT_ID = os.getenv("PROJECT_ID")

def extract_hospital_data() -> pd.DataFrame:
    client = bigquery.Client(project=PROJECT_ID)
    sql = """
    WITH internacoes_resumo AS (
        SELECT 
            ano,
            EXTRACT(MONTH FROM data_entrada_internacao) AS mes,
            sigla_uf,
            id_estabelecimento_cnes,
            COUNT(DISTINCT id_aih) AS total_internacoes,
            AVG(DATE_DIFF(data_saida_iternacao, data_entrada_internacao, DAY)) AS permanencia_media_dias
        FROM `basedosdados.br_ms_sih.servicos_profissionais`
        WHERE ano BETWEEN 2022 AND 2025
            AND data_entrada_internacao IS NOT NULL 
            AND data_saida_iternacao IS NOT NULL
        GROUP BY ano, mes, sigla_uf, id_estabelecimento_cnes
    ),
    leitos_resumo AS (
        SELECT 
            ano,
            mes,
            sigla_uf,
            id_estabelecimento_cnes,
            SUM(quantidade_total) AS total_leitos
        FROM `basedosdados.br_ms_cnes.leito`
        WHERE ano BETWEEN 2022 AND 2025
        GROUP BY ano, mes, sigla_uf, id_estabelecimento_cnes
    )
    SELECT 
        i.ano,
        i.mes,
        i.sigla_uf,
        i.id_estabelecimento_cnes,
        i.total_internacoes,
        CAST(ROUND(i.permanencia_media_dias, 0) AS INT64) AS permanencia_media_dias,
        COALESCE(l.total_leitos, 0) AS total_leitos
    FROM internacoes_resumo i
    INNER JOIN leitos_resumo l 
        ON i.id_estabelecimento_cnes = l.id_estabelecimento_cnes
        AND i.ano = l.ano
        AND i.mes = l.mes
        AND i.sigla_uf = l.sigla_uf
    """
    print("Executando extração no BigQuery (2022-2025)...")
    return client.query(sql).to_dataframe()

def apply_basic_treatment(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df['permanencia_media_dias'] <= 150].copy()

    month_mapping = {
        1: 'Janeiro', 
        2: 'Fevereiro',
        3: 'Março', 
        4: 'Abril',
        5: 'Maio', 
        6: 'Junho', 
        7: 'Julho',
        8: 'Agosto',
        9: 'Setembro', 
        10: 'Outubro', 
        11: 'Novembro', 
        12: 'Dezembro'
    }
    df['mes'] = df['mes'].map(month_mapping)

    final_columns = [
        'ano', 
        'mes', 
        'sigla_uf', 
        'id_estabelecimento_cnes', 
        'total_internacoes', 
        'permanencia_media_dias', 
        'total_leitos'
    ]
    return df[final_columns]

if __name__ == "__main__":
    os.makedirs("dados", exist_ok=True)
    raw_df = extract_hospital_data()
    treated_df = apply_basic_treatment(raw_df)

    output_path = "dados/bronze_hospital_2022_2025.csv"
    treated_df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"\n[✓] Data Extract Concluído! Arquivo salvo em: {output_path}")