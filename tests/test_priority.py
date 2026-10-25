"""Tests for multi-factor priority queue and transparent scoring."""
from rescuemind.algorithms.priority import (
    IncidentPriorityQueue,
    PriorityWeights,
    calculate_incident_score,
)
from rescuemind.models.incident import Incident, IncidentStatus, AnimalCategory


def create_test_incident(
    inc_id: str,
    urgency: int,
    waiting_time: float,
    is_vulnerable: bool,
    status: IncidentStatus = IncidentStatus.REPORTED,
    seq: int = 1,
) -> Incident:
    return Incident(
        incident_id=inc_id,
        title=f"Incident {inc_id}",
        description="Test incident",
        location_id="F7_JINNAH",
        latitude=33.72,
        longitude=73.05,
        animal_category=AnimalCategory.DOG,
        urgency=urgency,
        waiting_time=waiting_time,
        is_vulnerable=is_vulnerable,
        status=status,
        creation_sequence=seq,
    )


def test_score_calculation_breakdown():
    weights = PriorityWeights(weight_urgency=0.5, weight_waiting=0.3, weight_vulnerability=0.2, max_waiting_minutes=60.0)
    inc = create_test_incident("I1", urgency=5, waiting_time=30.0, is_vulnerable=True)

    score, bd = calculate_incident_score(inc, weights)
    # Urgency: 100 * 0.5 * (5/5) = 50.0
    # Waiting: 100 * 0.3 * (30/60) = 15.0
    # Vulnerability: 100 * 0.2 * 1.0 = 20.0
    # Total = 50 + 15 + 20 = 85.0
    assert score == 85.0
    assert bd["urgency_contribution"] == 50.0
    assert bd["waiting_contribution"] == 15.0
    assert bd["vulnerability_contribution"] == 20.0


def test_priority_ordering():
    pq = IncidentPriorityQueue()
    # High urgency, low wait
    inc_high = create_test_incident("I_HIGH", urgency=5, waiting_time=5.0, is_vulnerable=False, seq=1)
    # Low urgency, low wait
    inc_low = create_test_incident("I_LOW", urgency=1, waiting_time=5.0, is_vulnerable=False, seq=2)

    pq.push(inc_low)
    pq.push(inc_high)

    first = pq.pop()
    second = pq.pop()

    assert first.incident_id == "I_HIGH"
    assert second.incident_id == "I_LOW"


def test_equal_score_tie_breaking():
    pq = IncidentPriorityQueue()
    # Exactly identical scores, but I_FIRST registered earlier (seq=1 vs seq=2)
    inc_early = create_test_incident("I_EARLY", urgency=4, waiting_time=20.0, is_vulnerable=True, seq=1)
    inc_late = create_test_incident("I_LATE", urgency=4, waiting_time=20.0, is_vulnerable=True, seq=2)

    pq.push(inc_late)
    pq.push(inc_early)

    popped_first = pq.pop()
    assert popped_first.incident_id == "I_EARLY"


def test_resolved_and_cancelled_filtering():
    pq = IncidentPriorityQueue()
    inc_active = create_test_incident("I_ACT", urgency=2, waiting_time=10.0, is_vulnerable=False)
    inc_resolved = create_test_incident("I_RES", urgency=5, waiting_time=50.0, is_vulnerable=True, status=IncidentStatus.RESOLVED)
    inc_cancelled = create_test_incident("I_CNC", urgency=5, waiting_time=50.0, is_vulnerable=True, status=IncidentStatus.CANCELLED)

    pq.push(inc_resolved)
    pq.push(inc_cancelled)
    pq.push(inc_active)

    popped = pq.pop()
    assert popped.incident_id == "I_ACT"
    # Should be empty now
    assert pq.pop() is None


def test_waiting_time_dynamic_boost():
    weights = PriorityWeights(weight_urgency=0.4, weight_waiting=0.6, weight_vulnerability=0.0)
    inc_urgent = create_test_incident("I_URGENT", urgency=4, waiting_time=0.0, is_vulnerable=False)
    inc_waiting = create_test_incident("I_WAITING", urgency=2, waiting_time=60.0, is_vulnerable=False)

    pq = IncidentPriorityQueue(weights)
    ranked = pq.rebuild_queue([inc_urgent, inc_waiting])
    # The incident waiting for 60 min gets full 60 points from waiting!
    assert ranked[0].incident_id == "I_WAITING"
