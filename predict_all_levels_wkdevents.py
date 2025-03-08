import pandas as pd
from pandas import read_csv
from datetime import datetime
import numpy as np
import statistics
from sklearn.preprocessing import LabelEncoder
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.layers import TimeDistributed
import keras.backend as K
import random
import csv
random.seed(168)

#Load training sets and filter for Hobbies category
raw = read_csv("sales_train_validation.csv")
train =  read_csv("sales_test_validation.csv")
train_val = pd.concat([raw, train.iloc[:,-28:]],axis=1)
train_val = train_val[train_val['cat_id']=='HOBBIES']

#separate Hobbies1 and Hobbies2
Hobbies_1 = train_val[train_val['dept_id']=='HOBBIES_1']
Hobbies_2 = train_val[train_val['dept_id']=='HOBBIES_2']

#load store-dept predictions and name column headers
store_dep_pred = read_csv('level9_pred_wkdevents.csv', header=None)
store_dep_pred.columns = ['level_id','dept_id','store_id','quantile','d_1',
                          'd_2','d_3','d_4','d_5','d_6','d_7','d_8','d_9','d_10','d_11',
                          'd_12','d_13','d_14','d_15','d_16','d_17','d_18','d_19',
                          'd_20','d_21','d_22','d_23','d_24','d_25','d_26','d_27',
                          'd_28']

#define quantiles
quantiles = (0.005,0.025, 0.165, 0.250, 0.500, 0.750, 0.835, 0.975,0.995)

#load evaluation sets and separate hobbies1 and hobbies2
train_eval = read_csv("sales_test_evaluation.csv")
train_eval = train_eval[train_eval['cat_id']=='HOBBIES']
H1_eval = train_eval[train_eval['dept_id']=='HOBBIES_1']
H2_eval = train_eval[train_eval['dept_id']=='HOBBIES_2']

#load weights
weights = read_csv('weights_evaluation.csv')

#function to get denominator
def get_denominator(sales_data):
    diff = 0
    for i in range(1,len(sales_data)):
        diff += abs(sales_data[i] - sales_data[i-1])
    return diff/(len(sales_data)-1)


#function to calculate SPL   
def SPL(y_true, y_pred, quantile, denom):
    score = 0
    for i in range(len(y_true)):
        yt, yp = y_true[i],y_pred[i]
        if (yp<= yt):
            score = score + ((yt-yp)*quantile)
        else:
            score = (score + ((yp-yt)*(1-quantile)))
    return (score/(28*denom))

Level_Scores = {}

"""---------------------------- LEVEL 12 ---------------------------------------------------------------"""

print('L12')
prediction_lines=[]
score_lines = []
weighted_SPL = {}

prediction_lines=[]
score_lines = []
weighted_SPL = {}
for store in np.unique(Hobbies_1['store_id']):
#5for store in ['CA_1','CA_2']:
    df1 = Hobbies_1[Hobbies_1['store_id'] == store]
    df2 = Hobbies_2[Hobbies_2['store_id']==store]
    
    H1_item_info = {}
    H2_item_info = {}

    storesum = 0
    store2sum = 0
    agg= store_dep_pred[store_dep_pred['store_id']==store]
    agg1= agg[agg['dept_id'] == 'HOBBIES_1']
    agg2 = agg[agg['dept_id'] == 'HOBBIES_2']

    yt1_store = H1_eval[H1_eval['store_id']==store]
    yt2_store = H2_eval[H2_eval['store_id']==store]

    weights_store = weights[weights['Agg_Level_2']==store]
    
    for item in np.unique(df1['item_id']):
        item_df = df1[df1['item_id']==item]
        item_total = sum(item_df.iloc[0,-28:])
        storesum += item_total
        H1_item_info[item] = [item_total]

    for item in np.unique(df2['item_id']):
        item_df2 = df2[df2['item_id']==item]
        item_total2 = sum(item_df2.iloc[0,-28:])
        store2sum += item_total2
        H2_item_info[item] = [item_total2]


    print('a')
    for item in H1_item_info.keys():
        info = H1_item_info[item]
        percentage = info/storesum
        item_weight = weights_store[weights_store['Agg_Level_1']==item]['weight']
        for q in quantiles:
                upper_prediction = agg1[agg1['quantile']==q]
                base = upper_prediction.iloc[0,-28:]
                ypred = base*percentage[0]
                ypred = [round(i) for i in ypred]
                
                line = ['Level12',item, store,q]
                line.extend(ypred)
                prediction_lines.append(line)

                yt1 = yt1_store[yt1_store['item_id']==item]
                ytrue = list(yt1.iloc[0,-28:])
                
                item_sales = np.array(item_df.iloc[0,5:1946])
                ind = np.where(item_sales !=0)[0][0]
                item_sales_final = item_sales[ind:]
                d = get_denominator(item_sales_final)

                item_SPL = SPL(ytrue,ypred,q,d)

                
                item_WSPL = float(item_weight)*item_SPL/9
                
                score_line = ['Level12',item, store,q]
                score_line.append(item_WSPL)
                score_lines.append(score_line)

                key = 'Level12' +str(item) +str(store) +str(q)
                weighted_SPL[key] = item_WSPL

            
    print('b')
    for item in H2_item_info.keys():
        info = H2_item_info[item]
        percentage = info/store2sum
        for q in quantiles:
                upper_prediction = agg2[agg2['quantile']==q]
                base = upper_prediction.iloc[0,-28:]
                ypred = base*percentage[0]
                ypred = [round(i) for i in ypred]
                
                line = ['Level12',item, store,q]
                line.extend(ypred)
                prediction_lines.append(line)

                yt2 = yt2_store[yt2_store['item_id']==item]
                ytrue = list(yt2.iloc[0,-28:])
                
                item_sales = np.array(item_df2.iloc[0,5:1946])
                ind = np.where(item_sales !=0)[0][0]
                item_sales_final = item_sales[ind:]
                d = get_denominator(item_sales_final)

                item_SPL = SPL(ytrue,ypred,q,d)

                item_weight = weights_store[weights_store['Agg_Level_1']==item]['weight']
                item_WSPL = float(item_weight)*item_SPL/9
                
                score_line = ['Level12',item, store,q]
                score_line.append(item_WSPL)
                score_lines.append(score_line)

                score_lines.append(score_line)

                key = 'Level12' +str(item) +str(store) +str(q)
                weighted_SPL[key] = item_WSPL

Level_Scores['level12']=sum(weighted_SPL.values())

with open('level12_wkdeventspred.csv','w',newline='') as file:
    writer=csv.writer(file)
    writer.writerows(prediction_lines)
    
file.close()
"""
with open('level12_snap_results.csv','w',newline='') as file:
    writer=csv.writer(file)
    writer.writerows(score_lines)

file.close()
"""

"""---------------------------- LEVEL 11 ---------------------------------------------------------------"""
print('L11')
prediction_lines=[]
score_lines = []
weighted_SPL = {}

states = {}
states['CA'] = ['CA_1', 'CA_2', 'CA_3', 'CA_4']
states['TX'] = ['TX_1', 'TX_2', 'TX_3']
states['WI'] = ['WI_1','WI_2', 'WI_3']

level12_pred = read_csv('level12_wkdeventspred.csv',header = None)
level12_pred.columns = ['level_id','item_id','store_id','quantile','d_1',
                          'd_2','d_3','d_4','d_5','d_6','d_7','d_8','d_9','d_10','d_11',
                          'd_12','d_13','d_14','d_15','d_16','d_17','d_18','d_19',
                          'd_20','d_21','d_22','d_23','d_24','d_25','d_26','d_27',
                          'd_28']

weights_11 = weights[weights['Level_id']=='Level11']

for item in np.unique(level12_pred['item_id']):
    #get item predictions for all stores and quantiles
    item_sales = level12_pred[level12_pred['item_id']==item]

    #get item eval for all stores
    item_eval = train_eval[train_eval['item_id']==item]

    
    item_val = train_val[train_val['item_id']==item]

    #create zeros for total sales to be used in state totals
    total_sales = np.zeros(28)

    #get weights for item in each state    
    item_weights = weights_11[weights_11['Agg_Level_2']==item]
    
    for q in quantiles:
        q_sales = item_sales[item_sales['quantile']==q]
        for state in states.keys():
            item_state_eval = item_eval[item_eval['state_id']==state]
            y_true = list(item_state_eval.iloc[:,-28:].sum())

            item_store_val = item_val[item_val['state_id']==state]
            item_state_val = item_store_val.iloc[:,5:1946].sum()
            
            ind = np.where(item_state_val !=0)[0][0]
            item_sales_final = item_state_val[ind:]
            d = get_denominator(item_sales_final)
            
            for store in states[state]:
                store_sales = q_sales[q_sales['store_id']==store].iloc[0,-28:]
                total_sales += store_sales
                
            line = ['Level11',item, state,q]
            line.extend(total_sales)
            prediction_lines.append(line)
            
            item_SPL = SPL(y_true,total_sales,q,d)
            item_state_weight = item_weights[item_weights['Agg_Level_1']==state]['weight']
            item_WSPL = float(item_state_weight)*item_SPL/9

            score_line = ['Level11',item, state,q]
            score_line.append(item_WSPL)
            score_lines.append(score_line)

            key = 'Level11' +str(item) +str(state) +str(q)
            weighted_SPL[key] = item_WSPL

Level_Scores['level11']=sum(weighted_SPL.values())

with open('level11_wkdeventspred.csv','w',newline='') as file:
    writer=csv.writer(file)
    writer.writerows(prediction_lines)
    
file.close()
"""
with open('level11_snap_results.csv','w',newline='') as file:
    writer=csv.writer(file)
    writer.writerows(score_lines)

file.close()
"""

"""---------------------------- LEVEL 10 ---------------------------------------------------------------"""

print('L10')
prediction_lines=[]
score_lines = []
weighted_SPL = {}

level12_pred = read_csv('level12_wkdeventspred.csv',header = None)
level12_pred.columns = ['level_id','item_id','store_id','quantile','d_1',
                          'd_2','d_3','d_4','d_5','d_6','d_7','d_8','d_9','d_10','d_11',
                          'd_12','d_13','d_14','d_15','d_16','d_17','d_18','d_19',
                          'd_20','d_21','d_22','d_23','d_24','d_25','d_26','d_27',
                          'd_28']

weights_10 = weights[weights['Level_id']=='Level10']

for item in np.unique(level12_pred['item_id']):
    item_sales = level12_pred[level12_pred['item_id']==item]
    item_eval = train_eval[train_eval['item_id']==item]

    item_val = train_val[train_val['item_id']==item]
    total_sales = np.zeros(28)

    item_weight = float(weights_10[weights_10['Agg_Level_1']==item]['weight'])
    
    for q in quantiles:
        q_sales = item_sales[item_sales['quantile']==q]
        y_pred = list(q_sales.iloc[:,-28:].sum())
        y_true = list(item_eval.iloc[:,-28:].sum())

        item_total_val = item_val.iloc[:,5:1946].sum()
        ind = np.where(item_total_val !=0)[0][0]
        item_total_final = item_total_val[ind:]
        d = get_denominator(item_total_final)
            
        line = ['Level10',item, 'x',q]
        line.extend(y_pred)
        prediction_lines.append(line)
            
        item_SPL = SPL(y_true,y_pred,q,d)
        item_WSPL = item_weight*item_SPL/9

        score_line = ['Level10',item, 'x',q]
        score_line.append(item_WSPL)
        score_lines.append(score_line)

        key = 'Level10' +str(item) +'x' +str(q)
        weighted_SPL[key] = item_WSPL


Level_Scores['level10']=sum(weighted_SPL.values())

with open('level10_wkdeventspred.csv','w',newline='') as file:
    writer=csv.writer(file)
    writer.writerows(prediction_lines)
    
file.close()
"""

with open('level10_snap_results.csv','w',newline='') as file:
    writer=csv.writer(file)
    writer.writerows(score_lines)

file.close()
"""
"""---------------------------- LEVEL 8 ---------------------------------------------------------------"""
print('L8')
prediction_lines=[]
score_lines = []
weighted_SPL = {}

level9_pred = read_csv('level9_pred_wkdevents.csv',header=None)
level9_pred.columns = ['level_id','dept_id','store_id','quantile','d_1',
                          'd_2','d_3','d_4','d_5','d_6','d_7','d_8','d_9','d_10','d_11',
                          'd_12','d_13','d_14','d_15','d_16','d_17','d_18','d_19',
                          'd_20','d_21','d_22','d_23','d_24','d_25','d_26','d_27',
                          'd_28']

weights_8 = weights[weights['Level_id']=='Level8']
weights_8 = weights_8[weights_8['Agg_Level_2']=='HOBBIES']

for store in np.unique(level9_pred['store_id']):
    store_sales = level9_pred[level9_pred['store_id']==store]
    y_true = list(train_eval[train_eval['store_id']==store].iloc[:,-28:].sum())
    store_val = train_val[train_val['store_id']==store]
    store_val = store_val.iloc[:,5:1946].sum()
    weight = float(weights_8[weights_8['Agg_Level_1']==store]['weight'])
    d = get_denominator(store_val)
    
    for q in quantiles:
        store_q_sales = store_sales[store_sales['quantile']==q]
        y_pred = list(store_q_sales.iloc[:,-28:].sum())
            
        line = ['Level8',store, 'HOBBIES',q]
        line.extend(y_pred)
        prediction_lines.append(line)
            
        item_SPL = SPL(y_true,y_pred,q,d)
        item_WSPL = weight*item_SPL/9

        score_line = ['Level8',store, 'HOBBIES',q]
        score_line.append(item_WSPL)
        score_lines.append(score_line)

        key = 'Level8' +str(store) +'HOBBIES' +str(q)
        weighted_SPL[key] = item_WSPL
        
Level_Scores['level08']=sum(weighted_SPL.values())

with open('level08_wkdeventspred.csv','w',newline='') as file:
    writer=csv.writer(file)
    writer.writerows(prediction_lines)
    
file.close()
"""
with open('level08_snap_esults.csv','w',newline='') as file:
    writer=csv.writer(file)
    writer.writerows(score_lines)

file.close()
"""

"""---------------------------- LEVEL 7 ---------------------------------------------------------------"""
print('L7')
prediction_lines=[]
score_lines = []
weighted_SPL = {}

level9_pred = read_csv('level9_pred_wkdevents.csv',header=None)
level9_pred.columns = ['level_id','dept_id','store_id','quantile','d_1',
                          'd_2','d_3','d_4','d_5','d_6','d_7','d_8','d_9','d_10','d_11',
                          'd_12','d_13','d_14','d_15','d_16','d_17','d_18','d_19',
                          'd_20','d_21','d_22','d_23','d_24','d_25','d_26','d_27',
                          'd_28']

weights_7 = weights[weights['Level_id']=='Level7']
weights_H1 = weights_7[weights_7['Agg_Level_2']=='HOBBIES_1']
weights_H2 = weights_7[weights_7['Agg_Level_2']=='HOBBIES_2']

states = {}
states['CA'] = ['CA_1', 'CA_2', 'CA_3', 'CA_4']
states['TX'] = ['TX_1', 'TX_2', 'TX_3']
states['WI'] = ['WI_1','WI_2', 'WI_3']

H1_pred = level9_pred[level9_pred['dept_id']=='HOBBIES_1']
H2_pred = level9_pred[level9_pred['dept_id']=='HOBBIES_2']

H1_val = train_val[train_val['dept_id']=='HOBBIES_1']
H2_val = train_val[train_val['dept_id']=='HOBBIES_2']

for state in states.keys():
    H1_state_eval = list(H1_val[H1_val['state_id']==state].iloc[:,-28:].sum())
    H2_state_eval = list(H2_val[H2_val['state_id']==state].iloc[:,-28:].sum())

    H1_state_weight = float(weights_H1[weights_H1['Agg_Level_1']==state]['weight'])
    H2_state_weight = float(weights_H2[weights_H2['Agg_Level_1']==state]['weight'])

    d1 = get_denominator(H1_state_eval)
    d2 = get_denominator(H2_state_eval)
    
    for q in quantiles:
        H1_q_pred = H1_pred[H1_pred['quantile']==q]
        H2_q_pred = H2_pred[H2_pred['quantile']==q]
        
        H1_total_sales = np.zeros(28)
        H2_total_sales = np.zeros(28)
        
        for store in states[state]:
            H1_store_pred = list(H1_q_pred[H1_q_pred['store_id']==store].iloc[0,-28:])
            H2_store_pred = list(H2_q_pred[H2_q_pred['store_id']==store].iloc[0,-28:])
            H1_total_sales+= H1_store_pred
            H2_total_sales+=H2_store_pred
    
            
        line1 = ['Level8',state, 'HOBBIES_1',q]
        line1.extend(H1_total_sales)
        prediction_lines.append(line1)

        line2 = ['Level8',state, 'HOBBIES_2',q]
        line2.extend(H2_total_sales)
        prediction_lines.append(line2)
            
        state_SPL1 = SPL(H1_state_eval,H1_total_sales,q,d1)
        state_SPL2 = SPL(H2_state_eval,H2_total_sales,q,d2)
        
        state_WSPL1 = H1_state_weight*state_SPL1/9
        state_WSPL2 = H2_state_weight*state_SPL2/9

        score_line = ['Level7',state, 'HOBBIES_1',q]
        score_line.append(state_WSPL1)
        score_lines.append(score_line)

        score_line = ['Level7',state, 'HOBBIES_2',q]
        score_line.append(state_WSPL2)
        score_lines.append(score_line)

        key = 'Level7' +str(state) +'HOBBIES_1' +str(q)
        weighted_SPL[key] = state_WSPL1

        key = 'Level7' +str(state) +'HOBBIES_2' +str(q)
        weighted_SPL[key] = state_WSPL2
        
Level_Scores['level07']=sum(weighted_SPL.values())

with open('level07_wkdevents.csv','w',newline='') as file:
    writer=csv.writer(file)
    writer.writerows(prediction_lines)
    
file.close()
"""
with open('level07_snap_results.csv','w',newline='') as file:
    writer=csv.writer(file)
    writer.writerows(score_lines)

file.close()
"""
"""---------------------------- LEVEL 6 ---------------------------------------------------------------"""
print('L6')
prediction_lines=[]
score_lines = []
weighted_SPL = {}

level7_pred = read_csv('level07_wkdevents.csv',header=None)
level7_pred.columns = ['level_id','state_id','dept_id','quantile','d_1',
                          'd_2','d_3','d_4','d_5','d_6','d_7','d_8','d_9','d_10','d_11',
                          'd_12','d_13','d_14','d_15','d_16','d_17','d_18','d_19',
                          'd_20','d_21','d_22','d_23','d_24','d_25','d_26','d_27',
                          'd_28']

weights_6 = weights[weights['Level_id']=='Level6']
weights_H = weights_6[weights_6['Agg_Level_2']=='HOBBIES']

for state in np.unique(level7_pred['state_id']):
    state_pred = level7_pred[level7_pred['state_id']==state]
    state_val = train_val[train_val['state_id']==state]
    state_val_agg = state_val.iloc[:,5:1946].sum()
    y_true = list(state_val.iloc[:,-28:].sum())

    d = get_denominator(state_val_agg)
    weight_state = float(weights_H[weights_H['Agg_Level_1']==state]['weight'])
    
    for q in quantiles:
        q_pred = list(state_pred[state_pred['quantile']==q].iloc[:,-28:].sum())
    
        line = ['Level6',state, 'HOBBIES',q]
        line.extend(q_pred)
        prediction_lines.append(line)
            
        state_SPL = SPL(y_true,q_pred,q,d)
        
        state_WSPL = weight_state*state_SPL/9

        score_line = ['Level6',state, 'HOBBIES',q]
        score_line.append(state_WSPL)
        score_lines.append(score_line)

        key = 'Level6' +str(state) +'HOBBIES' +str(q)
        weighted_SPL[key] = state_WSPL

Level_Scores['level06']=sum(weighted_SPL.values())

with open('level06_wkdeventspred.csv','w',newline='') as file:
    writer=csv.writer(file)
    writer.writerows(prediction_lines)
    
file.close()
"""
with open('level06_snap_results.csv','w',newline='') as file:
    writer=csv.writer(file)
    writer.writerows(score_lines)

file.close()
"""
"""---------------------------- LEVEL 5 ---------------------------------------------------------------"""
print('L5')
prediction_lines=[]
score_lines = []
weighted_SPL = {}

level7_pred = read_csv('level07_wkdevents.csv',header=None)
level7_pred.columns = ['level_id','state_id','dept_id','quantile','d_1',
                          'd_2','d_3','d_4','d_5','d_6','d_7','d_8','d_9','d_10','d_11',
                          'd_12','d_13','d_14','d_15','d_16','d_17','d_18','d_19',
                          'd_20','d_21','d_22','d_23','d_24','d_25','d_26','d_27',
                          'd_28']

weights_5 = weights[weights['Level_id']=='Level5']

for department in np.unique(level7_pred['dept_id']):
    dept_weight = float(weights_5[weights_5['Agg_Level_1']==department]['weight'])
    dept_pred = level7_pred[level7_pred['dept_id']==department]
    dept_val = train_val[train_val['dept_id']==department]
    dept_val_agg = dept_val.iloc[:,5:1946].sum()
    y_true = list(dept_val.iloc[:,-28:].sum())

    d = get_denominator(dept_val_agg)
    
    for q in quantiles:
        q_pred = list(dept_pred[dept_pred['quantile']==q].iloc[:,-28:].sum())
    
        line = ['Level5',department, 'x',q]
        line.extend(q_pred)
        prediction_lines.append(line)
            
        dept_SPL = SPL(y_true,q_pred,q,d)
        
        dept_WSPL = dept_weight*dept_SPL/9

        score_line = ['Level5',department, 'x',q]
        score_line.append(dept_WSPL)
        score_lines.append(score_line)

        key = 'Level5' +str(department) +'x' +str(q)
        weighted_SPL[key] = dept_WSPL

Level_Scores['level05']=sum(weighted_SPL.values())

with open('level05_wkdeventspred.csv','w',newline='') as file:
    writer=csv.writer(file)
    writer.writerows(prediction_lines)
    
file.close()
"""
with open('level05_snap_results.csv','w',newline='') as file:
    writer=csv.writer(file)
    writer.writerows(score_lines)

file.close()
"""
"""---------------------------- LEVEL 4 ---------------------------------------------------------------"""
print('L4')
prediction_lines=[]
score_lines = []
weighted_SPL = {}

level6_pred = read_csv('level06_wkdeventspred.csv',header=None)
level6_pred.columns = ['level_id','state_id','cat_id','quantile','d_1',
                          'd_2','d_3','d_4','d_5','d_6','d_7','d_8','d_9','d_10','d_11',
                          'd_12','d_13','d_14','d_15','d_16','d_17','d_18','d_19',
                          'd_20','d_21','d_22','d_23','d_24','d_25','d_26','d_27',
                          'd_28']

weights_4 = weights[weights['Level_id']=='Level4']
weight_4 = float(weights_4[weights_4['Agg_Level_1']=='HOBBIES']['weight'])

cat_val = train_val[train_val['cat_id']=='HOBBIES']
cat_val_agg = cat_val.iloc[:,5:1946].sum()
y_true = list(cat_val.iloc[:,-28:].sum())

d = get_denominator(cat_val_agg)

for q in quantiles:
    q_pred = list(level6_pred[level6_pred['quantile']==q].iloc[:,-28:].sum())
    
    line = ['Level4','HOBBIES', 'x',q]
    line.extend(q_pred)
    prediction_lines.append(line)
            
    cat_SPL = SPL(y_true,q_pred,q,d)
        
    cat_WSPL = weight_4*cat_SPL/9

    score_line = ['Level4','HOBBIES', 'x',q]
    score_line.append(cat_WSPL)
    score_lines.append(score_line)

    key = 'Level4' +'HOBBIES' +'x' +str(q)
    weighted_SPL[key] = cat_WSPL


Level_Scores['level04']=sum(weighted_SPL.values())

with open('level04_wkdeventspred.csv','w',newline='') as file:
    writer=csv.writer(file)
    writer.writerows(prediction_lines)
    
file.close()
"""
with open('level04_snap_results.csv','w',newline='') as file:
    writer=csv.writer(file)
    writer.writerows(score_lines)

file.close()
"""
"""---------------------------- LEVEL 3 ---------------------------------------------------------------"""
print('L3')
prediction_lines=[]
score_lines = []
weighted_SPL = {}

level8_pred = read_csv('level08_wkdeventspred.csv',header=None)
level8_pred.columns = ['level_id','store_id','cat_id','quantile','d_1',
                          'd_2','d_3','d_4','d_5','d_6','d_7','d_8','d_9','d_10','d_11',
                          'd_12','d_13','d_14','d_15','d_16','d_17','d_18','d_19',
                          'd_20','d_21','d_22','d_23','d_24','d_25','d_26','d_27',
                          'd_28']

weights_3 = weights[weights['Level_id']=='Level3']

for store in np.unique(level8_pred['store_id']):
    weight = float(weights_3[weights_3['Agg_Level_1']==store]['weight'])
    store_pred = level8_pred[level8_pred['store_id']==store]
    store_val = train_val[train_val['store_id']==store]
    store_val_agg = store_val.iloc[:,5:1946].sum()
    y_true = list(store_val.iloc[:,-28:].sum())

    d = get_denominator(store_val_agg)

    for q in quantiles:
        q_pred = list(store_pred[store_pred['quantile']==q].iloc[:,-28:].sum())
        
        line = ['Level3',store, 'HOBBIES',q]
        line.extend(q_pred)
        prediction_lines.append(line)
                
        store_SPL = SPL(y_true,q_pred,q,d)
            
        store_WSPL = weight*store_SPL/9

        score_line = ['Level3',store, 'HOBBIES',q]
        score_line.append(store_WSPL)
        score_lines.append(score_line)

        key = 'Level3' +store +'HOBBIES'+str(q)
        weighted_SPL[key] = store_WSPL

Level_Scores['level03']=sum(weighted_SPL.values())

with open('level03_wkdeventspred.csv','w',newline='') as file:
    writer=csv.writer(file)
    writer.writerows(prediction_lines)
    
file.close()
"""
with open('level03_snap_results.csv','w',newline='') as file:
    writer=csv.writer(file)
    writer.writerows(score_lines)

file.close()
"""
"""---------------------------- LEVEL 2 ---------------------------------------------------------------"""
print('L2')
prediction_lines=[]
score_lines = []
weighted_SPL = {}

level6_pred = read_csv('level06_wkdeventspred.csv',header=None)
level6_pred.columns = ['level_id','state_id','cat_id','quantile','d_1',
                          'd_2','d_3','d_4','d_5','d_6','d_7','d_8','d_9','d_10','d_11',
                          'd_12','d_13','d_14','d_15','d_16','d_17','d_18','d_19',
                          'd_20','d_21','d_22','d_23','d_24','d_25','d_26','d_27',
                          'd_28']

weights_2 = weights[weights['Level_id']=='Level2']

for state in np.unique(level6_pred['state_id']):
    weight = float(weights_2[weights_2['Agg_Level_1']==state]['weight'])
    state_pred = level6_pred[level6_pred['state_id']==state]
    state_val = train_val[train_val['state_id']==state]
    state_val_agg = state_val.iloc[:,5:1946].sum()
    y_true = list(state_val.iloc[:,-28:].sum())

    d = get_denominator(state_val_agg)

    for q in quantiles:
        q_pred = list(state_pred[state_pred['quantile']==q].iloc[:,-28:].sum())
        
        line = ['Level2',state, 'HOBBIES',q]
        line.extend(q_pred)
        prediction_lines.append(line)
                
        state_SPL = SPL(y_true,q_pred,q,d)
            
        state_WSPL = weight*state_SPL/9

        score_line = ['Level2',state, 'HOBBIES',q]
        score_line.append(state_WSPL)
        score_lines.append(score_line)

        key = 'Level2' +state +'HOBBIES'+str(q)
        weighted_SPL[key] = state_WSPL

Level_Scores['level02']=sum(weighted_SPL.values())

with open('level02_wkdeventspred.csv','w',newline='') as file:
    writer=csv.writer(file)
    writer.writerows(prediction_lines)
    
file.close()
"""
with open('level02_snap_results.csv','w',newline='') as file:
    writer=csv.writer(file)
    writer.writerows(score_lines)

file.close()
"""

"""---------------------------- LEVEL 1 ---------------------------------------------------------------"""
print('L1')
prediction_lines=[]
score_lines = []
weighted_SPL = {}

level2_pred = read_csv('level02_wkdeventspred.csv',header=None)
level2_pred.columns = ['level_id','state_id','cat_id','quantile','d_1',
                          'd_2','d_3','d_4','d_5','d_6','d_7','d_8','d_9','d_10','d_11',
                          'd_12','d_13','d_14','d_15','d_16','d_17','d_18','d_19',
                          'd_20','d_21','d_22','d_23','d_24','d_25','d_26','d_27',
                          'd_28']

weight =float(weights[weights['Level_id']=='Level1']['weight'])
total_val_agg = train_val.iloc[:,5:1946].sum()
y_true = list(train_val.iloc[:,-28:].sum())

d = get_denominator(total_val_agg)

for q in quantiles:
    q_pred = list(level2_pred[level2_pred['quantile']==q].iloc[:,-28:].sum())
        
    line = ['Level1','Total', 'HOBBIES',q]
    line.extend(q_pred)
    prediction_lines.append(line)
                
    total_SPL = SPL(y_true,q_pred,q,d)
            
    total_WSPL = weight*total_SPL/9

    score_line = ['Level1','Total', 'HOBBIES',q]
    score_line.append(total_WSPL)
    score_lines.append(score_line)

    key = 'Level1' +'Total' +'HOBBIES'+str(q)
    weighted_SPL[key] = total_WSPL

Level_Scores['level01']=sum(weighted_SPL.values())

with open('level01_wkdevents_pred.csv','w',newline='') as file:
    writer=csv.writer(file)
    writer.writerows(prediction_lines)
    
file.close()

with open('level01_snap_esults.csv','w',newline='') as file:
    writer=csv.writer(file)
    writer.writerows(score_lines)

file.close()
    
###########################################################
"""
Level12_score = 0.055038435237690385
Level11_score = 0.38054203881247584
Level10_score = 0.03169971150515318
Level9_score = 0.02840082
Level8_score = 0.0310751983535637
Level7_score = 0.02939071213837144
Level6_score = 0.0374126443228736
Level5_score = 0.03731924574096176
Level4_score = 0.04287511778778213
Level3_score = 0.23506549026882895
Level2_score = 0.28391567838761467
Level1_score = 0.3323565999868749

####round 2 (not round)
level12_score = 0.05583203969558591
level11 : 0.380677947641822
level10 : 0.031939719018182475
level08 : 0.03162108105125364
level07 : 0.029886745095362988
level06 : 0.03669626142840219
level05 : 0.037977279396053616
level04 : 0.04263246551589196
level03 : 0.24473397262238533
level02 : 0.28307579229225466
level01 : 0.3304756236018376
"""
#average 0.1254624106132527
