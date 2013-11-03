# ===============================
# STEP 1: Load input data in JSon format:
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
# STEP 2: Level 1 filtering: BY MANUFACTURER

# 2.1 Get lists of unique manufacturers in the 2 files (for matching them up):
lManufs = np.sort(listings['manufacturer']).unique()
pManufs = np.sort(products['manufacturer']).unique()
    # Note: inspecting the above will give encoding errors if using an older versions of Pandas. Ensure you have version 0.11 or more recent.

lManufsSeries = Series(lManufs)
pManufsSeries = Series(pManufs)

# pManufsSeries:
# 0               Agfa
# 1              Canon
# 2              Casio
# 3             Contax
# 4              Epson
# 5           Fujifilm
# 6                 HP
# 7              Kodak
# 8     Konica Minolta
# 9            Kyocera
# 10             Leica
# 11             Nikon
# 12           Olympus
# 13         Panasonic
# 14            Pentax
# 15             Ricoh
# 16           Samsung
# 17             Sanyo
# 18             Sigma
# 19              Sony
# 20           Toshiba


# ----------------------------------------------------------------------
# Data discoveries:
#   1. lManufs has far more manufacturers than pManufs, including some bad data which is clear a product not a manufacturer
#   2. Some aren't even camera products (e.g. UBISOFT Assassin's Creed). 
#   3. Others are, but aren't on main list of products e.g. listings[listings['manufacturer'] == u'Roots']
#   4. In some cases, the listing manufacturer is a subsidiary of the products manufacturer e.g. 'Canon Canada' under 'Canon'
#   5. At least one typo: 'Canoon' instead of 'Canon': listings[listings['manufacturer'] == u'Canoon']
#   6. Product manufacturer gotchas to avoid:
#      6.1 Konica Minolta is two words, but it's simpler to match on single words rather than bigrams. 
#          So match on each word, not the combination. This will also catch cases where either word is used alone.
#      6.2 HP could also match Hewlett Packard. But that's two words. So match on "HP" or "Hewlett" or "Packard".
#      6.3 Fujifilm could also match Fuji or "Fuji film". So rather just match on "Fuji" not "Fujifilm"

# ----------------------------------------------------------------------
# 2.2 Generate and clean up manufacturer mappings in products data:
pManufsMapping = DataFrame( 
    { 'pManuf': pManufsSeries, 'Keyword': pManufsSeries.str.lower() } 
) # By default map each word to itself
pManufsMapping['Keyword'][pManufsMapping['pManuf'] == 'Konica Minolta'] = 'konica'
pManufsMapping = pManufsMapping.append( { 'pManuf': 'Konica Minolta', 'Keyword': 'minolta' }, ignore_index = True )
pManufsMapping = pManufsMapping.append( { 'pManuf': 'HP', 'Keyword': 'hewlett' }, ignore_index = True )
pManufsMapping = pManufsMapping.append( { 'pManuf': 'HP', 'Keyword': 'packard' }, ignore_index = True )
pManufsMapping['Keyword'][pManufsMapping['pManuf'] == 'Fujifilm'] = 'fuji'

pManufKeywords = pManufsMapping['Keyword']

# ----------------------------------------------------------------------
# 2.3 Experiment with Levenshtein distances between various similar strings:
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
# 2.4 Match lManufs to pManufs:
# 
# Precedence:
# 1. Exact match on entire string
# 2. Exact match on a single word in the string
# 3. Match contained in a single word in the string
# 4. Sufficiently small Levenshtein distance to a single word in the string
def matchManuf(lManuf):
    splits = lManuf.lower().split()
    for pManufKeyword in pManufKeywords:
        if pManufKeyword in splits:
            return pManufKeyword
    foundPManufs = [ p for s in splits
                       for p in pManufKeywords
                       if s.find(p.lower()) >= 0
                   ]
    if len(foundPManufs) > 0:
        return foundPManufs[0]
    levenshteinPManufs = [ p for s in splits
                             for p in pManufKeywords
                             if len(s) > min_manuf_word_len 
                             and edit_distance(s, p.lower()) <= edit_distance_threshold
                         ]
    if len(levenshteinPManufs) > 0:
        return levenshteinPManufs[0]
    return ''

mapData = { 'lManuf': lManufsSeries,
            'pManufKeyword': lManufsSeries.apply( matchManuf )
          }
lManufMap = DataFrame( mapData )
lManufMap = pd.merge( lManufMap, pManufsMapping, how='left', left_on='pManufKeyword', right_on='Keyword')
del lManufMap['Keyword']
lManufMap['pManuf'] = lManufMap['pManuf'].fillna('')
lManufMap

# ----------------------------------------------------------------------
# 2.5 Output intermediate data to check the accuracy of the manufacturer matching:
# 
#Possible mismatches:
def isPossibleMismatch(row):
    return row['pManuf'] != '' and (row['lManuf'].lower().find(row['pManuf'].lower()) == -1)

possibleMismatches = lManufMap.apply(isPossibleMismatch, axis=1)
# This trick was found at: 
#   http://stackoverflow.com/questions/13331698/how-to-apply-a-function-to-two-columns-of-pandas-dataframe
# An alternate approach would have been to modify matchManuf to also return the type of match, as described here: 
#   http://stackoverflow.com/questions/12356501/pandas-create-two-new-columns-in-a-dataframe-with-values-calculated-from-a-pre?rq=1

lManufMap[lManufMap['pManuf'] == ''].to_csv('data/intermediate/unmatched_manufs.csv', encoding='utf-8')
lManufMap[lManufMap['pManuf'] != ''].to_csv('data/intermediate/matched_manufs.csv', encoding='utf-8')
lManufMap[possibleMismatches].to_csv('data/intermediate/possible_mismatched_manufs.csv', encoding='utf-8')
# ASSUMPTION: using utf-8 encodings will be sufficient. 
# Note that Excel may show some less common letters as a "?". Nut in a text editor they are correct.

lManufMap[possibleMismatches]

#                           lManuf pManufKeyword          pManuf
# 428                   CANAL TOYS         canon           Canon
# 435                       Canoon         canon           Canon
# 439       Midland Consumer Radio         casio           Casio
# 440        Clip Sonic Technology        konica  Konica Minolta
# 441                       Konica        konica  Konica Minolta
# 447                      Epsilon         epson           Epson
# 451                         Fuji          fuji        Fujifilm
# 452                Fuji Film USA          fuji        Fujifilm
# 453                 Fuji FinePix          fuji        Fujifilm
# 454  Fuji Photo Film Europe GmbH          fuji        Fujifilm
# 455    Fuji Photo Film Usa, Inc.          fuji        Fujifilm
# 460              Hewlett Packard       hewlett              HP
# 461         Hewlett Packard GmbH       hewlett              HP
# 464                        LESCA         leica           Leica
# 466                        Leitz         leica           Leica
# 467                        Lenco         leica           Leica
# 469                      Minolta       minolta  Konica Minolta
# 475                      OPYMPUS       olympus         Olympus
# 476                      Olmypus       olympus         Olympus
# 482                     Olymypus       olympus         Olympus
# 498                      SAMYANG       samsung         Samsung
# 521           Syntax Corporation        contax          Contax

# DECISION: Quite a few of the above are mismatches. 
#           However the various olympus mappings and (possibly) canoon are correctly matched.
#           So rather allow all of these through and let the next layer of matching eliminate them.
#           
#           The alternative is to hard-code their elimination.
#           But rather avoid unnecessary customizations.

# DISCOVERIES:
# 1. Inspecting the 3 csv files showed up some anomalies.
#    This led to the new step 2.2 and subsequent refactorings.

# ----------------------------------------------------------------------
# 2.6 Map to manufacturers
# 

listingsByPManufAll = pd.merge( listings, lManufMap, how='inner', left_on='manufacturer', right_on='lManuf')
listingsByPManuf = listingsByPManufAll[listingsByPManufAll['pManuf'] != ''].reindex(columns = ['pManuf','lManuf', 'title','currency','price'])
listingsByPManuf.to_csv('data/intermediate/filtered_listings_by_pmanuf.csv', encoding='utf-8')


# ==============================================================================
# 3. Prepare the listings data for matching to products
# 

# ----------------------------------------------------------------------
# 3.1 Define terms that filter the product info from ancillary info
# 
import re
from string import Template

# Languages found by inspecting csv files: English, French, German...
applicabilitySplitTerms = [ u'for', u'pour', u'für', u'fur', u'fuer' ]
additionalSplitTerms = [ 'with',  'w/', 'avec', 'mit', '+' ]

applicabilityPatterns = '|'.join([ re.escape(term) for term in applicabilitySplitTerms ])
additionalPatterns = '|'.join([ re.escape(term) for term in additionalSplitTerms ])
allTermPatterns = applicabilityPatterns + '|' + additionalPatterns

patternToExpand = ur'''
^
\s*
(?P<productDesc>
  (?:
    (?!
      (?<!\w)
      (?:$allTermPatterns)
      (?!\w)
    )
    .
  )+
  # Ensure the last character is non-whitespace:
  (?:
    (?!
      (?<!\w)
      (?:$allTermPatterns)
      (?!\w)
    )
    \S
  )
)
\s*
(?:
  (?P<extraProdDetailsSection>
    (?:
      (?:$allTermPatterns)
      \W*
    )
    (?P<extraProdDetails>
      .+
      \S # Ensure the last character is non-whitespace:
    )
  )
  \s*
)?
$$
'''

patternTemplate = Template(patternToExpand)
titleSplitRegexPattern = patternTemplate.substitute(allTermPatterns=allTermPatterns)
titleSplitRegex = re.compile( titleSplitRegexPattern, re.IGNORECASE | re.UNICODE | re.VERBOSE )

#testing regex matches...
regexTestString = '   Nikon EN-EL9a 1080mAh Ultra High Capacity Li-ion Battery Pack   for Nikon D40, D40x, D60, D3000, & D5000 Digital SLR Cameras with love  for ever   with   salt and pepper'
testMatch = titleSplitRegex.match(regexTestString)
if testMatch:
  testMatch.group('productDesc')
  testMatch.group('extraProdDetails')
  # Discovery: Python provides no way to access all the captures for a named capture group if there is more than one (e.g. the text "for" is repeated)
  # Action: Simplify the regex to have a named captured group for extraProdDetails, instead of multiple ones

  
# ----------------------------------------------------------------------
# 3.2 Split the product titles into a product description and ancillary information
# 

def splitTitle(title):
    titleMatch = titleSplitRegex.match(title)
    return titleMatch.group('productDesc'), titleMatch.group('extraProdDetails')

title_regex_pairs = listingsByPManuf['title'].apply(splitTitle)
productDescs, extraProdDetails = zip(* title_regex_pairs )
listingsByPManuf['productDesc'] = productDescs
listingsByPManuf['extraProdDetails'] = extraProdDetails

listingsByPManuf.to_csv('data/intermediate/filtered_by_pmanuf_with_split_title.csv', encoding='utf-8')

# Check that the following give empty data frames:
# listingsByPManuf[pd.isnull(listingsByPManuf['productDesc'])]
# listingsByPManuf[listingsByPManuf['productDesc'] == '']

  
# ----------------------------------------------------------------------
# 3.3 Group by the product descriptions to reduce the amount of matching required
# 

productDescGrouping = listingsByPManuf.groupby(['pManuf', 'productDesc'])


# ==============================================================================
# 4. Prepare the products for matching to listings by finding duplicates:
# 

# ----------------------------------------------------------------------
# 4.1 Find duplicate models:
prod_model_counts = products.model.value_counts()
dup_models = prod_model_counts[prod_model_counts > 1]
#                     announced-date      family manufacturer   model
# 226  2011-02-15T19:00:00.000-05:00  Cybershot          Sony    T110
# 257  2009-02-16T19:00:00.000-05:00         NaN      Samsung   SL202
# 288  2011-02-15T19:00:00.000-05:00     FinePix     Fujifilm   S4000
# 370  2011-02-06T19:00:00.000-05:00        ELPH        Canon  300 HS
# 510  1998-11-01T19:00:00.000-05:00         NaN      Olympus   C900Z
# 517  1998-02-02T19:00:00.000-05:00     FinePix     Fujifilm     700
# 653  1999-04-15T20:00:00.000-04:00     PhotoPC        Epson     800
# 711  1998-03-15T19:00:00.000-05:00     Coolpix        Nikon     600
# 718  1999-02-14T19:00:00.000-05:00     Coolpix        Nikon     700
# 722  1996-05-12T20:00:00.000-04:00   PowerShot        Canon     600

# ------------------------------------------
# 4.2 Find duplicates by manufacturer and model:

products[products.duplicated(['manufacturer', 'model'])]
#                     announced-date family manufacturer   model
# 257  2009-02-16T19:00:00.000-05:00    NaN      Samsung   SL202
# 370  2011-02-06T19:00:00.000-05:00   ELPH        Canon  300 HS

# The problem with duplicated() is that it omits the first duplicate found.
# The following code allows us to examine the 'family' values for all records:
manuf_model_groups = products.groupby(['manufacturer', 'model'])
manuf_model_group_sizes = manuf_model_groups.size()
manuf_model_sizes = DataFrame({'group_count' : manuf_model_group_sizes}).reset_index()
manuf_model_dup_groups = manuf_model_sizes[manuf_model_sizes.group_count > 1]
manuf_model_dups = pd.merge(products, manuf_model_dup_groups, on=['manufacturer','model'], sort=True)[['manufacturer','family','model','announced-date']]
manuf_model_dups
#   manufacturer family   model                 announced-date
# 0        Canon   IXUS  300 HS  2010-05-10T20:00:00.000-04:00
# 1        Canon   ELPH  300 HS  2011-02-06T19:00:00.000-05:00
# 2      Samsung    NaN   SL202  2009-02-16T19:00:00.000-05:00
# 3      Samsung    NaN   SL202  2009-02-16T19:00:00.000-05:00


# ----------------------------------------------------------------------
# 4.3 Set the required matching action on the duplicates:
# 
# Note: A new text column named 'matchRule' will be added to the data frame.
#       Its value will guide the behaviour of the matching algorithm.
# 

# Ignore products which match on all 3 fields: manufacturer, family and model
manFamModel_dups = DataFrame({'isDup': products.duplicated(['manufacturer', 'family', 'model'])})
manFamModel_dups['matchRule'] = ''
manFamModel_dups.matchRule[manFamModel_dups.isDup] = 'ignore'

products['matchRule'] = manFamModel_dups.matchRule[manFamModel_dups.isDup]

# Match on family and model if the manufacturer and model are duplicated (but not the family):
manuf_model_groups = products[products.matchRule.isnull()].groupby(['manufacturer', 'model'])
manuf_model_group_sizes = manuf_model_groups.size()
manuf_model_sizes = DataFrame({'group_count' : manuf_model_group_sizes}).reset_index()  # reset_index() will copy the index into a column named 'index'
manuf_model_dup_groups = manuf_model_sizes[manuf_model_sizes.group_count > 1]

products2 = products.reset_index()  
    # products2 now has its index copied to a column named 'index'
    # This will be useful for matching up to the original index after the merge below...
manuf_model_dups = pd.merge(products2, manuf_model_dup_groups, on=['manufacturer','model'], sort=True).set_index('index')[['manufacturer','family','model']]
manuf_model_dups['matchRule'] = 'familyAndModel'
products = products.combine_first(manuf_model_dups[['matchRule']])  
    # Note: combine_first() is like a vectorized coalesce.
    #       It matches rows based on index.
    #       For each row and each column it takes the first non-null value
    #       in the two data frames (products and manuf_model_dups).

# test: products[products.matchRule.notnull()]


# ==============================================================================
# 5. Analyze the model column in the products data set in preparation 
#    for setting up rules for matching listings to products
# 

# ----------------------------------------------------------------------
# 5.1 Set up test regex for splitting the model into an array
#     of alphanumeric and non-alphanumeric sections
# 

regexTestString = ':::aaa-bb def   ghi   '

# Following regex pattern works to split with .Net, but not Python:
alphaNumSplitRegexPattern = r'(?<!^)\b'
alphaNumSplitRegex = re.compile( alphaNumSplitRegexPattern, re.IGNORECASE | re.UNICODE | re.VERBOSE )
alphaNumSplitRegex.split(regexTestString)

# This doesn't work either:
alphaNumSplitRegexPattern = '\b'
alphaNumSplitRegex = re.compile( alphaNumSplitRegexPattern, re.IGNORECASE | re.UNICODE | re.VERBOSE )
alphaNumSplitRegex.split(regexTestString)

# This also only works with .Net (\b seems to work differently)...
alphaNumRegexPattern = '(?:^|\b)(?:\w+|\W+)'
alphaNumRegex = re.compile( alphaNumRegexPattern, re.IGNORECASE | re.UNICODE | re.VERBOSE )
alphaNumRegex.findall(regexTestString)

# This works:
alphaNumRegexPattern = '(?:\w+|\W+)'
alphaNumRegex = re.compile( alphaNumRegexPattern, re.IGNORECASE | re.UNICODE | re.VERBOSE )
alphaNumRegex.findall(regexTestString)
alphaNumRegex.findall('aaa-bbb-ccc::ddd   ')
alphaNumRegex.findall('    aaa-bbb-ccc::ddd   ')

def split_into_blocks_by_alpha_num(stringToSplit):
    return alphaNumRegex.findall(stringToSplit)


# ----------------------------------------------------------------------
# 5.2 Categorize each block into one of the following:
#     a = alphabetic only
#     n = numeric only
#     w = alphanumeric, with both alphabetic and numeric characters
#     s = white space (1 or more i.e. \s+)
#     - = a dash (preceded or succeeded by zero or more whitespace characters),
#         since this is likely to be a common character in product codes.
#     x = any other non-alphanumeric sequences
#

# Use a list of tuples (instead of a dictionary) to control order of checking (dictionaries are unordered):
blockClassifications = [
        ('a', r'^[A-Za-z]+$'),
        ('n', r'^\d+$'),
        ('w', r'^\w+$'),
        ('s', r'^\s+$'),
        ('-', r'^\s*\-\s*$'),
        ('x', r'^.+$')
    ]
blockClassificationRegexes = [(classifier, re.compile(pattern, re.IGNORECASE | re.UNICODE | re.VERBOSE )) for (classifier,pattern) in blockClassifications]

def derive_classification(blockToClassify):
    for (classifier, regex) in blockClassificationRegexes:
        if regex.match(blockToClassify):
            return classifier
    return '?'

# Test classification function
# 
# Note: These should be moved into a unit test class 
#       when converting this exploratory script into an application
# 
def test_classification(blockToClassify, expected):
    classification = derive_classification(blockToClassify)
    if classification != expected:
        print '"{0}" classified as "{1}". But "{2}" expected!'.format(blockToClassify, classification, expected)

#Expect following to fail (test that test_classification works properly):
test_classification('abcd', 'test_failure')

# Expect these to succeed:
test_classification('abcd', 'a')
test_classification('1234', 'n')
test_classification('a12b', 'w')
test_classification(' \t ', 's')
test_classification('-', '-')
test_classification('   -  ', '-')
test_classification(':', 'x')
test_classification(':-)', 'x')
test_classification('', '?')


# ----------------------------------------------------------------------
# 5.3 Categorize a list of blocks into a 
#     single concatenated string of classifications:
#

def derive_classifications(blocksToClassify):
    block_classifications = [derive_classification(block) for block in blocksToClassify]
    return ''.join(block_classifications)

def test_derive_classifications(blocksToClassify, expected):
    classification = derive_classifications(blocksToClassify)
    if classification != expected:
        print '"{0}" classified as "{1}". But "{2}" expected!'.format(','.join(blocksToClassify), classification, expected)

# test that test_derive_classifications works by giving an incorrect expectation:
test_derive_classifications(['abc12','-','abc',':','12', '  ','IS'], 'test_failure')

# Expect these to succeed:
test_derive_classifications(['abc12','-','abc',':','12', '  ','IS'], 'w-axnsa')
test_derive_classifications(['  :  ','  -  ','12','.','1MP', '','IS'], 'x-nxw?a')
