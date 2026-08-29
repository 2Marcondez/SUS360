import subprocess
import sys

def run_step(script_name):
    print(f"🚀 Iniciando Step: {script_name}")

    result = subprocess.run([sys.executable, script_name])

    if result.returncode != 0:
        print(f"\n ERROR: O script {script_name} falhou. Interrompendo pipeline.")
        sys.exit(1)
    print(f"\n✅ STEP CONCLUÍDO: {script_name}")

if __name__ == "__main__":
    print("🏥 Iniciando Orquestrador - SUS360 🏥")

    # =====================================================================
    # CONTROLE DA PIPELINE
    # Comente com '#' a linha do step que você NÃO quer que rode.
    # =====================================================================
    run_step("data_extract.py")
    run_step("data_enrichment.py")
    run_step("data_clustering.py")
    run_step("data_to_oracle.py")
    run_step("streamlit run app.py")

    print("\n [✅] Pipeline Finalizada !")