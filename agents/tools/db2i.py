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

class SQLTools(Toolkit):
    def __init__(
        self,
        user: Optional[str] = None,
        password: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        schema: Optional[str] = None,
        tables: Optional[Dict[str, Any]] = None,
        list_tables: bool = True,
        describe_table: bool = True,
        run_sql_query: bool = True,
    ):
        super().__init__(name="db2i_tools")

        # Database connection
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.schema = schema

        # Tables this toolkit can access
        self.tables: Optional[Dict[str, Any]] = tables

        # Register functions in the toolkit
        if list_tables:
            self.register(self.list_tables)
        if describe_table:
            self.register(self.describe_table)
        if run_sql_query:
            self.register(self.run_sql)
            
        self._max_string_length = 300

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
            logger.debug(f"Connecting to database with host: {self.host}, user: {self.user}, port: {self.port}")
            with connect(
                DaemonServer(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    port=self.port or 8075,
                    ignoreUnauthorized=True,
                )
            ) as conn:
                logger.debug(f"Executing SQL: {sql} with options: {options}")
                with conn.execute(sql, options) as cursor:
                    if cursor.has_results:
                        logger.debug(f"SQL execution returned results, fetching data with fetch mode: {fetch}")
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

                        logger.debug(f"Fetched data: {result}")
                        return result["data"]

        except Exception as e:
            logger.error(f"An error occurred while executing: {sql}, Error: {e}")

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