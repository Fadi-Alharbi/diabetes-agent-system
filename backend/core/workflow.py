from langgraph.graph import StateGraph, END
from backend.core.state import PatientState
from backend.core.agents import (
    data_agent_node,
    trend_agent_node,
    prediction_agent_node,
    food_impact_agent_node,
    behavior_agent_node,
    risk_agent_node,
    recommendation_agent_node
)

def build_workflow():
    workflow = StateGraph(PatientState)

    # Add nodes
    workflow.add_node("DataAgent", data_agent_node)
    workflow.add_node("TrendAgent", trend_agent_node)
    workflow.add_node("PredictionAgent", prediction_agent_node)
    workflow.add_node("FoodImpactAgent", food_impact_agent_node)
    workflow.add_node("BehaviorAgent", behavior_agent_node)
    workflow.add_node("RiskAgent", risk_agent_node)
    workflow.add_node("MetaDecisionAgent", recommendation_agent_node)

    # Define edges (Sequential pipeline for now, can be parallelized)
    workflow.add_edge("DataAgent", "TrendAgent")
    workflow.add_edge("TrendAgent", "PredictionAgent")
    
    # Branching logic could go here, but for simplicity we run all analyzers
    workflow.add_edge("PredictionAgent", "FoodImpactAgent")
    workflow.add_edge("FoodImpactAgent", "BehaviorAgent")
    workflow.add_edge("BehaviorAgent", "RiskAgent")
    workflow.add_edge("RiskAgent", "MetaDecisionAgent")
    workflow.add_edge("MetaDecisionAgent", END)

    workflow.set_entry_point("DataAgent")
    
    return workflow.compile()

# Singleton graph app
app_graph = build_workflow()
