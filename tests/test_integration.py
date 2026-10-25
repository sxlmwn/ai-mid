"""End-to-end integration tests for RescueMind coordination workflow."""
from pathlib import Path
import pytest
from rescuemind.models.incident import AnimalCategory
from rescuemind.services.simulation_service import SimulationService


@pytest.fixture
def sim():
    data_dir = Path(__file__).resolve().parent.parent / "rescuemind" / "data"
    return SimulationService(data_dir)


def test_full_dispatch_cycle_execution(sim):
    plan = sim.dispatch_service.run_dispatch_cycle(use_optimization=False, routing_algo="A*")

    assert plan is not None
    assert len(plan.assignments) > 0
    assert plan.total_cost > 0.0
    assert len(plan.explanations) > 0

    # Ensure assigned incident state is updated
    first_assignment = plan.assignments[0]
    assigned_inc = sim.incident_service.get_incident(first_assignment.incident_id)
    assert assigned_inc.assigned_team_id == first_assignment.team_id
    assert first_assignment.route.success is True


def test_dynamic_incident_registration_and_dispatch(sim):
    # Add new high-urgency incident with waiting time to ensure immediate top dispatch
    new_inc = sim.incident_service.add_incident(
        title="Emergency Cheetah Sighting near Shakarparian",
        description="Escaped exotic wildlife spotted in park bushes.",
        location_id="SHAKARPARIAN",
        latitude=33.6890,
        longitude=73.0820,
        animal_category=AnimalCategory.WILDLIFE,
        urgency=5,
        is_vulnerable=True,
        required_skills=["wildlife_rescue"],
    )
    new_inc.waiting_time = 45.0  # Prolonged wait ensures #1 rank

    # High urgency and prolonged wait places it at top of priority queue
    queue = sim.incident_service.recompute_priorities()
    assert queue[0].incident_id == new_inc.incident_id

    # Run dispatch cycle
    plan = sim.dispatch_service.run_dispatch_cycle(use_optimization=False)
    # The wildlife squad (TEAM-02) should be assigned
    wildlife_assignment = [a for a in plan.assignments if a.incident_id == new_inc.incident_id]
    assert len(wildlife_assignment) == 1
    assert wildlife_assignment[0].team_id == "TEAM-02"


def test_road_blockage_and_route_replanning(sim):
    # Run initial plan
    plan_initial = sim.dispatch_service.run_dispatch_cycle(routing_algo="UCS")
    assert len(plan_initial.assignments) > 0

    # Pick an active route and block one of its segments
    chosen_assignment = plan_initial.assignments[0]
    path = chosen_assignment.route.path
    assert len(path) >= 2
    u, v = path[0], path[1]

    # Block the segment
    sim.routing_service.block_road(u, v)

    # Trigger replan
    replan_notes = sim.dispatch_service.replan_disrupted_routes(u, v)

    assert len(replan_notes) >= 1
    # Check that route was updated
    assert not sim.routing_service.route_contains_edge(chosen_assignment.route.path, u, v)
