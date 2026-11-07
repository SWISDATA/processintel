import streamlit as st
from app.analysis.detection_model import DetectionModel
from app.analysis.predictions_model import PredictionModel
from app.converters.csv_to_xes_converter import CsvToXesConverter
from app.converters.xes_to_csv_converter import XesToCsvConverter
from app.exceptions.io_exceptions import (
    UnsupportedFileTypeException,
    NotImplementedFileTypeException,
)
from app.io_operations.export_operations import ExportOperations
from app.io_operations.import_operations import ImportOperations
from app.logger import get_logger
from app.ui.base_ui.base_controller import BaseController
from app.config import DEMO_DATASET_PATH


class HomeController(BaseController):
    """Controller for the Home page."""

    def __init__(
        self,
        views=None,
        detection_model: DetectionModel = None,
        import_model: ImportOperations = None,
        export_model: ExportOperations = None,
        supported_file_types: list[str] = None,
        prediction_model: PredictionModel = None,
    ):
        """Initializes the controller for the Home page.

        Parameters
        ----------
        views :  List[BaseView] | BaseView, optional
            The views for the Home page. If None is passed, the HomeView is used, by default None
        detection_model : DetectionModel, optional
            The detection model for detecting file types and delimiters. If None is passed, a new instance is created, by default None
        import_model : ImportOperations, optional
            The import operations model for reading files. If None is passed, a new instance is created, by default None
        export_model : ExportOperations, optional
            The export operations model for writing or exporting files. If None is passed a new instance is created, by default None
        supported_file_types : list[str], optional
            The supported file types. If None is passed, the file suffixes from the config file are used, by default None
        """
        self.detection_model = DetectionModel()
        self.import_model = ImportOperations()
        self.export_model = ExportOperations()
        self.prediction_model = PredictionModel()
        if views is None:
            from app.ui.home_ui.home_view import HomeView

            views = [HomeView()]
        super().__init__(views)
        self.logger = get_logger("HomeController")

        if supported_file_types is None:
            from app.config import import_file_suffixes

            supported_file_types = import_file_suffixes

        self.supported_file_types = supported_file_types

        self.csv_to_xes_converter = CsvToXesConverter()
        self.xes_to_csv_converter = XesToCsvConverter()

    def get_page_title(self) -> str:
        """Returns the page title."""
        return ""

    def process_session_state(self):
        """Process the session state and store uploaded import and converter files."""
        super().process_session_state()
        self.uploaded_file = st.session_state.get("uploaded_file", None)

    def process_file(self, selected_view):
        """Processes the uploaded file and displays the import view.
        The file type is detected and the view is displayed accordingly.

        Parameters
        ----------
        selected_view : BaseView
            The view to display the import view.
        """
        if self.uploaded_file is None:
            return

        try:
            file_type = self.detection_model.detect_file_type(self.uploaded_file)

            if file_type == "csv":
                detected_delimiter = self._determine_delimiter(
                    self.uploaded_file, "auto"
                )
                selected_view.display_df_import(detected_delimiter)
            elif file_type == "pickle":
                model = self.import_model.read_model(self.uploaded_file)
                selected_view.display_model_import(model)
            elif file_type == "xes":
                selected_view.display_df_import("", False)
            else:
                raise NotImplementedFileTypeException(file_type)
        except UnsupportedFileTypeException as e:
            self.logger.exception(e)
            st.session_state.error = e.message
            st.rerun()
        except NotImplementedFileTypeException as e:
            self.logger.exception(e)
            st.session_state.error = e.message
            st.rerun()

    def set_model_and_algorithm(self, model, algorithm: str):
        """Sets the model and algorithm in the session state before navigating to the Algorithm page.

        Parameters
        ----------
        model : MiningInterface
            The mining model to be imported.
        algorithm : str
            The chosen algorithm.
        """
        st.session_state.model = model
        st.session_state.algorithm = algorithm

    def set_df(self, delimiter: str):
        """Creates a dataframe from the uploaded file with the given delimiter.
        Stores the dataframe in the session state and changes the routing to the ColumnSelection page.

        Parameters
        ----------
        delimiter : str
            The delimiter to be used for CSV file, ignored for XES file.
        """
        file_type = self.detection_model.detect_file_type(self.uploaded_file)
        if file_type == "csv":
            if delimiter == "":
                st.session_state.error = "Please enter a delimiter"
                # change routing to home
                st.session_state.page = "Home"
                return
            st.session_state.df = self.import_model.read_csv(
                self.uploaded_file, delimiter
            )
        elif file_type == "xes":
            try:
                xes_tree = self.import_model.read_xes(self.uploaded_file)
                df = self.xes_to_csv_converter.convert(
                    xes_tree, include_all_attributes=True
                )
            except Exception as e:
                self.logger.exception(e)
                st.session_state.error = f"Invalid XES file format:{str(e)}"
                st.session_state.page = "Home"
                return
            if df.empty:
                st.session_state.error = "The XES file contains no event data."
                st.session_state.page = "Home"
                return

            st.session_state.df = df

    def set_demo_df(self):
        """Loads the demo dataset and stores the dataframe in the session state."""
        try:
            st.session_state.df = self.import_model.read_csv(DEMO_DATASET_PATH, ",")
        except Exception as e:
            self.logger.exception(e)
            st.session_state.error = f"Could not load the demo dataset: {str(e)}"

    def get_demo_dataset(self) -> bytes:
        """Returns the content of the demo dataset file.

        Returns
        -------
        bytes
            The demo dataset file as bytes.
        """
        return self.import_model.read_file_binary(DEMO_DATASET_PATH)

    def convert_csv_to_xes(
        self,
        csv_file,
        delimiter: str,
        case_id_col: str,
        activity_col: str,
        timestamp_col: str,
    ):
        """Convert CSV to XES file and store result in session state.

        Parameters
        ----------
        csv_file : UploadedFile
            The uploaded CSV file to convert.
        delimiter : str
            The delimiter used for the CSV file.
        case_id_col : str
            Column containing case IDs.
        activity_col : str
            Column containing name of activities.
        timestamp_col : str
            Column containing timestamps.
        """
        self._reset_csv_to_xes_result()
        try:
            effective_delimiter = self._determine_delimiter(csv_file, delimiter)
            if effective_delimiter == "":
                st.error("Please enter a custom delimiter.")
                return

            df = self.import_model.read_csv(csv_file, effective_delimiter)

            xes_tree, summary, dropped_rows = self.csv_to_xes_converter.convert(
                df,
                case_id_col,
                activity_col,
                timestamp_col,
            )

            if dropped_rows > 0:
                st.warning(
                    f"Removed {dropped_rows} rows with missing values in required columns."
                )

            xes_bytes = self.export_model.export_to_xes_bytes(xes_tree)

            original_filename = csv_file.name.replace(".csv", "")
            xes_filename = f"{original_filename}_converted.xes"

            st.session_state.converted_xes_summary = summary
            st.session_state.converted_xes_bytes = xes_bytes
            st.session_state.converted_xes_filename = xes_filename
            st.session_state.converted_xes_ready = True
            st.session_state.converted_xes_dropped_rows = dropped_rows

        except ValueError as e:
            st.error(f"Error converting CSV to XES: {str(e)}")
        except Exception as e:
            self.logger.exception(e)
            st.error(f"Error converting CSV to XES: {str(e)}")

    def convert_xes_to_csv(
        self,
        xes_file,
        delimiter: str,
        include_all_attributes: bool,
    ):
        """Convert XES to CSV and store result in session state.

        Parameters
        ----------
        xes_file : UploadedFile
            The uploaded XES file to convert.
        delimiter : str
            The delimiter used for the CSV file.
        include_all_attributes: bool
            Whether to include all attributes in the CSV. If True, preserves original XES column names.
            If False, keeps only essential columns with user-friendly names.
        """
        self._reset_xes_to_csv_result()
        try:
            xes_tree = self.import_model.read_xes(xes_file)
            df = self.xes_to_csv_converter.convert(xes_tree, include_all_attributes)

            original_filename = xes_file.name.replace(".xes", "")
            csv_filename = f"{original_filename}_converted.csv"
            csv_data = self.export_model.export_to_csv_data(df, delimiter)

            st.session_state.converted_csv_df = df
            st.session_state.converted_csv_data = csv_data
            st.session_state.converted_csv_filename = csv_filename
            st.session_state.converted_csv_ready = True

        except Exception as e:
            self.logger.exception(e)
            st.error(f"Error converting XES to CSV: {str(e)}")

    def _reset_csv_to_xes_result(self) -> None:
        """Reset CSV to XES conversion results stored in session state."""
        st.session_state.converted_xes_summary = None
        st.session_state.converted_xes_bytes = None
        st.session_state.converted_xes_filename = None
        st.session_state.converted_xes_ready = False
        st.session_state.converted_xes_dropped_rows = 0

    def _reset_xes_to_csv_result(self) -> None:
        """Reset XES to CSV conversion results stored in session state."""
        st.session_state.include_attributes = False
        st.session_state.converted_csv_df = None
        st.session_state.converted_csv_data = None
        st.session_state.converted_csv_filename = None
        st.session_state.converted_csv_ready = False

    def _determine_delimiter(self, csv_file, delimiter: str) -> str:
        """Determine the delimiter for a CSV file.
        If the delimiter is set to "auto", the method detects the delimiter using the detection_model.
        If detection fails, return the default "," delimiter. In case delimiter is custom, returns it directly.

        Parameters
        ----------
        csv_file : UploadedFile
            The uploaded CSV file.
        delimiter : str
            The delimiter can be either "auto" or determined by user.

        Returns
        -------
        str
            The detected or user provided delimiter.
        """
        if delimiter == "auto":
            try:
                line = self.import_model.read_line(csv_file)
                delimiter = self.detection_model.detect_delimiter(line)
                csv_file.seek(0)
            except Exception:
                delimiter = ","
        return delimiter

    def determine_columns(self, csv_file, delimiter: str) -> list[str]:
        """Determine CSV columns using the effective delimiter.

        Parameters
        ----------
        csv_file : UploadedFile
            The uploaded CSV file.
        delimiter : str
            The delimiter to use. If set to "auto", it is detected automatically.

        Returns
        -------
        list[str]
            List of available column names.
        """
        available_columns = []
        try:
            effective_delimiter = self._determine_delimiter(csv_file, delimiter)
            df_preview = self.import_model.read_csv(csv_file, effective_delimiter)
            available_columns = df_preview.columns.tolist()
            csv_file.seek(0)
        except Exception:
            available_columns = []

        return available_columns

    def predict_available_columns(
        self, available_columns: list[str]
    ) -> tuple[str | None, str | None, str | None]:
        """Predict timestamp, case ID, and activity columns.

        Parameters
        ----------
        available_columns : list[str]
            The available CSV columns.

        Returns
        -------
        tuple[str | None, str | None, str | None]
            Predicted timestamp, case ID, and activity columns.
        """
        if not available_columns:
            return None, None, None

        predicted_time_col, predicted_case_col, predicted_activity_col = (
            self.prediction_model.predict_columns(
                available_columns,
                ["time_column", "case_column", "activity_column"],
            )
        )
        return predicted_time_col, predicted_case_col, predicted_activity_col

    def handle_xes_to_csv_input_change(
        self, xes_file, delimiter: str, include_all_attributes: bool
    ) -> None:
        """Handle changes in from XES to CSV converter inputs.

        Parameters
        ----------
        xes_file : UploadedFile | None
            The uploaded XES file.
        delimiter : str
            The selected delimiter.
        include_all_attributes : bool
            Whether to include all attributes in the CSV. If True, preserves original XES column names.
            If False, keeps only essential columns with user-friendly names.
        """
        current_signature = (
            xes_file.name if xes_file is not None else None,
            delimiter,
            include_all_attributes,
        )
        previous_signature = st.session_state.get("xes_to_csv_input_signature")
        if current_signature != previous_signature:
            st.session_state.xes_to_csv_input_signature = current_signature
            self._reset_xes_to_csv_result()

    def handle_csv_to_xes_input_change(
        self,
        csv_file,
        delimiter_type: str,
        delimiter: str,
        available_columns: list[str],
    ) -> None:
        """Handle changes from CSV to XES converter inputs.

        Parameters
        ----------
        csv_file : UploadedFile | None
            The uploaded CSV file.
        delimiter_type : str
            The selected delimiter mode (Auto-detect or Custom).
        delimiter : str
            The delimiter value used for parsing the CSV file.
        available_columns: list[str]
            The columns detected from CSV file.
        """
        current_signature = (
            csv_file.name if csv_file is not None else None,
            delimiter_type,
            delimiter,
            tuple(available_columns),
        )
        previous_signature = st.session_state.get("csv_to_xes_input_signature")
        if current_signature != previous_signature:
            for key in (
                "csv_case_id_col",
                "csv_activity_col",
                "csv_timestamp_col",
            ):
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.csv_to_xes_input_signature = current_signature
            self._reset_csv_to_xes_result()

    def handle_csv_to_xes_column_change(self, column_mapping: dict[str, str]):
        """Handle column changes in CSV to XES converter in selectbox.

        Parameters
        ----------
        column_mapping : dict[str, str]
            The column mappings of required XES columns, used to detect if user changed one of the column selections.
        """
        current_signature = tuple(column_mapping.items())
        previous_signature = st.session_state.get("csv_to_xes_mapping_signature")
        if current_signature != previous_signature:
            st.session_state.csv_to_xes_mapping_signature = current_signature
            self._reset_csv_to_xes_result()

    def run(self, selected_view, index):
        """Runs the controller for the Home page. This method is called to display the Home page and to react to user input.

        Parameters
        ----------
        selected_view : BaseView
            The view to display the import view.
        index : int
            The index of the selected view.
        """
        self.selected_view = selected_view
        selected_view.display_intro()
        selected_view.display_file_upload(self.supported_file_types)
        if self.uploaded_file is not None:
            self.process_file(selected_view)
        selected_view.display_demo_dataset()
        selected_view.display_file_converter()

        selected_view.display_disclaimer()
