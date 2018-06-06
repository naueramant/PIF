import astor, ast, sys, os
from termcolor import colored

# Global prefs

pif_secret_label = 1
pif_public_label = 0

# Data

var_labels = {}

#
# LABELING
# 

def doLabeling(node):
    if hasattr(node, 'body'):
        [doLabeling(n) for n in node.body]
    else:
        labelNode(node)

def labelNode(node):
    t = get_node_type(node)

    if t == 'Assign':
        label = pif_public_label
        target = node.targets[0]
        if is_name_confidential(node.targets[0]):
            label = pif_secret_label

        var_labels[target.id] = label

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
    if get_node_type(node) == 'Module':
        [doAnalysis(n, pc, label) for n in node.body]
    else:
        analyseNode(node, pc, label)

def analyseNode(node, pc, label):
    t = get_node_type(node)
    ln, col = get_node_pos(node)    

    # stmt
    if t == 'Expr':
        return analyseNode(node.value, pc, label)
    elif t == 'Assign':
        return handleAssign(node, pc, label, ln, col)
    elif t == 'If':
        return handleIf(node, node.body, node.orelse, pc, label, ln, col)
    elif t == 'While':
        return (node, pc, label)
    elif t == 'For':
        return (node, pc, label)
    elif t in ['Pass', 'Break', 'Continue']:
        return (node, pc, label)

    # expr
    elif t == 'Name':
        return (node, pc, get_variable_label(node)) 
    elif t == 'NameConstant':
        return (node, pc, pif_public_label) 
    elif t == 'Num':
        return (node, pc, pif_public_label) 
    elif t == 'Str':
        return (node, pc, pif_public_label)
    elif t == 'BoolOp':
        return handleOp(node, node.values[0], node.values[1], pc, label, ln, col)
    elif t == 'BinOp':
        return handleOp(node, node.left, node.right, pc, label, ln, col)     
    elif t == 'Compare':
        return handleCompare(node, pc, label, ln, col)
    elif t == 'UnaryOp':
        return analyseNode(node.operand, pc, label)
    elif t == 'IfExp':
        return handleIf(node, [node.body], [node.orelse], pc, label, ln, col)
    elif t == 'Tuple':
        return (node, pc, label) # TODO
    elif t == 'List':
        return (node, pc, label) # TODO
    elif t == 'Dict':
        return (node, pc, label) # TODO
    elif t == 'Set':
        return (node, pc, label) # TODO
    elif t == 'Subscript':
        return (node, pc, label) # TODO

    # no handler defined for node, just return it
    printw('Unsupported code "{}"'.format(get_source_at(ln, col)), ln, col)
    return (node, pc, label)

# Handling functions

def handleAssign(node, pc, label, ln, col):
    current_level = pc[-1]

    expr_level = analyseNode(node.value, pc, label)[2]
    target_level = get_variable_label(node.targets[0])
    
    if not is_upper_bound(get_least_upper_bound(current_level, expr_level), target_level):
        printb(get_source_at(ln, col), ln, col)
    
    return (node, pc, label)

def handleOp(node, left, right, pc, label, ln, col):
    left_label = analyseNode(left, pc, label)[2]
    right_label = analyseNode(right, pc, label)[2]
    
    label = get_least_upper_bound(left_label, right_label)

    return (node, pc, label)

def handleCompare(node, pc, label, ln, col):
    left_label = analyseNode(node.left, pc, label)[2]
    comp_labels = [analyseNode(x, pc, label)[2] for x in node.comparators]

    right_label = get_least_upper_bound_list(comp_labels)
    label = get_least_upper_bound(left_label, right_label)

    return (node, pc, label) 

def handleIf(node, body, orelse, pc, label, ln, col):
    guard_level = analyseNode(node.test, pc, label)[2]

    pc.append(guard_level)

    body_labels = [analyseNode(x, pc, label)[2] for x in body]
    orelse_label = [analyseNode(x, pc, label)[2] for x in orelse]

    body_level = get_least_upper_bound_list(body_labels)
    orelse_level = get_least_upper_bound_list(orelse_label)

    label = get_least_upper_bound_list([body_level, orelse_level, guard_level])

    pc.pop()

    return (node, pc, label)

def handleWhile(node, pc, label, ln, col):
    pass

# Analysis helping functions

def is_upper_bound(l1, l2):
    return l1 <= l2

def get_least_upper_bound_list(l):
    return 1 if sum(l) else 0 

def get_least_upper_bound(l1, l2):
    return l1 if l1 > l2 else l2

def get_variable_label(node : ast.Name):
    return var_labels[node.id]

def get_node_type(node):
    return type(node).__name__

def get_node_pos(node):
    return (node.lineno, node.col_offset)

def is_name_confidential(node : ast.Name):
    return node.id.endswith('_secret') 

# Other helping functions

def load_ast(file):
    return astor.code_to_ast.parse_file(file)

def printw(msg, ln, col):
    print(colored('PIF WARNING 😐: ({}, {}):'.format(ln, col), 'yellow'), msg)

def printb(msg, ln, col):
    print(colored('PIF ERROR 😭 confidentiality breach ({}, {}):'.format(ln, col), 'red'), msg)
    exit(-1)

def get_source_at(ln, col):
    return source[ln-1][col:].replace('\n', '')

# Main

if __name__ == "__main__":
    main_ast = load_ast(sys.argv[1])
    source = open(sys.argv[1]).readlines()

    doLabeling(main_ast) # Generate var -> label map
    doAnalysis(main_ast) # Do the information flow analysis

    os.system('python3 {}'.format(sys.argv[1])) # Execute the script