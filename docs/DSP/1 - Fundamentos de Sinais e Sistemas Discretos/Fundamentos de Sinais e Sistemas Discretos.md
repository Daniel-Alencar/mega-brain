# Fundamentos de Sinais e Sistemas Discretos no Tempo

Primeiro assunto da série de DSP (ver [Tópicos](../Tópicos/Tópicos.md)). Aqui se estabelece o vocabulário que todo o resto usa: o que é uma sequência, quais são os dois sinais elementares, o que caracteriza um sistema LTI e por que a resposta ao impulso $h[n]$ basta para descrever esse sistema inteiro.

### 1. Do contínuo ao discreto

Um sinal analógico $x(t)$ tem um valor para cada instante de tempo. O conversor analógico-digital (ADC) o observa apenas de tempos em tempos, a cada período $T$, produzindo uma **sequência**:

$x[n] = x(nT), \qquad f_s = \frac{1}{T}$

Duas consequências que costumam escapar na primeira leitura:

- $n$ é um **índice inteiro**, não um tempo. Escreve-se entre colchetes justamente para marcar essa diferença: $x[n]$, nunca $x(n)$.
- Entre duas amostras **não existe nada**. $x[1{,}5]$ não tem significado — não é "o valor do sinal no meio do caminho", é uma expressão malformada. Recuperar o que havia entre as amostras é o problema de reconstrução, assunto 2 da série.

A partir daqui, todo o tempo é medido em amostras, e a frequência em radianos por amostra.

### 2. Os dois sinais elementares

**Impulso unitário** (ou delta de Kronecker):

$\delta[n] = \begin{cases} 1, & n = 0 \\ 0, & n \neq 0\end{cases}$

Diferentemente do delta de Dirac do tempo contínuo, não há nada de singular aqui: é apenas o número 1 numa posição e 0 em todas as outras. É a **peça de montar** do DSP, e a seção 4 mostra por quê.

**Degrau unitário:**

$u[n] = \begin{cases} 1, & n \geq 0 \\ 0, & n < 0\end{cases}$

Os dois são o mesmo objeto visto de duas maneiras, ligados por uma diferença e por uma soma acumulada:

$\delta[n] = u[n] - u[n-1], \qquad u[n] = \sum_{k=-\infty}^{n} \delta[k]$

É o par derivada/integral do cálculo contínuo, traduzido para o discreto. Essa troca — **derivada vira diferença, integral vira soma acumulada** — reaparece no filtro CIC, cuja estrutura é literalmente um integrador seguido de um diferenciador.

### 3. Exponenciais e senoides discretas

**Exponencial real:** $x[n] = a^n$. A razão entre amostras vizinhas é constante e igual a $a$:

- $|a| < 1$: a sequência decai;
- $|a| > 1$: cresce sem limite.

Guarde essa separação: ela volta, com nome e critério formal, na seção 6.

**Exponencial complexa:** $x[n] = e^{j\omega n}$. É um fasor de módulo 1 que avança o mesmo ângulo $\omega$ a cada passo de $n$; sua parte real é $\cos(\omega n)$. Aqui moram as duas armadilhas que separam o tempo discreto do contínuo.

#### Armadilha 1 — $\omega$ é periódico

$e^{j(\omega + 2\pi)n} = e^{j\omega n} e^{j2\pi n} = e^{j\omega n}$

Duas frequências que diferem de $2\pi$ produzem **exatamente a mesma sequência de números**. Não há experimento, filtro ou algoritmo capaz de distingui-las depois de amostradas. Por isso só faz sentido falar de $\omega$ no intervalo $[-\pi, \pi]$ — e por isso o espectro de um sinal discreto é sempre periódico. Esta é a raiz matemática do *aliasing*, tratado no assunto 2.

Consequência prática: a "frequência mais alta" possível em tempo discreto é $\omega = \pi$, que corresponde a $f_s/2$ e à sequência alternada $1, -1, 1, -1, \dots$

#### Armadilha 2 — uma senoide discreta pode não ser periódica

No tempo contínuo, $\cos(\omega t)$ é periódica para qualquer $\omega$. No discreto, não:

$\cos(\omega n) \text{ é periódica em } n \iff \frac{\omega}{2\pi} \in \mathbb{Q}$

Para $\omega = 1$ rad/amostra, $\omega/2\pi \approx 0{,}159\dots$ é irracional: a sequência nunca se repete exatamente, por mais longe que se vá. É uma senoide perfeitamente bem definida e aperiódica ao mesmo tempo.

### 4. Toda sequência é uma soma de impulsos

Qualquer sequência pode ser escrita como uma combinação de impulsos deslocados e escalados:

$x[n] = \sum_{k=-\infty}^{\infty} x[k]\,\delta[n-k]$

A identidade parece trivial — cada amostra $x[k]$ é "um impulso na posição $k$ com a altura certa". Mas é a ideia mais importante de toda a teoria:

> Se o sistema é **linear**, a resposta à soma é a soma das respostas. Se também é **invariante no tempo**, a resposta ao impulso deslocado é a resposta ao impulso, deslocada. Juntando as duas, basta saber o que o sistema faz com **um único** impulso para prever o que ele fará com qualquer entrada.

Esse "o que ele faz com um impulso" é a resposta ao impulso, $h[n]$.

### 5. Linearidade e invariância no tempo

Um sistema é uma regra que transforma uma sequência em outra. Duas propriedades definem a classe que a teoria de DSP sabe resolver.

**Linearidade** (superposição e homogeneidade):

$a\,x_1[n] + b\,x_2[n] \;\longrightarrow\; a\,y_1[n] + b\,y_2[n]$

Contraexemplo: $y[n] = x^2[n]$. Entrada 1 dá saída 1; entrada 2 dá saída 4. Mas a entrada $1+2=3$ dá saída 9, e não $1+4=5$. Não é linear.

**Invariância no tempo:** atrasar a entrada apenas atrasa a saída, sem mudar sua forma.

$x[n - n_0] \;\longrightarrow\; y[n - n_0]$

Contraexemplo: $y[n] = n\,x[n]$. O ganho depende de *quando* a amostra chega; atrasar a entrada muda a forma da saída, não só a sua posição.

Quem tem as duas propriedades é um **sistema LTI**. Para essa classe — e apenas para ela — valem a convolução, a função de transferência $H(z)$ e a resposta em frequência $H(e^{j\omega})$ que ocupam os assuntos seguintes.

### 6. Causalidade e estabilidade

**Causalidade.** A saída no instante $n$ não pode depender de entradas futuras. $y[n] = x[n] + x[n-1]$ é causal; $y[n] = x[n] + x[n+1]$ não é, porque em tempo real $x[n+1]$ ainda não chegou ao pino do conversor. Para um sistema LTI, a condição é direta:

$h[n] = 0 \quad \text{para} \quad n < 0$

Filtros não causais são perfeitamente utilizáveis em processamento *offline*, sobre dados já gravados (é o que faz o `filtfilt`, obtendo fase zero). O que não existe é um sistema causal com resposta ao impulso simétrica em torno da origem — daí o atraso de grupo dos filtros de fase linear ser, literalmente, o preço da causalidade.

**Estabilidade BIBO** (*Bounded Input, Bounded Output*). Toda entrada limitada deve produzir saída limitada. Para um sistema LTI, o critério é a somabilidade absoluta da resposta ao impulso:

$\sum_{n=-\infty}^{\infty} |h[n]| < \infty$

Exemplos: $h[n] = 0{,}8^n u[n]$ soma 5 e é estável; $h[n] = 1{,}25^n u[n]$ diverge e é instável. É o mesmo $|a| < 1$ da seção 3, agora com nome e critério — e, no assunto 3, com interpretação geométrica: polos dentro do círculo unitário.

### 7. A convolução

Com a decomposição da seção 4 e as propriedades da seção 5, a saída de um sistema LTI para qualquer entrada é:

$y[n] = \sum_{k=-\infty}^{\infty} x[k]\,h[n-k] = x[n] * h[n]$

A receita prática tem três passos — **inverter, deslizar e somar os produtos**:

1. inverter $h[k]$ no eixo, obtendo $h[-k]$;
2. deslocá-la de $n$ posições;
3. multiplicar ponto a ponto por $x[k]$ e somar tudo.

Exemplo com $x = \{1, 2, 3\}$ e $h = \{1, 1, 1\}$ (uma média móvel não normalizada):

| $n$ | conta | $y[n]$ |
|---|---|---|
| 0 | $1\cdot1$ | 1 |
| 1 | $1\cdot1 + 2\cdot1$ | 3 |
| 2 | $1\cdot1 + 2\cdot1 + 3\cdot1$ | 6 |
| 3 | $2\cdot1 + 3\cdot1$ | 5 |
| 4 | $3\cdot1$ | 3 |

Duas observações que valem para sempre:

- o comprimento da saída é $N + M - 1$: convoluir 3 amostras com 3 amostras dá 5. O filtro **espalha** cada amostra de entrada;
- a convolução é comutativa, associativa e distributiva — propriedades que justificam trocar a ordem de filtros em cascata sem alterar o resultado.

### 8. Equações às diferenças (LCCDE)

Na prática, raramente se implementa um sistema a partir de $h[n]$. Implementa-se uma **receita de cálculo** — uma equação às diferenças linear com coeficientes constantes:

$y[n] = \sum_{k=0}^{M} b_k\,x[n-k] \;-\; \sum_{k=1}^{N} a_k\,y[n-k]$

- os coeficientes $b_k$ pesam entradas atuais e passadas;
- os coeficientes $a_k$ pesam **saídas passadas** — isto é, realimentação.

A presença ou não dos $a_k$ divide o mundo dos filtros digitais em dois:

| | FIR | IIR |
|---|---|---|
| realimentação | não | sim |
| resposta ao impulso | finita, $N$ amostras | infinita |
| exemplo | $y[n] = \tfrac{1}{4}\sum_{k=0}^{3} x[n-k]$ | $y[n] = 0{,}8\,y[n-1] + x[n]$ |
| $h[n]$ | $\{\tfrac14,\tfrac14,\tfrac14,\tfrac14\}$ | $0{,}8^n u[n]$, nunca zera |
| estabilidade | sempre estável | depende dos $a_k$ |
| fase linear | possível (coeficientes simétricos) | impossível (exceto casos triviais) |

A realimentação entrega muita seletividade com pouca conta — e é exatamente por isso que pode instabilizar: trocar $0{,}8$ por $1{,}2$ no exemplo faz $h[n]$ explodir, violando o critério BIBO da seção 6.

---

**A seguir:** assunto 2 da série, *Teoria de Amostragem e Reconstrução*, onde a armadilha 1 da seção 3 vira o teorema de Nyquist-Shannon e o fenômeno de aliasing.

**Animação correspondente:** [`fundamentos_sinais_discretos.py`](../../../src/DSP/1%20-%20Fundamentos%20de%20Sinais%20e%20Sistemas%20Discretos/fundamentos_sinais_discretos.py), cena `FundamentosSinaisDiscretos`.
