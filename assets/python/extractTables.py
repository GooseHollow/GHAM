import sys
import pandas as pd
import re
import numpy as np
from datetime import date
from datetime import date, timedelta
import calendar
# Get today's date
today = date.today()
# Calculate the last day of the previous month
last_day_of_prev_month = today.replace(day=1) - timedelta(days=1)
# Print the last month-end date
# Path to Excel Filepd.read
file_path = "finreturns.xls"
#

def generateTables(file_path):
    df = pd.read_excel(file_path, skiprows = 11, nrows=33, usecols= 'C:X')
    df = df.drop(columns=['Unnamed: 3', 'Unnamed: 4', 'Unnamed: 5', 'Unnamed: 6', 'Unnamed: 7',"Unnamed: 11", "Unnamed: 16", "Unnamed: 20"]) #drops nan numbers

    # print(df)

    relevant = ['Goose Hollow Tactical Allocation ETF',	    							
    'Goose Hollow Multi-Strategy Income ETF', 'Goose Hollow Tactical Allocation ETF - Market', 'Goose Hollow Multi-Strategy Income ETF - Market']
    relevantRowIndexes = []
    for etf in relevant:
        relevantRowIndex =  df.index[(df["Unnamed: 2"] == etf)].to_list()
        # print((relevantRowIndex))
        relevantRowIndexes.append(relevantRowIndex[0])
        
        # newDf = newDf.loc(relevantRow
    # print(relevantRowIndexes)
    new_df = pd.DataFrame(df, index = relevantRowIndexes)
    new_df.rename( #renames the columns accordingly
        columns={"Unnamed: 2": "ETF", "Unnamed: 8" : "Load",
                "Unnamed: 9": "Performance Inception Date", 
                "Unnamed: 10": "Month End NAV", "Unnamed: 12" : "1 Mo.", "Unnamed: 13" : "3 Mo.", "Unnamed: 14" : "6 Mo.", 
                "Unnamed: 15": "Year To Date", "Unnamed: 17" : "Since Incept.", 
                "Unnamed: 18": "1 Year", "Unnamed: 19" : "2 Years", "Unnamed: 21" : "3 Years", "Unnamed: 22" : "4 Years", "Unnamed: 23" : "5 Years", "Unnamed: 24" : "10 Years"},
        inplace=True,
    ) #renames columns with more relevant names


    new_df = new_df.fillna(0)
    print(new_df)

    def formatter(x): #changes the () to a negative sign 
        translate_table = dict({ord(i): None for i in '(),'})
        if ("(" in str(x)): #neg number (excel formatting)
            return -float(x.translate(translate_table))
        else: 
            return x #if not a neg, return the original val

    for col in new_df.columns[1:]: #run the above formatting function for each column
        new_df[col] = new_df[col].apply(formatter)

    # print(new_df)

    content = new_df.to_csv('allData.txt', sep='\t', index=False) 

    # GENERATING FILE
   
    

    #now that there's a text file for all the data, read and separate the data into two types (nav and market)
    def generateTableCode(nav_numerical_data, market_numerical_data):

        #print("{}/{}/{}".format(last_day_of_prev_month.month, last_day_of_prev_month.day, last_day_of_prev_month.year))
        html_table = f'''<table style="width: 100%; text-align: left;">
        <thead>
            <tr>
                <th>As of: {last_day_of_prev_month.month}/{last_day_of_prev_month.day}/{last_day_of_prev_month.year}</th>
                <th>1 Month</th>
                <th>3 Month</th>
                <th>YTD</th>
                <th>Since Inception</th>
                <th>1 Year</th>
                <th>2 Year</th>
           </tr>
        </thead>
        <tr>
            <td>Fund NAV</td>
            <td>{nav_numerical_data[2]}%</td>
            <td>{nav_numerical_data[3]}%</td>
            <td>{nav_numerical_data[5]}%</td>
            <td>{nav_numerical_data[6]}%</td>
            <td>{nav_numerical_data[7]}%</td>
            <td>{nav_numerical_data[8]}%</td>
        </tr>
        <tr>
            <td>Market Price</td>
            <td>{market_numerical_data[2]}%</td>
            <td>{market_numerical_data[3]}%</td>
            <td>{market_numerical_data[5]}%</td>
            <td>{market_numerical_data[6]}%</td>
            <td>{market_numerical_data[7]}%</td>
            <td>{market_numerical_data[8]}%</td>
        </tr>
        </table>'''
        #return (f'<table style=\"width: 100%; text-align: left;\">\n        <thead>\n            <tr>\n                <th>As of:\n                    {date.today().month}/{date.today().day}/{date.today().year}</th>\n                <th>1 Month</th>\n                <th>3 Month</th>\n                <th>YTD</th>\n                <th>Since Inception</th>\n                <th>1 Year</th>\n                <th>2 Year</th>\n           </tr>\n        </thead>\n        <tr>\n            <td>Fund NAV</td>\n            <td> {nav_numerical_data[2]}% </td>\n            <td> {nav_numerical_data[3]}% </td>\n            <td> {nav_numerical_data[5]} </td>\n            <td> {nav_numerical_data[6]}% </td>\n            <td> {nav_numerical_data[7]}% </td>\n            <td> {nav_numerical_data[8]}% </td>\n        </tr>\n        <tr>\n            <td>Market Price</td>\n            <td> {market_numerical_data[2]}% </td>\n            <td>  {market_numerical_data[3]}% </td>\n            <td> {market_numerical_data[5]}% </td>\n            <td>  {market_numerical_data[6]}% </td>\n            <td>  {market_numerical_data[7]}% </td>\n            <td> {market_numerical_data[8]}% </td>\n        </tr>\n    </table>')
        return(html_table)

    if __name__ == '__main__':
        etfs = ['Goose Hollow Tactical Allocation ETF',	 'Goose Hollow Multi-Strategy Income ETF',
                 'Goose Hollow Tactical Allocation ETF - Market', 'Goose Hollow Multi-Strategy Income ETF - Market']

        etf_keywords = ["Tactical Allocation", "Multi-Strategy"]

        f = open("allData.txt", "r")

        for keyword in etf_keywords:
            f.seek(0) #resets the file pointer back at the top
            keyword_file_name = "_" +keyword+".txt"
            keyword_file = open(keyword_file_name, 'w')
            keyword_file.write("Goose Hollow " + keyword + '\n')

            for line in f:
                line = line.strip('\n') # this is the line we add to strip the newline character
                # print(line)
                if (keyword in line): 
                    # print(line)
                    numerical_data = re.findall("(?<=[AZaz])?(?!\d*=)[0-9.+-]+",line)
                    # print(numerical_data)
                    
                    #rounds the decimal points of the values
                    new_numerical_data = []
                    for num in numerical_data: 
                        try: 
                            num = round(float(num),2)
                            new_numerical_data.append(num)
                        except:
                            new_numerical_data.append(num)
                            # print("Exception occured at ", num)

                    # print("numerical: ", numerical_data)
                    # print("new numerical: ", new_numerical_data)


                    if ("Multi-Strategy" in line): #remove the " - Market" and Multi-Strat
                        new_numerical_data.pop(0)
                        
                    if ("Market" in line): #remove the " - Market"
                        new_numerical_data.pop(0)
                        market_numerical_data = new_numerical_data
                    else:
                        nav_numerical_data = new_numerical_data
            

            # print("nav data", nav_numerical_data)
            # print("market data", market_numerical_data)
            # print("\n")

            generatedTags = generateTableCode(nav_numerical_data, market_numerical_data)
            keyword_file.write(generatedTags)
            keyword_file.truncate()

            keyword_file.close() #close the keyword file
            with open(keyword_file_name, 'r') as keyword_file_read:
                        file_contents = keyword_file_read.read()
                        print(file_contents)
                


if __name__ == '__main__':
    try:
        filename = sys.argv[1]
        generateTables(filename)
    except:
        file_path = "finreturns.xls"
        generateTables(file_path)
    
