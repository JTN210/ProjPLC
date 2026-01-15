import ply.lex as lex

# Palavras reservadas
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
    'mod': 'MOD',
    'for': 'FOR',
    'to': 'TO',
    'true': 'TRUE',
    'false': 'FALSE',
    'boolean': 'BOOLEAN',
    'and': 'AND',
    'or': 'OR',
    'not': 'NOT',
    'array': 'ARRAY',
    'of': 'OF',
    'function': 'FUNCTION',
    'procedure': 'PROCEDURE',
    'string': 'TYPE_STRING',
    'downto': 'DOWNTO'
}

tokens = [
    'ID', 'NUM', 'STRING',
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
    'LPAREN', 'RPAREN', 'SEMI', 'COLON', 'COMMA', 'DOT',
    'ASSIGN', 'EQ', 'NEQ', 'LT', 'GT', 'LE', 'GE',
    'LBRACKET', 'RBRACKET', 'DOTDOT' # [ ] ..
] + list(reserved.values())

# Regras simples
t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_DIVIDE  = r'/'
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_SEMI    = r';'
t_COLON   = r':'
t_COMMA   = r','
t_DOT     = r'\.'
t_DOTDOT  = r'\.\.'  # Atenção: .. deve vir antes de . se usasses regex genérico, aqui é literal
t_ASSIGN  = r':='
t_EQ      = r'='
t_NEQ     = r'<>'
t_LT      = r'<'
t_GT      = r'>'
t_LE      = r'<='
t_GE      = r'>='

def t_STRING(t):
    r'\'[^\']*\''
    t.value = t.value[1:-1]
    return t

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.value = t.value.lower()
    t.type = reserved.get(t.value, 'ID')
    return t

def t_NUM(t):
    r'\d+'
    t.value = int(t.value)
    return t

t_ignore = ' \t'

def t_COMMENT(t):
    r'\{[^}]*\}'
    pass

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Carácter ilegal '{t.value[0]}' na linha {t.lexer.lineno}")
    t.lexer.skip(1)

lexer = lex.lex()