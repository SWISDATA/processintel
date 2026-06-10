import streamlit as st

from app.components.buttons import home_button, navigation_button
from app.components.interactiveGraph import interactiveGraph
from app.components.number_input_slider import number_input_slider
from app.ui.base_ui.base_view import BaseView


class BaseAlgorithmView(BaseView):
    """Base class for the algorithm views. It provides the basic layout and methods for the algorithm views.
    The class is abstract and must be inherited by a subclass.
    """

    graph_height = 600

    def create_layout(self):
        """Creates the layout for the algorithm views. It creates the graph container, button containers and node data container.
        This is neeeded to display different elements not in the order they are created.
        """
        super().create_layout()
        graph_wrapper_container = st.container(
            border=True, height=self.graph_height + 40
        )  # add 40 to height to account for padding
        with graph_wrapper_container:
            self.graph_container = st.empty()
        button_container = st.container()
        self.node_data_container = st.container()
        with button_container:
            self.back_button_column, _, export_button_column = st.columns([1, 1, 1])

        with export_button_column:
            self.export_button_container = st.empty()

    def render_sidebar(
        self, sidebar_values: dict[str, any], supports_fixed_graph_layout: bool = False
    ) -> None:
        """Renders the sidebar for the algorithm views.
        Displays shared filters and calls extension hooks for node and edge filtering.

        Parameters
        ----------
        sidebar_values : dict[str, any]
            A dictionary containing the values for the sidebar elements. The keys of the dictionary
            are equal to the keys of the sliders and define the slider bounds.
        supports_fixed_graph_layout : bool, optional
            If True, the fixed graph layout is available, by default False.
        """
        st.write("### **Log Filtering**")

        if "spm_threshold" in sidebar_values:
            number_input_slider(
                label="SPM Threshold",
                min_value=sidebar_values["spm_threshold"][0],
                max_value=sidebar_values["spm_threshold"][1],
                key="spm_threshold",
                help="Filter nodes based on the SPM metric threshold.",
            )

        if "node_frequency_threshold_normalized" in sidebar_values:
            number_input_slider(
                label="Node Frequency (normalized)",
                min_value=sidebar_values["node_frequency_threshold_normalized"][0],
                max_value=sidebar_values["node_frequency_threshold_normalized"][1],
                key="node_freq_threshold_normalized",
                help="Filter nodes based on normalized frequency (0–1).",
            )

        if "node_frequency_threshold_absolute" in sidebar_values:
            number_input_slider(
                label="Node Frequency (absolute)",
                min_value=sidebar_values["node_frequency_threshold_absolute"][0],
                max_value=sidebar_values["node_frequency_threshold_absolute"][1],
                key="node_freq_threshold_absolute",
                help="Filter nodes based on absolute event counts.",
            )

        # Hook for additional node filters
        self.render_log_filter_extensions(sidebar_values)

        # UI toggle to highlight Happy Path in the model.
        st.write("### **Highlighting**")
        show_happy_path = st.toggle(
            "Show Happy Path",
            key="show_happy_path",
            value=st.session_state.get("show_happy_path", False),
            help="Highlights the activities that appear in the most frequent trace of the log.",
        )
        model = st.session_state.get("model")
        if model and hasattr(model, "get_happy_path_traces"):
            happy_path_traces = model.get_happy_path_traces()
            if len(happy_path_traces) > 1:
                current_index = st.session_state.get("happy_path_variant_index", 0)
                if not isinstance(current_index, int) or current_index not in range(
                    len(happy_path_traces)
                ):
                    st.session_state.happy_path_variant_index = 0
                st.selectbox(
                    "Happy Path Variant",
                    options=list(range(len(happy_path_traces))),
                    format_func=lambda idx: f"Variant {idx + 1}",
                    key="happy_path_variant_index",
                    help="Select which most frequent trace to use for highlighting.",
                )
            variant_index = st.session_state.get("happy_path_variant_index", 0)
            if not isinstance(variant_index, int) or variant_index not in range(
                len(happy_path_traces)
            ):
                variant_index = 0
                st.session_state.happy_path_variant_index = variant_index
            if show_happy_path:
                trace = model.get_happy_path_trace(variant_index)
                if trace:
                    trace_str = " -> ".join(str(step) for step in trace)
                    st.markdown(f"**Current Variant:** {trace_str}")

        if supports_fixed_graph_layout:
            st.write("### **Graph Layout**")
            st.toggle(
                "Fix Graph Layout",
                key="fix_graph_layout",
                value=st.session_state.get("fix_graph_layout", False),
                help="Fixes the graph in current position.",
            )
        else:
            st.session_state.fix_graph_layout = False

    def render_log_filter_extensions(self, sidebar_values: dict[str, any]) -> None:
        """Renders additional node filtering controls.
        Can be overridden by subclasses to add more node filters.
        """
        pass

    def display_sidebar(
        self, sidebar_values: dict[str, any], supports_fixed_graph_layout: bool = False
    ) -> None:
        """Displays the sidebar for the algorithm views. The methode calls the render_sidebar method of the subclass.

        Parameters
        ----------
        sidebar_values : dict[str, any]
            A dictionary containing the values for the sidebar elements. The keys of the dictionary are equal to the keys of the sliders.
        supports_fixed_graph_layout : bool, optional
            If true, the fixed graph layout is enabled, be default false.
        """
        with st.sidebar:
            self.render_sidebar(
                sidebar_values, supports_fixed_graph_layout=supports_fixed_graph_layout
            )

    def display_back_button(self) -> None:
        """Displays the back button. The button navigates back to the home page."""
        with self.back_button_column:
            home_button("Back", width="stretch")

    def display_export_button(self, disabled=False) -> None:
        """Displays the export button. The button is disabled while the graph is loading.

        Parameters
        ----------
        disabled : bool, optional
            If True, the button is disabled, by default False
        """
        with self.export_button_container:
            navigation_button(
                "Export",
                "Export",
                width="stretch",
                disabled=disabled,
                key="export_button-" + str(disabled),
            )

    def display_graph(self, graph) -> None:
        """Displays the graph in the graph container.

        Parameters
        ----------
        graph : BaseGraph
            The graph to be displayed.
        """
        with self.graph_container:
            if graph is not None:
                interactiveGraph(
                    graph,
                    onClick=self.display_element_info,
                    height=self.graph_height,
                )

    def display_loading_spinner(self, message: str, operation) -> None:
        """Displays a loading spinner while an operation is running.

        Parameters
        ----------
        message : str
            The message to be displayed in the spinner.
        operation : function
            The operation to be executed.
        """
        with self.graph_container:
            with st.spinner(message):
                operation()

    def display_element_info(self, title: str, description: str) -> None:
        """Displays the information of a node or edge in the node data container.

        Parameters
        ----------
        title : str
            The name of the node or edge.
        description : str
            The description of the node or edge.
        """
        with self.node_data_container:
            with st.expander(title):
                for line in description.split("\n"):
                    st.write(line)

    def display_page_title(self, title: str) -> None:
        """Displays the page title. If the algorithm has documentation, a button is displayed to navigate to the documentation.

        Parameters
        ----------
        title : str
            The title of the page.
        """
        from config import docs_path_mappings

        if st.session_state.algorithm not in docs_path_mappings:
            st.title(title)

        else:
            title_column, button_column = st.columns([3, 1])
            with title_column:
                st.title(title)
            with button_column:
                navigation_button(
                    "Algorithm Explanation",
                    "Documentation",
                    width="stretch",
                )
