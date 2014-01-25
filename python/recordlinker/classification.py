from abc import ABCMeta, abstractmethod
import itertools
import re
# from pdb import set_trace

# --------------------------------------------------------------------------------------------------
# A class to represent the value function for matching a specific number of characters:
# 
class MatchValueFunction(object):
    def __init__(self, fixed_val, val_per_char):
        self.fixed_value = fixed_val
        self.value_per_char = val_per_char
    
    def is_assigned(self):
        return self.fixed_value <> 0 or self.value_per_char <> 0
    
    def evaluate(self, num_chars_matched, family_and_model_len, is_after_sep):
        if num_chars_matched > 0:
            if is_after_sep:
                return self.fixed_value + num_chars_matched * self.value_per_char - family_and_model_len
            else:
                return 10 * (self.fixed_value + num_chars_matched * self.value_per_char) - family_and_model_len
                # Some listings show multiple alternate product codes (e.g. Canon EOS 550D = Rebel T2i = Kiss X4)
                # These other product codes are usually shown in brackets or separated by slashes.
                # To encourage the algorithm to choose the product shown first in the listing,
                # multiply the value of the match by 10 if there is no separator or if it comes before the separator
        else:
            return 0.0
        # Subtract the length of the family and model to encourage 
        # matching to the shortest applicable product when there are ties.
        # Unfortunately, when there are multiple matching rules, the subtraction will occur multiple times.
        # But since this is only applicable as a tie-breaker, it shouldn't matter.

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

# --------------------------------------------------------------------------------------------------
# A match rule class which uses a regular expression to test for a match:
# 
class RegexMatchingRule(MatchingRule):
    def __init__(self, regex, fam_and_model_len, value_func_on_desc, value_func_on_details, must_match_on_desc = False):
        self.family_and_model_len = fam_and_model_len
        self.match_regex = regex
        self.value_func_on_product_desc = value_func_on_desc
        self.value_func_on_extra_prod_details = value_func_on_details
        self.must_match_on_product_desc = must_match_on_desc  # this will be set for the mandatory match only
    
    def __try_match_text(self, text_to_match, match_value_func):
        match_obj = self.match_regex.search(text_to_match)
        if match_obj is None:
            return MatchResult(False)
        chars_matched = match_obj.end() - match_obj.start()
        
        # Make the match more valuable if it occurs before the first separator 
        # (i.e. a slash or an open bracket) in the text to match.
        # This ensures that, if the listing contains alternate product codes/names 
        # in brackets or after a slash, that the first product code is more likely to be matched:
        sep_mr = re.search('\(|\/', text_to_match, flags = re.UNICODE )
        is_after_sep = sep_mr != None and sep_mr.start() < match_obj.start()
        match_value = match_value_func.evaluate(chars_matched, self.family_and_model_len, is_after_sep)
        
        return MatchResult(True, match_value)
    
    def try_match(self, product_desc, extra_prod_details = None):
        match_result = RegexMatchingRule.__try_match_text(
            self, product_desc, self.value_func_on_product_desc)
        if self.must_match_on_product_desc and not match_result.is_match:
            return match_result
        if self.value_func_on_extra_prod_details.is_assigned() and extra_prod_details != None:
            extra_details_match_result = RegexMatchingRule.__try_match_text(
                self, extra_prod_details, self.value_func_on_extra_prod_details)
            if not match_result.is_match:
                return extra_details_match_result
            if extra_details_match_result.is_match:
                match_result.match_value = match_result.match_value + extra_details_match_result.match_value
        return match_result

# --------------------------------------------------------------------------------------------------
# A class which uses a set of mandatory and optional matching rules to try to match a listing:
# 
class ListingMatcher(object):
    def __init__(self, description, mandatory_rules, optional_rules):
        self.match_desc = description
        self.mandatory_matching_rules = mandatory_rules
        self.optional_matching_rules = optional_rules
    
    def try_match(self, product_desc, extra_prod_details):
        # There must be at least one mandatory rule:
        if len(self.mandatory_matching_rules) == 0:
            return MatchResult(False)
            
        is_first_rule = True
        
        for mandatory_rule in self.mandatory_matching_rules:
            mandatory_match_result = mandatory_rule.try_match(product_desc, extra_prod_details)
            if mandatory_match_result.is_match:
                if is_first_rule:
                    final_match_result = mandatory_match_result
                    is_first_rule = False
                else:
                    final_match_result.match_value = final_match_result.match_value + mandatory_match_result.match_value
            else:
                return MatchResult(False)
        
        final_match_result.description = self.match_desc
        
        for optional_rule in self.optional_matching_rules:
            optional_match_result = optional_rule.try_match(product_desc, extra_prod_details)
            if optional_match_result.is_match:
                final_match_result.match_value = final_match_result.match_value + optional_match_result.match_value
        
        return final_match_result

# --------------------------------------------------------------------------------------------------
# Matching engine to run through the ListingMatchers for a product, 
# and find the first one which applies to a particular listing:
class MatchingEngine(object):
    def __init__(self, matchers):
        self.listing_matchers = matchers
    
    def try_match_listing(self, product_desc, extra_product_details):
        for matcher in self.listing_matchers:
            match_result = matcher.try_match(product_desc, extra_product_details)
            if match_result.is_match:
                return match_result
        return MatchResult(False)


# --------------------------------------------------------------------------------------------------
# Templates to generate ListingMatchers and MatchItems:
# 

# --------------------------------------------------------------------------------------------------
# The base class for a template for a matching rule:
# 
class MatchingRuleTemplate(object):
    def __init__(self, slices, value_func_on_desc, value_func_on_details, must_match_on_desc = False):
        self.slices = slices
        self.value_func_on_product_desc = value_func_on_desc
        self.value_func_on_extra_prod_details = value_func_on_details
        self.must_match_on_product_desc = must_match_on_desc
    
    @abstractmethod
    def generate(self, all_blocks, family_and_model_len):
        pass

# --------------------------------------------------------------------------------------------------
# A class to represent the template for a RegexMatchingRule:
# 
class RegexRuleTemplate(MatchingRuleTemplate):
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
            escaped_text = escaped_text + r'(?!\w|%|\.\d|\,\d)'
        else:
            escaped_text = escaped_text + r'(?!\w)'
        return escaped_text
    
    def generate(self, all_blocks, family_and_model_len):
        # set_trace()
        block_gen = (all_blocks[s] for s in self.slices)
        extracted_blocks = itertools.chain.from_iterable(block_gen)
        extracted_text = ''.join(extracted_blocks)
        pattern = RegexRuleTemplate.regex_escape_with_optional_dashes_and_whitespace(extracted_text)
        regex = re.compile(pattern, flags = re.IGNORECASE or re.UNICODE )
        return RegexMatchingRule(regex, family_and_model_len, self.value_func_on_product_desc,
            self.value_func_on_extra_prod_details, self.must_match_on_product_desc)

# --------------------------------------------------------------------------------------------------
# A class to represent the template for a ListingMatcher:
# 
class ListingMatcherTemplate(object):
    def __init__(self, desc, mandatory_templates, optional_templates):
        self.description = desc
        self.mandatory_rule_templates = mandatory_templates
        self.optional_rule_templates = optional_templates
    
    def generate(self, all_blocks, family_and_model_len):
        # set_trace()
        mandatory_rules = [template.generate(all_blocks, family_and_model_len) for template in self.mandatory_rule_templates]
        optional_rules = [template.generate(all_blocks, family_and_model_len) for template in self.optional_rule_templates]
        listing_matcher = ListingMatcher(self.description, mandatory_rules, optional_rules)
        return listing_matcher

# --------------------------------------------------------------------------------------------------
# A class to represent the master template containing a list of ListingMatcherTemplates:
#
# These are used to generate a list of ListingMatcher objects which will be tested
# against a listing until the first match is found or no match has been found.
# 
class MasterTemplate(object):
    def __init__(self, classific, matcher_templates):
        self.classification = classific
        self.listing_matcher_templates = matcher_templates
    
    def generate(self, all_blocks, family_and_model_len):
        # set_trace()
        listing_matchers = [matcher_template.generate(all_blocks, family_and_model_len) for matcher_template in self.listing_matcher_templates]
        return MatchingEngine(listing_matchers)
