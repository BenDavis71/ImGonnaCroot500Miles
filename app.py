#!/usr/bin/env python
# coding: utf-8


import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st




st.title('College Football Blue Chip Distance')
st.markdown('_Data courtesy of @CFB_Data_')


#read-in data that was collected from collegefootballdata.com
#cache this function so that streamlit doesn't rerun it everytime a user input is changed
@st.cache(allow_output_mutation=True)
def getData():
    #read in
    towns = pd.read_csv(r'https://raw.githubusercontent.com/BenDavis71/ImGonnaCroot500Miles/master/towns.csv') 
    teams = pd.read_csv('https://raw.githubusercontent.com/BenDavis71/ImGonnaCroot500Miles/master/teams-lat-long.csv', index_col='school')
    
    #create recruits df by modifying towns
    recruits = towns[['city','position','year','lat_x','lng_x','count']].groupby(['city','position','year','lat_x','lng_x'], as_index=False).sum()
    recruits['count'] = (recruits['count']  / 132).astype(int)
    
    #force the logo string to behave as a list
    teams['logos'] = teams['logos'].apply(lambda x: eval(x))

    #generate list of teams from dataframe
    teamsList = teams.index.tolist()
    return towns, recruits, teams, teamsList 


towns, recruits, teams, teamsList = getData()

#user input for date range
years = st.slider("Date Range", min_value=2015, max_value=2020, value=(2015, 2020))

#user input for distance
distance = st.slider("Distance", min_value=0, max_value=500, value=250, step=25)

#user input for recruit type
positionFilter = st.radio('Position Filter', ['All Recruits', 'By Position'])

#user inputs for position
if positionFilter == 'By Position':
    positions = st.multiselect('Position Select', ['QB', 'RB','WR', 'TE', 'OL', 'DT', 'DE', 'LB', 'CB', 'S', 'ATH'], default = ['QB'])


#user input for team
schools = st.multiselect("Team", teamsList, default = ['Stanford','Colorado','Texas','Alabama', 'Virginia Tech'])





#filter towns dataframe to match user selections
towns = towns[(towns['school'].isin(schools)) & (towns['distance'] <= distance)]
towns = towns[towns['year'].between(years[0],years[1])]



#filter positions by user selections
positionString = 'Recruits'

if positionFilter == 'By Position':
    recruits = recruits[recruits['position'].isin(positions)]
    towns = towns[towns['position'].isin(positions)]
    positionString = f"{', '.join(positions)} Recruits"


#groupbys to reduce dataframe size
recruits = recruits[['city','lat_x','lng_x','count']].groupby(['city','lat_x','lng_x'], as_index=False).sum()
towns = towns[['city','lat_x','lng_x','count','school','lat_y','lng_y','distance']].groupby(['city','lat_x','lng_x','school','lat_y','lng_y','distance'], as_index=False).sum()



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
            #opacity = .1,
            opacity = .15+ (towns['count'][i] * .01 /132),
            hoverinfo = None,
        )
    )


#recruits
fig.add_trace(go.Scattergeo(
    locationmode = 'USA-states',
    lon = recruits['lng_x'],
    lat = recruits['lat_x'],
    hoverinfo = 'text',
    text = recruits['city'] + " - " + recruits['count'].astype(str),
    mode = 'markers',
    marker = dict(
        size = 2 + (recruits['count'] * .15),
        color = 'rgb(55, 0, 233)',
        opacity = .2+ (recruits['count'] * .01),
        line = dict(
            width = 2,
            color = 'rgba(68, 68, 68, 0)'
        )
    )))



#title and map layout
fig.update_layout(
    title_text = f'Blue Chip {positionString} within {distance} Miles of Campus',
    title_x=0.5,
    title_y=.75,
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
        text= str(years[0]) + ' - ' + str(years[1]),
        xref="paper", yref="paper",
        x= .5, y= .75,
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
    
    count = towns[towns['school']==school]['count'].sum()
    
    #school
    color = [teams.loc[school]['color']]
    
    fig.add_trace(go.Scattergeo(
        locationmode = 'USA-states',
        lon = [teams.loc[school]['lng']],
        lat = [teams.loc[school]['lat']],
        hoverinfo = 'text',
        text =  school + ' - ' + count.astype(str),
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
            x= 1-((len(schools) - 1) * .1 + (.5 - (i * .2))) , y= .02,
            sizex=0.2, sizey=0.2,
            xanchor="center", yanchor="bottom"
        )
    )
    
    #reruit counts annotations
    fig.add_annotation(
        text=count.astype(str),
        xref="paper", yref="paper",
        x= 1-((len(schools) - 1) * .1 + (.5 - (i * .2))) , y= -.03,
        showarrow = False,
        xanchor="center", yanchor="bottom",
        font=dict(
            family="Arial",
            size=24,
        )
    )
    
    i+=1
    

    
st.write(fig)

st.markdown('___')
st.markdown('Created by [Ben Davis](https://github.com/BenDavis71/)')
st.markdown('Map data from [SimpleMaps](https://simplemaps.com/data/us-cities)')
