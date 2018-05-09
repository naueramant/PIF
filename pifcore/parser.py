import parso, os

class Parser:
    def parse(self, path):
        p = os.path.join(os.path.dirname(os.path.realpath(__file__)),"Grammar/grammar37_pif")
        grammar = parso.load_grammar(path=p)
        with open(path) as f:
            return grammar.parse(f.read())