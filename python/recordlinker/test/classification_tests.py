import unittest
import re
from recordlinker.classification import *

class MatchingRuleStub(MatchingRule):
    def __init__(self, text_to_find, desc_value, details_value):
        self.to_find = text_to_find
        self.product_desc_value = desc_value
        self.product_details_value = details_value
    
    def try_match(self, product_desc, extra_prod_details = None):
        if product_desc.find(self.to_find) != -1:
            return True, self.product_desc_value
        if extra_prod_details.find(self.to_find) != -1:
            return True, self.product_details_value
        return False, 0

class ListingMatcherTestCase(unittest.TestCase):
    def setUp(self):
        primary_rule_1 = MatchingRuleStub('Sample', 1000, 500)
        secondary_rule_1_1 = MatchingRuleStub('Extra1', 100, 10)
        secondary_rule_1_2 = MatchingRuleStub('Extra2', 50, 5)
        secondary_rule_1_3 = MatchingRuleStub('Extra3', 20, 2)
        self.listing_matcher_1 = ListingMatcher('ManySecondaryRules', primary_rule_1, [secondary_rule_1_1, secondary_rule_1_2, secondary_rule_1_3])
        
        primary_rule_2 = MatchingRuleStub('Tester', 101, 21)
        secondary_rule_2_1 = MatchingRuleStub('Test', 41, 11)
        self.listing_matcher_2 = ListingMatcher('SingleSecondaryRule', primary_rule_2, [secondary_rule_2_1])
        
        primary_rule_3 = MatchingRuleStub('Taster', 82, 32)
        self.listing_matcher_3 = ListingMatcher('PrimaryOnly', primary_rule_3, [])
        
        self.listing_matchers = [self.listing_matcher_1, self.listing_matcher_2, self.listing_matcher_3]
        
        self.engine = MatchingEngine()
    
    # Test MatchingEngine and ListingMatcher by using the MatchingRuleStub implementation instead of an actual matching rule:
    def testWithNoMatchers(self):
        is_match, match_value, match_desc = self.engine.try_match_listing('some_product_desc', 'some_extra_prod_details', [])
        self.assertEqual(is_match, False, 'There should be no match when the matchers list is empty')
        self.assertEqual(match_value, 0, 'The value should be zero when the matchers list is empty')
        self.assertEqual(match_desc, '', 'The rule description should be empty when the matchers list is empty')
    
    def testWithSingleMatcherNotMatching(self):
        is_match, match_value, match_desc = self.engine.try_match_listing('some_product_desc', 'some_extra_prod_details', [self.listing_matcher_1])
        self.assertEqual(is_match, False, 'There should be no match when the single matcher does not match')
        self.assertEqual(match_value, 0, 'The value should be zero when the single matcher does not match')
        self.assertEqual(match_desc, '', 'The rule description should be empty when the single matcher does not match')
    
    def testWithSingleMatcherMatchingProductDesc(self):
        is_match, match_value, match_desc = self.engine.try_match_listing('Sample', 'some_extra_prod_details', [self.listing_matcher_1])
        self.assertEqual(is_match, True, "There should be a match when the single matcher's product desc does match")
        self.assertEqual(match_value, 1000, 'The value should be 1000 when the single matcher matches the first product desc')
        self.assertEqual(match_desc, 'ManySecondaryRules', 'The rule description should be "ManySecondaryRules" when the single matcher matches the rule')

    def testWithSingleMatcherAndMultipleMatchingRules(self):
        is_match, match_value, match_desc = self.engine.try_match_listing('Sample Extra2', 'Extra1 Extra3', [self.listing_matcher_1])
        self.assertEqual(is_match, True, "There should be a match when the single matcher's product desc matches the primary text")
        self.assertEqual(match_value, 1062)
        self.assertEqual(match_desc, 'ManySecondaryRules')

    def testThatAMatchRuleIsOnlySuccessfulOnEitherProductDescOrDetails(self):
        is_match, match_value, match_desc = self.engine.try_match_listing('Sample Extra2', 'Extra2', [self.listing_matcher_1])
        self.assertEqual(is_match, True, "There should be a match when the single matcher's product desc matches the primary text")
        self.assertEqual(match_value, 1050)
        self.assertEqual(match_desc, 'ManySecondaryRules')

    def testWithSingleMatcherAndMultipleMatchingRulesButNoPrimaryMatch(self):
        is_match, match_value, match_desc = self.engine.try_match_listing('Extra2', 'Extra1 Extra3', [self.listing_matcher_1])
        self.assertEqual(is_match, False)
        self.assertEqual(match_value, 0)
        self.assertEqual(match_desc, '')
    
    def testWithMultipleMatchers(self):
        'Note: both the second and third matchers should match, but only the second should be used'
        is_match, match_value, match_desc = self.engine.try_match_listing('Taster Tester', 'Rule', self.listing_matchers)
        self.assertEqual(is_match, True)
        self.assertEqual(match_value, 142)
        self.assertEqual(match_desc, 'SingleSecondaryRule')

        
class RegexMatchingRuleTestCase(unittest.TestCase):
    def setUp(self):
        self.regex = re.compile('DSC\-?HX100v', flags=re.IGNORECASE)
        self.product_code = 'DSC-HX100v'
        self.match_length = len(self.product_code)
        self.value_on_desc = 1000000
        self.value_on_details = 1000
        self.value_on_desc_per_char = 10
        self.value_on_details_per_char = 1
    
    def run_rule(self, product_desc, extra_prod_details, expected_value, expected_to_match, must_match_on_desc):
        rule = RegexMatchingRule(self.regex, self.value_on_desc, self.value_on_details, 
            self.value_on_desc_per_char, self.value_on_details_per_char, must_match_on_desc)
        is_match, match_value = rule.try_match(product_desc, extra_prod_details)
        self.assertEqual(is_match, expected_to_match)
        self.assertEqual(match_value, expected_value)
    
    def testRegexMatchingRuleOnProductDesc(self):
        product_desc = 'Cybershot DSC-HX100v'
        extra_prod_details = ''
        expected_value = self.value_on_desc + self.match_length * self.value_on_desc_per_char
        self.run_rule(product_desc, extra_prod_details, expected_value, expected_to_match = True, must_match_on_desc = True)
    
    def testRegexMatchingRuleOnProductDetailsWhenMustMatchOnDescTrue(self):
        product_desc = 'Cybershot'
        extra_prod_details = 'DSC-HX100v'
        self.run_rule(product_desc, extra_prod_details, expected_value = 0, expected_to_match = False, must_match_on_desc = True)
        
    def testRegexMatchingRuleOnProductDetailsWhenMustMatchOnDescFalse(self):
        product_desc = 'Cybershot'
        extra_prod_details = 'DSC-HX100v'
        expected_value = self.value_on_details + self.match_length * self.value_on_details_per_char
        self.run_rule(product_desc, extra_prod_details, expected_value, expected_to_match = True, must_match_on_desc = False)
        
    def testRegexMatchingRuleOnNoMatch(self):
        product_desc = 'Cybershot NO-HX100'
        extra_prod_details = ''
        self.run_rule(product_desc, extra_prod_details, expected_value = 0, expected_to_match = False, must_match_on_desc = False)
        

# Run unit tests from the command line:        
if __name__ == '__main__':
    unittest.main()
