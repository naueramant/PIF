import inspect, parso

class Transpiler:
    def transpile(self, path : str, node : parso.python.tree.Module):
        # Open an output file
        # Inject dependencies, libs osv..

        # Bootstrap traverse the start node
        self.traverse(node)

    def traverse(self, node : parso.python.tree.Module):
        # TODO: follow local imports...
        self.handleNode(node)

        try:
            if node.children:
                for c in node.children:
                    self.traverse(c)
        except(AttributeError):
            pass

    def handleNode(self, node : parso.python.tree.Module):
        t = str(node.type)
        
        if(t == 'pifassign'):
            self.handleAssign(node)
    #
    # Node specific methods
    #

    def handleAssign(self, node : parso.python.tree.Module):
        print(node.type)

    #
    # Helping methods
    #

    def inject(self, node, polyfillName):
        pass
        # TODO
        #polyfill = inspect.getsource(polyfillName)

        
        