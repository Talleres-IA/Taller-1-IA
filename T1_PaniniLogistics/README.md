# Workshop 1 - Panini Logistics

## Quick Setup

From this folder:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Road Graph

`data/colombia_roads.json` contains a real road graph extracted from OpenStreetMap through the Geofabrik Colombia extract:

- Source: `gis_osm_roads_free` layer from `colombia-latest-free.gpkg.zip`.
- Filter: `motorway`, `trunk`, `primary`, `secondary`, `tertiary`, and their link variants.
- Processing: undirected graph, largest connected component, costs in kilometers.
- Simplification: degree-2 chains are compressed to preserve intersections/endpoints while keeping runtimes reasonable.
- Final size: 41,718 nodes and 64,126 undirected edges.
- Expected validation: one connected component, positive costs, and symmetric edges.

## Example Commands

Predefined instances from `data/instances.json`:

```bash
python main.py --instance single_bogota_medellin --show
python main.py --instance single_bogota_cartagena_astar --show
python main.py --instance stops_bogota_cali_bfs --show
python main.py --instance ids_local_depth --show
python main.py --instance multi_andes_caribe --show
python main.py --instance multi_national_challenge --show
```

`--show` opens an interactive map in the browser with OpenStreetMap tiles.

## Recommended Problem/Algorithm Pairings

- `single`: use `ucs` or `astar` to minimize total kilometers.
- `stops`: use `dfs`, `bfs` or `ids` to minimize the number of road segments.
- `multi`: use `astar` with a multi-delivery heuristic.

The CLI prints a warning when an algorithm is valid but not recommended for the
selected problem type.

## Explore the Graph

The notebook `notebooks/graph_visualization.ipynb` lets you explore the complete graph:

- Graph loading and validation.
- Plotly/OpenStreetMap visualization of all nodes and edges.
- Tooltips with node and edge attributes.
