from recordlinker.classification import *
# from pdb import set_trace

# --------------------------------------------------------------------------------------------------
# A class which is used to build a MasterTemplate from a classification string:
# 
class MasterTemplateBuilder(object):
    all_of_family_and_model_with_regex_desc = 'Family and model approximately'
    family_and_model_separately_with_regex_desc = 'Family and model separately and approximately'
    
    all_of_family_and_model_with_regex_value_func_on_prod_desc = MatchValueFunction( 1000000, 10000)
    all_of_family_and_model_with_regex_value_func_on_prod_details = MatchValueFunction( 10000, 100)
    family_and_model_separately_with_regex_value_func_on_prod_desc = MatchValueFunction( 250000, 2500)  # NB: These will be added twice - once for family and once for model
    family_and_model_separately_with_regex_value_func_on_prod_details = MatchValueFunction( 2500, 25)  # NB: These will be added twice - once for family and once for model
    
    def __init__(self, classific):
        self.classification = classific
        sep_index = classific.index('+')
        self.family_model_separator_index = sep_index
        self.family_slice = slice( 0, sep_index )
        self.model_slice = slice( sep_index + 1, len(classific))
        # TODO: Calculate long_prod_code_slices, short_prod_code_slices, alternate_prod_code_slices, secondary_prod_code_slices
    
    def build(self):
        tpl1 = self.match_all_of_family_and_model_with_regex()
        tpl2 = self.match_family_and_model_separately_with_regex()
        # TODO: Build up other listing matcher templates...
        
        listing_matcher_templates = [tpl1, tpl2]
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
        return listing_tpl
    
    def match_family_and_model_separately_with_regex(self):
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
        return listing_tpl
