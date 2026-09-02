import os
import sys
import logging
import argparse
from bs4 import BeautifulSoup
from datetime import datetime
from shutil import copy2

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def read_performance_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Parse the HTML-like content
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find the date
        date_cell = soup.select_one('thead th')
        if date_cell:
            date = date_cell.text.split(':')[-1].strip()
        else:
            raise ValueError("Date not found in the performance data file")
        
        # Parse the table data
        data = {}
        headers = [th.text.strip() for th in soup.select('thead th')[1:]]  # Skip the first header (date)
        rows = soup.select('tbody tr')
        for row in rows:
            cells = row.select('td')
            if cells:
                row_name = cells[0].text.strip()
                row_data = {headers[i]: cells[i+1].text.strip() for i in range(len(headers))}
                data[row_name] = row_data
        
        return date, data
    except Exception as e:
        logging.error(f"Error reading performance data: {e}")
        raise

def is_end_of_quarter(date):
    try:
        date_obj = datetime.strptime(date, "%m/%d/%Y")
        return date_obj.month in [3, 6, 9, 12]
    except ValueError:
        logging.error(f"Invalid date format: {date}")
        return False

def backup_file(file_path):
    backup_path = f"{file_path}.bak"
    try:
        copy2(file_path, backup_path)
        logging.info(f"Backup created: {backup_path}")
    except Exception as e:
        logging.error(f"Failed to create backup: {e}")
        raise

def update_table(table, performance_data):
    rows = table.find_all('tr')
    for row in rows[1:]:  # Skip header row
        cells = row.find_all('td')
        if cells:
            row_name = cells[0].text.strip()
            if row_name in performance_data:
                for i, (header, value) in enumerate(performance_data[row_name].items()):
                    if i + 1 < len(cells):
                        cells[i+1].string = value

def update_html_file(html_file_path, performance_file_path):
    try:
        # Backup the HTML file
        backup_file(html_file_path)

        # Read the HTML file with explicit encoding
        encodings = ['utf-8', 'latin-1', 'ascii', 'utf-16']
        content = None
        for encoding in encodings:
            try:
                with open(html_file_path, 'r', encoding=encoding) as file:
                    content = file.read()
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            raise ValueError(f"Unable to decode the HTML file with any of the attempted encodings: {encodings}")

        soup = BeautifulSoup(content, 'html.parser')

        # Read performance data
        date, performance_data = read_performance_data(performance_file_path)

        # Update the date
        # date_elements = soup.select('.fund_info_date')
        # for date_element in date_elements:
        #     date_element.string = date

        # Update monthly performance
        monthly_table = soup.select_one('#markTab .table-wrapper')
        if monthly_table:
            update_table(monthly_table, performance_data)
        else:
            logging.warning("Monthly performance table not found in HTML")

        # Check if it's end of quarter and update quarterly performance if needed
        if is_end_of_quarter(date):
            quarterly_table = soup.select_one('#performanceTab .table-wrapper')
            if quarterly_table:
                update_table(quarterly_table, performance_data)
            else:
                logging.warning("Quarterly performance table not found in HTML")

        # Write updated content back to the file
        with open(html_file_path, 'w', encoding='utf-8') as file:
            file.write(str(soup))

        logging.info("HTML file updated successfully")
    except Exception as e:
        logging.error(f"Error updating HTML file: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Update HTML file with performance data")
    parser.add_argument("html_file", help="Path to the HTML file")
    parser.add_argument("performance_file", help="Path to the performance data file")
    args = parser.parse_args()

    try:
        update_html_file(args.html_file, args.performance_file)
    except Exception as e:
        logging.error(f"Script execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()