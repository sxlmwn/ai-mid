"""Simulation state coordinator managing scenarios, clock, and service integration."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from rescuemind.models.incident import AnimalCategory
from rescuemind.services.dispatch_service import DispatchService
from rescuemind.services.explanation_service import ExplanationService
from rescuemind.services.incident_service import IncidentService
from rescuemind.services.metrics_service import MetricsService
from rescuemind.services.routing_service import RoutingService
from rescuemind.utils.constants import DISCLAIMER_TEXT


class SimulationService:
    """Master simulation lifecycle service controlling time, scenarios, and coordinated services."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.simulation_time_minutes = 0.0
        self.active_scenario_id = "SCENARIO_DEFAULT"
        self.scenarios_data: Dict[str, Any] = {}

        # Initialize sub-services
        self.incident_service = IncidentService(data_dir / "incidents.json")
        self.routing_service = RoutingService(data_dir / "roads.json")
        self.dispatch_service = DispatchService(
            self.incident_service,
            self.routing_service,
            data_dir / "teams.json",
        )
        self.metrics_service = MetricsService(
            self.incident_service,
            self.dispatch_service,
            self.routing_service,
        )

        self._load_scenarios(data_dir / "scenarios.json")

    def _load_scenarios(self, path: Path):
        """Load predefined scenario configurations."""
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for sc in data.get("scenarios", []):
                    self.scenarios_data[sc["scenario_id"]] = sc

    def advance_time(self, delta_minutes: float = 15.0):
        """Advance simulation clock, increment waiting times for unassigned cases, and reprioritize."""
        self.simulation_time_minutes += delta_minutes
        self.incident_service.advance_waiting_time(delta_minutes)

    def load_scenario(self, scenario_id: str):
        """Apply a predefined scenario state."""
        if scenario_id not in self.scenarios_data:
            return

        self.reset_all()
        self.active_scenario_id = scenario_id
        sc = self.scenarios_data[scenario_id]

        # Apply road blockages
        for pair in sc.get("blocked_roads", []):
            if len(pair) == 2:
                self.routing_service.block_road(pair[0], pair[1])

        # Apply congestions
        for cong in sc.get("congestions", []):
            self.routing_service.set_congestion(cong["u"], cong["v"], float(cong["multiplier"]))

        # Run initial dispatch plan under this scenario
        self.dispatch_service.run_dispatch_cycle()

    def reset_all(self):
        """Reset entire simulation to initial baseline scenario."""
        self.simulation_time_minutes = 0.0
        self.active_scenario_id = "SCENARIO_DEFAULT"
        self.incident_service.reset_to_initial()
        self.routing_service.reset_to_initial()
        self.dispatch_service.reset_to_initial()

    def parse_natural_language_report(self, text: str) -> Dict[str, Any]:
        """Optional rule-based natural language incident intake assistant.
        Converts unstructured operator reports into structured draft incident fields
        WITHOUT requiring paid external APIs or LLMs.
        """
        text_lower = text.lower()
        extracted: Dict[str, Any] = {
            "title": "Reported Animal in Distress",
            "description": text.strip(),
            "animal_category": AnimalCategory.OTHER.value,
            "urgency": 3,
            "is_vulnerable": False,
            "required_skills": [],
            "suggested_location_id": "F7_JINNAH",
            "confidence": 0.85,
            "requires_operator_review": True,
        }

        # Animal category extraction
        if any(w in text_lower for w in ["dog", "puppy", "hound", "canine"]):
            extracted["animal_category"] = AnimalCategory.DOG.value
            extracted["title"] = "Canine Rescue Assistance"
        elif any(w in text_lower for w in ["cat", "kitten", "feline"]):
            extracted["animal_category"] = AnimalCategory.CAT.value
            extracted["title"] = "Feline Rescue Assistance"
        elif any(w in text_lower for w in ["bird", "pelican", "eagle", "pigeon", "owl"]):
            extracted["animal_category"] = AnimalCategory.BIRD.value
            extracted["title"] = "Avian Distress Assistance"
        elif any(w in text_lower for w in ["cow", "calf", "goat", "horse", "donkey", "livestock"]):
            extracted["animal_category"] = AnimalCategory.LIVESTOCK.value
            extracted["title"] = "Livestock Rescue Assistance"
        elif any(w in text_lower for w in ["porcupine", "monkey", "fox", "boar", "wildlife"]):
            extracted["animal_category"] = AnimalCategory.WILDLIFE.value
            extracted["title"] = "Wildlife Rescue Assistance"

        # Urgency deduction
        if any(w in text_lower for w in ["critical", "dying", "severe", "life threatening", "bleeding profusely", "hit by car"]):
            extracted["urgency"] = 5
            extracted["is_vulnerable"] = True
        elif any(w in text_lower for w in ["injured", "broken leg", "trapped", "drowning", "stuck"]):
            extracted["urgency"] = 4
            extracted["is_vulnerable"] = True
        elif any(w in text_lower for w in ["lost", "wandering", "lethargic", "shivering", "dehydrated"]):
            extracted["urgency"] = 3
        else:
            extracted["urgency"] = 2

        # Skill requirement deduction
        skills = []
        if any(w in text_lower for w in ["trapped", "stuck", "drain", "ditch", "grate", "well"]):
            skills.append("trapped_animal_extrication")
        if any(w in text_lower for w in ["water", "lake", "canal", "drowning", "pond"]):
            skills.append("water_rescue")
        if any(w in text_lower for w in ["aggressive", "biting", "growling", "hostile"]):
            skills.append("handling_aggressive")
        if any(w in text_lower for w in ["injured", "bleeding", "sick", "wound", "fracture"]):
            skills.append("veterinary_care")
        if any(w in text_lower for w in ["transport", "carry", "heavy", "large"]):
            skills.append("transport")

        extracted["required_skills"] = list(set(skills))

        # Location matching
        nodes = self.routing_service.get_all_nodes()
        for node_id, node in nodes.items():
            simple_name = node.name.lower()
            if any(part in text_lower for part in [node_id.lower(), simple_name.split()[0].lower()]):
                extracted["suggested_location_id"] = node_id
                break

        return extracted
