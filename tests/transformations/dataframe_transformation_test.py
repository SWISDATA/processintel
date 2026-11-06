import pandas as pd
import unittest

from app.exceptions.io_exceptions import InvalidColumnNameException
from app.transformations.dataframe_transformations import DataframeTransformations
from app.transformations.utils import cases_list_to_dict


class TestDataframeTransformations(unittest.TestCase):

    def read_csv(path: str) -> pd.DataFrame:
        return pd.read_csv(path)

    def setUp(self):
        self.transformations = DataframeTransformations()

    def test_cases_list_to_dict(self):
        cases_list = [
            ["a", "b"],
            ["a", "b"],
            ["a", "b", "c"],
            ["b", "c"],
        ]
        cases_dict = {
            ("a", "b"): 2,
            ("a", "b", "c"): 1,
            ("b", "c"): 1,
        }
        self.assertEqual(cases_list_to_dict(cases_list), cases_dict)

    def test_dataframe_to_cases_list(self):
        dataframe = pd.DataFrame(
            {
                "timestamp": [1, 2, 3, 4, 5],
                "case": ["a", "a", "a", "b", "b"],
                "event": ["b", "b", "c", "c", "d"],
            }
        )
        self.transformations.set_dataframe(dataframe)

        cases_list = [
            ["b", "b", "c"],
            ["c", "d"],
        ]
        self.assertEqual(self.transformations.dataframe_to_cases_list(), cases_list)

    def test_dataframe_to_cases_dict_with_test_csv(self):
        dataframe = TestDataframeTransformations.read_csv("tests/testcsv/test_csv.csv")
        self.transformations.set_dataframe(dataframe)

        cases_dict = {
            ("a", "e"): 5,
            ("a", "b", "c", "e"): 10,
            ("a", "c", "b", "e"): 10,
            ("a", "b", "e"): 1,
            ("a", "c", "e"): 1,
            ("a", "d", "e"): 10,
            ("a", "d", "d", "e"): 2,
            ("a", "d", "d", "d", "e"): 1,
        }
        self.assertEqual(self.transformations.dataframe_to_cases_dict(), cases_dict)

    def test_dataframe_to_cases_dict_with_basicexampl_with_custom_label_names(self):

        dataframe = TestDataframeTransformations.read_csv(
            "tests/testcsv/basicexample.csv"
        )
        self.transformations.set_dataframe(dataframe)

        cases_dict = {
            ("a", "b", "c", "d"): 2,
            ("a", "c", "b", "d"): 1,
            ("a", "b", "b", "c", "d"): 1,
        }

        self.assertEqual(
            self.transformations.dataframe_to_cases_dict(
                caseLabel="case", eventLabel="event", timeLabel="time"
            ),
            cases_dict,
        )

    def test_dataframe_to_cases_dict_throws_exception_when_column_name_does_not_exist(
        self,
    ):
        dataframe = pd.DataFrame(
            {
                "timestamp": [1, 2, 3, 4, 5],
                "case": ["a", "a", "a", "b", "b"],
                "event": ["b", "b", "c", "c", "d"],
            }
        )
        self.transformations.set_dataframe(dataframe)
        with self.assertRaises(InvalidColumnNameException):
            self.transformations.dataframe_to_cases_dict(timeLabel="time")

    def test_dataframe_transformation_without_setting_dataframe(self):
        with self.assertRaises(ValueError):
            self.transformations.dataframe_to_cases_dict()


if __name__ == "__main__":
    unittest.main()
