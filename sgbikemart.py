from bs4 import BeautifulSoup
import requests
import lxml.html as lh
import pandas as pd
import csv
import os
from datetime import datetime
#https://sgbikemart.com.sg/listing/usedbike
#/listing/usedbike/kymco-kymco-downtown-350i/24429/
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'}

data = []


# df = pd.read_csv("sgbikemart.csv",index_col=0)
# now = datetime.now()
# formattedDate = now.strftime("%b-%d-%Y")
# listOfExistingModels=[]

# else:

#     listOfExistingModels = df["Model"]
#     updatedPriceList = df["Price"]
#     if 'Price ('+formattedDate+')' in df.columns:
#         print('column exists')
#     else:
#         print('fetching matching models')
months_in_year = ['','Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def get_index_positions(list_of_elems, element):
    ''' Returns the indexes of all occurrences of give element in
    the list- listOfElements '''
    index_pos_list = []
    index_pos = 0
    while True:
        try:
            # Search for item in list from indexPos to the end of list
            index_pos = list_of_elems.index(element, index_pos)
            # Add the index position in list
            index_pos_list.append(index_pos)
            index_pos += 1
        except ValueError as e:
            break
    return index_pos_list
    
def write_excel(filename,sheetname,dataframe):
    with pd.ExcelWriter(filename, engine='openpyxl', mode='a') as writer: 
        workBook = writer.book
        try:
            workBook.remove(workBook[sheetname])
        except:
            print("Worksheet does not exist")
        finally:
            dataframe.to_excel(writer, sheet_name=sheetname,index=False)
            writer.save()

now = datetime.now()
formattedDate = now.strftime("%d-%b-%Y")
if os.path.exists("sgbikemartFinal.xlsx"):
    df = pd.read_excel("sgbikemartFinal.xlsx")
    df['Price ('+formattedDate+')']=""

else:
    df = pd.DataFrame(columns=['Brand','Model','Price','Engine Capacity','Classification','Registration Date','COE Expiry Date','Mileage','No. of owners','Type of Vehicle','Listing Details','Price ('+formattedDate+')'])


# coeExpiryDate = df['COE Expiry Date'].values.tolist()
# df['COE Expiry Date'] = df['COE Expiry Date'].apply(lambda x: x.split("(")[0])



listOfExistingModels = df['Model'].values.tolist()
# df = pd.DataFrame(columns=['Brand','Model','Price','Engine Capacity','Classification','Registration Date','COE Expiry Date','Mileage','No. of owners','Type of Vehicle','Listing Details','Price ('+formattedDate+')'])


baseurl="https://sgbikemart.com.sg/"
html_text = requests.get('https://sgbikemart.com.sg/listing/usedbikes/listing/?page=').text


soup = BeautifulSoup(html_text,'html.parser')
currentPageButton = soup.select_one('li.page-item')
currentPageLink = currentPageButton.find('a').get('href')
currentPageLink = currentPageLink.replace("?page=","")
currentPageLink = currentPageLink.replace("&","")
lastPageButton = soup.select_one('li.page-item:last-child')
lastPageLink = lastPageButton.find('a').get('href')
lastPageLink = lastPageLink.replace("?page=","")
lastPageLink = lastPageLink.replace("&","")




for x in range(int(currentPageLink),int(lastPageLink)):
    link = requests.get('https://sgbikemart.com.sg/listing/usedbikes/listing/?page='+str(x)).text
    soup = BeautifulSoup(link,'html.parser')
    motorcyclesList = soup.find_all('div',class_='row g-0')
    motorcycleLinks=[]
    for motorcycle in motorcyclesList:
        motorcycleName= motorcycle.find('h3',class_='mb-0').text
        link = motorcycle.find('a').get('href')
        motorcycleLinks.append(baseurl+link)

    for link in motorcycleLinks:


        page = requests.get(link).text
        motorcycleDetails = BeautifulSoup(page,'html.parser')
        tables = motorcycleDetails.find('table')
        rowName=tables.find_all('td',class_="name")
        rowValue=tables.find_all('td',class_="value")
        listingDetails = motorcycleDetails.find('div',class_="listing-details").text
        listingDetails = listingDetails.replace("\n","")
        price = motorcycleDetails.find('h2',class_='text-center strong').text
        price = price.replace("\n","")
        if price=="Carry On Installment":
            break
        else:
            price = price.split("$")[1]


            values = rowValue[0].find_all('td',class_="value")
            listOfValues=[]
            for value in rowValue:
                if value.text !="":
                    
                    listOfValues.append(value.text.replace("\n",""))

            model = listOfValues[2]  
            coeExpiryDate = listOfValues[6]
            coeExpiryDate = coeExpiryDate.strip()
            coeExpiryDate = coeExpiryDate.split("(")[0]
            #['30', '11', '2031 ']
            coeExpiryDate = coeExpiryDate.split("/")
            coeExpiryDate[2].strip()
            formattedCoeExpiryDate = coeExpiryDate[0] +"-"+months_in_year[int(coeExpiryDate[1])]+"-"+coeExpiryDate[2][-3:-1]




            if model in listOfExistingModels:

                listOfPossibleListingsIndex = get_index_positions(listOfExistingModels,model)
                correctPosition= None
                
                for i in listOfPossibleListingsIndex:
                #09-Jan-29(formattedCoeExpiryDate)
                #6-Jan-29(df.loc[i]['COE Expiry Date']) 
                    dateTime = df.loc[i]['COE Expiry Date'].strftime("%d-%b-%Y")
                    dateTime = dateTime.split('-')
                    dateTimeFormatted = dateTime[0]+"-"+dateTime[1]+"-"+dateTime[2][2:]

                    if(len(dateTimeFormatted)<9):
                        
                        if("0"+dateTimeFormatted == formattedCoeExpiryDate and df.loc[i]['Model'] == model):
                            correctPosition=i
                            break

                    else:    
                        if(dateTimeFormatted == formattedCoeExpiryDate and df.loc[i]['Model'] == model):
                            correctPosition=i
                            break

                if correctPosition != None:
                    print('Inserting new price for an existing model')
                    df.loc[correctPosition, 'Price ('+formattedDate+')'] = int(price)
                    df.loc[correctPosition, 'Price'] = int(price)

                else:
                    print("model does exist within list, but it's a new listing")
                    listingType = listOfValues[0]
                    brand = listOfValues[1]
                    engineCapacity = listOfValues[3]
                    classification = listOfValues[4]
                    registrationDate = listOfValues[5]
                    mileage = listOfValues[7]
                    noOfOwners = listOfValues[8]
                    typeOfVehicle = listOfValues[9]
                    df = df.append({'Brand':brand,'Model':model,'Price':int(price),'Engine Capacity':engineCapacity,'Classification':classification,'Registration Date':registrationDate,'COE Expiry Date':formattedCoeExpiryDate,'Mileage':mileage,'No. of owners':noOfOwners,'Type of Vehicle':typeOfVehicle,'Listing Details':listingDetails,'Price ('+formattedDate+')':price},ignore_index=True)

            else:
                print('new model, inserting new row')
                listingType = listOfValues[0]
                brand = listOfValues[1]
                engineCapacity = listOfValues[3]
                classification = listOfValues[4]
                registrationDate = listOfValues[5]
                mileage = listOfValues[7]
                noOfOwners = listOfValues[8]
                typeOfVehicle = listOfValues[9]
                df = df.append({'Brand':brand,'Model':model,'Price':price,'Engine Capacity':engineCapacity,'Classification':classification,'Registration Date':registrationDate,'COE Expiry Date':formattedCoeExpiryDate,'Mileage':mileage,'No. of owners':noOfOwners,'Type of Vehicle':typeOfVehicle,'Listing Details':listingDetails,'Price ('+formattedDate+')':price},ignore_index=True)
# df['Price'] = df['Price'].apply(lambda x: x.split("$")[1])

# print(df)
with pd.ExcelWriter("sgbikemartFinal.xlsx", engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
    df.to_excel(writer, sheet_name='sgbikemartFinal', index=False)


# for row in tables.tbody.find_all('tr'):    
#     print(row)



    # df = df.append({'Listing Type':listingType,'Brand':brand,'Model':model,'Price':price,'Engine Capacity':engineCapacity,'Classification':classification,'Registration Date':registrationDate,'COE Expiry Date':coeExpiryDate,'Mileage':mileage,'No. of owners':noOfOwners,'Type of Vehicle':typeOfVehicle},ignore_index=True)
# for table in motorcycleDetails.find_all('table'):
#     print(table)
    # rowName=table.find_all('td',class_="name").value
    # rowValue=table.find_all('td',class_="value").value
    # print(rowName,rowValue)

#if model doesnt exist, need to append new row
#if model exist, append new column at specific row
