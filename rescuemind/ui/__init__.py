"""UI package."""
from rescuemind.ui.map_view import render_operations_map
from rescuemind.ui.dashboard import render_dashboard_view
from rescuemind.ui.incident_views import render_incidents_view
from rescuemind.ui.dispatch_views import render_dispatch_view
from rescuemind.ui.analytics_views import render_analytics_view
from rescuemind.ui.settings_view import render_settings_view

__all__ = [
    "render_operations_map",
    "render_dashboard_view",
    "render_incidents_view",
    "render_dispatch_view",
    "render_analytics_view",
    "render_settings_view",
]
