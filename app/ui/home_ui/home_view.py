import base64
import os
import streamlit as st


from app.components.buttons import navigation_button
from app.config import algorithm_mappings, ASSETS_DIR, DEMO_DATASET_PATH
from app.ui.base_ui.base_view import BaseView
from app.components.footer import footer


@st.cache_data
def load_svg_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


class HomeView(BaseView):
    """View for the Home page."""

    def create_layout(self):
        """Creates the layout for the Home page."""
        super().create_layout()
        _, self.content_column, _ = st.columns([1, 3, 1])

    def display_intro(self):
        """Displays the introduction text for the Home page."""
        with self.content_column:
            svg_base64 = load_svg_base64(
                os.path.join(ASSETS_DIR, "process_intel_logo.svg")
            )
            st.markdown(
                f"""
                <div style="display:flex; align-items:center; gap:10px;">
                    <h1 style="margin:0;">ProcessIntel</h1>
                    <img
                        src="data:image/svg+xml;base64,{svg_base64}"
                        width="60"
                        style="height:auto;"
                    />
                </div>
            """,
                unsafe_allow_html=True,
            )

            st.write(
                "Welcome to ProcessIntel the transparent open-source application for process mining, event log visualization, and interactive exploration of process models."
            )
            st.write(
                """ProcessIntel enables you to:
- import and transform event logs
- discover process models 
  - by using state-of-the-art process mining algorithms 
  - by setting many parameters
  - and getting transparent explanations how the process models were discovered
- to explore results through an interactive graph-based interface
- export
  - process models
  - your workspace
  """
            )

    def display_file_upload(self, file_types: list[str]):
        """Displays the file upload component.

        Parameters
        ----------
        file_types : list[str]
            The allowed file types.
        """
        with self.content_column:
            st.file_uploader(
                "Upload a file",
                type=file_types,
                accept_multiple_files=False,
                key="uploaded_file",
            )

    def display_demo_dataset(self):
        """Displays the demo dataset component. The demo dataset can be loaded directly or donwloaded."""
        with self.content_column:
            st.markdown("##### Test on a demo dataset")
            st.write(
                "Load an ai generated demo dataset of an online shop to try out the mining algorithms, or download it to inspect it in more detail"
            )
            load_column, download_column = st.columns(2)
            with load_column:
                navigation_button(
                    label="Load demo dataset",
                    route="ColumnSelection",
                    width="stretch",
                    beforeNavigate=self.controller.set_demo_df,
                )
            with download_column:
                st.download_button(
                    label="Download demo dataset",
                    data=self.controller.get_demo_dataset(),
                    file_name=os.path.basename(DEMO_DATASET_PATH),
                    width="stretch",
                )

    def display_model_import(self, model):
        """Displays the model import component. A dropdown is displayed to select the mining algorithm.

        Parameters
        ----------
        model : MiningInterface
            The mining model to be imported.
        """
        with self.content_column:
            algorithm_col, _, button_column = st.columns([2, 2, 1])
            with algorithm_col:
                selection = st.selectbox(
                    "Mining Algorthm", list(algorithm_mappings.keys())
                )

            with button_column:
                st.write("")
                navigation_button(
                    label="Import Model",
                    route="Algorithm",
                    width="stretch",
                    beforeNavigate=self.controller.set_model_and_algorithm,
                    args=(model, algorithm_mappings[selection]),
                )

    def display_df_import(self, detected_delimiter: str, show_delimiter: bool = True):
        """Displays the dataframe import component. A text input is displayed to enter
        the delimiter.

        Parameters
        ----------
        detected_delimiter : str
            The detected delimiter of the CSV file. For file types that do not use a delimiter,
            an emtpy string is passed.
        show_delimiter : bool, optional
            Whether to display the delimiter input field, by default True.
        """
        with self.content_column:
            delimiter_col, _, button_column = st.columns([1, 3, 1])
            delimiter = ""

            if show_delimiter:
                with delimiter_col:
                    delimiter = st.text_input(
                        "Delimiter",
                        value=detected_delimiter,
                        key="delimiter",
                        max_chars=1,
                    )

            with button_column:
                st.write("")
                navigation_button(
                    label="Mine from File",
                    route="ColumnSelection",
                    width="stretch",
                    beforeNavigate=self.controller.set_df,
                    args=(delimiter,),
                )

    def display_file_converter(self):
        """Displays the file converter component."""
        with self.content_column:
            st.markdown("##### File Format Converter")
            st.write(
                "Convert and download your process log files between different formats (CSV ↔ XES)"
            )
        with self.content_column:
            tab1, tab2 = st.tabs(["CSV to XES", "XES to CSV"])
            with tab1:
                self._display_csv_to_xes_converter()

            with tab2:
                self._display_xes_to_csv_converter()

    def _display_xes_to_csv_converter(self):
        """Render the XES -> CSV converter UI"""
        xes_file = st.file_uploader(
            "Choose XES file",
            type="xes",
            accept_multiple_files=False,
            key="convert_xes",
        )

        delimiter = st.selectbox(
            "CSV delimiter",
            [",", ";", "\t", "|"],
            key="xes_csv_delimiter",
            format_func=lambda x: {
                ",": "Comma (,)",
                ";": "Semicolon (;)",
                "\t": "Tab",
                "|": "Pipe (|)",
            }[x],
        )

        include_all_attributes = st.checkbox(
            "Include all attributes (preserve XES column names)",
            value=True,
            key="include_all_attrs",
            help="Keep all event/case attributes with original XES column names. Recommended for round-trip conversion.",
        )

        self.controller.handle_xes_to_csv_input_change(
            xes_file,
            delimiter,
            include_all_attributes,
        )

        if xes_file is not None:
            if not st.session_state.get("converted_csv_ready", False):
                if st.button(
                    "Convert to CSV",
                    key="convert_xes_to_csv_button",
                    width="stretch",
                ):
                    self.controller.convert_xes_to_csv(
                        xes_file, delimiter, include_all_attributes
                    )
                    if st.session_state.get("converted_csv_ready", False):
                        st.rerun()
            else:
                df = st.session_state.get("converted_csv_df")
                csv_data = st.session_state.get("converted_csv_data")
                csv_filename = st.session_state.get("converted_csv_filename")

                st.download_button(
                    label="Download CSV File",
                    data=csv_data,
                    file_name=csv_filename,
                    mime="text/csv",
                    key="download_csv_file",
                    width="stretch",
                )

                if df is not None:
                    case_col = (
                        "case:concept:name"
                        if "case:concept:name" in df.columns
                        else "case_id"
                    )
                    activity_col = (
                        "concept:name" if "concept:name" in df.columns else "activity"
                    )
                    st.info(
                        f"Data Summary:\n\n"
                        f"- Columns: {len(df.columns)}\n"
                        f"- Cases: {df[case_col].nunique() if case_col in df.columns else 'N/A'}\n"
                        f"- Activities: {df[activity_col].nunique() if activity_col in df.columns else 'N/A'}\n"
                        f"- Events: {len(df)}"
                    )

                    st.subheader("Data Preview")
                    st.dataframe(df.head(10), width="stretch")

    def _display_csv_to_xes_converter(self):
        """Render the CSV -> XES converter UI"""
        csv_file = st.file_uploader(
            "Choose CSV file",
            type="csv",
            accept_multiple_files=False,
            key="convert_csv",
        )

        if csv_file is not None:
            delimiter_col1, delimiter_col2 = st.columns(2)
            with delimiter_col1:
                delimiter_type = st.radio(
                    "Delimiter type:",
                    ["Auto-detect", "Custom"],
                    key="csv_delimiter_type",
                    horizontal=True,
                )

            with delimiter_col2:
                if delimiter_type == "Custom":
                    delimiter = st.text_input(
                        "Enter delimiter:",
                        value=",",
                        key="csv_custom_delimiter",
                    )
                else:
                    delimiter = "auto"

            st.markdown("**Column Mapping:**")
            available_columns = self.controller.determine_columns(csv_file, delimiter)
            predicted_time_col = None
            predicted_case_col = None
            predicted_activity_col = None

            predicted_time_col, predicted_case_col, predicted_activity_col = (
                self.controller.predict_available_columns(available_columns)
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                case_id_col = st.selectbox(
                    "Case ID Column:",
                    options=available_columns if available_columns else [""],
                    index=(
                        self._default_index(available_columns, predicted_case_col)
                        if available_columns
                        else 0
                    ),
                    key="csv_case_id_col",
                    help="Column with case/trace identifiers",
                )

            with col2:
                activity_col = st.selectbox(
                    "Activity Column:",
                    options=available_columns if available_columns else [""],
                    index=(
                        self._default_index(available_columns, predicted_activity_col)
                        if available_columns
                        else 0
                    ),
                    key="csv_activity_col",
                    help="Column with activity names",
                )

            with col3:
                timestamp_col = st.selectbox(
                    "Timestamp Column:",
                    options=available_columns if available_columns else [""],
                    index=(
                        self._default_index(available_columns, predicted_time_col)
                        if available_columns
                        else 0
                    ),
                    key="csv_timestamp_col",
                    help="Column with event timestamps",
                )

            self.controller.handle_csv_to_xes_input_change(
                csv_file,
                delimiter_type,
                delimiter,
                available_columns,
            )

            self.controller.handle_csv_to_xes_column_change(
                {
                    "case_id_col": case_id_col,
                    "activity_col": activity_col,
                    "timestamp_col": timestamp_col,
                }
            )

            if not st.session_state.get("converted_xes_ready", False):
                if st.button(
                    "Convert to XES",
                    key="convert_csv_to_xes",
                    width="stretch",
                ):
                    self.controller.convert_csv_to_xes(
                        csv_file,
                        delimiter,
                        case_id_col,
                        activity_col,
                        timestamp_col,
                    )
                    if st.session_state.get("converted_xes_ready", False):
                        st.rerun()
            else:
                summary = st.session_state.get("converted_xes_summary")
                xes_bytes = st.session_state.get("converted_xes_bytes")
                xes_filename = st.session_state.get("converted_xes_filename")

                st.download_button(
                    label="Download XES File",
                    data=xes_bytes,
                    file_name=xes_filename,
                    mime="application/xml",
                    key="download_xes_file",
                    width="stretch",
                )

                if summary is not None:
                    summary_text = "Data Summary: \n\n"
                    for key in summary.keys():
                        summary_text += f"- {key}: {summary[key]}\n"

                    st.info(summary_text)

                    xes_bytes = st.session_state.get("converted_xes_bytes")

                    if xes_bytes is not None:
                        xes_text = xes_bytes.decode("utf-8")
                        lines = xes_text.splitlines()
                        all_lines = len(lines)
                        preview_lines = lines[:50]

                        if len(lines) > 50:
                            preview_lines.append("...")
                            number_of_lines = 50
                        else:
                            number_of_lines = len(preview_lines)

                        xes_preview = "\n".join(preview_lines)

                        st.subheader("Data Preview")
                        st.write(
                            f"Showing {number_of_lines} lines out of {all_lines} lines of the generated XES file."
                        )
                        st.code(xes_preview, language="xml")

                dropped_rows = st.session_state.get("converted_xes_dropped_rows", 0)
                if dropped_rows > 0:
                    st.warning(
                        f"Removed {dropped_rows} rows with missing values in required columns."
                    )

    def _default_index(self, options: list[str], preferred: str | None) -> int | None:
        """Find the index of the first preferred option in a list of available options.

        Parameters
        ----------
        options : list[str]
            The list of available options.
        preferred : list[str]
            A list of preferred values ordered by priority.

        Returns
        -------
        int | None
            The index of first matching preferred value or None if no match is found.
        """
        if preferred in options:
            return options.index(preferred)
        return 0

    def display_disclaimer(self):
        footer(
            """<div>
                <strong>Disclaimer</strong><br>
                ProcessIntel is hosted and operated as a service by
                <a href="https://swisdata.eu" target="_blank">SWISDATA</a>.<br>
                The application was developed by several authors, including developers from SWISDATA,
                but mainly as part of bachelor's theses at the University of Vienna under the supervision
                of Dr. Marian Lux.<br>
                Source code for self-hosting and further development:
                <a href="https://code.swisdata.eu/SWISDATA/ProcessIntel" target="_blank">
                    https://code.swisdata.eu/SWISDATA/ProcessIntel
                </a> <br>
                ProcessIntel is provided "as is" and under the MIT License.<br>
                No liability is assumed for the correctness, completeness, or reliability of the software or the results it produces.<br>
                For questions or feedback, please contact us via:
                <a href="https://www.swisdata.eu/contact/" target="_blank">
                    https://www.swisdata.eu/contact/
                </a>
            </div>"""
        )
