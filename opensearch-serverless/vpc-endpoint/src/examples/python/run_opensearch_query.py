#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import argparse
import json
import uuid

import boto3

from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

SERVICE = 'aoss'

SAMPLE_KEYWORDS = [
  "bennett",
  "darabont",
  "don",
  "frank",
  "gordon",
  "levitt",
  "howard",
  "jon",
  "joseph",
  "miller",
  "moneyball",
  "redemption",
  "ron",
  "rush",
  "shawshank"
]

SAMPLE_DOCUMENTS = [
  { 
    "title": "Shawshank Redemption",
    "genre": "Drama",
    "director": "Frank Darabont",
    "year": 1994
  },
  { 
    "title": "Don Jon",
    "genre": "Comedy",
    "director": "Joseph Gordon-Levitt",
    "year": 2013
  },
  { 
    "title": "Rush",
    "genre": "Action",
    "directors": "Ron Howard",
    "year": 2013
  }
]

def _create_index(client, index_name):
  response = client.indices.create(index_name)
  print('\nCreating index:')
  print(response)


def _index_document(client, index_name):
  document = {
    'title': 'Moneyball',
    "genre": "Sport",
    'director': 'Bennett Miller',
    'year': '2011'
  }
  doc_id = uuid.uuid4().hex[:16]

  response = client.index(
    index = index_name,
    body = document,
    id = doc_id
  )
  print('\nAdding document:')
  print(response)


def _bulk_index_document(client, index_name):
  document_list = []
  for elem in SAMPLE_DOCUMENTS:
    index_meta = json.dumps({"index": {"_index": index_name, "_id": uuid.uuid4().hex[:16]}})
    doc = json.dumps(elem)

    document_list.append(index_meta)
    document_list.append(doc)

  docs = '\n'.join([e for e in document_list])
  print('\nDocuments:')
  print(docs)

  response = client.bulk(docs)
  print('\nAdding bulk documents:')
  print(response)


def _search(client, index_name, keyword, limit=5):
  query = {
    'size': limit,
    'query': {
      'multi_match': {
        'query': keyword,
        'fields': ['title^2', 'director']
      }
    }
  }

  response = client.search(
    body = query,
    index = index_name
  )
  print('\nSearch results:')
  print(response)


def _search_all(client, index_name, limit=5):
  query = {
    'size': limit,
    'query': {
      'match_all': {}
    },
    'track_total_hits': 'true'
  }

  response = client.search(
    body = query,
    index = index_name
  )
  print('\nSearch all documents:')
  print(response)


def main():
  parser = argparse.ArgumentParser()

  parser.add_argument('--profile', dest='profile', default='default', help='The name of a profile to use. If not given, then the default profile is used.')
  parser.add_argument('--host', default='us-east-1', help='Collection endpoint without https://. For example, 07tjusf2h91cunochc.us-east-1.aoss.amazonaws.com')
  parser.add_argument('--region', default='us-east-1', help='Region name, default is us-east-1')
  parser.add_argument('--index-name', dest='index_name', default='movies-index', help='Index name, default is movies-index')
  parser.add_argument('--create-index', action='store_true', help='Create index')
  parser.add_argument('--put-doc', action='store_true', help='Put a single document')
  parser.add_argument('--bulk-load', action='store_true', help='Upload documents')
  parser.add_argument('--search', action='store_true', help='Search for a document')
  parser.add_argument('--keyword', choices=SAMPLE_KEYWORDS, default=SAMPLE_KEYWORDS[0], help='Search keyword')
  parser.add_argument('--search-all', action='store_true', help='Retrieve all documents')
  parser.add_argument('--limit', type=int, default=5, help='The number of documents to be retrieved, default: 5')
  parser.add_argument('--dry-run', action='store_true')

  options = parser.parse_args()

  credentials = boto3.Session(region_name=options.region, profile_name=options.profile).get_credentials()

  awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, 
    options.region, SERVICE, session_token=credentials.token)

  client = OpenSearch(
    hosts = [{'host': options.host, 'port': 443}],
    http_auth = awsauth,
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection
  )

  if options.create_index:
    _create_index(client, options.index_name)

  if options.put_doc:
    _index_document(client, options.index_name)

  if options.bulk_load:
    _bulk_index_document(client, options.index_name)

  if options.search:
    _search(client, options.index_name, options.keyword, options.limit)

  if options.search_all:
    _search_all(client, options.index_name, options.limit)


if __name__ == '__main__':
  main()

