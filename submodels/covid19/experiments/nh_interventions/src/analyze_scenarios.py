from pathlib import Path
import pandas as pd
from submodels.covid19.model.state import COVIDState, VaccinationStatus
import numpy as np
from src.misc_functions import get_multiplier
from submodels.covid19.model.parameters import CovidParameters
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly as plotly

experiment_dir = Path("submodels/covid19/experiments/nh_interventions")


if __name__ == "__main__":
    """
    Analyses preformed:
    1. Number of nursing home visits by Time, Visitor Order, and Covid State
    2. Number of healthcare worker days worked by Time, COVID State, Vacc Status
    """

    for scenario_dir in experiment_dir.glob("scenario*"):
        params = CovidParameters()
        params.update_from_file(scenario_dir.joinpath("parameters.yml"))
        multiplier = get_multiplier(params)

        nh_visits_dfs = []
        hcw_attendance_dfs = []

        for run in scenario_dir.glob("run_*"):

            # NH: Time, Visitor Order, Covid
            nh_visits = pd.read_csv(run.joinpath("model_output/nh_visits.csv"))
            nhdf = pd.DataFrame(nh_visits.groupby(["Time", "Visitor_Order", "COVID_State"]).size())
            nhdf[0] = np.round(nhdf[0]).astype(int)
            nhdf.columns = [f"Count_{run.name}"]
            nh_visits_dfs.append(nhdf)

            # HCW: Time, COVID, Vacc Status
            hcw_attendance = pd.read_csv(run.joinpath("model_output/hcw_attendance.csv"))
            hcw_df = pd.DataFrame(hcw_attendance.groupby(["Time", "COVID_State", "Vacc_Status"]).size())
            hcw_df[0] = np.round(hcw_df[0]).astype(int)
            hcw_df.columns = [f"Count_{run.name}"]
            hcw_attendance_dfs.append(hcw_df)

        output_dir = experiment_dir.joinpath("analysis")
        output_dir.mkdir(exist_ok=True)

        # ----- Nh Visits by Category
        nhdf = pd.concat(nh_visits_dfs, axis=1).reset_index()
        nhdf["COVID_State"] = [COVIDState(i).name.title() for i in nhdf["COVID_State"]]
        nhdf.insert(3, "Average", nhdf[[i for i in nhdf.columns if "Count_" in i]].mean(axis=1))
        nhdf.insert(4, "Std", nhdf[[i for i in nhdf.columns if "Count_" in i]].std(axis=1))
        nhdf.insert(5, "Max", nhdf[[i for i in nhdf.columns if "Count_" in i]].max(axis=1))
        nhdf.insert(6, "Min", nhdf[[i for i in nhdf.columns if "Count_" in i]].min(axis=1))
        nhdf.to_csv(output_dir.joinpath(f"{scenario_dir.name}-nh-visits.csv"))

        # ----- HCW
        hcw_df = pd.concat(hcw_attendance_dfs, axis=1).reset_index()
        hcw_df["COVID_State"] = [COVIDState(i).name.title() for i in hcw_df["COVID_State"]]
        hcw_df["Vacc_Status"] = [VaccinationStatus(i).name.title() for i in hcw_df["Vacc_Status"]]
        hcw_df.insert(3, "Average", hcw_df[[i for i in hcw_df.columns if "Count_" in i]].mean(axis=1))
        hcw_df.insert(4, "Std", hcw_df[[i for i in hcw_df.columns if "Count_" in i]].std(axis=1))
        hcw_df.insert(5, "Max", hcw_df[[i for i in hcw_df.columns if "Count_" in i]].max(axis=1))
        hcw_df.insert(6, "Min", hcw_df[[i for i in hcw_df.columns if "Count_" in i]].min(axis=1))
        hcw_df.to_csv(output_dir.joinpath(f"{scenario_dir.name}-hcw-attendance.csv"))
