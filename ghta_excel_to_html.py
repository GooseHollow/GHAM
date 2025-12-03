import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import re

df = pd.read_excel("assets/excel/finreturns.xls", dtype = "str")
df_cols = ['Unnamed: 12', 'Unnamed: 13', 'Unnamed: 15', 'Unnamed: 17', 'Unnamed: 18', 'Unnamed: 19']
df_rows = df[df["Unnamed: 2"].isin(["Goose Hollow Tactical Allocation ETF", "Goose Hollow Tactical Allocation ETF - Market"])]

word_date = df.iloc[1]
date_text = re.split(r'[, ]+',  (" ".join(word_date.dropna().astype(str))).strip())
months = {"January": 1, "February":2, "March":3, "April":4, "May":5, "June":6, "July":7, "August":8, "September": 9, "October": 10, "November":11, "December": 12}

month = 0
day = 0
year = 0

for i in range(len(date_text)):
    portion = date_text[i]
    if portion in months.keys():
        month = months[portion]
        day = date_text[i+1]
        year = date_text[i+2]

date = f"{month}/{day}/{year}"

with open('index.html', "r", encoding = "utf-8") as file:
    soup = BeautifulSoup(file, 'lxml')

def change_performance(is_monthly, date):
    if is_monthly:
        tables = soup.find_all('table', {'class': "monthly-performance"})
        date_span = soup.find_all('span', {'class': "month"})
    else:
        tables = soup.find_all('table', {'class': "quarterly-performance"})
        date_span = soup.find_all('span', {'class': "quarter"})
    for span in date_span:
        span.string = date
    for table in tables:
        html_rows = table.find_all("tr")[1:]
        for i, (_, excel_row) in enumerate(df_rows.iterrows()):
            if i < len(html_rows):
                html_cells = html_rows[i].find_all("td")
                excel_values = excel_row[df_cols].values

                for j, value in enumerate(excel_values):
                    col_i = j + 1
                    value = str(value)
                    if col_i < len(html_cells):
                        if (value[0] == "(" and value[-1]== ")"):
                            value = "-" + value[1:-1]
                        html_cells[col_i].string = f"{float(value):.2f}%"
                    if value == "nan":
                        html_cells[col_i].string = "0.0%"


# Monthly Performance
change_performance(True, date)

# Quarterly:
if month % 3 != 0:
    print("No changes to quarterly data")
else:
    change_performance(False, date)


with open("index.html", "w", encoding = "utf-8") as file:
    file.write(str(soup))

print("Complete")