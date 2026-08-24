"""
Agent d'analyse KYC utilisant LangGraph pour orchestrer les nodes d'analyse.
"""

from langgraph.graph import StateGraph, END
from src.config.config import AnalysisAgentState
from src.nodes.data_analysis_nodes import (
    analyze_msisdn,
    analyze_first_name,
    analyze_last_name,
    analyze_id_type,
    analyze_id_number,
    analyze_dob,
    analyze_city,
    analyze_address,
)
from typing import Dict, Any, List


def create_analysis_graph():
    """
    Crée le graph d'analyse KYC avec tous les nodes.
    
    Returns:
        Compiled graph
    """
    
    # Créer le graph
    workflow = StateGraph(AnalysisAgentState)
    
    # ====================================================================
    # AJOUTER LES NODES
    # ====================================================================
    
    workflow.add_node("analyze_msisdn", analyze_msisdn)
    workflow.add_node("analyze_first_name", analyze_first_name)
    workflow.add_node("analyze_last_name", analyze_last_name)
    workflow.add_node("analyze_id_type", analyze_id_type)
    workflow.add_node("analyze_id_number", analyze_id_number)
    workflow.add_node("analyze_dob", analyze_dob)
    workflow.add_node("analyze_city", analyze_city)
    workflow.add_node("analyze_address", analyze_address)  # ✅ Dernier node (inclut agrégation)
    
    # ====================================================================
    # DÉFINIR LES EDGES (CONNEXIONS)
    # ====================================================================
    
    # Point d'entrée
    workflow.set_entry_point("analyze_msisdn")
    
    # Chaîne d'exécution séquentielle
    workflow.add_edge("analyze_msisdn", "analyze_first_name")
    workflow.add_edge("analyze_first_name", "analyze_last_name")
    workflow.add_edge("analyze_last_name", "analyze_id_type")
    workflow.add_edge("analyze_id_type", "analyze_id_number")
    workflow.add_edge("analyze_id_number", "analyze_dob")
    workflow.add_edge("analyze_dob", "analyze_city")
    workflow.add_edge("analyze_city", "analyze_address")
    
    # Point de sortie
    workflow.add_edge("analyze_address", END)  # ✅ Directement à END
    
    # Compiler le graph
    return workflow.compile()


def aggregate_results_node(state: AnalysisAgentState) -> AnalysisAgentState:
    """
    Node final qui agrège tous les résultats d'analyse.
    
    Args:
        state: État avec tous les résultats d'analyse
        
    Returns:
        État mis à jour avec résultats agrégés
    """
    
    print("\n" + "=" * 60)
    print("📊 AGGREGATING ANALYSIS RESULTS")
    print("=" * 60)
    
    try:
        # Récupérer tous les résultats
        analyses = {
            "msisdn": state.get("msisdn_analysis", {}),
            "first_name": state.get("first_name_analysis", {}),
            "last_name": state.get("last_name_analysis", {}),
            "id_type": state.get("id_type_analysis", {}),
            "id_number": state.get("id_number_analysis", {}),
            "dob": state.get("dob_analysis", {}),
            "city": state.get("city_analysis", {}),
            "address": state.get("address_analysis", {}),
        }

        # ✅ DEBUG: Vérifier les analyses
        print(f"\n📊 Analyses found:")
        for field, analysis in analyses.items():
            status = analysis.get("status", "MISSING")
            print(f"   • {field}: {status}")
        
        # ====================================================================
        # CALCULER LES SCORES GLOBAUX
        # ====================================================================
        
        print(f"\n📊 Calculating global scores...")
        
        # Collecter les compliance rates
        compliance_rates = []
        risk_scores = []
        anomalies_count = 0
        
        for field, analysis in analyses.items():
            if analysis.get("status") == "completed":
                compliance = analysis.get("compliance_rate", 0)
                risk = analysis.get("risk_score", 0)
                anomalies = len(analysis.get("anomalies", []))
                
                compliance_rates.append(compliance)
                risk_scores.append(risk)
                anomalies_count += anomalies
                
                print(f"   • {field}: {compliance:.2f}% compliance, {risk} risk")
        
        # Moyenne des compliance rates
        if compliance_rates:
            overall_compliance_rate = sum(compliance_rates) / len(compliance_rates)
        else:
            overall_compliance_rate = 0.0
        
        # Moyenne des risk scores
        if risk_scores:
            overall_risk_score = sum(risk_scores) / len(risk_scores)
        else:
            overall_risk_score = 0.0
        
        # ====================================================================
        # DÉTERMINER LE NIVEAU DE RISQUE GLOBAL
        # ====================================================================
        
        if overall_risk_score <= 0.15:
            overall_risk_level = "LOW"
        elif overall_risk_score <= 0.35:
            overall_risk_level = "MEDIUM"
        elif overall_risk_score <= 0.55:
            overall_risk_level = "HIGH"
        else:
            overall_risk_level = "CRITICAL"
        
        # ====================================================================
        # COLLECTER TOUTES LES ANOMALIES
        # ====================================================================
        
        print(f"\n📊 Collecting anomalies...")
        
        all_anomalies = {}
        for field, analysis in analyses.items():
            if analysis.get("status") == "completed":
                anomalies = analysis.get("anomalies", [])
                if anomalies:
                    all_anomalies[field] = anomalies
                    print(f"   • {field}: {len(anomalies)} anomalies")
        
        # ====================================================================
        # CRÉER LE RÉSUMÉ EXÉCUTIF
        # ====================================================================
        
        print(f"\n📊 Creating executive summary...")
        
        # Compter les champs complétés vs skippés
        completed_fields = sum(1 for a in analyses.values() if a.get("status") == "completed")
        skipped_fields = sum(1 for a in analyses.values() if a.get("status") == "skipped")
        error_fields = sum(1 for a in analyses.values() if a.get("status") == "error")
        
        # Identifier les champs critiques
        critical_fields = []
        for field, analysis in analyses.items():
            if analysis.get("status") == "completed":
                anomalies = analysis.get("anomalies", [])
                for anomaly in anomalies:
                    if anomaly.get("severity") == "high":
                        critical_fields.append({
                            "field": field,
                            "anomaly": anomaly.get("type"),
                            "count": anomaly.get("count"),
                            "percentage": anomaly.get("percentage")
                        })
        
        # ====================================================================
        # CONSTRUIRE LE RÉSULTAT AGRÉGÉ
        # ====================================================================
        
        aggregated_result = {
            "status": "completed",
            "file_id": state.get("file_id"),
            "thread_id": state.get("thread_id"),
            "country": state.get("country"),
            "active_rows_count": state.get("active_rows_count"),
            
            # Scores globaux
            "overall_compliance_rate": round(overall_compliance_rate, 2),
            "overall_risk_score": round(overall_risk_score, 2),
            "overall_risk_level": overall_risk_level,
            
            # Comptages
            "fields_analyzed": {
                "completed": completed_fields,
                "skipped": skipped_fields,
                "errors": error_fields,
                "total": len(analyses)
            },
            
            # Anomalies
            "total_anomalies": anomalies_count,
            "anomalies_by_field": all_anomalies,
            "critical_fields": critical_fields,
            
            # Résultats détaillés
            "detailed_results": analyses,
            
            # Résumé exécutif
            "executive_summary": {
                "overall_data_quality": "EXCELLENT" if overall_compliance_rate >= 95 else 
                                       "GOOD" if overall_compliance_rate >= 90 else
                                       "FAIR" if overall_compliance_rate >= 80 else
                                       "POOR",
                "risk_assessment": overall_risk_level,
                "fields_with_issues": len(all_anomalies),
                "critical_issues": len(critical_fields),
                "recommendation": get_recommendation(overall_risk_level, critical_fields)
            }
        }
        
        state["aggregated_results"] = aggregated_result
        state["analysis_status"] = "completed"
        
        print(f"\n✅ Aggregation Complete")
        print(f"   Overall Compliance: {overall_compliance_rate:.2f}%")
        print(f"   Overall Risk: {overall_risk_level}")
        print(f"   Risk Score: {overall_risk_score:.2f}")
        print(f"   Anomalies: {anomalies_count}")
        print(f"   Critical Fields: {len(critical_fields)}")
        print("=" * 60)
        
        return state
        
    except Exception as e:
        print(f"\n✗ Error during aggregation: {str(e)}")
        import traceback
        traceback.print_exc()
        
        state["analysis_status"] = "error"
        state["analysis_error"] = str(e)
        state["aggregated_results"] = {
            "status": "error",
            "error": str(e)
        }
        
        print("=" * 60)
        return state


def get_recommendation(risk_level: str, critical_fields: List[Dict[str, Any]]) -> str:
    """
    Génère une recommandation basée sur le niveau de risque.
    
    Args:
        risk_level: Niveau de risque global
        critical_fields: Champs avec anomalies critiques
        
    Returns:
        Recommandation texte
    """
    
    if risk_level == "CRITICAL":
        return "⛔ CRITICAL: Reject this dataset. Multiple critical issues detected. Manual review required."
    elif risk_level == "HIGH":
        return "⚠️ HIGH RISK: Review required. Address critical issues before processing."
    elif risk_level == "MEDIUM":
        return "⚡ MEDIUM RISK: Proceed with caution. Monitor identified issues."
    else:
        return "✅ LOW RISK: Dataset appears clean. Proceed with normal processing."


def run_analysis_agent(initial_state: AnalysisAgentState, thread_id: str) -> Dict[str, Any]:
    """
    Lance l'agent d'analyse KYC.
    
    Args:
        initial_state: État initial avec données
        thread_id: ID du thread pour tracking
        
    Returns:
        Résultats d'analyse
    """
    
    print("\n" + "=" * 80)
    print("🚀 STARTING KYC ANALYSIS AGENT")
    print("=" * 80)
    print(f"Thread ID: {thread_id}")
    print(f"Country: {initial_state.get('country')}")
    print(f"Active Rows: {initial_state.get('active_rows_count'):,}")
    print("=" * 80)
    
    # Créer le graph
    graph = create_analysis_graph()
    
    # Exécuter le graph
    result = graph.invoke(initial_state)
    
    print("\n" + "=" * 80)
    print("✅ KYC ANALYSIS AGENT COMPLETED")
    print("=" * 80)
    
    # ✅ POST-TRAITEMENT : Ajouter l'agrégation si elle n'existe pas
    if "aggregated_results" not in result:
        print("\n📊 POST-PROCESSING: Aggregating results...")
        result["aggregated_results"] = _aggregate_results(result)
    
    return result


def _aggregate_results(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agrège les résultats d'analyse.
    
    Args:
        state: État avec tous les résultats d'analyse
        
    Returns:
        Résultats agrégés
    """
    
    try:
        # Récupérer tous les résultats
        analyses = {
            "msisdn": state.get("msisdn_analysis", {}),
            "first_name": state.get("first_name_analysis", {}),
            "last_name": state.get("last_name_analysis", {}),
            "id_type": state.get("id_type_analysis", {}),
            "id_number": state.get("id_number_analysis", {}),
            "dob": state.get("dob_analysis", {}),
            "city": state.get("city_analysis", {}),
            "address": state.get("address_analysis", {}),
        }
        
        # ====================================================================
        # CALCULER LES SCORES GLOBAUX
        # ====================================================================
        
        print(f"\n📊 Calculating global scores...")
        
        # Collecter les compliance rates
        compliance_rates = []
        risk_scores = []
        anomalies_count = 0
        
        for field, analysis in analyses.items():
            if analysis.get("status") == "completed":
                compliance = analysis.get("compliance_rate", 0)
                risk = analysis.get("risk_score", 0)
                anomalies = len(analysis.get("anomalies", []))
                
                compliance_rates.append(compliance)
                risk_scores.append(risk)
                anomalies_count += anomalies
                
                print(f"   • {field}: {compliance:.2f}% compliance, {risk} risk")
        
        # Moyenne des compliance rates
        if compliance_rates:
            overall_compliance_rate = sum(compliance_rates) / len(compliance_rates)
        else:
            overall_compliance_rate = 0.0
        
        # Moyenne des risk scores
        if risk_scores:
            overall_risk_score = sum(risk_scores) / len(risk_scores)
        else:
            overall_risk_score = 0.0
        
        # ====================================================================
        # DÉTERMINER LE NIVEAU DE RISQUE GLOBAL
        # ====================================================================
        
        if overall_risk_score <= 0.15:
            overall_risk_level = "LOW"
        elif overall_risk_score <= 0.35:
            overall_risk_level = "MEDIUM"
        elif overall_risk_score <= 0.55:
            overall_risk_level = "HIGH"
        else:
            overall_risk_level = "CRITICAL"
        
        # ====================================================================
        # COLLECTER TOUTES LES ANOMALIES
        # ====================================================================
        
        print(f"\n📊 Collecting anomalies...")
        
        all_anomalies = {}
        for field, analysis in analyses.items():
            if analysis.get("status") == "completed":
                anomalies = analysis.get("anomalies", [])
                if anomalies:
                    all_anomalies[field] = anomalies
                    print(f"   • {field}: {len(anomalies)} anomalies")
        
        # ====================================================================
        # CRÉER LE RÉSUMÉ EXÉCUTIF
        # ====================================================================
        
        print(f"\n📊 Creating executive summary...")
        
        # Compter les champs complétés vs skippés
        completed_fields = sum(1 for a in analyses.values() if a.get("status") == "completed")
        skipped_fields = sum(1 for a in analyses.values() if a.get("status") == "skipped")
        error_fields = sum(1 for a in analyses.values() if a.get("status") == "error")
        
        # Identifier les champs critiques
        critical_fields = []
        for field, analysis in analyses.items():
            if analysis.get("status") == "completed":
                anomalies = analysis.get("anomalies", [])
                for anomaly in anomalies:
                    if anomaly.get("severity") == "high":
                        critical_fields.append({
                            "field": field,
                            "anomaly": anomaly.get("type"),
                            "count": anomaly.get("count"),
                            "percentage": anomaly.get("percentage")
                        })
        
        # ====================================================================
        # CONSTRUIRE LE RÉSULTAT AGRÉGÉ
        # ====================================================================
        
        aggregated_result = {
            "status": "completed",
            "file_id": state.get("file_id"),
            "thread_id": state.get("thread_id"),
            "country": state.get("country"),
            "active_rows_count": state.get("active_rows_count"),
            
            # Scores globaux
            "overall_compliance_rate": round(overall_compliance_rate, 2),
            "overall_risk_score": round(overall_risk_score, 2),
            "overall_risk_level": overall_risk_level,
            
            # Comptages
            "fields_analyzed": {
                "completed": completed_fields,
                "skipped": skipped_fields,
                "errors": error_fields,
                "total": len(analyses)
            },
            
            # Anomalies
            "total_anomalies": anomalies_count,
            "anomalies_by_field": all_anomalies,
            "critical_fields": critical_fields,
            
            # Résultats détaillés
            "detailed_results": analyses,
            
            # Résumé exécutif
            "executive_summary": {
                "overall_data_quality": "EXCELLENT" if overall_compliance_rate >= 95 else 
                                       "GOOD" if overall_compliance_rate >= 90 else
                                       "FAIR" if overall_compliance_rate >= 80 else
                                       "POOR",
                "risk_assessment": overall_risk_level,
                "fields_with_issues": len(all_anomalies),
                "critical_issues": len(critical_fields),
                "recommendation": get_recommendation(overall_risk_level, critical_fields)
            }
        }
        
        print(f"\n✅ Aggregation Complete")
        print(f"   Overall Compliance: {overall_compliance_rate:.2f}%")
        print(f"   Overall Risk: {overall_risk_level}")
        print(f"   Risk Score: {overall_risk_score:.2f}")
        print(f"   Anomalies: {anomalies_count}")
        print(f"   Critical Fields: {len(critical_fields)}")
        print("=" * 60)
        
        return aggregated_result
        
    except Exception as e:
        print(f"\n✗ Error during aggregation: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "status": "error",
            "error": str(e)
        }



def aggregate_analysis_results(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrait les résultats agrégés du state final.
    
    Args:
        analysis_result: État final après exécution du graph
        
    Returns:
        Résultats agrégés
    """
    
    aggregated = analysis_result.get("aggregated_results", {})
    
    return {
        "overall_compliance_rate": aggregated.get("overall_compliance_rate", 0),
        "overall_risk_score": aggregated.get("overall_risk_score", 0),
        "overall_risk_level": aggregated.get("overall_risk_level", "UNKNOWN"),
        "fields_analyzed": aggregated.get("fields_analyzed", {}),
        "total_anomalies": aggregated.get("total_anomalies", 0),
        "critical_fields": aggregated.get("critical_fields", []),
        "executive_summary": aggregated.get("executive_summary", {}),
    }
