from backend.agents.base_agent import PatientState
import logging

logger = logging.getLogger("IMDCS_DecisionEngine")

class DecisionEngine:
    def __init__(self):
        self.agent_name = "Decision_Engine_Meta_Agent"

    async def process(self, state: PatientState) -> PatientState:
        """
        The Meta-Agent: Consolidates all agent outputs and formulates 
        the final clinical guidance and structured rationale (Explainable AI).
        """
        risk = state.risk_level
        trend = state.computed_trend
        predicted = state.predicted_glucose_30m
        current = state.current_reading.glucose_value
        insights = state.behavioral_insights

        # Final decision payload architecture
        decision = {
            "action_required": False,
            "notification_type": "NONE", # NONE, INFO, WARNING, URGENT_ALERT
            "clinical_guidance": "",
            "rationale": ""
        }

        # 1. Critical Situations Management
        if risk == "CRITICAL":
            decision["action_required"] = True
            decision["notification_type"] = "URGENT_ALERT"
            
            if current < 70 or predicted < 55:
                decision["clinical_guidance"] = "Critical Hypoglycemia Risk! Consume 15g of fast-acting carbohydrates (e.g., half a cup of juice) immediately and recheck in 15 minutes."
                decision["rationale"] = f"Current glucose ({current}) or predicted ({predicted}) has dropped into a severe danger zone with a [{trend}] dynamic trend."
            else:
                decision["clinical_guidance"] = "Severe Hyperglycemia detected. Please follow your insulin correction protocol and check ketones if necessary."
                decision["rationale"] = f"Glucose levels have spiked dangerously, reaching ({current}) mg/dL."

        # 2. High Risk Situations Management
        elif risk == "HIGH":
            decision["action_required"] = True
            decision["notification_type"] = "WARNING"
            
            if "FALLING" in trend:
                decision["clinical_guidance"] = "Glucose is dropping toward the target low boundary. Consider consuming a complex carbohydrate snack."
            else:
                decision["clinical_guidance"] = "Glucose level is elevated and rising. Continuous monitoring is required to avoid further spikes."
                
            # Inject behavioral insight into the rationale for Explainability
            behavioral_context = " " + " ".join(insights[:1]) if insights else ""
            decision["rationale"] = f"High medical risk evaluated based on current kinetics and trend.{behavioral_context}"

        # 3. Stable Situations (Low / Medium Risk)
        else:
            decision["action_required"] = False
            decision["notification_type"] = "INFO"
            decision["clinical_guidance"] = "Glucose levels are stable and within the safe target range. Keep up the good work!"
            decision["rationale"] = "All streaming metrics and velocity vectors indicate metabolic stability."

        # Save decision to the Shared State
        state.final_decision = decision
        
        logger.info(f"==> [Decision Engine] Decision formulated for Patient {state.patient_id}. Action Required: {decision['action_required']}")
        return state