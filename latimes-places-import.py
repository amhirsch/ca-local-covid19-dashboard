import pandas as pd

DATE = 'date'
COUNTY = 'county'
NAME = 'name'
ID = 'id'
POPULATION = 'population'

CONFIRMED_CASES = 'confirmed_cases'
NEW_CASES = 'new_cases'
NEW_CASES_7DAY, NEW_CASES_14DAY = [f'new_cases_{x}day' for x in (7, 14)]
CASE_RATE_7DAY, CASE_RATE_14DAY = [f'case_rate_{x}day' for x in (7, 14)]

df = pd.read_csv('latimes-place-totals.csv',
                 parse_dates=[DATE],
                 infer_datetime_format=True)

STR_COL = ['id', 'name', 'county', 'note']
df[STR_COL] = df[STR_COL].convert_dtypes()

df.sort_values([DATE, COUNTY, NAME, ID], inplace=True)
df.reset_index(drop=True, inplace=True)

for id_ in df[ID].unique():
    id_mask = df[ID] == id_
    df.loc[id_mask, NEW_CASES] = df.loc[id_mask, CONFIRMED_CASES].diff()
    df.loc[id_mask, NEW_CASES_7DAY] = df.loc[id_mask,
                                             NEW_CASES].rolling(7).sum()
    df.loc[id_mask,
           NEW_CASES_14DAY] = df.loc[id_mask, NEW_CASES].rolling(14).sum() / 2
    df.loc[id_mask, CASE_RATE_7DAY] = (
        (df.loc[id_mask, NEW_CASES_7DAY] / df.loc[id_mask, POPULATION]) *
        100_000).round(1)
    df.loc[id_mask, CASE_RATE_14DAY] = (
        (df.loc[id_mask, NEW_CASES_14DAY] / df.loc[id_mask, POPULATION]) *
        100_000).round(1)

df.to_pickle('latimes-places-ts.pickle')