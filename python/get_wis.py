#%%
import pandas as pd
import re
#%%

int_df = pd.read_csv('../census/ACSST5Y2018.S2801_data_with_overlays_2020-08-30T010210.csv')

int_df = int_df.iloc[1:]
# %%

int_df['zcta'] = int_df.NAME.apply(lambda x: re.search('[0-9]{2,}',x).group())

# %%
