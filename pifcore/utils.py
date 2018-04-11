from termcolor import colored

def prettyPrint(module, indentlevel=0):
    exclude = ["parent", "children", "type"]
    indent = "    "
    
    indentions = "".join([indent for x in range(indentlevel)])
    
    print(indentions, colored(module.type, "blue"), " {", sep="")

    for d in dir(module):
        a = getattr(module, d)
        if a and not callable(a) and d not in exclude and "_" != d[0]:
            print(indentions, indent, colored(d, "red"), ": ", colored(a, "green"), sep="") 
    
    try:
        if module.children:
            for c in module.children:
                prettyPrint(c, indentlevel+1)
    except(AttributeError):
        pass
    
    print(indentions, "}", sep="")
