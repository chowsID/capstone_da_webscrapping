from flask import Flask, render_template
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from bs4 import BeautifulSoup 
import requests

#don't change this
matplotlib.use('Agg')
app = Flask(__name__) #do not change this

#insert the scrapping here
url_get = requests.get('https://www.kalibrr.id/id-ID/job-board/te/data/1')
soup = BeautifulSoup(url_get.content,"html.parser")


#find your right key here
table = soup.find('div', attrs = {'k-border-b k-border-t k-border-tertiary-ghost-color md:k-border md:k-overflow-hidden md:k-rounded-lg'})
company_name = table.find_all('span', attrs = {'class':'k-inline-flex k-items-center k-mb-1'})
job_title = table.find_all('a', attrs = {'class': 'k-text-primary-color', 'itemprop': 'name'})
job_location = table.find_all('a', attrs = {'class':"k-text-subdued k-block"})
postingdate_and_deadline = table.find_all('span', attrs = {'class':'k-block k-mb-1'})

row_length = len(company_name)
row_length2 = len(job_title)
row_length3 = len(job_location)
row_length4 = len(postingdate_and_deadline)

temp = [] #initiating a list 

for i in range(0, row_length):

        
    #get company_name
    company_name = table.find_all('span', attrs = {'class':'k-inline-flex k-items-center k-mb-1'})[i].text
    company_name = company_name.strip()
    
    #get job_title
    job_title = table.find_all('a', attrs = {'class': 'k-text-primary-color', 'itemprop': 'name'})[i].text
    job_title = job_title.strip()
    
    #get job_location
    job_location = table.find_all('a', attrs = {'class':"k-text-subdued k-block"})[i].text
    job_location = job_location.strip()
    
    #get postingdate_and_deadline 
    postingdate_and_deadline = table.find_all('span', attrs = {'class':'k-block k-mb-1'})[i].text
    postingdate_and_deadline = postingdate_and_deadline.strip()

    temp.append((company_name, job_title, job_location, postingdate_and_deadline))


#change into dataframe
df = pd.DataFrame(temp, columns = ('company_name', 'job_title', 'job_location', 'postingdate_and_deadline'))

#insert data wrangling here
df['job_location'] = df['job_location'].str.replace(', Indonesia', '')
df['job_location'] = df['job_location'].str.replace('Jakarta Selatan', 'South Jakarta')
df['job_location'] = df['job_location'].str.replace('Kota Jakarta Barat', 'West Jakarta')
df['job_location'] = df['job_location'].str.replace('Jakarta Pusat', 'Central Jakarta')
df['job_location'] = df['job_location'].str.replace('Central Jakarta City', 'Central Jakarta')
df['job_location'] = df['job_location'].str.replace('Tangerang Selatan', 'South Tangerang')
df['postingdate_and_deadline'] = df['postingdate_and_deadline'].str.replace('a month','30 days')
df['postingdate_and_deadline'] = df['postingdate_and_deadline'].str.replace('a day','1 day')
df['posted_since_days_ago'] = df['postingdate_and_deadline'].str.extract('(\d+)')
df['application_deadline'] = df['postingdate_and_deadline'].str.slice(start = -6)
df= df.drop(['postingdate_and_deadline'], axis=1)
df['job_location'] = df['job_location'].astype('category')
df['application_deadline'] = df['application_deadline'].str.replace(' May','-05-2023' )
df['application_deadline'] = df['application_deadline'].str.replace(' Jun','-06-2023' )
df['application_deadline'] = df['application_deadline'].str.replace(' Jul','-07-2023' )
df['application_deadline'] = df['application_deadline'].str.replace(' Aug','-08-2023' )
df['application_deadline'] = pd.to_datetime(df['application_deadline'], format='mixed', dayfirst=True )
df['posted_since_days_ago'] = df['posted_since_days_ago'].astype('int')
df['posted_since_days_ago'] = pd.to_timedelta(df['posted_since_days_ago'], unit='D')
df['posting_date'] = pd.to_datetime('today') - df['posted_since_days_ago']
df['posting_date'] = df['posting_date'].dt.date
df['remaining_days'] = pd.to_datetime('today') - df['application_deadline']
df['remaining_days'] = abs(df['remaining_days'].dt.days)
df['number_of_job_offered'] = 1
df['posting_date'] = pd.to_datetime(df['posting_date'])
df_viz = df.pivot_table(index = 'job_location',
                        values = 'number_of_job_offered',
                        aggfunc = 'count')
df_viz.reset_index()


#end of data wranggling 

@app.route("/")
def index(): 
	
	card_data = f'{df_viz["number_of_job_offered"].count()}' #be careful with the " and ' 

	# generate plot
	ax = df_viz.sort_values(by= 'number_of_job_offered', ascending = False).plot(kind='bar', figsize = (20,9)) 
	
	# Rendering plot
	# Do not change this
	figfile = BytesIO()
	plt.savefig(figfile, format='png', transparent=True)
	figfile.seek(0)
	figdata_png = base64.b64encode(figfile.getvalue())
	plot_result = str(figdata_png)[2:-1]

	# render to html
	return render_template('index.html',
		card_data = card_data, 
		plot_result=plot_result
		)


if __name__ == "__main__": 
    app.run(debug=True)