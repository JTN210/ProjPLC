import ply.lex as lex

# Palavras reservadas (Pascal é case-insensitive, tratamos tudo como lower)
reserved = {
    'program': 'PROGRAM',
    'var': 'VAR',
    'integer': 'INTEGER',
    'begin': 'BEGIN',
    'end': 'END',
    'if': 'IF',
    'then': 'THEN',
    'else': 'ELSE',
    'while': 'WHILE',
    'do': 'DO',
    'readln': 'READLN',
    'writeln': 'WRITELN',
    'div': 'DIV',
    'mod': 'MOD'
}

tokens = [
    'ID', 'NUM', 'STRING',
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
    'LPAREN', 'RPAREN', 'SEMI', 'COLON', 'COMMA', 'DOT',
    'ASSIGN', 'EQ', 'NEQ', 'LT', 'GT', 'LE', 'GE'
] + list(reserved.values())

# Regras simples
t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_DIVIDE  = r'/'
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_SEMI    = r';'
t_COLON   = r':'
t_COMMA   = r','
t_DOT     = r'\.'
t_ASSIGN  = r':='
t_EQ      = r'='
t_NEQ     = r'<>'
t_LT      = r'<'
t_GT      = r'>'
t_LE      = r'<='
t_GE      = r'>='

# Strings (Pascal usa 'aspas simples')
def t_STRING(t):
    r'\'[^\']*\''
    t.value = t.value[1:-1] # Remove as aspas
    return t

# Identificadores e Palavras Reservadas
def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.value = t.value.lower() # Pascal é case-insensitive
    t.type = reserved.get(t.value, 'ID')
    return t

# Números
def t_NUM(t):
    r'\d+'
    t.value = int(t.value)
    return t

# Ignorar espaços e comentários
t_ignore = ' \t'

def t_COMMENT(t):
    r'\{[^}]*\}'
    pass

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Illegal character '{t.value[0]}' at line {t.lexer.lineno}")
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()