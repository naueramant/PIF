import astor, ast, sys, os
from termcolor import colored

# Global prefs

pif_secret_label = 1
pif_public_label = 0

# Data

var_labels = {}
collection_element_labels = {}
authorities = set()

#
# LABELING
# 

def doLabeling(node):
    if get_node_type(node) == 'Module':
        node.body = list(filter(None.__ne__, [doLabeling(n) for n in node.body]))
        return node
    else:
        return labelNode(node)

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

            col_labels = [analyseNode(x, [pif_public_label], [pif_public_label], label)[3] for x in items]
            col_label = get_least_upper_bound(col_labels)

            collection_element_labels[node.targets[0].id] = col_label
        elif get_node_type(node.value) == 'Str':
            collection_element_labels[node.targets[0].id] = pif_public_label

        # TODO: Support dicts

    elif t == 'For':
        label = pif_public_label
        target = node.target
        if is_name_confidential(node.target):
            label = pif_secret_label

        var_labels[target.id] = label

    elif t == 'Expr':
        if get_node_type(node.value) == 'Call':
            c = node.value
            if c.func.id == 'authorities':
                for a in c.args:
                    if get_node_type(a) == 'Str':
                        authorities.add(a.s)
                    else:
                        printe('Authorities can only be string literals')

                return None # Remove ast node form the real program

    return node

#
# ANALYSIS
# 

def doAnalysis(node, pc=None, lc=None, label=None):
    # generate the labels
    node = doLabeling(node)

    print(authorities)

    # default values
    if not pc:
        pc = [pif_public_label]

    if not label:
        label = pif_public_label
    if not lc:
        lc = [pif_public_label]

    # Walk! the ast...
    if get_node_type(node) == 'Module':
        node.body = [doAnalysis(n, pc, lc, label) for n in node.body]
    else:
        node = analyseNode(node, pc, lc, label)[0]

    return node

def analyseNode(node, pc, lc, label):
    t = get_node_type(node)
    ln, col = get_node_pos(node)    

    # stmt
    if t == 'Expr':
        return (node, pc, lc, analyseNode(node.value, pc, lc, label)[3])
    elif t == 'Assign':
        return handleAssign(node, pc, lc, label, ln, col)
    elif t == 'If':
        return handleIf(node, pc, lc, label, ln, col)
    elif t == 'While':
        return handleWhile(node, pc, lc, label, ln, col)
    elif t == 'For':
        return handleFor(node, pc, lc, label, ln, col)
    elif t == 'Pass':
        return (node, pc, lc, label) # Not handling timing attacks for now...
    elif t in ['Break', 'Continue']:
        return handleEscape(node, pc, lc, label, ln, col) # Not handling timing and non-termination attacks for now...

    # expr
    elif t == 'Name':
        return (node, pc, lc, get_variable_label(node)) 
    elif t == 'NameConstant':
        return (node, pc, lc, pif_public_label) 
    elif t == 'Num':
        return (node, pc, lc, pif_public_label) 
    elif t == 'Str':
        return (node, pc, lc, pif_public_label)
    elif t == 'BoolOp':
        return handleOp(node, pc, lc, label, ln, col)
    elif t == 'BinOp':
        return handleBinOp(node, pc, lc, label, ln, col)     
    elif t == 'Compare':
        return handleCompare(node, pc, lc, label, ln, col)
    elif t == 'UnaryOp':
        return analyseNode(node.operand, pc, lc, label)
    elif t == 'IfExp':
        return handleIfExp(node, pc, lc, label, ln, col)
    elif t == 'List':
        return handleList(node, pc, lc, label, ln, col)
    elif t == 'Tuple':
        return handleTuple(node, pc, lc, label, ln, col) 
    elif t == 'Set':
        return handleSet(node, pc, lc, label, ln, col) 
    elif t == 'Dict':
        return handleDict(node, pc, lc, label, ln, col) # TODO
    elif t == 'Subscript':
        return handleSubscript(node, pc, lc, label, ln, col) 
    elif t == 'Call':
        return handleCall(node, pc, lc, label, ln, col)

    # slice
    elif t == 'Index':
        return handleIndex(node, pc, lc, label, ln, col)
    elif t == 'Slice':
        return handleSlice(node, pc, lc, label, ln, col)
    elif t == 'ExtSlice':
        return handleSlice(node, pc, lc, label, ln, col) 

    # no handler defined for node, just return it
    printw('Unsupported statement', ln, col)
    return (node, pc, lc, label)

# Handling functions

def handleAssign(node, pc, lc, label, ln, col):
    current_level = pc[-1]

    node_analysis = analyseNode(node.value, pc, lc, label)
    expr_level = node_analysis[3]

    node.value = node_analysis[0]
    target_level = get_variable_label(node.targets[0])

    if not is_upper_bound(get_least_upper_bound(current_level, expr_level), target_level):
        printb("Can't assign secret to public variable {}".format(node.targets[0].id), ln, col)
    
    return (node, pc, lc, label)

def handleOp(node, pc, lc, label, ln, col):
    left = node.values[0]
    right = node.values[1]

    left_label_analysis = analyseNode(left, pc, lc, label)
    left_label = left_label_analysis[3]    
    node.left = left_label_analysis[0]

    right_label_analysis = analyseNode(right, pc, lc, label)
    right_label = right_label_analysis[3]    
    node.right = right_label_analysis[0]

    node.values = [node.left, node.right]
    
    label = get_least_upper_bound(left_label, right_label)

    return (node, pc, lc, label)

def handleBinOp(node, pc, lc, label, ln, col):
    node.values = [node.left, node.right]
    return handleOp(node, pc, lc, label, ln, col)

def handleCompare(node, pc, lc, label, ln, col):
    left_label_analysis = analyseNode(node.left, pc, lc, label)
    left_label = left_label_analysis[3]
    node.left = left_label_analysis[0]

    comp_labels_analysis = [analyseNode(x, pc, lc, label) for x in node.comparators]
    comp_labels = get_labels(comp_labels_analysis)
    node.comparators = get_nodes(comp_labels_analysis)

    right_label = get_least_upper_bound(comp_labels)
    label = get_least_upper_bound(left_label, right_label)

    return (node, pc, lc, label) 

def handleIf(node, pc, lc, label, ln, col):
    guard_analysis = analyseNode(node.test, pc, lc, label)
    guard_level = guard_analysis[3]
    node.test = guard_analysis[0]

    new_pc = get_least_upper_bound(guard_level, pc[-1])

    pc.append(new_pc)

    body_labels_analysis = [analyseNode(x, pc, lc, label) for x in node.body]
    body_labels = get_labels(body_labels_analysis)
    node.body = get_nodes(body_labels_analysis)

    orelse_label_analysis = [analyseNode(x, pc, lc, label) for x in node.orelse]
    orelse_labels = get_labels(orelse_label_analysis)
    node.orelse = get_nodes(orelse_label_analysis)

    body_level = get_least_upper_bound(body_labels)
    orelse_level = get_least_upper_bound(orelse_labels)

    label = get_least_upper_bound([body_level, orelse_level, guard_level])

    pc.pop()

    return (node, pc, lc, label)

def handleIfExp(node, pc, lc, label, ln, col):
    node.body = [node.body]
    node.orelse = [node.orelse]
    
    new_node = handleIf(node, pc, lc, label, ln, col)

    node.body = new_node[0].body[0]
    node.orelse = new_node[0].orelse[0]

    return (node, new_node[1], new_node[2], new_node[3]) 

def handleWhile(node, pc, lc, label, ln, col):
    guard_analysis = analyseNode(node.test, pc, lc, label)
    guard_level = guard_analysis[3]
    node.test = guard_analysis[0]
    new_pc = get_least_upper_bound(guard_level, pc[-1])

    pc.append(new_pc)
    lc.append(new_pc)

    [analyseNode(x, pc, lc, label)[3] for x in node.body]
    [analyseNode(x, pc, lc, label)[3] for x in node.orelse]

    lc.pop()
    pc.pop()

    return (node, pc, lc, label)

def handleFor(node, pc, lc, label, ln, col):
    target_level_analysis = analyseNode(node.target, pc, lc, label)
    target_level = target_level_analysis[3]
    node.target = target_level_analysis[0]

    t = get_node_type(node.iter)

    if t == 'Name':
        iter_el_labels = [collection_element_labels[node.iter.id]] 
    elif t in ['Call', 'Str']: # supported iterables
        iter_el_labels_analysis = analyseNode(node.iter, pc, lc, label)
        iter_el_labels = [iter_el_labels_analysis[3]]
        node.iter = iter_el_labels_analysis[0]
    else:
        iter_el_labels_analysis = [analyseNode(x, pc, lc, label) for x in node.iter.elts]
        iter_el_labels = get_labels(iter_el_labels_analysis)
        node.iter.elts = get_nodes(iter_el_labels_analysis)
    
    iter_el_level = get_least_upper_bound(iter_el_labels)
    iter_ref_level_analysis = analyseNode(node.iter, pc, lc, label)
    iter_ref_level = iter_ref_level_analysis[3]
    node.iter = iter_ref_level_analysis[0]

    if not is_upper_bound(get_least_upper_bound(pc[-1], iter_el_level), target_level):
        printb('Least upper bound is not upper bound', ln, col)
    
    pc.append(get_least_upper_bound(pc[-1], iter_ref_level))

    node.body = [analyseNode(x, pc, lc, label)[0] for x in node.body]
    node.orelse = [analyseNode(x, pc, lc, label)[0] for x in node.orelse]

    return (node, pc, lc, label)

def handleCall(node, pc, lc, label, ln, col):
    func_name = node.func.id
    
    arg_levels_analysis = [analyseNode(x, pc, lc, label) for x in node.args]
    arg_levels = get_labels(arg_levels_analysis)
    
    node.args = get_nodes(arg_levels_analysis)

    args_level = get_least_upper_bound(arg_levels)

    # Check if all args are public
    if func_name in ['print', 'exit']:
        if get_least_upper_bound(args_level, pc[-1]) != pif_public_label:
            printb('All arguments should be public', ln, col)
    
    if func_name == 'declassify':
        node_analysis = handleDeclassify(node, pc, lc, label, ln, col)
        node = node_analysis[0]
        args_level = node_analysis[3]

    # result of function is the same as least upper bound of the given args
    return (node, pc, lc, args_level)

def handleDeclassify(node, pc, lc, label, ln, col):
    node = node.args[0]

    if analyseNode(node, pc, lc, label)[3] == pif_public_label:
        printw('No need to declassify public variables', ln, col)

    return (node, pc, lc, pif_public_label)

def handleList(node, pc, lc, label, ln, col):
    item_levels_analysis = [analyseNode(x, pc, lc, label) for x in node.elts]
    item_levels = get_labels(item_levels_analysis)

    node.elts = get_nodes(item_levels_analysis)

    list_label = is_labels_same(item_levels)

    if list_label == None:
        printb("Mixed confidentiality levels in list", ln, col)

    return (node, pc, lc, pif_public_label)

def handleTuple(node, pc, lc, label, ln, col):
    return handleList(node, pc, lc, label, ln, col)

def handleSet(node, pc, lc, label, ln, col):
    return handleList(node, pc, lc, label, ln, col)

def handleDict(node, pc, lc, label, ln, col):
    return (node, pc, lc, label)

def handleSubscript(node, pc, lc, label, ln, col):
    list_label_analysis = analyseNode(node.value, pc, lc, label)
    list_label = list_label_analysis[3]
    node.value = list_label_analysis[0]

    slice_label_analysis = analyseNode(node.slice, pc, lc, label)
    slice_label = slice_label_analysis[3]
    node.slice = slice_label_analysis[0]    

    label = get_least_upper_bound(list_label, slice_label)

    return (node, pc, lc, label)

def handleIndex(node, pc, lc, label, ln, col):
    node_analysis = analyseNode(node.value, pc, lc, label)
    node.value = node_analysis[0]
    return (node, pc, lc, node_analysis[3])

def handleSlice(node, pc, lc, label, ln, col):
    upper_label = pif_public_label
    step_label = pif_public_label
    lower_label = pif_public_label

    if node.upper:
        upper_label_analysis = analyseNode(node.upper, pc, lc, label)
        upper_label = upper_label_analysis[3]
        node.upper = upper_label_analysis[0]
    if node.step:
        step_label_analysis = analyseNode(node.step, pc, lc, label)
        step_label = step_label_analysis[3]
        node.step = step_label_analysis[0]
    if node.lower:
        lower_label_analysis = analyseNode(node.lower, pc, lc, label)
        lower_label = lower_label_analysis[3]
        node.lower = lower_label_analysis[0]
        
    label = get_least_upper_bound([upper_label, step_label, lower_label])

    return (node, pc, lc, label)

def handleEscape(node, pc, lc, label, ln, col):
    if pc[-1] == pif_secret_label and lc[-1] == pif_public_label:
        printb('Trying to escape a public loop from a secret context', ln, col)

    return (node, pc, lc, label)

# Analysis helping functions

def get_labels(l):
    return [x[3] for x in l]

def get_nodes(l):
    return [x[0] for x in l]

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
        le = len(l1)

        if le == 0:
            return pif_public_label
        elif le == 1:
            return l1[0]
        else:
            return 1 if sum(l1) else 0 
    else:
        return l1 if l1 > l2 else l2
    
def get_variable_label(node : ast.Name):
    try:
        return var_labels[node.id]
    except KeyError:
        ln, col = get_node_pos(node)
        printe('Unknown variable {}'.format(node.id), ln, col)

def get_node_type(node):
    return type(node).__name__

def get_node_pos(node):
    if hasattr(node, 'lineno') and hasattr(node, 'col_offset'):
        return (node.lineno, node.col_offset)
    return (None, None)

def is_name_confidential(node : ast.Name):
    return node.id.endswith('_secret') 

# Other helping functions

def load_ast(file):
    return astor.code_to_ast.parse_file(file)

def printw(msg, ln, col):
    print(colored('PIF WARNING 😐 ln {} col {}:'.format(ln, col), 'yellow'))
    print('Msg: ', msg)
    print('Src: ', get_source_at(ln, col))

def printb(msg, ln, col):
    print(colored('PIF ERROR 😭 confidentiality breach at ln {} col {}:'.format(ln, col), 'red'))
    print('Msg: ', msg)
    print('Src: ', get_source_at(ln, col))
    exit(-1)

def printe(msg, ln, col):
    print(colored('PIF FATAL ERROR 🤯 ln {} col {}'.format(ln, col), 'red'))
    print('Msg: ', msg)
    print('Src: ', get_source_at(ln, col))
    exit(-1)

def get_source_at(ln, col):
    return source[ln-1][col:].replace('\n', '')

# Main

if __name__ == '__main__':
    main_ast = load_ast(sys.argv[1])
    source = open(sys.argv[1]).readlines()

    new_ast = doAnalysis(main_ast)
    new_source = astor.to_source(new_ast)

    exec(new_source)
    