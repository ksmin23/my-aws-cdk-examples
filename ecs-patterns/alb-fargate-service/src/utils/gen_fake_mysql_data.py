#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import argparse
import os

import pandas as pd
from sqlalchemy import create_engine


DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_USER = os.environ.get('DB_USER', 'clusteradmin')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')


def insert_movies(data_dir, engine):
  movies = pd.read_csv(os.path.join(data_dir, 'movies.csv'), header=0)

  movies['title_only'] = movies['title'].str.extract('(.*?)\s*\(', expand=False)

  movies['movie_year'] = movies['title'].str.extract(r"\(([0-9]+)\)", expand=False)
  movies['movie_year'].fillna(0, inplace=True)
  movies = movies.astype({'movie_year': 'int32'})
  movies.drop(movies[movies.movie_year < 1000].index, inplace=True)

  movies['movie_genre_list'] = movies['genres'].apply(lambda x: x.split('|'))
  movies = movies.explode('movie_genre_list', ignore_index=True)
  movies['movie_genre_list'] = movies['movie_genre_list'].apply(lambda x: 'Unknown' if x == '(no genres listed)' else x)

  movies.drop(['title', 'genres'], axis=1, inplace=True)
  movies.rename(columns={'title_only': 'title', 'movie_genre_list': 'genre', 'movie_year': 'year'}, inplace=True)

  movies.to_sql('movies', con=engine, if_exists='append', index=False)


def insert_movie_ratings(data_dir, engine):
  ratings = pd.read_csv(os.path.join(data_dir, 'ratings.csv'), header=0)
  movie_ratings = ratings.groupby('movieId').agg({'movieId': 'size', 'rating': 'mean'}).rename(columns={'movieId': 'cnt', 'rating': 'avg_rating'})
  movie_ratings['avg_rating'] = movie_ratings['avg_rating'].apply(lambda x: round(x, 2))
  movie_ratings = movie_ratings.reset_index()

  movie_ratings.to_sql('movie_ratings', con=engine, if_exists='append', index=False)


def main():
  parser = argparse.ArgumentParser()

  parser.add_argument('--data-dir', action='store', default='ml-20m', help='movie lens data')
  parser.add_argument('--host', action='store', default=DB_HOST, help='database host')
  parser.add_argument('-u', '--user', action='store', default=DB_USER, help='user name')
  parser.add_argument('-p', '--password', action='store', default=DB_PASSWORD, help='password')
  parser.add_argument('--database', action='store', default='testdb',
    help='database name (default: testdb)')

  options = parser.parse_args()

  db_host, db_user, db_password = options.host, options.user, options.password
  database_endpoint_url = f'mysql+pymysql://{db_user}:{db_password}@{db_host}:3306/testdb'
  database_engine = create_engine(database_endpoint_url)

  insert_movies(options.data_dir, database_engine)
  insert_movie_ratings(options.data_dir, database_engine)


if __name__ == '__main__':
  main()
