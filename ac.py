from typing import List
from functools import cmp_to_key
import readline

### most basic building-block ###
class Term:
    def __init__(self, name: str, weight, arity=0):
        self.name = name
        self.weight = weight
        self.arity = arity

    def __eq__(self, other):
        return isinstance(other, Term) and self.name == other.name

    def __repr__(self):
        return self.name

### the input formula and finally the normalized formula are represented as tree of terms ###
class TreeNode:
    def __init__(self, term: Term, children=None, display=None):
        self.term = term
        self.children = children if children is not None else []
        self.display = display if display is not None else self.children

    def count_vars(self):
        count = 0
        if self.term.weight < 0:
            count += 1
        for child in self.children:
            count += child.count_vars()
        return count
    
    def count_weight(self):
        w = self.term.weight + 2
        for child in self.children:
            w += child.count_weight()
        return w

    def add_child(self, node):
        self.children.append(node)

    # I only use x as a variable with weight -1 (multiple vars would render KBO partial)
    def is_var(self):
        return self.term.weight < 0

    def is_func(self):
        return len(self.children) > 0
    
    def is_ac_func(self):
        return self.is_func() and self.term.weight == 0
    
    def __eq__(self, other):
        if not isinstance(other, TreeNode) or self.term != other.term:
            return False
        for index, child1 in enumerate(self.children):
            child2 = other.children[index]
            if child1 != child2:
                return False
        return True

    def __repr__(self):
        repr_str = f"{self.term}"
        if self.is_func():
            repr_str += "("
            for child in self.display:
                repr_str += child.__repr__()
                repr_str += ","
            repr_str = repr_str[:-1] + ")"
        return repr_str

# hardcoded information that should always stay the same
f = Term("f", 0) # formula with ac axioms
x = Term("x", -1) # variable
terms = {"f" : f, "x" : x} # map of all terms used in the formula

# data for testing without console input
"""
a = Term("a", 1)
b = Term("b", 2)
g = Term("g", 3)
node = TreeNode(f, [TreeNode(x), TreeNode(f, [TreeNode(b), TreeNode(a)])])
node = TreeNode(f, [TreeNode(g, [TreeNode(x)]), TreeNode(f, [TreeNode(a), TreeNode(x)])])
node = TreeNode(f, [TreeNode(g, [TreeNode(f, [TreeNode(b), TreeNode(x)])]), TreeNode(g, [TreeNode(f, [TreeNode(b), TreeNode(a)])])])
node = TreeNode(f, [TreeNode(g, [TreeNode(f, [TreeNode(b), TreeNode(x)]), TreeNode(x)]), TreeNode(g, [TreeNode(a), TreeNode(f, [TreeNode(b), TreeNode(a)])])])
print(node)
"""

### logic for normalization of ac term ###
# KBO (is total as long as there is only one variable)
def comp_extended(term1: TreeNode, term2: TreeNode):
    if term1 == term2:
        return 0
    #1.
    if term1.count_vars() >= term2.count_vars() and term1.count_weight() > term2.count_weight():
        return 1
    #2.
    elif term1.count_vars() >= term2.count_vars() and term1.count_weight() == term2.count_weight():
        #2.1
        if term2.is_var() and term1.is_func():
            return 1
        #2.2
        elif term1.is_func() and term2.is_func() and term1.term.weight > term2.term.weight:
            return 1
        #2.3
        elif term1.is_func() and term2.is_func() and term1.term == term2.term:
            for index, child1 in enumerate(term1.children):
                child2 = term2.children[index]
                if child1 != child2:
                    return comp_extended(child1, child2)
    return -1

# compare method based on the input partial term ordering
def comp_term(term1: TreeNode, term2: TreeNode):
    if term1 == term2:
        return 0
    if term1.term.weight > 0 and term2.term.weight > 0:
        if term1.term.weight > term2.term.weight:
            return 1
        elif term1.term.weight < term2.term.weight:
            return -1
        else:
            for index, child1 in enumerate(term1.children):
                child2 = term2.children[index]
                if child1.is_var() or child2.is_var():
                    return 0
                elif child1 != child2:
                    return comp_term(child1, child2)
    else:
        return 0

# allows terms within ac context to be shifted
def csort(terms: List[TreeNode]):
    if len(terms) == 0:
        return []
    firstTerm = terms[0]
    if not firstTerm.is_var():
        for k, kterm in enumerate(terms):
            if comp_term(kterm, firstTerm) < 0:
                found_minimal = True
                for term2 in terms:
                    if comp_term(kterm, term2) > 0:
                        found_minimal = False
                        break
                if found_minimal:
                    return flatten([kterm, csort_prime(terms, k)])
    return flatten([firstTerm, csort(terms[1:])])

# after minimal element is found we sort with extended term-ordering of our choosing (I just use KBO)
def csort_prime(terms: List[TreeNode], k: int):
    del terms[k]
    return sorted(terms, key=cmp_to_key(comp_extended))

# normalize the ac term as loosely described in the paper
def norm(node: TreeNode):
    if node.is_func() and not node.is_ac_func():
        prime = []
        display = []
        for child in node.children:
            normalized = norm(child)
            prime.append(normalized)
            if child.is_ac_func():
                display.append(TreeNode(f, normalized))
            else:
                display.append(normalized)
        return TreeNode(node.term, flatten(prime), display)
    elif node.is_ac_func():
        prime = [norm(item) for item in flatten_ac(node.children)]
        return csort(prime)
    else:
        return node

### helper methods ###
def display(terms: List[TreeNode], ac_arity=2):
    while len(terms) > 1:
        d = TreeNode(f, terms[-ac_arity:])
        terms = terms[:-ac_arity]
        terms.append(d)
    print(terms[0])

def flatten_ac(children: List[TreeNode]):
    flat = []
    for child in children:
        if child.is_ac_func():
            flat.append(flatten_ac(child.children))
        else:
            flat.append(child)
    return flatten(flat)

def flatten(terms):
    result = []
    for term in terms:
        if isinstance(term, list):
            result.extend(flatten(term))
        else:
            result.append(term)
    return result

### parsing terms and ordering from command line ###
def parse_term(s):
    s = s.strip()
    if not "(" in s:
        if s not in terms:
            raise Exception(f"term-name '{name}' not present in input ordering")
        return TreeNode(terms[s])
    
    name, rest = s.split('(', 1)
    if name not in terms:
        raise Exception(f"term-name '{name}' not present in input ordering")
    args_str = rest[:-1]
    args = split_args(args_str)
    return TreeNode(terms[name], [parse_term(arg) for arg in args])

def split_args(s):
    args = []
    depth = 0
    current = ''
    for c in s:
        if c == ',' and depth == 0:
            args.append(current.strip())
            current = ''
        else:
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
            current += c
    if current:
        args.append(current.strip())
    return args

def term_ordering(s):
    s = s.strip()
    names = s.split('>')
    for index, name in enumerate(names):
        if name == "f" or name == "x":
            raise Exception("'f' and 'x' are keywords with hardcoded ordering.")
        else:
            terms[name] = Term(name, len(names) - index)

if __name__ == "__main__":
    print("input the termordering [e.g.: g>b>a]")
    try:
        line = input("#  ").strip()
        if line:
            term_ordering(line)
    except Exception as e:
        print(f"Error: {e}")

    print("input a formula to normalize [e.g.: f(g(x),f(a,x))]")
    while True:
        try:
            line = input("#  ").strip()
            if line:
                if line[0] != "f":
                    raise Exception("term should be wrapped in ac function")
                term = parse_term(line)
                print("=> ", end="")
                display(norm(term), len(term.children))
        except Exception as e:
            print(f"Error: {e}")
