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
st.cache(allow_output_mutation=True)
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
def get_table_download_link(df, titleString):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}" download="{titleString}.csv">Download {titleString} as CSV</a>'
    return href


recruits, teams, teamsList = getData()

#find the latest year of recruiting info
maxYear = int(recruits['year'].max())

#user input for date range
years = st.slider("Date Range", min_value=2010, max_value=maxYear, value=(2015, maxYear))

#user input for stars
stars = st.slider("Stars", min_value=1, max_value=5, value=(4, 5))

#user input for distance
distance = st.slider("Distance in Miles", min_value=0, max_value=1000, value=250, step=25)

#user input for recruit type
positionFilter = st.radio('Position Filter', ['All Recruits', 'By Position'])

#user inputs for position
if positionFilter == 'By Position':
    positions = st.multiselect('Position Select', ['QB', 'RB','WR', 'TE', 'OL', 'DT', 'DE', 'LB', 'CB', 'S', 'ATH'], default = ['QB'])


#user input for mapping
connectionFilter = st.radio('Connection Filter', [f'All Recruits within {str(distance)} Miles', 'Commits Only'])


#user input for team
schools = st.multiselect("Team", teamsList, default = ['USC','Nebraska','Texas','Alabama', 'Ohio State'])


#filter recruits dataframe to match user selections
recruits = recruits[recruits['year'].between(years[0],years[1])]
recruits = recruits[recruits['stars'].between(stars[0],stars[1])]

#filter positions by user selections
positionString = ''

if positionFilter == 'By Position':
    recruits = recruits[recruits['position'].isin(positions)]
    positionString = f" {', '.join(positions)}"

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
    
    
#save towns df's current state for later displayTable
townsTable = towns.copy(deep = True)


#set teams as index to make .locs easier
teams = teams.set_index('school')


#create and populate lists describing the number of commitss
commits = []
available = []

for school in schools:
    commits.append(towns[(towns['committedTo']==school) & (towns['school']==school)]['count'].sum())
    available.append(towns[towns['school']==school]['count'].sum())


#filter lines plotted based on connectionFilter
recruitString = 'Recruits'
if connectionFilter == 'Commits Only':
    towns = towns[towns['committedTo'] == towns['school']]
    recruitString = 'Commits'



#groupbys to reduce number of .applys called later
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
            opacity = .2,
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
        opacity = .25,#.2+ (recruits['count'] * .01),
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
    starString = 'Blue Chip'
else:
    stars = sorted(set(stars))
    starString = f"{' - '.join(str(x) for x in stars)} Star"

 
titleString =  f'{starString}{positionString} {recruitString}{distanceString}'
fontsize = 20
if len(titleString) > 50:
    fontsize = 15
    
#title and map layout
fig.update_layout(
    title_text = titleString,
    title_x=0.5,
    title_y=.76,
    font=dict(
        family='Arial',
        size=fontsize,
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
    
    schoolString = str(available[i])
    if connectionFilter == 'Commits Only':
        schoolString = str(commits[i])
    
    x = 1-((len(schools) - 1) * .112 + (.5 - (i * .224)))
    if len(schools) >= 7:
        x = 1-((len(schools) - 1) * .09 + (.5 - (i * .18)))
    
    fig.add_trace(go.Scattergeo(
        locationmode = 'USA-states',
        lon = [teams.loc[school]['lng']],
        lat = [teams.loc[school]['lat']],
        hoverinfo = 'text',
        text =  school + ' - ' + schoolString,
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
        viewOptions = [f'From how far away did all {starString.lower()} {positionString} {school}  commits come in {yearString}?', f'Where did {starString.lower()} {positionString} recruits within {distance} miles of {school} go in {yearString}?']
        view = st.radio('View', viewOptions, index = 0)
        
        try:
            
            if view == viewOptions[0]:
                
                titleString = f'{starString}{positionString} {school} Commits {yearString}'
                
                recruitsTable = recruitsTable[recruitsTable['committedTo'] == school]
                
                lat = teams.loc[school]['lat']
                lng = teams.loc[school]['lng']
                recruitsTable['distance'] = recruitsTable.apply(lambda row: int(great_circle(row['lng'], row['lat'], lng, lat)), axis = 1)
                
                color = teams.loc[school]['color']
                max = recruitsTable['distance'].max()
                hist = px.histogram(recruitsTable, x = 'distance', marginal = 'violin', color_discrete_sequence=[color], nbins = int(max / 100), template = 'simple_white', range_x = [0, max * 1.25])
                hist.update_xaxes(tick0=0).update_layout(font_family='Arial', font_size = 14)
                st.write(hist)
                
        
            elif view == viewOptions[1]:
                titleString = f'{starString}{positionString} {school} Recruits {distanceString} {yearString}'
                
                recruitsTable = townsTable
                towns = towns[towns['school'] == school]
                cityList = towns['city'].tolist()
                recruitsTable = recruitsTable[recruitsTable['city'].isin(cityList)]
    
                barTable = recruitsTable.groupby(['committedTo'], as_index=False).count()
                barTable = pd.merge(barTable,teamsTable,left_on='committedTo', right_on='school')
                barTable = barTable.sort_values(by='count',ascending=False).head(7)
                bar = px.bar(barTable, x = 'committedTo', y ='count', color = 'committedTo', color_discrete_sequence=barTable['color_y'].tolist(), template = 'simple_white').update_layout(showlegend=False,font_family='Arial', font_size = 12)
                st.write(bar)
              
              
              
            recruitsTable['distance'] = recruitsTable['distance'].astype(int)
            recruitsTable = recruitsTable.reindex(columns = ['year','name','committedTo','position','stars','city','distance'])
            recruitsTable = recruitsTable.sort_values(by = ['year','stars','city','committedTo'], ascending = [True,False,True,True]).reset_index(drop = True)
            
        except:
            st.write('No data available for this selection')
        
    else:
        recruitsTable = recruitsTable.reindex(columns = ['year','name','committedTo','position','stars','city'])
        recruitsTable['state'] = recruitsTable['city'].apply(lambda x: x[-2:])
        
        cityList = list(set(recruitsTable['city']))
        locationList = ['All Locations'] + sorted(list(set(recruitsTable['state']))) + sorted(list(set(recruitsTable['city'])))

        #user input for locations
        locationFilter = st.selectbox('Location', locationList)
        
        locationString = ''
        if locationFilter != locationList[0]:
            recruitsTable = recruitsTable[recruitsTable['city'] == locationFilter].append(recruitsTable[recruitsTable['state'] == locationFilter])
            locationString = f'from {locationFilter} '
 
        #user input for view
        viewOptions = [f'Where did {starString.lower()} {positionString} recruits {locationString}go in {yearString}?']
        view = st.radio('View', viewOptions, index = 0)
        
        titleString = f'{starString}{positionString} Recruits {locationString}{yearString}'
        
        barTable = recruitsTable.groupby(['committedTo'], as_index=False).count()
        barTable = pd.merge(barTable,teamsTable,left_on='committedTo', right_on='school')
        barTable['count'] = barTable['stars']
        barTable = barTable.sort_values(by='count',ascending=False).head(7)
        bar = px.bar(barTable, x = 'committedTo', y ='count', color = 'committedTo', color_discrete_sequence=barTable['color'].tolist(), template = 'simple_white').update_layout(showlegend=False,font_family='Arial', font_size = 12)
        st.write(bar)
         
    st.write(recruitsTable)
    
    st.markdown(get_table_download_link(recruitsTable, titleString), unsafe_allow_html=True)



#st.markdown('___')
st.markdown('Created by [Ben Davis](https://github.com/BenDavis71/)')
st.markdown('Map data from [SimpleMaps](https://simplemaps.com/data/us-cities)')
