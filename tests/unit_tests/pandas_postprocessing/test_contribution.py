# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from datetime import datetime

import pytest
from numpy import nan
from numpy.testing import assert_array_equal
from pandas import DataFrame

from superset.exceptions import InvalidPostProcessingError
from superset.utils.core import DTTM_ALIAS, PostProcessingContributionOrientation
from superset.utils.pandas_postprocessing import contribution

df_template = DataFrame(
    {
        DTTM_ALIAS: [
            datetime(2020, 7, 16, 14, 49),
            datetime(2020, 7, 16, 14, 50),
            datetime(2020, 7, 16, 14, 51),
        ],
        "a": [1, 3, nan],
        "b": [1, 9, nan],
        "c": [nan, nan, nan],
    }
)


def test_non_numeric_columns():
    with pytest.raises(InvalidPostProcessingError, match="not numeric"):
        contribution(df_template.copy(), columns=[DTTM_ALIAS])


def test_rename_should_have_same_length():
    with pytest.raises(InvalidPostProcessingError, match="same length"):
        contribution(df_template.copy(), columns=["a"], rename_columns=["aa", "bb"])


def test_cell_contribution_across_row():
    processed_df = contribution(
        df_template.copy(),
        orientation=PostProcessingContributionOrientation.ROW,
    )
    assert processed_df.columns.tolist() == [DTTM_ALIAS, "a", "b", "c"]
    assert_array_equal(processed_df["a"].tolist(), [0.5, 0.25, nan])
    assert_array_equal(processed_df["b"].tolist(), [0.5, 0.75, nan])
    assert_array_equal(processed_df["c"].tolist(), [nan, nan, nan])


def test_cell_contribution_across_column_without_temporal_column():
    df = df_template.copy()
    df.pop(DTTM_ALIAS)
    processed_df = contribution(
        df, orientation=PostProcessingContributionOrientation.COLUMN
    )
    assert processed_df.columns.tolist() == ["a", "b", "c"]
    assert_array_equal(processed_df["a"].tolist(), [0.25, 0.75, 0])
    assert_array_equal(processed_df["b"].tolist(), [0.1, 0.9, 0])
    assert_array_equal(processed_df["c"].tolist(), [nan, nan, nan])


def test_contribution_on_selected_columns():
    df = df_template.copy()
    df.pop(DTTM_ALIAS)
    processed_df = contribution(
        df,
        orientation=PostProcessingContributionOrientation.COLUMN,
        columns=["a"],
        rename_columns=["pct_a"],
    )
    assert processed_df.columns.tolist() == ["a", "b", "c", "pct_a"]
    assert_array_equal(processed_df["a"].tolist(), [1, 3, nan])
    assert_array_equal(processed_df["b"].tolist(), [1, 9, nan])
    assert_array_equal(processed_df["c"].tolist(), [nan, nan, nan])
    assert processed_df["pct_a"].tolist() == [0.25, 0.75, 0]


def test_contribution_with_time_shift_columns():
    df = DataFrame(
        {
            DTTM_ALIAS: [
                datetime(2020, 7, 16, 14, 49),
                datetime(2020, 7, 16, 14, 50),
            ],
            "a": [3, 6],
            "b": [3, 3],
            "c": [6, 3],
            "a__1 week ago": [2, 2],
            "b__1 week ago": [1, 1],
            "c__1 week ago": [1, 1],
        }
    )
    processed_df = contribution(
        df,
        orientation=PostProcessingContributionOrientation.ROW,
        time_shifts=["1 week ago"],
    )
    assert processed_df.columns.tolist() == [
        DTTM_ALIAS,
        "a",
        "b",
        "c",
        "a__1 week ago",
        "b__1 week ago",
        "c__1 week ago",
    ]
    assert_array_equal(processed_df["a"].tolist(), [0.25, 0.5])
    assert_array_equal(processed_df["b"].tolist(), [0.25, 0.25])
    assert_array_equal(processed_df["c"].tolist(), [0.50, 0.25])
    assert_array_equal(processed_df["a__1 week ago"].tolist(), [0.5, 0.5])
    assert_array_equal(processed_df["b__1 week ago"].tolist(), [0.25, 0.25])
    assert_array_equal(processed_df["c__1 week ago"].tolist(), [0.25, 0.25])


def test_contribution_with_row_limit_mode():
    """Test percentage calculation with row_limit mode (default behavior)"""
    df = DataFrame(
        {
            "category": ["A", "B", "C"],
            "sales": [100, 200, 300],
        }
    )
    # Default mode (row_limit) - percentages based on current df
    processed_df = contribution(
        df,
        orientation=PostProcessingContributionOrientation.COLUMN,
        columns=["sales"],
        rename_columns=["pct_sales"],
        percentage_calculation_mode="row_limit",
    )
    assert processed_df.columns.tolist() == ["category", "sales", "pct_sales"]
    # Total is 600, so percentages are 100/600, 200/600, 300/600
    assert_array_equal(
        processed_df["pct_sales"].tolist(), [100 / 600, 200 / 600, 300 / 600]
    )


def test_contribution_with_all_records_mode():
    """Test percentage calculation with all_records mode using provided totals"""
    df = DataFrame(
        {
            "category": ["A", "B", "C"],
            "sales": [100, 200, 300],
        }
    )
    # all_records mode with totals from full dataset
    # Simulate that total sales across ALL records is 10000
    totals = {"sales": 10000.0}
    processed_df = contribution(
        df,
        orientation=PostProcessingContributionOrientation.COLUMN,
        columns=["sales"],
        rename_columns=["pct_sales"],
        totals=totals,
        percentage_calculation_mode="all_records",
    )
    assert processed_df.columns.tolist() == ["category", "sales", "pct_sales"]
    # Percentages based on total of 10000
    assert_array_equal(
        processed_df["pct_sales"].tolist(), [100 / 10000, 200 / 10000, 300 / 10000]
    )


def test_contribution_with_totals_multiple_columns():
    """Test percentage calculation with totals for multiple columns"""
    df = DataFrame(
        {
            "category": ["A", "B"],
            "sales": [100, 200],
            "profit": [10, 20],
        }
    )
    totals = {"sales": 1000.0, "profit": 100.0}
    processed_df = contribution(
        df,
        orientation=PostProcessingContributionOrientation.COLUMN,
        columns=["sales", "profit"],
        rename_columns=["pct_sales", "pct_profit"],
        totals=totals,
    )
    assert processed_df.columns.tolist() == [
        "category",
        "sales",
        "profit",
        "pct_sales",
        "pct_profit",
    ]
    assert_array_equal(processed_df["pct_sales"].tolist(), [100 / 1000, 200 / 1000])
    assert_array_equal(processed_df["pct_profit"].tolist(), [10 / 100, 20 / 100])
