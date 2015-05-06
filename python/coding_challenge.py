#!/usr/bin/python
# -*- coding: utf-8 -*-

# This is the main script for performing the matching of listings to products.
# It accepts 3 command line parameters: productsFilePath listingsFilePath outputFilePath
# 
# It is a cut-down and refactored version of investigation.py.
# investigation.py is an exploratory script and contains explanations, examples and tests.
# Refer to investigation.py to understand the thought processes that led to the algorithm.
# 
# pylint has been run on the file, however many warnings have been ignored.
# For example, there are many warnings about constant versus variable naming conventions.
# This can be fixed by moving most of the code into a function.
# However this will remove the ability to be able to run chunks of the code in a REPL,
# since the indentation level will be wrong.

import sys

# Get file paths from command line arguments:
if len(sys.argv) != 4:
    sys.stderr.write("Usage: python %s productsFilePath listingsFilePath outputFilePath" % sys.argv[0])
    raise SystemExit(1)

productsFilePath = sys.argv[1]
listingsFilePath = sys.argv[2]
outputFilePath = sys.argv[3]
# To test the code in a REPL, set suitable values for these 3 variables,
# then paste the following code into a REPL...

# ----------------------------------------------------------------------
# Required imports:
import os
import json
from pandas import DataFrame, Series
import pandas as pd
import numpy as np
from nltk.metrics import *
import re
from string import Template
from math import floor
from operator import truediv
import codecs

# Load listings into a data frame:
listingData = [json.loads(line) for line in open(listingsFilePath)]
listings = DataFrame(listingData).reset_index()
listings.rename(columns={'index': 'original_listing_index'}, inplace=True)

# Load products into a data frame:
def loadProductsAsDataFrame(productsFilePath):
    productData = [json.loads(line) for line in open(productsFilePath)]
    return DataFrame(productData)

products = loadProductsAsDataFrame(productsFilePath)

def getUniqueManufacturersFromDataFrame(dataFrame):
    df = np.sort(dataFrame['manufacturer']).unique()
    return Series(df)

lManufsSeries = getUniqueManufacturersFromDataFrame(listings)
pManufsSeries = getUniqueManufacturersFromDataFrame(products)


# ----------------------------------------------------------------------
# Generate and clean up manufacturer mappings in products data:
pManufsMapping = DataFrame( 
    { 'pManuf': pManufsSeries, 'Keyword': pManufsSeries.str.lower() }
)  # By default map each word to itself
pManufsMapping['Keyword'][pManufsMapping['pManuf'] == 'Konica Minolta'] = 'konica'
pManufsMapping = pManufsMapping.append( { 'pManuf': 'Konica Minolta', 'Keyword': 'minolta' }, ignore_index = True )
pManufsMapping = pManufsMapping.append( { 'pManuf': 'HP', 'Keyword': 'hewlett' }, ignore_index = True )
pManufsMapping = pManufsMapping.append( { 'pManuf': 'HP', 'Keyword': 'packard' }, ignore_index = True )
pManufsMapping['Keyword'][pManufsMapping['pManuf'] == 'Fujifilm'] = 'fuji'

pManufKeywords = pManufsMapping['Keyword']

# ----------------------------------------------------------------------
# Match lManufs to pManufs:
# 
# Precedence:
# 1. Exact match on entire string
# 2. Exact match on a single word in the string
# 3. Match contained in a single word in the string
# 4. Sufficiently small Levenshtein distance to a single word in the string
# 
def matchListingManufsToProductManufs(pManufsMapping, pManufKeywords):
    # Set suitable parameters for Levenshtein distances to 
    # map manufacturers in listings to similar manufacturers in products:
    edit_distance_threshold = 2
    min_manuf_word_len = 4
    
    def matchManuf(lManuf):
        splits = lManuf.lower().split()
        for pManufKeyword in pManufKeywords:
            if pManufKeyword in splits:
                return pManufKeyword
        foundPManufs = [ p
                         for s in splits
                         for p in pManufKeywords
                         if s.find(p.lower()) >= 0
                       ]
        if len(foundPManufs) > 0:
            return foundPManufs[0]
        levenshteinPManufs = [ p
                               for s in splits
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
    
    # ----------------------------------------------------------------------
    # Map to manufacturers
    # 
    listingsByPManufAll = pd.merge( listings, lManufMap, how='inner', left_on='manufacturer', right_on='lManuf')
    return listingsByPManufAll[listingsByPManufAll['pManuf'] != ''].reindex(
        columns = ['pManuf','lManuf', 'title','currency','price', 'original_listing_index'])

listingsByPManuf = matchListingManufsToProductManufs(pManufsMapping, pManufKeywords)

def separatePrimaryAndSecondaryProductInformation(listingsByPManuf):
    # ----------------------------------------------------------------------
    # Define terms that filter the product info from ancillary info
    #
    
    # Languages found by inspecting csv files: English, French, German...
    applicabilitySplitTerms = [ u'for', u'pour', u'für', u'fur', u'fuer' ]
    additionalSplitTerms = [ 'with',  'w/', 'avec', 'mit', '+' ]
    
    # Build up a regular expression to find terms for splitting 
    # the product information out from the product it is related to:
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
    
    # ----------------------------------------------------------------------
    # Split the product titles into a product description and ancillary information
    # 
    def splitTitle(title):
        titleMatch = titleSplitRegex.match(title)
        return titleMatch.group('productDesc'), titleMatch.group('extraProdDetails')

    title_regex_pairs = listingsByPManuf['title'].apply(splitTitle)
    productDescs, extraProdDetails = zip(* title_regex_pairs )
    listingsByPManuf['productDesc'] = productDescs
    listingsByPManuf['extraProdDetails'] = extraProdDetails

separatePrimaryAndSecondaryProductInformation(listingsByPManuf)

# ----------------------------------------------------------------------
# Set the required matching action on the duplicates:
# 
# Notes: 
#   1. A new copy of the input products data frame will be returned.
#      The calling code should assign this to the original variable passed in.
#   2. A new text column named 'matchRule' will be added to the data frame.
#       Its value will guide the behaviour of the matching algorithm.
# 
def markDuplicateProductsToBeIgnored(products):
    # Ignore products which match on all 3 fields: manufacturer, family and model
    manFamModel_dups = DataFrame({'isDup': products.duplicated(['manufacturer', 'family', 'model'])})
    manFamModel_dups['matchRule'] = ''
    manFamModel_dups.matchRule[manFamModel_dups.isDup] = 'ignore'
    products['matchRule'] = manFamModel_dups.matchRule[manFamModel_dups.isDup]

    # Match on family and model if the manufacturer and model are duplicated (but not the family):
    manuf_model_groups = products[products.matchRule.isnull()].groupby(['manufacturer', 'model'])
    manuf_model_group_sizes = manuf_model_groups.size()
    manuf_model_sizes = DataFrame({'group_count' : manuf_model_group_sizes}).reset_index()
        # reset_index() will copy the index into a column named 'index'
    manuf_model_dup_groups = manuf_model_sizes[manuf_model_sizes.group_count > 1]

    products2 = products.reset_index()  
        # products2 now has its index copied to a column named 'index'
        # This will be useful for matching up to the original index after the merge below...
    manuf_model_dups = pd.merge(
        products2, manuf_model_dup_groups, on=['manufacturer','model'], sort=True)\
        .set_index('index')[['manufacturer','family','model']]
    manuf_model_dups['matchRule'] = 'familyAndModel'
    products = products.combine_first(manuf_model_dups[['matchRule']])  
        # Note: combine_first() is like a vectorized coalesce.
        #       It matches rows based on index.
        #       For each row and each column it takes the first non-null value
        #       in the two data frames (products and manuf_model_dups).
    return products

products = markDuplicateProductsToBeIgnored(products)


# ----------------------------------------------------------------------
# Split the model and family columns into blocks of various types (alphabetic, numeric, other).
# Then convert the blocks into a code with a single character for each type of block:
# 
# The categorization code for each block will be one of the following:
#     x = An 'x' on its own (so that an "x4" zoom specification is not seen as a product code)
#     c = consonants only, since this is a stronger indicator of a product code than if there are vowels as well
#     a = alphabetic only
#     n = numeric only
#     _ = white space (1 or more i.e. \s+)
#     - = a dash only, since this is likely to be a common character in product codes
#     ~ = a dash preceded or succeeded by whitespace characters
#     ( = a left bracket, possibly with whitespace on either side
#     ) = a right bracket, possibly with whitespace on either side
#     ! = a division symbol (/), possibly with whitespace on either side
#         Note: an exclamation mark is used since this character can be part of a file name.
#               This is useful for debugging
#     . = a single dot (no white space)
#     # = any other non-alphanumeric sequences
#
def splitModelAndFamilyIntoBlocksAndDeriveAClassificationString(products):
    # ----------------------------------------------------------------------
    # Set up a regex for splitting the model into an array
    # of alphabetic, numeric and non-alphanumeric sections
    # 
    alphaNumRegexPattern = r'[A-Za-z]+|\d+|\W+'
    alphaNumRegex = re.compile( alphaNumRegexPattern, re.IGNORECASE | re.UNICODE | re.VERBOSE )
    def split_into_blocks_by_alpha_num(stringToSplit):
        return alphaNumRegex.findall(stringToSplit)
    
    # Use a list of tuples (instead of a dictionary) to control order of checking (dictionaries are unordered):
    blockClassifications = [
            ('x', r'^x$'), # An 'x' on its own. This is to avoid treating something like an "x4" zoom specification as a product code
            ('c', r'^[B-DF-HJ-NP-TV-XZb-df-hj-np-tv-xz]+$'),
            ('a', r'^[A-Za-z]+$'),
            ('n', r'^\d+$'),
            ('_', r'^\s+$'),
            ('-', r'^\-$'),
            ('~', r'^\s*\-\s*$'),  # Allow spaces on either side of the dash
            ('(', r'^\s*\(\s*$'),  # To cater for "GXR (A12)"
            (')', r'^\s*\)\s*$'),  # To cater for "GXR (A12)"
            ('!', r'^\s*\/\s*$'),  # To cater for "DSC-V100 / X100"
            ('.', r'^\.$'),        # To cater for "4.3"
            ('#', r'^.+$')         # An unknown character
        ]
        # A potential issue here is that the regex patterns assume ANSI characters.
        # However it seems that all the products listed are English, so this shouldn't matter.
        
    blockClassificationRegexes = [
        (classifier, re.compile(pattern, re.IGNORECASE | re.UNICODE | re.VERBOSE )) 
        for (classifier,pattern) in blockClassifications]
    
    def derive_classification(blockToClassify):
        for (classifier, regex) in blockClassificationRegexes:
            if regex.match(blockToClassify):
                return classifier
        return '$'
    
    # ----------------------------------------------------------------------
    # Categorize a list of blocks into a single concatenated string of classifications:
    #
    def derive_classifications(blocksToClassify):
        block_classifications = [derive_classification(block) for block in blocksToClassify]
        classification = ''.join(block_classifications)
        
        # Convert an 'x' back to a consonant block 'c' if it is:
        #   a. not succeeded by an 'n', or
        #   b. preceded by a dash
        classification = re.sub(r'x(?!n)', 'c', classification)
        classification = re.sub(r'(?<=\-)x', 'c', classification)
        
        # There is no need to differentiate consonant blocks from other alphabetic blocks 
        # if a dash or number precedes or succeeds the consonant block 
        # (since that already indicates a product code pattern)...
        classification = re.sub(r'(?<=\-|n)c', 'a', classification)
        classification = re.sub(r'c(?=\-|n)', 'a', classification)
        return classification
    
    # ----------------------------------------------------------------------
    # Convert a string into a list of tuples, where each tuple contains:
    # 1. A list of the various alphanumeric and non-alphanumeric blocks
    # 2. The classification string for the list of blocks
    #
    def get_blocks_and_classification_tuple(text_to_classify):
        blocks = split_into_blocks_by_alpha_num(text_to_classify)
        classification = derive_classifications(blocks)
        return blocks, classification
    
    # Derive and classify blocks in the model column:
    model_block_pairs = products['model'].apply(get_blocks_and_classification_tuple)
    model_blocks, model_classifications = zip(* model_block_pairs )
    products['model_blocks'] = model_blocks
    products['model_classification'] = model_classifications
    
    # Derive and classify blocks in the family column:
    family_block_pairs = products['family'].fillna('').apply(get_blocks_and_classification_tuple)
    family_blocks, family_classifications = zip(* family_block_pairs )
    products['family_blocks'] = family_blocks
    products['family_classification'] = family_classifications

splitModelAndFamilyIntoBlocksAndDeriveAClassificationString(products)


# ----------------------------------------------------------------------
# Create a composite classification of family and model, 
# consisting of both classifications separated by a plus sign (and spaces, for readability).
# The plus sign is included, since the strength of a match could be affected by whether 
# the classification pattern crosses the boundary of family and model.
# 
def createACompositeClassificationOfFamilyAndModel(products):
    products['family_and_model'] = products.family.fillna('') + ' + ' + products.model.fillna('')
    products['family_and_model_len'] = products.apply(lambda prd: len(prd['family_and_model']) - 3, axis = 1).astype(np.object)
        # i.e. include the length of family and model, but without the joining characters: ' + '
        # NB: Convert to object data type, otherwise we start getting errors like this: 
        # "ValueError: Shape of passed values is (743,), indices imply (743, 13)"
    products['composite_classification'] = products.family_classification + '+' + products.model_classification

    # Concatenate the family and model blocks (with a joining block so that slices match up):
    def get_composite_blocks(prod_row):
        family_blocks = prod_row['family_blocks']
        model_blocks = prod_row['model_blocks']
        blocks = list(family_blocks)
        blocks.append('+')
        blocks.extend(model_blocks)
        return blocks

    products['blocks'] = products.apply(get_composite_blocks, axis=1)

createACompositeClassificationOfFamilyAndModel(products)


# ==============================================================================
# Extract mega-pixel ratings as an extra criterion to match on.
# This can be used to resolve ambiguous matches.
# In particular, the Canon EOS 1-D cameras share the same product code
# and are differented by Mark number only.
def extractMegaPixelRatings(listingsByPManuf):
    mpPattern = r'(\d+(?:[.,]\d+)?)\s*(?:\-\s*)?(?:MP|MPixe?l?s?|(?:(?:mega?|mio\.?)(?:|\-|\s+)pix?e?l?s?))(?:$|\W)'
    
    def convert_mp_to_float(s):
        if isinstance(s, float):
            return s 
        else:
            return float(s.replace(',','.'))

    listingsByPManuf['resolution_in_MP'] \
        = listingsByPManuf.productDesc.str.findall(mpPattern, flags=re.IGNORECASE).str.get(0).apply(convert_mp_to_float)
    listingsByPManuf['rounded_MP'] \
        = listingsByPManuf.resolution_in_MP[listingsByPManuf.resolution_in_MP.notnull()].apply(lambda mp: floor(mp))

extractMegaPixelRatings(listingsByPManuf)


# --------------------------------------------------------------------------
# Find "exact" matches
# 
# These have all the alphanumeric characters from manufacturer (optional), family and model
# in sequence, but with optional whitespace and dashes between every pair of adjacent characters.
# 
# The purpose of getting exact matches, is to infer the most likely MegaPixel rating 
# of the product from the most common MegaPixel rating of these listings.
# 
def get_products_and_listings(products, listingsByPManuf):
    def regex_escape_with_optional_dashes_and_whitespace(text):
        # Remove all white-space and dashes:
        escaped_text = re.sub(r'(\s|\-)+', '', text)
        is_last_char_numeric = len(escaped_text) > 0 and escaped_text[-1].isdigit()
        # Insert a dash after every character.
        # Note: this is just a place-holder for where a regex will be inserted later.
        escaped_text = '-'.join(escaped_text)
        escaped_text = re.escape(escaped_text)
        # Replace the "\-" place-holder with a regex sequence matching whitespace characters and/or a single dash:
        escaped_text = re.sub(r'\\\-', r'\s*(?:\-\s*)?', escaped_text)
        # Do negative lookbehind to ensure this is not in the middle of a word:
        escaped_text = r'(?<!\w)' + escaped_text
        # Do negative lookahead:
        if is_last_char_numeric:
            # Don't match a final numeric character if it's followed by a decimal point (or comma) and a number.
            # This is to prevent issues like a "Casio Exilim EX-Z3 3.2MP Digital Camera" being a match for an "EX-Z33" model.
            escaped_text = escaped_text + r'(?!\w|\-|\.\d|\,\d)'
        else:
            escaped_text = escaped_text + r'(?!\w|\-)'
        return escaped_text
    
    def generate_exact_match_pattern(family, model):
        fam_and_model = family + model
        fam_and_model_pattern = regex_escape_with_optional_dashes_and_whitespace(fam_and_model)
        return fam_and_model_pattern
    
    def generate_exact_match_regex_and_pattern(products_row):
        'Assumption: null/na values in the family column have been converted to empty strings'
        family = products_row['family']
        model = products_row['model']
        pattern = generate_exact_match_pattern( family, model)
        regex = re.compile( pattern, flags = re.IGNORECASE or re.UNICODE )
        return regex, pattern
    
    regex_pattern_pairs = products.fillna({'family': ''}).apply(generate_exact_match_regex_and_pattern, axis=1)
    exact_match_regexes, exact_match_patterns = zip(* regex_pattern_pairs )
    
    products['exact_match_regex'] = exact_match_regexes
    products['exact_match_pattern'] = exact_match_patterns
    
    # Perform join between products and listings by product:
    products_to_match = products.reset_index()[['index', 'manufacturer', 'family', 'model', 'exact_match_regex']]
    listings_to_match_columns \
        = ['index', 'pManuf', 'productDesc', 'extraProdDetails', 'resolution_in_MP', 'rounded_MP', 'original_listing_index']
    listings_to_match = listingsByPManuf.reset_index()[listings_to_match_columns]
    
    return pd.merge(left=listings_to_match, right=products_to_match, \
        how='inner', left_on='pManuf', right_on='manufacturer', suffixes=('_l','_p'))

products_and_listings = get_products_and_listings(products, listingsByPManuf)

def get_exact_matches(products_and_listings):
    def is_exact_match(p_and_l_row):
        product_desc = p_and_l_row['productDesc']
        regex = p_and_l_row['exact_match_regex']
        return regex.search(product_desc) != None
    
    products_and_listings['is_exact_match'] = products_and_listings.apply(is_exact_match, axis=1)
    exact_match_columns = ['index_l', 'productDesc', 'resolution_in_MP', 
        'rounded_MP', 'index_p', 'manufacturer', 'family', 'model']
    exact_matches = products_and_listings[products_and_listings.is_exact_match][exact_match_columns]
    return exact_matches

exact_matches = get_exact_matches(products_and_listings)


# --------------------------------------------------------------------------
# Determine technical specification (resolution in MP) 
# for the product from the exact matches:
# 
def setProductResolutionFromExactMatches(products, exact_matches):
    # Arbitrary rule: 
    #     75% of listings must share the same resolution (megapixels) for it to become the product's resolution:
    THRESHOLD_PRODUCT_RESOLUTION_RATIO = 0.75
    
    def analyze_matches(grp):
        ind_p = grp.iloc[0]['index_p']
        vc = grp.rounded_MP.value_counts()
        unique_count = vc.count()
        
        if unique_count == 0:
            product_resolution = np.NaN
        else:
            total_count = vc.sum()
            most_common_count = vc.order(ascending=False).iget_value(0)
            
            if (unique_count > 0) and (truediv(most_common_count, total_count) >= THRESHOLD_PRODUCT_RESOLUTION_RATIO):
                product_resolution = vc.order(ascending=False).index[0]
            else:
                product_resolution = np.NaN
        return ind_p, unique_count, product_resolution
    
    exact_match_groups = exact_matches.groupby('index_p')
    product_resolution_tuples = exact_match_groups.apply(analyze_matches)
    ind_ps, product_resolution_unique_counts, product_resolutions = zip(* product_resolution_tuples )
    
    exact_match_df = DataFrame( 
        { 'resolution_in_MP_unique_count': product_resolution_unique_counts, 
          'product_resolution_in_MP': product_resolutions
        }, index = ind_ps)

    products = pd.merge(products, exact_match_df, how='outer', left_index=True, right_index=True)
    return products

products = setProductResolutionFromExactMatches(products, exact_matches)


# ==============================================================================
# Load matching engine and matching rule classes to calculate 
# highest value matches between products and listings:
#
from recordlinker.classification import *
from recordlinker.builder import *

unique_classifications = products.composite_classification.unique()


# ==============================================================================
# Use the matching engine and matching rule classes to calculate 
# highest value matches between products and listings:
#

# -----------------------------------------------------------------------------
# Generate a master template for each classification:
master_template_dict = {
    classification: MasterTemplateBuilder(classification).build() 
    for classification in unique_classifications 
}

# -----------------------------------------------------------------------------
# Generate a matching engine for each product:
# 
def generate_matching_engine(prod_row):
    classification = prod_row['composite_classification']
    blocks = prod_row['blocks']
    family_and_model_len = prod_row['family_and_model_len']
    master_template = master_template_dict[classification]
    engine = master_template.generate(blocks, family_and_model_len)
    return engine

products['matching_engine'] = products.apply(generate_matching_engine, axis=1)

# -----------------------------------------------------------------------------
# Add engine to each row of products_and_listings:
# 
# Note: Ideally this should be done when products_and_listings is created.
#       However we didn't have the matching engine classes then.
# 
products_and_listings = pd.merge(products_and_listings, \
    products[products.matchRule != 'ignore'][['matching_engine']], \
    left_on='index_p', right_index=True, how='inner')

# -----------------------------------------------------------------------------
# Run the matching engine for each product and listing combination:
# 
def run_matching_engine_for_all_products_and_listings(products_and_listings):
    def run_matching_engine(p_and_l_row):
        product_desc = p_and_l_row['productDesc']
        extra_prod_details = p_and_l_row['extraProdDetails']
        engine = p_and_l_row['matching_engine']
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        return match_result
        # Originally this was returning a tuple, but this didn't work.
        # Why not? This approach had worked fine elsewhere in the script...
        # return match_result.is_match, match_result.match_value, match_result.description

    match_results = products_and_listings.apply(run_matching_engine, axis=1)

    products_and_listings['match_result'] = match_results
    products_and_listings['match_result_is_match'] \
        = products_and_listings['match_result'].map(lambda mr: mr.is_match)
    products_and_listings['match_result_value'] \
        = products_and_listings['match_result'].map(lambda mr: mr.match_value)
    products_and_listings['match_result_description'] \
        = products_and_listings['match_result'].map(lambda mr: mr.description)

run_matching_engine_for_all_products_and_listings(products_and_listings)
matched_products_and_listings = products_and_listings[products_and_listings.match_result_is_match]

# -----------------------------------------------------------------------------
# Find product with highest match value for each listing:
# 
def get_highest_value_product_for_listing(listing_grp):
    by_val = listing_grp.sort_index(by='match_result_value', ascending=False)
    return by_val.iloc[0]

matches_grouped_by_listing = matched_products_and_listings.groupby('index_l')
best_matches = matches_grouped_by_listing.apply(get_highest_value_product_for_listing)

best_match_columns = ['index_p', 'manufacturer', 'family', 'model', 'productDesc', \
    'extraProdDetails', 'match_result_value', 'match_result_description']
best_match_sort_by = ['manufacturer', 'family', 'model', 'productDesc', 'extraProdDetails']

# ==============================================================================
# Estimate the Megapixel rating of each product and use this
# to filter out incorrect matches:
#

# -----------------------------------------------------------------------------
# Estimate the likely Megapixel rating of each product
# based on the Megapixel ratings of the highest valued matches:
# 
def get_products_and_listings_with_rounded_MP_of_best_value_match(best_matches, matched_products_and_listings):
    matches_grouped_by_product_mp_and_result_value = best_matches[
        best_matches.rounded_MP.notnull()].groupby(['index_p', 'rounded_MP', 'match_result_value'])
    matches_by_product_mp_and_result_value_with_counts \
        = DataFrame({'group_count' : matches_grouped_by_product_mp_and_result_value.size()}).reset_index()

    THRESHOLD_FOR_REJECTING_MPS_DUE_TO_DIVERSITY = 0.75

    def get_rounded_MP_of_best_value_match(grp_by_prod):
        by_val = grp_by_prod.sort_index(by=['match_result_value','group_count'], ascending=False)
        # Check that second best rounded_MP is the same, has lower value, or has significantly lower group_count.
        # Else make rounded_MP -1 to signal too much ambiguity.
        best_rounded_MP = by_val.iloc[0]['rounded_MP']
        if by_val['match_result_value'].count() > 1:
            best_match_result_value = by_val.iloc[0]['match_result_value']
            second_best_rounded_MP = by_val.iloc[1]['rounded_MP']
            second_best_match_result_value = by_val.iloc[1]['match_result_value']
            
            # Check for multiple top-rated mega-pixel ratings:
            if second_best_match_result_value == best_match_result_value:
                count_of_top_valued_MPs \
                    = by_val[by_val.match_result_value == best_match_result_value]['group_count'].count()
                if count_of_top_valued_MPs > 2 or abs(second_best_rounded_MP - best_rounded_MP) > 1:
                    number_of_top_valued_MPs \
                        = by_val[by_val.match_result_value == best_match_result_value]['group_count'].sum()
                    best_match_group_count = by_val.iloc[0]['group_count']
                    proportion_of_best_match = best_match_group_count / number_of_top_valued_MPs
                    if proportion_of_best_match < THRESHOLD_FOR_REJECTING_MPS_DUE_TO_DIVERSITY:
                        return -1
                        # There is too much ambiguity in the Megapixel ratings, 
                        # suggesting that something is wrong with the product record.
                        # So create an invalid MP rating to ensure that all matches (with MP ratings) are rejected.
        return best_rounded_MP

    matches_grouped_by_product = matches_by_product_mp_and_result_value_with_counts.groupby('index_p')
    best_rounded_MP_by_product = matches_grouped_by_product.apply(get_rounded_MP_of_best_value_match)
    best_rounded_MP_by_product_DF = DataFrame({'best_value_rounded_MP' : best_rounded_MP_by_product}).reset_index()
    return pd.merge(matched_products_and_listings, best_rounded_MP_by_product_DF, 
        left_on='index_p', right_on='index_p', how='left')

matched_products_and_listings \
    = get_products_and_listings_with_rounded_MP_of_best_value_match(best_matches, matched_products_and_listings)


# -----------------------------------------------------------------------------
# Calculate the highest valued product for each listing, 
# where the listing's rounded megapixel rating matches 
# the highest valued mega-pixel rating
#      
def get_best_matches_filtered_by_rounded_MP(matched_products_and_listings):
    def get_is_rounded_MP_matched(matched_prod_and_listing):
        rounded_MP = matched_prod_and_listing['rounded_MP']
        best_value_rounded_MP = matched_prod_and_listing['best_value_rounded_MP']
        return abs(rounded_MP - best_value_rounded_MP) <= 1

    are_both_MPS_set = pd.notnull(matched_products_and_listings[
        ['rounded_MP', 'best_value_rounded_MP']]).all(axis=1)
    matched_products_and_listings['is_highest_type_of_match'] = \
        matched_products_and_listings.match_result_description \
            == BaseMasterTemplateBuilder.all_of_family_and_model_with_regex_desc
    matched_products_and_listings['is_best_value_rounded_MP_matched'] \
        = matched_products_and_listings[are_both_MPS_set].apply(get_is_rounded_MP_matched, axis=1)
    matched_products_and_listings.is_best_value_rounded_MP_matched \
        = matched_products_and_listings.is_best_value_rounded_MP_matched.fillna(True)

    is_not_filtered_out = matched_products_and_listings[
        ['is_highest_type_of_match', 'is_best_value_rounded_MP_matched']].any(axis = 1)

    filtered_matched_products_and_listings = matched_products_and_listings[is_not_filtered_out]
    filtered_matches_grouped_by_listing = filtered_matched_products_and_listings.groupby('index_l')
    filtered_best_matches = filtered_matches_grouped_by_listing.apply(get_highest_value_product_for_listing)
    return filtered_best_matches

filtered_best_matches = get_best_matches_filtered_by_rounded_MP(matched_products_and_listings)


# -----------------------------------------------------------------------------
# Set matched product on all listings:
# 
def get_listings_with_matched_products(listingsByPManuf, filtered_best_matches):
    filtered_columns = ['index_p', 'index_l']
    filtered_prod_columns = ['family', 'model', 'manufacturer', 'product_name', 'announced-date']
    listings_with_matched_products = pd.merge( 
        listingsByPManuf, filtered_best_matches[filtered_columns], how='left', left_index=True, right_on='index_l')
    listings_with_matched_products = pd.merge( 
        listings_with_matched_products, products[filtered_prod_columns], how='left', left_on='index_p', right_index=True )
    return listings_with_matched_products

listings_with_matched_products = get_listings_with_matched_products(listingsByPManuf, filtered_best_matches)
    
# ==============================================================================
# Export the resulting matches as a json file:
#

# -----------------------------------------------------------------------------
# Generate result objects:
# 
def generate_result_objects(listings_with_matched_products):
    def generate_json_listings_for_product(prod_grp):
        original_listing_indices = prod_grp['original_listing_index'].values.tolist()
        listings = [listingData[oli] for oli in original_listing_indices]
        return listings

    listings_with_matched_products_by_product_name = listings_with_matched_products.groupby('product_name')
    listings_by_product_name = listings_with_matched_products_by_product_name.apply(generate_json_listings_for_product)
    listings_by_product_name_df = DataFrame({'listings' : listings_by_product_name})

    listings_by_all_product_names = pd.merge(
        products[['product_name']],
        listings_by_product_name_df,
        how='left',
        left_on='product_name',
        right_index=True
    ).sort_index(by='product_name')

    def generate_json_product_dict(row):
        product_name = row['product_name']
        listings = row['listings']
        if not (type(listings) is list):
            listings = []
        product_dict = {
            "product_name": product_name,
            "listings": listings
        }
        return json.dumps(product_dict, encoding='utf-8', ensure_ascii=False)

    results = listings_by_all_product_names.apply(generate_json_product_dict, axis=1).values.tolist()
    return results

results = generate_result_objects(listings_with_matched_products)

# -----------------------------------------------------------------------------
# Create output folder:
#
outputFolderPath = os.path.dirname(outputFilePath)

if outputFolderPath != "" and not os.path.exists(outputFolderPath):
    os.makedirs(outputFolderPath)

# -----------------------------------------------------------------------------
# Write result objects to a file:
#
results_file_contents = u'\n'.join(results)
results_file = codecs.open(outputFilePath, 'w', 'utf-8')

with results_file as f:
    f.write(results_file_contents)
