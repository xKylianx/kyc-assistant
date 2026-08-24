from __future__ import annotations

import logging
from typing import Optional

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
# Option prod (selon version/install) :
# from langgraph.checkpoint.sqlite import SqliteSaver
# from langgraph.checkpoint.postgres import PostgresSaver

from src.config.config import PlotAgentState
from src.nodes.plot_nodes import (
    generate_msisdn_plot,
    generate_first_name_plot,
    generate_last_name_plot,
    generate_id_type_plot,
    generate_id_number_plot,
    generate_dob_plot,
    generate_address_plot,
    generate_city_plot,
    generate_compliance_summary,
)

logger = logging.getLogger(__name__)


def create_plot_agent_graph(checkpointer: Optional[object] = None):
    """
    Build and compile the Plot Agent graph.
    Input: PlotAgentState
    Output: PlotAgentState enriched with plot/compliance summary artifacts
    """
    logger.info("Building PLOT AGENT graph")

    builder = StateGraph(state_schema=PlotAgentState)

    # Nodes
    builder.add_node("generate_msisdn_plot", generate_msisdn_plot)
    builder.add_node("generate_first_name_plot", generate_first_name_plot)
    builder.add_node("generate_last_name_plot", generate_last_name_plot)
    builder.add_node("generate_id_type_plot", generate_id_type_plot)
    builder.add_node("generate_id_number_plot", generate_id_number_plot)
    builder.add_node("generate_dob_plot", generate_dob_plot)
    builder.add_node("generate_address_plot", generate_address_plot)
    builder.add_node("generate_city_plot", generate_city_plot)
    builder.add_node("generate_compliance_summary", generate_compliance_summary)

    # Edges
    builder.add_edge(START, "generate_msisdn_plot")
    builder.add_edge("generate_msisdn_plot", "generate_first_name_plot")
    builder.add_edge("generate_first_name_plot", "generate_last_name_plot")
    builder.add_edge("generate_last_name_plot", "generate_id_type_plot")
    builder.add_edge("generate_id_type_plot", "generate_id_number_plot")
    builder.add_edge("generate_id_number_plot", "generate_dob_plot")
    builder.add_edge("generate_dob_plot", "generate_address_plot")
    builder.add_edge("generate_address_plot", "generate_city_plot")
    builder.add_edge("generate_city_plot", "generate_compliance_summary")
    builder.add_edge("generate_compliance_summary", END)

    # DEV fallback
    if checkpointer is None:
        checkpointer = InMemorySaver()

    graph = builder.compile(checkpointer=checkpointer)
    logger.info("PLOT AGENT graph compiled successfully")
    return graph


def run_plot_agent(
    initial_state: PlotAgentState,
    thread_id: str,
    graph=None,
) -> PlotAgentState:
    """
    Execution entrypoint for service/FastAPI layer.
    """
    try:
        if graph is None:
            graph = create_plot_agent_graph()

        config = {"configurable": {"thread_id": thread_id}}
        result = graph.invoke(initial_state, config=config)
        return result

    except Exception as exc:
        logger.exception("Plot agent execution failed")
        failed_state = dict(initial_state)
        failed_state["plot_status"] = "error"
        failed_state["plot_error"] = str(exc)
        return failed_state
