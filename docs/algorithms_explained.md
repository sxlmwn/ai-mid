# RescueMind Algorithms Explained: Comprehensive Theoretical Guide

This guide provides an academic-level explanation of every algorithm implemented in **RescueMind**, covering mathematical foundations, complexity analysis, admissibility proofs, and step-by-step worked examples.

---

## 1. Graph Representation

The metropolitan road network is represented as a directed, weighted graph $G = (V, E)$, where:
- $V$: Set of vertices representing intersections, rescue depots, veterinary clinics, and landmarks.
- $E$: Set of edges representing road segments. Each edge $e = (u, v)$ has:
  - Base cost $c(u, v) \ge 0$ (distance in kilometers).
  - Base travel time $t(u, v) \ge 0$ (minutes).
  - Status flag $\text{isOpen} \in \{\text{True}, \text{False}\}$.
  - Congestion multiplier $\gamma(u, v) \ge 1.0$.

### Effective Cost Formulation
The effective travel cost $w(u, v)$ utilized by pathfinding search algorithms is:

$$w(u, v) = \begin{cases} c(u, v) \cdot \gamma(u, v) & \text{if } \text{isOpen}(u, v) = \text{True} \\ \infty & \text{if } \text{isOpen}(u, v) = \text{False} \end{cases}$$

Non-negativity constraint: $\forall (u, v) \in E, w(u, v) \ge 0$. This ensures UCS and A* never encounter negative cycles.

---

## 2. Search Algorithms Comparison

| Algorithm | Frontier Data Structure | Evaluation Function | Edge Weights | Optimal? | Complete? | Time Complexity | Space Complexity |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BFS** | FIFO Queue (`deque`) | Depth $d$ (hops) | Ignored | For unweighted edges only | Yes (finite $b$) | $O(b^d)$ | $O(b^d)$ |
| **DFS** | LIFO Stack (`list`) | Depth (deepest first) | Ignored | No | Yes (finite graph) | $O(b^m)$ | $O(b \cdot m)$ |
| **UCS** | Min-Priority Queue (`heapq`) | $g(n)$ (cumulative cost) | Weighted | Yes (cost optimal) | Yes ($\epsilon > 0$) | $O(b^{1 + \lfloor C^* / \epsilon \rfloor})$ | $O(b^{1 + \lfloor C^* / \epsilon \rfloor})$ |
| **A\*** | Min-Priority Queue (`heapq`) | $f(n) = g(n) + h(n)$ | Weighted + Heuristic | Yes (if $h$ admissible) | Yes | $O(b^{d})$ (pruned) | $O(b^{d})$ |
| **Greedy** | Min-Priority Queue (`heapq`) | $h(n)$ (heuristic only) | Ignored during search | No | No (can loop in bad graphs) | $O(b^m)$ worst case | $O(b \cdot m)$ |

*Notation: $b$ = branching factor, $d$ = depth of shallowest goal, $m$ = maximum depth, $C^*$ = cost of optimal solution, $\epsilon$ = minimum step cost.*

---

## 3. Detailed Algorithm Implementations

### 3.1 Breadth-First Search (BFS)
- **Concept:** Traverses the graph layer by layer using a FIFO queue.
- **Guarantee:** Guarantees finding the route with the fewest road segments (hop count).
- **Educational Contrast:** In weighted networks, the route with the fewest edges is often NOT the route with the lowest travel cost. For example, a single direct highway toll-segment might cost 20 km, while a 3-hop arterial route might cost only 6 km ($2 + 2 + 2$). BFS will pick the 20 km single-hop route, demonstrating why edge count alone is insufficient for emergency dispatch.

### 3.2 Depth-First Search (DFS)
- **Concept:** Plunges along each branch to maximal depth before backtracking, using a LIFO stack.
- **Neighbor Ordering:** In RescueMind, neighbors are sorted deterministically so demonstrations are 100% reproducible.
- **Educational Contrast:** DFS has low memory consumption $O(bm)$ compared to BFS, but frequently finds circuitous, suboptimal routes.

### 3.3 Uniform Cost Search (UCS)
- **Concept:** A generalization of Dijkstra's algorithm. Expands the node with the lowest accumulated path cost $g(n)$ from the start node:
  $$g(n) = \sum_{i=1}^{k} w(v_{i-1}, v_i)$$
- **Frontier:** Priority queue storing `(g(n), counter, node, path)`.
- **Handling Redundant Paths:** If a shorter path to a previously discovered node is found before it is expanded, the priority queue is updated with the lower cost. Once a node is popped from the priority queue, its optimal cost is guaranteed.

### 3.4 A* Search & Admissibility
- **Evaluation Function:**
  $$f(n) = g(n) + h(n)$$
  where $g(n)$ is the exact cost to reach node $n$, and $h(n)$ is an estimate of the cost from $n$ to the goal.
- **Heuristic Choice:** RescueMind uses the great-circle Haversine geodetic distance:
  $$d_{\text{haversine}}(n, \text{goal}) = 2 R \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)}\right)$$
  where $R = 6371\text{ km}$.

#### Proof of Admissibility:
A heuristic $h(n)$ is admissible if $\forall n, 0 \le h(n) \le h^*(n)$, where $h^*(n)$ is the true shortest travel cost to the goal.
Since physical roads on ground must curve around topography, buildings, and terrain:
$$\text{Straight-line Euclidean / Haversine Distance} \le \text{True Road Driving Distance}$$
Therefore, $h(n)$ never overestimates the true remaining cost ($h(n) \le h^*(n)$).
Because edge weights are non-negative and $h(n)$ satisfies the triangle inequality ($h(u) \le w(u, v) + h(v)$), $h(n)$ is also **consistent (monotonic)**. This guarantees that A* finds the optimal minimum-cost route without requiring node reopening.

### 3.5 Greedy Best-First Search
- **Concept:** Orders the frontier exclusively by $h(n)$.
- **Behavior:** Focuses all expansion power directly toward the coordinates of the goal.
- **Limitation:** Ignores $g(n)$. If a blocked river, highway divider, or dead-end lies directly between the rescuer and the incident, Greedy will charge straight toward the obstacle, potentially finding an extremely inefficient route or exploring blind alleys.

---

## 4. Multi-Factor Incident Prioritization

Incidents are prioritized using an internal min-heap where key $= -\text{Score}$.

### Mathematical Formulation
$$\text{Score} = 100 \times \left[ w_{\text{urgency}} \cdot \left(\frac{U}{5}\right) + w_{\text{wait}} \cdot \min\left(\frac{T_{\text{wait}}}{T_{\max}}, 1.0\right) + w_{\text{vuln}} \cdot V \right]$$

- $U \in \{1, 2, 3, 4, 5\}$: Reported urgency level.
- $T_{\text{wait}} \ge 0$: Simulated minutes elapsed since incident registration.
- $T_{\max} = 60.0$: Saturation window for waiting time penalty.
- $V \in \{0, 1\}$: Vulnerability indicator (e.g. juvenile, hypothermia, trapped animal).
- Normalized weights: $w_{\text{urgency}} + w_{\text{wait}} + w_{\text{vuln}} = 1.0$ (defaults: 0.45, 0.35, 0.20).

### Deterministic Tie-Breaking
When two incidents produce identical mathematical scores:
1. Incident with smaller `creation_sequence` (reported earlier) is popped first.
2. If creation sequences match, alphabetical order of `incident_id` breaks the tie.

---

## 5. Constraint Satisfaction Problem (CSP)

Dispatching rescue teams to emergency calls is formulated as a formal CSP:

### Formal Model
- **Variables $X$:** $\{I_1, I_2, \dots, I_k\}$ (active prioritized incidents).
- **Domain $D(I_i)$:** Available rescue teams $\{T_1, T_2, \dots, T_m\}$.
- **Hard Constraints $C$:**
  1. $\text{Status}(T) = \text{AVAILABLE}$.
  2. $\text{RequiredSkills}(I_i) \subseteq \text{Skills}(T)$.
  3. $\text{Category}(I_i) \in \text{SupportedCategories}(T)$.
  4. $|\{I_j \mid \text{Assign}(I_j) = T\}| \le \text{Capacity}(T)$.
  5. RouteExists$(\text{Location}(T), \text{Location}(I_i)) = \text{True}$.

### Heuristics & Inferences
1. **Minimum Remaining Values (MRV):**
   - The variable with the fewest eligible candidate teams in its domain is selected for assignment first:
     $$I^* = \arg\min_{I \in \text{Unassigned}} |D(I)|$$
   - "Fail-first" principle: If an incident has only 1 qualified team, assign it immediately before another incident consumes that scarce resource.
2. **Forward Checking:**
   - Whenever team $T$ is provisionally assigned to $I_i$, its remaining capacity is decremented. If remaining capacity reaches 0, $T$ is pruned from the domains of all remaining unassigned variables.

---

## 6. Branch-and-Bound (B&B) Optimization

While CSP finds *any* feasible assignment satisfying hard constraints, Branch-and-Bound finds the **cost-optimal** assignment that minimizes total fleet travel distance.

### Objective Function
$$\text{Minimize } Z = \sum_{(I, T) \in \text{Assignment}} \text{Cost}_{\text{UCS}}(T, I)$$

### Admissible Lower Bound Formulation
For a partial assignment with accumulated cost $g_{\text{accum}}$ and remaining unassigned incidents $U$:
$$\text{LB}(U) = \sum_{I \in U} \min_{T \in D(I)} \text{Cost}_{\text{UCS}}(T, I)$$

### Pruning Condition
$$\text{If } \left( g_{\text{accum}} + \text{LB}(U) \ge Z^* \right) \implies \text{PRUNE BRANCH}$$
where $Z^*$ is the cost of the best complete feasible assignment discovered so far.

Because each term in $\text{LB}(U)$ assumes the absolute cheapest possible route for every remaining incident, $\text{LB}(U)$ is strictly admissible ($\text{LB}(U) \le \text{True Remaining Cost}$). Therefore, no branch containing an optimal solution is ever pruned prematurely.
