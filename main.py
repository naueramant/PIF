import astor, ast, sys, os
from termcolor import colored

# Global prefs

pif_secret_label = {}
pif_public_label = {}

supported_iterables = ['Str', 'List', 'Tuple', 'Set']

# Data

var_labels = {}
collection_element_labels = {}

authorities = set()
principals = set()

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
    ln, col = get_node_pos(node) 

    if t == 'Assign':
        target_name = node.targets[0].id

        if get_node_type(node.value) == 'Call' and node.value.func.id == 'label':
            func = node.value
            labels = func.args[1]
            
            guestslist = []
            owners = []
            if hasattr(labels, 'keys'):
                owners = labels.keys
                guestslist = labels.values  

            res_dict = {}

            for o, l in zip(owners, guestslist):
                temp_names = []
                
                for guest in l.elts:
                    temp_names.append(guest.s)

                res_dict[o.s] = temp_names

            if get_node_type(node.value.args[0]) in supported_iterables:
                collection_element_labels[target_name] = res_dict
            
            var_labels[target_name] = res_dict

            node.value = func.args[0] 
        else:
            if not target_name in var_labels:
                if get_node_type(node.value) == 'Str':
                    collection_element_labels[target_name] = pif_public_label

                var_labels[target_name] = pif_public_label

        # TODO: Support dicts

    elif t == 'For':
        label = pif_public_label
        target = node.target

        if get_node_type(node.iter) == 'Name':
            if node.iter.id in var_labels:
                var_labels[target.id] = var_labels[node.iter.id]
            else:
                printe('Unknown variable {}'.format(node.iter.id), ln, col)
        else:
            var_labels[target.id] = pif_public_label
        
    # Authorities and principals
    elif t == 'Expr':
        if get_node_type(node.value) == 'Call':
            c = node.value

            if c.func.id == 'principals':
                for a in c.args:
                    if get_node_type(a) == 'Str':
                        principals.add(a.s)
                    else:
                        printe('Principals can only be string literals', ln, col)
                
                # Generate the public label
                for p in principals:
                    pif_public_label[p] = [x for x in principals if x != p]

                return None # Remove ast node from the real program

            elif c.func.id == 'authorities':
                for a in c.args:
                    if len(principals) == 0:
                        printe('Principals must be defined before authorities', ln, col)

                    if get_node_type(a) == 'Str':
                        if a.s in principals:
                            authorities.add(a.s)
                        else:
                            printe('Can\'t add authroity {} since it is not present in principals'.format(a.s), ln, col)

                    else:
                        printe('Authorities can only be string literals', ln, col)

                return None # Remove ast node form the real program

    return node

#
# ANALYSIS
# 

def doAnalysis(node, pc=None, lc=None, label=None):
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

    if not is_upper_bound(get_least_upper_bound(current_level, expr_level), get_allowed_principals(target_level)):
        printb("Confidentiality mismatch", ln, col)
    
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
        print(get_least_upper_bound(args_level, pc[-1]))
        if get_least_upper_bound(args_level, pc[-1]) != get_allowed_principals(pif_public_label):
            printb('All arguments should be public', ln, col)
    
    if func_name == 'declassify':
        node_analysis = handleDeclassify(node, pc, lc, label, ln, col)
        node = node_analysis[0]
        args_level = node_analysis[3]

    # result of function is the same as least upper bound of the given args
    return (node, pc, lc, args_level)

# Declassify is not robust!
def handleDeclassify(node, pc, lc, label, ln, col):
    print(node)
    new_node = node.args[0]
    node_analysis = analyseNode(new_node, pc, lc, label)

    if len(node.args) != 2:
        printe('declassify needs a expr and a set of authorities as strings', ln, col)

    if node_analysis[3] == pif_public_label:
        printw('No need to declassify public variables', ln, col)


    auth_arg = node.args[1]
    auth_arg_type = get_node_type(auth_arg)

    if auth_arg_type != 'Set':
        # This exites the analysis
        printe('Authorities must be defined in a set', ln, col)
    else:
        new_label = {}

        auth_arg_len = len(auth_arg.elts)

        if auth_arg_len == 0:
            new_label = pif_secret_label
        else:
            for s in auth_arg.elts:
                if get_node_type(s) == 'Str':
                    if s.s == 'public':
                        new_label = pif_public_label
                        break

                    new_label[s.s] = []
                else:
                    printe('Authorities must be a string literals', ln, col)

        label = new_label

    return (new_node, pc, lc, label)

def handleList(node, pc, lc, label, ln, col):
    item_levels_analysis = [analyseNode(x, pc, lc, label) for x in node.elts]
    item_levels = get_labels(item_levels_analysis)

    node.elts = get_nodes(item_levels_analysis)

    list_label = is_labels_same(item_levels)

    if list_label == None:
        printb("Mixed confidentiality levels in collection", ln, col)

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
    print(pc[-1], lc[-1])
    if  lc[-1] != pc[-1] and is_upper_bound(lc[-1], pc[-1]):
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

# l2 upperbound of l1
def is_upper_bound(l1, l2):
    return sorted(list(l1)) == sorted(list(l2)) or len(l2) < len(l1)

def get_least_upper_bound(l1, l2=None):
    res = principals
    if type(l1) == list:
        for l in l1:
            if type(l) == dict:
                l = get_allowed_principals(l)

            res = res & l
    else:
        if type(l1) == dict:
            l1 = get_allowed_principals(l1)
        if type(l2) == dict:
            l2 = get_allowed_principals(l2)

        res = l1 & l2
    return res

def get_allowed_principals(lbl):
    if len(lbl) == 0:
        return set()

    res = principals
    owners = set()
    for key in lbl:
        temp = set(lbl[key])
        owners.add(key)
        res = res & temp
    res = res | owners
    return res
    
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
    return source[ln-1].replace('\n', '')

# Main

if __name__ == '__main__':
    main_ast = load_ast(sys.argv[1])
    source = open(sys.argv[1]).readlines()

    labeled_ast = doLabeling(main_ast)
    print("Authorities---------------------")
    print(principals)
    print("Authorities---------------------")
    print(authorities)
    print("Var labels---------------------")
    print(var_labels)
    print("Collection labels---------------------")
    print(collection_element_labels)
    print("-------------------------------")

    new_ast = doAnalysis(labeled_ast)
    new_source = astor.to_source(new_ast)

    print(new_source)

    exec(new_source)
    