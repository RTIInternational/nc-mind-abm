import camelot
import numpy as np
import pandas as pd
import pdfquery
from data.sheps_data.src.helpers import ptchar_var_map
from pathlib import Path
from tqdm import trange

main_dir = Path("data/sheps_data/2018/")
file = main_dir.joinpath("ptchar_all_and_by_hosp_2018_and.pdf")
year = "2018"
n_year = "n_" + year

rows_to_drop = [
    # page type 1
    "Patient Distance to Hosp",
    "Age Group",
    "Race",
    "Ethnicity",
    "Point of Origin",
    "ED Revenue Code Present",
    "Payer",
    "Patient Disposition",
    "All",
    "Patient Residence State",
    # page type 2
    "Clinic or physician's",
    "Transfer from a hospital",
    "or other health care",
    "Transfer from a SNF,",
    "Information not",
    "ED Revenue Code",
    "Present",
    "Payer"
    # page type 3
    "Patient Disposition",
    "Home, self, or outpatient",
    "Discharged, transferred",
    "to facility that provides",
    "nursing, custodial, or",
    "to long term acute care",
    "Left against medical",
]

pdf_cols = [
    "variable",
    "n_2018",
    "p_2018",
    "n_2017",
    "p_2017",
    "n_2016",
    "p_2016",
    "n_2015",
    "p_2015",
    "n_2014",
    "p_2014",
]


if __name__ == "__main__":
    # Set up inputs
    page_range = range(1, 354)
    page_list = list(page_range)
    # query pdf for hospital titles
    pdf = pdfquery.PDFQuery(file)

    master_df = pd.DataFrame()

    # for each table (assuming 1 per page) determine the hospital and extract necessary data
    for i in trange(len(page_list)):

        # read pdf for tables
        table = camelot.read_pdf(str(file), flavor="stream", pages=str(page_list[i]))

        # extract the hospital name for that page
        pdf.load(page_list[i] - 1)
        label = pdf.pq('LTTextLineHorizontal:contains("Short Term Acute Care Hospital Discharge Data")')
        left_corner = float(label.attr("x0"))
        bottom_corner = float(label.attr("y0"))
        hospital = pdf.pq(
            'LTTextLineHorizontal:in_bbox("%s, %s, %s, %s")'
            % (left_corner, bottom_corner - 30, left_corner + 500, bottom_corner)
        ).text()

        hospital_string = hospital.replace(" ", "_").lower()

        # extract the dataframe for that page
        df = table[0].df
        df.rename(columns={df.columns[0]: "variable"}, inplace=True)

        # this pdf has 3 types of tables determine the type of page by locating appropriate headers
        if df["variable"].str.contains("Patient Distance to Hosp").any():
            page_type = 1
            keep = [i not in ["Patient Characteristics", "", "Patient Residence State", "Unknown"] for i in df.variable]
        elif df["variable"].str.contains("Payer").any():
            page_type = 2
            keep = [i not in ["", "Point of Origin", "Patient Characteristics", "Unknown"] for i in df.variable]
        elif df["variable"].str.contains("Home, self, or outpatient").any():
            page_type = 3
            keep = [i not in ["", "Patient Characteristics", "All", "Patient Disposition"] for i in df.variable]
        else:
            raise print("Unknown page type")

        df = df[keep]
        df = df[~df["variable"].isin(rows_to_drop)]

        # replace blank spaces with nans
        df = df.replace("", np.nan)
        # replace new line symbols with spaces
        df.replace({"\n": " "}, regex=True, inplace=True)

        # rows with na indicate that the columns did not separate correctly when the table was read in from the pdf
        # identify these rows to separate the strings
        if len(list(df)) == 11:
            rows_with_null = df[pd.isnull(df).any(axis=1)].set_index("variable")
            df.columns = pdf_cols
        # sometimes the pdf does not correctly read in the columns if the number of columns is not expected (ie not 11)
        # all rows must be split into 11 columns
        else:
            rows_with_null = df.set_index("variable")
            df = pd.DataFrame(columns=pdf_cols)

        # used later to drop rows
        rows_to_split = rows_with_null.index.values.tolist()

        df_temp = pd.DataFrame()

        # separate strings into columns this dataframe contains many nas and the size is not predictable
        for col in rows_with_null.columns:
            if not rows_with_null[col].isnull().all():
                new_df = rows_with_null[col].str.split(" ", expand=True)
                df_temp = pd.concat([df_temp, new_df], axis=1, sort=False)

        df_append = pd.DataFrame()

        # remove nas from temporary dataframe this should consistently create a dataframe with 11 columns
        for idx, row in df_temp.iterrows():
            new_row = row.dropna().reset_index(drop=True)
            new_row.columns = pdf_cols
            df_append = df_append.append(new_row, sort=False)

        df_append = df_append.reset_index()
        df_append.rename(columns={df_append.columns[0]: "variable"}, inplace=True)

        # if there are rows to append, add them to the dataframe
        if len(df_append) > 0 and df_append.shape[1] == 11:
            df = df[~df["variable"].isin(rows_to_split)]
            df_append.columns = pdf_cols
            df = df.append(df_append, sort=False)
        # if there are not 11 columns, hospital has not been operating continuously - manually review and add hospital
        elif len(df_append) > 0 and df_append.shape[1] != 11:
            print(f"Must manually evaluate {hospital} on page {str(page_list[i])}.")

            textfile = main_dir.joinpath("manual_evaluation_ptchar.txt")
            with open(textfile, "a") as myfile:
                myfile.write(f"\n must manually evaluate ptchar {hospital} on page {str(page_list[i])}")
            pass

        df = df.reset_index(drop=True)

        var_map = ptchar_var_map

        if page_type == 1:
            var_map.update(
                {
                    "Other": "Patient Residence State Other",
                    "Missing": "Patient Dist to Hospital Missing",
                    "Unavailable": "Race Unavailable",
                    "Unknown": "Ethnicity Unknown",
                }
            )
        if page_type == 2:
            var_map.update({"Other": "Payer Other", "Unknown": "Payer Unknown"})

        df.variable = df.variable.map(var_map).fillna(df["variable"])
        df.columns = pdf_cols
        df["hospital"] = hospital
        mini_df = df[["variable", n_year, "hospital"]]
        master_df = pd.concat([master_df, mini_df], axis=0, sort=False)

    final = master_df.pivot_table(index="variable", columns="hospital", values=n_year, aggfunc=lambda x: " ".join(x))
    final = final.replace("", np.nan)

    final.to_csv(main_dir.joinpath(f"{year}_master_ptchar_initial.csv"))
