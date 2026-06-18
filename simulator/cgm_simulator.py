import time
import math
import random
import httpx
from datetime import datetime

class AdvancedCGMSimulator:
    def __init__(self, patient_id: str, profile: str = "type_2"):
        """
        Profiles:
        - 'high_carb' (Patient A): High carbohydrate diet, frequent high spikes.
        - 'highly_active' (Patient B): Highly active, frequent drops from exercise.
        - 'hypo_prone' (Patient C): Frequent hypoglycemia, low baseline.
        - 'irregular_meals' (Patient D): Irregular meal schedule, unpredictable spikes.
        - 'poor_adherence' (Patient E): Poor medication adherence, sustained highs.
        - 'type_2': Standard Type 2, moderate baseline, moderate spikes.
        - 'healthy': Stable 80-120 mg/dL.
        """
        self.patient_id = patient_id
        self.profile = profile
        self.backend_url = "http://127.0.0.1:8000/glucose/stream"
        self.event_url = "http://127.0.0.1:8000/glucose/event"
        
        # Baselines
        baselines = {
            "healthy": 95.0,
            "type_2": 150.0,
            "high_carb": 160.0,
            "highly_active": 110.0,
            "hypo_prone": 85.0,
            "irregular_meals": 140.0,
            "poor_adherence": 190.0
        }
        self.current_glucose = baselines.get(profile, 100.0)
        
        self.time_step = 0
        self.active_events = []

    def inject_behavioral_event(self, event_type: str, details: dict):
        print(f"\n[Simulator] Injected Event locally: {event_type} with details {details}")
        self.active_events.append({
            "type": event_type,
            "details": details,
            "elapsed_time": 0
        })
        
        try:
            httpx.post(self.event_url, json={
                "patient_id": self.patient_id,
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type,
                "details": details
            })
        except Exception as e:
            print(f"[Simulator Warning] Could not send event to backend: {e}")

    def calculate_next_glucose(self) -> float:
        self.time_step += 1
        
        # Base circadian wave
        circadian_wave = 4 * math.sin(self.time_step / 6)
        noise = random.uniform(-3.0, 3.0)
        
        dynamic_change = 0.0
        
        for event in self.active_events[:]:
            event["elapsed_time"] += 5
            t = event["elapsed_time"]
            
            if event["type"] == "meal":
                carbs = event["details"].get("carbs_g", 50)
                # High carb profile has exaggerated response to meals
                multiplier = 1.5 if self.profile == "high_carb" else 1.0
                if t <= 120:
                    dynamic_change += multiplier * (carbs / 8) * math.sin(math.pi * t / 120)
                else:
                    self.active_events.remove(event)
                    
            elif event["type"] == "insulin":
                units = event["details"].get("units", 5)
                # Hypo prone profile has exaggerated response to insulin
                multiplier = 1.5 if self.profile == "hypo_prone" else 1.0
                # Poor adherence might have weak response or delayed
                if self.profile == "poor_adherence":
                    multiplier = 0.5
                if t <= 180:
                    dynamic_change -= multiplier * (units * 2.2) * math.sin(math.pi * t / 180)
                else:
                    self.active_events.remove(event)
                    
            elif event["type"] == "exercise":
                duration = event["details"].get("duration_min", 30)
                intensity = event["details"].get("intensity", 1.0)
                # Highly active profile burns glucose faster
                multiplier = 1.5 if self.profile == "highly_active" else 1.0
                if t <= duration:
                    dynamic_change -= (3.0 * intensity * multiplier)
                else:
                    self.active_events.remove(event)

        self.current_glucose += circadian_wave + dynamic_change + noise
        self.current_glucose = max(35.0, min(self.current_glucose, 450.0))
        return round(self.current_glucose, 1)

    def trigger_profile_events(self):
        """Automatically triggers events based on the patient's profile."""
        if self.profile == "high_carb":
            if self.time_step % 20 == 0: # Frequent high carb meals
                self.inject_behavioral_event("meal", {"carbs_g": 120, "food_name": "Pizza"})
                self.inject_behavioral_event("insulin", {"units": 6}) # often not enough
        
        elif self.profile == "highly_active":
            if self.time_step % 30 == 0:
                self.inject_behavioral_event("exercise", {"duration_min": 60, "intensity": 1.5})
            if self.time_step % 25 == 0:
                self.inject_behavioral_event("meal", {"carbs_g": 60, "food_name": "Protein Shake"})
                
        elif self.profile == "hypo_prone":
            if self.time_step % 15 == 0:
                self.inject_behavioral_event("insulin", {"units": 10}) # accidental overdose
            if self.time_step % 18 == 0:
                self.inject_behavioral_event("meal", {"carbs_g": 30, "food_name": "Salad"})
                
        elif self.profile == "irregular_meals":
            if random.random() < 0.05: # random meals
                self.inject_behavioral_event("meal", {"carbs_g": random.randint(30, 100), "food_name": "Snack"})
                if random.random() < 0.5:
                    self.inject_behavioral_event("insulin", {"units": random.randint(2, 8)})
                    
        elif self.profile == "poor_adherence":
            if self.time_step % 20 == 0:
                self.inject_behavioral_event("meal", {"carbs_g": 80, "food_name": "Burger"})
            # Misses insulin often
            if self.time_step % 20 == 0 and random.random() < 0.2:
                self.inject_behavioral_event("insulin", {"units": 5})

    def start_streaming(self, intervals_sec: int = 2):
        print(f"🚀 Started Live CGM Simulation for Patient: {self.patient_id} ({self.profile})")
        print(f"Streaming to {self.backend_url} every {intervals_sec} seconds...\n")
        
        while True:
            glucose_val = self.calculate_next_glucose()
            payload = {
                "patient_id": self.patient_id,
                "timestamp": datetime.utcnow().isoformat(),
                "glucose_value": glucose_val
            }
            
            try:
                response = httpx.post(self.backend_url, json=payload, timeout=5.0)
                if response.status_code == 200:
                    res_data = response.json()
                    analysis = res_data.get("analysis", {})
                    decision = res_data.get("decision", {})
                    
                    print(f"⏰ [CGM Sensor] Glucose: {glucose_val} mg/dL | "
                          f"Trend: {analysis.get('computed_trend')} | "
                          f"Predicted: {analysis.get('predicted_glucose_30m')} | "
                          f"Risk: {analysis.get('risk_level')}")
                    
                    if decision and decision.get("action_required"):
                        print(f"   🚨 ALERT [{decision.get('notification_type')}]: {decision.get('clinical_guidance')}")
                        print(f"   🧠 Rationale: {decision.get('rationale')}\n")
                else:
                    print(f"❌ Error from server: {response.status_code}")
            except Exception as e:
                # print(f"❌ Connection failed to Backend: {e}")
                # Silent failure if backend is not up, just keep simulating
                pass
                
            self.trigger_profile_events()

            time.sleep(intervals_sec)

def generate_historical_dataset(patient_id: str, profile: str, days: int = 7):
    """Generates a CSV of historical data for ML training."""
    import pandas as pd
    
    sim = AdvancedCGMSimulator(patient_id=patient_id, profile=profile)
    data = []
    
    print(f"Generating {days} days of historical data for {patient_id}...")
    total_steps = (days * 24 * 60) // 5 # 5 min intervals
    
    current_time = datetime.utcnow()
    
    for i in range(total_steps):
        glucose = sim.calculate_next_glucose()
        sim.trigger_profile_events()
        
        # log events for the timestep
        event_str = ""
        for e in sim.active_events:
            if e['elapsed_time'] == 5: # Just started
                event_str += f"{e['type']}: {e['details']}; "
                
        data.append({
            "timestamp": current_time,
            "glucose_value": glucose,
            "events": event_str
        })
        current_time = pd.Timestamp(current_time) + pd.Timedelta(minutes=5)
        
    df = pd.DataFrame(data)
    filename = f"dataset_{patient_id}_{profile}.csv"
    df.to_csv(filename, index=False)
    print(f"Saved {len(df)} records to {filename}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "generate":
        generate_historical_dataset("patient_A", "high_carb", 30)
        generate_historical_dataset("patient_B", "highly_active", 30)
        generate_historical_dataset("patient_C", "hypo_prone", 30)
        generate_historical_dataset("patient_D", "irregular_meals", 30)
        generate_historical_dataset("patient_E", "poor_adherence", 30)
    else:
        simulator = AdvancedCGMSimulator(patient_id="patient_A", profile="high_carb")
        simulator.start_streaming(intervals_sec=2)