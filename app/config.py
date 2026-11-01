from os import getenv, path

from app.ui.alpha_miner_ui.alpha_miner_controller import AlphaMinerController
from app.ui.fuzzy_miner_ui.fuzzy_miner_controller import FuzzyMinerController
from app.ui.genetic_miner_ui.genetic_miner_controller import GeneticMinerController
from app.ui.heuristic_miner_ui.heuristic_miner_controller import (
    HeuristicMinerController,
)
from app.ui.inductive_miner_infrequent_ui.inductive_miner_infrequent_controller import (
    InductiveMinerInfrequentController,
)
from app.ui.inductive_miner_ui.inductive_miner_controller import (
    InductiveMinerController,
)

DOCS_DIR = getenv("PROCESSINTEL_DOCS_DIR", "docs")
ASSETS_DIR = getenv("PROCESSINTEL_ASSETS_DIR", "assets")
DEMO_DATASET_PATH = path.join(ASSETS_DIR, "demo", "demo_online_shop_orders.csv")

# colon_substitute is used to replace the colon in event names to make them compatible with graphviz.
colon_substitute = "___"

# cluster seperator is used in the Fuzzy Mining algorithm to sepearte the events in the clusters.
cluster_seperator = "---"

# IMPORT FILE CONFIGURATIONS
# --------------------------

# The allowed file extensions for importing data.
import_file_types_mapping = {
    "csv": [".csv"],
    "xes": [".xes"],
}
# List of all allowed file extensions.
import_file_suffixes = [
    suffix for suffixes in import_file_types_mapping.values() for suffix in suffixes
]

# GRAPH EXPORT CONFIGURATIONS
# ---------------------------

graph_export_mime_types = {
    "svg": "image/svg",
    "png": "image/png",
    "dot": "text/plain",
}

graph_export_formats = list(map(lambda x: x.upper(), graph_export_mime_types.keys()))

# COLUMN TYPE PREDICTION CONFIGURATIONS
column_types_predictions_values = {
    "time": set(["time", "date", "timestamp"]),
    "event": set(["event", "activity", "action", "task", "operation", "concept:name"]),
    "case": set(
        ["case", "process", "instance", "session", "case:concept:name", "case_id"]
    ),
}

# ALGORITHM CONFIGURATIONS
# ------------------------

# Maps the algorithm names to the route names.
algorithm_mappings = {
    "Heuristic Mining": "heuristic",
    "Fuzzy Mining": "fuzzy",
    "Inductive Mining": "inductive",
    "Alpha Mining": "alpha",
    "Genetic Mining": "genetic",
    "Inductive Mining Infrequent": "inductive infrequent",
}
# Maps the algorithm routes to the paths of the documentation files.
docs_path_mappings = {
    "heuristic": f"{DOCS_DIR}/algorithms/heuristic_miner.md",
    "fuzzy": f"{DOCS_DIR}/algorithms/fuzzy_miner.md",
    "inductive": f"{DOCS_DIR}/algorithms/inductive_miner.md",
    "alpha": f"{DOCS_DIR}/algorithms/alpha_miner.md",
    "genetic": f"{DOCS_DIR}/algorithms/genetic_miner.md",
    "inductive infrequent": f"{DOCS_DIR}/algorithms/inductive_miner_infrequent.md",
}

# Maps the algorithm routes to the controllers.
algorithm_routes = {
    "heuristic": HeuristicMinerController,
    "fuzzy": FuzzyMinerController,
    "inductive": InductiveMinerController,
    "alpha": AlphaMinerController,
    "genetic": GeneticMinerController,
    "inductive infrequent": InductiveMinerInfrequentController,
}
