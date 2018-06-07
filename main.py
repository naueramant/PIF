import astor, ast, sys, os
from termcolor import colored

# Global prefs

pif_secret_label = 1
pif_public_label = 0

# Data

var_labels = {}
collection_element_labels = {}

#
# LABELING
# 

def doLabeling(node):
    if get_node_type(node) == 'Module':
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

        if get_node_type(node.value) in ['List', 'Set', 'Tuple']:
            n = node.value
            items = n.elts

            col_labels = [analyseNode(x, [pif_public_label], label)[2] for x in items]
            col_label = get_least_upper_bound(col_labels)

            collection_element_labels[node.targets[0].id] = col_label
        elif get_node_type(node.value) == "Str":
            collection_element_labels[node.targets[0].id] = pif_public_label

        # TODO: Support dicts
    elif t == 'For':
        label = pif_public_label
        target = node.target
        if is_name_confidential(node.target):
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
        return handleWhile(node, pc, label, ln, col)
    elif t == 'For':
        return handleFor(node, pc, label, ln, col) # TODO
    elif t == 'Pass':
        return (node, pc, label)
    elif t == 'Break':
        return (node, pc, label)  # TODO 
    elif t == 'Continue': 
        return (node, pc, label) # TODO 

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
    elif t == 'List':
        return handleList(node, pc, label, ln, col)
    elif t == 'Tuple':
        return handleTuple(node, pc, label, ln, col) 
    elif t == 'Set':
        return handleSet(node, pc, label, ln, col) 
    elif t == 'Dict':
        return handleDict(node, pc, label, ln, col) # TODO
    elif t == 'Subscript':
        return handleSubscript(node, pc, label, ln, col) # TODO
    elif t == 'Call':
        return handleCall(node, pc, label, ln, col)

    # slice
    elif t == 'Slice':
        return handleSlice(node, pc, label, ln, col)
    elif t == 'Index':
        return handleIndex(node, pc, label, ln, col)
    elif t = 'ExtSlice':
        return (node, ln, col) # TODO

    # no handler defined for node, just return it
    printw('Unsupported code "{}"'.format(get_source_at(ln, col)), ln, col)
    return (node, pc, label)

# Handling functions

def handleAssign(node, pc, label, ln, col):
    current_level = pc[-1]

    expr_level = analyseNode(node.value, pc, label)[2]
    target_level = get_variable_label(node.targets[0])

    print('assign',current_level, expr_level, target_level)
    
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

    right_label = get_least_upper_bound(comp_labels)
    label = get_least_upper_bound(left_label, right_label)

    return (node, pc, label) 

def handleIf(node, body, orelse, pc, label, ln, col):
    guard_level = analyseNode(node.test, pc, label)[2]
    new_pc = get_least_upper_bound(guard_level, pc[-1])

    pc.append(new_pc)

    body_labels = [analyseNode(x, pc, label)[2] for x in body]
    orelse_label = [analyseNode(x, pc, label)[2] for x in orelse]

    body_level = get_least_upper_bound(body_labels)
    orelse_level = get_least_upper_bound(orelse_label)

    label = get_least_upper_bound([body_level, orelse_level, guard_level])

    pc.pop()

    return (node, pc, label)

def handleWhile(node, pc, label, ln, col):
    guard_level = analyseNode(node.test, pc, label)[2]
    new_pc = get_least_upper_bound(guard_level, pc[-1])

    if new_pc != pif_public_label:
        printb(get_source_at(ln, col), ln, col)
    else:
        pc.append(new_pc)

        [analyseNode(x, pc, label)[2] for x in node.body]
        [analyseNode(x, pc, label)[2] for x in node.orelse]

        pc.pop()

    return (node, pc, label)

def handleFor(node, pc, label, ln, col):
    print(collection_element_labels)
    target_level = analyseNode(node.target,pc,label)[2]
    if get_node_type(node.iter) == 'Name':
        iter_el_labels = [collection_element_labels[node.iter.id]] 
    else:
        iter_el_labels = [analyseNode(x,pc,label) for x in node.iter.elts]
    
    iter_el_level = get_least_upper_bound(iter_el_labels)
    iter_ref_level = analyseNode(node.iter, pc, label)[2]



    print('For')
    print(node.iter.id, node.target.id)
    print(iter_el_level, target_level, iter_ref_level)

    if not is_upper_bound(get_least_upper_bound(pc[-1], iter_el_level), target_level):
        printb(get_source_at(ln, col), ln, col)
    
    pc.append(get_least_upper_bound(pc[-1], iter_ref_level))

    [analyseNode(x, pc, label)[2] for x in node.body]
    [analyseNode(x, pc, label)[2] for x in node.orelse]

    print(pc)

    return (node, pc, label)

def handleCall(node, pc, label, ln, col):
    func_name = node.func.id
    arg_levels = [analyseNode(x, pc, label)[2] for x in node.args]
    args_level = get_least_upper_bound(arg_levels)

    # Check if all args are public
    if func_name in ['print', 'exit']:
        if get_least_upper_bound(args_level, pc[-1]) != pif_public_label:
            printb(get_source_at(ln, col), ln, col)
        
    # result of function is the same as least upper bound of the given args
    else:
        return (node, pc, args_level)
    
    '''
    # Warn that other functions are not supported
    else:
        printw('Unsupported function "{}"'.format(func_name), ln, col)
    
    return (node, pc, label)
    '''

def handleList(node, pc, label, ln, col):
    item_levels = [analyseNode(x, pc, label)[2] for x in node.elts]
    list_label = is_labels_same(item_levels)

    if list_label == None:
        printb(get_source_at(ln, col), ln, col) # TODO: explain better

    return (node, pc, pif_public_label)

def handleTuple(node, pc, label, ln, col):
    return handleList(node, pc, label, ln, col)

def handleSet(node, pc, label, ln, col):
    return handleList(node, pc, label, ln, col)

def handleDict(node, pc, label, ln, col):
    return (node, pc, label)

def handleSubscript(node, pc, label, ln, col):
    List_label = analyseNode(node.value, pc, label)[2]
    slice_label = analyseNode(node.slice, pc, label)[2]

    label = get_least_upper_bound(List_label, slice_label)

    return (node, pc, label)

def handleIndex(node, pc, label, ln, col):
    return (node, pc, label)

def handleSlice(node, pc, label, ln, col):
    return (node, pc, label)

# Analysis helping functions

def is_labels_same(l):
    if not l:
        return pif_public_label
    else:
        label = l[0]

        for i in l:
            if i != label:
                return None
    
        return label

def is_upper_bound(l1, l2):
    return l1 <= l2

def get_least_upper_bound(l1, l2=None):
    if type(l1) == list:
        return 1 if sum(l1) else 0 
    else:
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