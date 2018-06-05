import astor, ast, sys
from termcolor import colored

# Global prefs

pif_secret_label = ast.Str('_pif_secret')
pif_public_label = ast.Str('_pif_public')

# Main functions

def load_ast(file):
    return astor.code_to_ast.parse_file(file)

def walk(node, fn):
    if hasattr(node, 'body'):
        node.body = [walk(n, fn) for n in node.body]
        return node
    else:
        return fn(node)

# Used for labeling run
def handleLabel(node):
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

# Used for analysis run
def handleAnalyse(node):
    t = get_node_type(node)
    ln, col = get_node_pos(node)    

    if t == 'Assign':
        return checkAssign(node, ln, col)

    # no handler defined for node, just return it
    return node

# Handling functions

def checkAssign(node, ln, col):
    t = get_node_type(node.value.elts[0])

    if t == 'Name':
        name_conf = get_name_confidential_label(node.value.elts[0])
        tuple_conf = get_tuple_confidentiality_label(node.value)
        
        if tuple_conf != name_conf:
            printb(source[ln-1][col:].replace('\n', ''), ln, col)

    return node


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

# Prints

def printw(msg, ln, col):
    print(colored('WARNING ({}, {}):'.format(ln, col), 'yellow'), msg)

def printb(msg, ln, col):
    print(colored('Confidentiality breach ({}, {}):'.format(ln, col), 'red'), msg)
    exit(-1)

# Main
main_ast = load_ast(sys.argv[1])
source = open(sys.argv[1]).readlines()

new_ast_label = walk(main_ast, handleLabel)
new_ast_analysed = walk(new_ast_label, handleAnalyse)

new_source = astor.to_source(new_ast_analysed)

print('SOURCE ---------------------------------')
print(''.join(source))
print('RESULT ---------------------------------')
print(new_source)
print('EXEC -----------------------------------')

exec(new_source)