# Filtro FIR

Um **Filtro FIR** (do inglês *Finite Impulse Response*, ou **Filtro de Resposta ao Impulso Finita**) é um tipo fundamental de filtro digital amplamente utilizado em Processamento Digital de Sinais (DSP).

A função de qualquer filtro é permitir a passagem de certas frequências em um sinal digital enquanto bloqueia ou atenua outras (como um filtro passa-baixa, passa-alta ou passa-banda). O termo "Finito" refere-se ao fato de que, se você aplicar um único pulso (um impulso) na entrada do filtro, a resposta na saída vai durar apenas um número específico de amostras antes de zerar completamente.

Aqui estão os conceitos essenciais para entender como ele funciona:

### 1. Como funciona a matemática

Um filtro FIR opera pegando uma amostra de entrada atual e uma quantidade definida de amostras de entrada anteriores, multiplicando cada uma por um peso específico (chamado de coeficiente) e somando tudo.

A equação de diferença linear que define um filtro FIR é:

$y[n] = \sum_{k=0}^{N-1} h[k] \cdot x[n-k]$

Onde:

- $y[n]$ é o sinal de saída no tempo $n$.
- $x[n]$ é o sinal de entrada atual, e $x[n-k]$ são as amostras passadas.
- $h[k]$ são os coeficientes do filtro (que determinam o comportamento do filtro, como as frequências de corte).
- $N$ é o número total de coeficientes (também chamado de número de *taps* ou o "tamanho" do filtro). A ordem do filtro é $N-1$.

### 2. Estrutura e Implementação

A arquitetura clássica de um filtro FIR é frequentemente descrita como uma linha de atraso com derivações (*tapped delay line*). Na prática, ela é construída por três elementos básicos:

- **Atrasos ($z^{-1}$):** Memorizam as amostras de entrada anteriores.
- **Multiplicadores:** Multiplicam cada amostra atrasada pelo seu respectivo coeficiente ($h[k]$).
- **Somadores:** Somam todos os resultados das multiplicações para gerar a saída final $y[n]$.

Como o sinal flui apenas para a frente, da entrada para a saída, o filtro FIR **não possui malha de realimentação** (feedback).

### 3. Vantagens do Filtro FIR

- **Estabilidade Inerente:** Como não há realimentação usando amostras de saída passadas (o que define os filtros IIR - *Infinite Impulse Response*), um filtro FIR nunca se tornará instável ou entrará em oscilação descontrolada.
- **Fase Linear:** Esta é a maior vantagem dos filtros FIR. Eles podem ser projetados para ter uma resposta de fase perfeitamente linear, o que significa que o filtro atrasa todas as frequências na mesma proporção de tempo. Isso garante que a "forma" do sinal não seja distorcida ao passar pelo filtro (crucial em comunicações de dados e áudio).
- **Simplicidade de Implementação:** A estrutura de multiplicações e somas é extremamente amigável para implementação em hardware (como FPGAs e ASICs) e processadores DSP.

### 4. Desvantagens

- **Custo Computacional:** Para atingir transições de corte muito abruptas (por exemplo, um filtro passa-baixa que corta frequências indesejadas de forma muito drástica), um filtro FIR requer uma ordem $N$ muito alta. Isso significa que ele precisa de muitos multiplicadores, somadores e memória em comparação com um filtro IIR equivalente.

### O que o Filtro FIR faz exatamente com o sinal?

Na prática, o filtro FIR atua como uma **"janela móvel" que faz uma média ponderada** das últimas amostras que chegaram.

Imagine que você está lendo os dados de um acelerômetro para calcular a inclinação de um sistema (como no controle de atitude de um robô ou drone). O motor vibra muito, então o sinal original chega cheio de "espinhos" (ruído de alta frequência).

1. **Ação no Tempo:** A cada instante (a cada ciclo de *clock*), o filtro pega o valor atual do sensor e, digamos, os últimos 9 valores (se $N=10$). Ele multiplica cada um desses valores por um "peso" (os coeficientes) e soma tudo. O resultado dessa soma é o novo ponto do sinal de saída.
2. **O Resultado:** Aqueles picos rápidos e bruscos da vibração do motor são suavizados, porque eles se diluem na média das amostras. O que sobra é apenas a variação lenta do sinal, que é o movimento real de inclinação que você quer medir.
3. **Na Prática de Hardware:** Se você estiver descrevendo isso em Verilog ou VHDL, um filtro FIR se traduz em algo muito visual: uma fila de registradores (*shift registers*) empurrando os dados a cada *clock*, ligados a vários blocos de multiplicação e um grande somador final (blocos MAC). Ele mastiga os dados em paralelo.

### A Diferença: FIR vs. IIR (Os "Outros" Filtros)

No mundo digital, existem basicamente duas grandes famílias de filtros: os **FIR** e os **IIR** (*Infinite Impulse Response*). A diferença fundamental entre eles se resume a uma palavra: **Realimentação (Feedback)**.

Enquanto o FIR calcula a saída olhando **apenas para as entradas** (passadas e presente), o filtro IIR calcula a saída olhando para as entradas E para as **saídas anteriores**. É como se o IIR pegasse o resultado que ele acabou de calcular e jogasse de volta na própria equação.

Aqui está um comparativo direto:

| **Característica** | **Filtro FIR (Resposta Finita)** | **Filtro IIR (Resposta Infinita)** |
| --- | --- | --- |
| **Realimentação** | **Não possui.** Usa apenas os dados que chegam da entrada. | **Possui.** Usa dados da entrada e os próprios resultados de saída. |
| **Estabilidade** | **Sempre estável.** Como não há realimentação, o sinal nunca vai "explodir" para o infinito, não importa o que aconteça. | **Pode ser instável.** Se os coeficientes forem mal calculados, a realimentação pode fazer o sinal oscilar fora de controle. |
| **Fase** | **Linear.** Ele atrasa todas as frequências pelo mesmo tempo. O formato da onda original (seja ela quadrada, triangular) não se deforma. | **Não-Linear.** Ele pode atrasar frequências graves e agudas em tempos diferentes, o que pode distorcer completamente o formato do sinal no tempo. |
| **Custo Computacional** | **Alto.** Para fazer um corte de frequência muito agressivo, você precisa de um $N$ (número de *taps*) muito grande. Isso consome muitos multiplicadores na FPGA ou ciclos no processador. | **Baixo.** Com uma ordem muito pequena (pouca matemática), ele consegue fazer cortes de frequência muito abruptos. |

![image.png](Filtro%20FIR/image.png)

![image.png](Filtro%20FIR/image%201.png)