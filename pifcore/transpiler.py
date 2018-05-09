import os, parso
from pifcore.polyfill import _pifassign

class Transpiler:
    destFile = None

    def transpile(self, path : str, node : parso.python.tree.Module):
        # Open files
        scriptname = os.path.basename(path).split(".")[0]
        scriptpath = os.path.dirname(os.path.abspath(path))

        with open(path, 'r') as srcFile:
            self.destFile = open(scriptpath + '/' + scriptname + '.py', 'r+')
            
            # Copy and inject polyfill
            self.destFile.writelines(srcFile.readlines())
            
            with open(os.path.dirname(os.path.abspath(__file__))+ '/polyfill.py') as p:
               self.destFile.writelines(['\n\n#PIF POLYFILL FROM HERE DOWN\n\n'] + p.readlines())

            # Bootstrap traverse the start node
            
        self.traverse(node)

    def traverse(self, node : parso.python.tree.Module):
        # TODO: follow local imports...
        self.handleNode(node)

        if hasattr(node, 'children'):
            for c in node.children:
                self.traverse(c)

    def handleNode(self, node : parso.python.tree.Module):
        t = str(node.type)
        pos = node.start_pos
        
        if(t == 'pifassign'):
            self.handleAssign(node, pos)
    #
    # Node specific methods
    #

    def handleAssign(self, node, pos):
        varName = self.getNodeChild(node.parent, 'name').value
        label =  self.getNodeChild(node, 'name').value
        val = self.getNodeChild(node, 'number').value

        # Now what...
        
    #
    # Helping methods
    #

    def getNodeChild(self, node, childname):
        if hasattr(node, 'children'):
            for c in node.children:
                if str(c.type) == str(childname):
                    return c

        return None

    def injectDependencies(self, polyfillName):
        try:
            polyfill = inspect.getsource(polyfillName)
            print(polyfill)

        except(TypeError):
            print("Polyfill '" + polyfillName + "' not found, not injection made.")
        
        