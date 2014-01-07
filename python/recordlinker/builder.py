from recordlinker.classification import *
import re
# from pdb import set_trace

# --------------------------------------------------------------------------------------------------
# A base class for classes which build a MasterTemplate from a classification string:
# 
class BaseMasterTemplateBuilder(object):
    all_of_family_and_model_with_regex_desc = 'Family and model approximately'
    family_and_model_separately_with_regex_desc = 'Family and model separately and approximately'
    model_and_words_in_family_with_regex_desc = 'Model and words in family approximately'
    
    all_of_family_and_model_with_regex_value_func_on_prod_desc = MatchValueFunction( 1000000, 10000)
    all_of_family_and_model_with_regex_value_func_on_prod_details = MatchValueFunction( 10000, 100)
    family_and_model_separately_with_regex_value_func_on_prod_desc = MatchValueFunction( 250000, 2500)  # NB: These will be added twice - once for family and once for model
    family_and_model_separately_with_regex_value_func_on_prod_details = MatchValueFunction( 2500, 25)  # NB: These will be added twice - once for family and once for model
    # model_and_words_in_family uses the value functions above for the model match, and the value functions below for each word match:
    family_word_with_regex_value_func_on_prod_desc = MatchValueFunction( 10000, 100)  # NB: These will be added twice - once for family and once for model
    family_word_with_regex_value_func_on_prod_details = MatchValueFunction( 100, 1)  # NB: These will be added twice - once for family and once for model
    
    word_regex_pattern = '(?:[can]|\-)+'
        
    def __init__(self, classific):
        self.classification = classific
        sep_index = classific.index('+')
        self.family_model_separator_index = sep_index
        self.family_slice = slice( 0, sep_index )
        self.family_classification = classific[self.family_slice]
        self.model_slice = slice( sep_index + 1, len(classific))
        self.model_classification = classific[self.model_slice]
        self.word_regex = re.compile( BaseMasterTemplateBuilder.word_regex_pattern, re.IGNORECASE | re.UNICODE | re.VERBOSE )
        # TODO: Calculate long_prod_code_slices, short_prod_code_slices, alternate_prod_code_slices, secondary_prod_code_slices
    
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
        start_index = 0
        word_slices = []
        while True:
            word = self.word_regex.search(self.family_classification, start_index)
            if word == None:
                break
            word_slice = slice(word.start(), word.end())
            word_slices.append(word_slice)
            start_index = word.end()
        
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

# --------------------------------------------------------------------------------------------------
# A derived class which is the standard way to build a MasterTemplate from a classification string:
# 
class MasterTemplateBuilder(BaseMasterTemplateBuilder):
    default_listing_template_methods = [
        BaseMasterTemplateBuilder.match_all_of_family_and_model_with_regex,
        BaseMasterTemplateBuilder.match_family_and_model_separately_with_regex,
        BaseMasterTemplateBuilder.match_model_and_words_in_family_with_regex
        # TODO: Extend with more methods
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
