from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from core.state import AgentState
from agent.nodes import (
    classify_intent_node,
    new_lead_node,
    pipeline_node,
    booked_node,
    service_node,
    clarification_node,
)


def route_by_stage(state: AgentState) -> str:
    stage = state.get("active_stage", "new_lead")
    if stage == "new_lead":
        return "new_lead_node"
    if stage == "ongoing_pipeline":
        return "pipeline_node"
    if stage == "booked_vehicle":
        return "booked_node"
    if stage == "post_purchase_service":
        return "service_node"
    return "clarification_node"


def build_automotive_graph():
    builder = StateGraph(AgentState)

    # Register Nodes
    builder.add_node("classify_intent", classify_intent_node)
    builder.add_node("new_lead_node", new_lead_node)
    builder.add_node("pipeline_node", pipeline_node)
    builder.add_node("booked_node", booked_node)
    builder.add_node("service_node", service_node)
    builder.add_node("clarification_node", clarification_node)

    # Define Edges
    builder.add_edge(START, "classify_intent")
    builder.add_conditional_edges(
        "classify_intent",
        route_by_stage,
        {
            "new_lead_node": "new_lead_node",
            "pipeline_node": "pipeline_node",
            "booked_node": "booked_node",
            "service_node": "service_node",
            "clarification_node": "clarification_node",
        },
    )

    builder.add_edge("new_lead_node", END)
    builder.add_edge("pipeline_node", END)
    builder.add_edge("booked_node", END)
    builder.add_edge("service_node", END)
    builder.add_edge("clarification_node", END)

    # In-memory checkpointer for session persistence
    memory = MemorySaver()
    return builder.compile(checkpointer=memory)


automotive_graph = build_automotive_graph()
