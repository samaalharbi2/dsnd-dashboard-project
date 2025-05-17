import pandas as pd

# Import the QueryBase class
from .query_base import QueryBase

# Import the SQL execution mixin 
from .sql_execution import execute_query 


# Define a subclass of QueryBase called Employee
class Employee(QueryBase):
    # Set the class attribute `name` to "employee"
    name = "employee"

    def __init__(self, db_path=None):
        """
        Initialize the database path and allow override from argument.
        """
        super().__init__(db_path=db_path)

    # Define a method called `names` that receives no arguments
    def names(self):
        # Query 3: Select full name and employee id for all employees
        query = """
            SELECT first_name || ' ' || last_name AS full_name,
                   employee_id
            FROM employee
        """
        return self.query(query)

    # Define a method called `username` that receives an `id` argument
    def username(self, id):
        # Query 4: Select full name using WHERE filter
        query = f"""
            SELECT first_name || ' ' || last_name AS full_name
            FROM employee
            WHERE employee_id = ?
        """
        return self.query(query, (id,))

    # Method that returns model data in a pandas DataFrame
    def model_data(self, id):
        query = f"""
            SELECT SUM(positive_events) AS positive_events,
                   SUM(negative_events) AS negative_events
            FROM {self.name}
            JOIN employee_events
            USING({self.name}_id)
            WHERE {self.name}.{self.name}_id = ?
        """
        result = self.query(query, (id,))
        return pd.DataFrame(result, columns=["positive_events", "negative_events"])
