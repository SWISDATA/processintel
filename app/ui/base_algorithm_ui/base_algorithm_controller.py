from abc import ABC
import streamlit as st

from app.components.buttons import to_home
from app.exceptions.graph_exceptions import InvalidNodeNameException, GraphException
from app.exceptions.type_exceptions import TypeIsNoneException
from app.graphs.visualization.base_graph import BaseGraph
from app.logger import get_logger
from app.transformations.dataframe_transformations import DataframeTransformations
from app.ui.base_ui.base_controller import BaseController


class BaseAlgorithmController(BaseController, ABC):
    """Base class for the algorithm controllers. It provides the basic methods for the algorithm controllers."""

    def __init__(
        self,
        views=None,
        mining_model_class=None,
        dataframe_transformations=None,
        supports_fixed_graph_layout: bool = False,
    ):
        """Initializes the controller for the algorithm views.

        Parameters
        ----------
        views : List[BaseView] | BaseView, optional
            The views for the algorithm page. If None is passed, the default view is used, by default None
        mining_model_class : MiningInterface class, optional
            The class of the mining model, by default None
        dataframe_transformations : DataframeTransformations, optional
            The class for the dataframe transformations. If None is passed, a new instance is created, by default None
        supports_fixed_graph_layout : bool
            If True, the fixed graph layout is available, by default False.
        """
        self.spm_threshold = None
        self.node_freq_threshold_normalized = None
        self.node_freq_threshold_absolute = None
        self.logger = get_logger("BaseAlgorithmController")
        self.supports_fixed_graph_layout = supports_fixed_graph_layout

        self.mining_model = None

        if dataframe_transformations is None:
            dataframe_transformations = DataframeTransformations()

        self.dataframe_transformations = dataframe_transformations

        if mining_model_class is None:
            self.logger.error("Mining model class is None")
            raise TypeIsNoneException("Mining model class is None")

        self.mining_model_class = mining_model_class
        super().__init__(views)

    def perform_mining(self, **kwargs) -> None:
        """Performs the mining of the algorithm using the default filter parameters.
        Can optionally be overridden by subclasses to customize parameter handling.

        Passes the SPM threshold, node frequency, and edge frequency to the model's
        draw_graph methods. Additional parameters can be provided via kwargs.
        """
        params = {
            "spm_threshold": self.spm_threshold,
            "node_freq_threshold_normalized": self.node_freq_threshold_normalized,
            "node_freq_threshold_absolute": self.node_freq_threshold_absolute,
        }
        params.update(kwargs)

        self.mining_model.generate_graph(**params)

    def process_algorithm_parameters(self):
        """Processes the algorithm parameters from the session state. Initializes shared filter
        parameters for node and edge filtering if they are not yet defined in the session state.

        This method can be extended or overridden by subclasses to read or define additional parameters.
        """
        if "spm_threshold" not in st.session_state:
            st.session_state.spm_threshold = self.mining_model.get_spm_threshold()
        if "node_freq_threshold_normalized" not in st.session_state:
            st.session_state.node_freq_threshold_normalized = (
                self.mining_model.get_node_frequency_threshold_normalized()
            )
        if "node_freq_threshold_absolute" not in st.session_state:
            st.session_state.node_freq_threshold_absolute = (
                self.mining_model.get_node_frequency_threshold_absolute()
            )

        self.spm_threshold = st.session_state.spm_threshold
        self.node_freq_threshold_normalized = (
            st.session_state.node_freq_threshold_normalized
        )
        self.node_freq_threshold_absolute = (
            st.session_state.node_freq_threshold_absolute
        )

    def have_parameters_changed(self) -> bool:
        """Checks if the shared algorithm parameters (node and edge filtering sliders)
        have changed compared to the current mining model.

        Returns
        -------
        bool
            True if any of the filtering parameters have changed, False otherwise.
        """
        return (
            self.mining_model.get_spm_threshold() != self.spm_threshold
            or self.mining_model.get_node_frequency_threshold_normalized()
            != self.node_freq_threshold_normalized
            or self.mining_model.get_node_frequency_threshold_absolute()
            != self.node_freq_threshold_absolute
        )

    def get_sidebar_values(self) -> dict[str, tuple[float, float]]:
        """Returns the values for the shared sidebar sliders. Can be used to define the minimum
        and maximum values for the SPM, node frequency, and edge frequency filters.

        This method can be overridden by subclasses to customize the slider bounds.

        Returns
        -------
        dict[str, tuple[float, float]]
            A dictionary containing the min and max values for each shared sidebar slider.
            Keys must match the corresponding Streamlit session_state keys.
        """
        max_abs_node = (
            max(self.mining_model.filtered_appearance_freqs.values())
            if self.mining_model.filtered_appearance_freqs
            else 1
        )

        return {
            "spm_threshold": (0.0, 1.0),
            "node_frequency_threshold_normalized": (0.0, 1.0),
            "node_frequency_threshold_absolute": (0, max_abs_node),
        }

    def is_correct_model_type(self, model) -> bool:
        """Checks if the model is of the correct type.

        Parameters
        ----------
        model : any
            The model to be checked.

        Returns
        -------
        bool
            True if the model is of the correct type, False otherwise.
        """
        return isinstance(model, self.mining_model_class)

    def create_empty_model(self, *log_data):
        """Creates an empty model instance. The method is used to create a model instance with the provided log data.
        The order of the log data must be the same as the order of the parameters of the create_mining_instance method of the mining model class.

        Returns
        -------
        MiningInterface
            An instance of the mining model class.
        """
        return self.mining_model_class.create_mining_instance(*log_data)

    def transform_df_to_log(self, df, **selected_columns) -> tuple:
        """Transforms the DataFrame to a log. The method uses the dataframe_transformations class to transform the DataFrame to a log.
        The selected columns are passed as keyword arguments to the 'DataframeTransformation' class. The method returns the log data that is used to create the mining model.
        Can be overridden by the subclass if additional transformations are needed.

        Parameters
        ----------
        df : pd.DataFrame
            The DataFrame to be transformed.

        Returns
        -------
        tuple
            The log data that is used to create the mining model.
        """
        self.dataframe_transformations.set_dataframe(df)
        return (
            self.dataframe_transformations.dataframe_to_cases_dict(
                timeLabel=selected_columns["time_column"],
                caseLabel=selected_columns["case_column"],
                eventLabel=selected_columns["activity_column"],
            ),
        )

    def process_session_state(self):
        """Processes the session state. If a model is already in the session state, it is checked if it is of the correct type. If not, an error message is displayed and the user is redirected to the home page.
        If no model is in the session state, a model is created from the provided DataFrame and selected columns. The model is stored in the session state.
        """
        super().process_session_state()
        if "model" in st.session_state:
            if not self.is_correct_model_type(st.session_state.model):
                self.logger.error(
                    f"Invalid model type. Expected model type: {str(self.mining_model_class)}, Received model type: {type(st.session_state.model)}"
                )
                self.logger.info("redirect to home page")
                st.session_state.error = f""" Invalid model type. 
                
                Expected model type: {str(self.mining_model_class)}, Received model type: {str(type(st.session_state.model))}
                """
                to_home("Home")
                st.rerun()
            self.mining_model = st.session_state.model
        else:
            if (
                "df" not in st.session_state
                or "selected_columns" not in st.session_state
            ):
                self.logger.warning("DataFrame or selected columns are missing.")
                self.logger.info("redirect to home page")
                st.session_state.error = "A DataFrame and selected columns must be provided to create a model."
                to_home()
                st.rerun()
            log_data = self.transform_df_to_log(
                st.session_state.df, **st.session_state.selected_columns
            )
            st.session_state.model = self.create_empty_model(*log_data)
            self.mining_model = st.session_state.model

            del st.session_state.df
            del st.session_state.selected_columns

    def run(self, view, pos):
        """Runs the algorithm controller.

        Parameters
        ----------
        view : BaseAlgorithmView
            The view for the algorithm.
        pos : int
            The position of the algorithm in the sidebar.
        """
        self.process_algorithm_parameters()
        view.display_back_button()
        view.display_export_button(disabled=True)

        if self.have_parameters_changed() or self.mining_model.get_graph() is None:
            try:
                view.display_loading_spinner("Mining...", self.perform_mining)
            except InvalidNodeNameException as ex:
                self.logger.exception(ex)
                self.logger.warning(
                    "Invalid node name. The string '___' is not allowed in node names."
                )
                st.session_state.error = (
                    ex.message
                    + "\n Please check the input data. The string '___' is not allowed in node names."
                )
                to_home()
                st.rerun()
            except GraphException as ex:
                self.logger.exception(ex)
                self.logger.warning(
                    "Graph could not be created. Wait until the mining is finished before changing parameters."
                )
                st.warning(
                    "Do not change the parameters while mining. This will cause an error. Wait until the mining is finished."
                )

        graph = self.mining_model.get_graph()
        self._disable_fixed_layout_if_graph_changed(graph)

        view.display_sidebar(
            self.get_sidebar_values(),
            supports_fixed_graph_layout=self.supports_fixed_graph_layout,
        )

        new_graph = self._apply_fixed_graph_position(graph)
        if new_graph is not None:
            graph = new_graph
        self._apply_happy_path_highlighting(graph)
        view.display_graph(graph)
        view.display_export_button(disabled=False)

    def _apply_happy_path_highlighting(self, graph) -> None:
        """Apply or clear Happy Path highlighting based on UI toggle."""
        if graph is None:
            return

        # Toggle lives in the shared BaseAlgorithmView sidebar.
        if not st.session_state.get("show_happy_path", False):
            graph.clear_highlighted_nodes()
            return

        happy_path_events = set()
        if hasattr(self.mining_model, "get_happy_path_events"):
            variant_index = st.session_state.get("happy_path_variant_index")
            happy_path_events = self.mining_model.get_happy_path_events(variant_index)

        graph.highlight_happy_path(happy_path_events)

    def _apply_fixed_graph_position(self, graph: BaseGraph) -> BaseGraph | None:
        """Apply fixed graph position handling to the current graph.

        Parameters
        ----------
        graph : BaseGraph
            The currently generated graph after applying filtering.

        Returns
        -------
        BaseGraph | None
            If fixed layout is enabled and graph already is stored, returns the graph
            with updated visibility information. Otherwirse, None.
        """
        if not self.supports_fixed_graph_layout:
            st.session_state.graph_fixed_position = None
            return None

        if graph is None:
            return None

        if not st.session_state.get("fix_graph_layout", False):
            st.session_state.graph_fixed_position = None
            return None

        if not st.session_state.get("graph_fixed_position"):
            st.session_state.graph_fixed_position = graph
            return None

        fixed_graph = st.session_state.get("graph_fixed_position")
        fixed_graph.set_invisible_nodes(graph.get_node_ids())
        fixed_graph.update_visible_nodes(graph.get_nodes())
        fixed_graph.set_invisible_edges(graph.get_edges())
        return fixed_graph

    def _disable_fixed_layout_if_graph_changed(self, graph: BaseGraph) -> None:
        """Disable fixed graph layout if the current graph structure has changed.

        Parameters
        ----------
        graph : BaseGraph
            The newly generated graph.
        """
        if graph is None:
            return
        if not st.session_state.get("fix_graph_layout", False):
            return

        fixed_graph = st.session_state.get("graph_fixed_position")
        if fixed_graph is None:
            return
        if self._has_current_graph_new_element(fixed_graph, graph):
            self._disable_fixed_layout()

    def _has_current_graph_new_element(
        self, fixed_graph: BaseGraph, current_graph: BaseGraph
    ) -> bool:
        """Compare edges and nodes of fixed graph and current graph.

        Parameters
        ----------
        fixed_graph : BaseGraph
            The saved graph when fixed layout was enabled.
        current_graph : BaseGraph
            The newly generated graph with which fixed graph will be compared.

        Returns
        -------
        bool
            Returns True when current graph has edge or node which are not present
            in fixed graph, otherwise False.
        """
        current_edge_ids = {
            (edge.source, edge.destination) for edge in current_graph.get_edges()
        }
        fixed_edge_ids = {
            (edge.source, edge.destination) for edge in fixed_graph.get_edges()
        }

        current_node_ids = {node.get_id() for node in current_graph.get_nodes()}
        fixed_node_ids = {node.get_id() for node in fixed_graph.get_nodes()}

        for source_id, target_id in current_edge_ids:
            if (source_id, target_id) not in fixed_edge_ids:
                return True

        for node_id in current_node_ids:
            if node_id not in fixed_node_ids:
                return True

        return False

    def _disable_fixed_layout(self) -> None:
        """Clear stored layout state and disable the fix layout toggle and show a warning that layout was disabled."""
        st.session_state.fix_graph_layout = False
        st.session_state.graph_fixed_position = None
        st.warning(
            "Fixed graph layout was disabled because the graph structure changed and the graph had to be regenerated."
        )
        return None
