import astor, ast, sys
from termcolor import colored

# Global prefs

pif_secret_label = ast.Str('_pif_secret')
pif_public_label = ast.Str('_pif_public')

# Main functions

def load_ast(file):
    return astor.code_to_ast.parse_file(file)

#
# LABELING
# 
def doLabeling(node):
    if hasattr(node, 'body'):
        node.body = [doLabeling(n) for n in node.body]
        return node
    else:
        return labelNode(node)

def labelNode(node):
    t = get_node_type(node)
    ln, col = get_node_pos(node)

    if t == 'Assign':
        l = pif_public_label
        if get_name_confidential(node.targets[0]):
            l = pif_secret_label

        t = ast.Tuple([
            node.value,
            l
        ], None)

        node.value = t

    return node

#
# ANALYSIS
# 
def doAnalysis(node, pc=None, label=None):
    # default values
    if not pc:
        pc = [pif_public_label]

    if not label:
        label = pif_public_label

    # Walk!
    if hasattr(node, 'body'):
        [doAnalysis(n, pc, label) for n in node.body]
    else:
        analyseNode(node, pc, label)

def analyseNode(node, pc, label):
    t = get_node_type(node)
    ln, col = get_node_pos(node)    

    # stmt
    if t == 'Expr':
        return (node, pc, label)
    elif t == 'Assign':
        return (node, pc, label)
    elif t == 'Compare':
        return (node, pc, label)
    elif t == 'If':
        return (node, pc, label)
    elif t == 'While':
        return (node, pc, label)
    elif t == 'For':
        return (node, pc, label)
    elif t == 'Pass':
        return (node, pc, label)
    elif t == 'Break':
        return (node, pc, label)
    elif t == 'Continue':
        return (node, pc, label)

    # expr
    elif t == 'Name':
        return (node, pc, label)
    elif t == 'Num':
        return (node, pc, label)
    elif t == 'Str':
        return (node, pc, label)
    elif t == 'BoolOp':
        return (node, pc, label)
    elif t == 'BinOp':
        return (node, pc, label)
    elif t == 'Compare':
        return (node, pc, label)
    elif t == 'UnaryOp':
        return (node, pc, label)
    elif t == 'IfExp':
        return (node, pc, label)
    elif t == 'Tuple':
        return (node, pc, label)
    elif t == 'List':
        return (node, pc, label)
    elif t == 'Dict':
        return (node, pc, label)
    elif t == 'Set':
        return (node, pc, label)
    elif t == 'Subscript':
        return (node, pc, label)

    # boolop
    elif t == 'And':
        return (node, pc, label)
    elif t == 'Or':
        return (node, pc, label)

    # operator
    elif t == 'Add':
        return (node, pc, label)
    elif t == 'Sub':
        return (node, pc, label)
    elif t == 'Mult':
        return (node, pc, label)
    elif t == 'Div':
        return (node, pc, label)
    elif t == 'Mod':
        return (node, pc, label)
    elif t == 'Pow':
        return (node, pc, label)

    # unaryop
    elif t in ['Invert', 'Not', 'UAdd', 'USub']:
        return (node, pc, label)

    # cmpop
    elif t in ['Eq', 'NotEq', 'Lt', 'LtE', 'Gt', 'Gte', 'Is', 'IsNot']:
        return (node, pc, label)
    elif t in ['In', 'NotIn']:
        return (node, pc, label)

    # no handler defined for node, just return it
    printw('Unsupported code {} 😭'.format(get_source_at(ln, col)), ln, col)
    return (node, pc, label)

# Handling functions

# Helping functions

def get_node_type(node):
    return type(node).__name__

def get_node_pos(node):
    return (node.lineno, node.col_offset)

def get_tuple_confidentiality_label(node):
    if is_pif_tuple(node):
        return node.elts[1]
    else:
        raise Exception('Can not get conf rating on none tuple!')

def get_name_confidential(node):
    if get_node_type(node) == 'Name':
        return node.id.endswith('_secret') 
    else:
        raise Exception('Can not get confidential of {} node!'.format(get_node_type(node)))

def get_name_confidential_label(node):
    if get_name_confidential(node):
        return pif_secret_label
    else:
        return pif_public_label

def is_pif_tuple(node):
    return get_node_type(node) == 'Tuple' and (node.elts[1] == pif_public_label or node.elts[1] == pif_secret_label)

def get_source_at(ln, col):
    return source[ln-1][col:].replace('\n', '')

# Prints

def printw(msg, ln, col):
    print(colored('WARNING ({}, {}):'.format(ln, col), 'yellow'), msg)

def printb(msg, ln, col):
    print(colored('Confidentiality breach ({}, {}):'.format(ln, col), 'red'), msg)
    exit(-1)

# Main
main_ast = load_ast(sys.argv[1])
source = open(sys.argv[1]).readlines()

new_ast_label = doLabeling(main_ast)
doAnalysis(new_ast_label)
new_source = astor.to_source(new_ast_label)

print('SOURCE ---------------------------------')
print(''.join(source))
print('RESULT ---------------------------------')
print(new_source)
print('EXEC -----------------------------------')

exec(new_source)