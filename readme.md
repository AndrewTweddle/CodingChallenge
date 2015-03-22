# Overview

This is my entry for the [Sortable.com coding challenge](http://web.archive.org/web/20131005200452/http://sortable.com/blog/coding-challenge/).

The goal is to find matches between a master list of products and retailer product listings (despite the data being very dirty).
Accuracy of matches is very important as false matches are heavily penalized.

I was originally going to submit this code to Sortable in early 2014. However the Sortable technical team appears to have been down-sized in December 2013, at which time they stopped advertising for new developers. So there was no opportunity to apply to Sortable and possibly find out how well I'd done on the challenge.

Though Sortable was no longer hiring, I went ahead and finished off the challenge anyway. After all, it still provided:
* An interesting algorithmic and data munging challenge
* Python practice
* An opportunity to apply knowledge from reading the book ["Python for Data Analysis"](http://shop.oreilly.com/product/0636920023784.do) by Wes McKinney, which I'd recently purchased
* Learnings from comparing my results with other solutions uploaded to GitHub, such as from:
  * Alex Black, former CTO of Sortable.com - his [succinct Scala solution](https://github.com/alexblack/Sortable) uses the prices of cameras as [a matching criterion](https://github.com/alexblack/Sortable/blob/master/src/main/ProductMatchFilter.scala). (Disclaimer: I've assumed this is Alex's code, but as co-founder I doubt he would need to pass the test himself, so I wonder if this is really his code or someone else's who wished to submit anonymously)
  * Aaron Levin, former employee at Sortable.com - [his Python solution](https://github.com/aaronlevin/sortable) was good enough to earn him a position at Sortable.

Generally I think my algorithm compared quite well to these two. I've included the details of the comparison towards the end of this page.

UPDATE: [Sortable are hiring again](https://sortable.recruiterbox.com/jobs/fk0h6hk?referer=simply_hired&referrer=simplyhired&utm_source=simplyhired&utm_medium=jobclick). 
So I might get to submit my entry after all!

# Running the code

* Install the prerequisites:
  * Python 2.7.5
  * NumPy 1.7.1
  * SciPy 0.12.0
  * pandas 0.11.0
  * scikits-learn 0.13.1
  * nltk 2.0.4
* Clone the github repo, checking it out to a folder of your choice e.g. coding_challenge
* Navigate to the python sub-folder of the checkout folder in your CLI e.g. coding_challenge/python
* Run: python investigation.py
* Navigate to the data/output/ sub-folder e.g. coding_challenge/data/output/
* Analyze the results.txt file (each line is in json format)

# My approach

## Pandas for data munging

I used the Pandas library to perform data munging and interactive investigation. 
Pandas provides similar functionality to R's vectors and data frames, which I have used previously. 
So this was a natural choice, and also provided an opportunity to improve my Python skills.

## The interactive investigation script

The results of the investigations into the data can be found in the [investigation.py](https://github.com/AndrewTweddle/CodingChallenge/blob/master/python/investigation.py) script.
Successive discoveries and experiments are well documented in the script.

## A hierarchy of matching criteria

My main strategy was to use a numeric scale to create a hierarchy of different matching criteria.

Each matching rule would create a score based on the number of characters matched, thus favouring complete matches over partial matches.
The various rule classes are defined in [python/recorlinker/classification.py](https://github.com/AndrewTweddle/CodingChallenge/blob/master/python/recordlinker/classification.py):

The following classes are found in classification.py:
* `MatchValueFunction`
* `MatchResult`
* `MatchingRule`
  * `RegexMatchingRule`
* `ListingMatcher`
* `MatchingEngine`
* `MatchingRuleTemplate`
  * `RegexRuleBaseTemplate`
    * `RegexRuleTemplate`
    * `RegexRuleTemplateFollowedByAnyLetterOrSpecificLetters`
* `ListingMatcherTemplate`
* `MasterTemplate`

The `MatchValueFunction` class has a constructor taking the fixed value and a value per matched character as its 2 parameters.
The set of value functions is configured in the `BaseMasterTemplateBuilder` class in [python/recorlinker/builder.py](https://github.com/AndrewTweddle/CodingChallenge/blob/master/python/recordlinker/builder.py):

```Python
class BaseMasterTemplateBuilder(object):
    all_of_family_and_model_with_regex_desc = 'Family and model approximately'
    family_and_model_separately_with_regex_desc = 'Family and model separately and approximately'
    model_and_words_in_family_with_regex_desc = 'Model and words in family approximately'
    prod_code_having_alphas_around_dash_with_regex_desc = 'Prod code with alphas-dash-alphas space number approximately'
    prod_code_having_dash_with_regex_desc = 'Prod code with dash approximately'
    alt_prod_code_having_dash_with_regex_desc = 'Alternate prod code with dash approximately'
    prod_code_having_no_dash_with_regex_desc = 'Prod code without a dash approximately'
    all_of_family_and_alpha_model_with_regex_desc = 'Family and alpha model approximately'
    prod_code_followed_by_a_letter_or_specific_letters_with_regex_desc = 'Prod code excluding last character or IS'
    word_and_number_crossing_family_and_model_with_regex_desc = 'Word and number crossing family and model'
    
    all_of_family_and_model_with_regex_value_func_on_prod_desc = MatchValueFunction( 1000000000, 10000000)
    all_of_family_and_model_with_regex_value_func_on_prod_details = MatchValueFunction( 10000000, 100000)
    family_and_model_separately_with_regex_value_func_on_prod_desc = MatchValueFunction( 250000000, 2500000)  # NB: These will be added twice - once for family and once for model
    family_and_model_separately_with_regex_value_func_on_prod_details = MatchValueFunction( 2500000, 25000)  # NB: These will be added twice - once for family and once for model
    # model_and_words_in_family uses the value functions above for the model match, and the value functions below for each word match:
    family_word_with_regex_value_func_on_prod_desc = MatchValueFunction( 1000000, 10000)
    family_word_with_regex_value_func_on_prod_details = MatchValueFunction( 10000, 100)
    model_word_with_regex_value_func_on_prod_desc = MatchValueFunction( 10000000, 100000)
    model_word_with_regex_value_func_on_prod_details = MatchValueFunction( 100000, 1000)
    # prod code value functions:
    prod_code_having_dash_with_regex_value_func_on_prod_desc = MatchValueFunction( 300000000, 3000000)
    prod_code_having_dash_with_regex_value_func_on_prod_details = MatchValueFunction( 3000000, 30000)
    alt_prod_code_having_dash_with_regex_value_func_on_prod_desc = MatchValueFunction( 250000000, 2500000)
    alt_prod_code_having_dash_with_regex_value_func_on_prod_details = MatchValueFunction( 2500000, 25000)
    prod_code_having_alphas_around_dash_with_regex_value_func_on_prod_desc = MatchValueFunction( 200000000, 2000000)
    prod_code_having_alphas_around_dash_with_regex_value_func_on_prod_details = MatchValueFunction( 2000000, 20000)
    prod_code_having_no_dash_with_regex_value_func_on_prod_desc = MatchValueFunction( 100000000, 1000000)
    prod_code_having_no_dash_with_regex_value_func_on_prod_details = MatchValueFunction( 1000000, 10000)
    prod_code_followed_by_a_letter_or_specific_letters_with_regex_value_func_on_prod_desc = MatchValueFunction( 100000, 1000)
    prod_code_followed_by_a_letter_or_specific_letters_with_regex_value_func_on_prod_details = MatchValueFunction( 1000, 10)
    # Match values where model is 'a':
    all_of_family_and_alpha_model_with_regex_value_func_on_prod_desc = MatchValueFunction( 1000000, 10000)
    all_of_family_and_alpha_model_with_regex_value_func_on_prod_details = MatchValueFunction( 10000, 100)
    # Other match patterns:
    word_and_number_crossing_family_and_model_with_regex_value_func_on_prod_desc = MatchValueFunction( 100000, 1000)
    word_and_number_crossing_family_and_model_with_regex_value_func_on_prod_details = MatchValueFunction( 1000, 10)
```

The classes defined in builder.py are as follows:
* `BaseMasterTemplateBuilder`
  * `MasterTemplateBuilder`
  * `SingleMethodMasterTemplateBuilder` (used to unit test a single rule in isolation from the other rules in the hierarchy)

## Matching on product codes

A matching product code was particularly important, but this was complicated by issues such as:
* differing use of dashes, dots and spaces in otherwise identical codes
* extra characters appended to the product code (such as to indicate colour)
* specifications that look similar to product codes (e.g. X4 could be a 4 times zoom, not a product code)
* model names sometimes being found in the "family" field and sometimes in the "model" field of the listing
* some product listings are for add-on products (such as batteries or lenses) and the description also contains the product code of the camera which the add-on is for

### Ancillary information

To handle this last issue, step 3.1 looks for complete words such as "with" and "for" and their translations into other relevant languages.
All text after the first such word is moved into a field called "extraProdDetails".
Matches found in this field get a much lower score.

### Classification patterns

To handle the other variations, the model and family fields were each turned into a "classification pattern" and joined by a "+" symbol.
These classification patterns are defined in step 5.2:

```
# ----------------------------------------------------------------------
# 5.2 Categorize each block into one of the following:
#     x = An 'x' on its own (so that an "x4" zoom specification is not seen as a product code)
#     c = consonants only
#     a = alphabetic only
#     n = numeric only
#     _ = white space (1 or more i.e. \s+)
#     - = a dash only, since this is likely to be a common character in product codes
#     ~ = a dash preceded or succeeded by whitespace characters
#     ( = a left bracket, possibly with whitespace on either side
#     ) = a right bracket, possibly with whitespace on either side
#     ! = a division symbol (/), possibly with whitespace on either side
#         Note: an exclamation mark is used since this character can be part of a file name
#     . = a single dot (no white space)
#     # = any other non-alphanumeric sequences
```

In step 6.3 you can see the set of classification patterns discovered in the data:

```
# ----------------------------------------------------------------------
# All composite classifications after a refactoring to treat an 'x'
# followed by a digit (but not preceded by a dash) as 'xn' not 'an':
# 
# Pattern: +a              count: 2      example:  + Digilux
# Pattern: +a-a            count: 2      example:  + K-r
# Pattern: +a-a_n          count: 2      example:  + V-LUX 20
# Pattern: +a-an           count: 11     example:  + PDR-M60
# Pattern: +a-an!xn        count: 1      example:  + DSC-V100 / X100
# Pattern: +a-ana          count: 2      example:  + R-D1x
# Pattern: +a-n            count: 41     example:  + FE-5010
# Pattern: +a-n_a          count: 17     example:  + C-2000 Zoom
# Pattern: +a-n_c          count: 2      example:  + C-2500 L
# Pattern: +a-na           count: 21     example:  + QV-5000SX
# Pattern: +a-na_a_a       count: 1      example:  + EOS-1D Mark IV
# Pattern: +a_a-an         count: 4      example:  + PEN E-P2
# Pattern: +a_a-ana        count: 1      example:  + PEN E-PL1s
# Pattern: +a_a_n          count: 7      example:  + mju Tough 8010
# Pattern: +a_n            count: 7      example:  + mju 9010
# Pattern: +a_na           count: 1      example:  + mju 550WP
# Pattern: +a_xn           count: 1      example:  + Kiss X4
# Pattern: +an             count: 109    example:  + TL240
# Pattern: +an_a           count: 2      example:  + DC200 plus
# Pattern: +ana            count: 17     example:  + HZ15W
# Pattern: +c(an)          count: 1      example:  + GXR (A12)
# Pattern: +c_a            count: 1      example:  + N Digital
# Pattern: +c_a_a          count: 1      example:  + GR Digital III
# Pattern: +xn             count: 3      example:  + X70
# Pattern: +xn_c           count: 1      example:  + X560 WP
# Pattern: a+a             count: 2      example: Digilux + Zoom
# Pattern: a+a-an          count: 119    example: Exilim + EX-Z29
# Pattern: a+a-ana         count: 3      example: Cybershot + DSC-HX100v
# Pattern: a+a-n           count: 15     example: Alpha + NEX-3
# Pattern: a+a-n_c         count: 1      example: Optio + WG-1 GPS
# Pattern: a+a_a_xn        count: 1      example: EOS + Kiss Digital X3
# Pattern: a+a_an          count: 2      example: EasyShare + Mini M200
# Pattern: a+a_n           count: 5      example: Stylus + Tough 6000
# Pattern: a+a_n_a         count: 2      example: DiMAGE + EX 1500 Zoom
# Pattern: a+an            count: 158    example: Coolpix + S6100
# Pattern: a+an_a          count: 29     example: PowerShot + SD980 IS
# Pattern: a+an_a#         count: 1      example: ePhoto + CL30 Clik!
# Pattern: a+an_c          count: 2      example: PowerShot + SX220 HS
# Pattern: a+ana           count: 20     example: Finepix + Z900EXR
# Pattern: a+n             count: 35     example: FinePix + 1500
# Pattern: a+n.n           count: 1      example: Digilux + 4.3
# Pattern: a+n_a           count: 8      example: FinePix + 4700 Zoom
# Pattern: a+n_c           count: 7      example: IXUS + 310 HS
# Pattern: a+na            count: 15     example: Coolpix + 900S
# Pattern: a+xn            count: 1      example: FinePix + X100
# Pattern: a-a+a-an        count: 37     example: Cyber-shot + DSC-W310
# Pattern: a-a+a-ana       count: 5      example: Cyber-shot + DSC-HX7v
# Pattern: a-a+n           count: 1      example: D-LUX + 5
# Pattern: a_+an           count: 6      example: Cybershot  + W580
# Pattern: a_a+n_a         count: 8      example: Digital IXUS + 130 IS
# Pattern: a_a+n_c         count: 1      example: Digital IXUS + 1000 HS
``` 

### Running the rules engine

Steps 10.1 to 10.4 in investigation.py use classification.py and builder.py to run the rules engine on all combinations of listings and products.
This produces a short list of candidate listings per product, with a score for each match. 

Step 10.5 finds listings which match more than one product, and discusses the various anomalies found in the matches, along with possible actions to resolve these.

Step 10.6 finds the product with the highest valued match for each listing, along with investigations and resolution for further anomalies found.

## Extracting and matching on product specifications

Certain specifications of products can be extracted from the product listing.

For example, the following can all be specifications of the Megapixel rating of a camera:
* 10MP
* 10.1 MP
* 10 Megapixels
* 11 MPix
* 10 Mega-pixels
* 10 mega pixels

Step 11 of investigation.py attempts to extract the Megapixel rating from the product listing.
The product's MP specification is inferred if a threshold percentage of the listings have the same rating.
This is then used as an extra filtering criterion on candidate matches.

However certain anomalies with fractional MP ratings needed to be addressed:
* The rating was often rounded down to the nearest integer
* In Germany the rating appears to be rounded *up* (so a 10.1 MP camera is rounded to 11 MP)

A match to the next lower or *higher* integer was therefore considered a match.

This approach could easily be extended to filtering on other specifications (such as zoom factors on lenses).
However, since the majority of products were cameras, the cost-benefit ratio didn't justify doing this.

## Investigating unmatched listings

Step 12 of investigation.py investigates the reasons for products not being matched.

For example, some listings appended an extra character to the product code to indicate the colour of the product.
Other listings appended HD or IS to the product code to indicate features such as "high definition" or "image stabilized".

The `RegexRuleTemplateFollowedByAnyLetterOrSpecificLetters` class was added to produce low scoring matches on such product code patterns.


# Development environment

## OS used
Windows 7 Home Premium, SP1, 64 bit

## Libraries used:

pythonxy 2.7.5.0, including:
* NumPy 1.7.1
* SciPy 0.12.0
* pandas 0.11.0
* scikits-learn 0.13.1
* nltk 2.0.4
  * installed via `c:\python27\scripts\easy_install nltk`

## Folder structure

### Data files and folders

* data/
  * input/
    * products.txt    - a JSON file of products
    * listings.txt    - a JSON file of price listings (to be matched to products in products.txt)
  * intermediate/        - will be generated by the investigation script, provided it is run from the 'python' sub-folder
    * model_classifications/
      * contains product records grouped by the classification pattern of the 'model' field, 
      * with a csv file per pattern
    * composite_classifications/
      * classification patterns, as above, but for the composite family + model
  * output/
    * results.txt      - the JSON output file produced by my algorithm
  * comparison/        - sub-folders for the results file of other entrants to the challenge, along with details of the comparison
    * aaron_levin
    * alex_black

### Python scripts and folders

* python/                  - assumption: the current directory for running all Python scripts is the python folder
  * investigation.py    - a script built up incrementally with investigations into the problem (ipython used for REPL)
  * comparison.py       - a script used to compare my results files with those of other entrants
  * recordlinker/       - the Python module to perform the linking of products with listings

## Useful commands

### Run unit tests

`python -m recordlinker.test.classification_tests`

`python -m recordlinker.test.builder_tests`


# Evaluation of success

I compared my code and results against the challenge repos on GitHub of two ex-employees at Sortable, [Alex Black](https://github.com/alexblack/Sortable) and [Aaron Levin](https://github.com/aaronlevin/sortable).

First a disclaimer... I don't know if this really is Alex's code, since all the check-ins appear to be by a j2stinso.
I'll keep referring to it as Alex's.
But it's very likely someone else's code, since Alex was a co-founder of Sortable and presumably wouldn't need to pass the test himself!
I'd imagine that someone might not have wanted to use their own GitHub account in case their employer saw it.

My code was a lot more complex, covering a variety of edge cases, and was consequently less elegant.
I also didn't think of the trick of converting prices to a common currency and using price as a matching or filtering criterion.
However I am very happy with the level of accuracy that I managed to achieve.

The common and unique matches are shown below:

| Entrant /Host | Common matches | My unique matches | Their unique matches | Notes |
|---            |---             |---                |---                   |---    |
| Alex Black    | 2647           | 3295              | 25                   | Price was used as a filtering mechanism. Both sets of unique matches appear to be largely correct. |
| Aaron Levin   | 5609           | 333               | 842                  | A fair number of Aaron's unique matches appear to be incorrect. |

I've included csv files with the details of the unique matches found. These can be found in the sub-folders of 
[/data/comparison](https://github.com/AndrewTweddle/CodingChallenge/blob/master/data/comparison).

Note: Many listings had duplicate titles (though sometimes different prices and currencies).
So to perform the comparison, I first removed these duplicates, then did a full outer join between my results and a particular entrant's results.



# Future actions to consider

## Refactor investigation.py into separate files

investigation.py is almost 3 000 lines long (though many of these consist of data snippets and descriptions of issues encountered).

I had originally planned to refactor it into separate files and classes before submitting it.
However I decided not to do this after the Sortable challenge was discontinued. 

Additionally, the large script has the side-effect that the investigation and thought process behind my solution is more visible. It's effectively a log of my thought process!

## Write a Scala version

While Python and Pandas were both very enjoyable to program in, I missed the benefits of type safety.

[Although a nice side-effect of this was that I used TDD more than usual, as this helped to compensate for the extra guarantees provided by a statically typed language.]

Scala provides many of the benefits of a dynamic language, such as a succinct syntax and the interactivity of a REPL (if desired).
So I'm curious to see how a Scala port of the code would compare to the Python solution.

## Write a Spark version

As of Spark 1.3, there is [support for data frames](https://databricks.com/blog/2015/02/17/introducing-dataframes-in-spark-for-large-scale-data-science.html).

Since the existing Pandas solution uses data frames, this might make it easier to port (disclaimer: I haven't looked into Spark's data frames API to verify this).

Sure, it's overkill to use Spark for a problem of this size. But it would still be a useful learning exercise.
