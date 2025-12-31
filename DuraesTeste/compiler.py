import sys
from lexer import lexer
from parserAndGrammar import parser

class CodeGenerator:
    def __init__(self):
        # Symbol Table agora guarda: {nome: {'addr': int, 'type': str, 'kind': 'var'/'array', 'size': int, 'start': int}}
        self.symbol_table = {} 
        self.address_counter = 0
        self.label_counter = 0
        self.instructions = []
        self.functions = {} # {nome_func: etiqueta_jump}

    def new_label(self):
        self.label_counter += 1
        return f"L{self.label_counter}"

    def emit(self, instr):
        self.instructions.append(instr)

    # Função Auxiliar: Verificação de Erro Semântico
    def check_variable(self, name):
        if name not in self.symbol_table:
            print(f"ERRO SEMÂNTICO: Variável '{name}' não foi declarada.")
            sys.exit(1)

    def generate(self, node):
        if not node: return

        tipo = node[0]

        if tipo == 'PROGRAM':
            # node: ('PROGRAM', nome, decls, subprograms, block)
            
            # 1. Alocar Variáveis Globais
            self.visit_declarations(node[2])
            
            # Jump para saltar por cima das funções
            label_main = self.new_label()
            self.emit(f'JUMP {label_main}')
            
            # 2. Gerar código das Funções
            for sub in node[3]:
                self.generate_subprogram(sub)
                
            self.emit(f'{label_main}:')
            self.emit('START')
            
            # 3. Bloco Principal
            for stmt in node[4]:
                self.generate(stmt)
                
            self.emit('STOP')

        elif tipo == 'ASSIGN':
            self.check_variable(node[1]) # Verifica existência
            self.generate(node[2]) 
            addr = self.symbol_table[node[1]]['addr']
            self.emit(f'STOREG {addr}')

        elif tipo == 'ASSIGN_ARRAY':
            name = node[1]
            self.check_variable(name)
            info = self.symbol_table[name]
            if info['kind'] != 'array':
                print(f"Erro: '{name}' não é um array.")
                sys.exit(1)
            
            self.emit('PUSHGP')
            self.emit(f"PUSHI {info['addr']}")
            self.emit('PADD') # Stack: [BaseAddr]
            
            self.generate(node[2])
            self.emit(f"PUSHI {info['start']}")
            self.emit('SUB') # Stack: [BaseAddr, Indice]
            
            # --- REMOVIDO: self.emit('PADD') ---
            
            self.generate(node[3]) # Stack: [BaseAddr, Indice, Valor]
            
            self.emit('STOREN')

        elif tipo == 'WRITELN':
            # node[1] é uma lista de expressões
            for expr in node[1]:
                if isinstance(expr, str):
                    self.emit(f'PUSHS "{expr}"')
                    self.emit('WRITES')
                else:
                    self.generate(expr)
                    self.emit('WRITEI')
            
            self.emit('PUSHS "\\n"')
            self.emit('WRITES')

        elif tipo == 'READLN':
             self.check_variable(node[1])
             self.emit('READ')
             self.emit('ATOI') 
             addr = self.symbol_table[node[1]]['addr']
             self.emit(f'STOREG {addr}')
        
        elif tipo == 'READLN_ARRAY':
            name = node[1]
            self.check_variable(name)
            info = self.symbol_table[name]
            
            # 1. Colocar Endereço Base na Stack
            self.emit('PUSHGP')
            self.emit(f"PUSHI {info['addr']}")
            self.emit('PADD') # Stack: [BaseAddr]
            
            # 2. Colocar Índice na Stack
            self.generate(node[2]) 
            self.emit(f"PUSHI {info['start']}")
            self.emit('SUB') # Stack: [BaseAddr, Indice]
            
            # --- REMOVIDO: self.emit('PADD') --- 
            # NÃO COMBINAR! O STOREN precisa do endereço e do índice separados.
            
            # 3. Ler valor (Fica no topo da stack)
            self.emit('READ')
            self.emit('ATOI') # Stack: [BaseAddr, Indice, Valor]
            
            # 4. Guardar (Consome os 3 elementos)
            self.emit('STOREN')

        elif tipo == 'BINOP':
            op = node[1]
            self.generate(node[2])
            self.generate(node[3])
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

        elif tipo == 'VAR_LOAD':
            self.check_variable(node[1])
            addr = self.symbol_table[node[1]]['addr']
            self.emit(f'PUSHG {addr}')

        elif tipo == 'ARRAY_LOAD':
            name = node[1]
            self.check_variable(name)
            info = self.symbol_table[name]
            
            self.emit('PUSHGP')
            self.emit(f"PUSHI {info['addr']}")
            self.emit('PADD') # Stack: [BaseAddr]
            
            self.generate(node[2]) 
            self.emit(f"PUSHI {info['start']}")
            self.emit('SUB') # Stack: [BaseAddr, Indice]
            
            # --- REMOVIDO: self.emit('PADD') ---
            
            self.emit('LOADN') # Consome BaseAddr e Indice

        elif tipo == 'IF':
            label_else = self.new_label()
            label_end = self.new_label()
            self.generate(node[1])
            self.emit(f'JZ {label_else}')
            for stmt in node[2]: self.generate(stmt)
            self.emit(f'JUMP {label_end}')
            self.emit(f'{label_else}:')
            if node[3]:
                for stmt in node[3]: self.generate(stmt)
            self.emit(f'{label_end}:')

        elif tipo == 'WHILE':
            label_start = self.new_label()
            label_end = self.new_label()
            self.emit(f'{label_start}:')
            self.generate(node[1])
            self.emit(f'JZ {label_end}')
            for stmt in node[2]: self.generate(stmt)
            self.emit(f'JUMP {label_start}')
            self.emit(f'{label_end}:')
            
        elif tipo == 'FOR':
             var_name = node[1]
             self.check_variable(var_name)
             # (Lógica mantida do anterior)
             start_expr = node[2]
             end_expr = node[3]
             body = node[4]
             
             # Inicializa
             self.generate(start_expr)
             addr = self.symbol_table[var_name]['addr']
             self.emit(f'STOREG {addr}')
             
             label_start = self.new_label()
             label_end = self.new_label()
             
             self.emit(f'{label_start}:')
             # Condição
             self.emit(f'PUSHG {addr}')
             self.generate(end_expr)
             self.emit('INFEQ') # <=
             self.emit(f'JZ {label_end}')
             
             for stmt in body: self.generate(stmt)
             
             # Incremento
             self.emit(f'PUSHG {addr}')
             self.emit('PUSHI 1')
             self.emit('ADD')
             self.emit(f'STOREG {addr}')
             
             self.emit(f'JUMP {label_start}')
             self.emit(f'{label_end}:')

        elif tipo == 'CALL_PROC' or tipo == 'CALL_FUNC':
            name = node[1]
            if name in self.functions:
                self.emit(f"PUSHA {self.functions[name]}")
                self.emit("CALL")
            else:
                print(f"Erro: Subprograma '{name}' não definido.")
                sys.exit(1)

    def visit_declarations(self, decls):
        for decl in decls:
            # decl structure: ('VAR', name, type)
            # type pode ser 'INTEGER' ou ('ARRAY', start, end, subtype)
            name = decl[1]
            dtype = decl[2]
            
            if isinstance(dtype, tuple) and dtype[0] == 'ARRAY':
                start, end = dtype[1], dtype[2]
                size = end - start + 1
                self.symbol_table[name] = {
                    'addr': self.address_counter,
                    'type': dtype[3],
                    'kind': 'array',
                    'size': size,
                    'start': start
                }
                self.emit(f'PUSHI 0') # Inicializa primeiro elemento
                self.emit(f'PUSHN {size-1}') # Reserva resto do espaço
                self.address_counter += size
            else:
                self.symbol_table[name] = {
                    'addr': self.address_counter, 
                    'type': dtype, 
                    'kind': 'var',
                    'size': 1
                }
                self.emit('PUSHI 0')
                self.address_counter += 1

    def generate_subprogram(self, node):
        # node: (TYPE, NAME, DECLS, BODY)
        tipo, name, decls, body = node
        label = self.new_label()
        self.functions[name] = label
        
        self.emit(f'{label}:')
        # Nota: Variáveis locais não implementadas (complexidade scope). 
        # Assumimos que usam variáveis globais por agora.
        for stmt in body:
            self.generate(stmt)
        self.emit('RETURN')

    def get_code(self):
        return "\n".join(self.instructions)

# Main execution block
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python3 compiler.py <ficheiro.pas>")
        sys.exit(1)

    nome_ficheiro = sys.argv[1]
    
    try:
        with open(nome_ficheiro, 'r') as f:
            codigo_pascal = f.read()
            
        print(f"--- A Compilar: {nome_ficheiro} ---")
        ast = parser.parse(codigo_pascal)

        if ast:
            codegen = CodeGenerator()
            codegen.generate(ast)
            assembly = codegen.get_code()
            nome_saida = nome_ficheiro.replace('.pas', '.vm')
            
            with open(nome_saida, "w") as f:
                f.write(assembly)
            print(f"--- Sucesso! Gerado: {nome_saida} ---")
        else:
            print("❌ Erro de Sintaxe (Sem AST gerada).")
            
    except FileNotFoundError:
        print(f"❌ Erro: Ficheiro não encontrado.")