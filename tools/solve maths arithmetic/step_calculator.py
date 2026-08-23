import re
import math
from decimal import Decimal, getcontext, InvalidOperation
from typing import List, Union, Dict, Any
from enum import Enum, auto
from dataclasses import dataclass

class TokenType(Enum):
    NUMBER = auto()
    OPERATOR = auto()
    LPAREN = auto()
    RPAREN = auto()
    IDENTIFIER = auto()
    COMMA = auto()
    EOF = auto()

@dataclass
class Token:
    type: TokenType
    value: Union[str, Decimal, None]
    pos: int

@dataclass
class NumNode:
    value: Decimal
@dataclass
class UnaryNode:
    op: str
    arg: Any
@dataclass
class BinNode:
    op: str
    left: Any
    right: Any
@dataclass
class FuncNode:
    name: str
    args: List[Any]

@dataclass
class Step:
    step_num: int
    expression: str
    result: Decimal
    description: str
    marks: int

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

class PerfectStepCalculator:
    """
    AST-based evaluator that tracks steps for educational / grading purposes.
    Maintains high precision and handles advanced functions exactly like PerfectCalculator.
    """
    def __init__(self, precision: int = 100):
        getcontext().prec = precision
        
        self.operators = {
            '+':  {'prec': 1, 'assoc': 'L', 'func': lambda a,b: a+b},
            '-':  {'prec': 1, 'assoc': 'L', 'func': lambda a,b: a-b},
            '*':  {'prec': 2, 'assoc': 'L', 'func': lambda a,b: a*b},
            '/':  {'prec': 2, 'assoc': 'L', 'func': lambda a,b: a/b},
            '//': {'prec': 2, 'assoc': 'L', 'func': lambda a,b: a//b},
            '%':  {'prec': 2, 'assoc': 'L', 'func': lambda a,b: a%b},
            '**': {'prec': 4, 'assoc': 'R', 'func': lambda a,b: a**b},
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

        # Lightning fast Regex lexer
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
                    tokens.append(Token(TokenType.NUMBER, Decimal(value), pos))
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

    def build_ast(self, expr: str, tokens: List[Token]):
        values = []
        ops = []
        
        def apply_op(op_token: Token):
            op = op_token.value
            if op == 'u-':
                if not values: raise_error(expr, op_token.pos, "Missing operand for unary '-'")
                values.append(UnaryNode('-', values.pop()))
                return
            if op in self.functions:
                if not values: raise_error(expr, op_token.pos, f"Missing arg for '{op}'")
                values.append(FuncNode(op, [values.pop()]))
                return
            if op in self.functions_2arg:
                if len(values) < 2: raise_error(expr, op_token.pos, f"Missing args for '{op}'")
                b = values.pop(); a = values.pop()
                values.append(FuncNode(op, [a, b]))
                return
            if len(values) < 2: raise_error(expr, op_token.pos, f"Missing operands for '{op}'")
            b = values.pop(); a = values.pop()
            values.append(BinNode(op, a, b))

        def should_pop(op2_str: str) -> bool:
            if not ops: return False
            op1_str = ops[-1].value
            if op1_str == '(': return False
            if op1_str in self.functions or op1_str in self.functions_2arg: return False
            p1 = self.unary_prec if op1_str == 'u-' else self.operators[op1_str]['prec']
            p2 = self.operators[op2_str]['prec']
            if p1 > p2: return True
            if p1 == p2 and self.operators[op2_str]['assoc'] == 'L': return True
            return False

        for idx, tok in enumerate(tokens):
            if tok.type == TokenType.EOF: break
            elif tok.type == TokenType.NUMBER: values.append(NumNode(tok.value))
            elif tok.type == TokenType.IDENTIFIER:
                name = tok.value
                if name in self.constants:
                    values.append(NumNode(self.constants[name]))
                elif name in self.functions or name in self.functions_2arg:
                    ops.append(tok)
                else:
                    raise_error(expr, tok.pos, f"Unknown identifier '{name}'")
            elif tok.type == TokenType.LPAREN: ops.append(tok)
            elif tok.type == TokenType.COMMA:
                while ops and ops[-1].value != '(': apply_op(ops.pop())
                if not ops: raise_error(expr, tok.pos, "Comma outside args")
            elif tok.type == TokenType.RPAREN:
                while ops and ops[-1].value != '(': apply_op(ops.pop())
                if not ops: raise_error(expr, tok.pos, "Mismatched closing parenthesis")
                ops.pop() 
                if ops and (ops[-1].value in self.functions or ops[-1].value in self.functions_2arg):
                    apply_op(ops.pop())
            elif tok.type == TokenType.OPERATOR:
                op = tok.value
                is_unary = (op == '-') and (idx == 0 or tokens[idx-1].type in (TokenType.OPERATOR, TokenType.LPAREN, TokenType.COMMA))
                if is_unary: ops.append(Token(TokenType.OPERATOR, 'u-', tok.pos))
                else:
                    while should_pop(op): apply_op(ops.pop())
                    ops.append(tok)
                    
        while ops:
            top = ops.pop()
            if top.value == '(': raise_error(expr, top.pos, "Mismatched opening parenthesis")
            apply_op(top)
            
        if not values: return NumNode(Decimal(0))
        if len(values) > 1: raise ValueError(f"Invalid expression layout: too many disconnected operations.")
        return values[0]

    def eval_ast(self, node, steps_list) -> Decimal:
        if isinstance(node, NumNode): return node.value
        
        if isinstance(node, UnaryNode):
            v = self.eval_ast(node.arg, steps_list)
            res = -v
            steps_list.append(Step(len(steps_list)+1, f"-{v}", res, "Unary negation", 1))
            return res
            
        if isinstance(node, FuncNode):
            args_eval = [self.eval_ast(arg, steps_list) for arg in node.args]
            if node.name in self.functions: res = self.functions[node.name](args_eval[0])
            else: res = self.functions_2arg[node.name](args_eval[0], args_eval[1])
            
            args_str = ", ".join(str(a) for a in args_eval)
            steps_list.append(Step(len(steps_list)+1, f"{node.name}({args_str})", res, f"{node.name} function", 1))
            return res

        # BinNode
        l = self.eval_ast(node.left, steps_list)
        r = self.eval_ast(node.right, steps_list)
        res = self.operators[node.op]['func'](l, r)
        steps_list.append(Step(len(steps_list)+1, f"{l} {node.op} {r}", res, f"{node.op} operation", 1))
        return res

    def evaluate(self, expr: str) -> Dict[str, Any]:
        """Returns full step-by-step resolution."""
        steps_list = []
        ast = self.build_ast(expr, self.tokenize(expr))
        final = self.eval_ast(ast, steps_list)
        
        return {
            "expression": expr,
            "final_answer": final,
            "steps": [
                {
                    "step_num": s.step_num,
                    "expression": s.expression,
                    "result": str(s.result),
                    "description": s.description,
                    "marks": s.marks
                } for s in steps_list
            ],
            "total_marks": sum(s.marks for s in steps_list) + 2,
            "marks_breakdown": {"working": sum(s.marks for s in steps_list), "final": 2}
        }

    def _quick_eval(self, node) -> Decimal:
        if isinstance(node, NumNode): return node.value
        if isinstance(node, UnaryNode): return -self._quick_eval(node.arg)
        if isinstance(node, FuncNode):
            args_eval = [self._quick_eval(arg) for arg in node.args]
            if node.name in self.functions: return self.functions[node.name](args_eval[0])
            return self.functions_2arg[node.name](args_eval[0], args_eval[1])
        return self.operators[node.op]['func'](self._quick_eval(node.left), self._quick_eval(node.right))

    def mark_student(self, expr: str, student_steps: List[str]) -> Dict[str, Any]:
        """Grades a student's working."""
        correct = self.evaluate(expr)
        marked, earned = [], 0
        possible = len(correct["steps"]) + 2
        
        for i, text in enumerate(student_steps):
            text = text.strip()
            eq = text.find('=')
            if eq == -1:
                marked.append({"step": i+1, "status": "invalid", "marks": 0, "feedback": "Missing '='" })
                continue
            try:
                # Use our robust builder to eval student's left side
                student_expr = text[:eq].strip()
                ast = self.build_ast(student_expr, self.tokenize(student_expr))
                val = self._quick_eval(ast)
                given = Decimal(text[eq+1:].strip())
                if val == given:
                    earned += 1
                    marked.append({"step": i+1, "status": "correct", "marks": 1, "feedback": f"{student_expr} = {val}"})
                else:
                    marked.append({"step": i+1, "status": "wrong", "marks": 0, "feedback": f"Math error: Should be {val}, not {given}"})
            except Exception as e:
                marked.append({"step": i+1, "status": "error", "marks": 0, "feedback": f"Parse error: {str(e)}"})
                
        return {
            "expression": expr,
            "correct_answer": str(correct["final_answer"]),
            "student_marked_steps": marked,
            "earned_marks": earned,
            "total_possible": possible,
            "percentage": round((earned/possible)*100, 1) if possible else 0,
            "correct_working": correct["steps"]
        }
