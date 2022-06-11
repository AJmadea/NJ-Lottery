#!/usr/bin/env python
# coding: utf-8

# In[1]:


import logging
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import os
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service
import time
from datetime import datetime
from os.path import exists
import os
import mysql.connector
import json
from mysql.connector import Error

logging.basicConfig(filename='logs/scratchoff runtime_{}.log'.format(datetime.now().strftime("%Y-%m-%d %H_%M_%S")),
                        encoding='utf-8', level=logging.INFO)

url = 'https://www.njlottery.com/en-us/scratch-offs/active.html#tab-active'

base = 'https://www.njlottery.com/en-us/scratch-offs/{}.html'
credentials = None
with open("db_credentials.json", 'r') as f:
    credentials = json.load(f)

options = Options()
options.headless = True

s = Service('chromedriver.exe')
driver = webdriver.Chrome(service=s,options=options)
driver.maximize_window()
rep= pd.DataFrame(columns=['File','Updated'])

driver.get(url)

e = driver.find_element(By.XPATH, '//*[@id="instantsGames-ACTIVE"]')
logging.info("Got WebElement from website")

html_data = e.get_attribute('innerHTML')

data = BeautifulSoup(html_data, features='lxml')


data.find_all('p')[0]


# In[10]:




logging.info("Parsing Data")
all_div = data.find_all('div')
df = pd.DataFrame()

for d in all_div:
    gn = d.find('h4').get_text().replace('\n','').strip()
    all_ps = d.find_all('p')
    #print(len(all_ps))
    df.loc[gn, 'Game #'] = all_ps[0].get_text().replace('\n','')
    
    _1p = all_ps[1].get_text().replace('\n','')
    df.loc[gn, '1st Prize'] = _1p.split('-')[0].strip()
    df.loc[gn, '1st Prize Count'] = _1p.split('-')[1].strip()
    
    _2p = all_ps[2].get_text().replace('\n','')
    df.loc[gn, '2nd Prize'] = _2p.split('-')[0].strip()
    df.loc[gn, '2nd Prize Count'] = _2p.split('-')[1].strip()
    
    if len(all_ps) < 4:
        continue
    _3p = all_ps[3].get_text().replace('\n','')
    df.loc[gn, '3rd Prize'] = _3p.split('-')[0].strip()
    df.loc[gn, '3rd Prize Count'] = _3p.split('-')[1].strip()
    
df


# In[11]:


for c in df.columns:
    try:
        print(c,pd.isna(df[c]).value_counts()[True])
    except KeyError as err:
        print(c,'0')


# In[12]:


df


# In[13]:


df.dtypes


# In[14]:


for c in df.columns:
    df[c] = df[c].astype(str)


# In[15]:


import re
for c in df.columns[1:]:
    df[c] = df[c].apply(lambda x : re.sub(r'[^0-9]','', x))


# In[16]:


for c in df.columns:
    df[c] = df[c].apply(lambda x : '0' if x=='' else x)
    
df


# In[17]:


for c in df.columns[1:]:
    
    df[c] = df[c].astype('int64')
df


# In[18]:


df['Total Prizes'] = df['1st Prize'] * df['1st Prize Count'] + df['2nd Prize']*df['2nd Prize Count'] + df['3rd Prize']*df['3rd Prize Count']
df.sort_values(by='Total Prizes', inplace=True)
df


# In[19]:


df['Game #'] = df['Game #'].str.replace('Game #','')
df


# In[20]:


df.reset_index(inplace=True)


# In[21]:


df.rename({'index': 'Name'},axis=1, inplace=True)


# In[22]:


logging.info("Data shape: {}".format(df.shape))
logging.info(str(df.index.tolist()))


# In[23]:


df.reset_index()
df.set_index('Game #', inplace=True)
df.index


# In[25]:




frames = []
_i=1
for g in df.index:
    url = base.format(g)
    driver.get(url)
    print(g)
    print(round(float(_i)/df.shape[0]*100,2),"%")
    _i+=1
    time.sleep(6)
    e = driver.find_element(By.XPATH, '//*[@id="prizeChartResult"]')
    html_data= e.get_attribute('innerHTML')
    new_data = pd.read_html(html_data)
    if type(new_data) == list:
        new_data = new_data[0]
    
    new_data.drop('Total Prizes.1', axis=1, inplace=True)
    new_data['Game #'] = g
    
    #driver.get('https://www.njlottery.com/en-us/scratch-offs/01683.html')
    e = driver.find_element(By.XPATH, '/html/body')
    html_data= e.get_attribute('innerHTML')
    bdata = BeautifulSoup(html_data, features='lxml')

    for p in bdata.find_all('p'):
        if 'Approximately' in p.get_text():
            l = p.get_text().split(' ')[1:3]
            tickets = l[0] + " " + l[1]
    
    new_data['Tickets'] = tickets
    
    time_start = '//*[@id="instantGameBanner"]/div/div[2]/div[2]/div/time'
    price = '//*[@id="instantGameBanner"]/div/div[2]/div[1]/div'
    
    e = driver.find_element(By.XPATH, time_start)
    html_data= e.get_attribute('innerHTML')
    bdata = BeautifulSoup(html_data, features='lxml')
    new_data['StartDate'] = bdata.get_text().strip()
    
    e = driver.find_element(By.XPATH, price)
    html_data= e.get_attribute('innerHTML')
    bdata = BeautifulSoup(html_data, features='lxml')
    new_data['Price'] = bdata.get_text().strip()
    
    frames.append(new_data)
    
print('Data Collection Completed')


# In[26]:


combined = pd.concat(frames)


# In[27]:


combined


# In[28]:


combined = combined[combined['Prize Amount'] != 'Tickets Printed  :']
combined.shape


# In[29]:


#combined['Tickets'].unique()
combined['Tickets'] = combined['Tickets'].astype(str)
combined['Tickets'] = combined['Tickets'].str.replace(' million','')
combined['Tickets'] = combined['Tickets'].str.strip()
combined['Tickets'] = combined['Tickets'].astype(float)


# In[30]:


combined['Tickets'].unique()


# In[31]:


combined['Tickets']=combined['Tickets']*1_000_000


# In[32]:


combined


# In[33]:


df


# In[34]:


df.reset_index(inplace=True)
df.rename({'index': 'Game #'},axis=1, inplace=True)

tic_dic = df[['Name', 'Game #']].copy()
tic_dic.drop_duplicates(inplace=True)
tic_dic.set_index('Game #', inplace=True)


#combined.reset_index(inplace=True)
#combined.rename({'index': 'Game #'}, axis=1, inplace=True)
combined = combined.merge(tic_dic, on='Game #', how='left')
logging.info("Shape: "+str(combined.shape))


combined


# In[35]:


tic_dic


# In[37]:


combined.dtypes


# In[ ]:





# In[38]:


combined['Prize Amount'].unique()


# In[39]:


driver.close()


# In[40]:


combined.to_csv("data/Scratch Off All Data.csv",index=False)


# In[41]:


#now = datetime.now().strftime("%Y-%m-%d %H_%M_%S")
df.to_csv('data/Scratch off Data.csv', mode='a', header=False)


# In[42]:


combined


# In[66]:


combined


# In[83]:



print(combined.dtypes)
combined['Total Prizes'] = combined['Total Prizes'].astype(int)
combined['Prize Amount'] = combined['Prize Amount'].astype(str)
combined['Prize Amount'] = combined['Prize Amount'].apply(lambda x : re.sub('[^0-9]','',x))
combined['Prize Amount'] = combined['Prize Amount'].apply(lambda x : '0' if x=='' else x)
combined['Prize Amount'] = combined['Prize Amount'].astype(int) 

rep = pd.DataFrame()
for name in combined.Name.unique():
    sli = combined[combined.Name == name].copy()
    rep.loc[name, 'Prize Tickets'] = (sli['Total Prizes'].sum())
    rep.loc[name, 'Prize Remain'] = (sli['PRIZES REMAINING'].sum())
    rep.loc[name, '% Winners'] = round((sli['Total Prizes'].sum() / sli['Tickets'].unique()[0] * 100),2)
    
    rep.loc[name, '% Game Completed'] = round((1-sli['PRIZES REMAINING'].sum()/sli['Total Prizes'].sum()) * 100,2)
    
    rep.loc[name, 'Tickets'] = (sli['Tickets'].unique()[0])
    rep.loc[name, 'Start Date'] = sli.StartDate.unique()[0]
    rep.loc[name, 'Price'] = sli.Price.unique()[0]
    
    val = 0
    try:
        val = sli['PRIZES REMAINING'].value_counts()[0]
    except KeyError as err:
        val = 0
        
    rep.loc[name, 'Count of 0s'] = val
    
    _sum=0
    for i in sli.index:
        _sum += sli.loc[i, 'Prize Amount'] * sli.loc[i, 'PRIZES REMAINING']
    
    rep.loc[name, 'Remaining Money'] = _sum
    
    _sum2=0
    for i in sli.index:
        _sum2 += sli.loc[i, 'Prize Amount'] * sli.loc[i, 'Total Prizes']
    
    rep.loc[name, 'Money Overall'] = _sum2
    rep.loc[name, '% Money Used'] = round((1-_sum/_sum2) * 100,2)
    
rep


# In[84]:


rep.sort_values(by=['% Game Completed','% Money Used'], ascending=[False,True])


# In[85]:


rep['Runtime'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# In[87]:


rep.to_csv("data/Scratch Off Scrape Report.csv", mode='a', header=False)

print(rep)



scratchoff = rep
scratchoff.reset_index(inplace=True)



sql_query = "INSERT INTO scratchoff (prizeTickets,prizeRemain,percentWinners,percentGameCompleted,tickets,startDate,price,zeroCount,remainingMoney,moneyUsed,runtime,name) VALUES"
name_col = "Unnamed: 0"
if name_col not in scratchoff.columns:
    name_col = "index"
print(scratchoff.columns)
scratchoff[name_col] = scratchoff[name_col].astype(str)
scratchoff[name_col] = scratchoff[name_col].str.replace("\'",'')
scratchoff.Price = scratchoff.Price.astype(str)
scratchoff.Price = scratchoff.Price.str.replace("$",'')
scratchoff['Start Date'] = pd.to_datetime(scratchoff['Start Date'])
int_cols = ["Prize Tickets", 'Prize Remain', 'Tickets', 'Count of 0s', "Remaining Money"]
for int_col in int_cols:
    scratchoff[int_col] = scratchoff[int_col].astype(int)

floats = ["% Winners", "% Game Completed", "% Money Used", "Price"]
for f in floats:
    scratchoff[f] = scratchoff[f].astype(float)

#scratchoff.Runtime = scratchoff.Runtime.astype(str)
#scratchoff.Runtime = scratchoff.Runtime.apply(lambda x: x.split(' ')[0])

scratchoff['Runtime'] = pd.to_datetime(scratchoff['Runtime'], format="%Y-%m-%d")

print(scratchoff.head())

for i in scratchoff.index:
    #print(scratchoff.loc[i,:])
    new_row = " (\'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\'), ".format(
        scratchoff.loc[i, "Prize Tickets"],
        scratchoff.loc[i, "Prize Remain"],
        scratchoff.loc[i, "% Winners"],
        scratchoff.loc[i, "% Game Completed"],
        scratchoff.loc[i, "Tickets"],
        scratchoff.loc[i, "Start Date"],
        scratchoff.loc[i, "Price"],
        scratchoff.loc[i, "Count of 0s"],
        scratchoff.loc[i, "Remaining Money"],
        scratchoff.loc[i, "% Money Used"],
        scratchoff.loc[i, "Runtime"],
        scratchoff.loc[i, name_col],
    )
    sql_query += new_row

    
sql_query=sql_query[:-2]+";"

try:
    

    connection = mysql.connector.connect(host=credentials["host"],
                                        database=credentials['database'],
                                        user=credentials['user'],
                                        password=credentials['password'])
    
    if connection.is_connected():
        db_Info = connection.get_server_info()
        print("Connected to MySQL Server version ", db_Info)
        cursor = connection.cursor()
        cursor.execute(sql_query)
        connection.commit()
        print(cursor.rowcount, "Record inserted successfully into Laptop table")
        #record = cursor.fetchone()
        print("You're connected to database: ", record)

except Error as e:
    print("Error while connecting to MySQL", e)
finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed")