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
    """program : PROGRAM ID SEMI functions decls block DOT"""
    p[0] = ('PROGRAM', p[2], p[4], p[5], p[6])

def p_functions(p):
    """functions : functions function
                 | empty"""
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = []

def p_function(p):
    """function : FUNCTION ID LPAREN args_decl RPAREN COLON type SEMI decls block SEMI"""
    # ('FUNCTION', nome, argumentos, tipo_retorno, decls_locais, corpo)
    p[0] = ('FUNCTION', p[2], p[4], p[7], p[9], p[10])

def p_args_decl(p):
    """args_decl : ids COLON type
                 | empty"""
    # Simplificação para o teste 5 (1 argumento). 
    # Para suportar vários (a; b: int) seria preciso uma lista parecida com var_list
    if len(p) == 2: p[0] = []
    else: 
        # Cria lista de argumentos: [('ARG', nome, tipo)]
        args = []
        for nome in p[1]:
             args.append(('ARG', nome, p[3]))
        p[0] = args
        
def p_args_list(p):
    """args_list : args_list COMMA expression
                 | expression"""
    if len(p) == 4:
        # Se temos: lista , expressão -> Juntar
        p[0] = p[1] + [p[3]]
    else:
        # Se temos só: expressão -> Criar lista nova
        p[0] = [p[1]]

# Declarações de Variáveis
def p_decls(p):
    """decls : VAR var_list
             | empty"""
    if len(p) == 3:
        p[0] = p[2]
    else:
        p[0] = []

def p_var_list_multi(p):
    """var_list : var_list var_item"""
    p[0] = p[1] + p[2]

def p_var_list_single(p):
    """var_list : var_item"""
    p[0] = p[1]

def p_var_item(p):
    """var_item : ids COLON type SEMI"""
    # Cria uma lista de tuplos: [('VAR', 'x', 'INTEGER'), ('VAR', 'y', 'INTEGER')]
    vars = []
    for var_name in p[1]:
        vars.append(('VAR', var_name, p[3]))
    p[0] = vars

def p_ids_multi(p):
    """ids : ids COMMA ID"""
    p[0] = p[1] + [p[3]]

def p_ids_single(p):
    """ids : ID"""
    p[0] = [p[1]]

def p_type(p):
    """type : INTEGER
            | BOOLEAN
            | STRING_TYPE
            | ARRAY PRA NUM DOTDOT NUM PRF OF type"""
    if len(p) == 2:
        p[0] = p[1].upper()
    else:
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

def p_statement_assign(p):
    """statement : ID ASSIGN expression"""
    p[0] = ('ASSIGN', p[1], p[3])

def p_statement_assign_array(p):
    """statement : ID PRA expression PRF ASSIGN expression"""
    # Cria um tuplo: ('ASSIGN_ARRAY', nome, indice, valor)
    p[0] = ('ASSIGN_ARRAY', p[1], p[3], p[6])
    
def p_statement_writeln(p):
    """statement : WRITELN LPAREN args_list RPAREN"""
    p[0] = ('WRITELN', p[3])

def p_statement_readln(p):
    """statement : READLN LPAREN ID RPAREN"""
    p[0] = ('READLN', p[3])

def p_statement_readln_array(p):
    """statement : READLN LPAREN ID PRA expression PRF RPAREN"""
    p[0] = ('READLN_ARRAY', p[3], p[5])

def p_stmt_or_block_stmt(p):
    """stmt_or_block : statement"""
    p[0] = [p[1]]

def p_stmt_or_block_block(p):
    """stmt_or_block : block"""
    p[0] = p[1]

def p_statement_if(p):
    """statement : IF expression THEN stmt_or_block ELSE stmt_or_block
                 | IF expression THEN stmt_or_block"""
    if len(p) == 7:
        p[0] = ('IF', p[2], p[4], p[6]) # Com Else
    else:
        p[0] = ('IF', p[2], p[4], None) # Sem Else

def p_statement_while(p):
    """statement : WHILE expression DO stmt_or_block"""
    p[0] = ('WHILE', p[2], p[4])

def p_statement_for(p):
    """statement : FOR ID ASSIGN expression TO expression DO stmt_or_block
                 | FOR ID ASSIGN expression DOWNTO expression DO stmt_or_block"""
    p[0] = ('FOR', p[2], p[4], p[5], p[6], p[8])
    
def p_statement_empty(p):
    """statement : empty"""
    pass

# Expressões
def p_expression_binop(p):
    """expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | expression DIV expression
                  | expression MOD expression
                  | expression EQ expression
                  | expression NEQ expression
                  | expression LT expression
                  | expression GT expression
                  | expression LE expression
                  | expression GE expression
                  | expression AND expression
                  | expression OR expression"""
    p[0] = ('BINOP', p[2], p[1], p[3])

def p_expression_string(p):
    """expression : STRING"""
    p[0] = ('STRING', p[1])
    
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

def p_expression_bool(p):
    """expression : TRUE
                  | FALSE"""
    p[0] = ('BOOL', p[1])

def p_expression_array_load(p):
    """expression : ID PRA expression PRF"""
    # Cria um tuplo: ('ARRAY_LOAD', nome, indice)
    p[0] = ('ARRAY_LOAD', p[1], p[3])

def p_expression_call(p):
    """expression : ID LPAREN args_list RPAREN"""
    p[0] = ('CALL', p[1], p[3])

def p_empty(p):
    """empty :"""
    pass

def p_error(p):
    if p:
        print(f"Erro sintático no token '{p.value}' linha {p.lineno}")
    else:
        print("Erro sintático: Fim de ficheiro inesperado")

parser = yacc.yacc()