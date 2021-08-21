import pandas as pd

EP_DATE = 'ep_date'
CSA = 'csa'
DPH_CASE_COLS = 'cases_{}day', 'case_{}day_rate', 'adj_case_{}day_rate'

df_dph_7day, df_dph_14day = [
    pd.read_csv(f'sources/LA_County_Covid19_CSA_{x}day_case_death_table.csv',
                parse_dates=[EP_DATE],
                infer_datetime_format=True) for x in (7, 14)
]

dph_last_day = df_dph_7day[EP_DATE].max() - pd.Timedelta(7, 'days')
df_dph_7day = df_dph_7day[(df_dph_7day[EP_DATE].notna()) &
                          (df_dph_7day[EP_DATE] <= dph_last_day)].copy()
df_dph_14day = df_dph_14day[(df_dph_14day[EP_DATE].notna()) &
                            (df_dph_14day[EP_DATE] <= dph_last_day)].copy()

for df in df_dph_7day, df_dph_14day:
    df.drop(columns=['Unnamed: 0'], inplace=True)
    df.rename(columns={'geo_merge': CSA}, inplace=True)
    df.sort_values([EP_DATE, CSA], inplace=True)
    df.reset_index(drop=True, inplace=True)
    df[CSA] = df[CSA].convert_dtypes()
    df['population'] = df['population'].astype('int')
    for stat in 'case', 'death':
        df[f'{stat}_rate_unstable'] = df[f'{stat}_rate_unstable'].apply(
            lambda x: x == '^')

for col in DPH_CASE_COLS:
    df_dph_7day[col.format(7)] = df_dph_7day[col.format(7)].astype('int')
    df_dph_14day[col.format(14)] = df_dph_14day[col.format(14)] / 2

if __name__ == '__main__':
    for df, duration in (df_dph_7day, 7), (df_dph_14day, 14):
        df.to_pickle(f'data/lacdph-{duration}day.pickle')
