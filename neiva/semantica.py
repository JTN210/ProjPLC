
from sin import parse_string

class TabelaSimbolos:
    def __init__(self):
        # A tabela é uma lista de dicionários (pilha de escopos)
        # O índice 0 é o escopo global
        self.escopos = [{}]
        # Dicionário separado para funções/procedimentos para validar assinaturas e parâmetros
        # Formato: { 'nome': { 'tipo_retorno': '...', 'params': ['TIPO1', 'TIPO2'] } }
        self.funcoes = {} 

    def entrar_escopo(self):
        self.escopos.append({})

    def sair_escopo(self):
        self.escopos.pop()

    def declarar_variavel(self, nome, tipo, detalhes=None):
        # Declara no escopo atual (o último da lista)
        escopo_atual = self.escopos[-1]
        if nome in escopo_atual:
            return False  # Erro: Variável já existe neste escopo
        # Guarda o tipo e detalhes (útil para arrays)
        escopo_atual[nome] = {'tipo': tipo, 'detalhes': detalhes}
        return True

    def procurar_variavel(self, nome):
        # Procura do escopo atual até ao global (de trás para a frente)
        for escopo in reversed(self.escopos):
            if nome in escopo:
                return escopo[nome]
        return None

    def declarar_funcao(self, nome, tipo_retorno, params):
        if nome in self.funcoes:
            return False
        self.funcoes[nome] = {'tipo_retorno': tipo_retorno, 'params': params}
        return True

    def procurar_funcao(self, nome):
        return self.funcoes.get(nome)


class AnalisadorSemantico:
    def __init__(self):
        self.tabela = TabelaSimbolos()
        self.erros = []
        self.tipo_retorno_atual = None # Para verificar se o return da função coincide

    def registar_erro(self, msg):
        self.erros.append(f"Erro Semântico: {msg}")

    def visit(self, node):
        """Método despachante que visita o nó apropriado baseado no tipo"""
        if node is None:
            return None
        
        # Se for uma lista (ex: lista de instruções), visita cada elemento
        if isinstance(node, list):
            for item in node:
                self.visit(item)
            return

        # Se for um valor primitivo, retorna o seu tipo em Pascal
        if isinstance(node, (int, float, str, bool)):
            if isinstance(node, bool): return 'BOOLEAN'
            if isinstance(node, int): return 'INTEGER'
            if isinstance(node, float): return 'REAL'
            if isinstance(node, str): return 'STRING'

        # Se for uma tupla da AST: ('tipo_no', dados...)
        if isinstance(node, tuple):
            tipo_no = node[0]
            # Constrói o nome do método: visit_program, visit_var_decl, etc.
            metodo_nome = f'visit_{tipo_no}'
            # Tenta chamar o método, se não existir chama o genérico
            visitante = getattr(self, metodo_nome, self.visit_generico)
            return visitante(node)
        
        return None

    def visit_generico(self, node):
        # Útil para debug se aparecer algum nó novo não tratado
        # print(f"AVISO: Nó não tratado na análise semântica: {node[0]}")
        return None

    # --------------------------------------------------------------------------
    # 1. ESTRUTURA DO PROGRAMA
    # --------------------------------------------------------------------------

    def visit_gramatica(self, node):
        # Tupla gerada em sin.py: ('gramatica', programa)
        self.visit(node[1])

    def visit_programa(self, node):
        # Tupla: ('programa', cabecalho, corpo)
        _, cabecalho, corpo = node
        self.visit(cabecalho) # Processa declarações globais
        self.visit(corpo)     # Processa o bloco principal

    def visit_cabecalho(self, node):
        # Tupla: ('cabecalho', titulo, declaracao_subprogramas, declaracoes_variaveis)
        _, titulo, subprogs, vars_globais = node
        
        # Nota: O Pascal permite recursão e chamadas forward.
        # No entanto, conforme a gramática, vamos processar na ordem.
        
        # Processar variáveis globais
        if vars_globais:
            self.visit(vars_globais)
            
        # Processar subprogramas (funções e procedimentos)
        if subprogs:
            self.visit(subprogs)

    # --------------------------------------------------------------------------
    # 2. DECLARAÇÕES DE VARIÁVEIS
    # --------------------------------------------------------------------------

    def visit_var_section(self, node):
        # Tupla: ('var_section', [lista_de_declaracoes])
        self.visit(node[1])

    def visit_var_decl(self, node):
        # Tupla: ('var_decl', [lista_ids], tipo)
        _, lista_id, tipo_raw = node
        
        # Verificar se é um array ou um tipo simples
        tipo_final = str(tipo_raw).upper()
        detalhes_array = None

        # Na tua gramática, tipo_array retorna: ('array', min, max, tipo_base)
        if isinstance(tipo_raw, tuple) and tipo_raw[0] == 'array':
            tipo_final = 'ARRAY'
            detalhes_array = tipo_raw 

        for nome_var in lista_id:
            sucesso = self.tabela.declarar_variavel(nome_var, tipo_final, detalhes_array)
            if not sucesso:
                self.registar_erro(f"A variável '{nome_var}' já foi declarada neste escopo.")

    # --------------------------------------------------------------------------
    # 3. SUBPROGRAMAS (PROCEDURES E FUNCTIONS)
    # --------------------------------------------------------------------------

    def visit_function(self, node):
        # Tupla: ('function', nome, params, tipo_retorno, corpo)
        _, nome, params, tipo_ret, corpo = node
        
        # Coletar tipos dos parâmetros para a assinatura da função
        tipos_params = []
        if params:
            for p in params:
                # p format: ('param', [ids], tipo)
                tipo_p = str(p[2]).upper()
                quantidade = len(p[1]) # Quantos IDs têm este tipo
                for _ in range(quantidade):
                    tipos_params.append(tipo_p)

        tipo_ret_str = str(tipo_ret).upper()
        
        # Regista a função no escopo global (ou atual)
        if not self.tabela.declarar_funcao(nome, tipo_ret_str, tipos_params):
            self.registar_erro(f"A função '{nome}' já se encontra definida.")

        # --- Entrar no escopo da função ---
        self.tabela.entrar_escopo()
        self.tipo_retorno_atual = tipo_ret_str

        # Em Pascal, o nome da função é usado como variável de retorno
        self.tabela.declarar_variavel(nome, tipo_ret_str)

        # Declarar parâmetros como variáveis locais
        if params:
            for p in params:
                ids_params = p[1]
                tipo_p = str(p[2]).upper()
                for pid in ids_params:
                    self.tabela.declarar_variavel(pid, tipo_p)

        # Visita o corpo (que contém declarações locais + instruções)
        self.visit(corpo)

        self.tabela.sair_escopo()
        self.tipo_retorno_atual = None

    def visit_procedure(self, node):
        # Tupla: ('procedure', nome, params, corpo)
        _, nome, params, corpo = node
        
        tipos_params = []
        if params:
            for p in params:
                tipo_p = str(p[2]).upper()
                quantidade = len(p[1])
                for _ in range(quantidade):
                    tipos_params.append(tipo_p)

        # Procedure tem retorno None
        if not self.tabela.declarar_funcao(nome, None, tipos_params):
            self.registar_erro(f"O procedimento '{nome}' já se encontra definido.")

        self.tabela.entrar_escopo()

        if params:
            for p in params:
                ids_params = p[1]
                tipo_p = str(p[2]).upper()
                for pid in ids_params:
                    self.tabela.declarar_variavel(pid, tipo_p)

        self.visit(corpo)
        self.tabela.sair_escopo()

    def visit_bloco(self, node):
        # Tupla: ('bloco', declaracoes_variaveis, corpo)
        _, decls, corpo_instrucoes = node
        if decls:
            self.visit(decls)
        self.visit(corpo_instrucoes)

    # --------------------------------------------------------------------------
    # 4. INSTRUÇÕES E CONTROLE DE FLUXO
    # --------------------------------------------------------------------------

    def visit_begin_end(self, node):
        # Tupla: ('begin_end', [lista_instrucoes])
        self.visit(node[1])

    def visit_assign(self, node):
        # Tupla: ('assign', variavel, expressao)
        _, var_node, expr_node = node
        
        # Determinar tipo da variável (L-Value) e da expressão (R-Value)
        tipo_var = self.visit(var_node)
        tipo_expr = self.visit(expr_node)

        if tipo_var and tipo_expr:
            # Tipos iguais são sempre compatíveis
            if tipo_var == tipo_expr:
                return
            
            # Pascal permite atribuir Integer a uma variável Real (coerção implícita)
            if tipo_var == 'REAL' and tipo_expr == 'INTEGER':
                return
            
            self.registar_erro(f"Atribuição incompatível: tentou atribuir '{tipo_expr}' à variável do tipo '{tipo_var}'.")

    def visit_if(self, node):
        # Tupla: ('if', condicao, then_stmt, else_stmt)
        _, cond, stmt_then, stmt_else = node
        
        tipo_cond = self.visit(cond)
        if tipo_cond != 'BOOLEAN':
            self.registar_erro(f"A condição do IF deve ser BOOLEAN. Recebido: {tipo_cond}")
        
        self.visit(stmt_then)
        if stmt_else:
            self.visit(stmt_else)

    def visit_while(self, node):
        # Tupla: ('while', condicao, corpo)
        _, cond, corpo = node
        tipo_cond = self.visit(cond)
        if tipo_cond != 'BOOLEAN':
            self.registar_erro(f"A condição do WHILE deve ser BOOLEAN. Recebido: {tipo_cond}")
        self.visit(corpo)

    def visit_for(self, node):
        # Tupla: ('for', id_variavel, inicio, fim, direcao, corpo)
        _, var_nome, inicio, fim, direcao, corpo = node
        
        # Verificar variável de controlo
        var_info = self.tabela.procurar_variavel(var_nome)
        if not var_info:
            self.registar_erro(f"A variável de controlo do FOR '{var_nome}' não foi declarada.")
        elif var_info['tipo'] != 'INTEGER':
            self.registar_erro(f"A variável de controlo do FOR deve ser INTEGER.")

        # Verificar limites
        t_inicio = self.visit(inicio)
        t_fim = self.visit(fim)
        
        if t_inicio != 'INTEGER' or t_fim != 'INTEGER':
            self.registar_erro("Os limites do ciclo FOR devem ser inteiros.")
            
        self.visit(corpo)

    # --------------------------------------------------------------------------
    # 5. EXPRESSÕES
    # --------------------------------------------------------------------------

    def visit_binop(self, node):
        # Tupla: ('binop', operador, esquerda, direita)
        _, op, esq, dir_node = node
        
        t_esq = self.visit(esq)
        t_dir = self.visit(dir_node)

        # Se algum dos operandos já deu erro antes, aborta para não gerar ruído
        if not t_esq or not t_dir:
            return None 

        # Operações Aritméticas
        if op in ['+', '-', '*', '/', 'DIV', 'MOD']:
            is_int = (t_esq == 'INTEGER' and t_dir == 'INTEGER')
            is_num = (t_esq in ['INTEGER', 'REAL'] and t_dir in ['INTEGER', 'REAL'])

            if not is_num:
                self.registar_erro(f"O operador aritmético '{op}' requer números. Recebido: {t_esq}, {t_dir}")
                return 'REAL' # Retorna um tipo dummy para evitar cascata de erros

            if op == '/': return 'REAL' # Divisão real resulta sempre em REAL
            
            if op in ['DIV', 'MOD']:
                if not is_int:
                    self.registar_erro(f"Os operadores DIV e MOD requerem operandos inteiros.")
                return 'INTEGER'
            
            # Para +, -, * : Se houver um Real, o resultado é Real
            if t_esq == 'REAL' or t_dir == 'REAL':
                return 'REAL'
            return 'INTEGER'

        # Operações Relacionais
        if op in ['=', '<>', '!=', '<', '<=', '>', '>=']:
            if t_esq != t_dir:
                # Exceção: Permite comparar int com real
                if not (t_esq in ['INTEGER', 'REAL'] and t_dir in ['INTEGER', 'REAL']):
                     self.registar_erro(f"Comparação inválida entre tipos {t_esq} e {t_dir}.")
            return 'BOOLEAN'

        # Operações Lógicas
        if op.lower() in ['and', 'or']:
            if t_esq != 'BOOLEAN' or t_dir != 'BOOLEAN':
                self.registar_erro(f"O operador lógico '{op}' requer operandos BOOLEAN.")
            return 'BOOLEAN'

        return None

    def visit_unop(self, node):
        # Tupla: ('unop', op, operando)
        _, op, operand = node
        t = self.visit(operand)
        
        if op.lower() == 'not':
            if t != 'BOOLEAN': self.registar_erro("O operador NOT requer BOOLEAN.")
            return 'BOOLEAN'
        if op in ['+', '-']:
            if t not in ['INTEGER', 'REAL']: self.registar_erro(f"O sinal unário '{op}' requer um número.")
            return t
        return t

    # --------------------------------------------------------------------------
    # 6. ACESSO A VARIÁVEIS E CHAMADAS
    # --------------------------------------------------------------------------

    def visit_var(self, node):
        # Tupla: ('var', ID)
        nome = node[1]
        info = self.tabela.procurar_variavel(nome)
        if not info:
            self.registar_erro(f"A variável '{nome}' não foi declarada.")
            return None
        return info['tipo']

    def visit_array_access(self, node):
        # Tupla: ('array_access', nome, indice_expr)
        _, nome, expr_index = node
        info = self.tabela.procurar_variavel(nome)
        
        if not info:
            self.registar_erro(f"O array '{nome}' não foi declarado.")
            return None
        
        if info['tipo'] != 'ARRAY':
            self.registar_erro(f"A variável '{nome}' não é do tipo array.")
            return info['tipo']

        t_index = self.visit(expr_index)
        if t_index != 'INTEGER':
            self.registar_erro("O índice do array deve ser do tipo INTEGER.")

        # Retorna o tipo base do array guardado nos detalhes
        # detalhes = ('array', min, max, tipo_base)
        return str(info['detalhes'][3]).upper()

    def visit_call(self, node):
        # Tupla: ('call', nome, [lista_args])
        _, nome, args = node

        # Caso especial: LENGTH (built-in)
        if nome.lower() == 'length':
            if len(args) != 1:
                self.registar_erro("A função 'length' requer exatamente 1 argumento.")
            self.visit(args[0])
            return 'INTEGER'

        func_info = self.tabela.procurar_funcao(nome)
        if not func_info:
            self.registar_erro(f"O subprograma '{nome}' não foi declarado.")
            return None

        params_esperados = func_info['params']
        if len(args) != len(params_esperados):
            self.registar_erro(f"A chamada a '{nome}' espera {len(params_esperados)} argumentos, mas recebeu {len(args)}.")
            return func_info['tipo_retorno']

        # Validar tipos dos argumentos
        for i, (arg_node, tipo_esperado) in enumerate(zip(args, params_esperados)):
            tipo_passado = self.visit(arg_node)
            if tipo_passado != tipo_esperado:
                # Exceção: Passar Integer onde se espera Real é válido
                if not (tipo_esperado == 'REAL' and tipo_passado == 'INTEGER'):
                    self.registar_erro(f"Argumento {i+1} de '{nome}' incompatível: esperava {tipo_esperado}, recebeu {tipo_passado}.")

        return func_info['tipo_retorno']

    def visit_readln(self, node): # Trata também o read
        # Tupla: ('readln', [lista_vars])
        for v in node[1]:
            self.visit(v)
            # Verifica se estamos a ler para uma variável válida e existente
            if isinstance(v, tuple) and v[0] == 'var':
                if not self.tabela.procurar_variavel(v[1]):
                    self.registar_erro(f"A variável '{v[1]}' usada no read/readln não existe.")
    
    def visit_read(self, node):
        self.visit_readln(node)

    def visit_writeln(self, node): # Trata também o write
        # Tupla: ('writeln', [lista_exprs])
        for expr in node[1]:
            self.visit(expr)
            
    def visit_write(self, node):
        self.visit_writeln(node)


# --------------------------------------------------------------------------
# FUNÇÕES PARA EXECUÇÃO E TESTE
# --------------------------------------------------------------------------

def analisar_semantica(codigo):
    """
    Função principal que integra o parser e a análise semântica.
    Recebe o código fonte como string.
    """
    ast = parse_string(codigo)
    if ast:
        analisador = AnalisadorSemantico()
        try:
            analisador.visit(ast)
            if not analisador.erros:
                print("✓ Análise Semântica: SUCESSO! O código é válido.")
                return True
            else:
                print("✗ Foram encontrados Erros Semânticos:")
                for erro in analisador.erros:
                    print(f"  - {erro}")
                return False
        except Exception as e:
            print(f"Erro interno no analisador: {e}")
            # Importa traceback apenas para debug em caso de crash
            import traceback
            traceback.print_exc()
            return False
    else:
        print("✗ A análise foi interrompida devido a erros de sintaxe.")
        return False

if __name__ == '__main__':
    # Teste com o Exemplo 5 (Função BinToInt) do enunciado
    codigo_teste = """
    program BinarioParaInteiro;
    
    function BinToInt(bin: string): integer;
    var
        i, valor, potencia: integer;
    begin
        valor := 0;
        potencia := 1;
        for i := length(bin) downto 1 do
        begin
            if bin[i] = '1' then
                valor := valor + potencia;
            potencia := potencia * 2;
        end;
        BinToInt := valor;
    end;
    
    var
        bin: string;
        valor: integer;
    begin
        writeln('Introduza uma string binária:');
        readln(bin);
        valor := BinToInt(bin);
        writeln('O valor inteiro correspondente é: ', valor);
    end.
    """
    
    print("=" * 60)
    print("TESTE SEMÂNTICO: Exemplo BinToInt")
    print("=" * 60)
    analisar_semantica(codigo_teste)

    # Teste de Erros para verificar a validação
    print("\n" + "=" * 60)
    print("TESTE DE ERROS COMUNS")
    print("=" * 60)
    codigo_erro = """
    program Erros;
    var x: integer;
    begin
        x := 'texto';       { Erro: String para Integer }
        naoExiste := 10;    { Erro: Variável não declarada }
        if x then x := 1;   { Erro: If sem booleano }
    end.
    """
    analisar_semantica(codigo_erro)