# RescueMind: 5-Minute University Demonstration Script
## Step-by-Step Presentation Guide for Faculty & Evaluators

**Total Duration:** 5 Minutes  
**Objective:** Deliver a confident, high-impact walk-through showing real AI algorithms working in unison across prioritization, constraint satisfaction, route optimization, dynamic disruptions, and explainability.

---

### Minute 0:00 – 0:45 | Introduction & Operations Overview
1. **Launch App:** Open browser to `http://localhost:8501`.
2. **Present Vision:**
   > *"Good morning professors. Today I am presenting **RescueMind: Twin Cities Animal Rescue Intelligence and Dispatch Simulator**. Animal welfare organizations face severe resource constraints: more distress calls arrive than available teams can handle, with varying urgencies, specialized skill needs, and dynamic road conditions. RescueMind simulates an transparent, resource-aware AI coordination system for the Islamabad-Rawalpindi metropolitan area."*
3. **Show Overview Dashboard:**
   - Point out the **Operations Overview** KPIs: Active Incidents, Unassigned Queue, Available Teams, and Disrupted Corridors.
   - Point to the interactive **Folium Map** showing the 24-node Islamabad-Rawalpindi synthetic network with team bases, clinics, and incidents color-coded by urgency.

---

### Minute 0:45 – 1:45 | AI Lab: Search Algorithms & Mathematical Contrast
1. **Navigate to Sidebar:** Click **"AI Lab & Search Arena"**.
2. **Select Endpoints:**
   - Set **Start Node:** `F6_SUPER` (North Base Alpha).
   - Set **Destination Node:** `ZERO_POINT` (Central Interchange).
   - Click **"Run Comparison"**.
3. **Highlight Key Mathematical Finding:**
   > *"Notice the comparison table: We designed a specific test topology where BFS selects the single high-toll bypass hop with cost 12.0 km. Uniform Cost Search (UCS) and A* explore further, choosing the 3-hop arterial route with cost 5.4 km. This directly demonstrates that BFS minimizes edge count, while UCS and A* mathematically guarantee minimum weighted travel cost."*
4. **Inspect A\* Step Trace:**
   - Scroll down to show the **A\* Step Trace** table.
   - Point out how $f(n) = g(n) + h(n)$ uses the admissible Haversine geodetic distance to prune search space toward the goal.

---

### Minute 1:45 – 2:45 | Incident Prioritization & Natural Language Intake
1. **Navigate to:** **"Incident Registry & Intake"**.
2. **Explain Priority Queue:**
   - Open the **Active Registry** tab and show the priority scores (e.g. 82.5 pts, 76.4 pts).
   - Explain: *"Prioritization uses a Python `heapq` multi-factor evaluation combining urgency, waiting time, and vulnerability flags, with deterministic creation-sequence tie-breaking."*
3. **Show Natural Language Intake Assistant:**
   - Switch to **"Natural Language Intake"** tab.
   - Pick the sample prompt: *"A critical dog was hit by a car near F-7 Jinnah Super Market and is bleeding heavily..."*
   - Click **"Extract Structured Fields"**.
   - Show how the rule-based extractor extracts category (dog), urgency (5), vulnerability (True), skills (veterinary_care, transport), and location node without needing external cloud APIs.
   - Point out: *"Crucially, the system enforces Human-in-the-Loop review: the operator must verify the extraction before confirming into the active queue."*

---

### Minute 2:45 – 3:45 | Dispatch Center: CSP Backtracking vs Branch-and-Bound
1. **Navigate to:** **"Dispatch Center"**.
2. **Run CSP Solver:**
   - Select **"CSP Backtracking (MRV + Forward Check)"**.
   - Click **"Generate Dispatch Plan"**.
   - Show the assigned missions and point to the **"Operational Explanations"** generated directly from algorithm constraints:
     > *"Team met all mandatory skill requirements, had available capacity (1/1), and dispatched via optimal route..."*
3. **Audit Hard Constraints & Rejections:**
   - Click **"Hard Constraint Auditing"** tab.
   - Show the candidate rejection log: *"Notice Team 01 was rejected for Incident INC-104 due to missing 'wildlife_rescue' skill, and Team 03 was rejected due to lack of medical care. The system never makes illegal assignments to force a plan."*
4. **Contrast with Branch-and-Bound:**
   - Toggle **"Branch-and-Bound (Cost Optimal)"** and generate plan.
   - Point to total travel cost reduction and show pruned branches.

---

### Minute 3:45 – 4:30 | Dynamic Simulation & Disruption Replanning
1. **Navigate to:** **"Settings & Scenarios"**.
2. **Inject Road Disruption:**
   - Click **"Road Disruption Controls"**.
   - Select a key road segment connecting the active dispatch (e.g., `ZERO_POINT <--> FAIZABAD`).
   - Click **"Block This Road Segment"**.
3. **Inspect Autonomous Replanning:**
   - Point to the instant replan alert:
     > *"Disruption detected! Route for Team Capital Rescue was severed by the blockage. The system autonomously calculated a detour bypass and computed the travel cost diff (+3.2 km)."*
4. **Show Before-and-After Tab in Dispatch Center:**
   - Return to **Dispatch Center** -> **"Before-and-After Replan Comparison"** tab to show the side-by-side previous vs new route paths.

---

### Minute 4:30 – 5:00 | Testing Rigor, Verification & Conclusion
1. **Show Automated Test Suite:**
   - Switch briefly to terminal or point to `docs/testing.md`:
   - *"All algorithms are validated by 33 automated unit and integration tests with 100% pass rate in 0.34 seconds, including validation of Branch-and-Bound against brute-force exhaustive enumeration."*
2. **Conclude Confidently:**
   > *"In summary, RescueMind demonstrates real, explainable AI: graph search (BFS, DFS, UCS, A*, Greedy), multi-factor priority queues, CSP backtracking with MRV, Branch-and-Bound optimization, and dynamic disruption handling. Thank you, and I look forward to your questions."*
