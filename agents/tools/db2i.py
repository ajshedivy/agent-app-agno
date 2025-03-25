import json
from textwrap import dedent
from typing import Any, Dict, Iterator, Literal, Optional, Union
from agno.tools.toolkit import Toolkit
from mapepire_python import Connection, DaemonServer, connect
from pep249 import QueryParameters, ResultRow, ResultSet
from utils.log import logger

def truncate_word(content: Any, *, length: int, suffix: str = "...") -> str:
    """
    Truncate a string to a certain number of words, based on the max string
    length.
    """

    if not isinstance(content, str) or length <= 0:
        return content

    if len(content) <= length:
        return content

    return content[: length - len(suffix)].rsplit(" ", 1)[0] + suffix


class Db2iTools(Toolkit):
    def __init__(
        self,
        schema: str,
        db_details: Union[dict, DaemonServer],
        tables: Optional[Dict[str, Any]] = None,
        list_tables: bool = True,
        describe_table: bool = True,
        run_sql_query: bool = True,
    ):
        super().__init__(name="Db2iTools")

        self.schema = schema
        self.connection_details = db_details
        self.connection = self._create_connection(db_details)
        self.tables: Optional[Dict[str, Any]] = tables

        if list_tables:
            self.register(self.list_tables)

        if describe_table:
            self.register(self.describe_table)

        if run_sql_query:
            self.register(self.run_sql)

    def _create_connection(
        self, details: Union[Dict[str, Any], DaemonServer]
    ) -> Connection:
        connection = connect(details)
        return connection
    
    def get_connection(self) -> Connection:
        if self.connection:
            return self.connection
        return self._create_connection(self.connection_details)
    
    def _execute(
        self,
        sql: str,
        options: Optional[QueryParameters] = None,
        fetch: Union[Literal["all", "one"], int] = "all",
    ) -> ResultRow | ResultSet | list:
        """Execute SQL query and return data

        Args:
            sql (str): _description_
            options (Optional[QueryParameters], optional): _description_. Defaults to None.
            fetch (Union[Literal[&quot;all&quot;, &quot;one&quot;], int], optional): _description_. Defaults to "all".

        Raises:
            ValueError: _description_

        Returns:
            ResultRow | ResultSet | list: _description_
        """
        
        try:
            with connect(self.connection_details) as conn:
                with conn.execute(sql, options) as cursor:
                    if cursor.has_results:
                        if fetch == "all":
                            result = cursor.fetchall()
                        elif fetch == "one":
                            result = cursor.fetchone()
                        elif isinstance(fetch, int):
                            result = []
                            for _ in range(fetch):
                                row = cursor.fetchone()
                                if row is None:
                                    break
                                result.append(row)
                        else:
                            raise ValueError(f"Invalid fetch value: {fetch}")

                        return result["data"]
            
        except Exception as e:
            logger.error(f"An error occured while executing: {sql}")

        return []
    
    def _get_table_definition(self, table: str) -> str:
        sql = dedent(
            f"""
            CALL QSYS2.GENERATE_SQL(
                DATABASE_OBJECT_NAME => ?,
                DATABASE_OBJECT_LIBRARY_NAME => ?,
                DATABASE_OBJECT_TYPE => 'TABLE',
                CREATE_OR_REPLACE_OPTION => '1',
                PRIVILEGES_OPTION => '0',
                STATEMENT_FORMATTING_OPTION => '0',
                SOURCE_STREAM_FILE_END_OF_LINE => 'LF',
                SOURCE_STREAM_FILE_CCSID => 1208
            )
        """
        )
        result = self._execute(sql, options=[table, self.schema])
        return "\n".join(res["SRCDTA"] for res in result)

    def list_tables(self) -> str:
        """Use this function to get a list of table names in the database.

        Returns:
            str: list of tables in the database.
        """
        if self.tables is not None:
            return json.dumps(self.tables)
        
        try:
            sql = f"""
                SELECT TABLE_NAME as name, TABLE_TYPE
                FROM QSYS2.SYSTABLES
                WHERE TABLE_SCHEMA = ? AND TABLE_TYPE = 'T'
                ORDER BY TABLE_NAME        
            """

            options = [self.schema]
            result = self._execute(sql, options=options, fetch="all")
            names = [row["NAME"] for row in result]

            return json.dumps(names)
        except Exception as e:
            logger.error(f"Error getting tables: {e}")
            return f"Error getting tables: {e}"
        
    def describe_table(self, table_name: str) -> str:
        """Use this function to describe a table.

        Args:
            table_name (str): The name of the table to get the schema for.

        Returns:
            str: schema of a table
        """
        try:
            logger.debug(f"Describing table: {table_name}")
            definition = self._get_table_definition(table_name)
            return definition
        except Exception as e:
            logger.error(f"Error getting table schema: {e}")
            return f"Error getting table schema: {e}"
        
    def run_sql(
        self,
        sql: str,
        options: Optional[QueryParameters] = None,
        include_columns: bool = False,
        fetch: Union[Literal["all", "one"], int] = "all",
    ) -> str | ResultRow | ResultSet | list:
        """Use this function to run a SQL query and return the result.

        Args:
            sql (str): The SQL query to execute.
            options (Optional[QueryParameters], optional): Parameters to pass to the query. Defaults to None.
            include_columns (bool, optional): Whether to include column names in the result. Defaults to False.
            fetch (Union[Literal["all", "one"], int], optional): Specifies how many rows to fetch:
                - "all": Fetch all rows (default).
                - "one": Fetch a single row.
                - int: Fetch a specific number of rows.

        Returns:
            str | ResultRow | ResultSet | list: The result of the SQL query. The format depends on the `fetch` parameter.
        Notes:
            - The result may be empty if the query does not return any data.
        """
        result = self._execute(sql, options=options, fetch=fetch)

        if fetch == "cursor":
            return result

        res = [
            {
                column: truncate_word(value, length=self._max_string_length)
                for column, value in r.items()
            }
            for r in result
        ]

        if not include_columns:
            res = [tuple(row.values()) for row in res]  # type: ignore[misc]

        if not res:
            return ""
        else:
            return str(res)
        
    # def __iter__(self) -> Iterator:
    #     """Make the toolkit iterable by returning an iterator of registered tools."""
    #     return iter(self.get_registered_tools())
    
    # def get_registered_tools(self):
    #     """Return the list of registered tools."""
    #     # Access the tools from the parent Toolkit class
    #     # This might need adjustment based on how Toolkit class is implemented
    #     return self.tools if hasattr(self, "tools") else []

        
        
        
    
