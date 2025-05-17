import sys
from pathlib import Path
import importlib
import matplotlib.pyplot as plt
import pandas as pd
import sqlite3
import os

# Set up path for local modules
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root / "python-package"))

# Try importing employee module
try:
    employee_events = importlib.import_module('employee_events.employee')
    print("Module loaded successfully!")
except ModuleNotFoundError:
    print("Module not found!")

# Import fasthtml
from fasthtml import FastHTML, serve
from fasthtml.common import Select, Label, Div, H1, Option, RedirectResponse

# Database path
db_file = project_root / "python-package" / "employee_events" / "employee_events.db"

# Import models and functions
from employee_events.employee import Employee
from employee_events.team import Team
from report.utils import load_model
from report.base_components import Dropdown, BaseComponent, Radio, MatplotlibViz, DataTable
from report.combined_components import FormGroup, CombinedComponent

# Create app
app = FastHTML(static_dir="assets")

# Custom Dropdown
class ReportDropdown(Dropdown):
    def build_component(self, entity_id, model):
        self.label = model.name
        return super().build_component(entity_id, model)

    def component_data(self, entity_id, model):
        return model.names()

# Header
class Header(BaseComponent):
    def build_component(self, entity_id, model):
        return H1(f"{model.name} Performance Dashboard")

# Line chart
class LineChart(MatplotlibViz):
    def visualization(self, entity_id, model):
        data = model.event_counts(entity_id)
        data = data.fillna(0)
        data['event_date'] = pd.to_datetime(data['event_date'])
        data.set_index('event_date', inplace=True)
        data = data.sort_index()
        data.rename(columns={"positive_events": "Positive", "negative_events": "Negative"}, inplace=True)

        if not set(["Positive", "Negative"]).issubset(data.columns):
            raise KeyError("Missing required columns")

        data[["Positive", "Negative"]] = data[["Positive", "Negative"]].apply(pd.to_numeric, errors="coerce")
        data = data.cumsum()

        fig, ax = plt.subplots(figsize=(8, 4))
        if data.empty:
            raise ValueError("No data to plot")
        
        # Use default style but customize colors
        data.plot(ax=ax, color=['#4CAF50', '#F44336'], linewidth=2.5)
        
        self.set_axis_styling(ax, bordercolor='#ddd', fontcolor='#555')
        ax.set_title("Event Trends Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Cumulative Event Count")
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend(frameon=True, facecolor='white')
        
        fig.tight_layout()
        return fig

# Bar chart
class BarChart(MatplotlibViz):
    predictor = load_model()

    def visualization(self, entity_id, model):
        data = model.model_data(entity_id)
        X = data[["positive_events", "negative_events"]]
        proba = self.predictor.predict_proba(X)[:, 1]
        pred = proba.mean() if model.name == "team" else proba[0]

        fig, ax = plt.subplots(figsize=(8, 2))
        
        bar_color = '#FFC107' if pred < 0.5 else '#F44336'
        
        ax.barh(["Recruitment Risk"], [pred], color=bar_color, height=0.6)
        ax.set_xlim(0, 1)
        ax.set_title("Employee Retention Risk Assessment")
        ax.set_xlabel("Probability (0 = Safe, 1 = High Risk)")
        
        ax.text(pred + 0.02, 0, f"{pred:.1%}", va='center', fontsize=12, fontweight='bold')
        
        self.set_axis_styling(ax, bordercolor="#ddd", fontcolor="#555")
        ax.grid(True, linestyle='--', alpha=0.7, axis='x')
        
        fig.tight_layout()
        return fig

# Visualizations
class Visualizations(CombinedComponent):
    children = [LineChart(), BarChart()]
    outer_div_type = Div()

# Notes table
class NotesTable(DataTable):
    def component_data(self, entity_id, model):
        notes = model.notes(entity_id)
        if notes.empty:
            return pd.DataFrame({"Message": ["No notes available for this employee/team"]})
        return notes

# Filters
class DashboardFilters(FormGroup):
    id = "top-filters"
    action = "/update_data"
    method = "POST"
    children = [
        Radio(
            values=["Employee", "Team"],
            name='profile_type',
            hx_get='/update_dropdown',
            hx_target='#selector'
        ),
        ReportDropdown(
            id="selector",
            name="user-selection"
        )
    ]

# Full report
class Report(CombinedComponent):
    children = [Header(), DashboardFilters(), Visualizations(), NotesTable()]

report = Report()

# Routes
@app.get('/')
def homepage():
    return report('1', Employee(db_file))

@app.get('/employee/{id}')
def employee_page(id: str):
    return report(id, Employee(db_file))

@app.get('/team/{id}')
def team_page(id: str):
    return report(id, Team(db_file))

@app.get('/update_dropdown')
def update_dropdown(r):
    profile = r.query_params.get('profile_type', 'Employee')
    model = Team(db_file) if profile == 'Team' else Employee(db_file)
    return DashboardFilters.children[1].build_component(None, model)

@app.post('/update_data')
async def update_data(r):
    data = await r.form()
    profile = data.get('profile_type')
    selected = data.get('user-selection')
    path = '/team/' if profile == 'Team' else '/employee/'
    return RedirectResponse(f"{path}{selected}", status_code=303)

# Start the app
if __name__ == '__main__':
    serve()
