"""Road and graph node domain models."""
from __future__ import annotations
from dataclasses import dataclass
from rescuemind.utils.validators import ValidationError, validate_coordinates, validate_id, validate_non_negative


@dataclass
class GraphNode:
    node_id: str
    name: str
    latitude: float
    longitude: float
    node_type: str = "junction"  # "base", "shelter", "clinic", "junction", "checkpoint"

    def __post_init__(self):
        self.node_id = validate_id(self.node_id, "Node ID")
        self.name = validate_id(self.name, "Node Name")
        self.latitude, self.longitude = validate_coordinates(self.latitude, self.longitude)

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "node_type": self.node_type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GraphNode:
        return cls(
            node_id=data["node_id"],
            name=data.get("name", data["node_id"]),
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            node_type=data.get("node_type", "junction"),
        )


@dataclass
class RoadEdge:
    start_node: str
    end_node: str
    cost: float  # Base travel cost (km or synthetic unit >= 0)
    travel_time: float  # Base travel time in minutes >= 0
    is_open: bool = True
    road_name: str = ""
    road_type: str = "primary"  # "expressway", "primary", "secondary", "local"
    congestion_multiplier: float = 1.0  # multiplier >= 1.0
    is_bidirectional: bool = True

    def __post_init__(self):
        self.start_node = validate_id(self.start_node, "Start Node")
        self.end_node = validate_id(self.end_node, "End Node")
        self.cost = validate_non_negative(self.cost, "Road edge cost")
        self.travel_time = validate_non_negative(self.travel_time, "Road travel time")
        if self.congestion_multiplier < 1.0:
            raise ValidationError(
                f"Congestion multiplier cannot be less than 1.0, got {self.congestion_multiplier}."
            )

    @property
    def effective_cost(self) -> float:
        """Effective travel cost factoring in road status and congestion."""
        if not self.is_open:
            return float("inf")
        return round(self.cost * self.congestion_multiplier, 3)

    @property
    def effective_time(self) -> float:
        """Effective travel time factoring in road status and congestion."""
        if not self.is_open:
            return float("inf")
        return round(self.travel_time * self.congestion_multiplier, 3)

    def to_dict(self) -> dict:
        return {
            "start_node": self.start_node,
            "end_node": self.end_node,
            "cost": self.cost,
            "travel_time": self.travel_time,
            "is_open": self.is_open,
            "road_name": self.road_name,
            "road_type": self.road_type,
            "congestion_multiplier": self.congestion_multiplier,
            "is_bidirectional": self.is_bidirectional,
        }

    @classmethod
    def from_dict(cls, data: dict) -> RoadEdge:
        return cls(
            start_node=data["start_node"],
            end_node=data["end_node"],
            cost=float(data["cost"]),
            travel_time=float(data.get("travel_time", data["cost"] * 1.5)),
            is_open=bool(data.get("is_open", True)),
            road_name=data.get("road_name", f"{data['start_node']}-{data['end_node']}"),
            road_type=data.get("road_type", "primary"),
            congestion_multiplier=float(data.get("congestion_multiplier", 1.0)),
            is_bidirectional=bool(data.get("is_bidirectional", True)),
        )
