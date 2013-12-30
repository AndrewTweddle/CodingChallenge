from abc import ABCMeta, abstractmethod
import itertools
import re

# --------------------------------------------------------------------------------------------------
# A class to represent the value function for matching a specific number of characters:
# 
class MatchValueFunction(object):
    def __init__(self, fixed_val, val_per_char):
        self.fixed_value = fixed_val
        self.value_per_char = val_per_char
    
    def is_assigned(self):
        return self.fixed_value <> 0 or self.value_per_char <> 0
    
    def evaluate(self, num_chars_matched):
        if num_chars_matched > 0:
            return self.fixed_value + num_chars_matched * self.value_per_char
        else:
            return 0.0

# --------------------------------------------------------------------------------------------------
# A class to represent the result of a matching attempt:
# 
class MatchResult(object):
    def __init__(self, is_matched, match_val = 0, desc = ""):
        self.is_match = is_matched
        self.match_value = match_val
        self.description = desc

# --------------------------------------------------------------------------------------------------
# Matching rules for a given product to test whether a listing matches that product:
# 
class MatchingRule(object):
    @abstractmethod
    def try_match(self, product_desc, extra_prod_details = None):
        pass

class RegexMatchingRule(MatchingRule):
    def __init__(self, regex, value_func_on_desc, value_func_on_details, must_match_on_desc = False):
        self.match_regex = regex
        self.value_func_on_product_desc = value_func_on_desc
        self.value_func_on_extra_prod_details = value_func_on_details
        self.must_match_on_product_desc = must_match_on_desc  # this will be set for the primary match only
    
    def __try_match_text(self, text_to_match, match_value_func):
        match_obj = self.match_regex.search(text_to_match)
        if match_obj is None:
            return MatchResult(False)
        chars_matched = match_obj.end() - match_obj.start()
        match_value = match_value_func.evaluate(chars_matched)
        return MatchResult(True, match_value)
    
    def try_match(self, product_desc, extra_prod_details = None):
        match_result = RegexMatchingRule.__try_match_text(
            self, product_desc, self.value_func_on_product_desc)
        if not match_result.is_match:
            if self.must_match_on_product_desc:
                return MatchResult(False)
            if self.value_func_on_extra_prod_details.is_assigned():
                return RegexMatchingRule.__try_match_text(
                    self, extra_prod_details, self.value_func_on_extra_prod_details)
        return match_result

class ListingMatcher(object):
    def __init__(self, description, primary_rule, secondary_rules):
        self.match_desc = description
        self.primary_matching_rule = primary_rule
        self.secondary_matching_rules = secondary_rules
    
    def try_match(self, product_desc, extra_prod_details):
        primary_match_result = self.primary_matching_rule.try_match(product_desc, extra_prod_details)
        if primary_match_result.is_match:
            primary_match_result.description = self.match_desc
            for secondary_rule in self.secondary_matching_rules:
                secondary_match_result = secondary_rule.try_match(product_desc, extra_prod_details)
                if secondary_match_result.is_match:
                    primary_match_result.match_value = primary_match_result.match_value + secondary_match_result.match_value
            return primary_match_result
        return MatchResult(False)

# --------------------------------------------------------------------------------------------------
# Matching engine to run through the ListingMatchers for a product, 
# and find the first one which applies to a particular listing:
class MatchingEngine(object):
    def try_match_listing(self, product_desc, extra_prod_details, listing_matchers):
        for matcher in listing_matchers:
            match_result = matcher.try_match(product_desc, extra_prod_details)
            if match_result.is_match:
                return match_result
        return MatchResult(False)


# --------------------------------------------------------------------------------------------------
# Templates to generate ListingMatchers and MatchItems:
# 

class RegexMatchingRuleTemplate(object):
    def __init__(self, slices, value_func_on_desc, value_func_on_details, must_match_on_desc = False):
        self.slices = slices
        self.value_func_on_product_desc = value_func_on_desc
        self.value_func_on_extra_prod_details = value_func_on_details
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
        return RegexMatchingRule(regex, self.value_func_on_product_desc,
            self.value_func_on_extra_prod_details, self.must_match_on_product_desc)

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
