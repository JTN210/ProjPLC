import ply.yacc as yacc
from lex import tokens, lexer
#--------------------------- FEITO PELO CLAUDE NÃO SEI SE ESTÁ BEM --------------------------------
#------------------------------------ MAS PARECE ESTAR BEM ----------------------------------------
# Precedência e associatividade dos operadores
precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('right', 'NOT'),
    ('left', 'EQUALS', 'NOT_EQUALS', 'LESS_THAN', 'LESS_THAN_OR_EQUAL_TO', 
             'GREATER_THAN', 'GREATER_THAN_OR_EQUAL_TO'),
    ('left', '+', '-'),
    ('left', '*', '/', 'DIV', 'MOD'),
    ('right', 'UMINUS'),  # Para menos unário
)


# 1. ESTRUTURA PRINCIPAL DO PROGRAMA

def p_gramatica(p):
    '''gramatica : programa '.' '''
    p[0] = ('gramatica', p[1])


def p_programa(p):
    '''programa : cabecalho corpo'''
    p[0] = ('programa', p[1], p[2])


def p_cabecalho(p):
    '''cabecalho : titulo declaracao_subprogramas declaracoes_variaveis'''
    p[0] = ('cabecalho', p[1], p[2], p[3])


def p_titulo(p):
    '''titulo : PROGRAM ID ';' '''
    p[0] = ('titulo', p[2])


# 2. DECLARAÇÃO DE SUBPROGRAMAS (PROCEDURES E FUNCTIONS)

def p_declaracao_subprogramas(p):
    '''declaracao_subprogramas : declaracao_subprogramas procedure_declaration
                               | declaracao_subprogramas function_declaration
                               | empty'''
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = p[1] + [p[2]]


def p_procedure_declaration(p):
    '''procedure_declaration : PROCEDURE ID ';' bloco_subprograma ';'
                             | PROCEDURE ID '(' parametros ')' ';' bloco_subprograma ';' '''
    if len(p) == 6:
        p[0] = ('procedure', p[2], [], p[4])
    else:
        p[0] = ('procedure', p[2], p[4], p[7])


def p_function_declaration(p):
    '''function_declaration : FUNCTION ID ':' tipo ';' bloco_subprograma ';'
                            | FUNCTION ID '(' parametros ')' ':' tipo ';' bloco_subprograma ';' '''
    if len(p) == 8:
        p[0] = ('function', p[2], [], p[4], p[6])
    else:
        p[0] = ('function', p[2], p[4], p[7], p[9])


def p_bloco_subprograma(p):
    '''bloco_subprograma : declaracoes_variaveis corpo'''
    p[0] = ('bloco', p[1], p[2])


def p_parametros(p):
    '''parametros : lista_parametros
                  | empty'''
    p[0] = p[1] if p[1] else []


def p_lista_parametros(p):
    '''lista_parametros : lista_id ':' tipo
                        | lista_id ':' tipo ';' lista_parametros'''
    if len(p) == 4:
        p[0] = [('param', p[1], p[3])]
    else:
        p[0] = [('param', p[1], p[3])] + p[5]


# 3. DECLARAÇÕES DE VARIÁVEIS

def p_declaracoes_variaveis(p):
    '''declaracoes_variaveis : VAR declaracoes
                             | empty'''
    if len(p) == 3:
        p[0] = ('var_section', p[2])
    else:
        p[0] = None


def p_declaracoes(p):
    '''declaracoes : declaracao
                   | declaracao declaracoes'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[2]


def p_declaracao(p):
    '''declaracao : lista_id ':' tipo ';' '''
    p[0] = ('var_decl', p[1], p[3])


def p_lista_id(p):
    '''lista_id : ID
                | lista_id ',' ID'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]


# 4. TIPOS

def p_tipo(p):
    '''tipo : INTEGER
            | REAL
            | BOOLEAN
            | CHAR
            | STRING
            | tipo_array'''
    p[0] = p[1] if isinstance(p[1], str) else p[1]


def p_tipo_array(p):
    '''tipo_array : ARRAY '[' NUMBER RANGE NUMBER ']' OF tipo'''
    p[0] = ('array', p[3], p[5], p[8])


# 5. CORPO DO PROGRAMA

def p_corpo(p):
    '''corpo : BEGIN lista_instrucoes END'''
    p[0] = ('begin_end', p[2])


def p_lista_instrucoes(p):
    '''lista_instrucoes : instrucao
                        | lista_instrucoes ';' instrucao'''
    if len(p) == 2:
        p[0] = [p[1]] if p[1] is not None else []
    else:
        p[0] = p[1] + ([p[3]] if p[3] is not None else [])


# 6. INSTRUÇÕES

def p_instrucao(p):
    '''instrucao : atribuicao
                 | leitura
                 | escrita
                 | if_statement
                 | while_statement
                 | for_statement
                 | chamada_procedimento
                 | bloco
                 | empty'''
    p[0] = p[1]


def p_bloco(p):
    '''bloco : BEGIN lista_instrucoes END'''
    p[0] = ('begin_end', p[2])


def p_atribuicao(p):
    '''atribuicao : variavel ASSIGN expressao'''
    p[0] = ('assign', p[1], p[3])


def p_chamada_procedimento(p):
    '''chamada_procedimento : ID '(' lista_expressao ')'
                            | ID'''
    if len(p) == 2:
        p[0] = ('call', p[1], [])
    else:
        p[0] = ('call', p[1], p[3])


# 7. COMANDOS DE ENTRADA/SAÍDA

def p_leitura(p):
    '''leitura : READ '(' lista_variaveis ')'
               | READLN '(' lista_variaveis ')'
               | READLN'''
    if len(p) == 2:
        p[0] = ('readln', [])
    elif p[1].lower() == 'read':
        p[0] = ('read', p[3])
    else:
        p[0] = ('readln', p[3])


def p_escrita(p):
    '''escrita : WRITE '(' lista_expressao ')'
               | WRITELN '(' lista_expressao ')'
               | WRITELN'''
    if len(p) == 2:
        p[0] = ('writeln', [])
    elif p[1].lower() == 'write':
        p[0] = ('write', p[3])
    else:
        p[0] = ('writeln', p[3])


def p_lista_variaveis(p):
    '''lista_variaveis : variavel
                       | lista_variaveis ',' variavel'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]


# 8. ESTRUTURAS DE CONTROLE

def p_if_statement(p):
    '''if_statement : IF expressao THEN instrucao
                    | IF expressao THEN instrucao ELSE instrucao'''
    if len(p) == 5:
        p[0] = ('if', p[2], p[4], None)
    else:
        p[0] = ('if', p[2], p[4], p[6])


def p_while_statement(p):
    '''while_statement : WHILE expressao DO instrucao'''
    p[0] = ('while', p[2], p[4])


def p_for_statement(p):
    '''for_statement : FOR ID ASSIGN expressao TO expressao DO instrucao
                     | FOR ID ASSIGN expressao DOWNTO expressao DO instrucao'''
    p[0] = ('for', p[2], p[4], p[6], p[5].lower(), p[8])


# 9. EXPRESSÕES (HIERARQUIA COMPLETA)

def p_lista_expressao(p):
    '''lista_expressao : expressao
                       | lista_expressao ',' expressao'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]


def p_expressao(p):
    '''expressao : expressao_logica'''
    p[0] = p[1]


def p_expressao_logica(p):
    '''expressao_logica : expressao_logica OR expressao_relacional
                        | expressao_logica AND expressao_relacional
                        | expressao_relacional'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ('binop', p[2].lower(), p[1], p[3])


def p_expressao_relacional(p):
    '''expressao_relacional : expressao_aritmetica operador_relacional expressao_aritmetica
                            | expressao_aritmetica'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ('binop', p[2], p[1], p[3])


def p_operador_relacional(p):
    '''operador_relacional : EQUALS
                           | NOT_EQUALS
                           | LESS_THAN
                           | LESS_THAN_OR_EQUAL_TO
                           | GREATER_THAN
                           | GREATER_THAN_OR_EQUAL_TO'''
    p[0] = p[1]


def p_expressao_aritmetica(p):
    '''expressao_aritmetica : expressao_aritmetica '+' termo
                            | expressao_aritmetica '-' termo
                            | termo'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ('binop', p[2], p[1], p[3])


def p_termo(p):
    '''termo : termo '*' fator
             | termo '/' fator
             | termo DIV fator
             | termo MOD fator
             | fator'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ('binop', p[2].lower() if isinstance(p[2], str) and p[2].isupper() else p[2], p[1], p[3])


def p_fator(p):
    '''fator : NUMBER
             | REAL_NUMBER
             | STRING_LITERAL
             | TRUE
             | FALSE
             | variavel
             | chamada_funcao
             | '(' expressao ')' '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[2]


def p_fator_not(p):
    '''fator : NOT fator'''
    p[0] = ('unop', 'not', p[2])


def p_fator_menos_unario(p):
    '''fator : '-' fator %prec UMINUS'''
    p[0] = ('unop', '-', p[2])


def p_fator_mais_unario(p):
    '''fator : '+' fator %prec UMINUS'''
    p[0] = ('unop', '+', p[2])


# 10. VARIÁVEIS E CHAMADAS DE FUNÇÃO

def p_variavel(p):
    '''variavel : ID
                | ID '[' expressao ']' '''
    if len(p) == 2:
        p[0] = ('var', p[1])
    else:
        p[0] = ('array_access', p[1], p[3])


def p_chamada_funcao(p):
    '''chamada_funcao : ID '(' lista_expressao ')'
                      | LENGTH '(' expressao ')' '''
    if len(p) == 5 and p[1].lower() == 'length':
        p[0] = ('call', 'length', [p[3]])
    else:
        p[0] = ('call', p[1], p[3])


# 11. REGRA VAZIA

def p_empty(p):
    '''empty :'''
    pass


# 12. TRATAMENTO DE ERROS

def p_error(p):
    if p:
        print(f"Erro de sintaxe no token '{p.value}' (tipo: {p.type}) na linha {p.lineno}")
        # Tentar recuperar do erro
        parser.errok()
    else:
        print("Erro de sintaxe: fim de arquivo inesperado")


# CONSTRUIR O PARSER

parser = yacc.yacc()


# FUNÇÕES AUXILIARES

def parse_file(filename):
    """Lê um arquivo Pascal e realiza a análise sintática"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = f.read()
        
        print(f"=== Analisando arquivo: {filename} ===\n")
        result = parser.parse(data, lexer=lexer)
        
        if result:
            print("✓ Análise sintática concluída com sucesso!")
            print("\n=== Árvore Sintática Abstrata (AST) ===")
            print_ast(result)
            return result
        else:
            print("✗ Falha na análise sintática")
            return None
            
    except FileNotFoundError:
        print(f"Erro: Arquivo '{filename}' não encontrado")
        return None
    except Exception as e:
        print(f"Erro ao processar arquivo: {e}")
        return None


def parse_string(code):
    """Analisa código Pascal fornecido como string"""
    result = parser.parse(code, lexer=lexer)
    return result


def print_ast(node, indent=0):
    """Imprime a AST de forma hierárquica"""
    spacing = "  " * indent
    
    if isinstance(node, tuple):
        print(f"{spacing}({node[0]}")
        for child in node[1:]:
            if child is not None:
                print_ast(child, indent + 1)
        print(f"{spacing})")
    elif isinstance(node, list):
        if node:  # Só imprime se a lista não estiver vazia
            print(f"{spacing}[")
            for item in node:
                if item is not None:
                    print_ast(item, indent + 1)
            print(f"{spacing}]")
    else:
        print(f"{spacing}{repr(node)}")


# TESTES

if __name__ == '__main__':
    # Teste 1: Hello World
    print("=" * 60)
    print("TESTE 1: Hello World")
    print("=" * 60)
    test1 = """
    program HelloWorld;
    begin
        writeln('Ola, Mundo!');
    end.
    """
    result1 = parse_string(test1)
    
    # Teste 2: Fatorial
    print("\n" + "=" * 60)
    print("TESTE 2: Fatorial")
    print("=" * 60)
    test2 = """
    program Fatorial;
    var
        n, i, fat: integer;
    begin
        writeln('Introduza um número inteiro positivo:');
        readln(n);
        fat := 1;
        for i := 1 to n do
            fat := fat * i;
        writeln('Fatorial de ', n, ': ', fat);
    end.
    """
    result2 = parse_string(test2)
    
    # Teste 3: Número Primo
    print("\n" + "=" * 60)
    print("TESTE 3: Número Primo")
    print("=" * 60)
    test3 = """
    program NumeroPrimo;
    var
        num, i: integer;
        primo: boolean;
    begin
        writeln('Introduza um número inteiro positivo:');
        readln(num);
        primo := true;
        i := 2;
        while (i <= (num div 2)) and primo do
        begin
            if (num mod i) = 0 then
                primo := false;
            i := i + 1;
        end;
        if primo then
            writeln(num, ' é um número primo')
        else
            writeln(num, ' não é um número primo')
    end.
    """
    result3 = parse_string(test3)
    
    # Teste 4: Array
    print("\n" + "=" * 60)
    print("TESTE 4: Soma de Array")
    print("=" * 60)
    test4 = """
    program SomaArray;
    var
        numeros: array[1..5] of integer;
        i, soma: integer;
    begin
        soma := 0;
        writeln('Introduza 5 números inteiros:');
        for i := 1 to 5 do
        begin
            readln(numeros[i]);
            soma := soma + numeros[i];
        end;
        writeln('A soma dos números é: ', soma);
    end.
    """
    result4 = parse_string(test4)
    
    # Teste 5: Função
    print("\n" + "=" * 60)
    print("TESTE 5: Função BinToInt")
    print("=" * 60)
    test5 = """
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
    result5 = parse_string(test5)
    
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)
    print(f"Teste 1 (Hello World): {'✓ PASSOU' if result1 else '✗ FALHOU'}")
    print(f"Teste 2 (Fatorial): {'✓ PASSOU' if result2 else '✗ FALHOU'}")
    print(f"Teste 3 (Número Primo): {'✓ PASSOU' if result3 else '✗ FALHOU'}")
    print(f"Teste 4 (Array): {'✓ PASSOU' if result4 else '✗ FALHOU'}")
    print(f"Teste 5 (Função): {'✓ PASSOU' if result5 else '✗ FALHOU'}")