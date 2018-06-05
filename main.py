import astor, ast
from termcolor import colored

# Main functions

def load_ast(file):
    return astor.code_to_ast.parse_file(file)

def walk(node):
    if hasattr(node, 'body'):
        node.body = [walk(n) for n in node.body]
        return node
    else:
        return handleType(node)

def handleType(node):
    t = get_node_type(node)
    ln, col = get_node_pos(node)

    if t == 'Assign':
        return handle_assign(node, ln, col)

    if t == 'Name':
        return node

    if t == 'Value':
        return node
    
    if t == 'Num':
        return node

    # no handler defined for node, just return it
    return node

# Helping functions

def get_node_type(node):
    return type(node).__name__

def get_node_pos(node):
    return (node.lineno, node.col_offset)

def get_name_confidential(node):
    if get_node_type(node) == 'Name':
        return node.id.endswith('_secret') 
    else:
        raise Exception('Can not get confidential of none Name node!')

def printw(msg, ln, col):
    print(colored('({}, {}) WARNING:'.format(ln, col), 'yellow'), msg)

# Handling functions

def handle_assign(node, ln, col):
    l = ast.Str('public')
    if get_name_confidential(node.targets[0]):
        l = ast.Str('secret')

    t = ast.Tuple([
        node.value,
        l
    ], None)

    node.value = t
    return node

# Main
main_ast = load_ast('./tests/assign1.py')
new_ast = walk(main_ast)
source = astor.to_source(new_ast)
print(source)