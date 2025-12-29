import ply.yacc as yacc
from lexer import tokens

# Precedência de operadores
precedence = (
    ('left', 'EQ', 'NEQ', 'LT', 'GT', 'LE', 'GE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'DIV', 'MOD'),
)

# --- Gramática ---

def p_program(p):
    """program : PROGRAM ID SEMI decls block DOT"""
    p[0] = ('PROGRAM', p[2], p[4], p[5])

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
    """type : INTEGER"""
    p[0] = 'INTEGER' # Simplificado para este exemplo

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

# Comandos
def p_statement_assign(p):
    """statement : ID ASSIGN expression"""
    p[0] = ('ASSIGN', p[1], p[3])

def p_statement_writeln(p):
    """statement : WRITELN LPAREN expression RPAREN
                 | WRITELN LPAREN STRING RPAREN"""
    p[0] = ('WRITELN', p[3])

def p_statement_readln(p):
    """statement : READLN LPAREN ID RPAREN"""
    p[0] = ('READLN', p[3])

def p_statement_if(p):
    """statement : IF expression THEN block ELSE block
                 | IF expression THEN block"""
    if len(p) == 7:
        p[0] = ('IF', p[2], p[4], p[6]) # Com Else
    else:
        p[0] = ('IF', p[2], p[4], None) # Sem Else

def p_statement_while(p):
    """statement : WHILE expression DO block"""
    p[0] = ('WHILE', p[2], p[4])

def p_statement_for(p):
    """statement : FOR ID ASSIGN expression TO expression DO block"""
    p[0] = ('FOR', p[2], p[4], p[6], p[8])

# Expressões
def p_expression_binop(p):
    """expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | expression EQ expression
                  | expression LT expression
                  | expression GT expression
                  | expression LE expression
                  | expression GE expression"""
    p[0] = ('BINOP', p[2], p[1], p[3])

def p_expression_group(p):
    """expression : LPAREN expression RPAREN"""
    p[0] = p[2]

def p_expression_num(p):
    """expression : NUM"""
    p[0] = ('NUM', p[1])

def p_expression_id(p):
    """expression : ID"""
    p[0] = ('VAR_LOAD', p[1])

def p_empty(p):
    """empty :"""
    pass

def p_error(p):
    if p:
        print(f"Erro sintático no token '{p.value}' linha {p.lineno}")
    else:
        print("Erro sintático: Fim de ficheiro inesperado")

parser = yacc.yacc()