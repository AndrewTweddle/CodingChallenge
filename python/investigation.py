# ===============================
# Load input data in JSon format:
import json

inputPath = 'data/input/'
listingData = [json.loads(line) for line in open(inputPath + 'listings.txt')]
productData = [json.loads(line) for line in open(inputPath + 'products.txt')]

# Convert input data into Pandas data frames:
from pandas import DataFrame, Series
import pandas as pd
import numpy as np

listings = DataFrame(listingData)
products = DataFrame(productData)

# ======================================================================
# Level 1 filtering: BY MANUFACTURER

# Get lists of unique manufacturers in the 2 files (for matching them up):
lManufs = np.sort(listings['manufacturer']).unique()
pManufs = np.sort(products['manufacturer']).unique()
    # Note: inspecting the above will give encoding errors if using an older versions of Pandas. Ensure you have version 0.11 or more recent.

lManufsSeries = Series(lManufs)

# ----------------------------------------------------------------------
# Data discoveries:
#   1. lManufs has far more manufacturers than pManufs, including some bad data which is clear a product not a manufacturer
#   2. Some aren't even camera products (e.g. UBISOFT Assassin's Creed). 
#   3. Others are, but aren't on main list of products e.g. listings[listings['manufacturer'] == u'Roots']
#   4. In some cases, the listing manufacturer is a subsidiary of the products manufacturer e.g. 'Canon Canada' under 'Canon'
#   5. At least one typo: 'Canoon' instead of 'Canon': listings[listings['manufacturer'] == u'Canoon']

# ----------------------------------------------------------------------
# Experiment with Levenshtein distances between various similar strings:
from nltk.metrics import *

s1 = 'Canon'
s2 = 'Canoon'
s3 = 'Cannon'
s4 = 'Cannoon'
s5 = 'Cannonn'
s_nikon = 'Nikon'

# Decide on a reasonable Levenshtein distance for matching manufacturer names:
edit_distance(s1, s2) # 1
edit_distance(s1, s3) # 1
edit_distance(s1, s4) # 2
edit_distance(s1, s5) # 2
edit_distance(s1, s_nikon) # 3

# test...
# min_manuf_word_len = 3
#test...
# edit_distance_threshold = 1

# Safest parameters:
edit_distance_threshold = 2
min_manuf_word_len = 4

# ----------------------------------------------------------------------
# Match lManufs to pManufs:
# 
# Precedence:
# 1. Exact match on entire string
# 2. Exact match on a single word in the string
# 3. Match contained in a single word in the string
# 4. Sufficiently small Levenshtein distance to a single word in the string
def matchManuf(lManuf):
    splits = lManuf.lower().split()
    for pManuf in pManufs:
        pManufLower = pManuf.lower()
        if pManufLower == lManuf.lower():
            return pManuf
        if pManufLower in splits:
            return pManuf
    foundPManufs = [ p for s in splits
                       for p in pManufs 
                       if s.find(p.lower()) >= 0
                   ]
    if len(foundPManufs) > 0:
        return foundPManufs[0]
    levenPManufs = [ p for s in splits
                       for p in pManufs 
                       if len(s) > min_manuf_word_len and edit_distance(s, p.lower()) <= edit_distance_threshold
                   ]
    if len(levenPManufs) > 0:
        return levenPManufs[0]
    return ''

mapData = { 'lManuf': lManufsSeries,
            'pManuf': lManufsSeries.apply( matchManuf )
          }
lManufMap = DataFrame( mapData )

#Possible mismatches:
def isPossibleMismatch(row):
    return row['pManuf'] != '' and (row['lManuf'].lower().find(row['pManuf'].lower()) == -1)

possibleMismatches = lManufMap.apply(isPossibleMismatch, axis=1)
# This trick was found at: 
#   http://stackoverflow.com/questions/13331698/how-to-apply-a-function-to-two-columns-of-pandas-dataframe
# An alternate approach would have been to modify matchManuf to also return the type of match, as described here: 
#   http://stackoverflow.com/questions/12356501/pandas-create-two-new-columns-in-a-dataframe-with-values-calculated-from-a-pre?rq=1

lManufMap[possibleMismatches]

                     # lManuf   pManuf
# 57               CANAL TOYS    Canon
# 76                   Canoon    Canon
# 86    Clip Sonic Technology     Sony
# 134                 Epsilon    Epson
# 242                   LESCA    Leica
# 253                   Leitz    Leica
# 254                   Lenco    Leica
# 292  Midland Consumer Radio    Casio
# 312                 OPYMPUS  Olympus
# 315                 Olmypus  Olympus
# 321                Olymypus  Olympus
# 378                 SAMYANG  Samsung
# 435      Syntax Corporation   Contax

# DECISION: Most of the above are mismatches. 
#           However the various olympus mappings and (possibly) canoon are correctly matched.
#           So rather allow all of these through and let the next layer of matching eliminate them.


# ----------------------------------------------------------------------
# Map to manufacturers

listingsByPManufAll = pd.merge( listings, lManufMap, how='inner', left_on='manufacturer', right_on='lManuf')
listingsByPManuf = listingsByPManufAll[listingsByPManufAll['pManuf'] != ''].reindex(columns = ['pManuf','lManuf', 'title','currency','price'])

# checking:
# listingsByPManuf[listingsByPManuf['pManuf'] != ''][9001:9050]
# listingsByPManuf[listingsByPManuf['lManuf'] == 'Olymypus']
# 
