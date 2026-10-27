# Filtro CIC

Na eletrônica e telecomunicações, o filtro CIC (*Cascaded Integrator-Comb*) é uma classe especial de filtro que altera a taxa de amostragem de um sinal (diminuindo ou aumentando). Ele opera sem usar multiplicadores, o que o torna incrivelmente eficiente em hardware (como chips FPGA ou ASICs) para aplicações de rádio digital e processamento de áudio. 

**Função principal:** Realizar *decimation* (redução da taxa de amostragem) ou *interpolation* (aumento da taxa de amostragem).

**Como funciona:** Ele é composto por duas partes em cascata: uma parte integradora e uma parte pente (*comb*). Geralmente, reduz taxas de amostragem muito altas para valores intermediários, economizando poder computacional antes do uso de filtros FIR tradicionais.

Em todo o texto o exemplo usa um atraso de $D = 4$ no comb (uma janela de 4 amostras).

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

Para $D = 4$:

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

## 5. Trocando o fator $D$

Tudo o que foi dito vale para qualquer $D$ — só os números mudam, e de forma previsível:

| | $D = 2$ | $D = 4$ | $D = 8$ | $D = 16$ |
| --- | --- | --- | --- | --- |
| Ganho em DC | 2 | 4 | 8 | 16 |
| Primeiro zero | $f_s/2$ | $f_s/4$ | $f_s/8$ | $f_s/16$ |
| Taxa de saída | $f_s/2$ | $f_s/4$ | $f_s/8$ | $f_s/16$ |
| Banda útil | $\approx f_s/4$ | $\approx f_s/8$ | $\approx f_s/16$ | $\approx f_s/32$ |

Passando o mesmo sinal ruidoso por cada um deles:

- $D = 2$: quase nada muda — são só duas amostras somadas.
- $D = 4$: o ruído já cai bastante e a onda continua inteira.
- $D = 8$: bem mais limpo, com uma amostra de saída a cada oito.
- $D = 16$: liso, mas a própria onda já perde amplitude. Para um seno de período de 40 amostras, o ganho normalizado cai para 0,758 — uma perda de cerca de 24%, o chamado ***droop***.

Esse é o compromisso: **$D$ maior deixa a saída mais suave e mais barata, mas mais lenta e com mais droop na banda útil**.

## 6. Por que o CIC é justamente o filtro certo para decimar

Decimar por $D$ é ficar com 1 amostra a cada $D$. No espectro, isso **dobra** tudo o que estiver em torno de $f_s/D,\ 2f_s/D,\ 3f_s/D \dots$ para cima da banda base — e, depois de dobrado, não há mais como separar o que era sinal do que era lixo (*aliasing*).

Agora compare com a lista de zeros do CIC: eles estão em **exatamente essas mesmas frequências**. O CIC não é um passa-baixa qualquer que por acaso serve; ele é o filtro anti-aliasing feito sob medida para o fator de decimação que vai ser usado logo depois dele.

A ressalva é que o zero é um ponto, não uma faixa: nas **bordas** dessas bandas a atenuação é bem menor (os tais −11 dB do lóbulo lateral). Por isso a cadeia padrão é **CIC primeiro, FIR depois**: o CIC derruba o grosso na taxa alta e barata, e o FIR, já rodando na taxa baixa, limpa o que sobrou e corrige o droop.

## 7. Onde a decimação se encaixa

No exemplo, assumimos um atraso de $D=4$ para o bloco Comb. Em um hardware real (como no FPGA), nós inserimos o **Decimador** entre o Integrador e o Comb e reduzimos a taxa de amostragem (velocidade do clock) em 4 vezes.

Isso faz com que o Comb, mesmo olhando apenas $1$ amostra para trás no seu novo "tempo lento", esteja na verdade subtraindo um valor de $4$ amostras atrás do "tempo rápido" original. O resultado da equação e o efeito de cancelamento das ondas ficam exatamente idênticos aos do seu exemplo matemático.

Comparando as duas ordens possíveis:

- **Ingênua:** `x[n] → Integrador (f_s) → Comb z⁻⁴ (f_s) → ↓4 → y[m]`. Funciona, mas o comb calcula 4 saídas para 3 irem direto para o lixo, e precisa de 4 registradores.
- **Hogenauer:** `x[n] → Integrador (f_s) → ↓4 → Comb z⁻¹ (f_s/4) → y[m]`. Mesma saída, com o comb rodando a 1/4 da taxa e usando **um único registrador**.

No tempo lento, $z^{-1}$ **já é** $z^{-4}$ no tempo rápido — é só isso que o truque explora. Na interpolação a ordem se inverte: comb → $\uparrow R$ → integrador.

## 8. Por que "Cascaded": N estágios

Um CIC de verdade quase nunca tem um estágio só. Colocam-se $N$ integradores antes do decimador e $N$ combs depois — daí o *Cascaded* do nome. Como os estágios são idênticos e em cascata, a resposta simplesmente vira $|H(f)|^N$:

| | Lóbulo lateral | Droop em $f_s/16$ |
| --- | --- | --- |
| $N = 1$ | −11 dB | −0,9 dB |
| $N = 2$ | −23 dB | −1,7 dB |
| $N = 3$ | −34 dB | −2,6 dB |

Mais estágios rejeitam muito melhor o que iria dobrar sobre o sinal na decimação; o preço é a banda útil afundar mais perto de DC. É esse droop que o **FIR compensador** seguinte corrige.
