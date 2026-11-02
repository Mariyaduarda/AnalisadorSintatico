# ---------------------------------------------------
# Analisador lexico para a linguagem D
#
# versao 1a
# ---------------------------------------------------
from ttoken_d import TOKEN


class Lexico:

    def __init__(self, arqFonte):
        self.arqFonte = arqFonte           # objeto file (ou StringIO)
        self.fonte = self.arqFonte.read()  # string contendo o fonte
        self.tamFonte = len(self.fonte)
        self.indiceFonte = 0
        self.tokenLido = None              # (token, lexema, linha, coluna)
        self.linha = 1                     # linha atual no fonte
        self.coluna = 0                    # coluna atual no fonte

    def fimDoArquivo(self):
        return self.indiceFonte >= self.tamFonte

    def getchar(self):
        if self.fimDoArquivo():
            return '\0'
        car = self.fonte[self.indiceFonte]
        self.indiceFonte += 1
        if car == '\n':
            self.linha += 1
            self.coluna = 0
        else:
            self.coluna += 1
        return car

    def ungetchar(self, simbolo):
        if simbolo == '\n':
            self.linha -= 1
        if self.indiceFonte > 0:
            self.indiceFonte -= 1
        self.coluna -= 1

    def imprimeToken(self, tokenCorrente):
        (token, lexema, linha, coluna) = tokenCorrente
        msg = TOKEN.msg(token)
        print(f'(tk={msg} lex="{lexema}" lin={linha} col={coluna})')

    def ignorarEspacosComentarios(self):
        # devolve o primeiro simbolo que NAO faz parte de espaco em
        # branco ou comentario (comentarios iniciam com // ate o fim
        # da linha, conforme a especificacao da linguagem D)
        simbolo = self.getchar()
        while True:
            if simbolo in [' ', '\t', '\n']:
                simbolo = self.getchar()
                continue

            if simbolo == '/':
                proximo = self.getchar()
                if proximo == '/':
                    # comentario: descarta ate o fim da linha
                    c = self.getchar()
                    while c not in ['\n', '\0']:
                        c = self.getchar()
                    simbolo = self.getchar()
                    continue
                else:
                    # nao era comentario, so uma '/' (divide) mesmo:
                    # devolve o caractere lido a mais e encerra
                    self.ungetchar(proximo)
                    return simbolo

            return simbolo

    def getToken(self):
        estado = 1
        simbolo = self.ignorarEspacosComentarios()
        lexema = ''
        # aqui comeca de fato um token
        lin = self.linha  # onde inicia o token, para msgs
        col = self.coluna  # onde inicia o token, para msgs
        while True:
            if estado == 1:
                # inicio do automato
                if simbolo.isalpha():
                    estado = 2  # idents, pal.reservadas, funcoes primitivas
                elif simbolo.isdigit():
                    estado = 3  # numeros (valorInt / valorFloat)
                elif simbolo == '"':
                    estado = 4  # strings
                elif simbolo == "(":
                    return (TOKEN.abrePar, "(", lin, col)
                elif simbolo == ")":
                    return (TOKEN.fechaPar, ")", lin, col)
                elif simbolo == "[":
                    return (TOKEN.abreCol, "[", lin, col)
                elif simbolo == "]":
                    return (TOKEN.fechaCol, "]", lin, col)
                elif simbolo == "{":
                    return (TOKEN.abreChave, "{", lin, col)
                elif simbolo == "}":
                    return (TOKEN.fechaChave, "}", lin, col)
                elif simbolo == ",":
                    return (TOKEN.virg, ",", lin, col)
                elif simbolo == ";":
                    return (TOKEN.ptoVirg, ";", lin, col)
                elif simbolo == "&":
                    return (TOKEN.endereco, "&", lin, col)
                elif simbolo == "+":
                    estado = 9   # + ou ++
                elif simbolo == "-":
                    estado = 10  # - ou --
                elif simbolo == "*":
                    return (TOKEN.multiplica, "*", lin, col)
                elif simbolo == "/":
                    # comentarios ja foram descartados antes de chegar aqui
                    return (TOKEN.divide, "/", lin, col)
                elif simbolo == "<":
                    estado = 5  # < ou <=
                elif simbolo == ">":
                    estado = 6  # > ou >=
                elif simbolo == "=":
                    estado = 7  # = ou ==
                elif simbolo == "!":
                    estado = 8  # != (! sozinho eh erro)
                elif simbolo == '\0':
                    return (TOKEN.eof, '<eof>', lin, col)
                else:
                    lexema += simbolo
                    return (TOKEN.erro, lexema, lin, col)

            elif estado == 2:
                # identificadores, palavras reservadas e funcoes primitivas
                if simbolo.isalnum() or simbolo == '_':
                    estado = 2
                else:
                    self.ungetchar(simbolo)
                    token = TOKEN.reservada(lexema)
                    return (token, lexema, lin, col)

            elif estado == 3:
                # parte inteira do numero
                if simbolo.isdigit():
                    estado = 3
                elif simbolo == '.':
                    estado = 31
                elif simbolo.isalpha():
                    lexema += simbolo
                    return (TOKEN.erro, lexema, lin, col)
                else:
                    self.ungetchar(simbolo)
                    return (TOKEN.valorInt, lexema, lin, col)

            elif estado == 31:
                # precisa de ao menos um digito depois do ponto
                if simbolo.isdigit():
                    estado = 32
                else:
                    self.ungetchar(simbolo)
                    return (TOKEN.erro, lexema, lin, col)

            elif estado == 32:
                # parte fracionaria do numero
                if simbolo.isdigit():
                    estado = 32
                elif simbolo.isalpha():
                    lexema += simbolo
                    return (TOKEN.erro, lexema, lin, col)
                else:
                    self.ungetchar(simbolo)
                    return (TOKEN.valorFloat, lexema, lin, col)

            elif estado == 4:
                # strings: ["]([^"\\]*|\\.)*["]
                while True:
                    if simbolo == '"':
                        lexema += simbolo
                        return (TOKEN.valorString, lexema, lin, col)
                    if simbolo in ['\n', '\0']:
                        return (TOKEN.erro, lexema, lin, col)
                    if simbolo == '\\':
                        lexema += simbolo
                        simbolo = self.getchar()
                        if simbolo in ['\n', '\0']:
                            return (TOKEN.erro, lexema, lin, col)

                    lexema = lexema + simbolo
                    simbolo = self.getchar()

            elif estado == 5:
                if simbolo == '=':
                    lexema = lexema + simbolo
                    return (TOKEN.menorIgual, lexema, lin, col)
                else:
                    self.ungetchar(simbolo)
                    return (TOKEN.menor, lexema, lin, col)

            elif estado == 6:
                if simbolo == '=':
                    lexema = lexema + simbolo
                    return (TOKEN.maiorIgual, lexema, lin, col)
                else:
                    self.ungetchar(simbolo)
                    return (TOKEN.maior, lexema, lin, col)

            elif estado == 7:
                if simbolo == '=':
                    lexema += simbolo
                    return (TOKEN.igual, lexema, lin, col)
                else:
                    self.ungetchar(simbolo)
                    return (TOKEN.atrib, lexema, lin, col)

            elif estado == 8:
                if simbolo == '=':
                    lexema += simbolo
                    return (TOKEN.diferente, lexema, lin, col)
                else:
                    # '!' sozinho nao existe na linguagem D
                    self.ungetchar(simbolo)
                    return (TOKEN.erro, lexema, lin, col)

            elif estado == 9:
                if simbolo == '+':
                    lexema += simbolo
                    return (TOKEN.increm, lexema, lin, col)
                else:
                    self.ungetchar(simbolo)
                    return (TOKEN.mais, lexema, lin, col)

            elif estado == 10:
                if simbolo == '-':
                    lexema += simbolo
                    return (TOKEN.decrem, lexema, lin, col)
                else:
                    self.ungetchar(simbolo)
                    return (TOKEN.menos, lexema, lin, col)

            else:
                print('BUG!!!')

            lexema = lexema + simbolo
            simbolo = self.getchar()


# ---------------------------------------------------
# teste rapido
# ---------------------------------------------------
if __name__ == '__main__':
    import io

    exemplo = '''
    // programa de exemplo na linguagem D
    int soma(int &a, int b) {
        int total;
        total = a + b++;
        if (total >= 10.5) {
            write("resultado: ", total);
        } elif (total < 0) {
            total = str2int("0");
        } else {
            total = NOT total;
        }
        return total;
    }
    '''

    lex = Lexico(io.StringIO(exemplo))
    while True:
        tk = lex.getToken()
        lex.imprimeToken(tk)
        if tk[0] == TOKEN.eof:
            break
