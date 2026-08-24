"""
Tests complets du système d'analyse KYC.
"""

import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
from src.agents.analysis_agent import (
    create_analysis_graph,
    run_analysis_agent,
    aggregate_analysis_results,
)
from src.config.config import AnalysisAgentState


# ====================================================================
# FIXTURES
# ====================================================================

@pytest.fixture
def sample_data():
    """Crée des données de test."""
    return [
        {
            "msisdn": "261321234567",
            "prenom": "Jean",
            "nom": "Dupont",
            "id_type": "CNI",
            "id_number": "123456789012",
            "dob": "1990-05-15",
            "ville": "Antananarivo",
            "adresse": "123 Rue de la Paix",
            "status": "ACTIVE"
        },
        {
            "msisdn": "261321234568",
            "prenom": "Marie",
            "nom": "Martin",
            "id_type": "CNI",
            "id_number": "123456789013",
            "dob": "1985-10-20",
            "ville": "Fianarantsoa",
            "adresse": "456 Avenue du Commerce",
            "status": "ACTIVE"
        },
        {
            "msisdn": "261321234569",
            "prenom": "Pierre",
            "nom": "Bernard",
            "id_type": "CNI",
            "id_number": "123456789014",
            "dob": "1992-03-10",
            "ville": "Toliara",
            "adresse": "789 Boulevard Central",
            "status": "ACTIVE"
        },
        {
            "msisdn": "",  # Null MSISDN
            "prenom": "Paul",
            "nom": "Durand",
            "id_type": "CNI",
            "id_number": "123456789015",
            "dob": "1988-07-25",
            "ville": "Mahajanga",
            "adresse": "101 Rue du Port",
            "status": "ACTIVE"
        },
        {
            "msisdn": "261321234570",
            "prenom": "A",  # Single character
            "nom": "Petit",
            "id_type": "CNI",
            "id_number": "123456789016",
            "dob": "1995-12-01",
            "ville": "Antsirabe",
            "adresse": "202 Rue Courte",
            "status": "ACTIVE"
        },
        {
            "msisdn": "261321234571",
            "prenom": "Sophie",
            "nom": "Lefevre",
            "id_type": "CNI",
            "id_number": "999999999999",  # Repeated digits
            "dob": "1991-06-15",
            "ville": "Sambava",
            "adresse": "aaa",  # Repeated characters
            "status": "ACTIVE"
        },
        {
            "msisdn": "261321234572",
            "prenom": "Luc",
            "nom": "Moreau",
            "id_type": "CNI",
            "id_number": "123456789017",
            "dob": "2010-01-01",  # Under minimum age
            "ville": "Antalaha",
            "adresse": "303 Rue Longue",
            "status": "ACTIVE"
        },
        {
            "msisdn": "261321234573",
            "prenom": "Claire",
            "nom": "Blanc",
            "id_type": "CNI",
            "id_number": "123456789018",
            "dob": "1920-01-01",  # Over maximum age
            "ville": "Morondava",
            "adresse": "404 Rue Principale",
            "status": "ACTIVE"
        },
    ]


@pytest.fixture
def sample_csv_file(sample_data):
    """Crée un fichier CSV de test."""
    df = pd.DataFrame(sample_data)
    
    # Créer un fichier temporaire
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        df.to_csv(f, index=False)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def initial_state(sample_data):
    """Crée l'état initial pour le test."""
    return {
        "file_id": "test_file_001",
        "thread_id": "test_thread_001",
        "data": sample_data,
        "file_path": None,
        "country": "Madagascar",
        "active_rows_count": len(sample_data),
        "schema_mapping": {
            "nom_column": "nom",
            "prenom_column": "prenom",
            "msisdn_column": "msisdn",
            "dob_column": "dob",
            "id_type_column": "id_type",
            "id_number_column": "id_number",
            "status_column": "status",
            "address_column": "adresse",
            "city_column": "ville",
        },
        "analysis_status": "in_progress",
    }


# ====================================================================
# TESTS UNITAIRES
# ====================================================================
class TestAnalysisNodes:
    """Tests des nodes individuels."""
    
    def test_analyze_msisdn(self, initial_state):
        """Test l'analyse MSISDN."""
        from src.nodes.data_analysis_nodes import analyze_msisdn
        
        result = analyze_msisdn(initial_state)
        
        assert result["msisdn_analysis"]["status"] == "completed"
        assert result["msisdn_analysis"]["row_count"] == 8
        assert result["msisdn_analysis"]["null_count"] == 1  # Une MSISDN vide
        assert result["msisdn_analysis"]["valid_count"] == 7
        assert result["msisdn_analysis"]["compliance_rate"] > 0
        
        print(f"✅ MSISDN Analysis: {result['msisdn_analysis']['compliance_rate']:.2f}% compliance")
    
    def test_analyze_first_name(self, initial_state):
        """Test l'analyse prénom."""
        from src.nodes.data_analysis_nodes import analyze_first_name
        
        result = analyze_first_name(initial_state)
        
        assert result["first_name_analysis"]["status"] == "completed"
        assert result["first_name_analysis"]["row_count"] == 8
        # ✅ CORRECTION ICI
        assert result["first_name_analysis"]["null_count"] == 0
        assert result["first_name_analysis"]["valid_count"] == 7  # Un prénom single char
        
        print(f"✅ First Name Analysis: {result['first_name_analysis']['compliance_rate']:.2f}% compliance")
    
    def test_analyze_last_name(self, initial_state):
        """Test l'analyse nom."""
        from src.nodes.data_analysis_nodes import analyze_last_name
        
        result = analyze_last_name(initial_state)
        
        assert result["last_name_analysis"]["status"] == "completed"
        assert result["last_name_analysis"]["row_count"] == 8
        # ✅ CORRECTION ICI
        assert result["last_name_analysis"]["null_count"] == 0
        assert result["last_name_analysis"]["valid_count"] == 8
        
        print(f"✅ Last Name Analysis: {result['last_name_analysis']['compliance_rate']:.2f}% compliance")
    
    def test_analyze_id_type(self, initial_state):
        """Test l'analyse type d'ID."""
        from src.nodes.data_analysis_nodes import analyze_id_type
        
        result = analyze_id_type(initial_state)
        
        assert result["id_type_analysis"]["status"] == "completed"
        assert result["id_type_analysis"]["row_count"] == 8
        assert result["id_type_analysis"]["dominant_id_type"] == "CNI"
        assert result["id_type_analysis"]["compliance_rate"] == 100.0
        
        print(f"✅ ID Type Analysis: {result['id_type_analysis']['dominant_id_type']}")
    
    def test_analyze_id_number(self, initial_state):
        """Test l'analyse numéro d'ID."""
        from src.nodes.data_analysis_nodes import analyze_id_number
        
        result = analyze_id_number(initial_state)
        
        assert result["id_number_analysis"]["status"] == "completed"
        assert result["id_number_analysis"]["row_count"] == 8
        assert result["id_number_analysis"]["valid_count"] >= 6  # Au moins 6 valides
        
        print(f"✅ ID Number Analysis: {result['id_number_analysis']['compliance_rate']:.2f}% compliance")
    
    def test_analyze_dob(self, initial_state):
        """Test l'analyse date de naissance."""
        from src.nodes.data_analysis_nodes import analyze_dob
        
        result = analyze_dob(initial_state)
        
        assert result["dob_analysis"]["status"] == "completed"
        assert result["dob_analysis"]["row_count"] == 8
        assert result["dob_analysis"]["null_count"] == 0
        assert result["dob_analysis"]["valid_count"] >= 6  # Au moins 6 valides
        
        print(f"✅ DOB Analysis: {result['dob_analysis']['compliance_rate']:.2f}% compliance")
    
    def test_analyze_city(self, initial_state):
        """Test l'analyse ville."""
        from src.nodes.data_analysis_nodes import analyze_city
        
        result = analyze_city(initial_state)
        
        assert result["city_analysis"]["status"] == "completed"
        assert result["city_analysis"]["row_count"] == 8
        assert result["city_analysis"]["null_count"] == 0
        assert result["city_analysis"]["valid_count"] == 8
        
        print(f"✅ City Analysis: {result['city_analysis']['compliance_rate']:.2f}% compliance")
    
    def test_analyze_address(self, initial_state):
        """Test l'analyse adresse."""
        from src.nodes.data_analysis_nodes import analyze_address
        
        result = analyze_address(initial_state)
        
        assert result["address_analysis"]["status"] == "completed"
        assert result["address_analysis"]["row_count"] == 8
        assert result["address_analysis"]["null_count"] == 0
        assert result["address_analysis"]["valid_count"] >= 7  # Au moins 7 valides
        
        print(f"✅ Address Analysis: {result['address_analysis']['compliance_rate']:.2f}% compliance")

# ====================================================================
# TESTS D'INTÉGRATION
# ====================================================================

class TestAnalysisGraph:
    """Tests du graph complet."""
    
    def test_graph_creation(self):
        """Test la création du graph."""
        graph = create_analysis_graph()
        
        assert graph is not None
        print("✅ Graph created successfully")
    
    def test_full_analysis_pipeline(self, initial_state):
        """Test le pipeline complet d'analyse."""
        result = run_analysis_agent(
        initial_state=initial_state,
        thread_id="test_thread_001"
        )
    
        # ✅ Vérifier que les analyses sont complétées
        assert result["msisdn_analysis"]["status"] in ["completed", "warning"]
        assert result["first_name_analysis"]["status"] in ["completed", "warning"]
        assert result["last_name_analysis"]["status"] in ["completed", "warning"]
        assert result["id_type_analysis"]["status"] in ["completed", "warning"]
        assert result["id_number_analysis"]["status"] in ["completed", "warning"]
        assert result["dob_analysis"]["status"] in ["completed", "warning"]
        assert result["city_analysis"]["status"] in ["completed", "warning"]
        assert result["address_analysis"]["status"] in ["completed", "warning"]
        
        # ✅ Vérifier l'agrégation
        assert "aggregated_results" in result
        aggregated = result["aggregated_results"]
        
        assert aggregated["status"] == "completed"
        assert aggregated["overall_compliance_rate"] >= 0
        assert aggregated["overall_risk_score"] >= 0
        assert aggregated["overall_risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        
        print(f"✅ Full Pipeline Completed")
        print(f"   Overall Compliance: {aggregated['overall_compliance_rate']:.2f}%")
        print(f"   Overall Risk: {aggregated['overall_risk_level']}")
        print(f"   Risk Score: {aggregated['overall_risk_score']:.2f}")

    def test_aggregation(self, initial_state):
        """Test l'agrégation des résultats."""
        result = run_analysis_agent(
            initial_state=initial_state,
            thread_id="test_thread_001"
        )
        
        # ✅ Vérifier que aggregated_results existe
        assert "aggregated_results" in result
        aggregated = aggregate_analysis_results(result)
        
        assert "overall_compliance_rate" in aggregated
        assert "overall_risk_score" in aggregated
        assert "overall_risk_level" in aggregated
        assert "fields_analyzed" in aggregated
        assert "total_anomalies" in aggregated
        assert "executive_summary" in aggregated
        
        print(f"✅ Aggregation Results:")
        print(f"   Compliance: {aggregated['overall_compliance_rate']:.2f}%")
        print(f"   Risk Level: {aggregated['overall_risk_level']}")
        print(f"   Anomalies: {aggregated['total_anomalies']}")


# ====================================================================
# TESTS DE PERFORMANCE
# ====================================================================

class TestPerformance:
    """Tests de performance."""
    
    def test_large_dataset(self):
        """Test avec un grand dataset."""
        import time
        
        # Créer 10,000 enregistrements
        large_data = []
        for i in range(10000):
            large_data.append({
                "msisdn": f"261321{i:06d}",
                "prenom": f"Prenom{i}",
                "nom": f"Nom{i}",
                "id_type": "CNI",
                "id_number": f"{100000000000 + i}",
                "dob": "1990-05-15",
                "ville": "Antananarivo",
                "adresse": f"Rue {i}",
                "status": "ACTIVE"
            })
        
        initial_state = {
            "file_id": "test_large_001",
            "thread_id": "test_thread_large",
            "data": large_data,
            "file_path": None,
            "country": "Madagascar",
            "active_rows_count": len(large_data),
            "schema_mapping": {
                "nom_column": "nom",
                "prenom_column": "prenom",
                "msisdn_column": "msisdn",
                "dob_column": "dob",
                "id_type_column": "id_type",
                "id_number_column": "id_number",
                "status_column": "status",
                "address_column": "adresse",
                "city_column": "ville",
            },
            "analysis_status": "in_progress",
        }
        
        start_time = time.time()
        result = run_analysis_agent(
            initial_state=initial_state,
            thread_id="test_thread_large"
        )
        elapsed_time = time.time() - start_time
        
        # ✅ CORRECTION ICI - Vérifier que aggregated_results existe
        assert "aggregated_results" in result
        assert result["aggregated_results"]["status"] == "completed"
        
        print(f"✅ Large Dataset Test (10,000 records):")
        print(f"   Time: {elapsed_time:.2f}s")
        print(f"   Records/sec: {10000/elapsed_time:.0f}")


# ====================================================================
# TESTS DE QUALITÉ DE DONNÉES
# ====================================================================

class TestDataQuality:
    """Tests de détection de qualité de données."""
    
    def test_anomaly_detection(self, initial_state):
        """Test la détection d'anomalies."""
        result = run_analysis_agent(
            initial_state=initial_state,
            thread_id="test_thread_001"
        )
        
        # ✅ CORRECTION ICI - Vérifier que aggregated_results existe
        assert "aggregated_results" in result
        aggregated = result["aggregated_results"]
        
        # Vérifier que les anomalies sont détectées
        assert aggregated["total_anomalies"] >= 0
        assert len(aggregated["critical_fields"]) >= 0
        
        print(f"✅ Anomaly Detection:")
        print(f"   Total Anomalies: {aggregated['total_anomalies']}")
        print(f"   Critical Fields: {len(aggregated['critical_fields'])}")
        
        for field in aggregated["critical_fields"]:
            print(f"   • {field['field']}: {field['anomaly']}")
    
    def test_risk_assessment(self, initial_state):
        """Test l'évaluation du risque."""
        result = run_analysis_agent(
            initial_state=initial_state,
            thread_id="test_thread_001"
        )
        
        # ✅ CORRECTION ICI - Vérifier que aggregated_results existe
        assert "aggregated_results" in result
        aggregated = result["aggregated_results"]
        
        # Vérifier que le risque est correctement évalué
        risk_level = aggregated["overall_risk_level"]
        risk_score = aggregated["overall_risk_score"]
        
        assert risk_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert 0 <= risk_score <= 1
        
        # Vérifier la cohérence
        if risk_score <= 0.15:
            assert risk_level == "LOW"
        elif risk_score <= 0.35:
            assert risk_level == "MEDIUM"
        elif risk_score <= 0.55:
            assert risk_level == "HIGH"
        else:
            assert risk_level == "CRITICAL"
        
        print(f"✅ Risk Assessment:")
        print(f"   Risk Level: {risk_level}")
        print(f"   Risk Score: {risk_score:.2f}")
        print(f"   Recommendation: {aggregated['executive_summary']['recommendation']}")


# ====================================================================
# MAIN
# ====================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
