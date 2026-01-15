import sys
from Projetoatualizado.lexer import lexer
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
                   '=': 'EQUAL', '<': 'INF', '>': 'SUP', 
                   '<=': 'INFEQ', '>=': 'SUPEQ',
                   'and': 'MUL', 'or': 'ADD'}

            if op == '<>':
                # Como a VM não tem 'NEQ', fazemos EQUAL + NOT
                self.emit('EQUAL')
                self.emit('NOT')
            else:
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
            val_str = str(node[1]).lower() # Garante que tratamos 'true'/'TRUE' da mesma forma
            if val_str == 'true':
                self.emit('PUSHI 1')
            else:
                self.emit('PUSHI 0')

        elif tipo == 'VAR_LOAD':
            self.check_variable(node[1])
            addr = self.symbol_table[node[1]]['addr']
            self.emit(f'PUSHG {addr}')

        elif tipo == 'ARRAY_LOAD':
            name = node[1]
            self.check_variable(name)
            info = self.symbol_table[name]
            
            # Se for STRING, usa CHARAT
            if info['type'] in ['STRING', 'TYPE_STRING']:
                self.emit(f"PUSHG {info['addr']}") # Stack: [StringRef]
                self.generate(node[2])             # Stack: [StringRef, Indice]
                # Nota: Pascal strings começam em 1, muitas VMs em 0. 
                # Se a VM usar base-0, precisas de: self.emit('PUSHI 1'); self.emit('SUB')
                self.emit('CHARAT')
            
            # Se for ARRAY normal
            elif info['kind'] == 'array':
                self.emit('PUSHGP')
                self.emit(f"PUSHI {info['addr']}")
                self.emit('PADD') 
                self.generate(node[2]) 
                self.emit(f"PUSHI {info['start']}")
                self.emit('SUB') 
                # Sem PADD extra aqui (correção anterior)
                self.emit('LOADN')

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
             # node: ('FOR', var, start, end, body, direction)
             var_name = node[1]
             self.check_variable(var_name)
             start_expr = node[2]
             end_expr = node[3]
             body = node[4]
             direction = node[5] # 'TO' ou 'DOWNTO'
             
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
             
             # --- LÓGICA DO DOWNTO ---
             if direction == 'DOWNTO':
                 self.emit('SUPEQ') # Se i >= fim, continua (loop inverso)
             else:
                 self.emit('INFEQ') # Se i <= fim, continua (loop normal)
             
             self.emit(f'JZ {label_end}')
             
             for stmt in body: self.generate(stmt)
             
             # Incremento/Decremento
             self.emit(f'PUSHG {addr}')
             self.emit('PUSHI 1')
             
             if direction == 'DOWNTO':
                 self.emit('SUB') # i = i - 1
             else:
                 self.emit('ADD') # i = i + 1
                 
             self.emit(f'STOREG {addr}')
             
             self.emit(f'JUMP {label_start}')
             self.emit(f'{label_end}:')

        elif tipo == 'CALL_PROC' or tipo == 'CALL_FUNC':
            name = node[1]
            # O parser pode ou não enviar argumentos dependendo da regra.
            # Se for CALL_FUNC com a nova regra, node[2] são os args.
            args = node[2] if len(node) > 2 else []

            # 1. Função Intrínseca: LENGTH
            if name == 'length':
                # Gera o código do argumento (deve ser uma string)
                if args:
                    self.generate(args[0]) 
                    self.emit('STRLEN') # Transforma StringAddr em Tamanho(Int)
                return

            # 2. Funções de Utilizador
            if name in self.functions:
                # Primeiro: Colocar argumentos na Stack
                for arg in args:
                    self.generate(arg)
                
                # Segundo: Chamar a função
                self.emit(f"PUSHA {self.functions[name]}")
                self.emit("CALL")
            else:
                print(f"Erro: Subprograma '{name}' não definido.")
                sys.exit(1)

    def visit_declarations(self, decls):
        for decl in decls:
            # decl: ('VAR', name, type)
            name = decl[1]
            dtype = decl[2]
            
            # --- ATUALIZAÇÃO: Suporte a Arrays ---
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
                self.emit(f'PUSHI 0') 
                self.emit(f'PUSHN {size-1}') 
                self.address_counter += size
            
            # --- ATUALIZAÇÃO: Suporte a String e Tipos Simples ---
            else:
                # Se for STRING ou TYPE_STRING, tratamos como variável simples (ponteiro)
                kind_type = 'string' if dtype in ['STRING', 'TYPE_STRING'] else dtype
                
                self.symbol_table[name] = {
                    'addr': self.address_counter, 
                    'type': kind_type, 
                    'kind': 'var',
                    'size': 1
                }
                # Se for string, inicializa com string vazia ou 0
                if kind_type == 'string':
                    self.emit('PUSHS ""')
                else:
                    self.emit('PUSHI 0')
                self.address_counter += 1

    def generate_subprogram(self, node):
        if node[0] == 'FUNCTION':
            _, name, args, decls, body, ret_type = node
            # Variável de retorno (mesmo nome da função)
            self.symbol_table[name] = {'addr': self.address_counter, 'type': ret_type, 'kind': 'var', 'size': 1}
            self.emit('PUSHI 0') 
            self.address_counter += 1
        else:
            _, name, args, decls, body = node

        label = self.new_label()
        self.functions[name] = label
        
        self.emit(f'{label}:')
        
        # 1. Argumentos: Registar e Guardar valores da Stack
        # Nota: Quem chama faz Push(Arg1), Push(Arg2). A Stack fica [Arg1, Arg2].
        # Para guardar, temos de fazer POP inverso: Store(Arg2), Store(Arg1).
        if args:
            temp_args = []
            for arg in args:
                # arg: ('VAR', nome, tipo)
                var_name = arg[1]
                var_type = arg[2]
                
                # Regista na tabela de símbolos (SEM emitir PUSHI 0)
                self.symbol_table[var_name] = {
                    'addr': self.address_counter,
                    'type': var_type,
                    'kind': 'var',
                    'size': 1
                }
                temp_args.append(self.address_counter)
                self.address_counter += 1
            
            # Guardar os valores da stack nas variáveis (Ordem Inversa)
            for addr in reversed(temp_args):
                self.emit(f'STOREG {addr}')

        if decls:
            self.visit_declarations(decls)

        # 3. Corpo
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