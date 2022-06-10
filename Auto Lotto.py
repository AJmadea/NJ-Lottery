#!/usr/bin/env python
# coding: utf-8

# In[ ]:





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
import yagmail
from os.path import exists
import os


# In[2]:


def combine_and_drop(path_to_old_data, new_data):
    if not exists(path_to_old_data):
        new_data.to_csv(path_to_old_data,index=False)
        rep.loc[path_to_old_data.replace(".csv",'').replace('data/','')] = new_data.shape[0]
    else:
        old = pd.read_csv(path_to_old_data)

        combined = pd.concat([old,new_data])
        before = old.shape[0]

        print('Old Data Shape: ',old.shape)
        combined.drop_duplicates(inplace=True)
        combined.to_csv(path_to_old_data, index=False)
        print('New Data Shape: ',combined.shape)

        rep.loc[path_to_old_data.replace(".csv",'').replace('data/','')] = abs(before-combined.shape[0])

if __name__ == '__main__':
    logging.basicConfig(filename='logs/runtime_{}.log'.format(datetime.now().strftime("%Y-%m-%d %H_%M_%S")),
                        encoding='utf-8', level=logging.DEBUG)
    logging.info('getting info from URL')
    
    base_url = 'https://www.njlottery.com/en-us/drawgames/{}.html'
    root = 'C:/Users/Andrew/Desktop/Lottery/'
    
    lotto_navigation = pd.read_csv(root+"Lottery Navigation.csv", index_col='HTML File')
    logging.info('Read Navigation')
    out_file = 'Lotto Data'
    options = Options()
    options.headless = True

    s = Service(root+'chromedriver.exe')
    driver = webdriver.Chrome(service=s,options=options)
    driver.maximize_window()
    rep= pd.DataFrame(columns=['File','Updated'])
    rep.set_index('File', inplace=True)

    logging.info('Opened Selenium')
    for each_file in lotto_navigation.index:
        driver.get(base_url.format(each_file))
        print(each_file)
        logging.info('getting info for {}'.format(each_file))
        time.sleep(4)
        
        we = driver.find_element(By.XPATH, lotto_navigation.loc[each_file,'XPATH'])
        table = pd.read_html(we.get_attribute('innerHTML'))
        table = table[0]
        rc = table.columns[0]
        table.dropna(subset=[rc],inplace=True)

        for c in table.columns:
            if 'Unnamed' in c:
                table.drop(c,axis=1,inplace=True)
        print(table.columns)
        combine_and_drop('{}data/{}'.format(root,lotto_navigation.loc[each_file,'OUTPUT FILE']),table)

        #time.sleep(4)
    print("Data Collection Ended")
    logging.info('Data Collection ended')
    now = datetime.now().strftime("%Y-%m-%d %H_%M_%S")
    logging.info('at {}'.format(now))
    
    rep.to_csv('{}rep/Report {}.csv'.format(root,now))
    contents = "Newly added rows\nReport for job ran on :"+now+"\n"

    for i in rep.index:
        contents += str(i)+'\t'+str(rep.loc[i,'Updated'])+'\n'

    print(contents)

    driver.close()
    logging.info('Driver closed')
    logging.info(contents)
    
    output_path='{}/data/Report Over Time.csv'.format(root)
    rep = rep.transpose()
    rep['Datetime'] = datetime.now()
    
    rep.to_csv(output_path, mode='a', header=not os.path.exists(output_path))
    
    '''
    try:
        yag = yagmail.SMTP("njlottoscraper@gmail.com", 'b8970ecvh', oauth2_file="oauth2_creds.json")
        yag.send(to='andrewmadea@gmail.com', subject="NJ Lotto Scrape at {}".format(now), contents=contents)
        yag.close()
    except HTTPException as err:
        print(err)
        if yag is not None:
            yag.close()'''

    

