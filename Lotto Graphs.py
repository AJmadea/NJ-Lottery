#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sns

files = glob.glob("data/* Data.csv")
files


# In[2]:


from joypy import joyplot
from matplotlib import cm


# In[3]:


from os.path import exists


# In[4]:


def create_dist(filename, delim, title, cmap, n=6, show=False):
    qd = pd.read_csv(filename)
    qd['Winning Numbers'] = qd["Winning Numbers"].str.replace("  ", " ")
    numbs = qd['Winning Numbers'].str.split(delim,n=n, expand=True)
    numbs.dropna(inplace=True)
    #i, numbs[i].value_counts().idxmax(), round(numbs[i].value_counts().max()/803 * 100,2)
    for c in numbs:
        numbs[c]=numbs[c].astype(int)
    mode_report = pd.DataFrame(columns=["Col","Mode","P"])
    
    for i in range(numbs.shape[1]):
        mode_report = mode_report.append({"Col":i,
                                         "Mode": numbs[i].value_counts().idxmax(),
                                         "P": round(numbs[i].value_counts().max()/numbs.shape[0] * 100,2)},
                                        ignore_index=True)
    if show:
        print(mode_report)
        
    _dir = "graphs"
    print(_dir)
    if not exists(_dir):
        os.mkdir(_dir)
    
    _max = 0
    for c in numbs.columns:

        if numbs[c].max() > _max:
            _max = numbs[c].max()
            
    matrix = pd.DataFrame(index=range(0,numbs.shape[1]), columns=range(1,_max+1))
    for i in matrix.index:
        for j in matrix.columns:
            try:
                matrix.loc[i,j] = round(numbs[i].value_counts()[j] / numbs.shape[0]*100, 4)
            except KeyError as err:
                matrix.loc[i,j] = 0

    heat = px.imshow(matrix, title='Number Position Frequency for {}'.format(title))
    heat.update_xaxes(title="Number")
    heat.update_yaxes(title="Position")
    heat.write_image(_dir+"/HeatMap {}.jpg".format(title))
    
    if show:
        heat.show()
        print(numbs.columns)
        
    frames=[]
    for col in numbs.columns:
        rep = pd.DataFrame(columns=["Position","Number"])
        rep['Number'] = numbs[col]
        rep['Position'] = col
        frames.append(
            rep
        )
        #print(col)
        '''for each_n in numbs[col]:
            rep = rep.append({"Position":col, "Number":each_n}, ignore_index=True)'''
        
        
    rep = pd.concat(frames)
    #print(rep.Position.value_counts())
    rep.Position = rep.Position+1
    rep.Position = rep.Position.astype(str)
    rep.Position = rep.Position.apply(lambda x: "0"+x if len(x)==1 else x)
    
    #print(rep.Number.value_counts())
    rep.dropna(subset=['Number'], inplace=True)
    rep.Number = rep.Number.astype(int)
    
    fig, ax = joyplot(rep, by="Position", column="Number", fade=True, title=title, colormap=cmap, figsize=(6,6))
    plt.title(title, color='white')
    plt.xlabel("Winning Number", fontsize=8, color='white')
    plt.ylabel("Position", fontsize=20, color='white')
    '''
    ax[-1].set_xlabel('Winning Number', fontsize=8)
    ax[4].set_ylabel('Position', fontsize=7)'''
    fig.savefig(_dir+"/{}.png".format(title), transparent=True)
    return rep


# In[5]:


files


# In[9]:


file_dict = {}
for f in files:
    file_dict[f] = f[f.find("\\")+1:f.find("Data")].strip()
    

plt.rcParams['axes.facecolor']='black'

for k in file_dict.keys():
    try:
        create_dist(k," ", file_dict[k],n=20, cmap=cm.summer,show=False)
    except Exception as err:
        print(err)

