import sys
from sin import parse_string

class GeradorCodigo:
    def __init__(self):
        self.codigo = []
        self.contador_labels = 0
        self.tabela_simbolos = {} 
        self.endereco_atual = 0

    def novo_label(self):
        self.contador_labels += 1
        return f"L{self.contador_labels}"
    
    def obter_endereco(self, nome_var):
        if nome_var not in self.tabela_simbolos:
            self.tabela_simbolos[nome_var] = self.endereco_atual
            self.endereco_atual += 1
        return self.tabela_simbolos[nome_var]

    def emitir(self, op, arg=None):
        if arg is None:
            self.codigo.append((op,))
        else:
            self.codigo.append((op, arg))

    def visit(self, node):
        if node is None: return
        if isinstance(node, list):
            for item in node: self.visit(item)
            return

        # Literais
        if isinstance(node, int):
            self.emitir('PUSHI', node)
            return
        if isinstance(node, float):
            self.emitir('PUSHF', node)
            return
        if isinstance(node, str):
            # IMPORTANTE: Strings precisam de aspas na VM
            self.emitir('PUSHS', f'"{node}"') 
            return
        
        # Tuplas AST
        if isinstance(node, tuple):
            tipo = node[0]
            metodo = getattr(self, f'visit_{tipo}', self.visit_generico)
            metodo(node)

    def visit_generico(self, node):
        pass 

    # --- Estrutura ---
    def visit_gramatica(self, node):
        self.visit(node[1]) 

    def visit_programa(self, node):
        _, cabecalho, corpo = node
        self.visit(corpo)
        self.emitir('STOP') 

    # --- Instruções ---
    def visit_begin_end(self, node):
        self.visit(node[1])

    def visit_assign(self, node):
        _, var_node, expr_node = node
        self.visit(expr_node)
        
        if var_node[0] == 'var':
            nome = var_node[1]
            addr = self.obter_endereco(nome)
            self.emitir('STOREG', addr)
        else:
            print("Aviso: Arrays não implementados totalmente neste gerador simples.")

    def visit_writeln(self, node):
        for expr in node[1]:
            self.visit(expr)
            # CORREÇÃO PRINCIPAL:
            # Se for string literal (Python str na AST) -> WRITES
            # Se for variável ou expressão -> Assumimos Inteiro -> WRITEI
            if isinstance(expr, str):
                self.emitir('WRITES')
            else:
                self.emitir('WRITEI')

    def visit_readln(self, node):
        for var_node in node[1]:
            self.emitir('READ') # Lê string
            self.emitir('ATOI') # Converte para Inteiro
            if var_node[0] == 'var':
                nome = var_node[1]
                addr = self.obter_endereco(nome)
                self.emitir('STOREG', addr)

    def visit_if(self, node):
        _, cond, stmt_then, stmt_else = node
        label_else = self.novo_label()
        label_fim = self.novo_label()

        self.visit(cond)
        if stmt_else:
            self.emitir('JZ', label_else)
        else:
            self.emitir('JZ', label_fim)

        self.visit(stmt_then)
        
        if stmt_else:
            self.emitir('JUMP', label_fim)
            self.emitir('LABEL', label_else)
            self.visit(stmt_else)
        
        self.emitir('LABEL', label_fim)

    def visit_while(self, node):
        label_inicio = self.novo_label()
        label_fim = self.novo_label()

        self.emitir('LABEL', label_inicio)
        self.visit(node[1]) 
        self.emitir('JZ', label_fim)
        self.visit(node[2])
        self.emitir('JUMP', label_inicio)
        self.emitir('LABEL', label_fim)

    def visit_for(self, node):
        _, var_nome, inicio, fim, direcao, corpo = node
        label_inicio = self.novo_label()
        label_fim = self.novo_label()

        addr = self.obter_endereco(var_nome)
        self.visit(inicio)
        self.emitir('STOREG', addr)

        self.emitir('LABEL', label_inicio)
        
        self.emitir('PUSHG', addr)
        self.visit(fim)
        
        if direcao == 'to':
            self.emitir('INF_EQ') # <=
        else:
            self.emitir('SUP_EQ') # >=

        self.emitir('JZ', label_fim)

        self.visit(corpo)

        self.emitir('PUSHG', addr)
        self.emitir('PUSHI', 1)
        if direcao == 'to':
            self.emitir('ADD')
        else:
            self.emitir('SUB')
        self.emitir('STOREG', addr)

        self.emitir('JUMP', label_inicio)
        self.emitir('LABEL', label_fim)

    # Expressões
    def visit_binop(self, node):
        _, op, left, right = node
        self.visit(left)
        self.visit(right)
        
        if op == '+': self.emitir('ADD')
        elif op == '-': self.emitir('SUB')
        elif op == '*': self.emitir('MUL')
        elif op == '/': self.emitir('DIV')
        elif op == 'DIV': self.emitir('DIV')
        elif op == 'MOD': self.emitir('MOD')
        elif op == '=': self.emitir('EQUAL')
        elif op == '<': self.emitir('INF')
        elif op == '>': self.emitir('SUP')
        elif op == '<=': self.emitir('INF_EQ')
        elif op == '>=': self.emitir('SUP_EQ')
        elif op.lower() == 'and': 
            self.emitir('MUL') # Truque: 1*1=1, 1*0=0
        elif op.lower() == 'or':
            self.emitir('ADD') # Truque simplificado (nota: 1+1=2, requer normalização num compilador real)

    def visit_var(self, node):
        nome = node[1]
        addr = self.obter_endereco(nome)
        self.emitir('PUSHG', addr)
        
if __name__ == "__main__":
    codigo_fonte = """
    program Fatorial;
    var n, i, fat: integer;
    begin
        writeln('Calculo Fatorial');
        readln(n);
        fat := 1;
        i := 1;
        while i < n do
        begin
            i := i + 1;
            fat := fat * i;
        end;
        write(fat);
    end.
    """
    
    # 1. Gerar AST
    # Nota: O parse_string imprime mensagens de debug ("Analisando...", "Sucesso"). 
    # Idealmente, remove esses prints do sin.py se quiseres output 100% limpo,
    # mas para copiar o código assembly, basta ignorares o texto inicial.
    ast = parse_string(codigo_fonte)
    
    if ast:
        gerador = GeradorCodigo()
        gerador.visit(ast)
        # 2. Imprimir APENAS o código Assembly
        print("\n\n")
        for instr in gerador.codigo:
            if instr[0] == 'LABEL':
                print(f"{instr[1]}:")
            else:
                args = f" {instr[1]}" if len(instr) > 1 else ""
                print(f"{instr[0]}{args}")
        print("\n")