# IMDCS System Architecture & UML

## 1. High-Level Architecture

The system utilizes a microservices-inspired multi-agent architecture orchestrated by LangGraph.

```mermaid
graph TD
    subgraph Data Sources
        CGM[CGM Simulator]
        Events[Behavioral Inputs: Meals/Insulin]
    end

    subgraph FastAPI Backend
        API[REST API Endpoints]
        LG[LangGraph Orchestrator]
    end

    subgraph Multi-Agent Pipeline
        DA[Data Agent]
        TA[Trend Agent]
        PA[Prediction Agent - ML]
        FA[Food Impact Agent]
        BA[Behavior Agent]
        RA[Risk Agent]
        MA[Meta Decision Agent]
    end

    subgraph Persistence & AI
        DB[(PostgreSQL)]
        SHAP[SHAP Explainer]
    end

    subgraph Frontend
        React[React + Vite Dashboard]
    end

    CGM -->|Glucose Stream| API
    Events -->|Event Stream| API
    API --> LG
    LG --> DA --> TA --> PA --> FA --> BA --> RA --> MA
    PA <--> SHAP
    MA --> DB
    API <--> React
```

## 2. Sequence Diagram: Data Ingestion to Decision

```mermaid
sequenceDiagram
    participant Sensor as CGM Sensor
    participant API as FastAPI
    participant LG as LangGraph
    participant Agents as Core Agents
    participant ML as XGBoost Model
    participant Meta as Meta Decision Agent
    participant DB as PostgreSQL

    Sensor->>API: POST /glucose/stream
    API->>LG: invoke(initial_state)
    LG->>Agents: Route to Data & Trend Agents
    Agents->>LG: Update Velocity & Trend
    LG->>Agents: Route to Prediction Agent
    Agents->>ML: Predict 30m Horizon
    ML-->>Agents: Predicted Value + SHAP Values
    LG->>Agents: Route to Risk & Behavior Agents
    Agents->>LG: Classify Risk Level
    LG->>Meta: Aggregate State
    Meta->>Meta: Generate Clinical Guidance & Rationale
    Meta->>DB: Persist Readings, Events, Decisions
    Meta-->>LG: final_decision
    LG-->>API: final_state
    API-->>Sensor: 200 OK + Decision JSON
```

## 3. LangGraph State Flow

```mermaid
stateDiagram-v2
    [*] --> DataAgent
    DataAgent --> TrendAgent: Cleaned Data
    TrendAgent --> PredictionAgent: Velocity & Trend
    PredictionAgent --> FoodImpactAgent: Forecasts (30m, 60m)
    FoodImpactAgent --> BehaviorAgent: Personalized Food Profiles
    BehaviorAgent --> RiskAgent: Activity Insights
    RiskAgent --> MetaDecisionAgent: Risk Classification
    MetaDecisionAgent --> [*]: Actionable Guidance
```
