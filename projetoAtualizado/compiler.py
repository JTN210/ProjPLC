import sys
from lexer import lexer
from parserAndGrammar import parser

class CodeGenerator:
    def __init__(self):
        self.symbol_table = {} # Globais: nome -> (endereco, start_idx, tipo)
        self.local_table = {}  # Locais: nome -> (indice_na_stack, tipo)
        self.scope = 'GLOBAL'  # Pode ser 'GLOBAL' ou 'LOCAL'
        self.address_counter = 0 # Contador para globais
        self.local_counter = 0   # Contador para locais
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
            # Estrutura nova: ('PROGRAM', nome, funcoes, decls_globais, statements)
            self.emit('START')

            funcoes = node[2]
            for func in funcoes:
                self.generate(func)
            
            declaracoes_globais = node[3]
            self.visit_declarations(declaracoes_globais)
            
            corpo_principal = node[4]
            for stmt in corpo_principal:
                self.generate(stmt)
                
            self.emit('STOP')
        elif tipo == 'ASSIGN':
            self.generate(node[2])
            name = node[1]  
            # No Pascal, "NomeFuncao := Valor" define o retorno.
            # Assumimos que o retorno fica na posição -1 ou 0 do FP, mas
            # para simplificar, vamos tratar como uma variável local se estiver na tabela.
            if self.scope == 'LOCAL' and name in self.local_table:
                idx, _ = self.local_table[name]
                self.emit(f'STOREL {idx}')
            elif name in self.symbol_table:
                addr, _, _ = self.symbol_table[name]
                self.emit(f'STOREG {addr}')

        elif tipo == 'WRITELN': 
            argumentos = node[1]   
            for arg in argumentos:
                if isinstance(arg, tuple) and arg[0] == 'STRING':
                    self.emit(f'PUSHS "{arg[1]}"')
                    self.emit('WRITES')
                else:
                    self.generate(arg)
                    self.emit('WRITEI') # Assume Inteiro por defeito
            
            # Só emite nova linha se for WRITELN
            if tipo == 'WRITELN':
                self.emit('PUSHS "\\n"')
                self.emit('WRITES')

        elif tipo == 'READLN':
             # node: ('READLN', 'nome_da_variavel')
             name = node[1]
             
             # Verificar se é Global ou Local e obter o TIPO
             var_type = None
             offset = 0
             
             if self.scope == 'LOCAL' and name in self.local_table:
                 offset, var_type = self.local_table[name]
                 instruction = f'STOREL {offset}'
             elif name in self.symbol_table:
                 # A tabela global guarda (endereco, start_idx, tipo)
                 entry = self.symbol_table[name]
                 offset = entry[0]
                 var_type = entry[2] # O tipo está na posição 2
                 instruction = f'STOREG {offset}'
             else:
                 print(f"Erro: Variável '{name}' não encontrada para leitura.")
                 return

             # 1. Ler a string do teclado (coloca endereço da Heap na stack)
             self.emit('READ')
             
             # 2. Se a variável for INTEGER, convertemos. Se for STRING, deixamos estar.
             if var_type == 'INTEGER':
                 self.emit('ATOI') # Converte String -> Int
             
             # 3. Guardar na variável
             self.emit(instruction)
             
        elif tipo == 'READLN_ARRAY':
             # node: ('READLN_ARRAY', 'nome_do_array', expressao_indice)
             name = node[1]
             idx_expr = node[2]
             # informações do array
             base_offset, start_index, _ = self.symbol_table[name]
             # CALCULAR O ENDEREÇO DA CÉLULA DO ARRAY
             # Stack começa a receber o endereço base
             self.emit('PUSHGP')           # Ponteiro das globais
             self.emit(f'PUSHI {base_offset}')
             self.emit('ADD')              # Endereço onde começa o array
             
             # Calcular o deslocamento do índice (i - inicio)
             self.generate(idx_expr)       # Gera o valor de 'i'
             self.emit(f'PUSHI {start_index}')
             self.emit('SUB')              # i - start_index
             
             self.emit('ADD')              # Soma tudo. Stack tem: [..., Endereco_Final]
             
             # LER O VALOR
             self.emit('READ')             # Stack: [..., Endereco_Final, String_Lida]
             self.emit('ATOI')             # Stack: [..., Endereco_Final, Valor_Inteiro]
             
             # GUARDAR (STORE 0 usa o endereço que calculámos na stack)
             self.emit('STORE 0')
        
        elif tipo == 'BINOP':
            op = node[1]
            self.generate(node[2])
            # Lógica especial para converter String Literal 'X' em Inteiro ASCII
            # se estivermos numa comparação
            direita = node[3]
            if isinstance(direita, tuple) and direita[0] == 'STRING' and len(direita[1]) == 1:
                self.emit(f'PUSHS "{direita[1]}"') # Mete string "1" na stack
                self.emit('CHRCODE')               # Converte para int 49
            else:
                self.generate(direita)
            
            if op == '<>':
                self.emit('EQUAL')
                self.emit('NOT')

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
            name = node[1]
            # Tenta Local
            if self.scope == 'LOCAL' and name in self.local_table:
                idx, _ = self.local_table[name]
                self.emit(f'PUSHL {idx}') # PUSHL = Push Local
            # Tenta Global
            elif name in self.symbol_table:
                addr, _, _ = self.symbol_table[name]
                self.emit(f'PUSHG {addr}') # PUSHG = Push Global
            else:
                 print(f"Erro: Variável '{name}' não definida.")

        elif tipo == 'ASSIGN_ARRAY':
            # node: ('ASSIGN_ARRAY', 'nome', indice_expr, valor_expr)
            name = node[1]
            base_offset, start_index, _ = self.symbol_table[name]
            
            #CALCULAR O ENDEREÇO ALVO
            self.emit('PUSHGP')          # 1. Pega o ponteiro base das globais
            self.emit(f'PUSHI {base_offset}') 
            self.emit('ADD')             # 2. Soma o offset da variável (Endereço base do array)
            
            self.generate(node[2])       # 3. Gera o código do índice (i)
            self.emit(f'PUSHI {start_index}')
            self.emit('SUB')             # 4. Ajusta o índice (i - start)
            
            self.emit('ADD')             # 5. Endereço Final = Base_Array + (i - start)
            
            #GERAR O VALOR E GUARDAR
            self.generate(node[3])       # 6. Gera o valor a guardar
            self.emit('STORE 0')         # 7. Guarda valor no endereço que está na stack
                                         # (STORE 0 usa o endereço no topo da stack com offset 0)

        elif tipo == 'ARRAY_LOAD':
            # node: ('ARRAY_LOAD', nome_var, expressao_indice)
            name = node[1]
            idx_expr = node[2]

            if self.scope == 'LOCAL' and name in self.local_table:
                stack_idx, var_type = self.local_table[name]

                if var_type == 'STRING_TYPE' or var_type == 'STRING':
                    self.emit(f'PUSHL {stack_idx}') 
                    self.generate(idx_expr)         
                    self.emit('CHARAT')             
                else:
                    # Se fosse array local, lógica seria diferente, mas assumimos array global
                    pass

            # VERIFICAR SE É GLOBAL
            elif name in self.symbol_table:
                # 1. Agora desempacotamos sempre 3 valores para ter o TIPO
                base_addr, start_index, var_type = self.symbol_table[name]

                # 2. Verificamos se é STRING (Global)
                # Strings não usam aritmética de ponteiros direta, usam a instrução CHARAT
                if var_type == 'STRING_TYPE' or var_type == 'STRING':
                    self.emit(f'PUSHG {base_addr}') # PUSHG para globais
                    self.generate(idx_expr)         # Gera o índice
                    self.emit('CHARAT')             # Retorna o código ASCII
                
                # 3. Se for ARRAY normal (Inteiros, etc)
                else:
                    # Calcular o endereço de memória: GP + Offset + (i - start)
                    self.emit('PUSHGP')
                    self.emit(f'PUSHI {base_addr}')
                    self.emit('ADD')

                    self.generate(idx_expr)       # Gera código do índice
                    self.emit(f'PUSHI {start_index}')
                    self.emit('SUB')              # Subtrai o índice inicial

                    self.emit('ADD')              # Soma tudo
                    self.emit('LOAD 0')           # Lê o valor

            else:
                print(f"Erro: Array ou String '{name}' não encontrado/a.")
                
        elif tipo == 'FUNCTION':
            # node: ('FUNCTION', nome, args, tipo_ret, decls_locais, corpo)
            nome_func = node[1]
            args = node[2]
            decls = node[4]
            body = node[5]
            
            # Label para saltar a definição (não executar sem ser chamada)
            label_after_func = self.new_label()
            self.emit(f'JUMP {label_after_func}')
            
            # Rótulo da Função
            self.emit(f'{nome_func}:')
            
            # Mudar Escopo
            antigo_escopo = self.scope
            self.scope = 'LOCAL'
            self.local_table = {}
            self.local_counter = 0 
            
            # --- 1. PROCESSAR ARGUMENTOS ---
            # Os argumentos já estão na stack (Call Stack).
            # Como a stack é LIFO, o último argumento declarado é o que está no topo.
            # Devemos iterar "de trás para a frente" para os guardar nas variáveis locais corretas.
            
            # Ex: function(a, b). Stack tem [a, b]. 
            # Fazemos STOREL b, depois STOREL a.
            
            # Primeiro, registamos os nomes na tabela para sabermos os índices
            lista_args_temp = []
            for _, arg_name, arg_type in args:
                self.local_table[arg_name] = (self.local_counter, arg_type)
                lista_args_temp.append(self.local_counter)
                self.local_counter += 1
            
            # Agora geramos os STOREL na ordem inversa
            for idx in reversed(lista_args_temp):
                self.emit(f'STOREL {idx}')
            
            # --- 2. VARIÁVEL DE RETORNO ---
            # Em Pascal, atribuir ao nome da função define o retorno.
            # Vamos criar uma variável local "extra" com o nome da função.
            idx_retorno = self.local_counter
            self.local_table[nome_func] = (idx_retorno, node[3]) # node[3] é o tipo de retorno
            self.local_counter += 1
            
            # Inicializa retorno com 0 (opcional, mas boa prática)
            self.emit('PUSHI 0')
            self.emit(f'STOREL {idx_retorno}')

            # --- 3. DECLARAÇÕES LOCAIS ---
            self.visit_declarations(decls)
            
            # Reservar espaço para locais (excluindo args que já tratámos, mas incluindo var retorno e decls)
            # Total de vars locais = self.local_counter
            # Já temos args na tabela. Precisamos reservar espaço para o resto.
            num_vars_alocar = self.local_counter - len(args)
            if num_vars_alocar > 0:
                self.emit(f'PUSHN {num_vars_alocar}')

            # --- 4. CORPO ---
            for stmt in body:
                self.generate(stmt)
            
            # --- 5. PREPARAR RETORNO ---
            # Colocar o valor da variável de retorno no topo da stack
            self.emit(f'PUSHL {idx_retorno}')
            
            self.emit('RETURN')
            
            # Restaurar Escopo
            self.scope = antigo_escopo
            self.emit(f'{label_after_func}:')
            
        elif tipo == 'CALL':
            # node: ('CALL', nome_funcao, lista_args)
            func_name = node[1]
            args = node[2]
            # Funções nativas (length) vs Funções do utilizador
            if func_name == 'length':
                self.generate(args[0]) # Argumento (string)
                self.emit('STRLEN')    # Instrução VM para tamanho
            else:
                # Chamada normal
                for arg in args:
                    self.generate(arg)
                self.emit(f'PUSHA {func_name}')
                self.emit('CALL')
                
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
            # node: ('FOR', var, inicio, 'TO'/'DOWNTO', fim, corpo)
            var_name = node[1]
            start_expr = node[2]
            direction = node[3] # 'TO' ou 'DOWNTO'
            end_expr = node[4]
            body = node[5]

            self.generate(('ASSIGN', var_name, start_expr))

            label_start = self.new_label()
            label_end = self.new_label()

            self.emit(f'{label_start}:')
            
            if direction == 'TO':
                op = '<='
            else:
                op = '>='
                
            # Gerar condicao: var <= fim  ou var >= fim
            self.generate(('BINOP', op, ('VAR_LOAD', var_name), end_expr))
            self.emit(f'JZ {label_end}')

            for stmt in body: self.generate(stmt)
            # Incremento ou Decremento
            val = 1
            op_math = '+' if direction == 'TO' else '-'
            
            self.generate(('ASSIGN', var_name, ('BINOP', op_math, ('VAR_LOAD', var_name), ('NUM', 1))))
            
            self.emit(f'JUMP {label_start}')
            self.emit(f'{label_end}:')
            
    def visit_declarations(self, decls):
        for _, name, tipo in decls:
            # ESCOPO GLOBAL 
            if self.scope == 'GLOBAL':
                if name not in self.symbol_table:
                    if isinstance(tipo, tuple) and tipo[0] == 'ARRAY':
                         start, end = tipo[1], tipo[2]
                         tamanho = end - start + 1
                         self.symbol_table[name] = (self.address_counter, start, 'ARRAY')
                         self.address_counter += tamanho
                         self.emit(f'PUSHN {tamanho}')
                    else:
                         # Guardamos também o TIPO
                         self.symbol_table[name] = (self.address_counter, 0, tipo)
                         self.address_counter += 1
                         self.emit('PUSHI 0')
            
            # ESCOPO LOCAL (Dentro de função)
            else: 
                # Nas locais, não usamos endereços de memória, usamos índices da stack (0, 1, 2...)
                if name not in self.local_table:
                    self.local_table[name] = (self.local_counter, tipo)
                    self.local_counter += 1
                    # Nota: Não fazemos PUSHI 0 aqui porque a função CALL já reserva espaço
                    # ou o código da função trata disso.
    def get_code(self):
        return "\n".join(self.instructions)

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
            print(" Erro: Não foi possível gerar a AST (Erro de Sintaxe).")
            
    except FileNotFoundError:
        print(f" Erro: O ficheiro '{nome_ficheiro}' não existe.")
