"""
Script pour corriger automatiquement les nodes.
"""

import re
from pathlib import Path

def fix_analyze_msisdn():
    """Corrige le début de analyze_msisdn."""
    file_path = Path("src/nodes/data_analysis_nodes.py")
    content = file_path.read_text()
    
    # Pattern à chercher
    pattern = r"(def analyze_msisdn\(state: AnalysisAgentState\).*?print\(f\"✓ Active rows:)"
    
    # Vérifier si la correction est déjà faite
    if "active_rows_count = state.get" in content:
        print("✅ analyze_msisdn déjà corrigé")
        return
    
    # Trouver la position
    match = re.search(r"def analyze_msisdn\(state: AnalysisAgentState\)", content)
    if match:
        print("✅ analyze_msisdn trouvé - correction manuelle requise")
        print("   Ajouter au début de la fonction:")
        print("   active_rows_count = state.get('active_rows_count', 0)")
        print("   if active_rows_count == 0 and data:")
        print("       active_rows_count = len(data)")
        print("       state['active_rows_count'] = active_rows_count")


def fix_first_last_name():
    """Corrige les clés manquantes dans first_name et last_name."""
    file_path = Path("src/nodes/data_analysis_nodes.py")
    content = file_path.read_text()
    
    # Chercher les deux fonctions
    for func_name in ["analyze_first_name", "analyze_last_name"]:
        if f"def {func_name}" in content:
            # Vérifier si null_count est présent
            if f'"{func_name}"' in content and '"null_count"' not in content:
                print(f"⚠️ {func_name} - null_count manquant")
                print(f"   Ajouter dans le dictionnaire analysis_result:")
                print(f'   "null_count": null_count,')
                print(f'   "non_null_count": non_null_count,')
            else:
                print(f"✅ {func_name} - OK")


if __name__ == "__main__":
    print("🔧 Vérification des corrections nécessaires...\n")
    fix_analyze_msisdn()
    print()
    fix_first_last_name()
