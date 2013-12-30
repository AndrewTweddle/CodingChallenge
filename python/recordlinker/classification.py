from abc import ABCMeta, abstractmethod
import itertools
import re

# --------------------------------------------------------------------------------------------------
# Class to represent the value function for matching a specific number of characters:
# 
class MatchValueFunction(object):
    def __init__(self, fixed_val, val_per_char):
        self.fixed_value = fixed_val
        self.value_per_char = val_per_char
    
    def evaluate(self, num_chars_matched):
        if num_chars_matched > 0:
            return self.fixed_value + num_chars_matched * self.value_per_char
        else:
            return 0.0

# --------------------------------------------------------------------------------------------------
# Matching rules for a given product to test whether a listing matches that product:
# 
class MatchingRule(object):
    @abstractmethod
    def try_match(self, product_desc, extra_prod_details = None):
        pass

class RegexMatchingRule(MatchingRule):
    def __init__(self, regex, value_on_desc, value_on_details, value_on_desc_per_char = 0, 
            value_on_details_per_char = 0, must_match_on_desc = False):
        self.match_regex = regex
        self.value_on_product_desc = value_on_desc
        self.value_on_extra_prod_details = value_on_details
        self.value_on_product_desc_per_char = value_on_desc_per_char
        self.value_on_extra_prod_details_per_char = value_on_details_per_char
        self.must_match_on_product_desc = must_match_on_desc  # this will be set for the primary match only
    
    def __try_match_text(self, text_to_match, value, value_per_char):
        match_obj = self.match_regex.search(text_to_match)
        if match_obj is None:
            return (False, 0)
        chars_matched = match_obj.end() - match_obj.start()
        return (True, value + value_per_char * chars_matched)
    
    def try_match(self, product_desc, extra_prod_details = None):
        is_matched, value = RegexMatchingRule.__try_match_text(
            self, product_desc, self.value_on_product_desc, self.value_on_product_desc_per_char)
        if not is_matched:
            if self.must_match_on_product_desc:
                return (False, 0)
            if self.value_on_extra_prod_details != 0 or self.value_on_extra_prod_details_per_char != 0:
                return RegexMatchingRule.__try_match_text(
                    self, extra_prod_details, self.value_on_extra_prod_details, self.value_on_extra_prod_details_per_char)
        return (is_matched, value)

class ListingMatcher(object):
    def __init__(self, description, primary_rule, secondary_rules):
        self.match_desc = description
        self.primary_matching_rule = primary_rule
        self.secondary_matching_rules = secondary_rules
    
    def try_match(self, product_desc, extra_prod_details):
        is_match, match_value = self.primary_matching_rule.try_match(product_desc, extra_prod_details)
        if is_match:
            for secondary_rule in self.secondary_matching_rules:
                is_match_2, match_value_2 = secondary_rule.try_match(product_desc, extra_prod_details)
                if is_match_2:
                    match_value = match_value + match_value_2
            return (is_match, match_value, self.match_desc)
        return (False, 0, '')

# --------------------------------------------------------------------------------------------------
# Matching engine to run through the ListingMatchers for a product, 
# and find the first one which applies to a particular listing:
class MatchingEngine(object):
    def try_match_listing(self, product_desc, extra_prod_details, listing_matchers):
        for matcher in listing_matchers:
            is_match, match_value, match_desc = matcher.try_match(product_desc, extra_prod_details)
            if is_match:
                return (is_match, match_value, match_desc)
        return (False, 0, '')


# --------------------------------------------------------------------------------------------------
# Templates to generate ListingMatchers and MatchItems:
# 

class RegexMatchingRuleTemplate(object):
    def __init__(self, slices, value_on_desc, value_on_details, value_on_desc_per_char, value_on_details_per_char, must_match_on_desc = False):
        self.slices = slices
        self.value_on_product_desc = value_on_desc
        self.value_on_extra_prod_details = value_on_details
        self.value_on_product_desc_per_char = value_on_desc_per_char
        self.value_on_extra_prod_details_per_char = value_on_details_per_char
        self.must_match_on_product_desc = must_match_on_desc
    
    @staticmethod
    def regex_escape_with_optional_dashes_and_whitespace(text):
        # Remove all white-space and dashes:
        escaped_text = re.sub('(\s|\-)+', '', text)
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
    
    def generate(self, all_blocks):
        block_gen = (all_blocks[s] for s in self.slices)
        extracted_blocks = itertools.chain.from_iterable(block_gen)
        extracted_text = ''.join(extracted_blocks)
        pattern = RegexMatchingRuleTemplate.regex_escape_with_optional_dashes_and_whitespace(extracted_text)
        regex = re.compile(pattern, flags = re.IGNORECASE or re.UNICODE )
        return RegexMatchingRule(regex, self.value_on_product_desc, self.value_on_extra_prod_details, 
            self.value_on_product_desc_per_char, self.value_on_extra_prod_details_per_char, self.must_match_on_product_desc)

class ListingMatcherTemplate(object):
    def __init__(self, desc, primary_template, secondary_templates):
        self.description = desc
        self.primary_rule_template = primary_template
        self.secondary_rule_templates = secondary_templates
    
    def generate(self, all_blocks):
        primary_rule = self.primary_rule_template.generate(all_blocks)
        secondary_rules = [template.generate(all_blocks) for template in self.secondary_rule_templates]
        listing_matcher = ListingMatcher(self.description, primary_rule, secondary_rules)
        return listing_matcher

class ListingMatchersBuilder(object):
    def __init__(self, matcher_templates):
        self.listing_matcher_templates = matcher_templates
    
    def generate_listing_matchers(self, all_blocks):
        return [matcher_template.generate(all_blocks) for matcher_template in self.listing_matcher_templates]
