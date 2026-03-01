import tree_sitter_c
from tree_sitter import Language, Parser, Node

class CParser:
    def __init__(self):
        try:
            self.LANGUAGE = Language(tree_sitter_c.language(), "c")
            self.parser = Parser()
            self.parser.set_language(self.LANGUAGE)
        except Exception as e:
            print(f"Error initializing Tree-sitter: {e}")
            raise

    def parse(self, code_str: str):
        """
        Parses the code string and returns the Tree-sitter Tree object.
        """
        if not code_str:
            return None
        
        code_bytes = code_str.encode('utf8')
        
        def read_callable(byte_offset, point):
            return code_bytes[byte_offset:byte_offset + 1024]  # Read in chunks
        
        return self.parser.parse(read_callable)

    def get_errors(self, tree):
        """
        Traverses the tree to find ERROR or MISSING nodes.
        Returns a list of error details.
        """
        errors = []
        if not tree or not tree.root_node:
            return errors
        
        def walk_tree(node):
            # Check if this node is an error
            if node.type == 'ERROR' or node.is_missing:
                errors.append({
                    "type": node.type,
                    "start_point": node.start_point,  # (row, col)
                    "end_point": node.end_point,      # (row, col)
                    "text": node.text.decode('utf8') if node.text else "",
                    "is_missing": node.is_missing
                })
            
            # Recursively check children
            for child in node.children:
                walk_tree(child)
        
        walk_tree(tree.root_node)
        return errors

# Global instance (lazy loaded)
_c_parser_instance = None

def get_parser():
    global _c_parser_instance
    if _c_parser_instance is None:
        _c_parser_instance = CParser()
    return _c_parser_instance

# For backward compatibility
c_parser = type('LazyParser', (), {
    'parse': lambda self, code: get_parser().parse(code),
    'get_errors': lambda self, tree: get_parser().get_errors(tree)
})()
