import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from src.config.config import AnalysisAgentState


def _create_streamlit_histogram(
    data: dict,
    title: str,
    field_name: str,
) -> dict:
    """
    Create histogram data for Streamlit display.
    
    Args:
        data: Dictionary with analysis data
        title: Title of the histogram
        field_name: Name of the field being analyzed
        
    Returns:
        Dictionary with chart data for Streamlit
    """
    
    # Extract relevant metrics
    valid_count = data.get("valid_count", 0)
    null_count = data.get("null_count", 0)
    row_count = data.get("row_count", 0)
    invalid_count = row_count - valid_count - null_count
    
    compliance_rate = data.get("compliance_rate", 0)
    
    # Create data for chart
    chart_data = {
        "Status": ["Valid", "Null", "Invalid"],
        "Count": [valid_count, null_count, invalid_count],
        "Percentage": [
            (valid_count / row_count * 100) if row_count > 0 else 0,
            (null_count / row_count * 100) if row_count > 0 else 0,
            (invalid_count / row_count * 100) if row_count > 0 else 0,
        ]
    }
    
    return {
        "title": title,
        "field_name": field_name,
        "data": chart_data,
        "compliance_rate": compliance_rate,
        "row_count": row_count,
        "valid_count": valid_count,
        "null_count": null_count,
        "invalid_count": invalid_count,
    }


def generate_msisdn_plot(state: AnalysisAgentState) -> AnalysisAgentState:
    """
    Generate MSISDN analysis histogram.
    
    Args:
        state: AnalysisAgentState with msisdn_analysis
        
    Returns:
        Updated state with msisdn_plot
    """
    
    print("\n" + "=" * 60)
    print("📱 GENERATING MSISDN PLOT")
    print("=" * 60)
    
    msisdn_columns = state.get("msisdn_columns", [])
    
    if not msisdn_columns:
        print("⏭️ No MSISDN columns - skipping plot")
        state["msisdn_plot"] = None
        state["msisdn_plot_status"] = "skipped"
        return state
    
    try:
        msisdn_analysis = state.get("msisdn_analysis", {})
        
        if not msisdn_analysis:
            print("⚠️ No MSISDN analysis data")
            state["msisdn_plot"] = None
            state["msisdn_plot_status"] = "error"
            return state
        
        # Create chart data
        plot_data = _create_streamlit_histogram(
            data=msisdn_analysis,
            title="📱 MSISDN Compliance Analysis",
            field_name="MSISDN"
        )
        
        state["msisdn_plot"] = plot_data
        state["msisdn_plot_status"] = "completed"
        
        compliance_rate = msisdn_analysis.get("compliance_rate", 0)
        print(f"✅ MSISDN plot generated (Compliance: {compliance_rate}%)")
        
        return state
        
    except Exception as e:
        print(f"❌ Error generating MSISDN plot: {str(e)}")
        state["msisdn_plot"] = None
        state["msisdn_plot_status"] = "error"
        state["msisdn_plot_error"] = str(e)
        return state


def generate_first_name_plot(state: AnalysisAgentState) -> AnalysisAgentState:
    """
    Generate First Name analysis histogram.
    """
    
    print("\n" + "=" * 60)
    print("👤 GENERATING FIRST NAME PLOT")
    print("=" * 60)
    
    first_name_columns = state.get("first_name_columns", [])
    
    if not first_name_columns:
        print("⏭️ No First Name columns - skipping plot")
        state["first_name_plot"] = None
        state["first_name_plot_status"] = "skipped"
        return state
    
    try:
        first_name_analysis = state.get("first_name_analysis", {})
        
        if not first_name_analysis:
            print("⚠️ No First Name analysis data")
            state["first_name_plot"] = None
            state["first_name_plot_status"] = "error"
            return state
        
        # Create chart data
        plot_data = _create_streamlit_histogram(
            data=first_name_analysis,
            title="👤 First Name Compliance Analysis",
            field_name="First Name"
        )
        
        state["first_name_plot"] = plot_data
        state["first_name_plot_status"] = "completed"
        
        compliance_rate = first_name_analysis.get("compliance_rate", 0)
        print(f"✅ First Name plot generated (Compliance: {compliance_rate}%)")
        
        return state
        
    except Exception as e:
        print(f"❌ Error generating First Name plot: {str(e)}")
        state["first_name_plot"] = None
        state["first_name_plot_status"] = "error"
        state["first_name_plot_error"] = str(e)
        return state


def generate_last_name_plot(state: AnalysisAgentState) -> AnalysisAgentState:
    """
    Generate Last Name analysis histogram.
    """
    
    print("\n" + "=" * 60)
    print("👤 GENERATING LAST NAME PLOT")
    print("=" * 60)
    
    last_name_columns = state.get("last_name_columns", [])
    
    if not last_name_columns:
        print("⏭️ No Last Name columns - skipping plot")
        state["last_name_plot"] = None
        state["last_name_plot_status"] = "skipped"
        return state
    
    try:
        last_name_analysis = state.get("last_name_analysis", {})
        
        if not last_name_analysis:
            print("⚠️ No Last Name analysis data")
            state["last_name_plot"] = None
            state["last_name_plot_status"] = "error"
            return state
        
        # Create chart data
        plot_data = _create_streamlit_histogram(
            data=last_name_analysis,
            title="👤 Last Name Compliance Analysis",
            field_name="Last Name"
        )
        
        state["last_name_plot"] = plot_data
        state["last_name_plot_status"] = "completed"
        
        compliance_rate = last_name_analysis.get("compliance_rate", 0)
        print(f"✅ Last Name plot generated (Compliance: {compliance_rate}%)")
        
        return state
        
    except Exception as e:
        print(f"❌ Error generating Last Name plot: {str(e)}")
        state["last_name_plot"] = None
        state["last_name_plot_status"] = "error"
        state["last_name_plot_error"] = str(e)
        return state


def generate_id_type_plot(state: AnalysisAgentState) -> AnalysisAgentState:
    """
    Generate ID Type analysis histogram.
    """
    
    print("\n" + "=" * 60)
    print("🆔 GENERATING ID TYPE PLOT")
    print("=" * 60)
    
    id_type_columns = state.get("id_type_columns", [])
    
    if not id_type_columns:
        print("⏭️ No ID Type columns - skipping plot")
        state["id_type_plot"] = None
        state["id_type_plot_status"] = "skipped"
        return state
    
    try:
        id_type_analysis = state.get("id_type_analysis", {})
        
        if not id_type_analysis:
            print("⚠️ No ID Type analysis data")
            state["id_type_plot"] = None
            state["id_type_plot_status"] = "error"
            return state
        
        # Create chart data
        plot_data = _create_streamlit_histogram(
            data=id_type_analysis,
            title="🆔 ID Type Compliance Analysis",
            field_name="ID Type"
        )
        
        state["id_type_plot"] = plot_data
        state["id_type_plot_status"] = "completed"
        
        compliance_rate = id_type_analysis.get("compliance_rate", 0)
        print(f"✅ ID Type plot generated (Compliance: {compliance_rate}%)")
        
        return state
        
    except Exception as e:
        print(f"❌ Error generating ID Type plot: {str(e)}")
        state["id_type_plot"] = None
        state["id_type_plot_status"] = "error"
        state["id_type_plot_error"] = str(e)
        return state


def generate_id_number_plot(state: AnalysisAgentState) -> AnalysisAgentState:
    """
    Generate ID Number analysis histogram.
    """
    
    print("\n" + "=" * 60)
    print("🆔 GENERATING ID NUMBER PLOT")
    print("=" * 60)
    
    id_number_columns = state.get("id_number_columns", [])
    
    if not id_number_columns:
        print("⏭️ No ID Number columns - skipping plot")
        state["id_number_plot"] = None
        state["id_number_plot_status"] = "skipped"
        return state
    
    try:
        id_number_analysis = state.get("id_number_analysis", {})
        
        if not id_number_analysis:
            print("⚠️ No ID Number analysis data")
            state["id_number_plot"] = None
            state["id_number_plot_status"] = "error"
            return state
        
        # Create chart data
        plot_data = _create_streamlit_histogram(
            data=id_number_analysis,
            title="🆔 ID Number Compliance Analysis",
            field_name="ID Number"
        )
        
        state["id_number_plot"] = plot_data
        state["id_number_plot_status"] = "completed"
        
        compliance_rate = id_number_analysis.get("compliance_rate", 0)
        print(f"✅ ID Number plot generated (Compliance: {compliance_rate}%)")
        
        return state
        
    except Exception as e:
        print(f"❌ Error generating ID Number plot: {str(e)}")
        state["id_number_plot"] = None
        state["id_number_plot_status"] = "error"
        state["id_number_plot_error"] = str(e)
        return state


def generate_dob_plot(state: AnalysisAgentState) -> AnalysisAgentState:
    """
    Generate Date of Birth analysis histogram.
    """
    
    print("\n" + "=" * 60)
    print("📅 GENERATING DATE OF BIRTH PLOT")
    print("=" * 60)
    
    dob_columns = state.get("dob_columns", [])
    
    if not dob_columns:
        print("⏭️ No DOB columns - skipping plot")
        state["dob_plot"] = None
        state["dob_plot_status"] = "skipped"
        return state
    
    try:
        dob_analysis = state.get("dob_analysis", {})
        
        if not dob_analysis:
            print("⚠️ No DOB analysis data")
            state["dob_plot"] = None
            state["dob_plot_status"] = "error"
            return state
        
        # Create chart data
        plot_data = _create_streamlit_histogram(
            data=dob_analysis,
            title="📅 Date of Birth Compliance Analysis",
            field_name="Date of Birth"
        )
        
        state["dob_plot"] = plot_data
        state["dob_plot_status"] = "completed"
        
        compliance_rate = dob_analysis.get("compliance_rate", 0)
        print(f"✅ DOB plot generated (Compliance: {compliance_rate}%)")
        
        return state
        
    except Exception as e:
        print(f"❌ Error generating DOB plot: {str(e)}")
        state["dob_plot"] = None
        state["dob_plot_status"] = "error"
        state["dob_plot_error"] = str(e)
        return state


def generate_address_plot(state: AnalysisAgentState) -> AnalysisAgentState:
    """
    Generate Address analysis histogram.
    """
    
    print("\n" + "=" * 60)
    print("📍 GENERATING ADDRESS PLOT")
    print("=" * 60)
    
    address_columns = state.get("address_columns", [])
    
    if not address_columns:
        print("⏭️ No Address columns - skipping plot")
        state["address_plot"] = None
        state["address_plot_status"] = "skipped"
        return state
    
    try:
        address_analysis = state.get("address_analysis", {})
        
        if not address_analysis:
            print("⚠️ No Address analysis data")
            state["address_plot"] = None
            state["address_plot_status"] = "error"
            return state
        
        # Create chart data
        plot_data = _create_streamlit_histogram(
            data=address_analysis,
            title="📍 Address Compliance Analysis",
            field_name="Address"
        )
        
        state["address_plot"] = plot_data
        state["address_plot_status"] = "completed"
        
        compliance_rate = address_analysis.get("compliance_rate", 0)
        print(f"✅ Address plot generated (Compliance: {compliance_rate}%)")
        
        return state
        
    except Exception as e:
        print(f"❌ Error generating Address plot: {str(e)}")
        state["address_plot"] = None
        state["address_plot_status"] = "error"
        state["address_plot_error"] = str(e)
        return state


def generate_city_plot(state: AnalysisAgentState) -> AnalysisAgentState:
    """
    Generate City analysis histogram.
    """
    
    print("\n" + "=" * 60)
    print("🏙️ GENERATING CITY PLOT")
    print("=" * 60)
    
    city_columns = state.get("city_columns", [])
    
    if not city_columns:
        print("⏭️ No City columns - skipping plot")
        state["city_plot"] = None
        state["city_plot_status"] = "skipped"
        return state
    
    try:
        city_analysis = state.get("city_analysis", {})
        
        if not city_analysis:
            print("⚠️ No City analysis data")
            state["city_plot"] = None
            state["city_plot_status"] = "error"
            return state
        
        # Create chart data
        plot_data = _create_streamlit_histogram(
            data=city_analysis,
            title="🏙️ City Compliance Analysis",
            field_name="City"
        )
        
        state["city_plot"] = plot_data
        state["city_plot_status"] = "completed"
        
        compliance_rate = city_analysis.get("compliance_rate", 0)
        print(f"✅ City plot generated (Compliance: {compliance_rate}%)")
        
        return state
        
    except Exception as e:
        print(f"❌ Error generating City plot: {str(e)}")
        state["city_plot"] = None
        state["city_plot_status"] = "error"
        state["city_plot_error"] = str(e)
        return state


def generate_compliance_summary(state: AnalysisAgentState) -> AnalysisAgentState:
    """
    Generate overall compliance summary.
    
    Args:
        state: AnalysisAgentState with all analysis results
        
    Returns:
        Updated state with compliance_summary
    """
    
    print("\n" + "=" * 60)
    print("📊 GENERATING COMPLIANCE SUMMARY")
    print("=" * 60)
    
    # Collect all compliance rates
    compliance_data = {}
    
    analysis_fields = [
        ("msisdn", "📱 MSISDN"),
        ("first_name", "👤 First Name"),
        ("last_name", "👤 Last Name"),
        ("id_type", "🆔 ID Type"),
        ("id_number", "🆔 ID Number"),
        ("dob", "📅 Date of Birth"),
        ("address", "📍 Address"),
        ("city", "🏙️ City"),
    ]
    
    for field_key, field_name in analysis_fields:
        analysis_key = f"{field_key}_analysis"
        analysis = state.get(analysis_key, {})
        
        if analysis:
            compliance_rate = analysis.get("compliance_rate", 0)
            compliance_data[field_name] = compliance_rate
            print(f"  {field_name}: {compliance_rate}%")
    
    # Calculate overall compliance
    if compliance_data:
        overall_compliance = sum(compliance_data.values()) / len(compliance_data)
    else:
        overall_compliance = 0.0
    
    print(f"\n✅ Overall Compliance: {overall_compliance:.2f}%")
    
    # Determine compliance status
    if overall_compliance >= 95:
        compliance_status = "Excellent"
        status_color = "🟢"
    elif overall_compliance >= 90:
        compliance_status = "Good"
        status_color = "🟡"
    elif overall_compliance >= 80:
        compliance_status = "Fair"
        status_color = "🟠"
    else:
        compliance_status = "Poor"
        status_color = "🔴"
    
    # Create summary
    summary = {
        "overall_compliance": round(overall_compliance, 2),
        "compliance_status": compliance_status,
        "status_color": status_color,
        "field_compliance": compliance_data,
        "total_fields_analyzed": len(compliance_data),
        "fields_with_issues": sum(1 for rate in compliance_data.values() if rate < 90),
        "fields_excellent": sum(1 for rate in compliance_data.values() if rate >= 95),
    }
    
    state["compliance_summary"] = summary
    state["compliance_summary_status"] = "completed"
    
    print("=" * 60)
    
    return state
