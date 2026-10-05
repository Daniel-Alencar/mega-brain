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

Avaliando a Equação em quatro instantes sucessivos ($t_0, t_1, t_2, t_3$):

- Em $\omega t_0 = 0$: $y(t_0) = I \sin(0) + Q \cos(0) = \mathbf{Q}$
- Em $\omega t_1 = \pi/2$: $y(t_1) = I \sin(\pi/2) + Q \cos(\pi/2) = \mathbf{I}$
- Em $\omega t_2 = \pi$: $y(t_2) = I \sin(\pi) + Q \cos(\pi) = \mathbf{-Q}$
- Em $\omega t_3 = 3\pi/2$: $y(t_3) = I \sin(3\pi/2) + Q \cos(3\pi/2) = \mathbf{-I}$

A sequência de dados que sai do ADC segue o padrão cíclico:

$Q,\quad I,\quad -Q,\quad -I,\quad Q,\quad I,\quad \dots$

#### O Algoritmo de Rotação

Como o fasor gira $90^\circ$ a cada amostra, para comparar duas amostras consecutivas e recuperar o vetor original fixo, aplica-se uma matriz de rotação inversa por passos de $\Delta\phi_i \in \{0^\circ, -90^\circ, -180^\circ, -270^\circ\}$:

$\begin{pmatrix} I \\ Q \end{pmatrix}_{t_i} = \begin{pmatrix} \cos\Delta\phi_i & -\sin\Delta\phi_i \\ \sin\Delta\phi_i & \cos\Delta\phi_i \end{pmatrix} \begin{pmatrix} y_{i+1} \\ y_i \end{pmatrix}$

Como os elementos dessa matriz são apenas **0**, **1** e **-1**, o hardware digital não necessita de multiplicadores complexos nem tabelas trigonométricas: a extração de $I$ e $Q$ resume-se a selecionar os dados e alternar o sinal algébrico. Este processo atua como um filtro FIR de 1.ª ordem.

### 4. Generalização para Múltiplos Inteiros

Caso a razão seja outro número inteiro $m$ (com passo angular $\Delta\phi = \frac{2\pi}{m}$), duas amostras consecutivas $y_n$ e $y_{n+1}$ formam um sistema linear bidimensional:

$\begin{pmatrix} I \\ Q \end{pmatrix} = \frac{1}{\sin\Delta\phi} \begin{pmatrix} \cos(\phi + n\Delta\phi) & -\cos(\phi + (n+1)\Delta\phi) \\ -\sin(\phi + n\Delta\phi) & \sin(\phi + (n+1)\Delta\phi) \end{pmatrix} \begin{pmatrix} y_{n+1} \\ y_n \end{pmatrix}$

O autor destaca que, caso $\Delta\phi$ se afaste substancialmente de $90^\circ$ ou $270^\circ$, o termo $\sin\Delta\phi$ no denominador torna-se pequeno, fazendo com que a estimativa de $I$ e $Q$ fique muito sensível a ruído e erros de amostragem.

### 5. Limitações e Fontes de Erro do *IQ Sampling* Clássico

Apesar da simplicidade e da baixíssima latência (ideais para malhas de realimentação rápida), o método tradicional com $\Delta\phi = 90^\circ$ apresenta vulnerabilidades espectrais:

- **Offset DC e Erro de Fase:** Desvios de tensão contínua na entrada do ADC ou desvios angulares em relação aos $90^\circ$ nominais modulam as amostras, manifestando-se diretamente como uma ondulação (*ripple*) indesejada na frequência $f_{IF}$.
- **Aliasing de Harmônicos:**
    - Não linearidades de misturadores analógicos e ADCs geram harmônicos de $f_{IF}$.
    - Com $f_s = 4 f_{IF}$, a frequência de Nyquist fica em $2 f_{IF}$.
    - O 2.º harmônico dobra sobre a frequência de Nyquist, enquanto o **3.º harmônico sofre aliasing e cai exatamente em cima da frequência fundamental** $f_{IF}$.
    - Em geral, todos os harmônicos ímpares caem sobre a portadora, tornando-se indistinguíveis do sinal real e gerando distorções de medição que não podem ser eliminadas por filtragem linear subsequente.

É justamente para superar essas limitações de harmônicos que o artigo introduz a seguir o **Non-IQ sampling** (onde a razão $f_s/f_{IF} = N/M$ distribui os harmônicos em outras partes do espectro) e o **Digital Down Conversion - DDC**.