# RescueMind System Architecture

## 1. System Overview

**RescueMind: Twin Cities Animal Rescue Intelligence and Dispatch Simulator** is built using a clean, modular, layered architecture that strictly decouples the AI algorithms and domain logic from the Streamlit presentation layer.

The architecture follows domain-driven design and dependency injection principles, ensuring that algorithms can be tested, evaluated, and executed in headless environments (e.g., standard CLI or automated pytest pipelines) without any dependence on Streamlit or web session state.

---

## 2. Component Architecture Diagram

```mermaid
flowchart TD
    subgraph Presentation_Layer["Presentation Layer (Streamlit & Folium)"]
        UI_Dash["Operations Dashboard\n(KPIs, Queues, Map Preview)"]
        UI_Map["Interactive Map View\n(Folium Road Network & Units)"]
        UI_Inc["Incident Registry & Intake\n(Table, Form, NL Extraction)"]
        UI_Disp["Dispatch Center\n(CSP, B&B, Replan Diffs)"]
        UI_Lab["AI Search & Benchmark Lab\n(BFS, DFS, UCS, A*, Greedy)"]
        UI_Set["Settings & Scenario Controls\n(Disruption Injector, Weights)"]
    end

    subgraph Coordination_Services["Service & State Layer"]
        SimService["SimulationService\n(Clock, Scenario Lifecycle, NL Intake)"]
        IncService["IncidentService\n(Registry, Priority Rebuilding)"]
        DispService["DispatchService\n(Planning Horizon, Replan Coordinator)"]
        RouteService["RoutingService\n(Road Graph, Road Closures, Detours)"]
        MetricsService["MetricsService\n(KPIs, Benchmark Comparison)"]
        ExplService["ExplanationService\n(Evidence-Based Rationale Generator)"]
    end

    subgraph AI_Algorithms["Core AI Algorithms Layer (Independent / Pure Python)"]
        Graph["RoadGraph\n(Weighted Topology, Disruption State)"]
        Search["Search Algorithms\n(BFS, DFS, UCS, A*, Greedy)"]
        Priority["IncidentPriorityQueue\n(Multi-Factor Min-Heap Score)"]
        CSP["RescueTeamCSP\n(MRV, Forward Checking, Constraints)"]
        BnB["BranchAndBoundAssigner\n(Lower-Bound Pruning, Cost Optimizer)"]
    end

    subgraph Domain_Models["Domain Models Layer"]
        M_Inc["Incident & IncidentStatus"]
        M_Team["RescueTeam & TeamStatus"]
        M_Road["GraphNode & RoadEdge"]
        M_Disp["RouteResult & DispatchPlan"]
    end

    subgraph Data_Layer["Data & Persistence"]
        D_Inc["incidents.json"]
        D_Team["teams.json"]
        D_Road["roads.json"]
        D_Scen["scenarios.json"]
    end

    %% Dependencies
    Presentation_Layer --> Coordination_Services
    Coordination_Services --> AI_Algorithms
    Coordination_Services --> Domain_Models
    AI_Algorithms --> Domain_Models
    Coordination_Services --> Data_Layer
```

---

## 3. Data Flow & Dispatch Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor Operator as Operations Coordinator
    participant UI as Dashboard / Dispatch View
    participant Coordinator as DispatchService
    participant PriorityQ as IncidentPriorityQueue
    participant Solver as RescueTeamCSP / B&B Optimizer
    participant Router as RoutingService (A* / UCS)
    participant Explainer as ExplanationService

    Operator->>UI: Request Dispatch Cycle
    UI->>Coordinator: run_dispatch_cycle()
    Coordinator->>PriorityQ: recompute_priorities()
    PriorityQ-->>Coordinator: Ranked active incidents
    Coordinator->>Coordinator: Slice to Planning Horizon (Top N)
    Coordinator->>Solver: solve(target_incidents, available_teams)
    Solver->>Solver: Audit hard constraints (Skills, Capacity, Availability)
    Solver-->>Coordinator: Valid incident-team assignment
    loop For each assigned pair
        Coordinator->>Router: calculate_route(team_location, incident_location)
        Router-->>Coordinator: Optimal path, cost, hops, step trace
        Coordinator->>Explainer: explain_assignment(incident, team, route)
        Explainer-->>Coordinator: Human-readable rationale
    end
    Coordinator-->>UI: Complete DispatchPlan (Assignments, Unassigned, Diffs)
    UI-->>Operator: Display Plan, Visual Map Paths & Rationale
```

---

## 4. Architectural Guarantees & Modularity

1. **Separation of Presentation and Algorithms:**
   - No algorithmic logic (queues, BFS/UCS traversals, backtracking, lower-bound pruning) resides in the `ui/` directory.
   - Algorithms in `rescuemind/algorithms/` import only standard library modules and domain models.
2. **Deterministic Reproducibility:**
   - Tie-breaking in priority queues and CSP candidate ordering is strictly deterministic (using creation sequences and stable entity IDs), ensuring repeatable viva demonstrations.
3. **Graceful Degradation:**
   - If map tiles fail to load (e.g. offline environment), the application provides tabular route representations and network node connectivity lists.
4. **Offline Operation:**
   - The entire system operates 100% offline without API keys, cloud databases, or paid model services.
