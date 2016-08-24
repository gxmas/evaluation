""" Automatically generate unit tests
""" 
from xml_generator import create_xml 

UNIT_TEST_TEMPLATE = """
BOOST_AUTO_TEST_CASE(Test_NUM)
{
INPUT
auto context = EvaluationParser::CreateFromFile("FNAME");
SET_VARIABLES
CHECKS
}
"""
import math

MATH_REPLACE = {
        'exp': 'math.exp'
        }

def get_xml_fname(test_id):
    return 'test_%s.xml' % test_id

def replace_in_expression(expr, variable_values):
    for variable, value in variable_values.items():
        expr = expr.replace(variable, str(value))
    return expr

class EvaluationTest:
    def __init__(self, expressions, variable_values = None):
        self.expressions = expressions
        self.variable_values = variable_values 
    def generate_test(self, test_id):
        # let's get the values
        # 0. Generate the xml
        create_xml(self.expressions, get_xml_fname(test_id), False)
        # 1. Compute values
        self.compute_values() 
        # 2. Generate unit test
        return self.generate_code(test_id)

    def generate_code(self, test_id):
        result = UNIT_TEST_TEMPLATE
        replacements = { 'NUM': str(test_id) }
        replacements['FNAME'] = get_xml_fname(test_id)
        replacements['INPUT'] = '\n'.join(['// %s' % expr for expr in self.expressions])
        replacements['SET_VARIABLES'] = '\n'.join(['context.setVariable("%s", %s);' % (variable, value) for variable, value in
                self.variable_values.items()]) 
        replacements['CHECKS'] = '\n'.join(['BOOST_TEST(%s == context.calc("%s"));' % (value, name) for name, value in
            self.new_values.items()])
        result = replace_in_expression(result, replacements)
        return result

    def compute_values(self): 
        new_expressions = [replace_in_expression(expression, self.variable_values) for expression in self.expressions]
        new_expressions = [replace_in_expression(expression, MATH_REPLACE) for expression in new_expressions]
        self.new_values = {}
        for expr in new_expressions:
            name, expression = [s.strip() for s in expr.split('=')]
            expression = replace_in_expression(expression, self.new_values)
            self.new_values[name] = eval(expression)

BOOST_TEST_TEMPLATE = """
#define BOOST_TEST_MODULE EvaluationTests
#include <boost/test/unit_test.hpp>

#include "evaluation.h"
#include "parser.h"

MY_TESTS
"""


class UnitTestGenerator:
    def __init__(self):
        self.num_test = 0
        self.tests = []
    def add_test(self, expressions, variables):
        self.tests.append(EvaluationTest(expressions, variables).generate_test(self.num_test))
        self.num_test += 1
    
    def generate_unit_test(self, test_fname):
        tests = {'MY_TESTS': '\n'.join(self.tests)}
        final = replace_in_expression(BOOST_TEST_TEMPLATE, tests)
        with open(test_fname, 'w') as f:
            f.write(final)

#####################################################################

gen = UnitTestGenerator()
gen.add_test(['X=3', 'Y=X+1+2+z'], {'z': 0.5})
gen.add_test(['X=exp(y)', 'Z=1*X'], {'y': 0.5})
gen.generate_unit_test('test/automatically_generated.cpp')
