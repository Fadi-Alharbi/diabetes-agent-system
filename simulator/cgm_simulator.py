import time
import math
import random
import httpx
from datetime import datetime

class AdvancedCGMSimulator:
    def __init__(self, patient_id: str, profile: str = "type_2"):
        """
        البروفايلات المدعومة بحثياً:
        - 'healthy': سكر مستقر بين 80-120 mg/dL
        - 'type_2': سكر مرتفع مع تذبذب حاد بعد الوجبات 140-280 mg/dL
        - 'hypo_prone': مريض معرض لنوبات هبوط حاد مفاجئ
        """
        self.patient_id = patient_id
        self.profile = profile
        self.backend_url = "http://127.0.0.1:8000/glucose/stream"
        self.event_url = "http://127.0.0.1:8000/glucose/event"
        
        # تحديد نقطة البداية الفسيولوجية لكل مريض
        self.current_glucose = {
            "healthy": 95.0,
            "type_2": 150.0,
            "hypo_prone": 85.0
        }.get(profile, 100.0)
        
        self.time_step = 0
        self.active_events = []

    def inject_behavioral_event(self, event_type: str, details: dict):
        """حقن حدث سلوكي (وجبة، إنسولين، رياضة) في المحاكي لإحداث تغير ديناميكي"""
        print(f"\n[Simulator] Injected Event locally: {event_type} with details {details}")
        self.active_events.append({
            "type": event_type,
            "details": details,
            "elapsed_time": 0
        })
        
        # إرسال الحدث إلى السيرفر أيضاً ليعلمه وكيل السلوك (Behavior Agent)
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
        """محاكاة رياضية حيوية لحركة الجلوكوز (Physiological Modeling)"""
        self.time_step += 1
        
        # تذبذب يومي طبيعي خفيف (Sine Wave) + نويز عشوائي محاكي للواقع
        circadian_wave = 4 * math.sin(self.time_step / 6)
        noise = random.uniform(-2.0, 2.0)
        
        dynamic_change = 0.0
        
        # معالجة الأحداث النشطة وتأثيراتها المنحنية (Pharmacokinetics Approximation)
        for event in self.active_events[:]:
            event["elapsed_time"] += 5  # نعتبر أن كل قراءة تمثل مرور 5 دقائق حيوية
            t = event["elapsed_time"]
            
            if event["type"] == "meal":
                carbs = event["details"].get("carbs_g", 50)
                # منحنى ارتفاع الأكل يبلغ ذروته عند 60 دقيقة وينتهي عند 120 دقيقة
                if t <= 120:
                    dynamic_change += (carbs / 8) * math.sin(math.pi * t / 120)
                else:
                    self.active_events.remove(event)
                    
            elif event["type"] == "insulin":
                units = event["details"].get("units", 5)
                # منحنى هبوط الإنسولين السريع يبلغ ذروته وينتهي بعد 180 دقيقة
                if t <= 180:
                    dynamic_change -= (units * 2.2) * math.sin(math.pi * t / 180)
                else:
                    self.active_events.remove(event)
                    
            elif event["type"] == "exercise":
                duration = event["details"].get("duration_min", 30)
                if t <= duration:
                    dynamic_change -= 3.0  # هبوط مستمر أثناء ممارسة الرياضة
                else:
                    self.active_events.remove(event)

        # تحديث القراءة الحالية بدمج كل العوامل الفسيولوجية
        self.current_glucose += circadian_wave + dynamic_change + noise
        
        # حماية الحدود البيولوجية للإنسان (لا يموت برمجياً)
        self.current_glucose = max(35.0, min(self.current_glucose, 450.0))
        return round(self.current_glucose, 1)

    def start_streaming(self, intervals_sec: int = 2):
        """بدء بث القراءات الحية إلى الـ Backend بانتظام وتلقائية"""
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
                    
                    # طباعة تقرير حي فوري في ترمنال المحاكي يوضح ذكاء الوكلاء
                    print(f"⏰ [CGM Sensor] Glucose: {glucose_val} mg/dL | "
                          f"Trend: {analysis.get('computed_trend')} | "
                          f"Predicted: {analysis.get('predicted_glucose_30m')} | "
                          f"Risk: {analysis.get('risk_level')}")
                    
                    if decision.get("action_required"):
                        print(f"   🚨 ALERT [{decision.get('notification_type')}]: {decision.get('clinical_guidance')}")
                        print(f"   🧠 Rationale: {decision.get('rationale')}\n")
                else:
                    print(f"❌ Error from server: {response.status_code}")
            except Exception as e:
                print(f"❌ Connection failed to Backend: {e}")
                
            # محاكاة الأحداث السلوكية تلقائياً عند فترات زمنية معينة لإثبات القوة البحثية للوكلاء
            if self.time_step == 3:
                # عند القراءة الثالثة، يتناول المريض وجبة كربوهيدرات
                self.inject_behavioral_event("meal", {"carbs_g": 60})
            elif self.time_step == 10 and self.profile == "type_2":
                # عند القراءة العاشرة، يحقن إنسولين لتصحيح الارتفاع الناتج عن الوجبة
                self.inject_behavioral_event("insulin", {"units": 8})

            time.sleep(intervals_sec)

if __name__ == "__main__":
    # تشغيل المحاكي لمريض من النوع الثاني (Type 2 Diabetes)
    # يمكنك تغيير الـ profile إلى 'healthy' أو 'hypo_prone' لمراقبة اختلاف قرارات الوكلاء!
    simulator = AdvancedCGMSimulator(patient_id="patient_fadi_01", profile="type_2")
    simulator.start_streaming(intervals_sec=3)