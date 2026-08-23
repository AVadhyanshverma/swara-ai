import re
import math
from decimal import Decimal, getcontext, InvalidOperation
from typing import List, Union
from enum import Enum, auto

class TokenType(Enum):
    NUMBER = auto()
    OPERATOR = auto()
    LPAREN = auto()
    RPAREN = auto()
    IDENTIFIER = auto()
    COMMA = auto()
    EOF = auto()

class Token:
    def __init__(self, type_: TokenType, value: Union[str, Decimal, None], pos: int):
        self.type = type_
        self.value = value
        self.pos = pos

    def __repr__(self):
        return f"Token({self.type.name}, {self.value}, pos={self.pos})"

def raise_error(expr: str, pos: int, msg: str):
    show_expr = expr
    show_pos = pos
    if len(expr) > 60:
        start = max(0, pos - 30)
        end = min(len(expr), pos + 30)
        prefix = "... " if start > 0 else ""
        suffix = " ..." if end < len(expr) else ""
        show_expr = prefix + expr[start:end] + suffix
        show_pos = pos - start + len(prefix)
    
    pointer = " " * show_pos + "^"
    raise ValueError(f"{msg} at position {pos}:\n{show_expr}\n{pointer}")

class PerfectCalculator:
    """
    High-precision arithmetic evaluator.
    
    Supports: +  -  *  /  //  %  **  and nested parentheses.
    Functions: sqrt, exp, ln, log10, sin, cos, tan, abs, max, min, log
    Constants: pi, e
    """

    def __init__(self, precision: int = 100):
        getcontext().prec = precision

        self.operators = {
            '+':  {'prec': 1, 'assoc': 'L', 'func': lambda a, b: a + b},
            '-':  {'prec': 1, 'assoc': 'L', 'func': lambda a, b: a - b},
            '*':  {'prec': 2, 'assoc': 'L', 'func': lambda a, b: a * b},
            '/':  {'prec': 2, 'assoc': 'L', 'func': lambda a, b: a / b},
            '//': {'prec': 2, 'assoc': 'L', 'func': lambda a, b: a // b},
            '%':  {'prec': 2, 'assoc': 'L', 'func': lambda a, b: a % b},
            '**': {'prec': 4, 'assoc': 'R', 'func': lambda a, b: a ** b},
        }
        self.unary_prec = 3 

        self.constants = {
            'pi': Decimal(str(math.pi)),
            'e': Decimal(str(math.e))
        }
        
        self.functions = {
            'sqrt': lambda x: x.sqrt(),
            'exp': lambda x: x.exp(),
            'ln': lambda x: x.ln(),
            'log10': lambda x: x.log10(),
            'sin': lambda x: Decimal(str(math.sin(float(x)))),
            'cos': lambda x: Decimal(str(math.cos(float(x)))),
            'tan': lambda x: Decimal(str(math.tan(float(x)))),
            'abs': lambda x: abs(x),
        }
        
        self.functions_2arg = {
            'log': lambda x, base: x.ln() / base.ln() if base != 1 else Decimal('NaN'),
            'max': lambda a, b: max(a, b),
            'min': lambda a, b: min(a, b),
        }

        self.token_regex = re.compile(r'''
            (?P<SPACE>\s+) |
            (?P<NUMBER>\d+\.\d+|\.\d+|\d+) |
            (?P<OPERATOR>\*\*|//|[+\-*/%]) |
            (?P<LPAREN>\() |
            (?P<RPAREN>\)) |
            (?P<COMMA>,) |
            (?P<IDENTIFIER>[a-zA-Z_][a-zA-Z0-9_]*) |
            (?P<MISMATCH>.)
        ''', re.VERBOSE)

    def tokenize(self, expr: str) -> List[Token]:
        tokens = []
        for match in self.token_regex.finditer(expr):
            kind = match.lastgroup
            value = match.group()
            pos = match.start()
            
            if kind == 'SPACE':
                continue
            elif kind == 'NUMBER':
                try:
                    num = Decimal(value)
                    tokens.append(Token(TokenType.NUMBER, num, pos))
                except InvalidOperation:
                    raise_error(expr, pos, f"Invalid number '{value}'")
            elif kind == 'OPERATOR':
                tokens.append(Token(TokenType.OPERATOR, value, pos))
            elif kind == 'LPAREN':
                tokens.append(Token(TokenType.LPAREN, '(', pos))
            elif kind == 'RPAREN':
                tokens.append(Token(TokenType.RPAREN, ')', pos))
            elif kind == 'COMMA':
                tokens.append(Token(TokenType.COMMA, ',', pos))
            elif kind == 'IDENTIFIER':
                tokens.append(Token(TokenType.IDENTIFIER, value, pos))
            elif kind == 'MISMATCH':
                raise_error(expr, pos, f"Invalid character '{value}'")
                
        tokens.append(Token(TokenType.EOF, None, len(expr)))
        return tokens

    def evaluate(self, expr: str) -> Decimal:
        tokens = self.tokenize(expr)
        values: List[Decimal] = []
        ops: List[Token] = [] 

        def apply_op(op_token: Token):
            op = op_token.value
            if op == 'u-':
                if not values:
                    raise_error(expr, op_token.pos, "Missing operand for unary minus")
                values.append(-values.pop())
                return
                
            if op in self.functions:
                if not values:
                    raise_error(expr, op_token.pos, f"Missing argument for function '{op}'")
                a = values.pop()
                try:
                    res = self.functions[op](a)
                    values.append(res)
                except Exception as e:
                    raise_error(expr, op_token.pos, f"Math error in '{op}': {e}")
                return
                
            if op in self.functions_2arg:
                if len(values) < 2:
                    raise_error(expr, op_token.pos, f"Missing arguments for function '{op}'")
                b = values.pop()
                a = values.pop()
                try:
                    res = self.functions_2arg[op](a, b)
                    values.append(res)
                except Exception as e:
                    raise_error(expr, op_token.pos, f"Math error in '{op}': {e}")
                return

            if len(values) < 2:
                raise_error(expr, op_token.pos, f"Missing operands for operator '{op}'")
            b = values.pop()
            a = values.pop()
            try:
                values.append(self.operators[op]['func'](a, b))
            except ZeroDivisionError:
                raise_error(expr, op_token.pos, "Division by zero")

        def should_pop(op2_str: str) -> bool:
            if not ops:
                return False
            op1_str = ops[-1].value
            if op1_str == '(':
                return False
                
            if op1_str in self.functions or op1_str in self.functions_2arg:
                return False

            p1 = self.unary_prec if op1_str == 'u-' else self.operators[op1_str]['prec']
            p2 = self.operators[op2_str]['prec']

            if p1 > p2:
                return True
            if p1 == p2 and self.operators[op2_str]['assoc'] == 'L':
                return True
            return False

        for idx, tok in enumerate(tokens):
            if tok.type == TokenType.EOF:
                break
                
            if tok.type == TokenType.NUMBER:
                values.append(tok.value)

            elif tok.type == TokenType.IDENTIFIER:
                name = tok.value
                if name in self.constants:
                    values.append(self.constants[name])
                elif name in self.functions or name in self.functions_2arg:
                    ops.append(tok)
                else:
                    raise_error(expr, tok.pos, f"Unknown identifier '{name}'")

            elif tok.type == TokenType.LPAREN:
                ops.append(tok)
                
            elif tok.type == TokenType.COMMA:
                while ops and ops[-1].value != '(':
                    apply_op(ops.pop())
                if not ops:
                    raise_error(expr, tok.pos, "Comma outside function arguments")
                    
            elif tok.type == TokenType.RPAREN:
                while ops and ops[-1].value != '(':
                    apply_op(ops.pop())
                if not ops:
                    raise_error(expr, tok.pos, "Mismatched closing parenthesis")
                ops.pop() 
                
                if ops and (ops[-1].value in self.functions or ops[-1].value in self.functions_2arg):
                    apply_op(ops.pop())

            elif tok.type == TokenType.OPERATOR:
                op = tok.value
                is_unary = (op == '-') and (
                    idx == 0 or
                    tokens[idx - 1].type in (TokenType.OPERATOR, TokenType.LPAREN, TokenType.COMMA)
                )

                if is_unary:
                    ops.append(Token(TokenType.OPERATOR, 'u-', tok.pos))
                else:
                    while should_pop(op):
                        apply_op(ops.pop())
                    ops.append(tok)

        while ops:
            top = ops.pop()
            if top.value == '(':
                raise_error(expr, top.pos, "Mismatched opening parenthesis")
            apply_op(top)

        if len(values) != 1:
            if not values:
                return Decimal(0)
            raise ValueError(f"Invalid expression layout: remaining values {values}")
            
        return values[0]
