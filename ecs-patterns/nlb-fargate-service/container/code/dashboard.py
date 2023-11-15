#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

from sqlalchemy import create_engine

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = int(os.environ.get('DB_PORT', '3306'))
DB_USER = os.environ.get('DB_USER', 'clusteradmin')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')

db_host, db_port, db_user, db_password = DB_HOST, DB_PORT, DB_USER, DB_PASSWORD
database_endpoint_url = f'mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/testdb'
database_engine = create_engine(database_endpoint_url)

query = '''SELECT genre, avg_rating
FROM movie_ratings AS t1, movies AS t2
WHERE t1.movieId = t2.movieId
GROUP BY genre
'''

genre_ratings = pd.read_sql(query, con=database_engine)

genre = genre_ratings['genre']
avg_rating = genre_ratings['avg_rating']

fig = plt.figure(figsize=(19, 10))

plt.bar(genre, avg_rating, color='maroon')
plt.xlabel('genre')
plt.ylabel('avg_rating')
plt.title('Matplotlib Bar Chart Showing the Average Rating of Movies in Each Genre')

st.pyplot(fig)

query = 'SELECT DISTINCT(genre) AS genre FROM movies'
genres = pd.read_sql(query, con=database_engine)
genre_list = genres['genre'].tolist()

query = 'SELECT DISTINCT(year) AS year FROM movies'
years = pd.read_sql(query, con=database_engine)
year_list = years['year'].tolist()

with st.sidebar:
  st.write("Select a range on the sidbar (it represents movie score) \
  to view the total number of movies in a genre that falls \
  within that range")

  # create a slider to hold user scores
  new_score_rating = st.slider(label="Choose a value:",
    min_value=1.0,
    max_value=5.0,
    value=(2.0, 3.0))

# create a multiselect widget to display genre
new_genre_list = st.multiselect('Choose Genre:',
  genre_list,
  default=[
    'Action',
    'Thriller',
    'Fantasy',
    'Romance'
  ]
)

year = st.selectbox('Choose a Year',
  year_list,
  0
)

new_genre_conditions = ','.join(['"%s"' % e for e in new_genre_list])

col1, col2 = st.columns([2, 3])
with col1:
  query = f'''SELECT title, genre, year
FROM movies
WHERE genre IN ({new_genre_conditions})
AND year = {year}
GROUP BY genre
'''

  genre_year = pd.read_sql(query, con=database_engine)
  genre_year = genre_year.astype({'year': str})

  st.write("""### Lists of movies filtered by year and genre""")
  st.dataframe(genre_year, width=400)


with col2:
  query = f'''SELECT genre, SUM(cnt) AS total
FROM movies AS t1, movie_ratings AS t2
WHERE t1.movieId = t2.movieId
AND (avg_rating >= {new_score_rating[0]} and avg_rating < {new_score_rating[1]})
AND genre in ({new_genre_conditions})
GROUP BY genre'''

  rating_count = pd.read_sql(query, con=database_engine)

  st.write("""### Total number of votes of movies and their genre""")
  figpx = px.line(rating_count, x='genre', y='total')
  st.plotly_chart(figpx)
