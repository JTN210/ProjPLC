import sys
from lexer import lexer
from parserAndGrammar import parser

class CodeGenerator:
    def __init__(self):
        self.symbol_table = {} # Mapa: nome_variavel -> endereco_gp
        self.address_counter = 0
        self.label_counter = 0
        self.instructions = []

    def new_label(self):
        self.label_counter += 1
        return f"L{self.label_counter}"

    def emit(self, instr):
        self.instructions.append(instr)

    def generate(self, node):
        if not node: return

        # node é um tuplo. node[0] é o tipo.
        tipo = node[0]

        if tipo == 'PROGRAM':
            # node: ('PROGRAM', nome, declaracoes, statements)
            self.emit('START')
            # 1. Processar variáveis (Alocar espaço)
            self.visit_declarations(node[2])
            # 2. Processar código
            for stmt in node[3]:
                self.generate(stmt)
            self.emit('STOP')

        elif tipo == 'ASSIGN':
            # node: ('ASSIGN', 'nome_var', expr)
            self.generate(node[2]) # Gera código para calcular a expressão (resultado fica no topo da stack)
            addr = self.symbol_table[node[1]]
            self.emit(f'STOREG {addr}')

        elif tipo == 'WRITELN':
            if isinstance(node[1], str) and not node[1].startswith('('): 
                # É uma string literal (hack simples)
                self.emit(f'PUSHS "{node[1]}"')
                self.emit('WRITES')
            else:
                # É uma expressão
                self.generate(node[1])
                self.emit('WRITEI')
            self.emit('PUSHS "\\n"')
            self.emit('WRITES')

        elif tipo == 'READLN':
             self.emit('READ')
             self.emit('ATOI') # Assumindo inteiros
             addr = self.symbol_table[node[1]]
             self.emit(f'STOREG {addr}')

        elif tipo == 'BINOP':
            op = node[1]
            self.generate(node[2]) # Esq
            self.generate(node[3]) # Dir
            ops = {'+': 'ADD', '-': 'SUB', '*': 'MUL', '/': 'DIV', 
                   'div': 'DIV', 'mod': 'MOD',
                   '=': 'EQUAL', '<': 'INF', '>': 'SUP', '<=': 'INFEQ', '>=': 'SUPEQ',
                    'and': 'MUL', 'or': 'ADD'}
            self.emit(ops[op])

        elif tipo == 'UNOP':
            op = node[1]
            self.generate(node[2])
            if op == 'not':
                self.emit('PUSHI 0')
                self.emit('EQUAL')

        elif tipo == 'NUM':
            self.emit(f'PUSHI {node[1]}')

        elif tipo == 'BOOL':
            val = 1 if node[1] == 'true' else 0
            self.emit(f'PUSHI {val}')

        elif tipo == 'VAR_LOAD':
            addr = self.symbol_table[node[1]]
            self.emit(f'PUSHG {addr}')

        elif tipo == 'IF':
            # node: ('IF', condicao, bloco_then, bloco_else)
            label_else = self.new_label()
            label_end = self.new_label()

            self.generate(node[1]) # Condição
            self.emit(f'JZ {label_else}') # Se falso, salta para o Else
            
            # Bloco Then
            for stmt in node[2]: self.generate(stmt)
            self.emit(f'JUMP {label_end}')
            
            self.emit(f'{label_else}:')
            # Bloco Else
            if node[3]:
                for stmt in node[3]: self.generate(stmt)
            
            self.emit(f'{label_end}:')

        elif tipo == 'WHILE':
            # node: ('WHILE', condicao, bloco_do)
            label_start = self.new_label()
            label_end = self.new_label()

            self.emit(f'{label_start}:')
            self.generate(node[1]) # Condição
            self.emit(f'JZ {label_end}')
            
            for stmt in node[2]: self.generate(stmt)
            self.emit(f'JUMP {label_start}') # Loop
            
            self.emit(f'{label_end}:')

        elif tipo == 'FOR':
            # Converte o for em assign inicial + while implícito
            var_name = node[1]
            start_expr = node[2]
            end_expr = node[3]
            body = node[4]

            # Inicializa a variável do loop
            init_assign = ('ASSIGN', var_name, start_expr)
            self.generate(init_assign)

            label_start = self.new_label()
            label_end = self.new_label()

            self.emit(f'{label_start}:')
            condition = ('BINOP', '<=', ('VAR_LOAD', var_name), end_expr)
            self.generate(condition)
            self.emit(f'JZ {label_end}')

            for stmt in body: self.generate(stmt)

            increment = ('ASSIGN', var_name, ('BINOP', '+', ('VAR_LOAD', var_name), ('NUM', 1)))
            self.generate(increment)
            self.emit(f'JUMP {label_start}')
            self.emit(f'{label_end}:')


    def visit_declarations(self, decls):
        # decls é uma lista de ('VAR', nome, tipo)
        for _, name, _ in decls:
            if name not in self.symbol_table:
                self.symbol_table[name] = self.address_counter
                self.address_counter += 1
                self.emit('PUSHI 0') # Inicializa com 0 na stack global

    def get_code(self):
        return "\n".join(self.instructions)

# --- Main ---
# ... (todo o código da classe CodeGenerator fica igual) ...

if __name__ == '__main__':
    import sys
    
    # Verifica se o utilizador passou um ficheiro
    if len(sys.argv) < 2:
        print("Uso: python3 compiler.py <ficheiro.pas>")
        sys.exit(1)

    nome_ficheiro = sys.argv[1]
    
    try:
        with open(nome_ficheiro, 'r') as f:
            codigo_pascal = f.read()
            
        print(f"--- A Compilar: {nome_ficheiro} ---")
        ast = parser.parse(codigo_pascal)
        print(ast)

        if ast:
            codegen = CodeGenerator()
            codegen.generate(ast)
            assembly = codegen.get_code()

            nome_saida = nome_ficheiro.replace('.pas', '.vm')
            
            print(f"--- Sucesso! ---")
            print(f"Código gerado em: {nome_saida}")
            
            with open(nome_saida, "w") as f:
                f.write(assembly)
        else:
            print("❌ Erro: Não foi possível gerar a AST (Erro de Sintaxe).")
            
    except FileNotFoundError:
        print(f"❌ Erro: O ficheiro '{nome_ficheiro}' não existe.")