import unittest
from recordlinker.builder import *
# from pdb import set_trace

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
        family_and_model_len = len('Cyber-shotDSC-W310')
        product_desc = 'C y b e r s h o t-DSC W 310'
        extra_prod_details = ''
        value_func = MasterTemplateBuilder.all_of_family_and_model_with_regex_value_func_on_prod_desc
        expected_match_value = 10 * ( value_func.fixed_value + value_func.value_per_char * len(product_desc) ) - family_and_model_len
        expected_description = MasterTemplateBuilder.all_of_family_and_model_with_regex_desc
        
        builder = MasterTemplateBuilder(classification)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks, family_and_model_len)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(match_result.is_match, 'A match should be found')
        self.assertEqual(match_result.match_value, expected_match_value)
        self.assertEqual(match_result.description, expected_description)
    
class FamilyAndModelSeparately_MasterTemplateBuilderTestCase(unittest.TestCase):
    def testFamilyAndModelSeparately(self):
        classification = 'a+an'
        blocks = ['Coolpix', '+','S','6100']
        family_and_model_len = len('CoolpixS6100')
        product_desc = 'Coolpix with code S6100'
        extra_prod_details = ''
        
        builder = FamilyAndModelSeparatelyMasterTemplateBuilder(classification)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks, family_and_model_len)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(match_result.is_match, 'Check match of family and model separately')
    
    def testFamilyAndModelSeparatelyWithOnlyFamilyMatched(self):
        classification = 'a+an'
        blocks = ['Coolpix', '+','S','6100']
        family_and_model_len = len('CoolpixS6100')
        product_desc = 'Coolpix 900S'
        extra_prod_details = ''
        
        builder = FamilyAndModelSeparatelyMasterTemplateBuilder(classification)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks, family_and_model_len)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(not match_result.is_match, 'There should be no match if only family is found')
    
    def testFamilyAndModelSeparatelyWithOnlyFamilyMatched(self):
        classification = 'a+an'
        blocks = ['Coolpix', '+','S','6100']
        family_and_model_len = len('CoolpixS6100')
        product_desc = 'Hotpix S6100'
        extra_prod_details = ''
        
        builder = FamilyAndModelSeparatelyMasterTemplateBuilder(classification)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks, family_and_model_len)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(not match_result.is_match, 'There should be no match if only model is found')
    
    def testFamilyAndModelSeparatelyWithFamilyClassificationEmpty(self):
        classification = '+a-a_n'
        blocks = ['+','V','-','LUX',' ','20']
        family_and_model_len = len('V-LUX 20')
        product_desc = 'V-LUX 20'
        extra_prod_details = ''
        
        builder = FamilyAndModelSeparatelyMasterTemplateBuilder(classification)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks, family_and_model_len)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(not match_result.is_match, 'No match should be found since the family is empty')
    
    def testFamilyAndModelSeparatelyWithNoAlphaInModel(self):
        classification = 'a-a+n'
        blocks = ['D-Lux','+','5']
        family_and_model_len = len('D-Lux5')
        product_desc = 'D-Lux 5'
        extra_prod_details = ''
        
        builder = FamilyAndModelSeparatelyMasterTemplateBuilder(classification)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks, family_and_model_len)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(not match_result.is_match, 'No match should be found since the model contains no alphabetic characters')

    def testFamilyAndModelSeparatelyWithNoNumericsInModel(self):
        classification = 'a+a'
        blocks = ['DigiLux','+','Zoom']
        family_and_model_len = len('DigiLuxZoom')
        product_desc = 'DigiLux Zoom'
        extra_prod_details = ''
        
        builder = FamilyAndModelSeparatelyMasterTemplateBuilder(classification)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks, family_and_model_len)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(not match_result.is_match, 'No match should be found since the model contains no digits')

class ModelAndWordsInFamily_MasterTemplateBuilderTestCase(unittest.TestCase):
    def testModelAndWordsInFamily(self):
        classification = 'a_a+n_c'
        blocks = ['Digital', ' ', 'IXUS', '+', '1000', ' ', 'HS']
        family_and_model_len = len('Digital IXUS1000 HS')
        product_desc = 'IXUS 1000 HS from Digital'
        extra_prod_details = 'Digital camera'
        
        expected_match_value \
            = BaseMasterTemplateBuilder.family_and_model_separately_with_regex_value_func_on_prod_desc.evaluate(len('1000 HS'), family_and_model_len, is_after_sep = False) \
            + BaseMasterTemplateBuilder.family_word_with_regex_value_func_on_prod_desc.evaluate(len('Digital'), family_and_model_len, is_after_sep = False) \
            + BaseMasterTemplateBuilder.family_word_with_regex_value_func_on_prod_desc.evaluate(len('IXUS'), family_and_model_len, is_after_sep = False) \
            + BaseMasterTemplateBuilder.family_word_with_regex_value_func_on_prod_details.evaluate(len('Digital'), family_and_model_len, is_after_sep = False)
        
        builder = SingleMethodMasterTemplateBuilder(classification, 
            BaseMasterTemplateBuilder.match_model_and_words_in_family_with_regex)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks, family_and_model_len)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(match_result.is_match, 'Check match of model and words in family')
        self.assertEqual(match_result.match_value, expected_match_value)
    
    def testModelAndWordsInFamilyWithOnlyModelMatched(self):
        classification = 'a_a+n_c'
        blocks = ['Digital', ' ', 'IXUS', '+', '1000', ' ', 'HS']
        family_and_model_len = len('Digital IXUS1000 HS')
        product_desc = '1000 HS'
        extra_prod_details = ''
        
        expected_match_value \
            = BaseMasterTemplateBuilder.family_and_model_separately_with_regex_value_func_on_prod_desc.evaluate( \
                len('1000 HS'), family_and_model_len, is_after_sep = False)
        
        builder = SingleMethodMasterTemplateBuilder(classification, 
            BaseMasterTemplateBuilder.match_model_and_words_in_family_with_regex)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks, family_and_model_len)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(match_result.is_match, 'There should still be a match if only model is found')
        self.assertEqual(match_result.match_value, expected_match_value)
    
    def testModelAndWordsInFamilyWithOnlyFamilyWordsMatched(self):
        classification = 'a_a+n_c'
        blocks = ['Digital', ' ', 'IXUS', '+', '1000', ' ', 'HS']
        family_and_model_len = len('Digital IXUS1000 HS')
        product_desc = 'Digital IXUS'
        extra_prod_details = '1000 HS'
        builder = SingleMethodMasterTemplateBuilder(classification, 
            BaseMasterTemplateBuilder.match_model_and_words_in_family_with_regex)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks, family_and_model_len)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(not match_result.is_match, 'There should be no match if only family words are found')
    
    def testModelAndWordsInFamilyWithFamilyHavingOnlyOneWord(self):
        classification = '+a-a_n'
        blocks = ['+','V','-','LUX',' ','20']
        family_and_model_len = len('V-LUX 20')
        product_desc = 'V-LUX 20'
        extra_prod_details = ''
        
        builder = SingleMethodMasterTemplateBuilder(classification, 
            BaseMasterTemplateBuilder.match_model_and_words_in_family_with_regex)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks, family_and_model_len)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(not match_result.is_match, 'No match should be found since the family is empty')
    
    def testModelAndWordsInFamilyWithOnlyOneWordInFamily(self):
        classification = 'a_+an'
        blocks = ['Cybershot',' ','+','W','580']
        family_and_model_len = len('Cybershot W580')
        product_desc = 'Cybershot W580'
        extra_prod_details = ''
        
        builder = SingleMethodMasterTemplateBuilder(classification, 
            BaseMasterTemplateBuilder.match_model_and_words_in_family_with_regex)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks, family_and_model_len)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(not match_result.is_match, 'No match should be found since the family field has only one word')

    def testModelAndWordsInFamilyWithNoAlphaInModel(self):
        classification = 'a_a+n'
        blocks = ['D',' ','Lux','+','5']
        family_and_model_len = len('D Lux5')
        product_desc = 'D Lux 5'
        extra_prod_details = ''
        
        builder = SingleMethodMasterTemplateBuilder(classification, 
            BaseMasterTemplateBuilder.match_model_and_words_in_family_with_regex)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks, family_and_model_len)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(not match_result.is_match, 'No match should be found since the model contains no alphabetic characters')

    def testModelAndWordsInFamilyWithNoNumericsInModel(self):
        classification = 'a_a+a'
        blocks = ['Digi', ' ','Lux','+','Zoom']
        family_and_model_len = len('Digi LuxZoom')
        product_desc = 'Digi Lux Zoom'
        extra_prod_details = ''
        
        builder = SingleMethodMasterTemplateBuilder(classification, 
            BaseMasterTemplateBuilder.match_model_and_words_in_family_with_regex)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks, family_and_model_len)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(not match_result.is_match, 'No match should be found since the model contains no digits')
    

class ProdCode_MasterTemplateBuilderTestCase(unittest.TestCase):
    def testProdCodeMatchHavingAlphasAroundDashThenASpaceAndANumber(self):
        classification = '+a-a_n'
        blocks = ['+','V','-','LUX',' ','20']
        family_and_model_len = len('V-LUX 20')
        product_desc = 'Leica V-LUX 20'
        extra_prod_details = 'Lux'
        
        expected_match_value \
            = BaseMasterTemplateBuilder.prod_code_having_alphas_around_dash_with_regex_value_func_on_prod_desc.evaluate( \
                len('V-LUX 20'), family_and_model_len, is_after_sep = False)
        
        builder = SingleMethodMasterTemplateBuilder(classification, 
            BaseMasterTemplateBuilder.match_prod_code_with_regex)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks, family_and_model_len)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(match_result.is_match, 'There should be a match for an "a-a_n" product')
        self.assertEqual(match_result.match_value, expected_match_value)
    
    def testProdCodeMatchHavingADash(self):
        classification = 'n+a-na_a_a'
        blocks = ['Canon','+','EOS','-','1','D',' ','Mark',' ','IV']
        family_and_model_len = len('Canon EOS-1D Mark IV')
        product_desc = 'Canon EOS 1-D Mk IV'
        extra_prod_details = 'Mark'
        
        expected_match_value \
            = BaseMasterTemplateBuilder.prod_code_having_dash_with_regex_value_func_on_prod_desc.evaluate(len('EOS 1-D'), family_and_model_len, is_after_sep = False) \
            + BaseMasterTemplateBuilder.family_word_with_regex_value_func_on_prod_desc.evaluate(len('Canon'), family_and_model_len, is_after_sep = False) \
            + BaseMasterTemplateBuilder.model_word_with_regex_value_func_on_prod_desc.evaluate(len('IV'), family_and_model_len, is_after_sep = False) \
            + BaseMasterTemplateBuilder.model_word_with_regex_value_func_on_prod_details.evaluate(len('Mark'), family_and_model_len, is_after_sep = False)
        
        builder = SingleMethodMasterTemplateBuilder(classification, 
            BaseMasterTemplateBuilder.match_prod_code_with_regex)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks, family_and_model_len)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(match_result.is_match, 'There should be a match for a product code with dashes')
        self.assertEqual(match_result.match_value, expected_match_value)
    
    def testAlternateProdCodeMatchHavingADash(self):
        classification = '+a-an!xn'
        blocks = ['+','DSC','-','V','100',' / ','X','100']
        family_and_model_len = len( 'DSC-V100 / X100' )
        product_desc = 'DSC-X100'
        extra_prod_details = 'V-100'
        
        expected_match_value \
            = BaseMasterTemplateBuilder.alt_prod_code_having_dash_with_regex_value_func_on_prod_desc.evaluate( \
                len('DSC-X100'), family_and_model_len, is_after_sep = False) \
            + BaseMasterTemplateBuilder.model_word_with_regex_value_func_on_prod_details.evaluate( \
                len('V-100'), family_and_model_len, is_after_sep = False)
        
        builder = SingleMethodMasterTemplateBuilder(classification, 
            BaseMasterTemplateBuilder.match_prod_code_with_regex)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks, family_and_model_len)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(match_result.is_match, 'There should be a match for an alternate product code with dashes')
        self.assertEqual(match_result.match_value, expected_match_value)
    
    def testProdCodeMatchWithNoDash(self):
        classification = 'a+a_an'
        blocks = ['EasyShare','+','Mini',' ','M','200']
        family_and_model_len = len('EasyShareMini M200')
        product_desc = 'EasyShare M-200'
        extra_prod_details = 'Mini M200'
        
        expected_match_value \
            = BaseMasterTemplateBuilder.prod_code_having_no_dash_with_regex_value_func_on_prod_desc.evaluate( \
                len('M-200'), family_and_model_len, is_after_sep = False) \
            + BaseMasterTemplateBuilder.family_word_with_regex_value_func_on_prod_desc.evaluate( \
                len('EasyShare'), family_and_model_len, is_after_sep = False) \
            + BaseMasterTemplateBuilder.model_word_with_regex_value_func_on_prod_details.evaluate( \
                len('Mini'), family_and_model_len, is_after_sep = False) \
            + BaseMasterTemplateBuilder.prod_code_having_no_dash_with_regex_value_func_on_prod_details.evaluate( \
                len('M200'), family_and_model_len, is_after_sep = False)
        
        builder = SingleMethodMasterTemplateBuilder(classification, 
            BaseMasterTemplateBuilder.match_prod_code_with_regex)
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks, family_and_model_len)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(match_result.is_match, 'There should be a match for a product code with no dashes')
        self.assertEqual(match_result.match_value, expected_match_value)
    
    def testProdCodeMatchIfFollowedByAPercentSymbol(self):
        product_desc = 'Olympus - E 30 - Appareil Photo Numérique Reflex (Boîtier nu) - AF 11points Visée 100% - Écran LCD 2,5'
        extra_prod_details = ''
        
        classification = '+a-n_c'
        blocks = ['+','E','-','100',' ','RS']
        family_and_model_len = len('E-100 RS')
        builder = MasterTemplateBuilder(classification)
        
        master_tpl = builder.build()
        engine = master_tpl.generate(blocks, family_and_model_len)
        match_result = engine.try_match_listing(product_desc, extra_prod_details)
        self.assert_(not match_result.is_match, u'There should be no match to the E-100 RS for a Visée 100%')
    
class MultipleCodesInProductDescTestCase(unittest.TestCase):
    
    def testProdCodeMatchAfterSlash(self):
        product_desc = 'Canon T2I / 550D 29 Piece Pro Deluxe Kit'
        extra_prod_details = ''
        
        classification_1 = 'a+na'
        blocks_1 = ['EOS','+','550','D']
        family_and_model_len_1 = len('EOS550D')
        builder_1 = MasterTemplateBuilder(classification_1)
        
        master_tpl_1 = builder_1.build()
        engine_1 = master_tpl_1.generate(blocks_1, family_and_model_len_1)
        match_result_1 = engine_1.try_match_listing(product_desc, extra_prod_details)
        self.assert_(match_result_1.is_match, 'There should be a match for the EOS 550D product')
        self.assertEqual(match_result_1.description, BaseMasterTemplateBuilder.prod_code_having_no_dash_with_regex_desc)
        match_value_1 = match_result_1.match_value
        
        classification_2 = 'a+ana'
        blocks_2 = ['Rebel','+','T','2','i']
        family_and_model_len_2 = len('RebelT2i')
        builder_2 = MasterTemplateBuilder(classification_2)
        master_tpl_2 = builder_2.build()
        engine_2 = master_tpl_2.generate(blocks_2, family_and_model_len_2)
        match_result_2 = engine_2.try_match_listing(product_desc, extra_prod_details)
        self.assert_(match_result_2.is_match, 'There should be a match for the Rebel T2i product')
        self.assertEqual(match_result_2.description, BaseMasterTemplateBuilder.prod_code_having_no_dash_with_regex_desc)
        match_value_2 = match_result_2.match_value
        
        self.assert_(match_value_1 < match_value_2, 'The Rebel T2i should be the higher value match as it precedes the slash')
    
    def testProdCodeMatchAfterBracket(self):
        product_desc = 'Canon EOS 550D (European EOS Rebel T2i) 18 MP CMOS APS-C Digital SLR Camera'
        extra_prod_details = ''
        
        classification_1 = 'a+na'
        blocks_1 = ['EOS','+','550','D']
        family_and_model_len_1 = len('EOS550D')
        builder_1 = MasterTemplateBuilder(classification_1)
        
        master_tpl_1 = builder_1.build()
        engine_1 = master_tpl_1.generate(blocks_1, family_and_model_len_1)
        match_result_1 = engine_1.try_match_listing(product_desc, extra_prod_details)
        self.assert_(match_result_1.is_match, 'There should be a match for the EOS 550D product')
        self.assertEqual(match_result_1.description, BaseMasterTemplateBuilder.all_of_family_and_model_with_regex_desc)
        match_value_1 = match_result_1.match_value
        
        classification_2 = 'a+ana'
        blocks_2 = ['Rebel','+','T','2','i']
        family_and_model_len_2 = len('RebelT2i')
        builder_2 = MasterTemplateBuilder(classification_2)
        master_tpl_2 = builder_2.build()
        engine_2 = master_tpl_2.generate(blocks_2, family_and_model_len_2)
        match_result_2 = engine_2.try_match_listing(product_desc, extra_prod_details)
        self.assert_(match_result_2.is_match, 'There should be a match for the Rebel T2i product')
        self.assertEqual(match_result_2.description, BaseMasterTemplateBuilder.all_of_family_and_model_with_regex_desc)
        match_value_2 = match_result_2.match_value
        
        self.assert_(match_value_1 > match_value_2, 'The Canon 550D should be the higher value match as it precedes the opening round bracket')
        
        
# Run unit tests from the command line:        
if __name__ == '__main__':
    unittest.main()
