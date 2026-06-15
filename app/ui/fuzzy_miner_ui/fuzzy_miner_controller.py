import streamlit as st

from app.mining_algorithms.fuzzy_mining import FuzzyMining
from app.ui.base_algorithm_ui.base_algorithm_controller import BaseAlgorithmController
from app.ui.fuzzy_miner_ui.fuzzy_miner_view import FuzzyMinerView


class FuzzyMinerController(BaseAlgorithmController):
    """Controller for the Fuzzy Miner algorithm."""

    def __init__(
        self, views=None, mining_model_class=None, dataframe_transformations=None
    ):
        """Initializes the controller for the Fuzzy Miner algorithm.

        Parameters
        ----------
        views : List[BaseAlgorithmView] | BaseAlgorithmView, optional
            The views for the Fuzzy Miner algorithm. If None is passed, the default view is used, by default None
        mining_model_class : MiningInterface Class, optional
            The mining model class for the Fuzzy Miner algorithm. If None is passed, the default model class is used, by default None
        dataframe_transformations : DataframeTransformations, optional
            The class for the dataframe transformations. If None is passed, a new instance is created, by default None
        """
        self.unary_significance = None
        self.binary_significance = None
        self.correlation = None
        self.edge_cutoff = None
        self.utility_ratio = None
        self.edge_frequency_threshold_normalized = None
        self.edge_frequency_threshold_absolute = None

        if views is None:
            views = [FuzzyMinerView()]

        if mining_model_class is None:
            mining_model_class = FuzzyMining

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
        return "Fuzzy Mining"

    def process_algorithm_parameters(self):
        """Processes the algorithm parameters from the session state. The parameters are set to the instance variables.
        If the parameters are not set in the session state, the default values are used.
        """
        super().process_algorithm_parameters()
        # set session state from instance variables if not set
        if "unary_significance" not in st.session_state:
            st.session_state.unary_significance = (
                self.mining_model.get_unary_significance()
            )

        if "binary_significance" not in st.session_state:
            st.session_state.binary_significance = (
                self.mining_model.get_binary_significance()
            )

        if "correlation" not in st.session_state:
            st.session_state.correlation = self.mining_model.get_correlation()

        if "edge_cutoff" not in st.session_state:
            st.session_state.edge_cutoff = self.mining_model.get_edge_cutoff()

        if "utility_ratio" not in st.session_state:
            st.session_state.utility_ratio = self.mining_model.get_utility_ratio()

        if "edge_freq_threshold_normalized" not in st.session_state:
            st.session_state.edge_freq_threshold_normalized = (
                self.mining_model.get_edge_frequency_threshold_normalized()
            )

        if "edge_freq_threshold_absolute" not in st.session_state:
            st.session_state.edge_freq_threshold_absolute = (
                self.mining_model.get_edge_frequency_threshold_absolute()
            )

        # set instance variables from session state
        self.unary_significance = st.session_state.unary_significance
        self.binary_significance = st.session_state.binary_significance
        self.correlation = st.session_state.correlation
        self.edge_cutoff = st.session_state.edge_cutoff
        self.utility_ratio = st.session_state.utility_ratio
        self.edge_frequency_threshold_normalized = (
            st.session_state.edge_freq_threshold_normalized
        )
        self.edge_frequency_threshold_absolute = (
            st.session_state.edge_freq_threshold_absolute
        )

    def perform_mining(self) -> None:
        """Performs the mining of the Fuzzy Miner algorithm."""
        super().perform_mining(
            unary_significance=self.unary_significance,
            binary_significance=self.binary_significance,
            correlation=self.correlation,
            edge_cutoff=self.edge_cutoff,
            utility_ratio=self.utility_ratio,
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
            or self.mining_model.get_unary_significance() != self.unary_significance
            or self.mining_model.get_binary_significance() != self.binary_significance
            or self.mining_model.get_correlation() != self.correlation
            or self.mining_model.get_edge_cutoff() != self.edge_cutoff
            or self.mining_model.get_utility_ratio() != self.utility_ratio
            or self.mining_model.get_edge_frequency_threshold_normalized()
            != self.edge_frequency_threshold_normalized
            or self.mining_model.get_edge_frequency_threshold_absolute()
            != self.edge_frequency_threshold_absolute
        )

    def get_sidebar_values(self) -> dict[str, tuple[int | float, int | float]]:
        """Returns the sidebar values for the Fuzzy Miner algorithm.

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
                "unary_significance": (0.0, 1.0),
                "binary_significance": (0.0, 1.0),
                "correlation": (0.0, 1.0),
                "edge_cutoff": (0.0, 1.0),
                "utility_ratio": (0.0, 1.0),
                "edge_frequency_threshold_normalized": (0.0, 1.0),
                "edge_frequency_threshold_absolute": (0, max_abs_edge),
            }
        )
        return sidebar_values
