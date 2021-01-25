#!/usr/bin/env python
# coding: utf-8


import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import base64
from math import radians, degrees, sin, cos, asin, acos, sqrt
import streamlit as st




st.title('College Football Recruiting Territories')
st.markdown('_Data courtesy of @CFB_Data_')


#read-in data that was collected from collegefootballdata.com
#cache this function so that streamlit doesn't rerun it everytime a user input is changed
@st.cache(allow_output_mutation=True)
def getData():
    #read in
    recruits = pd.read_csv(r'https://raw.githubusercontent.com/BenDavis71/ImGonnaCroot500Miles/master/recruits-lat-long.csv') 
    teams = pd.read_csv('https://raw.githubusercontent.com/BenDavis71/ImGonnaCroot500Miles/master/teams-lat-long.csv')#, index_col='school')
    
    #force the logo string to behave as a list
    teams['logos'] = teams['logos'].apply(lambda x: eval(x))

    #generate list of teams from dataframe
    teamsList = teams['school'].tolist()
    return recruits, teams, teamsList 


def great_circle(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    return 3958.756 * (
        acos(sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(lon1 - lon2))
    )
    

#download csv function from https://discuss.streamlit.io/t/how-to-download-file-in-streamlit/1806
def get_table_download_link(df, school, starsString, yearString):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}" download="{school} {starString}Recruits {yearString}.csv">Download {school} {starsString}Recruiting {yearString} as CSV</a>'
    return href


recruits, teams, teamsList = getData()

#user input for date range
years = st.slider("Date Range", min_value=2010, max_value=2020, value=(2015, 2020))

#user input for stars
stars = st.slider("Stars", min_value=1, max_value=5, value=(4, 5))

#user input for distance
distance = st.slider("Distance in Miles", min_value=0, max_value=500, value=250, step=25)

#user input for recruit type
positionFilter = st.radio('Position Filter', ['All Recruits', 'By Position'])

#user inputs for position
if positionFilter == 'By Position':
    positions = st.multiselect('Position Select', ['QB', 'RB','WR', 'TE', 'OL', 'DT', 'DE', 'LB', 'CB', 'S', 'ATH'], default = ['QB'])


#user input for team
schools = st.multiselect("Team", teamsList, default = ['USC','Nebraska','Texas','Alabama', 'Ohio State'])


#filter recruits dataframe to match user selections
recruits = recruits[recruits['year'].between(years[0],years[1])]
recruits = recruits[recruits['stars'].between(stars[0],stars[1])]

#filter positions by user selections
positionString = 'Recruits'

if positionFilter == 'By Position':
    recruits = recruits[recruits['position'].isin(positions)]
    positionString = f"{', '.join(positions)} Recruits"

#save recruits and teams df's current state for later displayTable
recruitsTable = recruits.copy(deep = True)
teamsTable = teams.copy(deep = True)

#groupbys to reduce dataframe size
teams = teams[teams['school'].isin(schools)]

recruits['merge'] = 1
teams['merge'] = 1
towns = pd.merge(recruits,teams,on='merge')





distanceString =  ''
if len(schools) > 0:
    towns['distance'] = towns.apply(lambda row: great_circle(row['lng_x'], row['lat_x'], row['lng_y'], row['lat_y']), axis = 1)
    towns = towns[towns['distance'] <= distance]
    distanceString =  f' within {distance} Miles of Campus'
else:
    towns = towns[:2]
    distanceString
    #convert user inputs to sets & strings (accounting for potential of single year selections)

#save towns df's current state for later displayTable
townsTable = towns.copy(deep = True)


teams = teams.set_index('school')


commits = []
available = []

for school in schools:
    commits.append(towns[(towns['committedTo']==school) & (towns['school']==school)]['count'].sum())
    available.append(towns[towns['school']==school]['count'].sum())

try:
    towns = towns[['city','lat_x','lng_x','count','school','lat_y','lng_y','distance']].groupby(['city','lat_x','lng_x','school','lat_y','lng_y','distance'], as_index=False).sum()
except:
    towns = towns[['city','lat_x','lng_x','count','school','lat_y','lng_y']].groupby(['city','lat_x','lng_x','school','lat_y','lng_y',], as_index=False).sum()
recruits = recruits[['city','lat','lng','count']].groupby(['city','lat','lng'], as_index=False).sum()




fig = go.Figure()


#lines
for i in range(len(towns)):
    school = towns['school'][i]
    fig.add_trace(
        go.Scattergeo(
            locationmode = 'USA-states',
            lon = [towns['lng_x'][i], towns['lng_y'][i]],
            lat = [towns['lat_x'][i], towns['lat_y'][i]],
            mode = 'lines',
            line = dict(width = 1.5,color = teams.loc[school]['color']),
            opacity = .11,
            #opacity = .15+ (towns['count'][i] * .01 /132),
            hoverinfo = None,
        )
    )


#recruits
fig.add_trace(go.Scattergeo(
    locationmode = 'USA-states',
    lon = recruits['lng'],
    lat = recruits['lat'],
    hoverinfo = 'text',
    text = recruits['city'] + " - " + recruits['count'].astype(str),
    mode = 'markers',
    marker = dict(
        size = 2 + (recruits['count'] * .075),
        color = 'rgb(55, 0, 233)',
        opacity = .2,#.2+ (recruits['count'] * .01),
        line = dict(
            width = 2,
            color = 'rgba(68, 68, 68, 0)'
        )
    )))



years = sorted(set(years))
yearString = " - ".join(str(x) for x in years)


if (stars[0] == 1) & (stars[1] == 5):
    starString = ''
elif (stars[0] == 4) & (stars[1] == 5):
    starString = 'Blue Chip '
else:
    stars = sorted(set(stars))
    starString = f"{' - '.join(str(x) for x in stars)} Star "



#title and map layout
fig.update_layout(
    title_text = f'{starString}{positionString}{distanceString}',
    title_x=0.5,
    title_y=.76,
    font=dict(
        family='Arial',
        size=20,
    ),
    showlegend = False,
    geo = go.layout.Geo(
        scope = 'usa',   
        showland = True,
        landcolor = 'rgb(235, 235, 240)'

    ),
    height=700,
 
)


#subtitle
fig.add_annotation(
        text= yearString,
        xref="paper", yref="paper",
        x= .49, y= .77,
        showarrow = False,
        xanchor="center", yanchor="bottom",
        font=dict(
            family="Arial",
            size=20,
        )
    )


#add school info and logos with for loop
i = 0


for school in schools:
    #school
    color = [teams.loc[school]['color']]
    
    x = 1-((len(schools) - 1) * .112 + (.5 - (i * .224)))
    if len(schools) >= 7:
        x = 1-((len(schools) - 1) * .09 + (.5 - (i * .18)))
    
    fig.add_trace(go.Scattergeo(
        locationmode = 'USA-states',
        lon = [teams.loc[school]['lng']],
        lat = [teams.loc[school]['lat']],
        hoverinfo = 'text',
        text =  school + ' - ' + str(available[i]),
        mode = 'markers',
        marker = dict(
            size = 6,
            color = color,
            opacity = .8,
            line = dict(
                width = 3,
                color = color
            )
        )))

    #logos
    logo = teams.loc[school]['logos'][0]
    
    fig.add_layout_image(
        dict(
            source=logo,
            xref="paper", yref="paper",
            x= x , y= .02,
            sizex=0.2, sizey=0.2,
            xanchor="center", yanchor="bottom"
        )
    )
    
    #reruit counts annotations
    fig.add_annotation(
        text= str(commits[i]) + "/" + str(available[i]),
        xref="paper", yref="paper",
        x= x , y= -.03,
        showarrow = False,
        xanchor="center", yanchor="bottom",
        font=dict(
            family="Arial",
            size=24,
        )
    )
    

    #add something that measures len difference between CMT # and AVBL and adjusts
    fig.add_annotation(
        text="<b>CMT / AVBL</b>",
        xref="paper", yref="paper",
        x= .005 + x, y= -.06,
        showarrow = False,
        xanchor="center", yanchor="bottom",
        font=dict(
            family="Arial",
            size=12,
        )
    )
    
    
    i+=1
    
st.write(fig)


moreDetails = st.beta_expander('More Details')
with moreDetails:
    

    #avoid errors on cases where no team is selected
    if len(schools) > 0:
        
        #user input for team
        school = st.selectbox("Team", schools)

        #user input for view
        viewOptions = [f'How far did all {starString.lower()} {positionString.lower()} that went to {school} in {yearString} come?', f'Where did {starString.lower()} {positionString.lower()} within {distance} miles of {school} in {yearString} go to?']
        view = st.radio('View', viewOptions, index = 0)
        
        try:
            
            if view == viewOptions[0]:
                recruitsTable = recruitsTable[recruitsTable['committedTo'] == school]
                
                lat = teams.loc[school]['lat']
                lng = teams.loc[school]['lng']
                recruitsTable['distance'] = recruitsTable.apply(lambda row: great_circle(row['lng'], row['lat'], lng, lat), axis = 1)
                
                color = teams.loc[school]['color']
                max = recruitsTable['distance'].max()
                hist = px.histogram(recruitsTable, x = 'distance', marginal = 'violin', color_discrete_sequence=[color], nbins = int(max / 100), template = 'simple_white', range_x = [0, max * 1.5])
                hist.update_xaxes(tick0=0)
                st.write(hist)
                
        
            else:
                recruitsTable = townsTable
                towns = towns[towns['school'] == school]
                cityList = towns['city'].tolist()
                recruitsTable = recruitsTable[recruitsTable['city'].isin(cityList)]
    
                barTable = recruitsTable.groupby(['committedTo'], as_index=False).count()
                barTable = pd.merge(barTable,teamsTable,left_on='committedTo', right_on='school')
                barTable = barTable.sort_values(by='count',ascending=False).head(7)
                bar = px.bar(barTable, x = 'committedTo', y ='count', color = 'committedTo', color_discrete_sequence=barTable['color_y'].tolist(), template = 'simple_white').update_layout(showlegend=False)
                st.write(bar)
              
              
              
            recruitsTable['distance'] = recruitsTable['distance'].astype(int)
            recruitsTable = recruitsTable.reindex(columns = ['year','name','committedTo','position','stars','city','distance'])
            recruitsTable = recruitsTable.sort_values(by = ['year','stars','city','committedTo'], ascending = [True,False,True,True]).reset_index(drop = True)
            
        except:
            st.write('No data available for this selection')
        
    else:
        recruitsTable = recruitsTable.reindex(columns = ['year','name','committedTo','position','stars','city'])
         
    st.write(recruitsTable)
    
    #handle exceptions for when no teams are selected
    st.markdown(get_table_download_link(recruits, school, starString, yearString), unsafe_allow_html=True)


#handle no team listed exceptions
#figure out what to do when title is too big (maybe use len() to move down font size?)
#maybe change colors depending on commit or not 
#fix capitalization of options filter for positions
#st.markdown('___')
st.markdown('Created by [Ben Davis](https://github.com/BenDavis71/)')
st.markdown('Map data from [SimpleMaps](https://simplemaps.com/data/us-cities)')
