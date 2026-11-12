from datetime import datetime
from typing import Any
import pandas as pd
import xml.etree.ElementTree as ET
import numpy as np


class CsvToXesConverter:
    """Converter for transforming CSV event logs into XES format."""

    xes_case_col = "case:concept:name"
    xes_activity_col = "concept:name"
    xes_timestamp_col = "time:timestamp"

    def convert(
        self,
        df: pd.DataFrame,
        case_id_col: str,
        activity_col: str,
        timestamp_col: str,
    ) -> tuple[ET.ElementTree, dict[str, int], int]:
        """Convert a CSV dataframe to an XES ElementTree.

        Parameters
        ----------
        df : pd.DataFrame
            The passed dataframe to be converted.
        case_id_col : str
            Column containing case IDs.
        activity_col : str
            Column containing name of activities.
        timestamp_col : str
            Column containing timestamps.

        Returns
        -------
        tuple[ET.ElementTree, dict[str, int], int]
            A tuple containing the converted XES XML tree, a summary of the converted data
            and number of rows removed because of missing values in the requeired XES columns.
        """

        self._validate_input(df, case_id_col, activity_col, timestamp_col)

        df = self._rename_columns(df, case_id_col, activity_col, timestamp_col)

        if not pd.api.types.is_datetime64_any_dtype(df[self.xes_timestamp_col]):
            df[self.xes_timestamp_col] = self._parse_timestamps(
                df[self.xes_timestamp_col]
            )

        original_len = len(df)
        df = df.dropna(
            subset=[self.xes_case_col, self.xes_activity_col, self.xes_timestamp_col]
        )
        dropped_rows = original_len - len(df)

        if df.empty:
            raise ValueError(
                "No valid data remaining after processing. Please check your data for missing values."
            )
        # convert only afte removing rows
        df[self.xes_case_col] = df[self.xes_case_col].astype(str)
        df[self.xes_activity_col] = df[self.xes_activity_col].astype(str)

        xes_tree = self._create_xes_tree(df)
        summary = {
            "Columns": len(df.columns),
            "Cases": df[self.xes_case_col].nunique(),
            "Activities": df[self.xes_activity_col].nunique(),
            "Events": len(df),
        }

        return xes_tree, summary, dropped_rows

    def _validate_input(
        self, df: pd.DataFrame, case_id_col: str, activity_col: str, timestamp_col: str
    ) -> None:
        """Validate the selected CSV columns before conversion.

        Parameters
        ----------
        df : pd.DataFrame
            The CSV data as dataframe.
        case_id_col : str
            Column containing case IDs.
        activity_col : str
            Column containing name of activities.
        timestamp_col : str
           Column containing timestamps.

        Raises
        ------
        ValueError
            If columns are missing, duplicated, invalid, if delimiter does not match
            the file, if timestamp parsing fails, or if no valid data remains after processing.
        """
        if not all([case_id_col, activity_col, timestamp_col]):
            raise ValueError(
                "Please select all required columns before converting the file."
            )

        if len(df.columns) <= 1:
            raise ValueError(
                "The selected delimiter does not match the file."
                " Please select the correct delimiter."
            )

        selected_cols = [case_id_col, activity_col, timestamp_col]
        if len(set(selected_cols)) != len(selected_cols):
            raise ValueError(
                "Please select three different columns for case ID, activity, and timestamp. "
            )

        missing_cols = [col for col in selected_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing columns in CSV: {', '.join(missing_cols)}")

    def _rename_columns(
        self,
        df: pd.DataFrame,
        case_id_col: str,
        activity_col: str,
        timestamp_col: str,
    ) -> pd.DataFrame:
        """Rename selected CSV columns according to the XES column names standard.

        Parameters
        ----------
        df : pd.DataFrame
            The CSV data as a dataframe.
        case_id_col : str
            Column containing case IDs.
        activity_col : str
            Column containing name of activities.
        timestamp_col : str
            Column containing timestamps.

        Returns
        -------
        pd.DataFrame
            Dataframe with renamed columns after XES standard.
        """
        column_mapping = {}
        selected_source_columns = {case_id_col, activity_col, timestamp_col}

        df, column_mapping = self._rename_existing_target_column(
            df, column_mapping, case_id_col, self.xes_case_col, selected_source_columns
        )
        df, column_mapping = self._rename_existing_target_column(
            df,
            column_mapping,
            activity_col,
            self.xes_activity_col,
            selected_source_columns,
        )
        df, column_mapping = self._rename_existing_target_column(
            df,
            column_mapping,
            timestamp_col,
            self.xes_timestamp_col,
            selected_source_columns,
        )

        if column_mapping:
            df = df.rename(columns=column_mapping)

        return df

    def _rename_existing_target_column(
        self,
        df: pd.DataFrame,
        column_mapping: dict[str, str],
        selected_col: str,
        xes_col: str,
        selected_source_columns: set[str],
    ) -> tuple[pd.DataFrame, dict[str, str]]:
        """Rename the user-selected column name. If column with the
        same name already exists, preserving the original column by adding
        "original" prefix.

        Parameters
        ----------
        df : pd.DataFrame
            The CSV data as a daraframe.
        column_mapping : dict[str, str]
            Mapping of a selected CSV column names to target XES column names.
        selected_col : str
            The user-selected column.
        xes_col : str
            The target XES column name.
        selected_source_columns: set[str]
            All source columns selected by user.

        Returns
        -------
        tuple[pd.DataFrame, dict[str,str]]
            The updated dataframe and column mappings.
        """
        if selected_col != xes_col:
            if xes_col in df.columns and xes_col not in selected_source_columns:
                original_name = self._get_original_name(xes_col, df.columns.to_list())
                df = df.rename(columns={xes_col: original_name})

            column_mapping[selected_col] = xes_col

        return df, column_mapping

    def _parse_timestamps(self, timestamps: pd.Series) -> pd.Series:
        """Parse timestamps from known timestamps formats.

        Parameters
        ----------
        timestamps : pd.Series
            The timestamps values to parse.

        Returns
        -------
        pd.Series
            Parsed timestamp values.

        Raises
        ------
        ValueError
            If the timestamp values cannot be parsed.
        """
        formats = [
            "%d-%m-%Y:%H.%M",
        ]

        for timestamp_format in formats:
            try:
                return pd.to_datetime(timestamps, format=timestamp_format)
            except (ValueError, TypeError):
                continue

        try:
            return pd.to_datetime(timestamps, format="mixed")
        except (ValueError, TypeError) as e:
            raise ValueError("The timestamp format is unknown.")

    def _get_original_name(self, column_name: str, existing_columns: list[str]) -> str:
        """Create an original name, if it exists add an index to get a unique one.

        Parameters
        ----------
        column_name : str
            The original column name that needs to be preserved.
        existing_columns : list[str]
            List of column names currently present.

        Returns
        -------
        str
            A unique name with "original" prefix. If it exists a number is
            added to make it unique.
        """
        original_name = f"original:{column_name}"
        if original_name not in existing_columns:
            return original_name
        counter = 1

        while f"{original_name}:{counter}" in existing_columns:
            counter += 1

        return f"{original_name}:{counter}"

    def _create_xes_tree(
        self,
        df: pd.DataFrame,
    ) -> ET.ElementTree:
        """Create an XES tree from a XES dataframe.

        Parameters
        ----------
        df : pd.DataFrame
            The DataFrame to export.

        Returns
        -------
        ET.ElementTree
            The created XES XML tree.
        """

        root = ET.Element("log")
        root.set("xes.version", "1.0")
        root.set("xes.features", "nested-attributes")
        root.set("xmlns", "http://www.xes-standard.org/")

        actual_case_col = self.xes_case_col
        actual_activity_col = self.xes_activity_col
        actual_timestamp_col = self.xes_timestamp_col

        standard_cols = {actual_case_col, actual_activity_col, actual_timestamp_col}
        additional_cols = [
            col for col in df.columns if col not in standard_cols and col is not None
        ]

        grouped = df.groupby(actual_case_col)

        for case_id, group in grouped:
            trace_elem = ET.SubElement(root, "trace")

            name_elem = ET.SubElement(trace_elem, "string")
            name_elem.set("key", "concept:name")
            name_elem.set("value", str(case_id))

            if actual_timestamp_col and actual_timestamp_col in group.columns:
                group = group.sort_values(by=actual_timestamp_col)

            for _, row in group.iterrows():
                event_elem = ET.SubElement(trace_elem, "event")

                activity_elem = ET.SubElement(event_elem, "string")
                activity_elem.set("key", "concept:name")
                activity_elem.set("value", str(row[actual_activity_col]))

                ts_value = (
                    row.get(actual_timestamp_col) if actual_timestamp_col else None
                )
                if (
                    actual_timestamp_col
                    and ts_value is not None
                    and not pd.isna(ts_value)
                ):
                    ts_elem = ET.SubElement(event_elem, "date")
                    ts_elem.set("key", "time:timestamp")
                    if isinstance(ts_value, datetime):
                        ts_elem.set("value", ts_value.isoformat())
                    elif isinstance(ts_value, pd.Timestamp):
                        ts_elem.set("value", ts_value.isoformat())
                    else:
                        ts_elem.set("value", str(ts_value))

                for col in additional_cols:
                    col_value = row.get(col)
                    if col_value is not None and not pd.isna(col_value):
                        self._add_attribute(event_elem, col, col_value)

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")

        return tree

    def _add_attribute(self, parent: ET.Element, key: str, value: Any) -> None:
        """Add an attribute element to a parent element.

        Parameters
        ----------
        parent : ET.Element
            The parent element
        key : str
            The attribute key
        value : Any
            The attribute value
        """

        # Handle numpy bool before regular bool (numpy.bool_ is also instance of bool in some cases)
        if isinstance(value, (np.bool_, bool)):
            elem = ET.SubElement(parent, "boolean")
            elem.set("key", key)
            elem.set("value", str(bool(value)).lower())
        elif isinstance(value, (np.integer, int)):
            elem = ET.SubElement(parent, "int")
            elem.set("key", key)
            elem.set("value", str(int(value)))
        elif isinstance(value, (np.floating, float)):
            if np.isnan(value) or np.isinf(value):
                return
            elem = ET.SubElement(parent, "float")
            elem.set("key", key)
            elem.set("value", str(float(value)))
        elif isinstance(value, (datetime, pd.Timestamp, np.datetime64)):
            elem = ET.SubElement(parent, "date")
            elem.set("key", key)
            if isinstance(value, np.datetime64):
                value = pd.Timestamp(value)
            elem.set(
                "value",
                value.isoformat() if hasattr(value, "isoformat") else str(value),
            )
        else:
            elem = ET.SubElement(parent, "string")
            elem.set("key", key)
            elem.set("value", str(value))
