import duckdb
import os
from dotenv import load_dotenv
from src.config.config import PrepAgentState
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

# Initialize the LLM (adjust based on your setup)
model = ChatOpenAI(
     model= "openai/gpt-5-chat",
     api_key=os.getenv("OPENAI_API_KEY"),
     base_url = os.getenv("BASE_URL"),
)


def active_lines_filter(state: PrepAgentState) -> PrepAgentState:
    """
    Filter active lines and detect the status column and values.
    
    For Orange Money: Uses ACCOUNT_STATUS = 'Y'
    For others: Uses LLM to determine which status values represent active records
    
    Args:
        state: PrepAgentState with file_path and is_orange_money flag
        
    Returns:
        Updated state with active lines count and status information
    """
    
    print("\n" + "=" * 60)
    print("🔥 FILTERING ACTIVE LINES")
    print("=" * 60)
    
    file_path = state.get("file_path")
    is_orange_money = state.get("is_orange_money", False)
    schema_profile = state.get("schema_profile", {})
    
    if not file_path:
        print("❌ No file path provided")
        state["active_lines_filter_error"] = "No file path provided"
        return state
    
    try:
        con = duckdb.connect()
        
        # ====================================================================
        # STEP 1: Get total row count
        # ====================================================================
        
        total_result = con.execute(
            f"SELECT COUNT(*) FROM read_csv_auto('{file_path}')"
        ).fetchall()
        
        total_rows = total_result[0][0] if total_result else 0
        print(f"✓ Total rows: {total_rows:,}")
        
        state["total_lines_count"] = total_rows
        
        # ====================================================================
        # STEP 2: Handle Orange Money case
        # ====================================================================
        
        if is_orange_money:
            print("\n🍊 Orange Money detected")
            print("✓ Using ACCOUNT_STATUS = 'Y' for active records")
            
            # Orange Money uses ACCOUNT_STATUS column
            active_result = con.execute(
                f"SELECT COUNT(*) FROM read_csv_auto('{file_path}') WHERE ACCOUNT_STATUS = 'Y'"
            ).fetchall()
            
            active_rows = active_result[0][0] if active_result else 0
            
            state["active_lines_count"] = active_rows
            state["active_lines_percentage"] = (active_rows / total_rows * 100) if total_rows > 0 else 0
            state["active_lines_filter_method"] = "orange_money"
            state["active_status_column"] = "ACCOUNT_STATUS"
            state["active_status_values"] = ["Y"]
            state["active_status_reasoning"] = "Orange Money schema uses ACCOUNT_STATUS = 'Y' for active records"
            
            print(f"✓ Active rows (ACCOUNT_STATUS = 'Y'): {active_rows:,}")
            print(f"✓ Percentage: {(active_rows / total_rows * 100):.2f}%")
            
            con.close()
            return state
        
        # ====================================================================
        # STEP 3: Detect status column for non-Orange Money
        # ====================================================================
        
        print("\n🔍 Detecting status column...")
        
        # Look for common status column names
        status_column_candidates = [
            "statut", "statut_in", "status", "state", "account_status",
            "customer_status", "subscription_status", "active", "is_active",
            "enabled", "disabled", "flag", "indicator"
        ]
        
        status_column = None
        
        for candidate in status_column_candidates:
            for col_name in schema_profile.keys():
                if col_name.lower() == candidate.lower():
                    status_column = col_name
                    print(f"✓ Found status column: '{status_column}'")
                    break
            if status_column:
                break
        
        if not status_column:
            print("⚠️ No status column detected - treating all records as active")
            state["active_lines_count"] = total_rows
            state["active_lines_percentage"] = 100.0
            state["active_lines_filter_method"] = "no_status_column"
            state["active_status_column"] = None
            state["active_status_values"] = []
            state["active_status_reasoning"] = "No status column found - all records considered active"
            
            con.close()
            return state
        
        # ====================================================================
        # STEP 4: Get unique values in status column
        # ====================================================================
        
        print(f"\n📊 Analyzing status column: '{status_column}'")
        
        unique_values_result = con.execute(
            f"SELECT DISTINCT \"{status_column}\" FROM read_csv_auto('{file_path}') ORDER BY \"{status_column}\""
        ).fetchall()
        
        unique_values = [str(row[0]) for row in unique_values_result if row[0] is not None]
        print(f"✓ Unique values in '{status_column}': {unique_values}")
        
        # ====================================================================
        # STEP 5: Use LLM to determine active values
        # ====================================================================
        
        print(f"\n🤖 Using LLM to determine active status values...")
        
        active_values, reasoning = _detect_active_values_with_llm(
            status_column=status_column,
            unique_values=unique_values
        )
        
        print(f"✓ LLM determined active values: {active_values}")
        print(f"✓ Reasoning: {reasoning}")
        
        # ====================================================================
        # STEP 6: Count active records
        # ====================================================================
        
        if active_values:
            # Build WHERE clause
            values_str = ", ".join([f"'{val}'" for val in active_values])
            where_clause = f"WHERE \"{status_column}\" IN ({values_str})"
            
            active_result = con.execute(
                f"SELECT COUNT(*) FROM read_csv_auto('{file_path}') {where_clause}"
            ).fetchall()
            
            active_rows = active_result[0][0] if active_result else 0
            
            state["active_lines_count"] = active_rows
            state["active_lines_percentage"] = (active_rows / total_rows * 100) if total_rows > 0 else 0
            state["active_lines_filter_method"] = "llm_identified"
            state["active_status_column"] = status_column
            state["active_status_values"] = active_values
            state["active_status_reasoning"] = reasoning
            
            print(f"\n✓ Active rows ({status_column} IN {active_values}): {active_rows:,}")
            print(f"✓ Percentage: {(active_rows / total_rows * 100):.2f}%")
        
        else:
            # LLM couldn't determine active values
            print("⚠️ LLM could not determine active values - treating all records as active")
            state["active_lines_count"] = total_rows
            state["active_lines_percentage"] = 100.0
            state["active_lines_filter_method"] = "llm_failed"
            state["active_status_column"] = status_column
            state["active_status_values"] = []
            state["active_status_reasoning"] = "LLM could not determine active status values"
        
        con.close()
        
        print("\n✅ Active Lines Filter Complete")
        print("=" * 60)
        
        return state
        
    except Exception as e:
        print(f"\n✗ Error during active lines filter: {str(e)}")
        import traceback
        traceback.print_exc()
        
        state["active_lines_filter_error"] = str(e)
        state["active_lines_count"] = 0
        state["active_lines_percentage"] = 0.0
        
        print("=" * 60)
        
        return state


def _detect_active_values_with_llm(status_column: str, unique_values: list) -> tuple:
    """
    Use LLM to determine which status values represent active records.
    
    Args:
        status_column: Name of the status column
        unique_values: List of unique values in the status column
        
    Returns:
        Tuple of (active_values, reasoning)
    """
    
    # Initialize LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
    )
    
    # Create prompt
    prompt = f"""
You are a data analyst expert. Your task is to determine which status values represent "active" records in a customer dataset.

Status Column Name: {status_column}
Unique Values in Column: {unique_values}

Based on the column name and the values present, determine:
1. Which value(s) represent ACTIVE records
2. Your reasoning for this determination

Respond in JSON format:
{{
    "active_values": ["value1", "value2"],
    "reasoning": "Your explanation here"
}}

Important:
- Be precise and only include values that clearly represent active status
- If unsure, explain your reasoning
- Consider common patterns like: Y/N, 1/0, ACTIVE/INACTIVE, ENABLED/DISABLED, etc.
- The column name "{status_column}" may provide hints about what the values mean
"""
    
    
    print(f"\n📝 Sending to LLM:")
    print(f"   Column: {status_column}")
    print(f"   Values: {unique_values}")
    
    # Get LLM response
    response = model.invoke(prompt)
    response_text = response.content
    
    print(f"\n🤖 LLM Response:")
    print(f"   {response_text}")
    
    # Parse response
    try:
        import json
        
        # Extract JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            
            active_values = result.get("active_values", [])
            reasoning = result.get("reasoning", "")
            
            return active_values, reasoning
        else:
            print("⚠️ Could not parse JSON from LLM response")
            return [], "Could not parse LLM response"
    
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON parsing error: {str(e)}")
        return [], f"JSON parsing error: {str(e)}"
    except Exception as e:
        print(f"⚠️ Error parsing LLM response: {str(e)}")
        return [], f"Error parsing response: {str(e)}"
