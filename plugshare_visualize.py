import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

import pandas as pd
import numpy as np

plt.style.use('seaborn-v0_8-notebook')

sheet_names = ['OVERALL RT', 'EXCL TESLA AND EA']
ts_data = pd.read_excel('/Users/salataresearchassistant/Desktop/Seamless EV Charging/EV_Charging/timeseries_visuals/raw_timeseries_data.xlsx', sheet_name=sheet_names)

overall_RT = ts_data['OVERALL RT']
overall_RT = overall_RT.fillna(method='ffill')


def plot_overall_RT():    
    
    plt.plot(overall_RT['Date'], overall_RT.drop(['Date', 'Total'], axis=1), marker='o', linestyle='dashed', linewidth=1)
    plt.plot(overall_RT['Date'], overall_RT['Total'], marker='D', linestyle='solid', linewidth=3, color='red')

    plt.xlabel('Date')
    plt.ylabel('Share of Charging Stations (%)')
    plt.ylim(0, 1)
    plt.title('Share of Stations Along Major Highways with Real-Time Data Available (>=1 plug)')
    plt.legend(overall_RT.drop('Date', axis=1).columns, loc='center left', bbox_to_anchor=(1, 0.5))
    
    plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{100*y:.0f}%'))

    plt.grid(True)
    plt.show()

plot_overall_RT()

excl_T_EA = ts_data['EXCL TESLA AND EA']
excl_T_EA = excl_T_EA.fillna(method='ffill')

def plot_excl_T_EA():    
    
    plt.plot(excl_T_EA['Date'], excl_T_EA.drop(['Date', 'Total'], axis=1), marker='o', linestyle='dashed', linewidth=1)
    plt.plot(excl_T_EA['Date'], excl_T_EA['Total'], marker='D', linestyle='solid', color='red', linewidth=3)

    plt.xlabel('Date')
    plt.ylabel('Share of Charging Stations (%)')
    plt.ylim(0, 1)
    plt.title('Share of Stations Along Major Highways with Real-Time Data Available (>=1 plug), Excluding Tesla and EA')
    plt.legend(excl_T_EA.drop('Date', axis=1).columns, loc='center left', bbox_to_anchor=(1, 0.5))
    
    plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{100*y:.0f}%'))

    plt.grid(True)
    plt.show()

plot_excl_T_EA()