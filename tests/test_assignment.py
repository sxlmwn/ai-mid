"""Tests for Constraint Satisfaction Problem (CSP) team assignment."""
import pytest
from rescuemind.algorithms.assignment import RescueTeamCSP
from rescuemind.models.incident import Incident, IncidentStatus, AnimalCategory
from rescuemind.models.rescue_team import RescueTeam, TeamStatus


def make_incident(
    inc_id: str,
    skills: list[str],
    category: AnimalCategory = AnimalCategory.DOG,
    loc: str = "F7_JINNAH",
) -> Incident:
    return Incident(
        incident_id=inc_id,
        title=f"Incident {inc_id}",
        description="desc",
        location_id=loc,
        latitude=33.72,
        longitude=73.05,
        animal_category=category,
        urgency=3,
        required_skills=skills,
        status=IncidentStatus.REPORTED,
    )


def make_team(
    team_id: str,
    skills: list[str],
    capacity: int = 1,
    status: TeamStatus = TeamStatus.AVAILABLE,
    categories: list[str] = None,
) -> RescueTeam:
    return RescueTeam(
        team_id=team_id,
        name=f"Team {team_id}",
        base_location_id="F6_SUPER",
        current_location_id="F6_SUPER",
        latitude=33.73,
        longitude=73.07,
        skills=skills,
        status=status,
        capacity=capacity,
        supported_categories=categories or [],
    )


def test_csp_valid_assignment():
    inc1 = make_incident("I1", ["veterinary_care"])
    inc2 = make_incident("I2", ["trapped_animal_extrication"])

    team1 = make_team("T1", ["veterinary_care"])
    team2 = make_team("T2", ["trapped_animal_extrication"])

    csp = RescueTeamCSP([inc1, inc2], [team1, team2])
    res = csp.solve()

    assert res.is_feasible is True
    assert res.assignment["I1"] == "T1"
    assert res.assignment["I2"] == "T2"


def test_csp_missing_skills_rejection():
    # Incident requires water_rescue, team only has veterinary_care
    inc = make_incident("I_WATER", ["water_rescue"])
    team = make_team("T_MED", ["veterinary_care"])

    csp = RescueTeamCSP([inc], [team])
    res = csp.solve()

    assert res.is_feasible is False
    assert len(res.assignment) == 0
    assert "I_WATER" in res.unassigned
    assert any("SKILL_DEFICIT" in r.failed_constraint for r in res.rejections)


def test_csp_capacity_constraint():
    # 2 incidents, but only 1 team with capacity 1
    inc1 = make_incident("I1", ["transport"])
    inc2 = make_incident("I2", ["transport"])
    team_single = make_team("T1", ["transport"], capacity=1)

    csp = RescueTeamCSP([inc1, inc2], [team_single])
    res = csp.solve()

    assert res.is_feasible is False
    assert len(res.assignment) <= 1


def test_csp_higher_capacity_allows_multiple():
    # 2 incidents, 1 team with capacity 2
    inc1 = make_incident("I1", ["transport"])
    inc2 = make_incident("I2", ["transport"])
    team_multi = make_team("T_HEAVY", ["transport"], capacity=2)

    csp = RescueTeamCSP([inc1, inc2], [team_multi])
    res = csp.solve()

    assert res.is_feasible is True
    assert res.assignment["I1"] == "T_HEAVY"
    assert res.assignment["I2"] == "T_HEAVY"


def test_csp_category_restriction():
    # Wildlife incident, but team only supports cats and dogs
    inc = make_incident("I_WILD", ["wildlife_rescue"], category=AnimalCategory.WILDLIFE)
    team = make_team("T_DOMESTIC", ["wildlife_rescue"], categories=["cat", "dog"])

    csp = RescueTeamCSP([inc], [team])
    res = csp.solve()

    assert res.is_feasible is False
    assert any("CATEGORY_MISMATCH" in r.failed_constraint for r in res.rejections)
