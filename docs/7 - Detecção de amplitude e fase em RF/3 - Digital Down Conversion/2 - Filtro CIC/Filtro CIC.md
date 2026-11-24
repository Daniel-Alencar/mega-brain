# Filtro CIC

Na eletrônica e telecomunicações, o filtro CIC (*Cascaded Integrator-Comb*) é uma classe especial de filtro que altera a taxa de amostragem de um sinal (diminuindo ou aumentando). Ele opera sem usar multiplicadores, o que o torna incrivelmente eficiente em hardware (como chips FPGA ou ASICs) para aplicações de rádio digital e processamento de áudio. 

**Função principal:** Realizar *decimation* (redução da taxa de amostragem) ou *interpolation* (aumento da taxa de amostragem).

**Como funciona:** Ele é composto por duas partes em cascata: uma parte integradora e uma parte pente (*comb*). Geralmente, reduz taxas de amostragem muito altas para valores intermediários, economizando poder computacional antes do uso de filtros FIR tradicionais.

Um CIC é definido por três números: o fator de decimação $R$, o atraso diferencial do comb
$D$ e o número de estágios $M$ (a seção 8 detalha cada um). A **janela** do filtro tem
$R \cdot D$ amostras, e em todo o texto ela vale 4:

| | $R$ | $D$ | $M$ | janela $R\cdot D$ |
| --- | --- | --- | --- | --- |
| seções 1 a 4 | 1 | 4 | 1 | 4 — o filtro ainda não decima |
| seção 5 | 2, 4, 8, 16 | 1 | 1 | igual a $R$ |
| seções 6 a 9 | 4 | 1 | 1 | 4 — o exemplo de referência |

Nas seções 8 e 9 um parâmetro de cada vez sai desse ponto de partida: primeiro $D$, depois
$M$.

## 0. Lendo o diagrama de blocos

Antes da matemática, vale saber ler o desenho. Um diagrama de CIC tem só quatro símbolos:

| Símbolo | O que é | O que faz |
| --- | --- | --- |
| **Seta** | um fio | por onde as amostras andam: **uma amostra nova a cada ciclo de clock** |
| **$\Sigma$ em um círculo** | somador | junta o que chega pelas setas; o `+` ou `−` ao lado de cada entrada diz o sinal |
| **Caixa $z^{-1}$** | registrador (*flip-flop*) | guarda a amostra deste ciclo e a devolve no ciclo seguinte |
| **Ponto cheio** | nó (derivação) | o mesmo valor segue por dois caminhos ao mesmo tempo — ele é **copiado, não dividido** |

Duas consequências que explicam o filtro inteiro:

- $z^{-D}$ não é um símbolo novo: são **$D$ registradores em fila**. O valor leva $D$ ciclos para atravessar a fila e sair pela outra ponta.
- Se um fio **volta** para um bloco anterior, há **realimentação** (memória infinita). Se nenhum fio volta, o bloco só olha um pedaço finito do passado.

É exatamente essa a diferença entre as duas metades do CIC: o integrador é realimentado, o comb não é.

## 1. O Integrador

O Integrador é o bloco que faz o trabalho bruto de guardar absolutamente tudo o que entra. Matematicamente, ele é a soma contínua de todo o histórico do sinal desde que o sistema foi ligado.

$$I[n] = I[n-1] + x[n]$$

Lendo o diagrama: o somador recebe a amostra nova $x[n]$ e, pelo fio que volta, o valor que o registrador guardou no ciclo anterior ($I[n-1]$). O resultado sai pelo nó — e o nó manda esse mesmo resultado para dois lugares: para a saída e de volta para o registrador.

Ciclo a ciclo, com a entrada `2, 1, 3, 1, 2`:

| $n$ | $x[n]$ | $z^{-1}$ (guardado) | $I[n]$ |
| --- | --- | --- | --- |
| 0 | 2 | 0 | 2 |
| 1 | 1 | 2 | 3 |
| 2 | 3 | 3 | 6 |
| 3 | 1 | 6 | 7 |
| 4 | 2 | 7 | 9 |

- **No exemplo:** Quando o sinal chega no instante 4, o integrador pegou a amostra nova ($x[4]$) e somou com todo o seu passado:
    
    $I[4] = x[4] + x[3] + x[2] + x[1] + x[0]$
    
- **O seu papel:** Sozinho, o integrador não filtra nada. Ele apenas acumula os dados em alta velocidade, deixando o valor crescer indefinidamente (causando um *overflow* proposital no limite de bits do hardware). Em aritmética de complemento de dois o comb desfaz esse estouro e a saída final continua correta.

## 2. O Comb

O Comb (pente) é o bloco que "puxa o freio". A função dele é olhar para o valor gigante acumulado do Integrador agora e subtrair o valor que ele tinha no passado (neste caso, 4 amostras atrás).

$$y[n] = I[n] - I[n-4]$$

No diagrama, o $I[n]$ chega a um nó e segue por dois caminhos: por cima vai direto ao somador (entrada `+`); por baixo entra na fila de quatro registradores e só chega ao somador (entrada `−`) quatro ciclos depois. Nos quatro primeiros ciclos a fila ainda está enchendo e nada é subtraído; a partir do quinto, sempre sai pela ponta o valor de 4 ciclos atrás.

- **No exemplo:** A equação $y[n] = I[n] - I[n-4]$ atua como uma tesoura.
- **O seu papel:** Ao fazer a equação $(x[4] + x[3] + x[2] + x[1] + x[0]) - (x[0])$, ele anula o $x[0]$ e corta o passado distante. Ele transforma aquela acumulação infinita em uma **janela limitada e precisa de 4 amostras**:
    
    $y[4] = x[4] + x[3] + x[2] + x[1]$
    

## 3. O Efeito de Filtragem (A Média Móvel)

É aqui que a mágica acontece. O Integrador e o Comb, trabalhando juntos, formaram um somatório de uma janela fechada (uma média móvel). E é essa janela que atua como o **filtro passa-baixa**, distinguindo o que é ruído do que é sinal útil.

$$y[n] = x[n] + x[n-1] + x[n-2] + x[n-3]$$

Dividindo por 4, é literalmente a média das 4 últimas amostras. Dito de outro jeito: a resposta ao impulso do CIC é `1 1 1 1`, ou seja, ele é um **filtro FIR de 4 coeficientes iguais a 1** — a diferença é que ele chega nesse resultado sem nenhum multiplicador, só com um somador, um subtrator e registradores.

### Destruindo o Ruído (Cenário de Alta Frequência)

O ruído de alta frequência varia muito rápido. A cada instante ele muda de fase (sobe e desce).

- **Entrada rápida:** `+1, -1, +1, -1`
- **Ação dos blocos:** Como a janela matemática do CIC é obrigada a somar esses 4 itens juntos, os picos positivos encontram os vales negativos no mesmo exato momento dentro da equação.
- **Resultado ($0$):** O ruído se auto-cancela. O filtro barrou com sucesso a alta frequência.

### Preservando o Sinal (Cenário de Baixa Frequência)

O seu sinal útil (a banda base onde está a informação que você quer demodular) varia de forma extremamente lenta. O "topo" de uma onda de baixa frequência dura dezenas ou centenas de amostras.

- **Entrada lenta:** `+1, +1, +1, +1`
- **Ação dos blocos:** Como a onda quase não mudou de valor durante essas 4 amostras, não há nada negativo para cancelar a soma.
- **Resultado ($4$):** A soma se acumula perfeitamente. O sinal sobrevive ao filtro. Ele sai 4 vezes maior (o que chamamos de *ganho intrínseco* do filtro), mas a forma da onda e a informação continuam intactas.

## 4. A resposta em frequência

Os dois cenários acima testam só duas frequências. A **resposta em frequência** é o mesmo teste feito para *todas* elas, e é isso que o gráfico de $|H(f)|$ mostra.

A receita é sempre a mesma: entra uma senoide pura de frequência $f$, mede-se a amplitude que sai, e o ganho é a razão entre as duas. Repetindo para cada $f$ entre 0 e $f_s/2$ (o limite de Nyquist, a maior frequência que um sinal amostrado consegue representar), os pontos medidos desenham a curva.

Para a janela de 4 amostras ($R = 1$, $D = 4$, $M = 1$):

| Frequência | Amostras por período | Ganho | Normalizado ($\div 4$) |
| --- | --- | --- | --- |
| $0$ (DC) | ∞ | 4,00 | 1,000 |
| $f_s/16$ | 16 | 3,63 | 0,906 |
| $f_s/8$ | 8 | 2,61 | 0,653 |
| $f_s/4$ | 4 | **0** | 0 |
| ≈ $0{,}37\,f_s$ | ≈ 2,7 | 1,09 | 0,272 (−11,3 dB) |
| $f_s/2$ | 2 | **0** | 0 |

**Como ler o gráfico:**

- **Eixo horizontal:** a frequência do sinal que entra, de 0 (DC) até $f_s/2$.
- **Eixo vertical:** o ganho — por quanto a amplitude daquela frequência é multiplicada.
- **Em DC o ganho é $D$** (aqui, 4): é o ganho intrínseco. Dividir a saída por $D$ normaliza o filtro.
- **Os zeros** estão em $f_s/4$ e $f_s/2$, ou seja, em múltiplos de $f_s/D$. O motivo é geométrico: em $f_s/4$ cabe **exatamente um período inteiro** dentro da janela de 4 amostras (`+1, 0, −1, 0`), e em $f_s/2$ cabem **dois períodos inteiros** (`+1, −1, +1, −1`). Toda vez que um número inteiro de períodos cabe na janela, a soma dá zero.
- **Lóbulo principal:** a faixa que o filtro deixa passar, do DC até o primeiro zero.
- **Lóbulos laterais:** o que escapa entre um zero e o próximo. Para $D = 4$ o pico do primeiro lóbulo lateral vale 1,09 contra 4 em DC — cerca de **−11 dB** apenas. É o ponto fraco do CIC, e a razão de ele quase nunca andar sozinho.

A forma fechada dessa curva é:

$$|H(f)| = \left| \frac{\sin(\pi D f / f_s)}{\sin(\pi f / f_s)} \right|$$

- o **numerador** zera sempre que $D f / f_s$ é inteiro — são os zeros, em $f_s/D,\ 2f_s/D,\ 3f_s/D \dots$;
- em $f = 0$ numerador e denominador zeram juntos e a razão vale exatamente $D$;
- é o mesmo formato de um *sinc*, só que amostrado: o "sinc digital" (núcleo de Dirichlet).

Trocando $D$ pela janela $R \cdot D$, essa fórmula descreve qualquer CIC de um estágio.

## 5. Trocando o fator de decimação $R$

Até aqui o filtro não decimava: a janela de 4 vinha do comb ($R = 1$, $D = 4$). A partir
daqui o CIC decima, e a janela passa a vir do $R$, com o comb reduzido a um registrador
($D = 1$). Tudo o que foi dito vale para qualquer janela — só os números mudam, e de forma
previsível:

| | $R = 2$ | $R = 4$ | $R = 8$ | $R = 16$ |
| --- | --- | --- | --- | --- |
| Janela $R \cdot D$ | 2 | 4 | 8 | 16 |
| Ganho em DC | 2 | 4 | 8 | 16 |
| Primeiro zero | $f_s/2$ | $f_s/4$ | $f_s/8$ | $f_s/16$ |
| Taxa de saída | $f_s/2$ | $f_s/4$ | $f_s/8$ | $f_s/16$ |
| Banda útil | $\approx f_s/4$ | $\approx f_s/8$ | $\approx f_s/16$ | $\approx f_s/32$ |

Passando o mesmo sinal ruidoso por cada um deles:

- $R = 2$: quase nada muda — são só duas amostras somadas.
- $R = 4$: o ruído já cai bastante e a onda continua inteira. É a mesma janela de 4 das
  seções anteriores — o mesmo filtro, agora com a janela vindo do $R$.
- $R = 8$: bem mais limpo, com uma amostra de saída a cada oito.
- $R = 16$: liso, mas a própria onda já perde amplitude. Para um seno de período de 40 amostras, o ganho normalizado cai para 0,758 — uma perda de cerca de 24%, o chamado ***droop***.

Esse é o compromisso: **janela maior deixa a saída mais suave e mais barata, mas mais lenta e com mais droop na banda útil**.

## 6. Por que o CIC é justamente o filtro certo para decimar

Decimar por $R$ é ficar com 1 amostra a cada $R$. No espectro, isso **dobra** tudo o que estiver em torno de $f_s/R,\ 2f_s/R,\ 3f_s/R \dots$ para cima da banda base — e, depois de dobrado, não há mais como separar o que era sinal do que era lixo (*aliasing*).

Agora compare com a lista de zeros do CIC, que estão em múltiplos de $f_s/(R \cdot D)$: com $D = 1$ eles caem em **exatamente essas mesmas frequências**. O CIC não é um passa-baixa qualquer que por acaso serve; ele é o filtro anti-aliasing feito sob medida para o fator de decimação que vai ser usado logo depois dele.

A ressalva é que o zero é um ponto, não uma faixa: nas **bordas** dessas bandas a atenuação é bem menor (os tais −11 dB do lóbulo lateral). Por isso a cadeia padrão é **CIC primeiro, FIR depois**: o CIC derruba o grosso na taxa alta e barata, e o FIR, já rodando na taxa baixa, limpa o que sobrou e corrige o droop.

## 7. Onde a decimação se encaixa

A janela de 4 amostras pode ser obtida de duas maneiras: sem decimar, com o comb olhando 4 amostras para trás ($R = 1$, $D = 4$); ou decimando por 4, com o comb olhando uma só ($R = 4$, $D = 1$). Em um hardware real (como no FPGA) usa-se a segunda: inserimos o **Decimador** entre o Integrador e o Comb e reduzimos a taxa de amostragem (velocidade do clock) em 4 vezes.

Isso faz com que o Comb, mesmo olhando apenas $1$ amostra para trás no seu novo "tempo lento", esteja na verdade subtraindo um valor de $4$ amostras atrás do "tempo rápido" original. O resultado da equação e o efeito de cancelamento das ondas ficam exatamente idênticos aos do seu exemplo matemático.

Comparando as duas ordens possíveis:

- **Ingênua:** `x[n] → Integrador (f_s) → Comb z⁻⁴ (f_s) → ↓4 → y[m]`. Funciona, mas o comb calcula 4 saídas para 3 irem direto para o lixo, e precisa de 4 registradores.
- **Hogenauer:** `x[n] → Integrador (f_s) → ↓4 → Comb z⁻¹ (f_s/4) → y[m]`. Mesma saída, com o comb rodando a 1/4 da taxa e usando **um único registrador**.

No tempo lento, $z^{-1}$ **já é** $z^{-4}$ no tempo rápido — é só isso que o truque explora. Na interpolação a ordem se inverte: comb → $\uparrow R$ → integrador.

## 8. O atraso diferencial $D$, e as três letras de um CIC

Na seção 7 o comb da taxa lenta ficou com $z^{-1}$: ele olha **uma** amostra
lenta para trás. Mas nada obriga que seja uma. O comb pode ter $z^{-D}$, com $D$
registradores — esse $D$ é o **atraso diferencial**.

Como cada passo lento vale $R$ passos rápidos, a janela equivalente no tempo
rápido é

$$\text{janela} = R \cdot D \ \text{amostras}$$

### A notação

| Letra | O que é |
| --- | --- |
| $R$ | fator de decimação — quantas amostras se descarta |
| $D$ | atraso diferencial do comb — quantos registradores ele tem |
| $M$ | número de estágios — quantas vezes o filtro é repetido (seção 9). Parte da literatura chama esse número de $N$ |

São as mesmas letras da seção 3 de [Digital Down Conversion](../Digital%20Down%20Conversion.md),
onde o CIC aparece como $M$ integradores, $\downarrow R$ e $M$ pentes de atraso $D$, com

$$|H(f)| = \left| \frac{\sin(\pi D f / f_{out})}{\sin(\pi f / f_{in})} \right|^{M}
\qquad \text{e zeros em } k\,\frac{f_s}{R D}$$

As seções 1 a 4 não têm decimador: $R = 1$ e $D = 4$, logo a janela é
$R \cdot D = 4$. Da seção 5 em diante o CIC decima e a janela passa a vir do $R$,
com o comb reduzido a um registrador ($D = 1$); o exemplo de referência vira
$R = 4$, $D = 1$. A janela continua valendo 4 nos dois casos, e é por isso que a
resposta é idêntica.

### O que $D$ faz com o gráfico

Aqui está a diferença importante em relação à seção 5. Lá, aumentar a janela
aumentava junto o fator de decimação, e portanto mudava a **taxa de saída**.
Agora $R$ fica fixo em 4 — a taxa de saída é a mesma nos três casos — e $D$ muda
**só o formato do filtro**, em relação a marcos que não se movem:

- a **banda útil**, de 0 a $f_s/16$;
- o **Nyquist da saída**, em $f_s/(2R) = f_s/8$;
- as **faixas que dobram** ao decimar por 4, em torno de $f_s/4$ e $f_s/2$.

Os zeros ficam em múltiplos de $f_s/(RD)$, então aumentar $D$ os traz para a
esquerda, para cima desses marcos:

| | $D = 1$ | $D = 2$ | $D = 4$ |
| --- | --- | --- | --- |
| janela equivalente $R\cdot D$ | 4 amostras | 8 amostras | 16 amostras |
| 1º zero | $f_s/4$ | $f_s/8$ | $f_s/16$ |
| topo da banda útil ($f_s/16$) | −0,9 dB | −3,9 dB | **zero** |
| pior vazamento ao decimar | −9,9 dB | −13,0 dB | −20,1 dB |
| registradores no comb | 1 | 2 | 4 |

Lendo a tabela de cima para baixo: **mais $D$ é mais rejeição, pago em banda
útil**.

- $D = 1$ põe um zero no centro de cada faixa que dobra — é exatamente o
  argumento da seção 6.
- $D = 2$ põe o primeiro zero **em cima do Nyquist da saída**. É o limite
  natural: o zero pousa na borda do que a saída ainda consegue representar, e
  isso compra 3 dB de rejeição a mais.
- $D = 4$ rejeita ainda melhor, mas joga um zero **para dentro da banda útil**:
  o filtro passa a apagar o próprio sinal que deveria preservar.

Por isso um CIC real usa $D = 1$ ou $D = 2$, e quase nunca mais que isso. Quando
é preciso rejeitar mais, aumenta-se $M$ (seção 9), não $D$.

> A curva de $D = 2$ é a mesma de uma janela de 8 na seção 5 — afinal
> $R \cdot D = 8$ nos dois casos. O que muda é o motivo: lá a janela maior vinha
> junto com uma decimação maior; aqui a taxa de saída não mudou.

## 9. O número de estágios $M$ — o "Cascaded" do nome

Tudo até aqui descreveu um CIC de **um estágio**: um integrador e um comb. Um
CIC de verdade quase nunca tem um só. Um **estágio** é esse par completo, e
usar $M$ estágios é aplicar o mesmo filtro $M$ vezes seguidas — a saída de um é
a entrada do próximo. Daí o *Cascaded* do nome.

Na prática ele não é desenhado assim. Como integrar e decimar comutam (seção 7),
os blocos iguais podem ser agrupados: **$M$ integradores, o decimador, $M$
combs**. É o mesmo filtro, redesenhado.

### O que $M$ faz com o sinal: a janela muda de forma

A maneira mais concreta de ver o efeito de $M$ é olhar a janela que o filtro
aplica. Filtrar duas vezes é convoluir a resposta ao impulso consigo mesma:

$$h_M = \underbrace{h_1 * h_1 * \cdots * h_1}_{M \text{ vezes}}$$

Com uma janela de 4 amostras:

| $M$ | Resposta ao impulso | Forma | Comprimento | Ganho em DC |
| --- | --- | --- | --- | --- |
| 1 | `1 1 1 1` | retangular | 4 | 4 |
| 2 | `1 2 3 4 3 2 1` | triangular | 7 | 16 |
| 3 | `1 3 6 10 12 12 10 6 3 1` | um sino | 10 | 64 |

Fazer a média das médias deixa de pesar todas as amostras igualmente: as do meio
entram em várias janelas e passam a pesar mais que as das pontas. É daí que vem
tudo o mais — a rejeição melhor (transição suave em vez de corte seco) e o
atraso maior (a janela tem $M(RD-1)+1$ amostras).

### O mesmo gráfico da seção 4, agora com $M = 4$

Como os estágios são idênticos e em cascata, as respostas se multiplicam:

$$|H_M(f)| = |H_1(f)|^M$$

Vale olhar isso primeiro no **mesmo gráfico da seção 4** — eixo linear, ganho
normalizado para 1 em DC, com a janela de 4 amostras do exemplo. Três coisas
mudam, e uma não muda:

| | $M = 1$ | $M = 2$ | $M = 4$ |
| --- | --- | --- | --- |
| pico do lóbulo lateral | 0,272 | 0,074 | 0,0055 |
| o mesmo em dB | −11 dB | −23 dB | −45 dB |
| ganho em $f_s/16$ | 0,91 | 0,82 | 0,67 |
| posição dos zeros | $f_s/4$, $f_s/2$ | $f_s/4$, $f_s/2$ | $f_s/4$, $f_s/2$ |
| ordem dos zeros | 1 | 2 | 4 |

- **Os zeros não se movem.** Quem posiciona os zeros é $D$ (seção 8); $M$ não
  mexe neles. O que muda é a **ordem**: com $M = 4$ o zero é quádruplo, e a
  curva deixa de cruzar o eixo em bico — ela encosta e fica rente a ele, o que
  alarga a região de atenuação forte em torno de cada zero.
- **O lóbulo lateral praticamente desaparece**: $0{,}272^4 = 0{,}0055$. É o
  ponto fraco do CIC (seção 4) sendo resolvido.
- **A banda útil afunda**: o ganho em $f_s/16$ cai de 0,91 para 0,67. O droop é
  o preço.
- E, na escala linear, o lóbulo de $M = 4$ simplesmente **não se vê mais** — é
  essa a razão de todo artigo sobre CIC mostrar a resposta em dB.

### O que $M$ faz com o gráfico em dB

Em dB (assunto 9), elevar a $M$ é só multiplicar a curva inteira por $M$:

| | Lóbulo lateral | Droop em $f_s/16$ | Droop em $f_s/8$ | Atraso | Bits a mais |
| --- | --- | --- | --- | --- | --- |
| $M = 1$ | −11 dB | −0,9 dB | −3,7 dB | 1,5 amostras | +2 |
| $M = 2$ | −23 dB | −1,7 dB | −7,4 dB | 3,0 amostras | +4 |
| $M = 3$ | −34 dB | −2,6 dB | −11,1 dB | 4,5 amostras | +6 |
| $M = 4$ | −45 dB | −3,4 dB | −14,8 dB | 6,0 amostras | +8 |

Cada estágio tira cerca de **11 dB** do lóbulo lateral — e multiplica o droop na
mesma proporção. O atraso é $M(RD-1)/2$ amostras, e o crescimento do acumulador
(seção 3) passa a exigir $M\log_2(RD)$ bits a mais.

### Então quanto vale aumentar $M$?

Aqui vale desfazer uma expectativa. Passando o mesmo sinal ruidoso por 1, 2, 3 e
4 estágios, o desvio-padrão do ruído cai assim:

| $M$ | 1 | 2 | 3 | 4 |
| --- | --- | --- | --- | --- |
| $\sigma$ do ruído | 0,25 | 0,21 | 0,19 | 0,18 |

Ou seja: **o sinal quase não fica mais liso**. O primeiro estágio faz quase todo
o trabalho de suavização, e o quarto quase não acrescenta nada visível.

O ganho real de mais estágios não está na aparência do sinal — está no que o
lóbulo lateral **rejeita**. Com $M = 1$, uma interferência que caia num lóbulo é
atenuada só 11 dB antes de dobrar sobre a banda base na decimação (seção 6); com
$M = 3$, são 34 dB. Mais estágios não deixam o sinal mais bonito: deixam a
decimação mais segura.

O preço é o droop, e é por isso que depois do CIC vem um **FIR compensador**, que
corrige essa inclinação e termina a filtragem.
