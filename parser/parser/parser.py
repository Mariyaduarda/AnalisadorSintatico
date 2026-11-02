# ---------------------------------------------------
# Parser (Analisador Sintático) para a linguagem D
#
# Implementa análise sintática descendente recursiva
# Identifica erros sintáticos com mensagens de erro
# ---------------------------------------------------

from ttoken_d import TOKEN
from lexico_d import Lexico
import sys


class ErroSintatitico(Exception):
    """Exceção para erros sintáticos"""
    def __init__(self, mensagem, token):
        self.mensagem = mensagem
        self.token = token
        super().__init__(self.mensagem)


class Parser:
    def __init__(self, arqFonte):
        """Inicializa o parser com um arquivo fonte"""
        self.lexico = Lexico(arqFonte)
        self.tokenCorrente = None
        self.tokenAnterior = None
        self.erros = []
        self.avisos = []
        self.simbolos = {}  # tabela de símbolos simples
        self.avancar()  # lê o primeiro token

    def avancar(self):
        """Lê o próximo token"""
        self.tokenAnterior = self.tokenCorrente
        self.tokenCorrente = self.lexico.getToken()

    def verificarToken(self, tipoEsperado):
        """Verifica se o token atual é do tipo esperado"""
        if self.tokenCorrente[0] != tipoEsperado:
            return False
        return True

    def consumir(self, tipoEsperado, mensagemErro=""):
        """Consome um token esperado ou gera erro"""
        if not self.verificarToken(tipoEsperado):
            token, lexema, linha, coluna = self.tokenCorrente
            msg = f"Linha {linha}, coluna {coluna}: "
            msg += f"esperado {TOKEN.msg(tipoEsperado)}, "
            msg += f"mas encontrado {TOKEN.msg(token)} '{lexema}'"
            if mensagemErro:
                msg += f" ({mensagemErro})"
            raise ErroSintatitico(msg, self.tokenCorrente)
        
        token_lido = self.tokenCorrente
        self.avancar()
        return token_lido

    def sincronizar(self, tokens_sincronizacao=None):
        """Sincroniza o parser após um erro"""
        if tokens_sincronizacao is None:
            tokens_sincronizacao = [TOKEN.ptoVirg, TOKEN.abreChave, TOKEN.fechaChave]
        
        while self.tokenCorrente[0] != TOKEN.eof:
            if self.tokenCorrente[0] in tokens_sincronizacao:
                break
            self.avancar()

    def programa(self):
        """
        programa → funcDef*
        """
        while self.tokenCorrente[0] != TOKEN.eof:
            try:
                self.definirFuncao()
            except ErroSintatitico as e:
                self.erros.append(e)
                self.sincronizar()

        return len(self.erros) == 0

    def definirFuncao(self):
        """
        funcDef → tipo ident '(' params? ')' '{' bloco '}'
        """
        # Lê o tipo de retorno
        tipo_ret = self.lerTipo()

        # Lê o identificador da função
        ident = self.consumir(TOKEN.ident, "esperado identificador")
        nome_funcao = ident[1]

        # Verifica se já existe a função
        if nome_funcao in self.simbolos:
            self.avisos.append(f"Função '{nome_funcao}' já foi definida")
        
        self.simbolos[nome_funcao] = {'tipo': 'funcao', 'tipo_retorno': tipo_ret}

        # Parâmetros
        self.consumir(TOKEN.abrePar, "em definição de função")
        parametros = []
        
        if not self.verificarToken(TOKEN.fechaPar):
            parametros = self.lerParametros()
        
        self.consumir(TOKEN.fechaPar, "em definição de função")

        # Bloco de função
        self.consumir(TOKEN.abreChave, "esperado bloco de função")
        self.bloco(tipo_ret)
        self.consumir(TOKEN.fechaChave, "fechamento do bloco")

    def lerTipo(self):
        """
        Lê um tipo básico da linguagem D
        tipo → 'int' | 'float' | 'string' | 'void'
        """
        tiposValidos = [TOKEN.INT, TOKEN.FLOAT, TOKEN.STRING, TOKEN.VOID]
        
        if not self.verificarToken(tiposValidos[0]) and \
           not self.verificarToken(tiposValidos[1]) and \
           not self.verificarToken(tiposValidos[2]) and \
           not self.verificarToken(tiposValidos[3]):
            token = self.tokenCorrente
            raise ErroSintatitico(
                f"Linha {token[2]}, coluna {token[3]}: tipo esperado",
                token
            )
        
        tipo = self.tokenCorrente[1]
        self.avancar()
        return tipo

    def lerParametros(self):
        """
        params → param (',' param)*
        param → tipo '&'? ident ('[' ']')*
        """
        parametros = []
        
        while True:
            tipo = self.lerTipo()
            
            # Referência por endereço?
            por_referencia = False
            if self.verificarToken(TOKEN.endereco):
                por_referencia = True
                self.avancar()
            
            ident = self.consumir(TOKEN.ident, "esperado nome do parâmetro")
            
            # Array?
            eh_array = False
            if self.verificarToken(TOKEN.abreCol):
                self.avancar()
                self.consumir(TOKEN.fechaCol, "em declaração de array")
                eh_array = True
            
            parametros.append({
                'nome': ident[1],
                'tipo': tipo,
                'referencia': por_referencia,
                'array': eh_array
            })
            
            if not self.verificarToken(TOKEN.virg):
                break
            self.avancar()
        
        return parametros

    def bloco(self, tipo_funcao=None):
        """
        bloco → decl* comando*
        """
        # Processa declarações locais
        while self.ehDeclaracao():
            self.declaracao()
        
        # Processa comandos
        while not self.verificarToken(TOKEN.fechaChave) and \
              not self.verificarToken(TOKEN.eof):
            self.comando(tipo_funcao)

    def ehDeclaracao(self):
        """Verifica se é uma declaração"""
        tipos = [TOKEN.INT, TOKEN.FLOAT, TOKEN.STRING]
        for t in tipos:
            if self.verificarToken(t):
                return True
        return False

    def declaracao(self):
        """
        decl → tipo ident ('[' valorInt ']')? ';'
        """
        tipo = self.lerTipo()
        ident = self.consumir(TOKEN.ident, "esperado identificador")
        
        # É array?
        if self.verificarToken(TOKEN.abreCol):
            self.avancar()
            if not self.verificarToken(TOKEN.valorInt):
                raise ErroSintatitico(
                    f"Linha {self.tokenCorrente[2]}: tamanho de array deve ser inteiro",
                    self.tokenCorrente
                )
            self.avancar()
            self.consumir(TOKEN.fechaCol, "em declaração de array")
        
        self.consumir(TOKEN.ptoVirg, "em final de declaração")

    def comando(self, tipo_funcao=None):
        """
        comando → atribCmd | ifCmd | whileCmd | forCmd | loopCmd | 
                  readCmd | writeCmd | breakCmd | continueCmd | returnCmd |
                  blocoCmd | exprCmd
        """
        try:
            if self.verificarToken(TOKEN.IF):
                self.comandoIf(tipo_funcao)
            elif self.verificarToken(TOKEN.WHILE):
                self.comandoWhile()
            elif self.verificarToken(TOKEN.FOR):
                self.comandoFor()
            elif self.verificarToken(TOKEN.LOOP):
                self.comandoLoop()
            elif self.verificarToken(TOKEN.READ):
                self.comandoRead()
            elif self.verificarToken(TOKEN.WRITE):
                self.comandoWrite()
            elif self.verificarToken(TOKEN.BREAK):
                self.comandoBreak()
            elif self.verificarToken(TOKEN.CONTINUE):
                self.comandoContinue()
            elif self.verificarToken(TOKEN.RETURN):
                self.comandoReturn(tipo_funcao)
            elif self.verificarToken(TOKEN.abreChave):
                self.avancar()
                self.bloco(tipo_funcao)
                self.consumir(TOKEN.fechaChave, "fechamento de bloco")
            else:
                # Comando de expressão
                self.expressao()
                self.consumir(TOKEN.ptoVirg, "em final de comando")
        except ErroSintatitico as e:
            self.erros.append(e)
            self.sincronizar()

    def comandoIf(self, tipo_funcao=None):
        """
        ifCmd → 'if' '(' expr ')' '{' bloco '}' elifCmd* elseCmd?
        """
        self.consumir(TOKEN.IF, "em comando if")
        self.consumir(TOKEN.abrePar, "em comando if")
        self.expressao()
        self.consumir(TOKEN.fechaPar, "em comando if")
        
        self.consumir(TOKEN.abreChave, "em bloco if")
        self.bloco(tipo_funcao)
        self.consumir(TOKEN.fechaChave, "em bloco if")
        
        # elif?
        while self.verificarToken(TOKEN.ELIF):
            self.avancar()
            self.consumir(TOKEN.abrePar, "em comando elif")
            self.expressao()
            self.consumir(TOKEN.fechaPar, "em comando elif")
            self.consumir(TOKEN.abreChave, "em bloco elif")
            self.bloco(tipo_funcao)
            self.consumir(TOKEN.fechaChave, "em bloco elif")
        
        # else?
        if self.verificarToken(TOKEN.ELSE):
            self.avancar()
            self.consumir(TOKEN.abreChave, "em bloco else")
            self.bloco(tipo_funcao)
            self.consumir(TOKEN.fechaChave, "em bloco else")

    def comandoWhile(self):
        """
        whileCmd → 'while' '(' expr ')' '{' bloco '}'
        """
        self.consumir(TOKEN.WHILE, "em comando while")
        self.consumir(TOKEN.abrePar, "em comando while")
        self.expressao()
        self.consumir(TOKEN.fechaPar, "em comando while")
        
        self.consumir(TOKEN.abreChave, "em bloco while")
        self.bloco()
        self.consumir(TOKEN.fechaChave, "em bloco while")

    def comandoFor(self):
        """
        forCmd → 'for' ident 'in' expr '{' bloco '}'
        """
        self.consumir(TOKEN.FOR, "em comando for")
        self.consumir(TOKEN.ident, "em comando for")
        self.consumir(TOKEN.IN, "em comando for")
        self.expressao()
        
        self.consumir(TOKEN.abreChave, "em bloco for")
        self.bloco()
        self.consumir(TOKEN.fechaChave, "em bloco for")

    def comandoLoop(self):
        """
        loopCmd → 'loop' '{' bloco '}'
        """
        self.consumir(TOKEN.LOOP, "em comando loop")
        self.consumir(TOKEN.abreChave, "em bloco loop")
        self.bloco()
        self.consumir(TOKEN.fechaChave, "em bloco loop")

    def comandoRead(self):
        """
        readCmd → 'read' '(' ident (',' ident)* ')' ';'
        """
        self.consumir(TOKEN.READ, "em comando read")
        self.consumir(TOKEN.abrePar, "em comando read")
        
        self.consumir(TOKEN.ident, "em comando read")
        while self.verificarToken(TOKEN.virg):
            self.avancar()
            self.consumir(TOKEN.ident, "em comando read")
        
        self.consumir(TOKEN.fechaPar, "em comando read")
        self.consumir(TOKEN.ptoVirg, "em comando read")

    def comandoWrite(self):
        """
        writeCmd → 'write' '(' expr (',' expr)* ')' ';'
        """
        self.consumir(TOKEN.WRITE, "em comando write")
        self.consumir(TOKEN.abrePar, "em comando write")
        
        self.expressao()
        while self.verificarToken(TOKEN.virg):
            self.avancar()
            self.expressao()
        
        self.consumir(TOKEN.fechaPar, "em comando write")
        self.consumir(TOKEN.ptoVirg, "em comando write")

    def comandoBreak(self):
        """
        breakCmd → 'break' ';'
        """
        self.consumir(TOKEN.BREAK, "em comando break")
        self.consumir(TOKEN.ptoVirg, "em comando break")

    def comandoContinue(self):
        """
        continueCmd → 'continue' ';'
        """
        self.consumir(TOKEN.CONTINUE, "em comando continue")
        self.consumir(TOKEN.ptoVirg, "em comando continue")

    def comandoReturn(self, tipo_funcao=None):
        """
        returnCmd → 'return' expr? ';'
        """
        self.consumir(TOKEN.RETURN, "em comando return")
        
        if not self.verificarToken(TOKEN.ptoVirg):
            self.expressao()
        
        self.consumir(TOKEN.ptoVirg, "em comando return")

    def expressao(self):
        """
        expr → atribExpr
        """
        self.atribExpr()

    def atribExpr(self):
        """
        atribExpr → orExpr ('=' orExpr)*
        """
        self.orExpr()
        
        while self.verificarToken(TOKEN.atrib):
            self.avancar()
            self.orExpr()

    def orExpr(self):
        """
        orExpr → andExpr ('OR' andExpr)*
        """
        self.andExpr()
        
        while self.verificarToken(TOKEN.OR):
            self.avancar()
            self.andExpr()

    def andExpr(self):
        """
        andExpr → notExpr ('AND' notExpr)*
        """
        self.notExpr()
        
        while self.verificarToken(TOKEN.AND):
            self.avancar()
            self.notExpr()

    def notExpr(self):
        """
        notExpr → 'NOT' notExpr | relaExpr
        """
        if self.verificarToken(TOKEN.NOT):
            self.avancar()
            self.notExpr()
        else:
            self.relaExpr()

    def relaExpr(self):
        """
        relaExpr → aditExpr (op_relacional aditExpr)*
        """
        self.aditExpr()
        
        ops_relacionais = [TOKEN.igual, TOKEN.diferente, TOKEN.menor,
                          TOKEN.maior, TOKEN.menorIgual, TOKEN.maiorIgual]
        
        while self.tokenCorrente[0] in ops_relacionais:
            self.avancar()
            self.aditExpr()

    def aditExpr(self):
        """
        aditExpr → multExpr (('+' | '-') multExpr)*
        """
        self.multExpr()
        
        while self.verificarToken(TOKEN.mais) or self.verificarToken(TOKEN.menos):
            self.avancar()
            self.multExpr()

    def multExpr(self):
        """
        multExpr → unExpr (('*' | '/' | 'div' | 'mod') unExpr)*
        """
        self.unExpr()
        
        ops_mult = [TOKEN.multiplica, TOKEN.divide, TOKEN.DIV, TOKEN.MOD]
        
        while self.tokenCorrente[0] in ops_mult:
            self.avancar()
            self.unExpr()

    def unExpr(self):
        """
        unExpr → ('++' | '--' | '-' | '&') unExpr | posExpr
        """
        ops_unarios = [TOKEN.increm, TOKEN.decrem, TOKEN.menos, TOKEN.endereco]
        
        if self.tokenCorrente[0] in ops_unarios:
            self.avancar()
            self.unExpr()
        else:
            self.posExpr()

    def posExpr(self):
        """
        posExpr → primExpr ('++' | '--')*
        """
        self.primExpr()
        
        while self.verificarToken(TOKEN.increm) or self.verificarToken(TOKEN.decrem):
            self.avancar()

    def primExpr(self):
        """
        primExpr → ident | valorInt | valorFloat | valorString | 
                   funcPrimitiva | ident '[' expr ']' | '(' expr ')'
        """
        if self.verificarToken(TOKEN.ident):
            ident = self.tokenCorrente[1]
            self.avancar()
            
            # Array?
            if self.verificarToken(TOKEN.abreCol):
                self.avancar()
                self.expressao()
                self.consumir(TOKEN.fechaCol, "em acesso a array")
            
            # Chamada de função?
            if self.verificarToken(TOKEN.abrePar):
                self.avancar()
                if not self.verificarToken(TOKEN.fechaPar):
                    self.expressao()
                    while self.verificarToken(TOKEN.virg):
                        self.avancar()
                        self.expressao()
                self.consumir(TOKEN.fechaPar, "em chamada de função")
        
        elif self.verificarToken(TOKEN.valorInt):
            self.avancar()
        
        elif self.verificarToken(TOKEN.valorFloat):
            self.avancar()
        
        elif self.verificarToken(TOKEN.valorString):
            self.avancar()
        
        elif self.verificarToken(TOKEN.abrePar):
            self.avancar()
            self.expressao()
            self.consumir(TOKEN.fechaPar, "em expressão entre parênteses")
        
        elif self.tokenCorrente[0] in [TOKEN.STR2INT, TOKEN.STR2FLOAT,
                                       TOKEN.INT2STR, TOKEN.FLOAT2STRING]:
            self.avancar()
            self.consumir(TOKEN.abrePar, "em chamada de função primitiva")
            self.expressao()
            self.consumir(TOKEN.fechaPar, "em chamada de função primitiva")
        
        else:
            token = self.tokenCorrente
            raise ErroSintatitico(
                f"Linha {token[2]}, coluna {token[3]}: expressão esperada, "
                f"mas encontrado {TOKEN.msg(token[0])} '{token[1]}'",
                token
            )

    def analisar(self):
        """Inicia a análise sintática"""
        sucesso = self.programa()
        return sucesso, self.erros, self.avisos


def imprimeResultados(parser):
    """Imprime os resultados da análise"""
    sucesso, erros, avisos = parser.analisar()
    
    print("=" * 70)
    print("RESULTADO DA ANÁLISE SINTÁTICA")
    print("=" * 70)
    
    if erros:
        print(f"\n❌ ERROS ENCONTRADOS: {len(erros)}\n")
        for i, erro in enumerate(erros, 1):
            print(f"  {i}. {erro.mensagem}")
    else:
        print("\n✅ Nenhum erro sintático encontrado!")
    
    if avisos:
        print(f"\n⚠️  AVISOS: {len(avisos)}\n")
        for i, aviso in enumerate(avisos, 1):
            print(f"  {i}. {aviso}")
    
    print("\n" + "=" * 70)
    
    return sucesso


# ---------------------------------------------------
# Teste rápido
# ---------------------------------------------------
if __name__ == '__main__':
    import io

    # Exemplo de código válido
    codigo_valido = '''
    int fib(int n) {
        if (n <= 1) {
            return n;
        }
        return fib(n - 1) + fib(n - 2);
    }

    int main() {
        int resultado;
        resultado = fib(10);
        write("Fibonacci: ", resultado);
        return 0;
    }
    '''

    # Exemplo com erros
    codigo_com_erros = '''
    int soma(int a int b) {
        int total
        total = a + b
        return total
    }
    '''

    print("\n\n>>> TESTANDO CÓDIGO VÁLIDO:")
    try:
        parser1 = Parser(io.StringIO(codigo_valido))
        imprimeResultados(parser1)
    except Exception as e:
        print(f"Erro: {e}")

    print("\n\n>>> TESTANDO CÓDIGO COM ERROS:")
    try:
        parser2 = Parser(io.StringIO(codigo_com_erros))
        imprimeResultados(parser2)
    except Exception as e:
        print(f"Erro: {e}")