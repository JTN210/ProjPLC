def visit(self, node):
        if node is None: return
        if isinstance(node, list):
            for n in node: self.visit(n)
            return
        
        # --- CORREÇÃO IMPORTANTE ---
        # 1. Verificar BOOLEAN primeiro!
        # A VM espera 0 ou 1, não "True" ou "False".
        if isinstance(node, bool):
            val = 1 if node else 0
            self.emit(f"PUSHI {val}")
            return 'BOOLEAN'

        # 2. Verificar INTEGER
        if isinstance(node, int):
            self.emit(f"PUSHI {node}")
            return 'INTEGER'

        # 3. Verificar FLOAT (caso uses números reais)
        # A instrução para reais é PUSHF, segundo a documentação
        if isinstance(node, float):
            self.emit(f"PUSHF {node}")
            return 'REAL'

        # 4. Verificar STRING
        if isinstance(node, str):
            # O lexer por vezes mantém as aspas, removemo-las para a VM
            val = node.replace("'", "")
            self.emit(f'PUSHS "{val}"')
            return 'STRING'

        # 5. Visitar Nó da AST (Tuplo)
        if isinstance(node, tuple):
            tipo = node[0]
            metodo = getattr(self, f"visit_{tipo}", self.visit_generico)
            return metodo(node)