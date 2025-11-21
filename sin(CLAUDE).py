import ply.yacc as yacc
from lex import tokens, lexer


# ------------- FEITO PELO CLAUDE NÃO SEI SE ESTÁ DIREITO ----------------------
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


# 1. ESTRUTURA DO PROGRAMA

def p_program(p):
    '''program : PROGRAM ID ';' declarations compound_statement '.' '''
    p[0] = ('program', p[2], p[4], p[5])


# 2. DECLARAÇÕES

def p_declarations(p):
    '''declarations : declarations variable_declaration
                    | declarations procedure_declaration
                    | declarations function_declaration
                    | empty'''
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = p[1] + [p[2]]


def p_variable_declaration(p):
    '''variable_declaration : VAR variable_decl_list'''
    p[0] = ('var_decl', p[2])


def p_variable_decl_list(p):
    '''variable_decl_list : variable_decl_list variable_decl
                          | variable_decl'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]


def p_variable_decl(p):
    '''variable_decl : id_list ':' type ';' '''
    p[0] = ('var', p[1], p[3])


def p_id_list(p):
    '''id_list : id_list ',' ID
               | ID'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]


# 3. TIPOS

def p_type(p):
    '''type : simple_type
            | array_type'''
    p[0] = p[1]


def p_simple_type(p):
    '''simple_type : INTEGER
                   | REAL
                   | BOOLEAN
                   | CHAR
                   | STRING'''
    p[0] = p[1].lower()


def p_array_type(p):
    '''array_type : ARRAY '[' NUMBER RANGE NUMBER ']' OF type'''
    p[0] = ('array', p[3], p[5], p[8])


# 4. SUBPROGRAMAS (PROCEDURES E FUNCTIONS)

def p_procedure_declaration(p):
    '''procedure_declaration : PROCEDURE ID ';' declarations compound_statement ';'
                             | PROCEDURE ID '(' parameters ')' ';' declarations compound_statement ';' '''
    if len(p) == 7:
        p[0] = ('procedure', p[2], [], p[4], p[5])
    else:
        p[0] = ('procedure', p[2], p[4], p[7], p[8])


def p_function_declaration(p):
    '''function_declaration : FUNCTION ID ':' type ';' declarations compound_statement ';'
                            | FUNCTION ID '(' parameters ')' ':' type ';' declarations compound_statement ';' '''
    if len(p) == 9:
        p[0] = ('function', p[2], [], p[4], p[6], p[7])
    else:
        p[0] = ('function', p[2], p[4], p[7], p[9], p[10])


def p_parameters(p):
    '''parameters : parameter_list'''
    p[0] = p[1]


def p_parameter_list(p):
    '''parameter_list : parameter_list ';' parameter
                      | parameter'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]


def p_parameter(p):
    '''parameter : id_list ':' type'''
    p[0] = ('param', p[1], p[3])


# 5. COMANDOS (STATEMENTS)

def p_compound_statement(p):
    '''compound_statement : BEGIN statement_list END'''
    p[0] = ('compound', p[2])


def p_statement_list(p):
    '''statement_list : statement_list ';' statement
                      | statement'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]


def p_statement(p):
    '''statement : assignment_statement
                 | procedure_call
                 | compound_statement
                 | if_statement
                 | while_statement
                 | for_statement
                 | read_statement
                 | write_statement
                 | empty'''
    p[0] = p[1]


def p_assignment_statement(p):
    '''assignment_statement : variable ASSIGN expression'''
    p[0] = ('assign', p[1], p[3])


def p_procedure_call(p):
    '''procedure_call : ID '(' expression_list ')'
                      | ID'''
    if len(p) == 2:
        p[0] = ('call', p[1], [])
    else:
        p[0] = ('call', p[1], p[3])


# 6. ESTRUTURAS DE CONTROLE

def p_if_statement(p):
    '''if_statement : IF expression THEN statement
                    | IF expression THEN statement ELSE statement'''
    if len(p) == 5:
        p[0] = ('if', p[2], p[4], None)
    else:
        p[0] = ('if', p[2], p[4], p[6])


def p_while_statement(p):
    '''while_statement : WHILE expression DO statement'''
    p[0] = ('while', p[2], p[4])


def p_for_statement(p):
    '''for_statement : FOR ID ASSIGN expression TO expression DO statement
                     | FOR ID ASSIGN expression DOWNTO expression DO statement'''
    p[0] = ('for', p[2], p[4], p[6], p[5].lower(), p[8])


# 7. COMANDOS DE I/O

def p_read_statement(p):
    '''read_statement : READ '(' variable_list ')'
                      | READLN '(' variable_list ')'
                      | READLN'''
    if len(p) == 2:
        p[0] = ('readln', [])
    elif p[1].lower() == 'read':
        p[0] = ('read', p[3])
    else:
        p[0] = ('readln', p[3])


def p_write_statement(p):
    '''write_statement : WRITE '(' expression_list ')'
                       | WRITELN '(' expression_list ')'
                       | WRITELN'''
    if len(p) == 2:
        p[0] = ('writeln', [])
    elif p[1].lower() == 'write':
        p[0] = ('write', p[3])
    else:
        p[0] = ('writeln', p[3])


def p_variable_list(p):
    '''variable_list : variable_list ',' variable
                     | variable'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]


def p_expression_list(p):
    '''expression_list : expression_list ',' expression
                       | expression'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]


# 8. EXPRESSÕES

def p_expression(p):
    '''expression : simple_expression relational_op simple_expression
                  | simple_expression'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ('binop', p[2], p[1], p[3])


def p_relational_op(p):
    '''relational_op : EQUALS
                     | NOT_EQUALS
                     | LESS_THAN
                     | LESS_THAN_OR_EQUAL_TO
                     | GREATER_THAN
                     | GREATER_THAN_OR_EQUAL_TO'''
    p[0] = p[1]


def p_simple_expression(p):
    '''simple_expression : simple_expression '+' term
                         | simple_expression '-' term
                         | simple_expression OR term
                         | term'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ('binop', p[2], p[1], p[3])


def p_simple_expression_unary(p):
    '''simple_expression : '+' term %prec UMINUS
                         | '-' term %prec UMINUS'''
    p[0] = ('unop', p[1], p[2])


def p_term(p):
    '''term : term '*' factor
            | term '/' factor
            | term DIV factor
            | term MOD factor
            | term AND factor
            | factor'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ('binop', p[2], p[1], p[3])


def p_factor(p):
    '''factor : NUMBER
              | REAL_NUMBER
              | STRING_LITERAL
              | TRUE
              | FALSE
              | variable
              | function_call
              | '(' expression ')' '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[2]


def p_factor_not(p):
    '''factor : NOT factor'''
    p[0] = ('unop', 'not', p[2])


def p_variable(p):
    '''variable : ID
                | ID '[' expression ']' '''
    if len(p) == 2:
        p[0] = ('var', p[1])
    else:
        p[0] = ('array_access', p[1], p[3])


def p_function_call(p):
    '''function_call : ID '(' expression_list ')'
                     | LENGTH '(' expression ')' '''
    if p[1].lower() == 'length':
        p[0] = ('call', 'length', [p[3]])
    else:
        p[0] = ('call', p[1], p[3])


# 9. REGRA VAZIA

def p_empty(p):
    '''empty :'''
    pass


# 10. TRATAMENTO DE ERROS

def p_error(p):
    if p:
        print(f"Erro de sintaxe no token '{p.value}' (tipo: {p.type}) na linha {p.lineno}")
    else:
        print("Erro de sintaxe: fim de arquivo inesperado")



parser = yacc.yacc()

# FUNÇÃO PARA TESTAR O PARSER

def parse_file(filename):
    """Lê um arquivo Pascal e realiza a análise sintática"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = f.read()
        
        result = parser.parse(data, lexer=lexer)
        
        if result:
            print("✓ Análise sintática concluída com sucesso!")
            print("\nÁrvore Sintática Abstrata (AST):")
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


def print_ast(node, indent=0):
    """Imprime a AST de forma hierárquica"""
    spacing = "  " * indent
    
    if isinstance(node, tuple):
        print(f"{spacing}{node[0]}")
        for child in node[1:]:
            print_ast(child, indent + 1)
    elif isinstance(node, list):
        for item in node:
            print_ast(item, indent)
    else:
        print(f"{spacing}{node}")


# TESTE

if __name__ == '__main__':
    # Teste simples
    test_code = """
    program HelloWorld;
    begin
        writeln('Ola, Mundo!');
    end.
    """
    
    print("=== Testando Parser ===\n")
    result = parser.parse(test_code, lexer=lexer)
    
    if result:
        print("\n✓ Teste básico passou!")
        print("\nAST:")
        print_ast(result)