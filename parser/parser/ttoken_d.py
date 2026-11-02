# ---------------------------------------------------
# Tokens da linguagem D
#
# versao 1a
# ---------------------------------------------------
from enum import IntEnum


class TOKEN(IntEnum):
    erro = 1
    eof = 2

    ident = 3
    valorInt = 4
    valorFloat = 5
    valorString = 6

    abrePar = 7
    fechaPar = 8
    abreCol = 9
    fechaCol = 10
    abreChave = 11
    fechaChave = 12

    virg = 13
    ptoVirg = 14
    endereco = 15

    increm = 16
    decrem = 17

    maior = 18
    maiorIgual = 19
    menor = 20
    menorIgual = 21
    igual = 22
    diferente = 23

    mais = 24
    menos = 25
    multiplica = 26
    divide = 27
    atrib = 28

    # ---- palavras reservadas ----
    INT = 29
    FLOAT = 30
    STRING = 31
    VOID = 32
    BREAK = 33
    CONTINUE = 34
    LOOP = 35
    WHILE = 36
    FOR = 37
    IN = 38
    IF = 39
    ELIF = 40
    ELSE = 41
    READ = 42
    WRITE = 43
    OR = 44
    AND = 45
    NOT = 46
    DIV = 47
    MOD = 48
    RETURN = 49

    # ---- funcoes primitivas ----
    STR2INT = 50
    STR2FLOAT = 51
    INT2STR = 52
    FLOAT2STRING = 53

    @classmethod
    def msg(cls, token):
        nomes = {
            1: 'erro',
            2: '<eof>',
            3: 'ident',
            4: 'valorInt',
            5: 'valorFloat',
            6: 'valorString',
            7: '(',
            8: ')',
            9: '[',
            10: ']',
            11: '{',
            12: '}',
            13: ',',
            14: ';',
            15: '&',
            16: '++',
            17: '--',
            18: '>',
            19: '>=',
            20: '<',
            21: '<=',
            22: '==',
            23: '!=',
            24: '+',
            25: '-',
            26: '*',
            27: '/',
            28: '=',
            29: 'int',
            30: 'float',
            31: 'string',
            32: 'void',
            33: 'break',
            34: 'continue',
            35: 'loop',
            36: 'while',
            37: 'for',
            38: 'in',
            39: 'if',
            40: 'elif',
            41: 'else',
            42: 'read',
            43: 'write',
            44: 'OR',
            45: 'AND',
            46: 'NOT',
            47: 'div',
            48: 'mod',
            49: 'return',
            50: 'str2int',
            51: 'str2float',
            52: 'int2str',
            53: 'float2string',
        }
        return nomes[token]

    @classmethod
    def reservada(cls, lexema):
        mapa = {
            'int': TOKEN.INT,
            'float': TOKEN.FLOAT,
            'string': TOKEN.STRING,
            'void': TOKEN.VOID,
            'break': TOKEN.BREAK,
            'continue': TOKEN.CONTINUE,
            'loop': TOKEN.LOOP,
            'while': TOKEN.WHILE,
            'for': TOKEN.FOR,
            'in': TOKEN.IN,
            'if': TOKEN.IF,
            'elif': TOKEN.ELIF,
            'else': TOKEN.ELSE,
            'read': TOKEN.READ,
            'write': TOKEN.WRITE,
            'OR': TOKEN.OR,
            'AND': TOKEN.AND,
            'NOT': TOKEN.NOT,
            'div': TOKEN.DIV,
            'mod': TOKEN.MOD,
            'return': TOKEN.RETURN,
            'str2int': TOKEN.STR2INT,
            'str2float': TOKEN.STR2FLOAT,
            'int2str': TOKEN.INT2STR,
            'float2string': TOKEN.FLOAT2STRING,
        }
        return mapa.get(lexema, TOKEN.ident)
