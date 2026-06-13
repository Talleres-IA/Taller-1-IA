"""Interactive Folium/Leaflet visualization for Colombia routes."""

from __future__ import annotations

import tempfile
import webbrowser

from graph.road_graph import ColombiaRoadGraph


def build_route_map(
    graph: ColombiaRoadGraph,
    route: list[str] | None = None,
    deliveries: set[str] | None = None,
    expanded: set[str] | None = None,
    title: str = "Panini logistics route",
    max_graph_edges: int = 12000,
    max_expanded_nodes: int = 1000,
):
    """Create an interactive map with OSM tiles, graph edges, and route popups."""

    import folium

    route = route or []
    deliveries = deliveries or set()
    expanded = expanded or set()

    m = folium.Map(
        location=[4.6, -74.1],
        zoom_start=6,
        tiles="OpenStreetMap",
        control_scale=True,
        prefer_canvas=True,
    )
    folium.map.Marker(
        [12.6, -81.7],
        popup=title,
        icon=folium.DivIcon(html=f"<b>{title}</b>"),
    ).add_to(m)

    graph_layer = folium.FeatureGroup(name="OSM road graph sample", show=True)
    route_edges = {frozenset(pair) for pair in zip(route, route[1:], strict=False)}
    drawn_edges: set[frozenset[str]] = set()
    edge_budget = max_graph_edges
    for source, edges in graph.adjacency.items():
        for edge in edges:
            key = frozenset((source, edge.target))
            if key in drawn_edges or key in route_edges:
                continue
            drawn_edges.add(key)
            if edge_budget <= 0:
                continue
            edge_budget -= 1
            s = graph.nodes[source]
            t = graph.nodes[edge.target]
            folium.PolyLine(
                locations=[(s.lat, s.lon), (t.lat, t.lon)],
                color="#8c8c8c",
                weight=1,
                opacity=0.35,
                popup=(
                    f"{source} -> {edge.target}<br>"
                    f"{edge.distance_km:.3f} km<br>"
                    f"{edge.highway}"
                ),
            ).add_to(graph_layer)
    graph_layer.add_to(m)

    expanded_layer = folium.FeatureGroup(name="Expanded nodes", show=False)
    for node_id in list(expanded)[:max_expanded_nodes]:
        if node_id not in graph.nodes:
            continue
        node = graph.nodes[node_id]
        folium.CircleMarker(
            location=(node.lat, node.lon),
            radius=2,
            color="#636363",
            fill=True,
            fill_opacity=0.4,
            popup=_node_popup(graph, node_id),
        ).add_to(expanded_layer)
    expanded_layer.add_to(m)

    if route:
        route_layer = folium.FeatureGroup(name="Solution route", show=True)
        coordinates = [graph.coordinates(node_id) for node_id in route]
        folium.PolyLine(
            locations=coordinates,
            color="#d7301f",
            weight=5,
            opacity=0.9,
            popup=f"Route with {len(route) - 1} actions",
        ).add_to(route_layer)
        for index, node_id in enumerate(route):
            if index not in {0, len(route) - 1} and node_id not in deliveries:
                continue
            node = graph.nodes[node_id]
            if index == 0:
                color = "green"
            elif index == len(route) - 1:
                color = "purple"
            else:
                color = "orange"
            folium.Marker(
                location=(node.lat, node.lon),
                popup=_node_popup(graph, node_id),
                tooltip=node_id,
                icon=folium.Icon(color=color),
            ).add_to(route_layer)
        route_layer.add_to(m)
        m.fit_bounds(coordinates)

    if deliveries:
        delivery_layer = folium.FeatureGroup(name="Delivery nodes", show=True)
        for node_id in deliveries:
            if node_id not in graph.nodes:
                continue
            node = graph.nodes[node_id]
            folium.Marker(
                location=(node.lat, node.lon),
                popup=_node_popup(graph, node_id),
                tooltip=f"delivery: {node_id}",
                icon=folium.Icon(color="orange", icon="gift", prefix="fa"),
            ).add_to(delivery_layer)
        delivery_layer.add_to(m)

    folium.LayerControl().add_to(m)
    return m


def show_route_map(graph: ColombiaRoadGraph, **kwargs) -> str:
    m = build_route_map(graph, **kwargs)
    with tempfile.NamedTemporaryFile(
        prefix="panini_route_", suffix=".html", delete=False
    ) as handle:
        html_path = handle.name
    m.save(html_path)
    webbrowser.open(f"file://{html_path}")
    return html_path


def _node_popup(graph: ColombiaRoadGraph, node_id: str) -> str:
    node = graph.nodes[node_id]
    return (
        f"<b>node_id:</b> {node_id}<br>"
        f"<b>lat:</b> {node.lat:.6f}<br>"
        f"<b>lon:</b> {node.lon:.6f}<br>"
        f"<b>degree:</b> {node.degree}"
    )
