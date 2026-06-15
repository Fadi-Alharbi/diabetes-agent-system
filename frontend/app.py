import streamlit as st
import httpx
import pandas as pd
import time
from datetime import datetime

# إعدادات الصفحة العامة للوحة التحكم
st.set_page_config(
    page_title="IMDCS - Multi-Agent Dashboard",
    page_icon="🩺",
    layout="wide"
)

# عنوان لوحة التحكم
st.title("🩺 Intelligent Multi-Agent Diabetes Care System (IMDCS)")
st.subheader("Real-Time Physiological Monitoring & Decision Support Dashboard")
st.markdown("---")

# روابط الـ API الخاصة بالـ Backend
BACKEND_URL = "http://127.0.0.1:8000/glucose/stream"
ROOT_URL = "http://127.0.0.1:8000/"

# تهيئة الـ Session State لحفظ قراءات المريض وعرض المنحنى ديناميكياً
if "glucose_history" not in st.session_state:
    st.session_state.glucose_history = []
if "predictions_history" not in st.session_state:
    st.session_state.predictions_history = []
if "timestamps" not in st.session_state:
    st.session_state.timestamps = []
if "alerts_log" not in st.session_state:
    st.session_state.alerts_log = []

# التأكد من اتصال الواجهة بالسيرفر الخلفي
try:
    with httpx.Client() as client:
        server_check = client.get(ROOT_URL, timeout=2.0)
        server_online = server_check.status_code == 200
except Exception:
    server_online = False

if not server_online:
    st.error("❌ Cannot connect to the IMDCS Backend Server. Please ensure 'python -m backend.main' is running on port 8000.")
    st.stop()

# --- الجزء الجانبي (Sidebar) للتحكم بالمحاكاة وضخ البيانات ---
st.sidebar.header("🎯 Patient Profile & Controls")
patient_id = st.sidebar.text_input("Patient ID", value="patient_fadi_01")
simulation_mode = st.sidebar.checkbox("Enable Live Dashboard Polling", value=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🍔 Injected Behavioral Events")
st.sidebar.info("To see behavioral insights, inject events via the simulator terminal while this dashboard is running.")

# --- الجسم الرئيسي للوحة التحكم (Main Layout) ---

# 1. طبقة المؤشرات الرقمية اللحظية (Real-Time Cards Metric Layer)
metric_container = st.container()

# 2. طبقة الرسم البياني وصندوق القرارات والتحذيرات الطبية
col_graph, col_alerts = st.columns([2, 1])

# جلب آخر البيانات المتاحة المعالجة بواسطة الوكلاء من الـ Backend
# ملاحظة: نظراً لأن المحاكي يرسل البيانات تلقائياً، سنقوم هنا بمحاكاة "تنصت وتحديث تلقائي"
if simulation_mode:
    # نقوم بعمل طلب سريع لجلب البيانات المخزنة بالـ Backend أو الاستماع إليها
    # لتسهيل التناغم، سنعرض آخر البيانات المستقرة المحدثة في النظام
    pass

# لإعطاء الواجهة قوة تفاعلية، سنطلب من الطبيب/المستخدم إدخال القراءات يدوياً أيضاً إذا أراد الاختبار الفوري من المتصفح:
st.markdown("### 🧪 Manual Ingestion Testbed (Optional)")
with st.form("manual_stream_form"):
    c1, c2 = st.columns(2)
    with c1:
        manual_glucose = st.number_input("Enter Glucose Value (mg/dL)", min_value=40.0, max_value=400.0, value=120.0, step=5.0)
    with c2:
        st.write("")
        st.write("")
        submit_button = st.form_submit_button("➔ Stream to Multi-Agent Engine")

if submit_button:
    payload = {
        "patient_id": patient_id,
        "timestamp": datetime.utcnow().isoformat(),
        "glucose_value": manual_glucose
    }
    with httpx.Client() as client:
        try:
            res = client.post(BACKEND_URL, json=payload)
            if res.status_code == 200:
                data = res.json()
                analysis = data.get("analysis", {})
                decision = data.get("decision", {})
                
                # حفظ القراءات لتحديث الرسم البياني
                st.session_state.glucose_history.append(manual_glucose)
                st.session_state.predictions_history.append(analysis.get("predicted_glucose_30m"))
                st.session_state.timestamps.append(datetime.now().strftime("%H:%M:%S"))
                
                # حفظ التنبيهات إذا تطلبت فعلاً إشعاراً ولم يتم حجبها
                if decision.get("action_required") or decision.get("is_suppressed_by_agent"):
                    st.session_state.alerts_log.insert(0, {
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "type": decision.get("notification_type"),
                        "guidance": decision.get("clinical_guidance"),
                        "rationale": decision.get("rationale"),
                        "suppressed": decision.get("is_suppressed_by_agent", False)
                    })
                st.success("Data processed by agents successfully!")
            else:
                st.error("Error from Backend core.")
        except Exception as e:
            st.error(f"Failed to connect to backend: {e}")

# --- تحديث وعرض المكونات المرئية بناءً على البيانات المتوفرة ---
if st.session_state.glucose_history:
    latest_g = st.session_state.glucose_history[-1]
    latest_p = st.session_state.predictions_history[-1]
    
    # حساب السهم الحركي للاتجاه
    with httpx.Client() as client:
        # جلب تفاصيل المعالجة الأخيرة لعرضها في بطاقات المؤشرات
        pass

    # تحديث كروت المؤشرات الرقمية (Metrics Display)
    with metric_container:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(label="Current Glucose", value=f"{latest_g} mg/dL")
        m2.metric(label="Predicted (30 Mins)", value=f"{latest_p} mg/dL")
        
        # تلوين مستوى الخطورة ديناميكياً
        m3.metric(label="Target Status", value="Within Range" if 70 <= latest_g <= 180 else "Out of Range")
        m4.metric(label="Monitoring Active Patient", value=patient_id)

    # تحديث الرسم البياني (Physiological Kinetics Plot)
    with col_graph:
        st.markdown("### 📈 Glucose Kinematics (CGM Stream)")
        chart_data = pd.DataFrame({
            "Current Glucose": st.session_state.glucose_history,
            "Predicted Glucose (30m)": st.session_state.predictions_history
        }, index=st.session_state.timestamps)
        st.line_chart(chart_data)

    # تحديث صندوق التنبيهات المفسر (Explainable Alerts Room)
    with col_alerts:
        st.markdown("### 🚨 Multi-Agent Clinical Room")
        if st.session_state.alerts_log:
            for alert in st.session_state.alerts_log:
                if alert["suppressed"]:
                    st.warning(f"⏳ **[ Fatigue Suppressed Alert ]** at {alert['time']}\n\n*System blocked duplicate notification to protect patient focus. Inside background logs: {alert['guidance']}*")
                else:
                    if alert["type"] == "URGENT_ALERT":
                        st.error(f"🔴 **[ CRITICAL ALERT ]** at {alert['time']}\n\n**Guidance:** {alert['guidance']}\n\n**AI Rationale:** {alert['rationale']}")
                    elif alert["type"] == "WARNING":
                        st.warning(f"🟡 **[ WARNING ]** at {alert['time']}\n\n**Guidance:** {alert['guidance']}\n\n**AI Rationale:** {alert['rationale']}")
                st.markdown("---")
        else:
            st.success("🟢 No critical issues flagged by Risk and Decision agents. Metabolism is stable.")
else:
    st.info("👋 Welcome to IMDCS Dashboard! Please stream glucose readings manually using the form below or launch your automated backend simulator to push data live.")