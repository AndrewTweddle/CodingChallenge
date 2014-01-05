from recordlinker.classification import *
# from pdb import set_trace

# --------------------------------------------------------------------------------------------------
# A base class for classes which build a MasterTemplate from a classification string:
# 
class BaseMasterTemplateBuilder(object):
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
    
    @abstractmethod
    def get_listing_templates(self):
        pass
    
    def generate_listing_templates_from_methods(self, list_of_methods):
        listing_matcher_templates = [listing_template_method(self) for listing_template_method in list_of_methods]
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

# --------------------------------------------------------------------------------------------------
# A derived class which is the standard way to build a MasterTemplate from a classification string:
# 
class MasterTemplateBuilder(BaseMasterTemplateBuilder):
    default_listing_template_methods = [
        BaseMasterTemplateBuilder.match_all_of_family_and_model_with_regex,
        BaseMasterTemplateBuilder.match_family_and_model_separately_with_regex
        # TODO: Extend with more methods
    ]
    
    def get_listing_templates(self):
        return self.generate_listing_templates_from_methods(MasterTemplateBuilder.default_listing_template_methods)
