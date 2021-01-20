from a2ml.api.utils.roi_calc import Lexer, Parser

def test_lexer_bike_rental_investment():
    lexer = Lexer("2*max(P-10,0)")
    res = lexer.all_tokens()

    assert ['2', '*', 'max', '(', 'P', '-', '10', ',', '0', ')'] == res

def test_lexer_bike_rental_investment_with_spaces():
    lexer = Lexer("2 * max(P - 10, 0)")
    res = lexer.all_tokens()

    assert ['2', '*', 'max', '(', 'P', '-', '10', ',', '0', ')'] == res

def test_lexer_options_app_revenue():
    lexer = Lexer("@sum((1 + A) * 100)")
    res = lexer.all_tokens()

    assert ['@', 'sum', '(', '(', '1', '+', 'A', ')', '*', '100', ')'] == res

def test_parser_bike_rental_investment():
    expression = "2 * max(P - 10, 0)"
    const_values = { "P": 20, "A": 10 }
    func_values = { "max": max }
    parser = Parser(expression, const_values=const_values, func_values=func_values)
    tree = parser.parse()

    assert 20 == tree.evaluate()
