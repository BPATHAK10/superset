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
import logging
from typing import Any, Optional

import pandas as pd
from flask_babel import lazy_gettext as _
from werkzeug.datastructures import FileStorage

from superset.commands.database.exceptions import DatabaseUploadFailed
from superset.commands.database.uploaders.base import (
    BaseDataReader,
    DataTypeError,
    FileMetadata,
    ReaderOptions,
)

logger = logging.getLogger(__name__)

READ_CSV_CHUNK_SIZE = 1000
ROWS_TO_READ_METADATA = 2


class CSVReaderOptions(ReaderOptions, total=False):
    delimiter: str
    column_data_types: dict[str, str]
    column_dates: list[str]
    columns_read: list[str]
    index_column: str
    day_first: bool
    decimal_character: str
    header_row: int
    null_values: list[str]
    rows_to_read: int
    skip_blank_lines: bool
    skip_initial_space: bool
    skip_rows: int


class CSVReader(BaseDataReader):
    def __init__(
        self,
        options: Optional[CSVReaderOptions] = None,
    ) -> None:
        options = options or {}
        super().__init__(
            options=dict(options),
        )

    @staticmethod
    def _validate_column_types(
        df: pd.DataFrame,
        column_data_types: dict[str, str],
        skip_rows: int = 0,
        header_row: int = 0,
    ) -> tuple[list[DataTypeError], int]:
        """
        Validate column data types and collect detailed errors.
        
        :param df: DataFrame with columns read as strings
        :param column_data_types: Expected types for columns
        :param skip_rows: Number of rows skipped at file start
        :param header_row: Header row position
        :return: Tuple of (list of errors up to MAX_ERRORS_TO_SHOW, total error count)
        """
        from superset.commands.database.uploaders.base import MAX_ERRORS_TO_SHOW
        
        errors: list[DataTypeError] = []
        total_errors = 0
        
        for column, expected_type in column_data_types.items():
            if column not in df.columns:
                continue
                
            for idx, value in enumerate(df[column]):
                # Skip null/empty values
                if pd.isna(value) or value == "":
                    continue

                is_valid = True
                error_msg = ""
                
                try:
                    if expected_type in ("int64", "Int64", "integer", "int"):
                        int(value)
                    elif expected_type in ("float64", "Float64", "float"):
                        float(value)
                    elif expected_type == "bool":
                        if str(value).lower() not in ("true", "false", "0", "1"):
                            raise ValueError(f"Cannot convert '{value}' to boolean")
                    elif "datetime" in expected_type.lower() or expected_type == "date":
                        pd.to_datetime(value)
                    # For other types, we assume they're valid
                except (ValueError, TypeError) as e:
                    is_valid = False
                    error_msg = str(e)
                
                if not is_valid:
                    total_errors += 1
                    
                    # Only collect up to MAX_ERRORS_TO_SHOW
                    if len(errors) < MAX_ERRORS_TO_SHOW:
                        # Calculate actual line number in file
                        # idx is 0-based row in dataframe
                        line_number = skip_rows + header_row + idx + 2
                        
                        errors.append(
                            DataTypeError(
                                column=column,
                                expected_type=expected_type,
                                invalid_value=str(value),
                                line_number=line_number,
                                error_message=error_msg or f"Could not convert to {expected_type}",
                            )
                        )
        
        return errors, total_errors

    @staticmethod
    def _read_csv(file: FileStorage, kwargs: dict[str, Any]) -> pd.DataFrame:
        # Extract dtype and skip_rows for potential error handling
        column_data_types = kwargs.get("dtype")
        skip_rows = kwargs.get("skiprows", 0)
        header_row = kwargs.get("header", 0)
        
        # Datetime columns should use parse_dates instead
        # Filter out datetime types from dtype dict before passing to pandas
        if column_data_types:
            dtype_for_pandas = {}
            datetime_columns = []
            
            for col, dtype in column_data_types.items():
                if dtype in ('datetime', 'datetime64', 'date'):
                    datetime_columns.append(col)
                else:
                    dtype_for_pandas[col] = dtype
            
            # Update kwargs with filtered dtype
            if dtype_for_pandas:
                kwargs["dtype"] = dtype_for_pandas
            else:
                kwargs.pop("dtype", None)
            
            # Add datetime columns to parse_dates if not already there
            if datetime_columns:
                parse_dates = kwargs.get("parse_dates", [])
                if isinstance(parse_dates, list):
                    parse_dates = list(set(parse_dates + datetime_columns))
                    kwargs["parse_dates"] = parse_dates

        try:
            if "chunksize" in kwargs:
                df = pd.concat(
                    pd.read_csv(
                        filepath_or_buffer=file.stream,
                        **kwargs,
                    )
                )
            else:
                df = pd.read_csv(
                    filepath_or_buffer=file.stream,
                    **kwargs,
                )
            
            # For datetime columns, pandas parse_dates silently converts invalid dates to NaT
            if column_data_types:
                datetime_cols = [
                    col for col, dtype in column_data_types.items()
                    if dtype in ('datetime', 'datetime64', 'date')
                ]
                
                if datetime_cols and any(col in df.columns for col in datetime_cols):
                    # Check if we need to validate datetime columns
                    needs_validation = False
                    for col in datetime_cols:
                        if col in df.columns:
                            if df[col].isna().any():
                                needs_validation = True
                                break
                    
                    if needs_validation:
                        raise ValueError("Invalid datetime values detected")
            
            return df
        except (
            pd.errors.ParserError,
            pd.errors.EmptyDataError,
            UnicodeDecodeError,
        ) as ex:
            raise DatabaseUploadFailed(
                message=_("Parsing error: %(error)s", error=str(ex))
            ) from ex
        except ValueError as ex:
            # ValueError is raised for dtype conversion errors
            if column_data_types:
                try:
                    # Reset file stream to beginning
                    file.stream.seek(0)
                    
                    # Re-read CSV as strings to validate types manually
                    kwargs_no_dtype = kwargs.copy()
                    kwargs_no_dtype.pop("dtype", None)
                    kwargs_no_dtype.pop("parse_dates", None)  # Don't parse dates
                    kwargs_no_dtype["dtype"] = str  # Read all as strings
                    kwargs_no_dtype["keep_default_na"] = False
                    
                    if "chunksize" in kwargs_no_dtype:
                        df_str = pd.concat(
                            pd.read_csv(
                                filepath_or_buffer=file.stream,
                                **kwargs_no_dtype,
                            )
                        )
                    else:
                        df_str = pd.read_csv(
                            filepath_or_buffer=file.stream,
                            **kwargs_no_dtype,
                        )
                    
                    # Validate types and collect errors
                    errors, total_errors = CSVReader._validate_column_types(
                        df_str, column_data_types, skip_rows, header_row
                    )
                    
                    if errors:
                        # Build the error message as a string with all the detail about the errors
                        error_header = f"Data type conversion errors found ({total_errors} total, showing {len(errors)}):\n"
                        error_details = "\n".join(
                            [
                                f"  • Line {error['line_number']}: "
                                f"Column '{error['column']}' - "
                                f"Expected {error['expected_type']}, "
                                f"got '{error['invalid_value']}' "
                                f"({error['error_message']})"
                                for error in errors
                            ]
                        )
                        raise DatabaseUploadFailed(
                            message=error_header + error_details,
                            exception=ex,
                        ) from ex
                except DatabaseUploadFailed:
                    # Re-raise exception 
                    raise
                except Exception:
        
                    pass
            
            # Fallback to generic error
            raise DatabaseUploadFailed(
                message=_("Parsing error: %(error)s", error=str(ex))
            ) from ex
        except TypeError as ex:
            # TypeError can occur with invalid dtype specifications
            raise DatabaseUploadFailed(
                message=_("Invalid data type specification: %(error)s", error=str(ex))
            ) from ex
        except Exception as ex:
            raise DatabaseUploadFailed(_("Error reading CSV file")) from ex

    def file_to_dataframe(self, file: FileStorage) -> pd.DataFrame:
        """
        Read CSV file into a DataFrame

        :return: pandas DataFrame
        :throws DatabaseUploadFailed: if there is an error reading the file
        """
        kwargs = {
            "chunksize": READ_CSV_CHUNK_SIZE,
            "encoding": "utf-8",
            "header": self._options.get("header_row", 0),
            "decimal": self._options.get("decimal_character", "."),
            "index_col": self._options.get("index_column"),
            "dayfirst": self._options.get("day_first", False),
            "iterator": True,
            "keep_default_na": not self._options.get("null_values"),
            "usecols": self._options.get("columns_read")
            if self._options.get("columns_read")  # None if an empty list
            else None,
            "na_values": self._options.get("null_values")
            if self._options.get("null_values")  # None if an empty list
            else None,
            "nrows": self._options.get("rows_to_read"),
            "parse_dates": self._options.get("column_dates"),
            "sep": self._options.get("delimiter", ","),
            "skip_blank_lines": self._options.get("skip_blank_lines", False),
            "skipinitialspace": self._options.get("skip_initial_space", False),
            "skiprows": self._options.get("skip_rows", 0),
            "dtype": self._options.get("column_data_types")
            if self._options.get("column_data_types")
            else None,
        }
        return self._read_csv(file, kwargs)

    def file_metadata(self, file: FileStorage) -> FileMetadata:
        """
        Get metadata from a CSV file

        :return: FileMetadata
        :throws DatabaseUploadFailed: if there is an error reading the file
        """
        kwargs = {
            "nrows": ROWS_TO_READ_METADATA,
            "header": self._options.get("header_row", 0),
            "sep": self._options.get("delimiter", ","),
        }
        df = self._read_csv(file, kwargs)
        return {
            "items": [
                {
                    "column_names": df.columns.tolist(),
                    "sheet_name": None,
                }
            ]
        }
