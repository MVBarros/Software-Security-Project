#!/bin/python3

import json
import sys
import copy

class Statement:
    '''
        Statement := Expression | If | If Else | While | Identifier = Expression
    '''
    @staticmethod
    def parse_from_node(node: dict):
        pass

    def eval(self, variables, patterns):
        pass


class Expression(Statement):
    '''
        In Python every Expression can be a Statement
        Expression := Literal | Identifier | Expression Operator Expression | not Expression | Function(Args) | Expression BooleanOperator Expression
        Operator := + | - | / | * | % | or | ** | // | == | and (? what else)
        BooleanOperator := and | or
    '''
    @staticmethod
    def parse_from_node(node: dict):
        pass

    def eval(self, variables, patterns):
        pass

class Identifier(Expression):
    '''
        An Identifier is a program variable id
    '''
    def __init__(self, name: str, lineno: int):
        self.name = name
        self.lineno = lineno

    def __repr__(self):
        return f"{self.name}"

    @staticmethod
    def parse_from_node(node: dict):
        name = node['id']
        return Identifier(name, node["lineno"])

    @staticmethod
    def new_variable_eval(name, patterns):
        new_var = []
        for vuln_name in patterns.keys():
            new_var.append({"vuln": vuln_name, "source": name, "sanitizer": None})
        return new_var

    def eval(self, variables, patterns):
        if not self.name in variables:
            variables[self.name] = Identifier.new_variable_eval( self.name, patterns)
        return copy.deepcopy(variables[self.name])

class Literal(Expression):
    '''
        A literal is a constant value (like 3 or "Hello world")
        Literal := Num | Str
    '''
    def __init__(self, val, lineno: int):
        self.val = val
        self.lineno = lineno

    def __repr__(self):
        return f"{self.val}"

    @staticmethod
    def parse_from_node(node: dict):
        ast_type = node['ast_type']
        if ast_type == 'Str':
            return Literal(node['s'], node["lineno"])
        if ast_type == 'Num':
            return Literal(node['n']['n'], node["lineno"])
        if ast_type == 'NameConstant':
            return Literal(node["value"], node["lineno"])
        #should never happen
        return None

    def eval(self, variables, patterns):
        return []

class AssignExpression(Statement):
    def __init__(self, left_val: Identifier, right_val: Expression, lineno: int):
        self.left_val = left_val
        self.right_val = right_val
        self.lineno = lineno

    def __repr__(self):
        return f"{self.left_val} := {self.right_val}"

    @staticmethod
    def parse_from_node(node: dict):
        left_val = parse_node_expr_value(node['targets'][0])
        right_val = parse_node_expr_value(node['value'])
        return AssignExpression(left_val, right_val, node["lineno"])

    def eval(self, variables, patterns):
        variables[self.left_val.name] = self.right_val.eval(variables, patterns)
        return copy.deepcopy(variables[self.left_val.name])

class DoubleExpression(Expression):
    '''
        A DoubleExpression is an operation of two or more expressions
    '''
    def __init__(self, left_val: Expression, right_val: Expression, operator: str, lineno: int):
        self.left_val = left_val
        self.right_val = right_val
        self.operator = operator
        self.lineno = lineno


    def __repr__(self):
        return f"{self.left_val} {self.operator} {self.right_val}"

    @staticmethod
    def parse_from_node(node: dict):
        left_val = parse_node_expr_value(node["left"])
        right_val = parse_node_expr_value(node["right"])
        operator = node["op"]["ast_type"]
        return DoubleExpression(left_val, right_val, operator, node["lineno"])

    def eval(self, variables, patterns):
        return self.left_val.eval(variables, patterns) + self.right_val.eval(variables, patterns)

class AttributeExpression(Expression):
    '''
        A AttributeExpression 
    '''
    def __init__(self, left_val: Expression, right_val: Expression, lineno: int):
        self.left_val = left_val
        self.right_val = right_val
        self.lineno = lineno


    def __repr__(self):
        return f"{self.right_val}.{self.left_val}"

    @staticmethod
    def parse_from_node(node: dict):
        left_val = Identifier(node["attr"], node["lineno"])
        right_val = parse_node_expr_value(node["value"])
        return AttributeExpression(left_val, right_val, node["lineno"])

    def eval(self, variables, patterns):
        return self.left_val.eval(variables, patterns) + self.right_val.eval(variables, patterns)


class BooleanExpression(Expression):
    '''
        A BooleanOperation is an operation of two or more expressions and a boolean operator
    '''
    def __init__(self, left_val: Expression, right_val: Expression, operator: str, lineno: int):
        self.left_val = left_val
        self.right_val = right_val
        self.operator = operator
        self.lineno = lineno


    def __repr__(self):
        return f"{self.left_val} {self.operator} {self.right_val}"

    @staticmethod
    def parse_from_node(node: dict):
        left_val = parse_node_expr_value(node["values"][0])
        right_val = parse_node_expr_value(node["values"][1])
        operator = node["op"]["ast_type"]
        return DoubleExpression(left_val, right_val, operator, node["lineno"])

    def eval(self, variables, patterns):
        return self.left_val.eval(variables, patterns) + self.right_val.eval(variables, patterns)

class UnaryExpression(Expression):
    '''
        UnaryExpression := not Expression
    '''
    def __init__(self, left_operator: str, right_val: Expression, lineno: int):
        self.left_operator = left_operator
        self.right_val = right_val
        self.lineno = lineno

    def __repr__(self):
        return f"{self.left_operator} {self.right_val}"

    @staticmethod
    def parse_from_node(node: dict):
        left_operator = node["op"]["ast_type"]
        right_val = parse_node_expr_value(node["operand"])
        return UnaryExpression(left_operator, right_val, node["lineno"])

    def eval(self, variables, patterns):
        return self.right_val.eval(variables, patterns)

class FunctionCall(Expression):
    '''
    FunctionCall:= name(Args)
    Args := Args , Expression | Expression | Empty
    '''
    def __init__(self, name: str, args: list, lineno: int): #args list of expressions
        self.name = name
        self.lineno = lineno
        self.args = args

    def __repr__(self):
        return f"{self.name}({self.args})"

    @staticmethod
    def parse_from_node(node: dict):
        name = node["func"]["attr" if "attr" in node["func"] else "id"]
        args = [parse_node_expr_value(arg) for arg in node["args"]]
        return FunctionCall(name, args, node["lineno"])

    def get_vulnerabilities(self, patterns):
        vulnerabilities = list()
        for name, vulnerability in patterns.items():
            if self.name in vulnerability.sources:
                vulnerabilities.append({"vuln": name, "source": self.name, "sanitizer": None})
        return vulnerabilities

    def get_sanitizers(self, patterns):
        vulnerabilities = list()
        for name, vulnerability in patterns.items():
            if self.name in vulnerability.sanitizers:
                vulnerabilities.append(name)
        return vulnerabilities

    def get_sinks(self, patterns):
        vulnerabilities = list()
        for name, vulnerability in patterns.items():
            if self.name in vulnerability.sinks:
                vulnerabilities.append(name)
        return vulnerabilities

    def eval(self, variables, patterns):
        vulnerabilities = []
        for arg in self.args:
            vulnerabilities += arg.eval(variables, patterns)

        vulnerabilities += self.get_vulnerabilities(patterns)

        sanitized_vulnerabilities = self.get_sanitizers(patterns)
        for sanitized_vulnerability in sanitized_vulnerabilities:
            for vulnerability in vulnerabilities:
                if vulnerability["vuln"] == sanitized_vulnerability:
                    vulnerability["sanitizer"] = self.name

        for sink in self.get_sinks(patterns):
            for arg in self.args:
                for vulnerability in arg.eval(variables, patterns):
                    if vulnerability["vuln"] == sink:
                        to_print = copy.deepcopy(vulnerability)
                        to_print["sink"] = self.name
                        print(to_print)

        return vulnerabilities

class IfExpression(Statement):
    def __init__(self, cond: Expression, body: list, else_body: list, lineno: int):
        #body, else_body list of statements
        self.cond = cond
        self.body = body
        self.else_body = else_body #if no else else_body should be Empty List
        self.lineno = lineno

    def __repr__(self):
        return f"If {self.cond} then {self.body} else {self.else_body}"

    @staticmethod
    def parse_from_node(node: dict):
        cond = parse_node_expr_value(node["test"])
        body = []
        for sub_node in node["body"]:
            body.append(parse_node(sub_node))
        else_body = []
        for sub_node in node["orelse"]:
            else_body.append(parse_node(sub_node))
        return IfExpression(cond, body, else_body, node["lineno"])

    def eval(self, variables, patterns):
        pass


class WhileExpression(Statement):
    def __init__(self, cond: Expression, body: list, lineno: int): #body: list of statements
        self.cond = cond
        self.body = body
        self.lineno = lineno

    def __repr__(self):
        return f"While {self.cond} do {self.body}"

    @staticmethod
    def parse_from_node(node: dict):
        cond = parse_node_expr_value(node["test"])
        body = [parse_node(n) for n in node["body"]]
        return WhileExpression(cond, body, node["lineno"])

    def eval(self, variables, patterns):
        pass

def parse_node_expr_value(node):
    if node['ast_type'] == 'Name':
        return Identifier.parse_from_node(node)
    if node['ast_type'] in ('Str', 'Num', 'NameConstant'):
        return Literal.parse_from_node(node)
    if node['ast_type'] == "UnaryOp":
        return UnaryExpression.parse_from_node(node)
    if node['ast_type'] == "BinOp":
        return DoubleExpression.parse_from_node(node)
    if node['ast_type'] == "BoolOp":
        return BooleanExpression.parse_from_node(node)
    if node["ast_type"] == "Call":
        return FunctionCall.parse_from_node(node)
    if node["ast_type"] == "Attribute":
        return AttributeExpression.parse_from_node(node)
    return None

def parse_node(node):
    #stmt -> Assign, Expr, if, while
    if node['ast_type'] == "Assign":
        return AssignExpression.parse_from_node(node)
    #A statement that is just an expression
    if node['ast_type'] == 'Expr':
        return parse_node_expr_value(node["value"])
    if node['ast_type'] == 'If':
        return IfExpression.parse_from_node(node)
    if node['ast_type'] == 'While':
        return WhileExpression.parse_from_node(node)
    return None


def parse(file_path):
    program = list()
    with open(file_path, 'r') as f:
        tree = json.load(f)
    for node in tree['body']:
        stmt = parse_node(node)
        program.append(stmt)
    return program


if __name__ == "__main__":
    prog = parse(sys.argv[1])
    for statement in prog:
        print(statement)
        print(statement.lineno)
