import unittest
from recordlinker.builder import *

class FamilyAndModelSeparatelyMasterTemplateBuilder(SingleMethodMasterTemplateBuilder):
    def __init__(self, classific):
        SingleMethodMasterTemplateBuilder.__init__(self, classific, 
            BaseMasterTemplateBuilder.match_family_and_model_separately_with_regex)

class MasterTemplateBuilderTestCase(unittest.TestCase):
    def testBuilderInit(self):
        classification = 'a-a+a-an'
        builder = MasterTemplateBuilder(classification)
        self.assertEqual(builder.classification, classification)
        self.assertEqual(builder.family_model_separator_index, 3)
        self.assertEqual(classification[builder.family_slice], 'a-a')
        self.assertEqual(classification[builder.model_slice], 'a-an')
        self.assertEqual(builder.family_slice.start, 0)
        self.assertEqual(builder.family_slice.stop, 3)
        self.assertEqual(builder.model_slice.start, 4)
        self.assertEqual(builder.model_slice.stop, 8)
    
class AllOfFamilyAndModel_MasterTemplateBuilderTestCase(unittest.TestCase):
    def testAllOfFamilyAndModelApproximately(self):
        classification = 'a-a+a-an'
        blocks = ['Cyber', '-', 'shot', ' ', 'DSC', '-', 'W', '310']
        product_desc = 'C y b e r s h o t-DSC W 310'
        extra_prod_details = ''
        value_func = MasterTemplateBuilder.all_of_family_and_model_with_regex_value_func_on_prod_desc
        expected_match_value = value_func.fixed_value + value_func.value_per_char * len(product_desc)
        expected_description = MasterTemplateBuilder.all_of_family_and_model_with_regex_desc
        
        builder = MasterTemplateBuilder(classification)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(match_result.is_match, 'A match should be found')
        self.assertEqual(match_result.match_value, expected_match_value)
        self.assertEqual(match_result.description, expected_description)
    
class FamilyAndModelSeparately_MasterTemplateBuilderTestCase(unittest.TestCase):
    def testFamilyAndModelSeparately(self):
        classification = 'a+an'
        blocks = ['Coolpix', '+','S','6100']
        product_desc = 'Coolpix with code S6100'
        extra_prod_details = ''
        
        builder = FamilyAndModelSeparatelyMasterTemplateBuilder(classification)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(match_result.is_match, 'Check match of family and model separately')
    
    def testFamilyAndModelSeparatelyWithOnlyFamilyMatched(self):
        classification = 'a+an'
        blocks = ['Coolpix', '+','S','6100']
        product_desc = 'Coolpix 900S'
        extra_prod_details = ''
        
        builder = FamilyAndModelSeparatelyMasterTemplateBuilder(classification)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(not match_result.is_match, 'There should be no match if only family is found')
    
    def testFamilyAndModelSeparatelyWithOnlyFamilyMatched(self):
        classification = 'a+an'
        blocks = ['Coolpix', '+','S','6100']
        product_desc = 'Hotpix S6100'
        extra_prod_details = ''
        
        builder = FamilyAndModelSeparatelyMasterTemplateBuilder(classification)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(not match_result.is_match, 'There should be no match if only model is found')
    
    def testFamilyAndModelSeparatelyWithFamilyClassificationEmpty(self):
        classification = '+a-a_n'
        blocks = ['+','V','-','LUX',' ','20']
        product_desc = 'V-LUX 20'
        extra_prod_details = ''
        
        builder = FamilyAndModelSeparatelyMasterTemplateBuilder(classification)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(not match_result.is_match, 'No match should be found since the family is empty')
    
    def testFamilyAndModelSeparatelyWithNoAlphaInModel(self):
        classification = 'a-a+n'
        blocks = ['D-Lux','+','5']
        product_desc = 'D-Lux 5'
        extra_prod_details = ''
        
        builder = FamilyAndModelSeparatelyMasterTemplateBuilder(classification)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(not match_result.is_match, 'No match should be found since the model contains no alphabetic characters')

    def testFamilyAndModelSeparatelyWithNoNumericsInModel(self):
        classification = 'a+a'
        blocks = ['DigiLux','+','Zoom']
        product_desc = 'DigiLux Zoom'
        extra_prod_details = ''
        
        builder = FamilyAndModelSeparatelyMasterTemplateBuilder(classification)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(not match_result.is_match, 'No match should be found since the model contains no digits')

class ModelAndWordsInFamily_MasterTemplateBuilderTestCase(unittest.TestCase):
    def testModelAndWordsInFamily(self):
        classification = 'a_a+n_c'
        blocks = ['Digital', ' ', 'IXUS', '+', '1000', ' ', 'HS']
        product_desc = 'IXUS 1000 HS from Digital'
        extra_prod_details = 'Digital camera'
        
        expected_match_value \
            = BaseMasterTemplateBuilder.family_and_model_separately_with_regex_value_func_on_prod_desc.evaluate(len('1000 HS')) \
            + BaseMasterTemplateBuilder.family_word_with_regex_value_func_on_prod_desc.evaluate(len('Digital')) \
            + BaseMasterTemplateBuilder.family_word_with_regex_value_func_on_prod_desc.evaluate(len('IXUS')) \
            + BaseMasterTemplateBuilder.family_word_with_regex_value_func_on_prod_details.evaluate(len('Digital'))
        
        builder = SingleMethodMasterTemplateBuilder(classification, 
            BaseMasterTemplateBuilder.match_model_and_words_in_family_with_regex)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(match_result.is_match, 'Check match of model and words in family')
        self.assertEqual(match_result.match_value, expected_match_value)
    
    def testModelAndWordsInFamilyWithOnlyModelMatched(self):
        classification = 'a_a+n_c'
        blocks = ['Digital', ' ', 'IXUS', '+', '1000', ' ', 'HS']
        product_desc = '1000 HS'
        extra_prod_details = ''
        
        expected_match_value \
            = BaseMasterTemplateBuilder.family_and_model_separately_with_regex_value_func_on_prod_desc.evaluate(len('1000 HS'))
        
        builder = SingleMethodMasterTemplateBuilder(classification, 
            BaseMasterTemplateBuilder.match_model_and_words_in_family_with_regex)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(match_result.is_match, 'There should still be a match if only model is found')
        self.assertEqual(match_result.match_value, expected_match_value)
    
    def testModelAndWordsInFamilyWithOnlyFamilyWordsMatched(self):
        classification = 'a_a+n_c'
        blocks = ['Digital', ' ', 'IXUS', '+', '1000', ' ', 'HS']
        product_desc = 'Digital IXUS'
        extra_prod_details = '1000 HS'
        builder = SingleMethodMasterTemplateBuilder(classification, 
            BaseMasterTemplateBuilder.match_model_and_words_in_family_with_regex)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(not match_result.is_match, 'There should be no match if only family words are found')
    
    def testModelAndWordsInFamilyWithFamilyHavingOnlyOneWord(self):
        classification = '+a-a_n'
        blocks = ['+','V','-','LUX',' ','20']
        product_desc = 'V-LUX 20'
        extra_prod_details = ''
        
        builder = SingleMethodMasterTemplateBuilder(classification, 
            BaseMasterTemplateBuilder.match_model_and_words_in_family_with_regex)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(not match_result.is_match, 'No match should be found since the family is empty')
    
    def testModelAndWordsInFamilyWithOnlyOneWordInFamily(self):
        classification = 'a_+an'
        blocks = ['Cybershot',' ','+','W','580']
        product_desc = 'Cybershot W580'
        extra_prod_details = ''
        
        builder = SingleMethodMasterTemplateBuilder(classification, 
            BaseMasterTemplateBuilder.match_model_and_words_in_family_with_regex)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(not match_result.is_match, 'No match should be found since the family field has only one word')

    def testModelAndWordsInFamilyWithNoAlphaInModel(self):
        classification = 'a_a+n'
        blocks = ['D',' ','Lux','+','5']
        product_desc = 'D Lux 5'
        extra_prod_details = ''
        
        builder = SingleMethodMasterTemplateBuilder(classification, 
            BaseMasterTemplateBuilder.match_model_and_words_in_family_with_regex)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(not match_result.is_match, 'No match should be found since the model contains no alphabetic characters')

    def testModelAndWordsInFamilyWithNoNumericsInModel(self):
        classification = 'a_a+a'
        blocks = ['Digi', ' ','Lux','+','Zoom']
        product_desc = 'Digi Lux Zoom'
        extra_prod_details = ''
        
        builder = SingleMethodMasterTemplateBuilder(classification, 
            BaseMasterTemplateBuilder.match_model_and_words_in_family_with_regex)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(not match_result.is_match, 'No match should be found since the model contains no digits')


# Run unit tests from the command line:        
if __name__ == '__main__':
    unittest.main()
