#! /bin/env python3

import parso, os, sys
from pif.utils import prettyPrintGrammar

p = path=os.path.join(os.path.dirname(os.path.realpath(__file__)),"Grammar/grammar37_pif")
print(p)

grammar = parso.load_grammar(path=p)

with open("./tests/simple.pif") as f:
    m = grammar.parse(f.read())
    prettyPrintGrammar(m)