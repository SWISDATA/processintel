import streamlit as st

from app.mining_algorithms.heuristic_mining import HeuristicMining
from app.ui.base_algorithm_ui.base_algorithm_controller import BaseAlgorithmController
from app.ui.heuristic_miner_ui.heuristic_miner_view import HeuristicMinerView


class HeuristicMinerController(BaseAlgorithmController):
    """Controller for the Heuristic Miner algorithm."""

    def __init__(
        self, views=None, mining_model_class=None, dataframe_transformations=None
    ):
        """Initializes the controller for the Heuristic Miner algorithm.

        Parameters
        ----------
        views : List[BaseAlgorithmView] | BaseAlgorithmView, optional
            The views for the Heuristic Miner algorithm. If None is passed, the default view is used, by default None
        mining_model_class : MiningInterface Class, optional
            The mining model class for the Heuristic Miner algorithm. If None is passed, the default model class is used, by default None
        dataframe_transformations : DataframeTransformations, optional
            The class for the dataframe transformations. If None is passed, a new instance is created, by default None
        """
        self.threshold = None
        self.edge_frequency_threshold_normalized = None
        self.edge_frequency_threshold_absolute = None

        if views is None:
            views = [HeuristicMinerView()]

        if mining_model_class is None:
            mining_model_class = HeuristicMining

        super().__init__(
            views,
            mining_model_class,
            dataframe_transformations,
            supports_fixed_graph_layout=True,
        )

    def get_page_title(self) -> str:
        """Returns the page title.

        Returns
        -------
        str
            The page title.
        """
        return "Heuristic Mining"

    def process_algorithm_parameters(self):
        """Processes the algorithm parameters from the session state. The parameters are set to the instance variables.
        If the parameters are not set in the session state, the default values are used.
        """
        super().process_algorithm_parameters()
        # set session state from instance variables if not set
        if "threshold" not in st.session_state:
            st.session_state.threshold = self.mining_model.get_threshold()

        if "edge_freq_threshold_normalized" not in st.session_state:
            st.session_state.edge_freq_threshold_normalized = (
                self.mining_model.get_edge_frequency_threshold_normalized()
            )

        if "edge_freq_threshold_absolute" not in st.session_state:
            st.session_state.edge_freq_threshold_absolute = (
                self.mining_model.get_edge_frequency_threshold_absolute()
            )

        # set instance variables from session state
        self.threshold = st.session_state.threshold
        self.edge_frequency_threshold_normalized = (
            st.session_state.edge_freq_threshold_normalized
        )
        self.edge_frequency_threshold_absolute = (
            st.session_state.edge_freq_threshold_absolute
        )

    def perform_mining(self) -> None:
        super().perform_mining(
            dependency_threshold=self.threshold,
            edge_freq_threshold_normalized=self.edge_frequency_threshold_normalized,
            edge_freq_threshold_absolute=self.edge_frequency_threshold_absolute,
        )

    def have_parameters_changed(self) -> bool:
        """Checks if the algorithm parameters have changed.

        Returns
        -------
        bool
            True if the algorithm parameters have changed, False otherwise.
        """
        return (
            super().have_parameters_changed()
            or self.mining_model.get_threshold() != self.threshold
            or self.mining_model.get_edge_frequency_threshold_normalized()
            != self.edge_frequency_threshold_normalized
            or self.mining_model.get_edge_frequency_threshold_absolute()
            != self.edge_frequency_threshold_absolute
        )

    def get_sidebar_values(self) -> dict[str, tuple[int | float, int | float]]:
        """Returns the sidebar values for the Heuristic Miner algorithm.

        Returns
        -------
        dict[str, tuple[int | float, int | float]]
            A dictionary containing the minimum and maximum values for the sidebar sliders.
            The keys of the dictionary are equal to the keys of the sliders.
        """
        sidebar_values = super().get_sidebar_values()
        max_abs_edge = (
            max(self.mining_model.edge_absolute_counts.values())
            if self.mining_model.edge_absolute_counts
            else 1
        )
        sidebar_values.update(
            {
                "threshold": (0.0, 1.0),
                "edge_frequency_threshold_normalized": (0.0, 1.0),
                "edge_frequency_threshold_absolute": (0, max_abs_edge),
            }
        )
        return sidebar_values
