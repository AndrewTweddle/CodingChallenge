import os
import json
from pandas import DataFrame, Series
import pandas as pd

def load_results(json_file_path):
  lines = [json.loads(line) for line in open(json_file_path)]
  joins = [ { 'product_name': line['product_name'],
              'listing_manufacturer': listing['manufacturer'],
              'listing_title': listing['title']
            }
            for line in lines
            for listing in line['listings']
          ]
  return DataFrame(joins).reset_index()

def compare_with_entrant(entrant_folder_name):
  my_file = "../data/output/results.txt"
  mine = load_results(my_file)
  
  their_file = "../data/comparison/" + entrant_folder_name + "/results.txt"
  theirs = load_results(their_file)

  comparison = pd.merge(left=mine, right=theirs, how='outer', on=['product_name', 'listing_manufacturer', 'listing_title'], suffixes=['_mine','_theirs'])

  their_unique_matches = comparison[comparison['index_mine'].isnull()]
  my_unique_matches = comparison[comparison['index_theirs'].isnull()]
  
  their_unique_matches[['product_name', 'listing_manufacturer', 'listing_title']].to_csv("../data/comparison/" + entrant_folder_name + "/their_unique_listings.csv", encoding='utf-8')
  my_unique_matches[['product_name', 'listing_manufacturer', 'listing_title']].to_csv("../data/comparison/" + entrant_folder_name + "/my_unique_listings.csv", encoding='utf-8')

# Compare with other entrants:
compare_with_entrant('alex_black')

# Following doesn't work, as each json object doesn't fit on a single line...
# compare_with_entrant('aaron_levin')
