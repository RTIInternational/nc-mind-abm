## Data

This project requires several input data files. These files are collected form different places and often require preprocessing. The following will walk a new user through the process of obtaining and preparing these files.


**1. County Populations**

The 2020 North Carolina population estimates were pulled from the US Census website. [Link](https://www.census.gov/programs-surveys/popest/technical-documentation/research/evaluation-estimates/2020-evaluation-estimates/2010s-counties-total.html)

**2. Nursing Home List**

The list of nursing home facilities starts by downloading CMS data. We then check to see if any new NHs have been added, or if any old NHs have been removed. This is done by comparing the CMS data to the `nursing_homes_base` file, which is a snapshot of the NC nursing home data at the start of this project. The base file incldues geocodes generated during a past project and other variables from the CMS data. 

New NHs are also geocoded. It is possible that a new nursing will not automatically be geocoded (due to an unrecognized address). You will need to manually fix this if a warning message is printed.

The final nursing home list, generated by running the script below, includes any updates made during the above process and some basic preprocessing to prepare the file for use.

```
python src/create_nursing_home_file.py 
```

**3. Hospital List**

Creating a list of accurate hospitals in NC is tricky. [NCDHSR reports](https://info.ncdhhs.gov/dhsr/reports.htm) have a list of all active hospitals. However, this list does not contain ICU bed counts, or information about admissions/discharges. Data from the [SHEPs center](https://www.shepscenter.unc.edu/data/nc-hospital-discharge-data/descriptive-statistics/) is often 1-2 years outdated, but provides details on admissions and discharges for each hospitals.

Hospitals change, open, close, and are often combined into one. Therefore - we use the NCDHSR list of hospitals, but require the hospital to have data in the 2018 SHEPs PDFs. 

3.1 Collect SHEPs Data - Follow [this](sheps_data/README.md)


3.2 Check for updated NCDHSR facilities

```
python src/check_ncdhsr_facilities.py
```

Make updates as promoted and save the files.

**4. Distance Files**

Next we need to calculate the distance from each county to each facility.

```
python src/calculate_distances.py
```

**5. County-to-county distances**

The `county_distances` file contains distances between each NC county and other NC counties within 500 miles. It is based on the National Bureau of Economic Research's [County Distance Database](https://www.nber.org/research/data/county-distance-database). The `county_distances_base` file was downloaded from the above link (2010, 500 miles, csv format). The base file was filtered and processed using `src/create_county_distances.py`.

The base file is not included in this repo since it is large. If you want to recalculate distances (unlikely but possible, perhaps if NBER releases a new file using 2020 census data), download a new base file from the link above. Save it in `data/geography`. Update the file path in `config/filepaths.yaml` if necessary. Then run `python src/create_county_distances.py`.