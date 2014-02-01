from recordlinker.classification import *
import re
# 
from pdb import set_trace

# --------------------------------------------------------------------------------------------------
# A base class for classes which build a MasterTemplate from a classification string:
# 
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
    
    word_regex_pattern = '(?:[can]|\-)+'
    
    # The following product code patterns all prevent a product code from
    # being preceded by an opening bracket or succeeded by a closing bracket.
    # This is to prevent products such as the "Ricoh GXR (A12)" being matched to the "Ricoh GR A12".
    # Note that the product code should not be preceded or succeeded by another alphanumeric block.
    prod_code_having_alpha_dash_pattern_then_a_number = '(?<!\(|a|c|n)a-a_n(?!\)|a|c|n)'
    prod_code_having_dash_pattern = '(?<!\(|a|c|n)[acn]+\-[-acn]*[acn](?!\)|a|c|n)'
    prod_code_having_alpha_and_numeric_pattern = '(?<!\(|a|c)(?:[ac]+n[acn]*|n+[ac][acn]*)(?!\)|a|c|n)'
    alt_prod_code_pattern = '(?<!\(|a|c|n)(?P<prefix>[acn][-acn]*\-)(?:[acn]*[acn])\!(?P<suffix>[acnx]*[acn])(?!\)|a|c|n)'
    
    word_and_number_crossing_family_and_model_pattern = '(?:^a|(?<=_)a)\+n(?=$|_)'
        # was: '(?<=^|_)a\+n(?=$|_)'
        # but this gives "error: look-behind requires fixed-width pattern"
        
    def __init__(self, classific):
        self.classification = classific
        sep_index = classific.index('+')
        self.family_model_separator_index = sep_index
        self.family_slice = slice( 0, sep_index )
        self.family_classification = classific[self.family_slice]
        self.model_slice = slice( sep_index + 1, len(classific))
        self.model_classification = classific[self.model_slice]
        self.word_regex = re.compile( BaseMasterTemplateBuilder.word_regex_pattern, re.IGNORECASE | re.UNICODE | re.VERBOSE )
    
    @abstractmethod
    def get_listing_templates(self):
        pass
    
    def generate_listing_templates_from_methods(self, list_of_methods):
        listing_matcher_templates = [
            listing_template
            for listing_template_method in list_of_methods
            for listing_template in listing_template_method(self) 
        ]
        return listing_matcher_templates
    
    def build(self):
        listing_matcher_templates = self.get_listing_templates()
        master_tpl = MasterTemplate(self.classification, listing_matcher_templates)
        return master_tpl
    
    def match_all_of_family_and_model_with_regex(self):
        # set_trace()
        
        # Don't apply this rule if the model is all alphabetic:
        if self.model_classification.replace('_','') == 'a':
            return []
        
        slices = [self.family_slice, self.model_slice]
        rule_tpl = RegexRuleTemplate( slices,
            MasterTemplateBuilder.all_of_family_and_model_with_regex_value_func_on_prod_desc,
            MasterTemplateBuilder.all_of_family_and_model_with_regex_value_func_on_prod_details,
            must_match_on_desc = True)
        listing_tpl = ListingMatcherTemplate(
            MasterTemplateBuilder.all_of_family_and_model_with_regex_desc, 
            [rule_tpl], [])
        return [listing_tpl]
    
    def match_family_and_model_separately_with_regex(self):
        # Check that family is not empty:
        if len(self.family_classification) == 0:
            return []
        
        # Check that model has both alphas and numerics.
        # This is to avoid matching "Digilux" "4.3", "Digilux" "Zoom", "D-Lux" "5":
        modelc = self.model_classification
        has_no_alpha = modelc.find('a') == -1 and modelc.find('c') == -1
        has_no_numeric = modelc.find('n') == -1
        if has_no_alpha or has_no_numeric:
            return []
        
        # Generate the listing template:
        family_rule_tpl = RegexRuleTemplate( [self.family_slice], 
            MasterTemplateBuilder.family_and_model_separately_with_regex_value_func_on_prod_desc,
            MasterTemplateBuilder.family_and_model_separately_with_regex_value_func_on_prod_details,
            must_match_on_desc = True)
        model_rule_tpl = RegexRuleTemplate( [self.model_slice],
            MasterTemplateBuilder.family_and_model_separately_with_regex_value_func_on_prod_desc,
            MasterTemplateBuilder.family_and_model_separately_with_regex_value_func_on_prod_details,
            must_match_on_desc = True)
        listing_tpl = ListingMatcherTemplate(
            MasterTemplateBuilder.family_and_model_separately_with_regex_desc,
            [family_rule_tpl, model_rule_tpl], [])
        return [listing_tpl]
    
    def find_word_slices_in_classification(self, classification_text, start_index = 0, slice_offset = 0):
        word_slices = []
        while True:
            word = self.word_regex.search(classification_text, start_index)
            if word == None:
                break
            word_slice = slice(word.start() + slice_offset, word.end() + slice_offset)
            word_slices.append(word_slice)
            start_index = word.end()
        return word_slices
    
    def match_model_and_words_in_family_with_regex(self):
        # Check that family is not empty:
        if len(self.family_classification) == 0:
            return []
        
        # Check that model has both alphas and numerics.
        # This is to avoid matching "Digilux" "4.3", "Digilux" "Zoom", "D-Lux" "5":
        modelc = self.model_classification
        has_no_alpha = modelc.find('a') == -1 and modelc.find('c') == -1
        has_no_numeric = modelc.find('n') == -1
        if has_no_alpha or has_no_numeric:
            return []
        
        # Check that family has multiple words i.e. it contains whitespace:
        index_of_whitespace = self.family_classification.find('_', 1)  # Start at index 1 to ignore leading whitespace
        famc_len = len(self.family_classification)
        if index_of_whitespace == -1 or index_of_whitespace == famc_len - 1:
            return []
        
        # Find words in family:
        word_slices = self.find_word_slices_in_classification(self.family_classification, start_index = 0, slice_offset = 0)
        
        # Generate the listing template:
        model_rule_tpl = RegexRuleTemplate( [self.model_slice],
            MasterTemplateBuilder.family_and_model_separately_with_regex_value_func_on_prod_desc,
            MasterTemplateBuilder.family_and_model_separately_with_regex_value_func_on_prod_details,
            must_match_on_desc = True)
        family_word_rule_tpls = [
            RegexRuleTemplate( [word_slice], 
                MasterTemplateBuilder.family_word_with_regex_value_func_on_prod_desc,
                MasterTemplateBuilder.family_word_with_regex_value_func_on_prod_details,
                must_match_on_desc = False)
            for word_slice in word_slices
        ]
        listing_tpl = ListingMatcherTemplate(
            MasterTemplateBuilder.model_and_words_in_family_with_regex_desc,
            [model_rule_tpl], family_word_rule_tpls)
        return [listing_tpl]
    
    def get_family_and_model_regex_word_templates(self, family_classification_text, model_classification_text):
        # set_trace()
        model_slice_offset = self.family_model_separator_index + 1
        family_word_slices = self.find_word_slices_in_classification(
            family_classification_text, start_index = 0, slice_offset = 0)
        model_word_slices = self.find_word_slices_in_classification(
            model_classification_text, start_index = 0, slice_offset = model_slice_offset)
        family_word_rule_tpls = [
            RegexRuleTemplate( [word_slice], 
                MasterTemplateBuilder.family_word_with_regex_value_func_on_prod_desc,
                MasterTemplateBuilder.family_word_with_regex_value_func_on_prod_details,
                must_match_on_desc = False)
            for word_slice in family_word_slices
        ]
        model_word_rule_tpls = [
            RegexRuleTemplate( [word_slice], 
                MasterTemplateBuilder.model_word_with_regex_value_func_on_prod_desc,
                MasterTemplateBuilder.model_word_with_regex_value_func_on_prod_details,
                must_match_on_desc = False)
            for word_slice in model_word_slices
        ]
        family_word_rule_tpls.extend(model_word_rule_tpls)
        return family_word_rule_tpls
    
    def get_prod_code_listing_tpl_from_match_result(self, match_result, 
        value_func_on_prod_desc, value_func_on_prod_details, listing_desc):
        start = match_result.start()
        end = match_result.end()
        match_len = end - start
        model_slice_offset = self.family_model_separator_index + 1
        
        prod_code_slices = [slice(start + model_slice_offset, end + model_slice_offset)]
        prod_code_rule_tpl = RegexRuleTemplate( prod_code_slices,
            value_func_on_prod_desc, value_func_on_prod_details, must_match_on_desc = True)
        
        # Replace the product code with spaces to ensure that it doesn't contribute to the word matches as well:
        model_classification_text = self.model_classification[:start] + (match_len * ' ') + self.model_classification[end:]
        word_rule_tpls = self.get_family_and_model_regex_word_templates(self.family_classification, model_classification_text)
        
        listing_tpl = ListingMatcherTemplate( listing_desc, [prod_code_rule_tpl], word_rule_tpls)
        return listing_tpl
    
    def get_alt_prod_code_listing_tpl_from_match_result(self, match_result, 
        value_func_on_prod_desc, value_func_on_prod_details, listing_desc):
        start_1 = match_result.start('prefix')
        end_1 = match_result.end('prefix')
        start_2 = match_result.start('suffix')
        end_2 = match_result.end('suffix')
        match_len_1 = end_1 - start_1
        match_len_2 = end_2 - start_2
        
        model_slice_offset = self.family_model_separator_index + 1
        
        prod_code_slices = [
            slice(start_1 + model_slice_offset, end_1 + model_slice_offset),
            slice(start_2 + model_slice_offset, end_2 + model_slice_offset)
        ]
        prod_code_rule_tpl = RegexRuleTemplate( prod_code_slices,
            value_func_on_prod_desc, value_func_on_prod_details, must_match_on_desc = True)
        
        # Replace the product code with spaces to ensure that it doesn't contribute to the word matches as well:
        model_classification_text = self.model_classification[:start_1] + (match_len_1 * ' ') \
            + self.model_classification[end_1:start_2] + (match_len_2 * ' ')  + self.model_classification[end_2:]
        word_rule_tpls = self.get_family_and_model_regex_word_templates(self.family_classification, model_classification_text)
        
        listing_tpl = ListingMatcherTemplate( listing_desc, [prod_code_rule_tpl], word_rule_tpls)
        return listing_tpl
    
    def match_prod_code_having_alphas_around_dash_then_a_number(self, match_result):
        listing_tpl = self.get_prod_code_listing_tpl_from_match_result(match_result, 
            MasterTemplateBuilder.prod_code_having_alphas_around_dash_with_regex_value_func_on_prod_desc, 
            MasterTemplateBuilder.prod_code_having_alphas_around_dash_with_regex_value_func_on_prod_details, 
            MasterTemplateBuilder.prod_code_having_alphas_around_dash_with_regex_desc)
        if listing_tpl == None:
            return []
        else:
            return [listing_tpl]
    
    def match_prod_code_having_dash(self, match_result):
        listing_tpl = self.get_prod_code_listing_tpl_from_match_result(match_result, 
            MasterTemplateBuilder.prod_code_having_dash_with_regex_value_func_on_prod_desc, 
            MasterTemplateBuilder.prod_code_having_dash_with_regex_value_func_on_prod_details, 
            MasterTemplateBuilder.prod_code_having_dash_with_regex_desc)
        if listing_tpl == None:
            return []
        # Search for an alternate product code (indicated by a slash)
        # For example, a 'DSC-V100 / X100' has classification 'a-an!an'
        # In this case, create an alternate product code to match DSC-X100:
        alt_match_result = re.search( BaseMasterTemplateBuilder.alt_prod_code_pattern, 
            self.model_classification, re.IGNORECASE | re.UNICODE | re.VERBOSE )
        if alt_match_result == None:
            return [listing_tpl]
        
        alt_listing_tpl = self.get_alt_prod_code_listing_tpl_from_match_result(alt_match_result, 
            MasterTemplateBuilder.alt_prod_code_having_dash_with_regex_value_func_on_prod_desc, 
            MasterTemplateBuilder.alt_prod_code_having_dash_with_regex_value_func_on_prod_details, 
            MasterTemplateBuilder.alt_prod_code_having_dash_with_regex_desc)
        
        if alt_listing_tpl == None:
            return [listing_tpl]
        else:
            return [listing_tpl, alt_listing_tpl]
    
    def match_prod_code_with_no_dash(self, match_result):
        listing_tpl = self.get_prod_code_listing_tpl_from_match_result(match_result, 
            MasterTemplateBuilder.prod_code_having_no_dash_with_regex_value_func_on_prod_desc, 
            MasterTemplateBuilder.prod_code_having_no_dash_with_regex_value_func_on_prod_details, 
            MasterTemplateBuilder.prod_code_having_no_dash_with_regex_desc)
        if listing_tpl == None:
            return []
        else:
            return [listing_tpl]
    
    def match_prod_code_with_regex(self):
        # First try to match the 'a-a_n' pattern.
        # This addresses the case where there are only alpha characters around a dash.
        # This may be correct (e.g. a Pentax 'K-r' camera).
        # But when followed by a number, that should also be treated as part of the product code.
        # e.g. 'V-LUX 20' is the product code, not just 'V-LUX'
        match_result = re.search( BaseMasterTemplateBuilder.prod_code_having_alpha_dash_pattern_then_a_number, 
            self.model_classification, re.IGNORECASE | re.UNICODE | re.VERBOSE )
        if match_result != None:
            return self.match_prod_code_having_alphas_around_dash_then_a_number(match_result)
        
        # Match product codes which contain a dash:
        match_result = re.search( BaseMasterTemplateBuilder.prod_code_having_dash_pattern, 
            self.model_classification, re.IGNORECASE | re.UNICODE | re.VERBOSE )
        if match_result != None:
            return self.match_prod_code_having_dash(match_result)
            
        # Match product codes which contain both alphabetic and numeric characters but no dash:
        match_result = re.search( BaseMasterTemplateBuilder.prod_code_having_alpha_and_numeric_pattern, 
            self.model_classification, re.IGNORECASE | re.UNICODE | re.VERBOSE )
        if match_result != None:
            return self.match_prod_code_with_no_dash(match_result)
        
        # No product code match found:
        return []
    
    def get_prod_code_followed_by_a_letter_or_specific_letters_listing_tpl_from_match_result(self, match_result, 
        value_func_on_prod_desc, value_func_on_prod_details, listing_desc):
        start = match_result.start()
        end = match_result.end()
        match_len = end - start
        model_slice_offset = self.family_model_separator_index + 1
        
        prod_code_slices = [slice(start + model_slice_offset, end + model_slice_offset)]
        prod_code_rule_tpl = RegexRuleTemplateFollowedByAnyLetterOrSpecificLetters( prod_code_slices,
            value_func_on_prod_desc, value_func_on_prod_details, must_match_on_desc = True)
        
        # Replace the product code with spaces to ensure that it doesn't contribute to the word matches as well:
        model_classification_text = self.model_classification[:start] + (match_len * ' ') + self.model_classification[end:]
        word_rule_tpls = self.get_family_and_model_regex_word_templates(self.family_classification, model_classification_text)
        
        listing_tpl = ListingMatcherTemplate( listing_desc, [prod_code_rule_tpl], word_rule_tpls)
        return listing_tpl
    
    def get_listing_tpl_for_prod_code_followed_by_a_letter_or_specific_letters(self, match_result):
        listing_tpl = self.get_prod_code_followed_by_a_letter_or_specific_letters_listing_tpl_from_match_result(match_result, 
            MasterTemplateBuilder.prod_code_followed_by_a_letter_or_specific_letters_with_regex_value_func_on_prod_desc, 
            MasterTemplateBuilder.prod_code_followed_by_a_letter_or_specific_letters_with_regex_value_func_on_prod_details, 
            MasterTemplateBuilder.prod_code_followed_by_a_letter_or_specific_letters_with_regex_desc)
        if listing_tpl == None:
            return []
        
        return [listing_tpl]
    
    def match_prod_code_followed_by_a_letter_or_specific_letters_with_regex(self):
        # Match product codes which contain a dash:
        match_result = re.search( BaseMasterTemplateBuilder.prod_code_having_dash_pattern, 
            self.model_classification, re.IGNORECASE | re.UNICODE | re.VERBOSE )
        if match_result != None:
            return self.get_listing_tpl_for_prod_code_followed_by_a_letter_or_specific_letters(match_result)
            
        # Match product codes which contain both alphabetic and numeric characters but no dash:
        match_result = re.search( BaseMasterTemplateBuilder.prod_code_having_alpha_and_numeric_pattern, 
            self.model_classification, re.IGNORECASE | re.UNICODE | re.VERBOSE )
        if match_result != None:
            return self.get_listing_tpl_for_prod_code_followed_by_a_letter_or_specific_letters(match_result)
        
        # No product code match found:
        return []
    
    def match_all_of_family_and_alpha_model_with_regex(self):
        # set_trace()
        
        # Only apply this rule if the model is all alphabetic:
        if self.model_classification.replace('_','') != 'a':
            return []
        
        slices = [self.family_slice, self.model_slice]
        rule_tpl = RegexRuleTemplate( slices,
            MasterTemplateBuilder.all_of_family_and_alpha_model_with_regex_value_func_on_prod_desc,
            MasterTemplateBuilder.all_of_family_and_alpha_model_with_regex_value_func_on_prod_details,
            must_match_on_desc = True)
        listing_tpl = ListingMatcherTemplate(
            MasterTemplateBuilder.all_of_family_and_alpha_model_with_regex_desc, 
            [rule_tpl], [])
        return [listing_tpl]
    
    def match_word_and_number_crossing_family_and_model(self):
        # set_trace()
        if self.classification == 'a+n':
            return []
        
        match_result = re.search( BaseMasterTemplateBuilder.word_and_number_crossing_family_and_model_pattern, 
            self.classification, re.IGNORECASE | re.UNICODE | re.VERBOSE )
        if match_result == None:
            return []
        
        start = match_result.start()
        end = match_result.end()
        match_len = end - start
        
        prod_code_slices = [slice(start, start + 1), slice(end - 1, end)]
        prod_code_rule_tpl = RegexRuleTemplate( prod_code_slices,
            BaseMasterTemplateBuilder.word_and_number_crossing_family_and_model_with_regex_value_func_on_prod_desc,
            BaseMasterTemplateBuilder.word_and_number_crossing_family_and_model_with_regex_value_func_on_prod_details,
            must_match_on_desc = True)
        
        # Replace the product code with spaces to ensure that it doesn't contribute to the word matches as well:
        family_classification_text = self.family_classification[:start] + '_'
        model_classification_text = '_' + self.model_classification[1:]
        word_rule_tpls = self.get_family_and_model_regex_word_templates(family_classification_text, model_classification_text)
        
        listing_tpl = ListingMatcherTemplate(
            BaseMasterTemplateBuilder.word_and_number_crossing_family_and_model_with_regex_desc,
            [prod_code_rule_tpl], word_rule_tpls)
        return [listing_tpl]

# --------------------------------------------------------------------------------------------------
# A derived class which is the standard way to build a MasterTemplate from a classification string:
# 
class MasterTemplateBuilder(BaseMasterTemplateBuilder):
    default_listing_template_methods = [
        BaseMasterTemplateBuilder.match_all_of_family_and_model_with_regex,
        BaseMasterTemplateBuilder.match_family_and_model_separately_with_regex,
        BaseMasterTemplateBuilder.match_model_and_words_in_family_with_regex,
        BaseMasterTemplateBuilder.match_prod_code_with_regex,
        BaseMasterTemplateBuilder.match_all_of_family_and_alpha_model_with_regex,
        BaseMasterTemplateBuilder.match_prod_code_followed_by_a_letter_or_specific_letters_with_regex,
        BaseMasterTemplateBuilder.match_word_and_number_crossing_family_and_model
    ]
    
    def get_listing_templates(self):
        return self.generate_listing_templates_from_methods(MasterTemplateBuilder.default_listing_template_methods)

# --------------------------------------------------------------------------------------------------
# A derived class using a single method to build a MasterTemplate from a classification string:
# 
class SingleMethodMasterTemplateBuilder(BaseMasterTemplateBuilder):
    def __init__(self, classific, single_method):
        BaseMasterTemplateBuilder.__init__(self, classific)
        self.single_list_template_method = single_method
    
    def get_listing_templates(self):
        return self.generate_listing_templates_from_methods([self.single_list_template_method])
