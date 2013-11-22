from abc import ABCMeta, abstractmethod

# --------------------------------------------------------------------------------------------------
# Matching rules for a given product to test whether a listing matches that product:
# 
class MatchingRule(object):
    @abstractmethod
    def try_match(self, product_desc, extra_prod_details = None):
        pass

class RegexMatchingRule(MatchingRule):
    def __init__(self, regex, value_on_desc, value_on_details, value_on_desc_per_char = 0, value_on_details_per_char = 0, must_match_on_desc = False):
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
        return (True, value + self.value_per_char * chars_matched)
    
    def try_match(self, product_desc, extra_prod_details = None):
        is_matched, value = __try_match_text(self, product_desc, self.value_on_product_desc, self.value_on_product_desc_per_char)
        if not is_matched:
            if self.must_match_on_product_desc:
                return (False, 0)
            if self.value_on_extra_prod_details != 0 or self.value_on_extra_prod_details_per_char != 0:
                return __try_match_text(self, extra_prod_details, self.value_on_extra_prod_details, self.value_on_extra_prod_details_per_char)
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
