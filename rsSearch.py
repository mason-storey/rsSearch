# Defining imports here
import requests, time, random, os, sys, traceback
from bs4 import BeautifulSoup
from datetime import datetime

# Defining methods
def trimOutputString(string,length):
    if len(string) > length:
        return (string[:length-5] + "...").ljust(length)
    return string.ljust(length)

# Defining variables here
partNumbers = []
stockNos = []
mfrPartNos = []
brands = []
failed = []
prices = []
quantities = []

# Getting file location
file_path = os.path.dirname(sys.argv[0])
file_path_name = file_path + "/" + "rsinput.csv"

# Creating file names
timeStamp = datetime.today().strftime('%Y %m %d %H.%M.%S')
output_file_name = timeStamp + " output.csv"
failed_file_name = timeStamp + " failed.csv"
remaining_file_name = timeStamp + " remaining.csv"

# Reading input file and parsing RS numbers
with open(file_path_name,"r") as rsInput:
    for line in rsInput:
        line = line.strip(",")
        line = line.strip("RS")
        line = line.replace("-","")
        line = line.strip("\n")
        partNumbers.append(line)

# Creating output file
with open(output_file_name,"w") as file:
    file.write("Stock No,Mfr Part No,Brand,Price,Quantity\n")
    
# Iterating through part numbers and searching for number on RS website
try:
    while len(partNumbers) > 0:
        part = partNumbers.pop(0)

        # Searching for part number and parsing result page
        try:
            r = requests.get("https://uk.rs-online.com/web/c/?searchTerm="+part)
            page = BeautifulSoup(r.text, "html.parser")
        except:
            failed.append(
                {
                    "partNo":part,
                    "reason":"failed to load seach page"
                }
            )
            print("Failed to load search page -", part)
            continue

        # Fix here
        link = page.select('a[data-qa="product-tile-container"]')
        if len(link) == 0:
            failed.append(
                {
                    "partNo":part,
                    "reason":"failed to find in search"
                }
            )
            print("failed to find in search - ", part)
            continue
        
        try:
            link = "https://uk.rs-online.com" + link[0]['href']
        except:
            failed.append(
                {
                    "partNo":part,
                    "reason":"failed to find link of search item - error html created"
                }
            )
            print("failed to find link of search item")
            with open(part+"_failed.html","w") as out:
                out.write(r.text)
            continue
        
        # Loading item page to gather information
        r = requests.get(link)
        page = BeautifulSoup(r.text, "html.parser")
        # Fix complete


        try:
            price = page.select('table[data-testid="price-breaks"]')[0].findAll('tr')[1].text
            price = price[price.index("£"):]
            quantity = page.select('p[data-testid="price-heading"]')
            description = page.select('div[data-testid="long-description"]')[0].text
        except:
            failed.append(
                {
                    "partNo":part,
                    "reason":"failed to find item info in page"
                }
            )
            print("failed to find item info in page -", part)
            continue


        
        details = page.select('dl[data-testid="key-details-desktop"]')
        if len(details) == 0:
            failed.append(
                {
                    "partNo":part,
                    "reason":"failed to find details in page"
                }
            )
            print("failed to find details in page - ", part, link)
            continue

        dd = details[0].select("dd")

        if len(dd) == 3:
            stockNumber = dd[0].text
            mfrPartNumber = dd[1].text
            brand = dd[2].text
        else:
            stockNumber = dd[0].text
            mfrPartNumber = dd[0].text
            brand = dd[1].text

        quant = 1

        print(trimOutputString(stockNumber,10), trimOutputString(mfrPartNumber,15), trimOutputString(brand,15), trimOutputString(price,15), trimOutputString(description,40))

        # Outputting results of the search to CSV file
        with open(output_file_name,"a") as file:
            tempStr = "{},{},{},{},{}\n".format(
                "\""+stockNumber+"\"",
                "\""+mfrPartNumber+"\"",
                "\""+brand+"\"",
                "\""+price+"\"",
                "\""+str(quant)+"\"")
            file.write(tempStr)

except Exception as e:
    print("fatal error")
    print("recovered - see remaining.csv for unsearched numbers")
    print("error log produced to error.log - send this file to mason")

    # Creating remaining error CSV files
    with open(remaining_file_name,"w") as remaining:
        remaining.write("Remaining after fatal error\n")
        partNumbers.insert(0,part)
        for partNum in partNumbers:
            remaining.write(partNum+"\n")

    # Creating error log file
    with open("error.log","w") as error:
        traceback.print_exc(file=error)
        error.write("="*50)
        error.write("\nFailed on part number {}".format(part))

# Printing failed search numbers
with open(failed_file_name,"w") as failCsv:
        failCsv.write("Part Number, Reason\n")
        for failure in failed:
            failCsv.write(failure.get("partNo") + "," + failure.get("reason") + "\n")


