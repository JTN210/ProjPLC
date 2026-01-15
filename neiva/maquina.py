import sys
from sin import parse_file

class GeradorCodigo:
    def __init__(self):
        self.codigo = []
        self.contador_labels = 0
        self.tabela_simbolos = {}  # {nome: {'addr': int, 'size': int}}
        self.endereco_atual = 0
        self.funcoes = {} 
        self.funcao_atual = None 
        self.info_arrays = {}  # {nome: {'min': int, 'max': int}}
        self.funcoes_processadas = set()  # Para evitar duplicação

    def novo_label(self):
        self.contador_labels += 1
        return f"label{self.contador_labels}"
    
    def obter_endereco(self, nome_var, size=1):
        if nome_var not in self.tabela_simbolos:
            self.tabela_simbolos[nome_var] = {
                'addr': self.endereco_atual,
                'size': size
            }
            self.endereco_atual += size
        return self.tabela_simbolos[nome_var]['addr']

    def emitir(self, op, arg=None):
        if arg is None:
            self.codigo.append(f"{op}")
        else:
            self.codigo.append(f"{op} {arg}")

    def visit(self, node):
        if node is None: return
        if isinstance(node, list):
            for item in node: self.visit(item)
            return

        if isinstance(node, bool):
            valor = 1 if node else 0
            self.emitir('PUSHI', valor)
            return

        if isinstance(node, int):
            self.emitir('PUSHI', node)
            return
        if isinstance(node, float):
            self.emitir('PUSHF', node)
            return
        if isinstance(node, str):
            self.emitir('PUSHS', f'"{node}"') 
            return
        
        if isinstance(node, tuple):
            tipo = node[0]
            metodo = getattr(self, f'visit_{tipo}', self.visit_generico)
            metodo(node)

    def visit_var_decl(self, node):
        """Processa declarações de variáveis para alocar espaço para arrays"""
        _, lista_id, tipo_raw = node
        
        if isinstance(tipo_raw, tuple) and tipo_raw[0] == 'array':
            # tipo_raw = ('array', min, max, tipo_base)
            min_idx = tipo_raw[1]
            max_idx = tipo_raw[2]
            tamanho = max_idx - min_idx + 1
            
            for nome_var in lista_id:
                self.obter_endereco(nome_var, tamanho)
                self.info_arrays[nome_var] = {'min': min_idx, 'max': max_idx}
        else:
            # Variável simples
            for nome_var in lista_id:
                self.obter_endereco(nome_var, 1)

    def visit_declaracao_subprogramas(self, node):
        # Este método NÃO deve ser chamado - é apenas para debugging
        pass
    
    def visit_procedure(self, node):
        _, nome, params, corpo = node
        
        lbl_proc = nome
        self.funcoes[nome] = lbl_proc
        
        self.emitir('LABEL', f"{lbl_proc}:")
        
        # Guardar parametros da pilha nas variaveis
        if params:
            todos_params = []
            for p in params:
                todos_params.extend(p[1]) 
            
            for param_id in reversed(todos_params):
                addr = self.obter_endereco(param_id, 1)
                self.emitir('STOREG', addr)

        old_func = self.funcao_atual
        self.funcao_atual = nome
        
        # Processar declarações de variáveis locais
        if corpo and corpo[0] == 'bloco':
            decls_locais = corpo[1]
            if decls_locais:
                self.processar_declaracoes(decls_locais)
        
        self.visit(corpo)
        
        self.emitir('RETURN') 
        self.funcao_atual = old_func 

    # ==========================
    # ESTRUTURA E BLOCOS
    # ==========================

    def visit_gramatica(self, node): 
        self.visit(node[1]) 
    
    def visit_programa(self, node):
        label_main = "main"
        
        self.emitir('JUMP', label_main)
        
        # node = ('programa', cabecalho, corpo)
        # cabecalho = ('cabecalho', titulo, declaracao_subprogramas, declaracoes_variaveis)
        cabecalho = node[1]
        
        # Primeiro: processar variáveis globais
        if len(cabecalho) > 3 and cabecalho[3]:  # vars_globais
            self.processar_declaracoes(cabecalho[3])
        
        # Segundo: gerar código dos subprogramas
        if len(cabecalho) > 2 and cabecalho[2]:  # subprogramas
            subprogs = cabecalho[2]
            # subprogs é uma lista de funções/procedures
            if isinstance(subprogs, list):
                for subprog in subprogs:
                    if subprog:  # Evitar None
                        self.visit(subprog)
        
        # Terceiro: gerar o main
        self.emitir('LABEL', f"{label_main}:")
        self.emitir('START')
        self.visit(node[2])  # corpo principal
        self.emitir('STOP')

    def visit_cabecalho(self, node):
        # Não fazer nada aqui - tudo é processado em visit_programa
        pass

    def processar_declaracoes(self, var_section):
        """Processa declarações para alocar endereços"""
        if var_section and var_section[0] == 'var_section':
            for decl in var_section[1]:
                if decl[0] == 'var_decl':
                    self.visit_var_decl(decl)

    def visit_bloco(self, node):
        _, decls, corpo = node
        self.visit(corpo)
    
    def visit_function(self, node):
        nome = node[1]
        
        # Evitar processar a mesma função duas vezes
        if nome in self.funcoes_processadas:
            return
        self.funcoes_processadas.add(nome)
        
        params = node[2]
        corpo = node[4]
        
        lbl_func = nome
        self.funcoes[nome] = lbl_func
        
        self.emitir('LABEL', f"{lbl_func}:")
        
        # Alocar espaço para a variável de retorno
        self.obter_endereco(nome, 1)
        
        # Os parâmetros JÁ ESTÃO NA PILHA quando CALL é executado
        if params:
            todos_params = []
            for p in params:
                todos_params.extend(p[1]) 
            
            for param_id in reversed(todos_params):
                addr = self.obter_endereco(param_id, 1)
                self.emitir('STOREG', addr)

        old_func = self.funcao_atual
        self.funcao_atual = nome
        
        # Processar declarações de variáveis locais
        if corpo and corpo[0] == 'bloco':
            decls_locais = corpo[1]
            if decls_locais:
                self.processar_declaracoes(decls_locais)
        
        self.visit(corpo)
        
        addr_ret = self.tabela_simbolos[nome]['addr']
        self.emitir('PUSHG', addr_ret)
        
        self.emitir('RETURN') 
        self.funcao_atual = old_func
        # Alocar espaço para a variável de retorno (mesmo nome da função)
        self.obter_endereco(nome, 1)
        
        # Guardar parametros da pilha nas variaveis
        if params:
            todos_params = []
            for p in params:
                todos_params.extend(p[1]) 
            
            for param_id in reversed(todos_params):
                addr = self.obter_endereco(param_id, 1)
                self.emitir('STOREG', addr)

        old_func = self.funcao_atual
        self.funcao_atual = nome
        
        # Processar declarações de variáveis locais da função
        if corpo and corpo[0] == 'bloco':
            decls_locais = corpo[1]
            if decls_locais:
                self.processar_declaracoes(decls_locais)
        
        # Visitar o corpo (agora vai chamar visit_bloco)
        self.visit(corpo)
        
        # Retorno - empurra o valor da variável com nome da função
        addr_ret = self.tabela_simbolos[nome]['addr']
        self.emitir('PUSHG', addr_ret)
        
        self.emitir('RETURN') 
        self.funcao_atual = old_func

    # ==========================
    # CHAMADAS E ACESSOS
    # ==========================

    def visit_call(self, node):
        nome = node[1]
        args = node[2]
        
        if nome.lower() == 'length':
            if args:
                self.visit(args[0])
                self.emitir('STRLEN') 
            return

        if nome in self.funcoes:
            for arg in args:
                self.visit(arg)
            
            lbl = self.funcoes[nome]
            self.emitir('PUSHA', lbl) 
            self.emitir('CALL')       
        else:
            print(f"Erro: Função '{nome}' não definida.")

    def visit_array_access(self, node):
        nome_var = node[1]
        expr_index = node[2]
        
        # Para strings, usar CHARAT
        if nome_var not in self.info_arrays:
            # É uma string
            addr = self.tabela_simbolos[nome_var]['addr']
            self.emitir('PUSHG', addr)
            
            self.visit(expr_index)
            self.emitir('PUSHI', 1)
            self.emitir('SUB')  # Converter índice Pascal (1-based) para 0-based
            
            self.emitir('CHARAT')
        else:
            # É um array de inteiros/reais
            addr_base = self.tabela_simbolos[nome_var]['addr']
            min_idx = self.info_arrays[nome_var]['min']
            
            # Empurrar ponteiro global
            self.emitir('PUSHGP')
            
            # Calcular offset
            self.visit(expr_index)
            self.emitir('PUSHI', min_idx)
            self.emitir('SUB')
            self.emitir('PUSHI', addr_base)
            self.emitir('ADD')
            
            # Adicionar offset ao ponteiro
            self.emitir('PADD')
            
            # Empurrar offset interno (0)
            self.emitir('PUSHI', 0)
            
            # LOADN: carrega valor de address[offset]
            self.emitir('LOADN') 

    # ==========================
    # INSTRUÇÕES
    # ==========================

    def visit_begin_end(self, node): 
        self.visit(node[1])
    
    def visit_assign(self, node):
        _, var_node, expr_node = node
        
        # Se é acesso a array
        if var_node[0] == 'array_access':
            nome_array = var_node[1]
            expr_index = var_node[2]
            
            addr_base = self.tabela_simbolos[nome_array]['addr']
            
            if nome_array in self.info_arrays:
                min_idx = self.info_arrays[nome_array]['min']
            else:
                min_idx = 1
            
            # Avaliar a expressão do lado direito
            self.visit(expr_node)
            
            # Calcular o offset: índice - min_idx
            self.visit(expr_index)
            self.emitir('PUSHI', min_idx)
            self.emitir('SUB')
            
            # Adicionar ao endereço base
            self.emitir('PUSHI', addr_base)
            self.emitir('ADD')
            
            # Agora temos [valor, endereço_final] na pilha
            # Trocar para [endereço_final, valor]
            self.emitir('SWAP')
            
            # STOREL: store in gp[n] onde n vem da pilha
            # Mas STOREL não existe... vamos usar PUSHGP + PADD + indexação
            
            # Na verdade, a solução é usar STOREL que opera em fp
            # Mas para variáveis globais, precisamos de outra abordagem
            
            # Solução: usar STOREG com offset calculado manualmente
            # Para isso, precisamos gerar código assembly mais baixo nível
            
            # Última tentativa: STOREN com parâmetros corretos
            # STOREN: takes a value v, an integer n and an address a and stores v in a[n]
            self.emitir('PUSHI', 0)  # offset dentro do endereço (sempre 0)
            self.emitir('STOREN')
            
        elif var_node[0] == 'var':
            self.visit(expr_node)
            nome = var_node[1]
            addr = self.tabela_simbolos[nome]['addr']
            self.emitir('STOREG', addr)

    def visit_writeln(self, node):
        exprs = node[1]
        for expr in exprs:
            self.visit(expr)
            # Determinar o tipo de saída baseado no tipo da expressão
            if isinstance(expr, str):
                self.emitir('WRITES')
            elif isinstance(expr, float):
                self.emitir('WRITEF')
            elif isinstance(expr, int) or isinstance(expr, bool):
                self.emitir('WRITEI')
            elif isinstance(expr, tuple):
                # Para expressões complexas, assumir inteiro por padrão
                # (idealmente deveria haver análise de tipos aqui)
                self.emitir('WRITEI')
        self.emitir('WRITELN')

    def visit_write(self, node):
        exprs = node[1]
        for expr in exprs:
            self.visit(expr)
            if isinstance(expr, str):
                self.emitir('WRITES')
            elif isinstance(expr, float):
                self.emitir('WRITEF')
            elif isinstance(expr, int) or isinstance(expr, bool):
                self.emitir('WRITEI')
            elif isinstance(expr, tuple):
                self.emitir('WRITEI')

    def visit_readln(self, node):
        for var_node in node[1]:
            self.emitir('READ')
            
            # READ sempre retorna um endereço de string no String Heap
            # NÃO converter automaticamente - deixar como string
            # Se o programa precisar de inteiro, ele que faça a conversão explícita
            
            if var_node[0] == 'var':
                addr = self.tabela_simbolos[var_node[1]]['addr']
                self.emitir('STOREG', addr)
                
            elif var_node[0] == 'array_access':
                # Para arrays, guardar o endereço da string
                nome_array = var_node[1]
                expr_index = var_node[2]
                
                addr_base = self.tabela_simbolos[nome_array]['addr']
                min_idx = self.info_arrays.get(nome_array, {}).get('min', 1)
                
                # Usar variável temporária
                temp_val = self.endereco_atual
                self.endereco_atual += 1
                
                # Guardar o valor lido
                self.emitir('STOREG', temp_val)
                
                # Calcular endereço do array
                self.emitir('PUSHGP')
                self.visit(expr_index)
                self.emitir('PUSHI', min_idx)
                self.emitir('SUB')
                self.emitir('PUSHI', addr_base)
                self.emitir('ADD')
                self.emitir('PADD')
                
                # Empilhar [address, 0, valor]
                self.emitir('PUSHI', 0)
                self.emitir('PUSHG', temp_val)
                
                self.emitir('STOREN')

    def visit_read(self, node):
        self.visit_readln(node)

    def visit_if(self, node):
        _, cond, stmt_then, stmt_else = node
        lbl_else = self.novo_label()
        lbl_fim = self.novo_label()
        self.visit(cond)
        self.emitir('JZ', lbl_else if stmt_else else lbl_fim)
        self.visit(stmt_then)
        if stmt_else:
            self.emitir('JUMP', lbl_fim)
            self.emitir('LABEL', f'{lbl_else}:')
            self.visit(stmt_else)
        self.emitir('LABEL', f'{lbl_fim}:')

    def visit_while(self, node):
        lbl_ini = self.novo_label()
        lbl_fim = self.novo_label()
        self.emitir('LABEL', f'{lbl_ini}:')
        self.visit(node[1])
        self.emitir('JZ', lbl_fim)
        self.visit(node[2])
        self.emitir('JUMP', lbl_ini)
        self.emitir('LABEL', f'{lbl_fim}:')

    def visit_for(self, node):
        _, var, ini, fim, dir, corpo = node
        lbl_ini, lbl_fim = self.novo_label(), self.novo_label()
        addr = self.tabela_simbolos[var]['addr']
        
        # Inicialização
        self.visit(ini)
        self.emitir('STOREG', addr)
        
        # Loop
        self.emitir('LABEL', f'{lbl_ini}:')
        self.emitir('PUSHG', addr)
        self.visit(fim)
        
        # Condição: queremos CONTINUAR enquanto a condição é verdadeira
        if dir == 'to':
            # Para 'to': continua se var <= fim
            self.emitir('SUP')  # var > fim?
            self.emitir('NOT')  # inverte: agora é var <= fim
        else:  # downto
            # Para 'downto': continua se var >= fim
            self.emitir('INF')  # var < fim?
            self.emitir('NOT')  # inverte: agora é var >= fim
        
        self.emitir('JZ', lbl_fim)  # salta se falso (sai do loop)
        
        # Corpo do loop
        self.visit(corpo)
        
        # Incremento/Decremento
        self.emitir('PUSHG', addr)
        self.emitir('PUSHI', 1)
        if dir == 'to':
            self.emitir('ADD')
        else:  # downto
            self.emitir('SUB')
        self.emitir('STOREG', addr)
        
        self.emitir('JUMP', lbl_ini)
        self.emitir('LABEL', f'{lbl_fim}:')

    def visit_binop(self, node):
        _, op, l, r = node
        self.visit(l)
        self.visit(r)
        
        ops = {
            '+': 'ADD', '-': 'SUB', '*': 'MUL', '/': 'DIV', 
            'DIV': 'DIV', 'div': 'DIV',
            'MOD': 'MOD', 'mod': 'MOD', 
            'and': 'AND', 'or': 'OR', 
            '=': 'EQUAL', '<': 'INF', '>': 'SUP', 
            '<=': 'INFEQ', '>=': 'SUPEQ'
        }
        
        if op in ops:
            self.emitir(ops[op])
        elif op in ['<>', '!=']:
            self.emitir('EQUAL')
            self.emitir('NOT')

    def visit_unop(self, node):
        _, op, e = node
        self.visit(e)
        if op == 'not':
            self.emitir('NOT')
        elif op == '-':
            self.emitir('PUSHI', -1)
            self.emitir('MUL')

    def visit_var(self, node):
        nome = node[1]
        addr = self.tabela_simbolos[nome]['addr']
        self.emitir('PUSHG', addr)

# --- MAIN ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 maquina.py <ficheiro.pas>")
        sys.exit(1)
    filename = sys.argv[1]
    ast = parse_file(filename)
    if ast:
        gerador = GeradorCodigo()
        gerador.visit(ast)
        nome_saida = filename.replace('.pas', '.vm')
        if nome_saida == filename: 
            nome_saida += ".vm"
        try:
            with open(nome_saida, "w") as f:
                for instr in gerador.codigo:
                    if instr.startswith('LABEL') or instr.endswith(':'):
                        clean_instr = instr.replace('LABEL ', '')
                        f.write(f"{clean_instr}\n")
                    else:
                        f.write(f"\t{instr}\n")
            print(f"✅ Sucesso! {nome_saida}")
        except Exception as e: 
            print(f"Erro ao escrever ficheiro: {e}")