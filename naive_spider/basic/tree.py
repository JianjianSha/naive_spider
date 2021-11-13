class _Node:
    def __init__(self, key, value=None):
        self.k = key
        self.v = value
        self.d = {}

class Tree:
    def __init__(self) -> None:
        self.root = {}

    def find(self, path, build=False):
        def _find(node, path):
            if len(path) == 0:
                return node
            if path[0] not in node:
                if not build:
                    return None
                node.d[path[0]] = _Node(path[0])
            return _find(node.d[path[0]], path[1:])
        return _find(self.root, path)

    def set(self, path, value):
        if not isinstance(path, (tuple, list)):
            path = [path]
        pnode = self.find(path[:-1], build=True)
        pnode.d[path[-1]] = _Node(path[-1], value)
        
    
    
