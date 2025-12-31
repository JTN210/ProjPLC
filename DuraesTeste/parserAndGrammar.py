import ply.yacc as yacc
from lexer import tokens

precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('right', 'NOT'),
    ('left', 'EQ', 'NEQ', 'LT', 'GT', 'LE', 'GE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'DIV', 'MOD'),
)

# --- Gramática ---

def p_program(p):
    """program : PROGRAM ID SEMI decls subprograms block DOT"""
    # Adicionado subprograms
    p[0] = ('PROGRAM', p[2], p[4], p[5], p[6])

# Declarações de Variáveis
def p_decls(p):
    """decls : VAR var_list
             | empty"""
    if len(p) == 3:
        p[0] = p[2]
    else:
        p[0] = []

# --- Subprogramas (Funções e Procedimentos) ---
def p_subprograms(p):
    """subprograms : subprograms subprogram
                   | empty"""
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = []

def p_subprogram(p):
    """subprogram : FUNCTION ID SEMI decls block SEMI
                  | PROCEDURE ID SEMI decls block SEMI"""
    # Simplificação: Sem argumentos por agora
    p[0] = (p[1].upper(), p[2], p[4], p[5]) # Tipo, Nome, VarsLocais, Corpo

# --- Variáveis ---
def p_var_list_multi(p):
    """var_list : var_list var_item"""
    p[0] = p[1] + p[2]

def p_var_list_single(p):
    """var_list : var_item"""
    p[0] = p[1]

def p_var_item(p):
    """var_item : ids COLON type SEMI"""
    vars = []
    # O type agora devolve um tuplo se for array, ou string se for simples
    for var_name in p[1]:
        vars.append(('VAR', var_name, p[3]))
    p[0] = vars

def p_ids_multi(p):
    """ids : ids COMMA ID"""
    p[0] = p[1] + [p[3]]

def p_ids_single(p):
    """ids : ID"""
    p[0] = [p[1]]

# Tipos (com Array)
def p_type_simple(p):
    """type : INTEGER
            | BOOLEAN"""
    p[0] = p[1].upper()

def p_type_array(p):
    """type : ARRAY LBRACKET NUM DOTDOT NUM RBRACKET OF type"""
    # Ex: ('ARRAY', 1, 5, 'INTEGER')
    p[0] = ('ARRAY', p[3], p[5], p[8]) 

# Bloco Principal
def p_block(p):
    """block : BEGIN statements END"""
    p[0] = p[2]

def p_statements_multi(p):
    """statements : statements SEMI statement"""
    p[0] = p[1] + [p[3]]

def p_statements_single(p):
    """statements : statement"""
    p[0] = [p[1]]

# --- Comandos ---

# Atribuição Simples ou Array
def p_statement_assign(p):
    """statement : ID ASSIGN expression"""
    p[0] = ('ASSIGN', p[1], p[3])

def p_statement_assign_array(p):
    """statement : ID LBRACKET expression RBRACKET ASSIGN expression"""
    p[0] = ('ASSIGN_ARRAY', p[1], p[3], p[6]) # Nome, Índice, Valor

# Writeln com Múltiplos Argumentos
def p_statement_writeln(p):
    """statement : WRITELN LPAREN expr_list RPAREN"""
    p[0] = ('WRITELN', p[3]) # p[3] é uma lista de expressões

# Readln (mantido simples)
def p_statement_readln(p):
    """statement : READLN LPAREN ID RPAREN"""
    p[0] = ('READLN', p[3])

def p_statement_readln_array(p):
    """statement : READLN LPAREN ID LBRACKET expression RBRACKET RPAREN"""
    p[0] = ('READLN_ARRAY', p[3], p[5])

# Lista de Expressões (para writeln)
def p_expr_list_multi(p):
    """expr_list : expr_list COMMA expression
                 | expr_list COMMA STRING"""
    p[0] = p[1] + [p[3]]

def p_expr_list_single(p):
    """expr_list : expression
                 | STRING"""
    p[0] = [p[1]]

def p_stmt_or_block_stmt(p):
    """stmt_or_block : statement"""
    p[0] = [p[1]]

def p_stmt_or_block_block(p):
    """stmt_or_block : block"""
    p[0] = p[1]

# Controlo de Fluxo
def p_statement_if(p):
    """statement : IF expression THEN stmt_or_block ELSE stmt_or_block
                 | IF expression THEN stmt_or_block"""
    if len(p) == 7:
        p[0] = ('IF', p[2], p[4], p[6])
    else:
        p[0] = ('IF', p[2], p[4], None)

def p_statement_while(p):
    """statement : WHILE expression DO stmt_or_block"""
    p[0] = ('WHILE', p[2], p[4])

def p_statement_for(p):
    """statement : FOR ID ASSIGN expression TO expression DO stmt_or_block"""
    p[0] = ('FOR', p[2], p[4], p[6], p[8])

# Chamada de Função/Procedimento (Sem argumentos por simplicidade)
def p_statement_call(p):
    """statement : ID""" 
    # Ambíguo com Expression ID? Em Pascal, chamada de proc pode ser só ID.
    # Vamos assumir que se aparecer sozinho como statement, é uma chamada.
    p[0] = ('CALL_PROC', p[1])

# --- Expressões ---
def p_expression_binop(p):
    """expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | expression DIV expression
                  | expression MOD expression
                  | expression EQ expression
                  | expression LT expression
                  | expression GT expression
                  | expression LE expression
                  | expression GE expression
                  | expression AND expression
                  | expression OR expression"""
    p[0] = ('BINOP', p[2], p[1], p[3])

def p_expression_not(p):
    """expression : NOT expression"""
    p[0] = ('UNOP', p[1], p[2])

def p_expression_group(p):
    """expression : LPAREN expression RPAREN"""
    p[0] = p[2]

def p_expression_num(p):
    """expression : NUM"""
    p[0] = ('NUM', p[1])

def p_expression_id(p):
    """expression : ID"""
    p[0] = ('VAR_LOAD', p[1])

# Acesso a Array em Expressão
def p_expression_array_access(p):
    """expression : ID LBRACKET expression RBRACKET"""
    p[0] = ('ARRAY_LOAD', p[1], p[3]) # Nome, Índice

# Chamada de Função em Expressão
def p_expression_func_call(p):
    """expression : ID LPAREN RPAREN""" # Simplificado: sem args
    p[0] = ('CALL_FUNC', p[1])

def p_expression_bool(p):
    """expression : TRUE
                  | FALSE"""
    p[0] = ('BOOL', p[1])

def p_empty(p):
    """empty :"""
    pass

def p_error(p):
    if p:
        print(f"Erro sintático no token '{p.value}' linha {p.lineno}")
    else:
        print("Erro sintático: Fim de ficheiro inesperado")

parser = yacc.yacc()