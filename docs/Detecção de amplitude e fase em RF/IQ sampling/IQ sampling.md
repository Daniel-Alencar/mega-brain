# IQ sampling

Como extrair a amplitude $A$ e a fase $\varphi_0$ de um sinal senoidal de radiofrequência (RF) ou de frequência intermediária (IF) utilizando um único conversor analógico-digital (ADC) e processamento digital.

### 1. Representação Polar vs. Cartesiana (I/Q)

Qualquer sinal senoidal de RF pode ser representado por:

$y(t) = A \cdot \sin(\omega t + \varphi_0)$

Expandindo pela identidade trigonométrica da soma de arcos ($\sin(\alpha+\beta) = \sin\alpha\cos\beta + \cos\alpha\sin\beta$):

$y(t) = \underbrace{A \cos\varphi_0}_{I} \sin(\omega t) + \underbrace{A \sin\varphi_0}_{Q} \cos(\omega t) = I \sin(\omega t) + Q \cos(\omega t)$

- $I$ **(In-phase):** componente em fase ($I = A \cos\varphi_0$).
- $Q$ **(Quadrature):** componente em quadratura ($Q = A \sin\varphi_0$).

A conversão inversa (de cartesiano para polar) é dada por:

$A = \sqrt{I^2 + Q^2}, \qquad \varphi_0 = \text{atan}\left(\frac{Q}{I}\right)$

> **Por que usar** $I$ **e** $Q$**?** No meio digital, calcular raízes quadradas e arcos-tangentes a cada ciclo de amostragem consome muitos recursos de hardware e introduz latência. Em contrapartida, algoritmos de controle (como o PI) e rotações de fase operam de forma direta e linear sobre as coordenadas cartesianas $I$ e $Q$.
> 

### 2. O Desafio da Amostragem por ADC

Um conversor ADC mede apenas uma grandeza escalar instantânea por vez (a projeção vertical da tensão do fasor no tempo). Para reconstruir o vetor bidimensional completo $(I, Q)$, é necessário correlacionar amostras consecutivas no tempo.

### 3. Amostragem Síncrona Clássica

O caso padrão de *IQ sampling* ocorre quando a frequência de amostragem do ADC ($f_s$) é exatamente quatro vezes a frequência do sinal de entrada ($f_{IF}$):

$f_s = 4 \cdot f_{IF}$

Nesta condição, o avanço de fase entre duas amostras consecutivas é precisamente de um quarto de ciclo ($90^\circ$ ou $\pi/2\text{ rad}$):

$\Delta\phi = \omega \cdot T_s = 2\pi f_{IF} \cdot \frac{1}{4 f_{IF}} = \frac{\pi}{2} = 90^\circ$ 

Avaliando $y(t) = I \sin(\omega t) + Q \cos(\omega t)$ em quatro instantes sucessivos ($t_0, t_1, t_2, t_3$):

- Em $\omega t_0 = 0$: $y(t_0) = I \sin(0) + Q \cos(0) = \mathbf{Q}$
- Em $\omega t_1 = \pi/2$: $y(t_1) = I \sin(\pi/2) + Q \cos(\pi/2) = \mathbf{I}$
- Em $\omega t_2 = \pi$: $y(t_2) = I \sin(\pi) + Q \cos(\pi) = \mathbf{-Q}$
- Em $\omega t_3 = 3\pi/2$: $y(t_3) = I \sin(3\pi/2) + Q \cos(3\pi/2) = \mathbf{-I}$

A sequência de dados que sai do ADC segue o padrão cíclico:

$Q,\quad I,\quad -Q,\quad -I,\quad Q,\quad I,\quad \dots$

#### Os quatro vetores $(y_{i+1},\, y_i)$

Como o ADC entrega **um número por vez**, o algoritmo monta o plano cartesiano agrupando duas amostras consecutivas no vetor $\begin{pmatrix} y_{i+1} \\ y_i \end{pmatrix}$ — a abscissa é a amostra mais nova, a ordenada é a anterior. Avaliando nos quatro instantes:

| instante | par $(y_{i+1},\, y_i)$ | ângulo |
|---|---|---|
| $t_0$ | $(I,\ Q)$ | $\varphi_0$ |
| $t_1$ | $(-Q,\ I)$ | $\varphi_0 + 90^\circ$ |
| $t_2$ | $(-I,\ -Q)$ | $\varphi_0 + 180^\circ$ |
| $t_3$ | $(Q,\ -I)$ | $\varphi_0 + 270^\circ$ |

São quatro vetores de mesmo comprimento, separados por exatamente $90^\circ$ — é a figura clássica do IQ sampling.

> **A armadilha da notação.** As letras dentro do vetor **não** indicam o nome do eixo onde a ponta se encontra: indicam os **comprimentos medidos em $t_0$**, já girados para os novos eixos. Em $t_1$ a ponta está à esquerda e acima; a projeção horizontal vale $-Q$ e a vertical vale $I$. Daí o rótulo $(-Q,\, I)$.
>
> É comum escrever $(-I,\, Q)$ por engano. Mas girar $90^\circ$ no sentido anti-horário leva
>
> $(x,\, y) \;\longrightarrow\; (-y,\; x)$
>
> ou seja, $(I,\, Q) \to (-Q,\, I)$. Trocar o sinal de uma coordenada só seria um **espelhamento**, não uma rotação.

Com $A = 1$ e $\varphi_0 = 30^\circ$ ($I = 0{,}866$, $Q = 0{,}5$), os quatro pares ficam em $(0{,}866;\ 0{,}5)$, $(-0{,}5;\ 0{,}866)$, $(-0{,}866;\ -0{,}5)$ e $(0{,}5;\ -0{,}866)$ — ângulos de 30°, 120°, 210° e 300°.

#### O Algoritmo de Rotação

Como o fasor gira $90^\circ$ a cada amostra, para comparar duas amostras consecutivas e recuperar o vetor original fixo, aplica-se uma matriz de rotação inversa por passos de $\Delta\phi_i \in \{0^\circ, -90^\circ, -180^\circ, -270^\circ\}$:

$\begin{pmatrix} I \\ Q \end{pmatrix}_{t_i} = \begin{pmatrix} \cos\Delta\phi_i & -\sin\Delta\phi_i \\ \sin\Delta\phi_i & \cos\Delta\phi_i \end{pmatrix} \begin{pmatrix} y_{i+1} \\ y_i \end{pmatrix}$

Como os elementos dessa matriz são apenas **0**, **1** e **-1**, o hardware digital não necessita de multiplicadores complexos nem tabelas trigonométricas: a extração de $I$ e $Q$ resume-se a selecionar os dados e alternar o sinal algébrico. Este processo atua como um filtro FIR de 1.ª ordem.

O algoritmo roda à taxa de amostragem $f_s$ e repousa sobre uma hipótese explícita: **a amplitude e a fase do sinal não mudam substancialmente entre duas amostras consecutivas**. Se mudarem, $y_i$ e $y_{i+1}$ deixam de pertencer ao mesmo estado do fasor e a extração de $I$ e $Q$ fica corrompida. Não se exige que o sinal seja uma senoide pura — exige-se que a sua modulação seja lenta comparada a $f_s$.

### 4. Para que serve o número: duas leituras do mesmo cálculo

O algoritmo devolve $(I, Q)$ a cada amostra, e a fase sai de $\varphi_0 = \operatorname{atan}(Q/I)$. O que se faz com esse ângulo depende da aplicação — e os dois usos abaixo utilizam exatamente o mesmo hardware.

#### a) Malha de controle: a variação de fase é um erro

Em LLRF, a fase do campo deve ficar parada. Suponha um estado de referência com $I = 1$ e $Q = 1$:

$\varphi_0 = \operatorname{atan}(1/1) = 45^\circ, \qquad A = \sqrt{1^2 + 1^2} = 1{,}414$

Enquanto nada muda, qualquer janela de duas amostras devolve os mesmos $45^\circ$ — o fluxo do ADC é $1,\ 1,\ -1,\ -1,\ \dots$ e a rotação inversa recupera o vetor original a cada passo.

Agora suponha que uma instabilidade atrase a fase do sinal em $10^\circ$, levando $\varphi_0$ a $35^\circ$. As amostras passam a ser

$Q = 1{,}414 \sin 35^\circ = 0{,}81, \qquad I = 1{,}414 \cos 35^\circ = 1{,}16$

O algoritmo não sabe disso: ele continua desfazendo rigidamente $90^\circ$ por passo. O que sai é

$\operatorname{atan}(0{,}81 / 1{,}16) = 35^\circ$

A amplitude permanece $\sqrt{0{,}81^2 + 1{,}16^2} = 1{,}41$: no plano I/Q o ponto **deslizou sobre o círculo**, assinatura de uma perturbação puramente de fase. O controlador compara com a referência,

$\Delta\varphi = 45^\circ - 35^\circ = 10^\circ$

e aciona a correção. (Durante o próprio salto, o par de amostras que atravessa a descontinuidade produz uma leitura intermediária — é a hipótese de estabilidade mostrando o seu limite.)

#### b) Comunicação: a variação de fase é a mensagem

Quando a fase carrega informação, o processo físico e a matemática são **idênticos**; muda apenas o destino do número. Em vez de alimentar um PI que anula o desvio, o ângulo é traduzido em bits.

Num esquema de modulação por fase com amplitude constante (QPSK), o transmissor associa pares de bits a ângulos:

| ângulo | $(I, Q)$ | bits |
|---|---|---|
| $45^\circ$ | $(+1{,}00;\ +1{,}00)$ | `00` |
| $135^\circ$ | $(-1{,}00;\ +1{,}00)$ | `01` |
| $225^\circ$ | $(-1{,}00;\ -1{,}00)$ | `11` |
| $315^\circ$ | $(+1{,}00;\ -1{,}00)$ | `10` |

O receptor amostra, aplica a mesma rotação inversa, calcula $\operatorname{atan}(Q/I)$ e decide qual dos quatro pontos da **constelação** foi transmitido. O salto angular não é tratado como falha: ele **é** o fluxo de dados.

A hipótese de estabilidade continua valendo e vira uma especificação de projeto: cada símbolo precisa durar muitas amostras, ou seja, a taxa de símbolos deve ser bem menor que $f_s$.

### 5. Generalização para Múltiplos Inteiros

Caso a razão seja outro número inteiro $m$ (com passo angular $\Delta\phi = \frac{2\pi}{m}$), duas amostras consecutivas $y_n$ e $y_{n+1}$ formam um sistema linear bidimensional:

$\begin{pmatrix} I \\ Q \end{pmatrix} = \frac{1}{\sin\Delta\phi} \begin{pmatrix} \cos(\phi + n\Delta\phi) & -\cos(\phi + (n+1)\Delta\phi) \\ -\sin(\phi + n\Delta\phi) & \sin(\phi + (n+1)\Delta\phi) \end{pmatrix} \begin{pmatrix} y_{n+1} \\ y_n \end{pmatrix}$

Caso $\Delta\phi$ se afaste substancialmente de $90^\circ$ ou $270^\circ$, o termo $\sin\Delta\phi$ no denominador torna-se pequeno, fazendo com que a estimativa de $I$ e $Q$ fique muito sensível a ruído e erros de amostragem.

### 6. Limitações e Fontes de Erro do *IQ Sampling* Clássico

Apesar da simplicidade e da baixíssima latência (ideais para malhas de realimentação rápida), o método tradicional com $\Delta\phi = 90^\circ$ apresenta vulnerabilidades espectrais:

- **Offset DC e Erro de Fase:** Desvios de tensão contínua na entrada do ADC ou desvios angulares em relação aos $90^\circ$ nominais modulam as amostras, manifestando-se diretamente como uma ondulação (*ripple*) indesejada na frequência $f_{IF}$.
- **Aliasing de Harmônicos:**
    - Não linearidades de misturadores analógicos e ADCs geram harmônicos de $f_{IF}$.
    - Com $f_s = 4 f_{IF}$, a frequência de Nyquist fica em $2 f_{IF}$.
    - O 2.º harmônico dobra sobre a frequência de Nyquist, enquanto o **3.º harmônico sofre aliasing e cai exatamente em cima da frequência fundamental** $f_{IF}$.
    - Em geral, todos os harmônicos ímpares caem sobre a portadora, tornando-se indistinguíveis do sinal real e gerando distorções de medição que não podem ser eliminadas por filtragem linear subsequente.

É justamente para superar essas limitações de harmônicos que existem as técnicas de **Non-IQ sampling** (onde a razão $f_s/f_{IF} = N/M$ distribui os harmônicos em outras partes do espectro) e de **Digital Down Conversion (DDC)**.

---

**Animação correspondente:** [`iq_sampling.py`](../../../src/Detecção%20de%20amplitude%20e%20fase%20em%20RF/IQ%20sampling/iq_sampling.py), cena `IQSampling`.
