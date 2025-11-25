
class ErroSemantico(Exception):
    """Exceção para erros semânticos"""
    pass


class Simbolo:
    """Representa um símbolo na tabela de símbolos"""
    def __init__(self, nome, tipo_simbolo, tipo_dados=None, parametros=None, escopo=None):
        self.nome = nome
        self.tipo_simbolo = tipo_simbolo  # 'var', 'funcao', 'procedimento', 'parametro'
        self.tipo_dados = tipo_dados      # 'integer', 'real', 'boolean', 'string', 'char', ('array', ...)
        self.parametros = parametros or []      # Lista de parâmetros para funções/procedimentos
        self.escopo = escopo              # Nome do escopo onde foi declarado


class TabelaSimbolos:
    """Tabela de símbolos com suporte a escopos"""
    def __init__(self):
        self.escopos = [{}]  # Lista de dicionários (pilha de escopos)
        self.escopo_atual = 'global'
        
    def entrar_escopo(self, nome_escopo):
        """Entra num novo escopo (função/procedimento)"""
        self.escopos.append({})
        self.escopo_atual = nome_escopo
        
    def sair_escopo(self):
        """Sai do escopo atual"""
        if len(self.escopos) > 1:
            self.escopos.pop()
            self.escopo_atual = 'global' if len(self.escopos) == 1 else 'local'
            
    def adicionar(self, simbolo):
        """Adiciona um símbolo ao escopo atual"""
        escopo_corrente = self.escopos[-1]
        if simbolo.nome in escopo_corrente:
            raise ErroSemantico(f"Símbolo '{simbolo.nome}' já foi declarado no escopo atual")
        escopo_corrente[simbolo.nome] = simbolo
        
    def procurar(self, nome):
        """Procura um símbolo em todos os escopos (do mais interno para o mais externo)"""
        for escopo in reversed(self.escopos):
            if nome in escopo:
                return escopo[nome]
        return None
        
    def procurar_escopo_atual(self, nome):
        """Procura um símbolo apenas no escopo atual"""
        return self.escopos[-1].get(nome)


class AnalisadorSemantico:
    """Analisador Semântico"""
    
    def __init__(self):
        self.tabela_simbolos = TabelaSimbolos()
        self.erros = []
        self.funcao_atual = None  # Para verificar retorno de funções
        
        # Funções built-in
        self._adicionar_funcoes_internas()
        
    def _adicionar_funcoes_internas(self):
        """Adiciona funções built-in do Pascal"""
        # length(string) -> integer
        funcao_length = Simbolo('length', 'funcao', 'integer', [('parametro', ['s'], 'string')])
        self.tabela_simbolos.adicionar(funcao_length)
        
    def analisar(self, ast):
        """Inicia a análise semântica da AST"""
        try:
            self.visitar(ast)
            if self.erros:
                return False, self.erros
            return True, []
        except ErroSemantico as e:
            self.erros.append(str(e))
            return False, self.erros
            
    def visitar(self, no):
        """Visita um nó da AST"""
        if no is None:
            return None
            
        if isinstance(no, tuple):
            tipo_no = no[0]
            nome_metodo = f'visitar_{tipo_no}'
            visitador = getattr(self, nome_metodo, self.visita_generica)
            return visitador(no)
        elif isinstance(no, list):
            return [self.visitar(item) for item in no]
        else:
            return no  # Literais (números, strings, booleanos)
            
    def visita_generica(self, no):
        """Visita genérica para nós não implementados"""
        if isinstance(no, tuple):
            for filho in no[1:]:
                self.visitar(filho)
        return None
        
    
    # VISITADORES PARA CADA TIPO DE NÓ
    
    def visitar_gramatica(self, no):
        """gramatica : programa"""
        _, programa = no
        return self.visitar(programa)
        
    def visitar_programa(self, no):
        """programa : cabecalho corpo"""
        _, cabecalho, corpo = no
        self.visitar(cabecalho)
        self.visitar(corpo)
        
    def visitar_cabecalho(self, no):
        """cabecalho : titulo subprogramas variaveis"""
        _, titulo, subprogramas, variaveis = no
        self.visitar(titulo)
        self.visitar(subprogramas)
        self.visitar(variaveis)
        
    def visitar_titulo(self, no):
        """titulo : nome_programa"""
        _, nome = no
        # Apenas regista o nome do programa
        return nome
        
    def visitar_var_section(self, no):
        """var_section : lista de declarações"""
        _, declaracoes = no
        if declaracoes:
            self.visitar(declaracoes)
            
    def visitar_var_decl(self, no):
        """var_decl : lista_ids tipo"""
        _, ids, tipo = no
        tipo_dados = self.visitar(tipo)
        
        for nome_var in ids:
            simbolo = Simbolo(nome_var, 'var', tipo_dados, escopo=self.tabela_simbolos.escopo_atual)
            try:
                self.tabela_simbolos.adicionar(simbolo)
            except ErroSemantico as e:
                self.erros.append(str(e))
                
    def visitar_procedure(self, no):
        """procedure : nome parametros declaracoes corpo"""
        if len(no) == 5:
            _, nome, params, declaracoes, corpo = no
        else:
            _, nome, params, bloco = no
            declaracoes, corpo = bloco if isinstance(bloco, tuple) and bloco[0] == 'bloco' else (None, bloco)
            
        # Adiciona procedimento à tabela de símbolos global
        lista_params = self.visitar(params) if params else []
        simbolo_proc = Simbolo(nome, 'procedimento', None, lista_params, 'global')
        
        try:
            self.tabela_simbolos.adicionar(simbolo_proc)
        except ErroSemantico as e:
            self.erros.append(str(e))
            return
            
        # Entra no escopo do procedimento
        self.tabela_simbolos.entrar_escopo(nome)
        
        # Adiciona parâmetros ao escopo local
        for tipo_param, nomes_param, tipo_dados_param in lista_params:
            for nome_param in nomes_param:
                simbolo_param = Simbolo(nome_param, 'parametro', tipo_dados_param, escopo=nome)
                try:
                    self.tabela_simbolos.adicionar(simbolo_param)
                except ErroSemantico as e:
                    self.erros.append(str(e))
                    
        # Visita declarações locais e corpo
        if declaracoes:
            self.visitar(declaracoes)
        self.visitar(corpo)
        
        # Sai do escopo
        self.tabela_simbolos.sair_escopo()
        
    def visitar_function(self, no):
        """function : nome parametros tipo_retorno declaracoes corpo"""
        if len(no) == 6:
            _, nome, params, tipo_retorno, declaracoes, corpo = no
        else:
            _, nome, params, tipo_retorno, bloco = no
            declaracoes, corpo = bloco if isinstance(bloco, tuple) and bloco[0] == 'bloco' else (None, bloco)
            
        # Processa tipo de retorno
        tipo_ret = self.visitar(tipo_retorno) if isinstance(tipo_retorno, tuple) else tipo_retorno
        
        # Adiciona função à tabela de símbolos global
        lista_params = self.visitar(params) if params else []
        simbolo_func = Simbolo(nome, 'funcao', tipo_ret, lista_params, 'global')
        
        try:
            self.tabela_simbolos.adicionar(simbolo_func)
        except ErroSemantico as e:
            self.erros.append(str(e))
            return
            
        # Entra no escopo da função
        self.tabela_simbolos.entrar_escopo(nome)
        self.funcao_atual = nome
        
        # Adiciona parâmetros ao escopo local
        for tipo_param, nomes_param, tipo_dados_param in lista_params:
            for nome_param in nomes_param:
                simbolo_param = Simbolo(nome_param, 'parametro', tipo_dados_param, escopo=nome)
                try:
                    self.tabela_simbolos.adicionar(simbolo_param)
                except ErroSemantico as e:
                    self.erros.append(str(e))
                    
        # Adiciona a própria função como variável (para atribuição de retorno)
        simbolo_ret = Simbolo(nome, 'var', tipo_ret, escopo=nome)
        try:
            self.tabela_simbolos.adicionar(simbolo_ret)
        except ErroSemantico as e:
            pass  # Pode já existir
            
        # Visita declarações locais e corpo
        if declaracoes:
            self.visitar(declaracoes)
        self.visitar(corpo)
        
        # Sai do escopo
        self.tabela_simbolos.sair_escopo()
        self.funcao_atual = None
        
    def visitar_param(self, no):
        """param : ids tipo"""
        _, ids, tipo = no
        tipo_dados = self.visitar(tipo) if isinstance(tipo, tuple) else tipo
        return ('parametro', ids, tipo_dados)
        
    def visitar_bloco(self, no):
        """bloco : declaracoes corpo"""
        _, declaracoes, corpo = no
        if declaracoes:
            self.visitar(declaracoes)
        return self.visitar(corpo)
        
    def visitar_begin_end(self, no):
        """begin_end : lista de instruções"""
        _, instrucoes = no
        if instrucoes:
            self.visitar(instrucoes)
            
    def visitar_assign(self, no):
        """assign : variavel expressao"""
        _, var, expr = no
        
        # Obtém tipo da variável
        tipo_var = self.visitar(var)
        
        # Obtém tipo da expressão
        tipo_expr = self.visitar(expr)
        
        # Verifica compatibilidade de tipos
        if not self._tipos_compativeis(tipo_var, tipo_expr):
            self.erros.append(
                f"Erro de tipo: não é possível atribuir '{tipo_expr}' a '{tipo_var}'"
            )
            
    def visitar_var(self, no):
        """var : nome"""
        _, nome = no
        
        simbolo = self.tabela_simbolos.procurar(nome)
        if simbolo is None:
            self.erros.append(f"Variável '{nome}' não foi declarada")
            return 'desconhecido'
            
        return simbolo.tipo_dados
        
    def visitar_array_access(self, no):
        """array_access : nome indice"""
        _, nome, indice = no
        
        simbolo = self.tabela_simbolos.procurar(nome)
        if simbolo is None:
            self.erros.append(f"Array '{nome}' não foi declarado")
            return 'desconhecido'
            
        # Verifica se é realmente um array
        if not isinstance(simbolo.tipo_dados, tuple) or simbolo.tipo_dados[0] != 'array':
            self.erros.append(f"'{nome}' não é um array")
            return 'desconhecido'
            
        # Verifica se o índice é inteiro
        tipo_indice = self.visitar(indice)
        if tipo_indice != 'integer':
            self.erros.append(f"Índice de array deve ser do tipo 'integer', não '{tipo_indice}'")
            
        # Retorna o tipo dos elementos do array
        return simbolo.tipo_dados[3]  # ('array', inicio, fim, tipo_elemento)
        
    def visitar_call(self, no):
        """call : nome argumentos"""
        _, nome, args = no
        
        simbolo = self.tabela_simbolos.procurar(nome)
        if simbolo is None:
            self.erros.append(f"Função/Procedimento '{nome}' não foi declarado")
            return 'desconhecido'
            
        if simbolo.tipo_simbolo not in ['funcao', 'procedimento']:
            self.erros.append(f"'{nome}' não é uma função ou procedimento")
            return 'desconhecido'
            
        # Verifica número de argumentos
        parametros_esperados = len(simbolo.parametros)
        argumentos_recebidos = len(args) if args else 0
        
        if parametros_esperados != argumentos_recebidos:
            self.erros.append(
                f"'{nome}' espera {parametros_esperados} argumento(s), mas recebeu {argumentos_recebidos}"
            )
            
        # Verifica tipos dos argumentos
        if args:
            tipos_args = [self.visitar(arg) for arg in args]
            for i, (info_param, tipo_arg) in enumerate(zip(simbolo.parametros, tipos_args)):
                tipo_param = info_param[2]  # ('parametro', nomes, tipo)
                if not self._tipos_compativeis(tipo_param, tipo_arg):
                    self.erros.append(
                        f"Argumento {i+1} de '{nome}': esperado tipo '{tipo_param}', mas recebeu '{tipo_arg}'"
                    )
                    
        # Retorna tipo de retorno (se for função)
        return simbolo.tipo_dados if simbolo.tipo_simbolo == 'funcao' else None
        
    def visitar_binop(self, no):
        """binop : operador expr1 expr2"""
        _, op, esquerda, direita = no
        
        tipo_esq = self.visitar(esquerda)
        tipo_dir = self.visitar(direita)
        
        # Operadores aritméticos
        if op in ['+', '-', '*', '/']:
            if tipo_esq not in ['integer', 'real'] or tipo_dir not in ['integer', 'real']:
                self.erros.append(
                    f"Operador '{op}' requer operandos numéricos, mas recebeu '{tipo_esq}' e '{tipo_dir}'"
                )
                return 'desconhecido'
            # Se um é real, resultado é real
            return 'real' if 'real' in [tipo_esq, tipo_dir] else 'integer'
            
        # Operadores inteiros
        elif op in ['div', 'mod']:
            if tipo_esq != 'integer' or tipo_dir != 'integer':
                self.erros.append(
                    f"Operador '{op}' requer operandos do tipo 'integer', mas recebeu '{tipo_esq}' e '{tipo_dir}'"
                )
                return 'desconhecido'
            return 'integer'
            
        # Operadores relacionais
        elif op in ['=', '<>', '<', '<=', '>', '>=']:
            if not self._tipos_compativeis(tipo_esq, tipo_dir):
                self.erros.append(
                    f"Não é possível comparar tipo '{tipo_esq}' com tipo '{tipo_dir}'"
                )
            return 'boolean'
            
        # Operadores lógicos
        elif op in ['and', 'or']:
            if tipo_esq != 'boolean' or tipo_dir != 'boolean':
                self.erros.append(
                    f"Operador '{op}' requer operandos do tipo 'boolean', mas recebeu '{tipo_esq}' e '{tipo_dir}'"
                )
                return 'desconhecido'
            return 'boolean'
            
        return 'desconhecido'
        
    def visitar_unop(self, no):
        """unop : operador expr"""
        _, op, expr = no
        
        tipo_expr = self.visitar(expr)
        
        if op == 'not':
            if tipo_expr != 'boolean':
                self.erros.append(f"Operador 'not' requer operando do tipo 'boolean', não '{tipo_expr}'")
                return 'desconhecido'
            return 'boolean'
            
        elif op in ['+', '-']:
            if tipo_expr not in ['integer', 'real']:
                self.erros.append(f"Operador unário '{op}' requer operando numérico, não '{tipo_expr}'")
                return 'desconhecido'
            return tipo_expr
            
        return 'desconhecido'
        
    def visitar_if(self, no):
        """if : condicao parte_then parte_else"""
        _, condicao, parte_then, parte_else = no
        
        # Verifica se a condição é booleana
        tipo_cond = self.visitar(condicao)
        if tipo_cond != 'boolean':
            self.erros.append(f"Condição do IF deve ser do tipo 'boolean', não '{tipo_cond}'")
            
        self.visitar(parte_then)
        if parte_else:
            self.visitar(parte_else)
            
    def visitar_while(self, no):
        """while : condicao corpo"""
        _, condicao, corpo = no
        
        # Verifica se a condição é booleana
        tipo_cond = self.visitar(condicao)
        if tipo_cond != 'boolean':
            self.erros.append(f"Condição do WHILE deve ser do tipo 'boolean', não '{tipo_cond}'")
            
        self.visitar(corpo)
        
    def visitar_for(self, no):
        """for : var inicio fim direcao corpo"""
        _, var, inicio, fim, direcao, corpo = no
        
        # Verifica se a variável existe e é inteira
        simbolo = self.tabela_simbolos.procurar(var)
        if simbolo is None:
            self.erros.append(f"Variável '{var}' do FOR não foi declarada")
        elif simbolo.tipo_dados != 'integer':
            self.erros.append(f"Variável do FOR deve ser do tipo 'integer', não '{simbolo.tipo_dados}'")
            
        # Verifica se início e fim são inteiros
        tipo_inicio = self.visitar(inicio)
        tipo_fim = self.visitar(fim)
        
        if tipo_inicio != 'integer':
            self.erros.append(f"Valor inicial do FOR deve ser do tipo 'integer', não '{tipo_inicio}'")
        if tipo_fim != 'integer':
            self.erros.append(f"Valor final do FOR deve ser do tipo 'integer', não '{tipo_fim}'")
            
        self.visitar(corpo)
        
    def visitar_readln(self, no):
        """readln : lista de variáveis"""
        _, vars = no
        if vars:
            for var in vars:
                self.visitar(var)
                
    def visitar_read(self, no):
        """read : lista de variáveis"""
        return self.visitar_readln(no)
        
    def visitar_writeln(self, no):
        """writeln : lista de expressões"""
        _, exprs = no
        if exprs:
            for expr in exprs:
                self.visitar(expr)
                
    def visitar_write(self, no):
        """write : lista de expressões"""
        return self.visitar_writeln(no)
        
    def visitar_array(self, no):
        """array : inicio fim tipo_elemento"""
        _, inicio, fim, tipo_elem = no
        tipo_elem_resolvido = self.visitar(tipo_elem) if isinstance(tipo_elem, tuple) else tipo_elem
        return ('array', inicio, fim, tipo_elem_resolvido)
        
    
    # FUNÇÕES AUXILIARES
        
    def _tipos_compativeis(self, tipo1, tipo2):
        """Verifica se dois tipos são compatíveis"""
        if tipo1 == 'desconhecido' or tipo2 == 'desconhecido':
            return True  # Não reporta erro se já houve erro anterior
            
        # Tipos iguais são compatíveis
        if tipo1 == tipo2:
            return True
            
        # Integer pode ser promovido para real
        if (tipo1 == 'real' and tipo2 == 'integer') or \
           (tipo1 == 'integer' and tipo2 == 'real'):
            return True
            
        # Boolean true/false são compatíveis com boolean
        if (tipo1 == 'boolean' and tipo2 in [True, False]) or \
           (tipo2 == 'boolean' and tipo1 in [True, False]):
            return True
            
        return False


# FUNÇÃO PRINCIPAL PARA TESTAR

def analisar_ficheiro(nome_ficheiro):
    """Analisa um arquivo Pascal semanticamente"""
    from yacc import parse_file
    
    print(f"\n{'='*60}")
    print(f"ANÁLISE SEMÂNTICA: {nome_ficheiro}")
    print(f"{'='*60}\n")
    
    # Parse do arquivo
    ast = parse_file(nome_ficheiro)
    
    if not ast:
        print("✗ Falha na análise sintática - análise semântica cancelada")
        return False
        
    # Análise semântica
    analisador = AnalisadorSemantico()
    sucesso, erros = analisador.analisar(ast)
    
    if sucesso:
        print("\n✓ Análise semântica concluída com sucesso!")
        print("✓ Nenhum erro semântico encontrado")
        return True
    else:
        print("\n✗ Erros semânticos encontrados:")
        for i, erro in enumerate(erros, 1):
            print(f"  {i}. {erro}")
        return False


def analisar_codigo(codigo):
    """Analisa código Pascal semanticamente"""
    from yacc import parse_string
    
    ast = parse_string(codigo)
    
    if not ast:
        return False, ["Falha na análise sintática"]
        
    analisador = AnalisadorSemantico()
    return analisador.analisar(ast)


if __name__ == '__main__':
    # Teste com código correto
    teste_correto = """
    program Teste;
    var
        x, y: integer;
        z: real;
    begin
        x := 5;
        y := x + 10;
        z := x + y;
        writeln(z);
    end.
    """
    
    print("TESTE 1: Código Correto")
    print("="*60)
    sucesso, erros = analisar_codigo(teste_correto)
    if sucesso:
        print("✓ Análise semântica passou!")
    else:
        print("✗ Erros encontrados:")
        for erro in erros:
            print(f"  - {erro}")
    
    # Teste com erros
    teste_erros = """
    program TesteErro;
    var
        x: integer;
    begin
        y := 5;
        x := true;
        if x then
            writeln('erro');
    end.
    """
    
    print("\n\nTESTE 2: Código com Erros")
    print("="*60)
    sucesso, erros = analisar_codigo(teste_erros)
    if sucesso:
        print("✓ Análise semântica passou!")
    else:
        print("✗ Erros encontrados (esperado):")
        for erro in erros:
            print(f"  - {erro}")