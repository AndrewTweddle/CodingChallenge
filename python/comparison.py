import os
import json
from pandas import DataFrame, Series
import pandas as pd

def load_results(json_file_path, new_line_offset):
  lines = [ json.loads(line[0:len(line) - new_line_offset]) # Filter out newline character at the end of each line
            for line in open(json_file_path, 'r') 
            if len(line) > 0  # Filter out possible final blank line
          ]
  joins = [ { 'product_name': line['product_name'],
              'listing_manufacturer': listing['manufacturer'],
              'listing_title': listing['title']
            }
            for line in lines
            for listing in line['listings']
          ]
  return DataFrame(joins).reset_index()

def compare_with_entrant(entrant_folder_name, new_line_offset):
  columns_to_compare = ['product_name', 'listing_manufacturer', 'listing_title']
  
  my_file = "../data/output/results.txt"
  mine = load_results(my_file, 0).drop_duplicates(columns_to_compare)
  
  their_file = "../data/comparison/" + entrant_folder_name + "/results.txt"
  theirs = load_results(their_file, new_line_offset).drop_duplicates(columns_to_compare)

  comparison = pd.merge(left=mine, right=theirs, how='outer', on=columns_to_compare, suffixes=['_mine','_theirs'])

  their_unique_matches = comparison[comparison['index_mine'].isnull()]
  my_unique_matches = comparison[comparison['index_theirs'].isnull()]
  
  common_match_count = len(comparison.index) - len(my_unique_matches) - len(their_unique_matches)
  
  print '|entrant | common matches | my unique matches | their unique matches |'
  print '|---|---|---|---|'
  print '|' + entrant_folder_name + ' | ' + str(common_match_count) + ' | ' + str(len(my_unique_matches)) + ' | ' + str(len(their_unique_matches)) + ' |'
  print
  
  their_unique_matches[['product_name', 'listing_manufacturer', 'listing_title']].to_csv("../data/comparison/" + entrant_folder_name + "/their_unique_listings.csv", encoding='utf-8')
  my_unique_matches[['product_name', 'listing_manufacturer', 'listing_title']].to_csv("../data/comparison/" + entrant_folder_name + "/my_unique_listings.csv", encoding='utf-8')

# Compare with other entrants:
compare_with_entrant('alex_black', 0)

# Aaron Levin's original results.txt file caused issues as each JSON object covered many lines. 
# Additionally there was an extra invalid double quote character next to the "title" field.
# This was first normalized to a single correct JSON object per line using the data/comparison/aaron_levin/normalize-json.ps1 Powershell script.
compare_with_entrant('aaron_levin', 1)
