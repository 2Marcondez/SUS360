import time
import requests
import pandas as pd

def enrich_with_cnes_api(df: pd.DataFrame) -> pd.DataFrame:
    unique_cnes = df['id_estabelecimento_cnes'].unique()
    print(f"Iniciando API para {len(unique_cnes)} estabelecimentos...")

    api_data = []

    with requests.Session() as session:
        for cnes in unique_cnes:
            url = f"https://apidadosabertos.saude.gov.br/cnes/estabelecimentos/{cnes}"
            try:
                time.sleep(0.01)
                response = session.get(url, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    
                    # Capturando as lat/longs
                    lat = data.get('latitude_estabelecimento_decimo_grau')
                    lon = data.get('longitude_estabelecimento_decimo_grau')
                    
                    api_data.append({
                        'id_estabelecimento_cnes': cnes,
                        'nome_fantasia': data.get('nome_fantasia', 'N/A'),
                        'descricao_esfera_administrativa': data.get('descricao_esfera_administrativa', 'N/A'),
                        'latitude': lat,
                        'longitude': lon
                    })
                else:
                    api_data.append({'id_estabelecimento_cnes': cnes, 'nome_fantasia': 'API ERROR'})

            except Exception as e:
                print(f"[!] Falha CNES {cnes}: {e}")
                api_data.append({'id_estabelecimento_cnes': cnes, 'nome_fantasia': 'TIMEOUT'})

    api_df = pd.DataFrame(api_data)

    df['id_estabelecimento_cnes'] = df['id_estabelecimento_cnes'].astype(str)
    api_df['id_estabelecimento_cnes'] = api_df['id_estabelecimento_cnes'].astype(str)

    enriched_df = pd.merge(df, api_df, on='id_estabelecimento_cnes', how='left')
    
    def create_coordinate(row):
        lat = row['latitude']
        lon = row['longitude']
        
        if pd.notna(lat) and pd.notna(lon):
            return f"{lat},{lon}"
        
        return None

    enriched_df['coordinate'] = enriched_df.apply(create_coordinate, axis=1)

    return enriched_df

if __name__ == "__main__":
    input_path = "dados/bronze_hospital_2022_2025.csv"
    output_path = "dados/silver_hospital_2022_2025.csv"

    treated_df = pd.read_csv(input_path)

    final_df = enrich_with_cnes_api(treated_df)

    final_df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"\n[✓] Data Enrichment Concluído! Arquivo salvo em: {output_path}")