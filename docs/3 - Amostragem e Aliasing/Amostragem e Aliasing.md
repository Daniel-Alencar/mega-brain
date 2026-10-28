# Amostragem e Aliasing

Terceiro assunto da trilha, e o pré-requisito mais usado do repositório: tudo o
que vem depois — detecção de amplitude e fase, decimação, filtros digitais,
up-conversion — acontece **depois** de um ADC. Aqui se estabelece o que a
amostragem preserva, o que ela destrói sem avisar, e como escolher a taxa.

São dois erros independentes, e vale separá-los desde o começo:

| | Pergunta | Erro | Recuperável? |
| --- | --- | --- | --- |
| **Amostragem** | *quando* se mede | aliasing | **não** — a informação não existe mais |
| **Quantização** | *com quantos bits* se mede | ruído de quantização | não, mas é previsível e pequeno |

Exemplo numérico usado aqui e na animação: $f_s = 10$ kHz (período
$T = 0{,}1$ ms), sinal útil de 0 a 4 kHz.

## 1. A ambiguidade: a mesma sequência serve a infinitas ondas

Amostrar é guardar o valor do sinal em instantes $t = nT$ e **não guardar mais
nada**. Entre duas amostras não existe informação — e é aí que nasce o problema.

Com $f_s = 10$ kHz, as três senoides abaixo passam exatamente pelos mesmos
pontos:

$$\cos(2\pi \cdot 1\,\text{kHz} \cdot nT) = \cos(2\pi \cdot 9\,\text{kHz} \cdot nT)
= \cos(2\pi \cdot 11\,\text{kHz} \cdot nT)$$

A conta é só aritmética de arco. Para $f = 9$ kHz e $T = 1/10$ kHz:

$$\cos\!\left(2\pi \cdot \frac{9n}{10}\right)
= \cos\!\left(2\pi n - 2\pi \cdot \frac{n}{10}\right)
= \cos\!\left(2\pi \cdot \frac{n}{10}\right)$$

porque o cosseno tem período $2\pi$ e é par. Mais geralmente, **toda** frequência
$f + k f_s$, com $k$ inteiro, produz a mesma sequência que $f$. Olhando só os
números, não há como decidir qual das infinitas ondas foi amostrada.

Esse é o fato central: o ADC não erra a medida de cada amostra: ele **perde a
identidade da frequência**. O nome desse apagamento é *aliasing* — a frequência
alta adota o "apelido" (*alias*) de uma frequência baixa.

## 2. De onde vem: amostrar é multiplicar por um pente de impulsos

A forma rigorosa de ver o mesmo fato é no domínio da frequência. O sinal
amostrado pode ser escrito como o sinal contínuo multiplicado por um trem de
impulsos (*Dirac comb*) espaçados de $T$:

$$x_s(t) = x(t) \cdot \sum_{n=-\infty}^{\infty} \delta(t - nT)$$

E a transformada de Fourier de um pente de impulsos no tempo é **outro pente de
impulsos na frequência**, espaçados de $f_s = 1/T$. Como multiplicação no tempo
é convolução na frequência, convoluir o espectro do sinal com esse pente
**replica o espectro inteiro em torno de cada múltiplo de $f_s$**:

$$X_s(f) = f_s \sum_{k=-\infty}^{\infty} X(f - k f_s)$$

O espectro de um sinal amostrado é, portanto, **periódico** com período $f_s$ —
e essa periodicidade é a mesma armadilha da seção 1 vista de outro ângulo: as
réplicas em $f + k f_s$ são as infinitas ondas que caberiam nas mesmas amostras.

## 3. O critério de Nyquist-Shannon

As réplicas vizinhas são cópias do mesmo espectro, deslocadas de $f_s$. Se o
sinal vai de $0$ a $f_{max}$, a réplica centrada em $f_s$ começa em
$f_s - f_{max}$. Para que ela não invada a banda original é preciso que

$$f_s - f_{max} > f_{max} \qquad \Longrightarrow \qquad \boxed{f_s > 2 f_{max}}$$

A frequência $f_s/2$ é a **frequência de Nyquist**: a maior frequência que a
taxa $f_s$ consegue representar sem ambiguidade. Os três regimes:

| Taxa | O que acontece com as réplicas | Resultado |
| --- | --- | --- |
| $f_s > 2f_{max}$ | ficam separadas, com uma folga de $f_s - 2f_{max}$ | reconstrução exata é possível |
| $f_s = 2f_{max}$ | encostam-se exatamente em $f_{max}$ | caso-limite teórico, inútil na prática |
| $f_s < 2f_{max}$ | **sobrepõem-se** | aliasing: as bandas se somam e não há como separá-las |

O teorema é mais forte do que costuma se dizer: satisfeito o critério, o sinal
contínuo pode ser **integralmente reconstruído** a partir das amostras (seção 7)
— não se perde nada por amostrar, desde que se amostre rápido o bastante.

## 4. A regra da dobra: para onde vai cada frequência

Quando o critério é violado, é útil saber exatamente onde cada frequência vai
aparecer. A regra é:

$$f_{ap} = \big|\, f - f_s \cdot \text{round}(f / f_s) \,\big|$$

ou seja: subtrai-se o múltiplo de $f_s$ mais próximo e toma-se o módulo. O
gráfico de $f_{ap}$ contra $f$ é uma **onda triangular** entre $0$ e $f_s/2$ — a
frequência real sobe sem parar, a aparente vai e volta, como uma sanfona. Daí o
nome *folding* (dobra).

Com $f_s = 10$ kHz:

| $f$ de entrada | Conta | $f_{ap}$ |
| --- | --- | --- |
| 1 kHz | dentro da banda | 1 kHz |
| 4 kHz | dentro da banda | 4 kHz |
| 6 kHz | $\lvert 6 - 10 \rvert$ | 4 kHz |
| 9 kHz | $\lvert 9 - 10 \rvert$ | 1 kHz |
| 11 kHz | $\lvert 11 - 10 \rvert$ | 1 kHz |
| 19 kHz | $\lvert 19 - 20 \rvert$ | 1 kHz |
| 21 kHz | $\lvert 21 - 20 \rvert$ | 1 kHz |

As faixas $[0, f_s/2]$, $[f_s/2, f_s]$, $[f_s, 3f_s/2]$, … são as **zonas de
Nyquist**. Todas se dobram sobre a primeira, e as zonas **pares** chegam lá com
o espectro **invertido** (uma frequência maior na entrada vira uma menor na
saída) — o que, num sinal modulado, troca o sinal da fase.

É essa a regra que o assunto 7.1 aplica às harmônicas ímpares de $f_{IF}$ e que o
assunto 7.3.1 usa para explicar o que a decimação dobra para dentro da banda.

## 5. O filtro anti-aliasing

Como nenhuma informação sobrevive à dobra, o aliasing tem de ser impedido
**antes** do ADC — e isso só pode ser feito por um filtro **analógico**. Nenhum
processamento digital resolve: no momento em que a amostra foi tomada, a
frequência alta já virou uma frequência baixa indistinguível do sinal.

Exemplo: sinal útil de 0 a 4 kHz, $f_s = 10$ kHz, e uma interferência em 7 kHz.
Sem filtro, a interferência aparece em $\lvert 7 - 10 \rvert = 3$ kHz, **dentro**
da banda útil. Com um passa-baixa analógico cortando antes de 5 kHz, ela é
atenuada enquanto ainda é 7 kHz, e nunca chega a se dobrar.

Na prática, o filtro ideal não existe: ele tem uma **banda de transição**. Isso
obriga a uma das duas escolhas:

- **folga de guarda:** amostrar acima do mínimo teórico, deixando o espaço entre
  $f_{max}$ e $f_s/2$ para o filtro descer;
- **sobreamostragem (*oversampling*):** amostrar muito acima de $2f_{max}$, usar
  um filtro analógico suave e barato, e terminar a filtragem no digital — onde um
  FIR de fase linear faz um corte que nenhum analógico faria (assuntos 7.3.1 e
  7.3.3).

A segunda é a que o LLRF usa: filtro analógico modesto, ADC rápido e o trabalho
fino dentro da FPGA.

## 6. Quantização e o ruído que ela cria

O segundo erro é independente do primeiro. O ADC tem $B$ bits, e divide a faixa
de entrada $V_{FS}$ em $2^B$ níveis de largura

$$\Delta = \frac{V_{FS}}{2^B}$$

Cada amostra é arredondada para o nível mais próximo, com erro no intervalo
$[-\Delta/2, +\Delta/2]$. Tratando esse erro como ruído uniforme, a sua potência é

$$\sigma_q^2 = \frac{\Delta^2}{12}$$

Comparando com a potência de uma senoide de fundo de escala, chega-se à relação
sinal-ruído de quantização:

$$SQNR \approx 6{,}02 \cdot B + 1{,}76 \ \text{dB}$$

**Cada bit vale ≈ 6 dB.** É a mesma conta que aparece no assunto 6 na forma
$SFDR \approx -6{,}02 \cdot B$ para os espúrios do DDS.

| $B$ | SQNR | Uso típico |
| --- | --- | --- |
| 8 bits | 49,9 dB | aquisição grosseira, osciloscópios rápidos |
| 12 bits | 74,0 dB | ADCs rápidos de uso geral |
| 14 bits | 86,0 dB | ADCs de LLRF |
| 16 bits | 98,1 dB | medida de precisão, taxas menores |

Duas ressalvas úteis: o resultado supõe o sinal ocupando a faixa inteira — um
sinal 20 dB abaixo do fundo de escala perde 20 dB de SQNR, e é por isso que
existe controle de ganho antes do ADC; e o ruído de quantização se espalha por
toda a banda $[0, f_s/2]$, de modo que **sobreamostrar e filtrar depois melhora
o SQNR**, ganhando 3 dB a cada duplicação de $f_s$.

## 7. Reconstrução: voltando ao contínuo

O teorema da amostragem promete reconstrução exata. A fórmula dessa promessa é a
**interpolação sinc**: cada amostra é substituída por uma função sinc centrada
nela e escalada pelo seu valor, e a soma de todas reproduz o sinal original.

$$x(t) = \sum_{n=-\infty}^{\infty} x[n] \cdot
\text{sinc}\!\left(\frac{t - nT}{T}\right), \qquad
\text{sinc}(u) = \frac{\sin \pi u}{\pi u}$$

Funciona porque a sinc é, na frequência, um passa-baixa ideal em $f_s/2$:
reconstruir é **apagar todas as réplicas** e deixar só a original. Só que a sinc
é infinita nos dois sentidos — o interpolador ideal não é causal e não existe.

O que um DAC real faz é o **Zero-Order Hold** (ZOH): segura cada valor até a
amostra seguinte, produzindo uma escada. A escada tem dois defeitos, ambos
visíveis na sua resposta em frequência:

$$|H_{ZOH}(f)| = \left| \frac{\sin(\pi f / f_s)}{\pi f / f_s} \right|$$

1. **Droop na banda:** a resposta cai dentro da própria banda útil, chegando a
   $2/\pi = 0{,}637$ (**−3,9 dB**) em $f_s/2$. Corrige-se com um filtro inverso,
   normalmente no digital, antes do DAC.
2. **Imagens:** a escada não elimina as réplicas, só as atenua. Sobra energia em
   torno de $f_s - f$, $f_s + f$, … que precisa de um **filtro de suavização**
   (*reconstruction* ou *smoothing filter*) analógico na saída.

É exatamente a cadeia que o assunto 1 mostra no lado do DAC, e a razão de existir
um passa-banda depois do mixer no assunto 8.

## 8. Sub-amostragem deliberada: quando o aliasing é a ferramenta

Até aqui o aliasing foi o inimigo. Mas o critério de Nyquist fala de
$f_{max}$ apenas porque supõe que o sinal ocupa tudo de $0$ a $f_{max}$. Quando o
sinal é uma **faixa estreita em torno de uma portadora alta** — o caso de todo
sistema de RF — o que importa é a **largura de banda**, não a frequência
absoluta:

| Critério | Taxa exigida para uma banda de 2 MHz em 500 MHz |
| --- | --- |
| Nyquist sobre $f_{max}$ | $> 1000$ MSps |
| Nyquist sobre a largura de banda | $> 4$ MSps |

A diferença é de mais de duas ordens de grandeza, e é por isso que ninguém
amostra RF diretamente. Amostra-se **de propósito** abaixo de $2f_{max}$, e a
banda cai dobrada numa zona de Nyquist baixa, onde a eletrônica digital funciona.

Com $f_s = 80$ MSps e uma portadora de 500 MHz:

$$f_{ap} = \big| 500 - 80 \cdot \text{round}(500/80) \big| = |500 - 480| = 20 \ \text{MHz}$$

Os 500 MHz aparecem em 20 MHz — e 20 MHz é exatamente $f_s/4$. Ou seja: **a IF de
20 MHz do assunto 1 e a regra $f_s = 4 \cdot f_{IF}$ do assunto 7.1 são a mesma
escolha de projeto**, vista de dois lugares diferentes.

O que muda nesse regime:

- o filtro anti-aliasing passa a ser **passa-banda**, não passa-baixa: ele tem de
  deixar entrar a zona de Nyquist escolhida e rejeitar todas as outras (senão o
  ruído de banda larga de todas elas se dobra para dentro da banda útil);
- a **zona** escolhida importa: zonas pares invertem o espectro (seção 4), o que
  troca o sinal da fase medida;
- o **jitter** do clock passa a ser o erro dominante. O erro de amplitude é
  $\Delta v \approx \frac{dv}{dt} \cdot \Delta t$, e $dv/dt$ cresce com a
  frequência da portadora — e não com a frequência aparente. É a conta do assunto
  1, cena 5, e é o que impede subir a portadora indefinidamente.

## Resumo

| Conceito | Fórmula | Onde reaparece |
| --- | --- | --- |
| Réplicas do espectro | $X_s(f) = f_s \sum_k X(f - k f_s)$ | 7.3 (DDC), 7.3.1 (decimador) |
| Critério de Nyquist | $f_s > 2 f_{max}$ | todos |
| Regra da dobra | $f_{ap} = \lvert f - f_s \cdot \text{round}(f/f_s) \rvert$ | 7.1 (harmônicas), 7.3.1 |
| Ruído de quantização | $SQNR \approx 6{,}02B + 1{,}76$ dB | 1 (ADC/DAC), 6 (DDS) |
| Reconstrução ideal | soma de sincs | 7.3.3 (FIR) |
| Droop do ZOH | $\lvert \text{sinc}(f/f_s) \rvert$, −3,9 dB em $f_s/2$ | 1 (DAC), 8 (up-conversion) |
| Sub-amostragem | banda em vez de $f_{max}$ | 7.1, 7.2, 7.3 |

**Animação correspondente:** [`amostragem_aliasing.py`](../../src/3%20-%20Amostragem%20e%20Aliasing/amostragem_aliasing.py), cena `AmostragemAliasing`.

Material de apoio de terceiros, em inglês, sobre o mesmo assunto:
[`aliasing.ipynb`](../../src/3%20-%20Amostragem%20e%20Aliasing/aliasing.ipynb).
