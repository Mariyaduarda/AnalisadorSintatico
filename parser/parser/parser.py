# ---------------------------------------------------
# Analisador Sintático para a linguagem D
# (no formato do esqueleto: um método por regra da gramática BETA)
#
# Para a análise no primeiro erro (como o esqueleto CALC).
# ---------------------------------------------------
import io
import sys
from ttoken_d import TOKEN
from lexico_d import Lexico


class Sintatico:
    TIPOS_PRIM = [TOKEN.INT, TOKEN.FLOAT, TOKEN.STRING]
    TIPOS_FUNC = [TOKEN.VOID, TOKEN.INT, TOKEN.FLOAT, TOKEN.STRING]
    OPS_REL = [TOKEN.maior, TOKEN.maiorIgual, TOKEN.menor,
               TOKEN.menorIgual, TOKEN.igual, TOKEN.diferente]
    INICIO_EXP = [TOKEN.increm, TOKEN.decrem, TOKEN.NOT, TOKEN.mais, TOKEN.menos,
                  TOKEN.ident, TOKEN.valorInt, TOKEN.valorFloat, TOKEN.valorString,
                  TOKEN.abreCol, TOKEN.abrePar]
    INICIO_COM = [TOKEN.LOOP, TOKEN.WHILE, TOKEN.FOR, TOKEN.IF, TOKEN.READ,
                  TOKEN.WRITE, TOKEN.BREAK, TOKEN.CONTINUE, TOKEN.RETURN,
                  TOKEN.abreChave] + INICIO_EXP

    def __init__(self, lexico):
        """
        O QUE É: Construtor da classe Sintatico.
        PARA QUE SERVE: Inicializa os atributos essenciais para o funcionamento do parser.
        COMO FUNCIONA: Recebe a instância do analisador léxico, inicializa uma fila para 
        lookahead extra (usada em instruções como o 'for'), define o token lido como None 
        e marca o sucesso da análise como True inicialmente.
        """
        self.lexico = lexico
        self.fila = []           # lookahead extra (usado no 'for')
        self.tokenLido = None
        self.sucesso = True

    # ------------------------------------------------------------
    # Infraestrutura
    # ------------------------------------------------------------
    def traduz(self):
        """
        O QUE É: Método principal que inicia o processo de compilação/análise sintática.
        PARA QUE SERVE: Dispara a regra inicial da gramática e valida se o arquivo terminou corretamente.
        COMO FUNCIONA: Pede o primeiro token, tenta chamar a regra raiz 'prog()', verifica 
        se todo o código foi consumido (esperando EOF) e trata exceções caso ocorra erro sintático.
        """
        self.proximo()
        try:
            self.prog()
            if self.lido() != TOKEN.eof:
                self.erro("esperado fim do arquivo, "
                          f"mas veio {self.descreve()}")
            print("Programa sintaticamente correto.")
        except Exception:
            self.sucesso = False
        return self.sucesso

    def proximo(self):
        """
        O QUE É: Avança para o próximo token da fita de entrada.
        PARA QUE SERVE: Alimenta o parser com novos tokens à medida que a análise avança.
        COMO FUNCIONA: Se houver tokens guardados na fila de lookahead extra, retira o primeiro; 
        caso contrário, solicita um novo token diretamente ao analisador léxico.
        """
        if self.fila:
            self.tokenLido = self.fila.pop(0)
        else:
            self.tokenLido = self.lexico.getToken()

    def espia(self, n=1):
        """
        O QUE É: Mecanismo de Lookahead (olhar adiante).
        PARA QUE SERVE: Permite inspecionar tokens futuros sem consumi-los (remover da fita).
        COMO FUNCIONA: Preenche a fila de lookahead com tokens do léxico até atingir a posição 'n' 
        desejada e retorna o tipo do token correspondente a n posições à frente.
        """
        while len(self.fila) < n:
            if self.fila and self.fila[-1][0] == TOKEN.eof:
                self.fila.append(self.fila[-1])
            else:
                self.fila.append(self.lexico.getToken())
        return self.fila[n - 1][0]

    def lido(self):
        """
        O QUE É: Inspetor do token atual.
        PARA QUE SERVE: Retorna apenas o tipo (enum) do token que está sendo analisado no momento.
        COMO FUNCIONA: Acede à tupla guardada em 'self.tokenLido' e retorna o primeiro elemento ([0]).
        """
        return self.tokenLido[0]

    def descreve(self):
        """
        O QUE É: Formatador de descrição de token.
        PARA QUE SERVE: Gera uma mensagem legível para humanos sobre o token atual (útil para mensagens de erro).
        COMO FUNCIONA: Desempacota o token lido e retorna uma string descritiva com o nome do token e seu lexema.
        """
        token, lexema, _, _ = self.tokenLido
        if token == TOKEN.eof:
            return "fim do arquivo"
        return f"{TOKEN.msg(token)} '{lexema}'"

    def erro(self, msg):
        """
        O QUE É: Gerador de exceções de erro sintático.
        PARA QUE SERVE: Interrompe a compilação informando a linha, coluna e a causa do erro.
        COMO FUNCIONA: Extrai a linha e coluna do token atual, imprime a mensagem detalhada 
        no console e dispara uma exceção para cancelar a execução.
        """
        _, _, linha, coluna = self.tokenLido
        print(f"Erro na linha {linha}, coluna {coluna}")
        print(msg)
        raise Exception(msg)

    def consome(self, tokenEsperado):
        """
        O QUE É: Validador e consumidor obrigatório de tokens.
        PARA QUE SERVE: Garante que o código fonte obedece estritamente à ordem esperada pela gramática.
        COMO FUNCIONA: Compara o tipo do token atual com o 'tokenEsperado'. Se coincidirem, 
        avança para o próximo token; caso contrário, chama o método de erro.
        """
        (token, lexema, linha, coluna) = self.tokenLido
        if tokenEsperado == token:
            self.proximo()
        else:
            self.erro(f"Era esperado {TOKEN.msg(tokenEsperado)} "
                      f"mas veio {self.descreve()}")

    def consomeVariavel(self):
        """
        O QUE É: Validador específico para identificadores de variáveis.
        PARA QUE SERVE: Garante que o identificador siga a convenção de nomenclatura (ex: iniciar com maiúscula).
        COMO FUNCIONA: Consome o token de identificador genérico e valida se a regra de letra maiúscula foi cumprida.
        """
        (token, lexema, linha, coluna) = self.tokenLido
        self.consome(TOKEN.ident)
        self.checaMaiuscula(lexema, linha, coluna)

    def checaMaiuscula(self, lexema, linha, coluna):
        """
        O QUE É: Verificador semântico/sintático de convenção de nomes.
        PARA QUE SERVE: Assegura que nomes de variáveis comecem obrigatoriamente com letra maiúscula na linguagem D.
        COMO FUNCIONA: Checa o primeiro caractere do lexema da variável usando '.isupper()'. 
        Se não for maiúsculo, exibe erro e interrompe.
        """
        if not lexema or not lexema[0].isupper():
            print(f"Erro na linha {linha}, coluna {coluna}")
            print(f"Variável '{lexema}' deve começar com letra maiúscula")
            raise Exception("variável minúscula")

    def testaLexico(self):
        """
        O QUE É: Função utilitária de depuração (debug).
        PARA QUE SERVE: Permite testar apenas o analisador léxico imprimindo todos os tokens da entrada.
        COMO FUNCIONA: Percorre todos os tokens do arquivo até encontrar o EOF, imprimindo cada um.
        """
        self.proximo()
        while self.lido() != TOKEN.eof:
            self.lexico.imprimeToken(self.tokenLido)
            self.proximo()

    # ------------------------------------------------------------
    # Programa e funções
    # ------------------------------------------------------------
    def prog(self):
        """
        O QUE É: Regra gramatical raiz (Prog -> Func RestoProg).
        PARA QUE SERVE: Analisa a estrutura global do programa, que consiste em uma ou mais funções.
        COMO FUNCIONA: Chama a regra de função e em seguida o restante do programa.
        """
        self.func()
        self.restoProg()

    def restoProg(self):
        """
        O QUE É: Regra gramatical para recursão de funções (RestoProg -> LAMBDA | Func RestoProg).
        PARA QUE SERVE: Permite que o programa tenha múltiplas funções declaradas em sequência.
        COMO FUNCIONA: Verifica se o token atual pertence aos tipos de função válidos; se sim, processa outra função recursivamente.
        """
        if self.lido() in self.TIPOS_FUNC:
            self.func()
            self.restoProg()

    def func(self):
        """
        O QUE É: Regra gramatical de declaração de função (Func -> TipoFunc ident ( ListaArgs ) Corpo).
        PARA QUE SERVE: Analisa a estrutura completa de uma função (retorno, nome, parâmetros e bloco de código).
        COMO FUNCIONA: Consome o tipo de retorno, o identificador do nome, abre parênteses, 
        analisa a lista de argumentos, fecha parênteses e valida o corpo da função.
        """
        self.tipoFunc()
        self.consome(TOKEN.ident)
        self.consome(TOKEN.abrePar)
        self.listaArgs()
        self.consome(TOKEN.fechaPar)
        self.corpo()

    def tipoPrim(self):
        """
        O QUE É: Regra gramatical de tipos primitivos (TipoPrim -> int | float | string).
        PARA QUE SERVE: Valida se o tipo informado é um dos tipos de dados básicos suportados.
        COMO FUNCIONA: Verifica se o token atual está na lista de tipos primitivos permitidos e o consome; senão, dispara erro.
        """
        if self.lido() in self.TIPOS_PRIM:
            self.consome(self.lido())
        else:
            self.erro("Era esperado tipo (int, float ou string) "
                      f"mas veio {self.descreve()}")

    def tipoFunc(self):
        """
        O QUE É: Regra gramatical de tipo de retorno de função (TipoFunc -> void | TipoPrim).
        PARA QUE SERVE: Valida se a função retorna um tipo primitivo ou se é 'void' (sem retorno).
        COMO FUNCIONA: Testa se é 'void' ou um tipo primitivo válido e consome adequadamente.
        """
        if self.lido() == TOKEN.VOID:
            self.consome(TOKEN.VOID)
        elif self.lido() in self.TIPOS_PRIM:
            self.tipoPrim()
        else:
            self.erro("Era esperado tipo de retorno (void, int, float ou string) "
                      f"mas veio {self.descreve()}")

    def listaArgs(self):
        """
        O QUE É: Regra gramatical de lista de argumentos (ListaArgs -> LAMBDA | Arg RestoListaArgs).
        PARA QUE SERVE: Gerencia os parâmetros passados na assinatura de uma função.
        COMO FUNCIONA: Se houver argumentos (não encontrar o fecha-parênteses direto), analisa um argumento e o restante da lista.
        """
        if self.lido() != TOKEN.fechaPar:
            self.arg()
            self.restoListaArgs()

    def restoListaArgs(self):
        """
        O QUE É: Regra gramatical para múltiplos argumentos separados por vírgula.
        PARA QUE SERVE: Processa argumentos adicionais após o primeiro em uma função.
        COMO FUNCIONA: Se encontrar uma vírgula, consome-a, processa o próximo argumento e chama recursivamente.
        """
        if self.lido() == TOKEN.virg:
            self.consome(TOKEN.virg)
            self.arg()
            self.restoListaArgs()

    def arg(self):
        """
        O QUE É: Regra gramatical de um argumento individual (Arg -> TipoPrim OpcRef ident OpcColchete).
        PARA QUE SERVE: Analisa a tipagem, passagem por referência opcional, nome e se é vetor de um parâmetro.
        COMO FUNCIONA: Chama sequencialmente as regras de tipo primitivo, referência (&), nome da variável e colchetes.
        """
        self.tipoPrim()
        self.opcRef()
        self.consomeVariavel()
        self.opcColchete()

    def opcRef(self):
        """
        O QUE É: Regra gramatical opcional de referência (OpcRef -> LAMBDA | &).
        PARA QUE SERVE: Permite identificar se o argumento é passado por referência usando o operador '&'.
        COMO FUNCIONA: Verifica se o token atual é o operador de endereço; se for, consome-o.
        """
        if self.lido() == TOKEN.endereco:
            self.consome(TOKEN.endereco)

    def opcColchete(self):
        """
        O QUE É: Regra gramatical opcional de colchetes vazios (OpcColchete -> LAMBDA | [ ]).
        PARA QUE SERVE: Indica se uma variável ou argumento é declarada como um arranjo/vetor de tamanho dinâmico.
        COMO FUNCIONA: Se encontrar um colchete aberto, consome-o junto com o colchete fechado correspondente.
        """
        if self.lido() == TOKEN.abreCol:
            self.consome(TOKEN.abreCol)
            self.consome(TOKEN.fechaCol)

    def corpo(self):
        """
        O QUE É: Regra gramatical de corpo de função/bloco (Corpo -> { ListaDeclar ListaCom }).
        PARA QUE SERVE: Delimita o escopo de código contendo declarações de variáveis seguidas de comandos.
        COMO FUNCIONA: Consome a chave de abertura, processa as declarações locais, os comandos e consome a chave de fechamento.
        """
        self.consome(TOKEN.abreChave)
        self.listaDeclar()
        self.listaCom()
        self.consome(TOKEN.fechaChave)

    def bloco(self):
        """
        O QUE É: Regra gramatical de bloco aninhado (Bloco -> Corpo).
        PARA QUE SERVE: Funciona como um alias para o corpo, usado dentro de estruturas de controle (if, while, etc.).
        COMO FUNCIONA: Delega diretamente para o método 'corpo()'.
        """
        self.corpo()

    # ------------------------------------------------------------
    # Declarações
    # ------------------------------------------------------------
    def listaDeclar(self):
        """
        O QUE É: Regra gramatical para lista de declarações de variáveis no início de blocos.
        PARA QUE SERVE: Permite declarar múltiplas variáveis locais sequencialmente.
        COMO FUNCIONA: Se o token atual for um tipo primitivo, processa uma declaração e repete recursivamente.
        """
        if self.lido() in self.TIPOS_PRIM:
            self.declar()
            self.listaDeclar()

    def declar(self):
        """
        O QUE É: Regra gramatical de declaração de variável individual.
        PARA QUE SERVE: Processa a declaração de uma ou mais variáveis do mesmo tipo, com atribuição opcional.
        COMO FUNCIONA: Consome o tipo, o identificador da variável, colchetes opcionais, 
        inicialização opcional, lista de identificadores adicionais e ponto e vírgula final.
        """
        self.tipoPrim()
        self.consomeVariavel()
        self.opcColchete()
        self.opcInicializa()
        self.listaIdent()
        self.consome(TOKEN.ptoVirg)

    def opcInicializa(self):
        """
        O QUE É: Regra gramatical opcional de atribuição inicial (OpcInicializa -> LAMBDA | = Exp).
        PARA QUE SERVE: Permite atribuir um valor inicial a uma variável no momento de sua declaração.
        COMO FUNCIONA: Se encontrar o operador de atribuição ('='), consome-o e avalia a expressão correspondente.
        """
        if self.lido() == TOKEN.atrib:
            self.consome(TOKEN.atrib)
            self.exp()

    def listaIdent(self):
        """
        O QUE É: Regra gramatical para múltiplas variáveis declaradas na mesma linha (ex: `int A, B, C;`).
        PARA QUE SERVE: Permite declarar várias variáveis do mesmo tipo agrupadas por vírgulas.
        COMO FUNCIONA: Se encontrar uma vírgula, consome-a, pega o identificador, colchete opcional e repete.
        """
        if self.lido() == TOKEN.virg:
            self.consome(TOKEN.virg)
            self.consomeVariavel()
            self.opcColchete()
            self.listaIdent()

    # ------------------------------------------------------------
    # Comandos
    # ------------------------------------------------------------
    def listaCom(self):
        """
        O QUE É: Regra gramatical para uma sequência de comandos executáveis.
        PARA QUE SERVE: Analisa todos os comandos presentes em um bloco de código.
        COMO FUNCIONA: Enquanto o token corresponder ao início de um comando válido, processa o comando e continua a lista.
        """
        if self.lido() in self.INICIO_COM:
            self.com()
            self.listaCom()

    def com(self):
        """
        O QUE É: Centralizador de comandos da linguagem (atribuições, estruturas de controle, I/O, etc.).
        PARA QUE SERVE: Direciona a análise sintática para o método específico do comando encontrado.
        COMO FUNCIONA: Identifica o tipo do token atual e despacha para a função correspondente 
        (repetição, decisão, E/S, break, continue, return, bloco ou expressão genérica).
        """
        t = self.lido()
        if t in [TOKEN.LOOP, TOKEN.WHILE, TOKEN.FOR]:
            self.comRepete()
        elif t == TOKEN.IF:
            self.comDecisao()
        elif t in [TOKEN.READ, TOKEN.WRITE]:
            self.comIO()
        elif t == TOKEN.BREAK:
            self.consome(TOKEN.BREAK)
            self.consome(TOKEN.ptoVirg)
        elif t == TOKEN.CONTINUE:
            self.consome(TOKEN.CONTINUE)
            self.consome(TOKEN.ptoVirg)
        elif t == TOKEN.RETURN:
            self.consome(TOKEN.RETURN)
            self.opcExp()
            self.consome(TOKEN.ptoVirg)
        elif t == TOKEN.abreChave:
            self.bloco()
        elif t in self.TIPOS_PRIM:
            self.erro("Declarações só são permitidas no início do bloco, "
                      "antes dos comandos")
        else:
            self.exp()
            self.consome(TOKEN.ptoVirg)

    def comRepete(self):
        """
        O QUE É: Regra gramatical para comandos de laço de repetição (`loop`, `while`, `for`).
        PARA QUE SERVE: Analisa construções de loops na linguagem D.
        COMO FUNCIONA: Verifica se é `loop`, `while` ou `for` e faz o parse da sintaxe específica de cada um.
        """
        if self.lido() == TOKEN.LOOP:
            self.consome(TOKEN.LOOP)
            self.bloco()
        elif self.lido() == TOKEN.WHILE:
            self.consome(TOKEN.WHILE)
            self.consome(TOKEN.abrePar)
            self.exp()
            self.consome(TOKEN.fechaPar)
            self.bloco()
        else:
            self.consome(TOKEN.FOR)
            self.consome(TOKEN.abrePar)
            self.restoComRepete()

    def restoComRepete(self):
        """
        O QUE É: Resolvente de ambiguidade para o comando `for` (`for-in` vs `for` clássico de 3 partes).
        PARA QUE SERVE: Decide qual sintaxe de laço `for` está sendo usada no código.
        COMO FUNCIONA: Usa o lookahead (`espia(1)`) para checar se após a variável há a palavra-chave `in`. 
        Se sim, faz o parse de `for element in collection`; senão, faz o parse do `for` tradicional com ponto e vírgula.
        """
        if self.lido() == TOKEN.ident and self.espia(1) == TOKEN.IN:
            self.consomeVariavel()
            self.consome(TOKEN.IN)
            self.consomeVariavel()
            self.consome(TOKEN.fechaPar)
            self.bloco()
        else:
            self.opcExp()
            self.consome(TOKEN.ptoVirg)
            self.opcExp()
            self.consome(TOKEN.ptoVirg)
            self.opcExp()
            self.consome(TOKEN.fechaPar)
            self.bloco()

    def comDecisao(self):
        """
        O QUE É: Regra gramatical para tomada de decisão condicional (`if`, `elif`, `else`).
        PARA QUE SERVE: Analisa estruturas condicionais completas.
        COMO FUNCIONA: Consome o `if`, a condição entre parênteses, o bloco de código correspondente, 
        seguido de listas opcionais de `elif` e fechando com um `else` opcional.
        """
        self.consome(TOKEN.IF)
        self.consome(TOKEN.abrePar)
        self.exp()
        self.consome(TOKEN.fechaPar)
        self.bloco()
        self.listaElif()
        self.elseOpc()

    def listaElif(self):
        """
        O QUE É: Regra gramatical para múltiplos blocos `elif` encadeados.
        PARA QUE SERVE: Permite avaliar múltiplas condições alternativas em uma decisão.
        COMO FUNCIONA: Se encontrar a palavra-chave `elif`, consome a estrutura condicional e repete recursivamente.
        """
        if self.lido() == TOKEN.ELIF:
            self.consome(TOKEN.ELIF)
            self.consome(TOKEN.abrePar)
            self.exp()
            self.consome(TOKEN.fechaPar)
            self.bloco()
            self.listaElif()

    def elseOpc(self):
        """
        O QUE É: Regra gramatical opcional para o bloco `else`.
        PARA QUE SERVE: Define o comportamento padrão caso nenhuma condição anterior seja satisfeita.
        COMO FUNCIONA: Se encontrar a palavra-chave `else`, consome-a e analisa o bloco associado.
        """
        if self.lido() == TOKEN.ELSE:
            self.consome(TOKEN.ELSE)
            self.bloco()

    def comIO(self):
        """
        O QUE É: Regra gramatical para comandos de Entrada e Saída (`read` e `write`).
        PARA QUE SERVE: Permite leitura de dados do usuário e escrita de valores no console.
        COMO FUNCIONA: Se for `read`, espera uma variável entre parênteses; se for `write`, aceita uma lista de expressões.
        """
        if self.lido() == TOKEN.READ:
            self.consome(TOKEN.READ)
            self.consome(TOKEN.abrePar)
            self.consomeVariavel()
            self.consome(TOKEN.fechaPar)
            self.consome(TOKEN.ptoVirg)
        else:
            self.consome(TOKEN.WRITE)
            self.consome(TOKEN.abrePar)
            self.listaExp()
            self.consome(TOKEN.fechaPar)
            self.consome(TOKEN.ptoVirg)

    def listaExp(self):
        """
        O QUE É: Regra gramatical para uma lista de expressões separadas por vírgula (usada no `write`).
        PARA QUE SERVE: Permite imprimir múltiplos valores ou variáveis de uma só vez.
        COMO FUNCIONA: Avalia uma expressão e chama a função auxiliar para verificar se há mais itens.
        """
        self.exp()
        self.restoListaExp()

    def restoListaExp(self):
        """
        O QUE É: Regra gramatical auxiliar para itens adicionais na lista de expressões.
        PARA QUE SERVE: Processa vírgulas e expressões subsequentes em comandos de escrita.
        COMO FUNCIONA: Se encontrar uma vírgula, consome-a, processa a nova expressão e chama recursivamente.
        """
        if self.lido() == TOKEN.virg:
            self.consome(TOKEN.virg)
            self.exp()
            self.restoListaExp()

    def opcExp(self):
        """
        O QUE É: Regra gramatical opcional para expressão (usada em retornos e comandos `for`).
        PARA QUE SERVE: Permite que trechos como o `return` ou partes do `for` fiquem vazios quando necessário.
        COMO FUNCIONA: Se o token atual fizer parte do início de uma expressão válida, processa a regra 'zero()'.
        """
        if self.lido() in self.INICIO_EXP:
            self.zero()

    # ------------------------------------------------------------
    # Expressões (Precedência de Operadores - Níveis de 0 a 8)
    # ------------------------------------------------------------
    def exp(self):
        """
        O QUE É: Ponto de entrada para a avaliação de expressões.
        PARA QUE SERVE: Delega para o nível mais alto de precedência de operadores.
        COMO FUNCIONA: Chama o método 'zero()', que inicia a hierarquia de precedência de expressões.
        """
        self.zero()

    def zero(self):
        """
        O QUE É: Nível 0 de precedência (incremento e decremento pré-fixados: `++`, `--`).
        PARA QUE SERVE: Trata operadores unários de pré-incremento e pré-decremento em expressões.
        COMO FUNCIONA: Verifica se há operadores `++` ou `--`, consome-os e passa para o próximo nível ('um()').
        """
        if self.lido() == TOKEN.increm:
            self.consome(TOKEN.increm)
            self.um()
        elif self.lido() == TOKEN.decrem:
            self.consome(TOKEN.decrem)
            self.um()
        else:
            self.um()

    def um(self):
        """
        O QUE É: Nível 1 de precedência.
        PARA QUE SERVE: Conecta o nível atual com o operador lógico `OR`.
        COMO FUNCIONA: Processa o nível inferior ('dois()') e chama a verificação do resto ('restoUm()').
        """
        self.dois()
        self.restoUm()

    def restoUm(self):
        """
        O QUE É: Regra recursiva para operador lógico `OR`.
        PARA QUE SERVE: Permite encadear múltiplas operações lógicas `OR`.
        COMO FUNCIONA: Se encontrar o token `OR`, consome-o, avalia o operando à direita e repete.
        """
        if self.lido() == TOKEN.OR:
            self.consome(TOKEN.OR)
            self.dois()
            self.restoUm()

    def dois(self):
        """
        O QUE É: Nível 2 de precedência.
        PARA QUE SERVE: Conecta o nível atual com o operador lógico `AND`.
        COMO FUNCIONA: Processa o nível inferior ('tres()') e chama a verificação do resto ('restoDois()').
        """
        self.tres()
        self.restoDois()

    def restoDois(self):
        """
        O QUE É: Regra recursiva para operador lógico `AND`.
        PARA QUE SERVE: Permite encadear múltiplas operações lógicas `AND`.
        COMO FUNCIONA: Se encontrar o token `AND`, consome-o, avalia o operando à direita e repete.
        """
        if self.lido() == TOKEN.AND:
            self.consome(TOKEN.AND)
            self.tres()
            self.restoDois()

    def tres(self):
        """
        O QUE É: Nível 3 de precedência (negação lógica `NOT`).
        PARA QUE SERVE: Trata o operador unário de negação lógica.
        COMO FUNCIONA: Se encontrar o token `NOT`, consome-o e avalia recursivamente; caso contrário, vai para o nível 'quatro()'.
        """
        if self.lido() == TOKEN.NOT:
            self.consome(TOKEN.NOT)
            self.tres()
        else:
            self.quatro()

    def quatro(self):
        """
        O QUE É: Nível 4 de precedência.
        PARA QUE SERVE: Prepara a avaliação de operadores relacionais.
        COMO FUNCIONA: Processa o nível inferior ('cinco()') e chama a verificação de operadores relacionais ('resto4()').
        """
        self.cinco()
        self.resto4()

    def resto4(self):
        """
        O QUE É: Regra para operadores relacionais (`>`, `>=`, `<`, `<=`, `==`, `!=`).
        PARA QUE SERVE: Compara valores em expressões relacionais.
        COMO FUNCIONA: Se o token atual for um operador relacional válido, consome-o e avalia o operando seguinte.
        """
        if self.lido() in self.OPS_REL:
            self.consome(self.lido())
            self.cinco()

    def cinco(self):
        """
        O QUE É: Nível 5 de precedência.
        PARA QUE SERVE: Prepara a avaliação de operações de adição e subtração algébrica.
        COMO FUNCIONA: Processa o nível inferior ('seis()') e chama o encadeamento 'restoCinco()'.
        """
        self.seis()
        self.restoCinco()

    def restoCinco(self):
        """
        O QUE É: Regra recursiva para operadores de soma (`+`) e subtração (`-`).
        PARA QUE SERVE: Processa operações aritméticas de baixa precedência.
        COMO FUNCIONA: Se encontrar `+` ou `-`, consome o operador, avalia o próximo termo ('seis()') e repete.
        """
        if self.lido() == TOKEN.mais:
            self.consome(TOKEN.mais)
            self.seis()
            self.restoCinco()
        elif self.lido() == TOKEN.menos:
            self.consome(TOKEN.menos)
            self.seis()
            self.restoCinco()

    def seis(self):
        """
        O QUE É: Nível 6 de precedência.
        PARA QUE SERVE: Prepara a avaliação de multiplicação, divisão, divisão inteira (`div`) e resto (`mod`).
        COMO FUNCIONA: Processa o nível inferior ('sete()') e chama o encadeamento 'restoSeis()'.
        """
        self.sete()
        self.restoSeis()

    def restoSeis(self):
        """
        O QUE É: Regra recursiva para operadores multiplicativos (`*`, `/`, `div`, `mod`).
        PARA QUE SERVE: Processa operações aritméticas de alta precedência.
        COMO FUNCIONA: Se encontrar um operador multiplicativo válido, consome-o, avalia o termo seguinte ('sete()') e repete.
        """
        if self.lido() in [TOKEN.multiplica, TOKEN.divide, TOKEN.DIV, TOKEN.MOD]:
            self.consome(self.lido())
            self.sete()
            self.restoSeis()

    def sete(self):
        """
        O QUE É: Nível 7 de precedência (sinais unários `+` e `-`).
        PARA QUE SERVE: Trata sinais positivos ou negativos aplicados diretamente a valores ou variáveis.
        COMO FUNCIONA: Se encontrar unários de sinal (`+` ou `-`), consome-os e chama recursivamente; senão, passa para o nível 'oito()'.
        """
        if self.lido() == TOKEN.mais:
            self.consome(TOKEN.mais)
            self.sete()
        elif self.lido() == TOKEN.menos:
            self.consome(TOKEN.menos)
            self.sete()
        else:
            self.oito()

    def oito(self):
        """
        O QUE É: Nível 8 de precedência (identificadores, chamadas de função, atribuições e vetores).
        PARA QUE SERVE: Trata o uso de variáveis, chamadas de funções e atribuições diretas em expressões.
        COMO FUNCIONA: Se não for identificador, delega para 'folha()'. Se for identificador, verifica se é 
        chamada de função (seguido de parêntese), acesso a vetor (colchete) ou atribuição de valor.
        """
        if self.lido() != TOKEN.ident:
            self.folha()
            return

        (token, lexema, linha, coluna) = self.tokenLido
        self.consome(TOKEN.ident)

        if self.lido() == TOKEN.abrePar:             # chamada: ident ( ListaParam )
            self.consome(TOKEN.abrePar)
            self.listaParam(TOKEN.fechaPar)
            self.consome(TOKEN.fechaPar)
            return

        self.checaMaiuscula(lexema, linha, coluna)    # é variável
        if self.lido() == TOKEN.abreCol:              # OpcPos / RestoFolha: [ Zero ]
            self.consome(TOKEN.abreCol)
            self.zero()
            self.consome(TOKEN.fechaCol)
        if self.lido() == TOKEN.atrib:                # atribuição
            self.consome(TOKEN.atrib)
            self.oito()

    def folha(self):
        """
        O QUE É: Regra base (folha) da árvore de expressões.
        PARA QUE SERVE: Processa literais (números, strings), listas literais, expressões entre parênteses ou identificadores.
        COMO FUNCIONA: Identifica se o token é um valor constante, lista, parêntese ou identificador, consumindo-o adequadamente.
        """
        t = self.lido()
        if t in [TOKEN.valorInt, TOKEN.valorFloat, TOKEN.valorString]:
            self.consome(t)
        elif t == TOKEN.abreCol:
            self.valorLista()
        elif t == TOKEN.abrePar:
            self.consome(TOKEN.abrePar)
            self.zero()
            self.consome(TOKEN.fechaPar)
        elif t == TOKEN.ident:
            self.oito()
        else:
            self.erro(f"Era esperada uma expressão mas veio {self.descreve()}")

    def valorLista(self):
        """
        O QUE É: Regra gramatical para inicialização literal de listas/vetores (`[ ListaParam ]`).
        PARA QUE SERVE: Permite definir conteúdos de vetores diretamente no código (ex: `[1, 2, 3]`).
        COMO FUNCIONA: Consome o colchete de abertura, processa a lista de parâmetros internos e consome o colchete de fechamento.
        """
        self.consome(TOKEN.abreCol)
        self.listaParam(TOKEN.fechaCol)
        self.consome(TOKEN.fechaCol)

    def listaParam(self, fecha):
        """
        O QUE É: Regra gramatical para lista de parâmetros em chamadas de função ou listas.
        PARA QUE SERVE: Gerencia os argumentos repassados dinamicamente.
        COMO FUNCIONA: Se o token atual não for o delimitador de fechamento esperado, processa o parâmetro e o restante da lista.
        """
        if self.lido() != fecha:
            self.param()
            self.restoListaParam()

    def restoListaParam(self):
        """
        O QUE É: Regra recursiva para múltiplos parâmetros separados por vírgula.
        PARA QUE SERVE: Trata parâmetros adicionais em chamadas de funções ou construtores de listas.
        COMO FUNCIONA: Se encontrar uma vírgula, consome-a, processa o parâmetro e chama recursivamente.
        """
        if self.lido() == TOKEN.virg:
            self.consome(TOKEN.virg)
            self.param()
            self.restoListaParam()

    def param(self):
        """
        O QUE É: Regra gramatical de um parâmetro individual (Param -> Zero).
        PARA QUE SERVE: Avalia uma expressão individual passada como parâmetro.
        COMO FUNCIONA: Delega diretamente para a regra de expressão 'zero()'.
        """
        self.zero()


# ---------------------------------------------------
# Execução:  python sintatico_d.py programa.d   (ou sem argumento: exemplo)
# ---------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            Sintatico(Lexico(f)).traduz()
    else:
        codigo = '''
        int Fib(int N) {
            if (N <= 1) { return N; }
            return Fib(N - 1) + Fib(N - 2);
        }
        void main() {
            int R = 0, V[];
            V = [1, 2, 3];
            for (I in V) { write(I); }
            for (R = 0; R < 10; R = R + 1) { write(R); }
            R = Fib(10);
            write("Fib: ", R);
        }
        '''
        Sintatico(Lexico(io.StringIO(codigo))).traduz()