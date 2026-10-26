# RescueMind: Twin Cities Animal Rescue Intelligence & Dispatch Simulator

> **An interactive, modular, explainable Artificial Intelligence university project modeling autonomous animal rescue coordination, constraint satisfaction, and multi-algorithm route optimization in the Islamabad–Rawalpindi metropolitan area.**

---

## 1. Project Summary & Problem Statement

Animal welfare non-profit organizations operating in dense metropolitan areas routinely receive more distress calls than their limited fleets can immediately dispatch. Incidents vary drastically by:
- **Urgency** (minor injuries vs. life-threatening entrapments).
- **Specialized skill requirements** (veterinary surgery, wildlife handling, water rescue, or aggressive restraint).
- **Geographic distribution and transit impediments** (congested arteries, flash floods, or infrastructure roadblocks).

**RescueMind** is an academic decision-support and dispatch simulation platform that demonstrates how transparent, resource-aware Artificial Intelligence can aid coordinators by:
1. Prioritizing active emergency calls using a multi-factor priority queue.
2. Formulating team dispatch as a formal **Constraint Satisfaction Problem (CSP)** with **Minimum Remaining Values (MRV)** and **Forward Checking**.
3. Optimizing fleet travel costs using **Branch-and-Bound (B&B)** pruning.
4. Comparing route planning across **BFS, DFS, Uniform Cost Search (UCS), A\*, and Greedy Best-First Search**.
5. Autonomously detecting road disruptions, calculating detour detours, and reporting before-and-after cost diffs.
6. Generating evidence-grounded human-readable explanations for every single decision.

> [!IMPORTANT]
> **Academic & Research Simulator Notice:** RescueMind is an educational simulation utilizing synthetic telemetry, simulated incidents, and an abstract 24-node model of Islamabad and Rawalpindi. It does **not** dispatch real-world personnel, connect to emergency services, or provide clinical veterinary triage.

---

## 2. Key Features

- **Multi-Algorithm Route Search Arena:** Manual, zero-library implementations of:
  - **Breadth-First Search (BFS):** Guarantees fewest road hops (unweighted shortest path).
  - **Depth-First Search (DFS):** Educational exploration with deterministic neighbor traversal.
  - **Uniform Cost Search (UCS):** Priority queue min-cost optimization with non-negative edge weights.
  - **A\* Search:** Mathematically optimal pathfinding guided by an admissible geodetic Haversine heuristic ($f(n) = g(n) + h(n)$).
  - **Greedy Best-First Search:** Fast heuristic-only exploration prioritizing spatial proximity $h(n)$.
- **Multi-Factor Priority Scoring:** Configurable scoring queue with transparent contribution breakdowns ($w_{\text{urgency}}$, $w_{\text{wait}}$, $w_{\text{vuln}}$) and deterministic creation-sequence tie-breaking.
- **Formal CSP Team Assignment:** Backtracking solver with Minimum Remaining Values (MRV) and Forward Checking that enforces hard operational constraints:
  - Rescuer availability & vehicle capacity limits.
  - Mandatory skill coverage (e.g. `veterinary_care`, `water_rescue`).
  - Supported species category restrictions.
  - Graph route reachability.
  - Transparent candidate rejection audit logging.
- **Branch-and-Bound Travel Cost Optimization:** Minimizes global fleet travel kilometers with admissible lower-bound pruning, mathematically validated against exhaustive enumeration.
- **Dynamic Disruption & Route Replanning:** Live injection of road closures and traffic congestion multipliers that trigger autonomous detour recalculations and before/after comparisons.
- **Interactive Twin Cities Map:** Integrated Folium map featuring Islamabad-Rawalpindi road networks, team locations, incident severity markers, and animated active routes.
- **Natural Language Incident Intake Assistant:** Rule-based offline transcript parser that converts caller notes into structured draft incident records with Human-in-the-Loop review.
- **100% Offline & Open-Source:** Zero external AI API keys, zero cloud databases, zero telemetry tracking.

---

## 3. Technology Stack

- **Language:** Python 3.12 (compatible with Python 3.11+)
- **Presentation & Web Dashboard:** [Streamlit](https://streamlit.io/)
- **Geographic Mapping:** [Folium](https://python-visualization.github.io/folium/) & [streamlit-folium](https://github.com/randyzwitch/streamlit-folium)
- **Data Manipulation & Metrics:** [Pandas](https://pandas.pydata.org/)
- **Interactive Visualizations:** [Plotly Express & Graph Objects](https://plotly.com/python/)
- **Testing Framework:** [pytest](https://pytest.org/)
- **Core Algorithms:** Pure Python standard library (`heapq`, `collections`, `math`, `time`)

---

## 4. Project Directory Structure

```text
RescueMind/
│
├── app.py                         # Streamlit application entry point
├── Code.py                        # Root launcher shortcut
├── requirements.txt               # Pinned Python package dependencies
├── .gitignore                     # Git hygiene configuration
├── .env.example                   # Local environment variable template
│
├── rescuemind/                    # Core application package
│   ├── algorithms/                # Pure Python AI algorithm implementations
│   │   ├── graph.py               # Weighted RoadGraph with Haversine formula
│   │   ├── search.py              # Manual BFS, DFS, UCS, A*, and Greedy search
│   │   ├── priority.py            # PriorityWeights & IncidentPriorityQueue
│   │   ├── assignment.py          # RescueTeamCSP with MRV & Forward Checking
│   │   ├── optimization.py        # BranchAndBoundAssigner with lower-bound pruning
│   │   └── comparison.py          # Multi-algorithm comparative benchmark harness
│   │
│   ├── models/                    # Data classes and domain validation
│   │   ├── incident.py            # Incident, IncidentStatus, AnimalCategory
│   │   ├── rescue_team.py         # RescueTeam, TeamStatus
│   │   ├── road.py                # GraphNode, RoadEdge
│   │   └── dispatch.py            # RouteResult, DispatchAssignment, DispatchPlan
│   │
│   ├── services/                  # Business coordination and orchestration
│   │   ├── incident_service.py    # Incident registry, priority queue rebuild
│   │   ├── routing_service.py     # Graph management, closures, detours
│   │   ├── dispatch_service.py    # Planning horizon, CSP/B&B coordinator, replanner
│   │   ├── explanation_service.py # Evidence-based explanation generator
│   │   ├── metrics_service.py     # KPIs, distribution statistics, comparisons
│   │   └── simulation_service.py  # Simulation lifecycle, clock, scenarios, NL intake
│   │
│   ├── data/                      # Synthetic data files
│   │   ├── roads.json             # 24-node Islamabad-Rawalpindi road network
│   │   ├── teams.json             # 5 specialized rescue teams & equipment profiles
│   │   ├── incidents.json         # 7 synthetic active animal emergency calls
│   │   └── scenarios.json         # 4 operational demonstration scenarios
│   │
│   ├── ui/                        # Modular Streamlit view components
│   │   ├── dashboard.py           # Operations Overview dashboard & KPI cards
│   │   ├── map_view.py            # Interactive Folium map renderer
│   │   ├── incident_views.py      # Incident registry, editing form, NL intake
│   │   ├── dispatch_views.py      # Dispatch center, candidate rejections, replan diffs
│   │   ├── analytics_views.py     # AI Lab, algorithm comparison, Plotly charts
│   │   └── settings_view.py       # Scenarios, road disruption injector, weight tuning
│   │
│   └── utils/                     # Shared constants and validation logic
│       ├── constants.py           # Defaults, coordinates, skills, disclaimer
│       └── validators.py          # Coordinates, non-negative weights, ID checks
│
├── tests/                         # Automated pytest suite (33 tests, 100% pass)
│   ├── test_graph.py              # Road graph topology and edge weight tests
│   ├── test_search.py             # BFS, DFS, UCS, A*, Greedy search tests
│   ├── test_priority.py           # Priority queue scoring and tie-breaking tests
│   ├── test_assignment.py         # CSP hard constraints and capacity tests
│   ├── test_optimization.py       # Branch-and-Bound vs exhaustive brute force
│   ├── test_simulation.py         # Time advancement and scenario loading
│   └── test_integration.py        # End-to-end dispatch and replan workflows
│
└── docs/                          # University presentation & viva documentation
    ├── architecture.md            # Component diagrams & data flow (Mermaid)
    ├── algorithms_explained.md    # Detailed mathematical proofs and complexity
    ├── testing.md                 # Test matrix, coverage, and execution report
    ├── viva_questions.md          # 27 likely viva questions and model answers
    ├── demo_script.md             # Step-by-step 5-minute presentation script
    └── IMPLEMENTATION_STATUS.md   # Engineering milestone tracking log
```

---

## 5. Installation & Setup Instructions (Windows PowerShell)

Follow these exact steps in PowerShell to set up and run RescueMind:

### Step 1: Open PowerShell in the Project Directory
```powershell
cd "c:\Users\alifo\Downloads\AI Lab Mid"
```

### Step 2: Create a Python Virtual Environment
```powershell
py -3.12 -m venv .venv
```
*(Or use `python -m venv .venv`)*

### Step 3: Install Required Dependencies
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

---

## 6. How to Run the Automated Test Suite

To verify all algorithms, constraints, and integration flows:
```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

**Expected Outcome:**
```text
============================= 33 passed in 0.34s ==============================
```

---

## 7. How to Launch the Web Application

Launch the Streamlit interactive dashboard:
```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Once executed, open your web browser to:
👉 **`http://localhost:8501`**

---

## 8. Five-Minute University Demonstration Sequence

1. **Overview:** Open the main dashboard to inspect active requests, available rescue teams, and the live Folium map.
2. **Rescue Operations:** Unified operations screen containing the prominent live map, current rescue plan assignments and routes, requests registry, distress call logging (with Natural Language intake assistant), fleet roster, and road disruption controls.
3. **AI Lab:** Navigate to **"AI Lab"**, select Start: `F6_SUPER` and Goal: `ZERO_POINT`. Click **"Compare Routes"** to demonstrate that BFS picks the 2-hop route with higher cost (12.0 km), while UCS and A\* pick the 3-hop route with lower cost (5.4 km). Inspect step-by-step search traces in clean expanders.
4. **Insights & Settings:** View real-time urgency distribution charts, algorithm efficiency charts, predefined scenario controls (e.g. Faizabad disruption or monsoon congestion), and priority policy weight sliders.


---

## 9. Predefined Demonstration Scenarios

RescueMind includes four predefined scenarios in `rescuemind/data/scenarios.json`:
1. **Twin Cities Morning Baseline (`SCENARIO_DEFAULT`):** Standard morning conditions with all corridors open and balanced queues.
2. **Faizabad Gateway Disruption (`SCENARIO_FAIZABAD_CLOSURE`):** Central arterial link severed between Islamabad and Rawalpindi; forces teams to detour via I-8 or Expressway.
3. **High Urgency Skill Shortage (`SCENARIO_RESOURCE_EXHAUSTION`):** Multiple simultaneous wildlife and avian distress calls designed to test CSP rejection diagnostics and capacity bottlenecks.
4. **Monsoon Flash Rainstorm Congestion (`SCENARIO_HIGH_CONGESTION`):** Major routes experience 2.5x traffic congestion multipliers, shifting optimal routing choices.

---

## 10. Capturing Actual Application Screenshots

To include visual documentation in university submissions or reports:
1. Start the application (`.\.venv\Scripts\python.exe -m streamlit run app.py`).
2. Use **Windows Snipping Tool** (`Windows Key + Shift + S`) to capture:
   - `docs/screenshots/overview_dashboard.png`: The Operations Overview showing KPIs and the Folium map.
   - `docs/screenshots/ai_lab_comparison.png`: The Search Algorithm comparison table and A\* step trace.
   - `docs/screenshots/dispatch_rejections.png`: The Candidate Team Rejections audit log in the Dispatch Center.
   - `docs/screenshots/replan_comparison.png`: The Before-and-After route comparison after blocking a road.

---

## 11. Known Limitations & Responsible AI Notice

- **Synthetic Topology:** The 24-node network models key transit hubs in Islamabad and Rawalpindi for demonstration purposes and is not a complete road GIS map.
- **Complexity Horizon:** Branch-and-Bound has worst-case exponential complexity with large numbers of unassigned incidents; RescueMind bounds this cleanly via a configurable planning horizon (default 5 incidents).
- **Human Oversight:** The platform is an autonomous recommendation engine designed to empower human operators, not replace them.
- **Triage Scope:** Priority scores are operational dispatch scheduling heuristics, not certified veterinary medical diagnoses.
