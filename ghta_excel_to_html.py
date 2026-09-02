import glob
import os
import re
import sys
from datetime import date

import pandas as pd
from bs4 import BeautifulSoup

EXCEL_DIR = "assets/excel"
HTML_FILE = "index.html"

MONTHS = {"January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
          "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12}

PERIOD_RE = re.compile(
    r"Period\s+Ending\s+(" + "|".join(MONTHS) + r")\s+(\d{1,2}),?\s+(\d{4})", re.IGNORECASE)


def extract_period_end(text):
    """Return the 'Period Ending <Month> <D>, <YYYY>' date in text, or None."""
    match = PERIOD_RE.search(text or "")
    if not match:
        return None
    month_name, day, year = match.groups()
    return date(int(year), MONTHS[month_name.capitalize()], int(day))


def period_end_of_file(path):
    """Read the header rows of an Excel workbook and return its period-ending date."""
    header = pd.read_excel(path, dtype="str", nrows=5, header=None)
    for _, row in header.iterrows():
        found = extract_period_end(" ".join(row.dropna().astype(str)))
        if found:
            return found
    return None


def find_latest_excel(directory=EXCEL_DIR):
    """Return the most recently added workbook in `directory`.

    Ranked by file modification time, not by name -- filenames are unreliable
    here (finreturns_july2026.xls holds July 31 data while finreturns.xls holds
    August 31 data). Note a fresh clone resets mtimes, so run this against a
    working copy where the files were actually dropped in.
    """
    candidates = sorted(glob.glob(os.path.join(directory, "*.xls")) +
                        glob.glob(os.path.join(directory, "*.xlsx")))
    if not candidates:
        raise FileNotFoundError(f"No Excel files found in {directory}")
    return max(candidates, key=os.path.getmtime)


def main(excel_path=None, html_path=HTML_FILE):
    if excel_path is None:
        excel_path = find_latest_excel()
    print(f"Using Excel file: {excel_path}")

    df = pd.read_excel(excel_path, dtype="str")
    df_cols = ['Unnamed: 12', 'Unnamed: 13', 'Unnamed: 15', 'Unnamed: 17', 'Unnamed: 18', 'Unnamed: 19']
    df_rows = df[df["Unnamed: 2"].isin(["Goose Hollow Tactical Allocation ETF",
                                        "Goose Hollow Tactical Allocation ETF - Market"])]

    period_end = period_end_of_file(excel_path)
    if period_end is None:
        raise ValueError(f"No 'Period Ending' date found in {excel_path}")
    month = period_end.month
    date_str = f"{period_end.month}/{period_end.day}/{period_end.year}"
    print(f"Period ending: {date_str}")

    with open(html_path, "r", encoding="utf-8") as file:
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
                            if (value[0] == "(" and value[-1] == ")"):
                                value = "-" + value[1:-1]
                            html_cells[col_i].string = f"{float(value):.2f}%"
                        if value == "nan":
                            html_cells[col_i].string = "0.0%"

    # Monthly Performance
    change_performance(True, date_str)

    # Quarterly:
    if month % 3 != 0:
        print("No changes to quarterly data")
    else:
        change_performance(False, date_str)

    with open(html_path, "w", encoding="utf-8") as file:
        file.write(str(soup))

    print("Complete")


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else None)
