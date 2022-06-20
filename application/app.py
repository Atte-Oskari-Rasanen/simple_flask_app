#from application import app
import pandas as pd
import json
from email import header
import requests
import os 
import statistics as stat
from flask import Flask, render_template
from datetime import datetime
import re

'''
A flask app that gathers information from a given API, calculates certain stats
and presents them on the browser.
'''

os.chdir("/home/atte/Documents/flask_tutorials/tut3_new/")

#os.chdir("/home/atte/Documents/flask_tutorials/flask_tutorial2")

#
my_header = {
        "Content-Type": "application/json",
        "Accept": "application/hal+json",
        "x-api-key": "undetermined"
}


#import flask object and create an instance of flask application called app
app = Flask(__name__)

def get_api_data(headers, url):
    # First call to get first data page from the API
    response = requests.get(url=url,
                            headers=my_header,
                            data=None,
                            verify=False)

    # Convert response string into json data and get embedded limeobjects
    json_data = json.loads(response.text)
    limeobjects = json_data.get("_embedded").get("limeobjects")

    # Check for more data pages and get thoose too
    nextpage = json_data.get("_links").get("next")
    while nextpage is not None:
        url = nextpage["href"]
        response = requests.get(url=url,
                                headers=my_header,
                                data=None,
                                verify=False)

        json_data = json.loads(response.text)
        limeobjects += json_data.get("_embedded").get("limeobjects")
        nextpage = json_data.get("_links").get("next")

    return limeobjects


#when we go over the companies there are multiple companies with same name. this is cuz
#different ppl fromsame companies may have contacted them


#go over the companies and save the deals done with the same company into a dict
#with key being the company name and the value being the index in the limeobject
def companies_x_index(limeobjects):
    names=[]
    comp_x_index=dict()
    for i in range(len(limeobjects)):
        if limeobjects[i]['name'] not in comp_x_index.keys():
            val_list=[]
            val_list.append(i)
            comp_x_index[limeobjects[i]['name']]=val_list
        else:
            indeces=[]
            new_i=[]
            new_i.append(i)
            
            indeces.extend(list(set(comp_x_index[limeobjects[i]['name']])) + new_i)
    
            #indeces.append(comp_x_index[limeobjects2[i]['name']])
            indeces.append(i)
            comp_x_index.update({limeobjects[i]['name']: indeces})
    
    #to remove potential duplicates
    for key, value in comp_x_index.items():
        comp_x_index[key]=list(set(value))
    return(comp_x_index)
    

##CLUSTERING

# #get mean deal values for each company, use k means to cluster, get the means for the different groups
# base_url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/deal/"

# params = "?_limit=50"
# url = base_url + params

# limeobjects=get_api_data(header, url)

# comp_x_index=companies_x_index(limeobjects)
# company_x_deal=dict()
# for company, comp_i in comp_x_index.items():
#     deal_values_comp=[]
#     for i in comp_i:       
#         deal_values_comp.append(limeobjects[i]['value'])
#     company_x_deal[company]=round(stat.mean(deal_values_comp),3)
# company_x_deal.keys()
# df_comp_deal=pd.DataFrame(company_x_deal.items(), columns=['Company', 'Mean_deal_value'])
# df_comp_deal
# df_comp_deal.iloc[:,1]
# import matplotlib.pyplot as plt
# pd.Series(df_comp_deal.iloc[:,1]).plot(kind="bar")
# #which companies belong to these groups?

# import seaborn as sns
# df_comp_deal.info()
# sns.pairplot(df_comp_deal)
# from sklearn.cluster import KMeans
# # feature vector
# X = df_comp_deal

# # target variable
# y = df_comp_deal['Company']

# # importing label encoder
# from sklearn.preprocessing import LabelEncoder

# # converting the non-numeric to numeric values
# le = LabelEncoder()
# X['Company'] = le.fit_transform(X['Company'])
# y = le.transform(y)

# # k value assigned to 2
# kmeans = KMeans(n_clusters=2, random_state=0) 

# # fitting the values
# kmeans.fit(X)

# # Cluster centers
# kmeans.cluster_centers_





def dealsvalue_customer(limeobject,comp_x_index):
    customer_won=dict()
    for company, comp_i in comp_x_index.items():
        for i in comp_i:
            crm_object=limeobject[i]
            #get last years results only
            if int(crm_object['_timestamp'].split("-")[0])==2021 and crm_object['dealstatus']['key']=='agreement':
                if company in customer_won:
                    customer_won[company]=customer_won[company] + crm_object['value']
                else:
                    customer_won[company]=crm_object['value']
            else:
                continue
        customer_won_df= pd.DataFrame(customer_won.items(), columns=["Company", "Total value of won deals"])
        customer_won_df=customer_won_df.fillna(0)
    return(customer_won_df)

#gets the status of the company, returns the status with number of companies in it
#and the company names formatted as html format bullet points
def status_company(limeobjects, comp_x_index):
    company_status=dict()

    for company, comp_i in comp_x_index.items():
        for i in comp_i:
            #get the specific deal that the company has made
            
            company_deal=limeobjects[i]
            url_relation_comp=limeobjects[i]['_links']['relation_company']["href"]
            
            # First call to get first data page from the API
            response = requests.get(url=url_relation_comp,
                                    headers=my_header,
                                    data=None,
                                    verify=False)
            if not re.search('2.+', str(response).split("[")[1].split("]")[0]):
                #print("Could not retrieve information from " + company + " at index " + str(i))
                continue
            else:
                # Convert response string into json data and get embedded limeobjects
                company_json = json.loads(response.text)
                #get last years results only. If any of the company's purchases have been made in the prev year, label it as customer and continue
                #if datetime.strptime("-".join(limeobjects[0]['_timestamp'].split("-")[:2]) + "-", "%Y-%m-")<= datetime.now() and datetime.strptime("-".join(limeobjects[0]['_timestamp'].split("-")[:2]) + "-", "%Y-%m-")>=datetime(datetime.now().year - 1, datetime.now().month, datetime.now().day) and company_deal['dealstatus']['key']=='agreement':
                if datetime.strptime("-".join(limeobjects[i]['_timestamp'].split("-")[:2]) + "-", "%Y-%m-")>=datetime(datetime.now().year - 1, datetime.now().month, datetime.now().day) and company_deal['dealstatus']['key']=='agreement':
                    company_status[company]="customer"
                    continue
                elif int(company_deal['_timestamp'].split("-")[0])<2021 and company_deal['dealstatus']['key']=='agreement':
                    company_status[company]="inactive"
                elif int(company_deal['_timestamp'].split("-")[0])<2021 and company_deal['dealstatus']['key']!='agreement' and company_json['buyingstatus']['key']!='notinterested':
                        company_status[company]="prospect"
                else:
                    company_status[company]="notinterested"
            
    from collections import Counter
    count = Counter(company_status.values())
    customers=[]
    inactives=[]
    prospects=[]
    notinterested=[]
    for company, status in company_status.items():
        if status=='customer':
            customers.append(company)
        elif status=='inactive':
            inactives.append(company)
        elif status=='prospect':
            prospects.append(company)
        else:
            notinterested.append(company)
            
    col1="Customers" + " (" + str(count['customer']) + ")"
    col2="Inactives" +" (" + str(count['inactive']) + ")"
    col3="Prospects" + " (" + str(count['prospect']) + ")"
    col4="Not interested" + " (" + str(count['notinterested']) + ")"
    
    table_dic={col1: customers, col2:inactives, col3:prospects, col4:notinterested}
    
    bulletpoints={}
    companies_inlist=['<ul>']
    for keys, values in table_dic.items():
        companies_inlist=['<ul>']
        for value in values:
            companies_inlist.append("<li>" + value + "</li>")
        companies_inlist.append("</u>")
        companies_list="\n".join(companies_inlist)
        bulletpoints[keys]=companies_list

    return(bulletpoints)


########################################

def calculations(base_url):
    # Convert response string into json data and get embedded limeobjects
    params = "?_limit=50"
    url = base_url + params
    limeobjects=get_api_data(header, url)
    
   #1 Average,    
    deal_values=[]
    for data_dic in limeobjects:
        #get last years results only
        if data_dic['_timestamp'].split("-")[0]=='2021':
            if data_dic['dealstatus']['key']=='agreement':
                deal_values.append(data_dic['value'])
    av_deal=str(int(stat.mean(deal_values))) + " SEK"  
    std_deal=str(int(stat.stdev(deal_values))) + " SEK" 
    med_deal=str(int(stat.median(deal_values))) + " SEK"
    av_std_med=[av_deal,std_deal,med_deal]

    #2 Number of won deals per month
    month_deals=dict()
    for data_dic in limeobjects:
        month=data_dic['_timestamp'].split("-")[1]
        #get last years results only
        if data_dic['_timestamp'].split("-")[0]=='2021' and data_dic['dealstatus']['key']=='agreement':
            if month in month_deals:
                month_deals[month]=month_deals[month] + 1
            else:
                month_deals[month]=1

    month_deals_sort=dict()
    for key in sorted(month_deals):
        month_deals_sort[key]=month_deals[key]
    month_deals_df= pd.DataFrame(month_deals_sort.items(), columns=["Month", "Number of deals won"])
    month_deals_df
    
   
    comp_x_index=companies_x_index(limeobjects)
    
    #3 - Total value of won deals per customer
    customer_won_df=dealsvalue_customer(limeobjects, comp_x_index)

    '''
    check if the company has bought anything last year - customer 
    if not last year but in past - inactive
    never bought - prospect unless status notinterested
    '''
    #4
    table_dic=status_company(limeobjects, comp_x_index)
    return([av_std_med,month_deals_df,customer_won_df, table_dic])




#set the app instance up to manage web requests and send responses to the user
@app.route("/")


def home():
    base_url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/deal/"

    data_list=calculations(base_url)      

    new_pie={'Customer': ' '.join(re.findall(r"\((\d+)\)",list(data_list[-1].keys())[0])), 'Inactive': ' '.join(re.findall(r"\((\d+)\)",list(data_list[-1].keys())[1])), 'Prospects': ' '.join(re.findall(r"\((\d+)\)",list(data_list[-1].keys())[2])), 'Not interested': ' '.join(re.findall(r"\((\d+)\)",list(data_list[-1].keys())[3]))}
    
   
    return render_template('home.html', av=data_list[0][0], std=data_list[0][1], med=data_list[0][2],
           x1 = list(data_list[1]['Month']), y1=list(data_list[1]['Number of deals won']), 
           x2 = list(data_list[2]['Company']), y2=list(data_list[2]['Total value of won deals']),
           pie_keys=list(new_pie.keys()), pie_values=list(new_pie.values()), 
           customers=data_list[-1][list(data_list[-1].keys())[0]],
           inactives=data_list[-1][list(data_list[-1].keys())[1]],
           prospects=data_list[-1][list(data_list[-1].keys())[2]],
           notinterested=data_list[-1][list(data_list[-1].keys())[3]])

#           set=zip(companies_all, companies_categ, colors))

#    return render_template("home.html")
# make a list of companies that were put in each status
if __name__=="__main__":
    app.run(debug=True)
