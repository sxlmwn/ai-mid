"""Tests for simulation lifecycle, time progression, scenarios, and NL intake."""
from pathlib import Path
import pytest
from rescuemind.services.simulation_service import SimulationService


@pytest.fixture
def sim_service():
    data_dir = Path(__file__).resolve().parent.parent / "rescuemind" / "data"
    sim = SimulationService(data_dir)
    return sim


def test_advance_time(sim_service):
    active_before = sim_service.incident_service.get_unassigned_incidents()
    initial_waits = {inc.incident_id: inc.waiting_time for inc in active_before}

    sim_service.advance_time(20.0)
    assert sim_service.simulation_time_minutes == 20.0

    for inc in sim_service.incident_service.get_unassigned_incidents():
        assert inc.waiting_time == initial_waits[inc.incident_id] + 20.0


def test_load_scenario_faizabad_closure(sim_service):
    sim_service.load_scenario("SCENARIO_FAIZABAD_CLOSURE")
    assert sim_service.active_scenario_id == "SCENARIO_FAIZABAD_CLOSURE"
    # Verify road is blocked
    edge = sim_service.routing_service.graph.get_edge("ZERO_POINT", "FAIZABAD")
    assert edge.is_open is False


def test_reset_all(sim_service):
    sim_service.advance_time(45.0)
    sim_service.routing_service.block_road("F6_SUPER", "F7_JINNAH")
    assert sim_service.simulation_time_minutes > 0

    sim_service.reset_all()
    assert sim_service.simulation_time_minutes == 0.0
    edge = sim_service.routing_service.graph.get_edge("F6_SUPER", "F7_JINNAH")
    assert edge.is_open is True


def test_natural_language_intake_extraction(sim_service):
    report_text = "Urgent: A critical dog was hit by a car near F-7 Jinnah Super Market and is bleeding heavily. Needs immediate surgery and transport."
    parsed = sim_service.parse_natural_language_report(report_text)

    assert parsed["animal_category"] == "dog"
    assert parsed["urgency"] == 5
    assert parsed["is_vulnerable"] is True
    assert "veterinary_care" in parsed["required_skills"]
    assert "transport" in parsed["required_skills"]
    assert parsed["suggested_location_id"] == "F7_JINNAH"
