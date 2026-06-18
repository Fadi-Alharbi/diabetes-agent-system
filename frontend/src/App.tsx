import { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceArea, AreaChart, Area
} from 'recharts';
import {
  Activity, Droplet, HeartPulse, AlertCircle, Apple, Users,
  Shield, TrendingUp, Clock, Zap, Settings, BarChart3, Brain
} from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8000';

// ═══════════════════════════════════════════════════════════════
//  Main App Component
// ═══════════════════════════════════════════════════════════════

export default function App() {
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [overviewData, setOverviewData] = useState<any[]>([]);
  const [sensorStatuses, setSensorStatuses] = useState<any[]>([]);
  const [lang, setLang] = useState<'ar' | 'en'>('ar');
  const [fullAnalysis, setFullAnalysis] = useState<any>(null);
  const [isConnected, setIsConnected] = useState(false);

  // ─── Fetch overview data ───
  useEffect(() => {
    const fetchOverview = async () => {
      try {
        const [overviewRes, sensorRes] = await Promise.all([
          fetch(`${API_BASE}/patients/all/overview`),
          fetch(`${API_BASE}/sensor/status`)
        ]);
        const oData = await overviewRes.json();
        const sData = await sensorRes.json();
        setOverviewData(oData.patients || []);
        setSensorStatuses(sData.sensors || []);
        setIsConnected(true);
      } catch {
        setIsConnected(false);
      }
    };
    fetchOverview();
    const interval = setInterval(fetchOverview, 5000);
    return () => clearInterval(interval);
  }, []);

  // ─── Fetch patient data when tab changes ───
  useEffect(() => {
    if (!activeTab.startsWith('patient_')) {
      setDashboardData(null);
      setFullAnalysis(null);
      return;
    }
    const pid = activeTab.replace('patient_', '');
    const fetchPatient = async () => {
      try {
        const [dashRes, analysisRes] = await Promise.all([
          fetch(`${API_BASE}/patients/${pid}/dashboard`),
          fetch(`${API_BASE}/patients/${pid}/full-analysis`)
        ]);
        const dData = await dashRes.json();
        const aData = await analysisRes.json();
        if (dData.status === 'active' || dData.status === 'stopped') {
          setDashboardData(dData);
        }
        setFullAnalysis(aData.full_analysis || null);
      } catch (e) {
        console.error('Fetch error', e);
      }
    };
    fetchPatient();
    const interval = setInterval(fetchPatient, 3000);
    return () => clearInterval(interval);
  }, [activeTab]);

  // ═══════════════════════════════════════════════════════════════
  //  Overview Page
  // ═══════════════════════════════════════════════════════════════

  const renderOverview = () => (
    <div>
      <header className="header">
        <div>
          <h2>🏥 {lang === 'ar' ? 'نظرة عامة على المرضى' : 'Patient Overview'}</h2>
          <p>{lang === 'ar' ? 'مراقبة حية لجميع المرضى عبر الحساسات الافتراضية' : 'Live monitoring of all patients via virtual sensors'}</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div className="lang-toggle">
            <button className={`lang-btn ${lang === 'ar' ? 'active' : ''}`} onClick={() => setLang('ar')}>عربي</button>
            <button className={`lang-btn ${lang === 'en' ? 'active' : ''}`} onClick={() => setLang('en')}>EN</button>
          </div>
          <span className={`badge ${isConnected ? 'safe' : 'danger'}`}>
            {isConnected ? (lang === 'ar' ? '● متصل' : '● Connected') : (lang === 'ar' ? '○ غير متصل' : '○ Disconnected')}
          </span>
        </div>
      </header>

      <div className="grid-3" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
        {overviewData.map((p: any) => (
          <div
            key={p.patient_id}
            className={`glass-card overview-patient-card ${p.riskClass}`}
            onClick={() => setActiveTab(`patient_${p.patient_id}`)}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>
                {lang === 'ar' ? p.name_ar : p.name}
              </h3>
              <span className={`badge ${p.riskClass}`}>{p.risk}</span>
            </div>
            <div className="metric-value" style={{ fontSize: '2rem' }}>
              {p.glucose ? `${p.glucose}` : '—'}
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginLeft: '4px' }}>mg/dL</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.75rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              <span>{p.trend || 'STABLE'}</span>
              <span>TIR: {p.tir || '—'}</span>
            </div>
            <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              {p.status === 'active' && <><span className="sensor-dot active" /> {lang === 'ar' ? 'الحساس يعمل' : 'Sensor Active'}</>}
              {p.status !== 'active' && <><span className="sensor-dot stopped" /> {lang === 'ar' ? 'متوقف' : 'Stopped'}</>}
            </div>
          </div>
        ))}
      </div>

      {overviewData.length === 0 && (
        <div className="glass-card" style={{ textAlign: 'center', padding: '3rem' }}>
          <div className="loading-pulse" style={{ margin: '0 auto 1rem' }} />
          <p style={{ color: 'var(--text-secondary)' }}>
            {lang === 'ar' ? 'جاري الاتصال بالسيرفر...' : 'Connecting to server...'}
          </p>
        </div>
      )}
    </div>
  );

  // ═══════════════════════════════════════════════════════════════
  //  Patient Dashboard
  // ═══════════════════════════════════════════════════════════════

  const renderPatient = () => {
    if (!dashboardData || dashboardData.status === 'no_data') {
      return (
        <div className="glass-card" style={{ textAlign: 'center', padding: '3rem' }}>
          <div className="loading-pulse" style={{ margin: '0 auto 1rem' }} />
          <p style={{ color: 'var(--text-secondary)' }}>
            {lang === 'ar' ? 'جاري تحميل بيانات المريض...' : 'Loading patient data...'}
          </p>
        </div>
      );
    }

    const d = dashboardData;
    const a = fullAnalysis || {};

    return (
      <>
        {/* Header */}
        <header className="header">
          <div>
            <h2 style={{ fontSize: '1.75rem', fontWeight: 700 }}>
              {lang === 'ar' ? (d.name_ar || d.name) : d.name}
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              {lang === 'ar' ? (d.description_ar || d.description) : d.description}
              {' · '}
              {lang === 'ar' ? 'حساس افتراضي' : 'Virtual Sensor'}
              {d.status === 'active' && <> · <span className="sensor-dot active" style={{ verticalAlign: 'middle' }} /></>}
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div className="lang-toggle">
              <button className={`lang-btn ${lang === 'ar' ? 'active' : ''}`} onClick={() => setLang('ar')}>عربي</button>
              <button className={`lang-btn ${lang === 'en' ? 'active' : ''}`} onClick={() => setLang('en')}>EN</button>
            </div>
            <span className={`badge ${d.riskClass}`}>{d.risk}</span>
          </div>
        </header>

        {/* Metrics Row */}
        <div className="grid-3" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
          <div className="glass-card">
            <div className="metric-label" style={{ color: 'var(--accent-color)' }}>
              <Droplet size={18} /> {lang === 'ar' ? 'السكر الحالي' : 'Current Glucose'}
            </div>
            <div className="metric-value">{d.glucose} <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>mg/dL</span></div>
            <p style={{ color: d.trendColor, marginTop: '0.4rem', fontWeight: 600, fontSize: '0.85rem' }}>{d.trendText}</p>
          </div>

          <div className="glass-card">
            <div className="metric-label" style={{ color: 'var(--purple)' }}>
              <Activity size={18} /> {lang === 'ar' ? 'التنبؤ (30 دقيقة)' : 'Predicted (30m)'}
            </div>
            <div className="metric-value">{d.pred30 || '—'} <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>mg/dL</span></div>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.4rem', fontSize: '0.8rem' }}>
              {lang === 'ar' ? `الثقة: ${d.predictionConfidence || '—'}` : `Confidence: ${d.predictionConfidence || '—'}`}
            </p>
          </div>

          <div className="glass-card">
            <div className="metric-label" style={{ color: 'var(--success)' }}>
              <HeartPulse size={18} /> {lang === 'ar' ? 'الوقت في النطاق' : 'Time in Range'}
            </div>
            <div className="metric-value">{d.tir}</div>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.4rem', fontSize: '0.8rem' }}>
              {lang === 'ar' ? 'النطاق: 70-180 mg/dL' : 'Range: 70-180 mg/dL'}
            </p>
          </div>

          <div className="glass-card">
            <div className="metric-label" style={{ color: 'var(--warning)' }}>
              <Shield size={18} /> {lang === 'ar' ? 'مستوى الخطورة' : 'Risk Level'}
            </div>
            <div className="metric-value" style={{ fontSize: '1.5rem', color: d.riskClass === 'safe' ? 'var(--success)' : d.riskClass === 'critical' ? 'var(--danger)' : 'var(--warning)' }}>
              {d.risk}
            </div>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.4rem', fontSize: '0.8rem' }}>
              {lang === 'ar' ? `السرعة: ${d.velocity} mg/dL/min` : `Velocity: ${d.velocity} mg/dL/min`}
            </p>
          </div>
        </div>

        {/* Chart */}
        <div className="glass-card" style={{ marginBottom: '1.5rem', height: '350px' }}>
          <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '1rem' }}>
            <TrendingUp size={18} style={{ color: 'var(--accent-color)' }} />
            {lang === 'ar' ? 'المنحنى الحركي والتنبؤ' : 'Glucose Trajectory & Prediction'}
          </h3>
          <ResponsiveContainer width="100%" height="85%">
            <LineChart data={d.chart || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="time" stroke="var(--text-secondary)" fontSize={11} />
              <YAxis domain={[40, 350]} stroke="var(--text-secondary)" fontSize={11} />
              <Tooltip
                contentStyle={{ backgroundColor: 'var(--surface-color)', border: '1px solid var(--border-color)', borderRadius: '10px', color: 'white', fontSize: '0.85rem' }}
              />
              <ReferenceArea y1={70} y2={180} fill="var(--success)" fillOpacity={0.06} />
              <Line type="monotone" dataKey="glucose" stroke="var(--accent-color)" strokeWidth={3} dot={{ fill: 'var(--accent-color)', r: 4 }} activeDot={{ r: 6 }} connectNulls={false} />
              <Line type="monotone" dataKey="pred" stroke="var(--purple)" strokeWidth={3} strokeDasharray="6 4" dot={{ fill: 'var(--purple)', r: 4 }} connectNulls={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Severity Explanation */}
        {d.severityExplanation && (
          <div className={`advice-card ${d.riskClass === 'safe' ? 'safe' : d.riskClass === 'critical' ? 'critical' : d.riskClass === 'danger' ? 'critical' : 'warning'}`} style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Zap size={18} />
              {lang === 'ar' ? 'شرح الحالة' : 'Status Explanation'}
            </h3>
            <p style={{ fontSize: '0.9rem', lineHeight: 1.8, direction: lang === 'ar' ? 'rtl' : 'ltr', textAlign: lang === 'ar' ? 'right' : 'left', fontFamily: lang === 'ar' ? "'Tajawal', sans-serif" : "'Inter', sans-serif" }}>
              {d.severityExplanation}
            </p>
          </div>
        )}

        <div className="grid-2">
          {/* Medical Advice + Action Steps */}
          <div>
            {/* Advice Card */}
            {d.patientAdvice && d.patientAdvice.title && (
              <div className={`advice-card ${d.riskClass === 'safe' ? 'safe' : d.riskClass === 'critical' ? 'critical' : d.riskClass === 'danger' ? 'critical' : 'warning'}`}>
                <h3 style={{ marginBottom: '0.75rem', fontSize: '1.05rem' }}>
                  {lang === 'ar' ? d.patientAdvice.title : d.patientAdvice.title_en}
                </h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1rem', direction: lang === 'ar' ? 'rtl' : 'ltr', textAlign: lang === 'ar' ? 'right' : 'left', fontFamily: lang === 'ar' ? "'Tajawal', sans-serif" : "'Inter', sans-serif" }}>
                  {lang === 'ar' ? d.patientAdvice.guidance_ar : d.patientAdvice.guidance_en}
                </p>
                {d.patientAdvice.contextual_note_ar && (
                  <p style={{ fontSize: '0.8rem', color: 'var(--accent-color)', marginTop: '0.5rem', direction: lang === 'ar' ? 'rtl' : 'ltr' }}>
                    💡 {lang === 'ar' ? d.patientAdvice.contextual_note_ar : d.patientAdvice.contextual_note_en}
                  </p>
                )}
              </div>
            )}

            {/* Action Steps */}
            {d.actionSteps && d.actionSteps.length > 0 && (
              <div className="advice-card info">
                <h3 style={{ marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <AlertCircle size={18} />
                  {lang === 'ar' ? '📋 خطوات عملية' : '📋 Action Steps'}
                </h3>
                <ul className="action-steps" style={{ direction: lang === 'ar' ? 'rtl' : 'ltr', textAlign: lang === 'ar' ? 'right' : 'left', fontFamily: lang === 'ar' ? "'Tajawal', sans-serif" : "'Inter', sans-serif" }}>
                  {(lang === 'ar' ? d.actionSteps : (a.action_steps_en || d.actionSteps)).map((step: string, i: number) => (
                    <li key={i}>{step}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Right Column: Prediction + Prevention + Meal */}
          <div>
            {/* Prediction Narrative */}
            {(d.predictionNarrativeAr || a.prediction_narrative_ar) && (
              <div className="advice-card info" style={{ marginBottom: '1.25rem' }}>
                <h3 style={{ marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Brain size={18} style={{ color: 'var(--purple)' }} />
                  {lang === 'ar' ? '🔮 سرد التنبؤ' : '🔮 Prediction Narrative'}
                </h3>
                <div className={`narrative-block ${lang === 'en' ? 'en' : ''}`}>
                  {lang === 'ar'
                    ? (d.predictionNarrativeAr || a.prediction_narrative_ar)
                    : (d.predictionNarrativeEn || a.prediction_narrative_en)
                  }
                </div>
              </div>
            )}

            {/* Prevention Tips */}
            {d.preventionTips && d.preventionTips.length > 0 && (
              <div className="advice-card safe" style={{ marginBottom: '1.25rem' }}>
                <h3 style={{ marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Shield size={18} style={{ color: 'var(--success)' }} />
                  {lang === 'ar' ? '🛡️ نصائح وقائية' : '🛡️ Prevention Tips'}
                </h3>
                <div style={{ direction: lang === 'ar' ? 'rtl' : 'ltr', textAlign: lang === 'ar' ? 'right' : 'left', fontFamily: lang === 'ar' ? "'Tajawal', sans-serif" : "'Inter', sans-serif" }}>
                  {(lang === 'ar' ? d.preventionTips : (a.prevention_tips_en || d.preventionTips)).map((tip: string, i: number) => (
                    <div key={i} className="prevention-tip">{tip}</div>
                  ))}
                </div>
              </div>
            )}

            {/* Meal Suggestion */}
            {d.nextMealSuggestion && (
              <div className="advice-card warning">
                <h3 style={{ marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Apple size={18} style={{ color: 'var(--warning)' }} />
                  {lang === 'ar' ? '🍽️ اقتراح الوجبة' : '🍽️ Meal Suggestion'}
                </h3>
                <p style={{ fontSize: '0.9rem', direction: lang === 'ar' ? 'rtl' : 'ltr', textAlign: lang === 'ar' ? 'right' : 'left', fontFamily: lang === 'ar' ? "'Tajawal', sans-serif" : "'Inter', sans-serif" }}>
                  {lang === 'ar' ? d.nextMealSuggestion : (a.next_meal_suggestion_en || d.nextMealSuggestion)}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Behavioral Insight */}
        {d.insight && (
          <div className="glass-card" style={{ marginTop: '1rem' }}>
            <h3 style={{ marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <BarChart3 size={18} style={{ color: 'var(--accent-color)' }} />
              {lang === 'ar' ? '🧠 تحليل سلوكي' : '🧠 Behavioral Insight'}
            </h3>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', direction: lang === 'ar' ? 'rtl' : 'ltr', fontFamily: lang === 'ar' ? "'Tajawal', sans-serif" : "'Inter', sans-serif" }}>
              {d.insight}
            </p>
          </div>
        )}
      </>
    );
  };

  // ═══════════════════════════════════════════════════════════════
  //  Settings Page
  // ═══════════════════════════════════════════════════════════════

  const renderSettings = () => (
    <div>
      <h2 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '1rem' }}>
        {lang === 'ar' ? '⚙️ إعدادات النظام' : '⚙️ System Settings'}
      </h2>
      <div className="grid-2">
        <div className="glass-card">
          <h3 style={{ marginBottom: '1rem' }}>{lang === 'ar' ? 'حالة الحساسات' : 'Sensor Status'}</h3>
          {sensorStatuses.map((s: any) => (
            <div key={s.patient_id} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid var(--border-color)' }}>
              <span>Patient {s.patient_id} ({s.profile_type})</span>
              <span className={`badge ${s.is_running ? 'safe' : 'danger'}`}>
                {s.is_running ? (lang === 'ar' ? 'يعمل' : 'Running') : (lang === 'ar' ? 'متوقف' : 'Stopped')}
              </span>
            </div>
          ))}
        </div>
        <div className="glass-card">
          <h3 style={{ marginBottom: '1rem' }}>{lang === 'ar' ? 'إعدادات الاتصال' : 'Connection Settings'}</h3>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', color: 'var(--text-secondary)', marginBottom: '0.3rem', fontSize: '0.85rem' }}>FastAPI Backend URL</label>
            <input type="text" value={API_BASE} readOnly style={{ width: '100%', padding: '0.5rem', background: 'var(--surface-color)', border: '1px solid var(--border-color)', color: 'white', borderRadius: '8px', fontSize: '0.85rem' }} />
          </div>
          <div>
            <label style={{ display: 'block', color: 'var(--text-secondary)', marginBottom: '0.3rem', fontSize: '0.85rem' }}>
              {lang === 'ar' ? 'الإطار: LangGraph + Virtual Sensor' : 'Framework: LangGraph + Virtual Sensor'}
            </label>
          </div>
        </div>
      </div>
    </div>
  );

  // ═══════════════════════════════════════════════════════════════
  //  Render
  // ═══════════════════════════════════════════════════════════════

  const renderContent = () => {
    if (activeTab === 'overview') return renderOverview();
    if (activeTab === 'settings') return renderSettings();
    if (activeTab.startsWith('patient_')) return renderPatient();
    return renderOverview();
  };

  const patientIds = ['A', 'B', 'C', 'D', 'E'];
  const patientLabels: Record<string, { en: string; ar: string }> = {
    A: { en: 'Patient A (High Carb)', ar: 'المريض أ (كربوهيدرات عالية)' },
    B: { en: 'Patient B (Active)', ar: 'المريض ب (نشط بدنياً)' },
    C: { en: 'Patient C (Hypo-Prone)', ar: 'المريض ج (هبوط متكرر)' },
    D: { en: 'Patient D (Irregular)', ar: 'المريض د (وجبات غير منتظمة)' },
    E: { en: 'Patient E (Poor Adherence)', ar: 'المريض هـ (التزام ضعيف)' },
  };

  return (
    <div className="dashboard-container">
      <aside className="sidebar">
        <h1>🩺 IMDCS Core</h1>
        <nav>
          <div
            className={`nav-item ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            <Users size={16} /> {lang === 'ar' ? 'نظرة عامة' : 'Overview'}
          </div>

          <div className="nav-section-label">
            <Users size={12} /> {lang === 'ar' ? 'المرضى' : 'Patients'}
          </div>

          {patientIds.map(pid => {
            const sensor = sensorStatuses.find((s: any) => s.patient_id === pid);
            const isRunning = sensor?.is_running;
            return (
              <div
                key={pid}
                className={`nav-item ${activeTab === `patient_${pid}` ? 'active' : ''}`}
                onClick={() => setActiveTab(`patient_${pid}`)}
              >
                {lang === 'ar' ? patientLabels[pid].ar : patientLabels[pid].en}
                <span className={`sensor-dot ${isRunning ? 'active' : 'stopped'}`} />
              </div>
            );
          })}

          <div style={{ marginTop: '1.5rem' }} />
          <div
            className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            <Settings size={16} /> {lang === 'ar' ? 'الإعدادات' : 'Settings'}
          </div>
        </nav>
      </aside>

      <main className="main-content">
        {renderContent()}
      </main>
    </div>
  );
}
