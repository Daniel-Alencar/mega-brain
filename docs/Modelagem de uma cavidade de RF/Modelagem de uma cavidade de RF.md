# Modelagem de uma cavidade de RF

A equivalência entre uma **cavidade metálica ressonante 3D** e um **circuito RLC paralelo com transformador e fontes de corrente** é um dos conceitos fundamentais da física de aceleradores e da engenharia de micro-ondas.

Para compreender como esta analogia física é construída, o circuito pode ser dividido nos seguintes blocos principais:

### Por que um circuito RLC paralelo representa a cavidade?

![image.png](Modelagem%20de%20uma%20cavidade%20de%20RF/image.png)

Fisicamente, uma cavidade de RF é um volume oco de cobre onde ondas eletromagnéticas ficam confinadas em modos de ressonância (frequentemente o modo fundamental $TM_{010}$):

- **Armazenamento de energia elétrica ($C$):** As partículas passam pelo eixo central, onde existe um campo elétrico axial oscilante ($E_z$) intenso. A energia acumulada neste campo elétrico comporta-se exatamente como a energia acumulada num condensador ($W_E = \frac{1}{2} C V_c^2$).
- **Armazenamento de energia magnética (**$L$**):** À volta do feixe e perto das paredes circula um campo magnético azimutal ($B_\theta$). A energia armazenada neste campo magnético comporta-se como a energia num indutor ($W_M = \frac{1}{2} L I_L^2$).
- **Perdas por efeito Joule (**$R$**):** As correntes superficiais de RF fluem pelas paredes de cobre da cavidade, que têm condutividade finita, dissipando potência em calor. Essa perda de energia é modelada pela resistência em paralelo $R$ (conhecida como resistência *shunt* da cavidade). Na ressonância ($\omega_0 = 1/\sqrt{LC}$), a impedância atinge o seu valor máximo e puramente resistivo, tal como numa cavidade real em sintonização perfeita.

### O que representa o transformador?

A potência de RF vinda do transmissor viaja por uma linha de transmissão ou guia de ondas com impedância característica $Z_0$ (tipicamente $50\,\Omega$). No entanto, a tensão na cavidade atinge centenas de quilovolts ou megavolts, o que significa que a cavidade apresenta uma resistência equivalente de vários megaohms ($M\Omega$).

Para introduzir a potência na cavidade, utiliza-se uma antena (acoplador capacitivo) ou uma espira/janela (acoplador indutivo). Esse elemento faz a **adaptação de impedâncias** entre a linha de $50\,\Omega$ e os megaohms da cavidade. Em teoria de circuitos de RF, esse acoplador é modelado com precisão por um **transformador ideal de razão** $1:n$, em que a razão de transformação $n$ define o fator de acoplamento $\beta = \frac{R}{n^2 Z_0}$.

### A fonte do gerador

O amplificador de potência de RF (ou klystron/estado sólido) e a linha de transmissão são modelados como um gerador real através de um **equivalente de Norton**:

- Uma fonte de corrente $I'_{rf}$ em paralelo com a sua impedância de saída característica $Z_0$.

### Por que o feixe de eletrões é uma fonte de corrente?

Esta é uma das partes mais elegantes do modelo:

- O feixe de eletrões num acelerador não passa de forma contínua, mas sim em pequenos pacotes (*bunches*) ultracurtos que se repetem periodicamente à frequência de aceleração.
- Como os eletrões viajam a velocidades próximas à velocidade da luz ($v \approx c$), a sua trajetória e corrente praticamente **não dependem da tensão instantânea da cavidade** — o feixe comporta-se como uma fonte de corrente quase ideal e "rígida" ($I_b$), que injeta corrente na cavidade e induz campos eletromagnéticos contrários (*beam loading*).

### Em resumo

Quando se analisa em torno da frequência de ressonância de interesse:

$\text{Cavidade metálica} \longrightarrow \text{Circuito ressonante } RLC \text{ paralelo}$

$\text{Acoplador/Antena de entrada} \longrightarrow \text{Transformador de impedâncias } 1:n$

$\text{Potência de RF externa} \longrightarrow \text{Fonte do gerador } I'_{rf} \text{ com impedância } Z_0$

$\text{Feixe de partículas relativistas} \longrightarrow \text{Fonte de corrente alternada } I_b$

Essa simplificação circuital permite passar das complexas Equações de Maxwell 3D para equações diferenciais lineares simples de circuitos elétricos, viabilizando o projeto de funções de transferência e controladores em malha fechada (LLRF).

# Rebater a impedância pelo transformador

Aqui ocorrem dois passos fundamentais de teoria de circuitos: **rebater a impedância pelo transformador** e **deduzir a equação diferencial** que rege a tensão $v_C(t)$.

### O que significa rebater para o secundário?

No circuito, a fonte do gerador e a impedância $Z_0$ estavam no enrolamento primário do transformador ideal de relação de espiras $1:n$.

Num transformador ideal de relação $1:n$:

- A tensão no secundário é $V_2 = n \cdot V_1$.
- A corrente no secundário é $I_2 = \frac{I_1}{n}$.
- A impedância vista a partir do secundário é:
    
    $Z'_0 = \frac{V_2}{I_2} = \frac{n V_1}{\frac{I_1}{n}} = n^2 \frac{V_1}{I_1} = n^2 Z_0$
    

Por essa razão, ao eliminar o transformador e trazer tudo para o lado da cavidade (o secundário), a impedância da linha $Z_0$ passa a valer $n^2 Z_0$, e a corrente do gerador vista no secundário passa a ser denotada por $I_{rf}$.

### Análise do Nó Principal (Lei dos Nós de Kirchhoff)

Todos os ramos estão em paralelo sob a mesma tensão $v_C(t)$:

- A corrente injetada pelo gerador de RF e pelo feixe entra no nó superior:
    
    $i_C(t) = i_{rf}(t) + i_b(t)$
    
- Essa corrente total divide-se pelos ramos passivos em paralelo:
    1. No resistor rebatedor: $i_{Z} = \frac{v_C}{n^2 Z_0}$
    2. No resistor de perdas da cavidade: $i_R = \frac{v_C}{R}$
    3. No indutor: $i_L$, onde $v_C = L \frac{d i_L}{dt} \implies i_L(t) = \frac{1}{L} \int v_C(t) \, dt$
    4. No condensador: $i_C = C \frac{d v_C}{dt}$

Pela Lei das Correntes de Kirchhoff no nó da tensão $v_C$:

$i_{total\_in} = i_{total\_out}$

$i_C = \frac{v_C}{n^2 Z_0} + \frac{v_C}{R} + \frac{1}{L}\int v_C \, dt + C \frac{dv_C}{dt}$

Juntando os termos resistivos:

$\left( \frac{1}{n^2 Z_0} + \frac{1}{R} \right) = \frac{R + n^2 Z_0}{n^2 R Z_0}$

Logo:

$C \frac{dv_C}{dt} + \left( \frac{R + n^2 Z_0}{n^2 R Z_0} \right) v_C + \frac{1}{L}\int v_C \, dt = i_C(t)$

### Obtenção da Equação Diferencial

Para eliminar o termo integral $\int v_C \, dt$, deriva-se a equação inteira em relação ao tempo $t$:

$C \frac{d^2 v_C}{dt^2} + \left( \frac{R + n^2 Z_0}{n^2 R Z_0} \right) \frac{d v_C}{dt} + \frac{1}{L} v_C = \frac{d i_C}{dt}$

Por fim, divide-se toda a equação pela capacitância $C$:

$\frac{d^2 v_C}{dt^2} + \left( \frac{n^2 Z_0 + R}{n^2 R Z_0 C} \right) \frac{dv_C}{dt} + \frac{1}{LC} v_C = \frac{1}{C}\frac{di_C}{dt}$

Usando a notação de ponto para as derivadas temporais ($\ddot{v}_C = \frac{d^2 v_C}{dt^2}$ e $\dot{v}_C = \frac{dv_C}{dt}$), obtém-se a equação diferencial de 2.ª ordem do circuito equivalente da cavidade:

$\ddot{v}_C + \left( \frac{n^2 Z_0 + R}{n^2 R Z_0 C} \right) \dot{v}_C + \frac{1}{LC} v_C = \frac{1}{C}\dot{i}_C$

# Da análise no tempo para análise em frequência

Para compreender a dedução detalhada passo a passo, analisemos novamente o circuito equivalente da cavidade, já com a impedância da linha rebatida para o secundário ($n^2 Z_0$).

### Passo 1: Aplicação da Lei dos Nós de Kirchhoff (KCL)

No circuito, todos os ramos estão em paralelo sob o mesmo nó de potencial com tensão $v_C(t)$ em relação à referência (terra).

A corrente total de excitação que entra no nó superior é:

$i_C(t) = i_{rf}(t) + i_b(t)$

Esta corrente divide-se pelos ramos passivos em paralelo:

1. **Resistência refletida da linha de transmissão (**$n^2 Z_0$**):**
    
    $i_{Z}(t) = \frac{v_C(t)}{n^2 Z_0}$
    
2. **Resistência shunt de perdas da cavidade (**$R$**):**
    
    $i_{R}(t) = \frac{v_C(t)}{R}$
    
3. **Indutor (**$L$**):**
    
    Como $v_C(t) = L \frac{d i_L(t)}{dt}$, temos que a corrente é:
    
    $i_L(t) = \frac{1}{L} \int_{-\infty}^{t} v_C(\tau) \, d\tau$
    
4. **Condensador (**$C$**):**
    
    $i_C(t) = C \frac{d v_C(t)}{dt}$
    

Pela Lei das Correntes de Kirchhoff, a corrente que entra é igual à soma das correntes que saem:

$i_C(t) = i_{Z}(t) + i_R(t) + i_L(t) + i_{cap}(t)$

Substituindo cada termo:

$i_C(t) = \frac{v_C(t)}{n^2 Z_0} + \frac{v_C(t)}{R} + \frac{1}{L} \int_{-\infty}^{t} v_C(\tau) \, d\tau + C \frac{d v_C(t)}{dt}$

### Passo 2: Simplificação dos termos resistivos

Podemos agrupar os dois termos proporcionais a $v_C(t)$:

$\left(\frac{1}{n^2 Z_0} + \frac{1}{R}\right) v_C(t) = \left( \frac{R + n^2 Z_0}{n^2 R Z_0} \right) v_C(t)$

A equação íntegro-diferencial fica:

$C \frac{d v_C(t)}{dt} + \left( \frac{n^2 Z_0 + R}{n^2 R Z_0} \right) v_C(t) + \frac{1}{L} \int_{-\infty}^{t} v_C(\tau) \, d\tau = i_C(t)$

### Passo 3: Obtenção da Equação Diferencial

Para transformar a equação numa equação puramente diferencial (eliminando o integral do indutor), deriva-se ambos os membros em relação ao tempo $t$:

$\frac{d}{dt}\left[ C \frac{d v_C(t)}{dt} + \left( \frac{n^2 Z_0 + R}{n^2 R Z_0} \right) v_C(t) + \frac{1}{L} \int_{-\infty}^{t} v_C(\tau) \, d\tau \right] = \frac{d}{dt}\big[ i_C(t) \big]$

Calculando as derivadas termo a termo:

$C \frac{d^2 v_C(t)}{dt^2} + \left( \frac{n^2 Z_0 + R}{n^2 R Z_0} \right) \frac{d v_C(t)}{dt} + \frac{1}{L} v_C(t) = \frac{d i_C(t)}{dt}$

Em seguida, divide-se toda a equação pela capacitância $C$:

$\frac{d^2 v_C(t)}{dt^2} + \left( \frac{n^2 Z_0 + R}{n^2 R Z_0 C} \right) \frac{d v_C(t)}{dt} + \frac{1}{LC} v_C(t) = \frac{1}{C} \frac{d i_C(t)}{dt}$

Adotando a notação clássica de ponto para as derivadas no tempo ($\ddot{v}_C = \frac{d^2 v_C}{dt^2}$, $\dot{v}_C = \frac{d v_C}{dt}$ e $\dot{i}_C = \frac{d i_C}{dt}$):

$\ddot{v}_C + \dot{v}_C \frac{(n^2 Z_0 + R)}{n^2 R Z_0 C} + \frac{v_C}{LC} = \frac{\dot{i}_C}{C}$

### Passo 4: Transformada de Laplace

Para encontrar a função de transferência $\frac{V_C(s)}{I_C(s)}$, aplica-se a **Transformada de Laplace** em ambos os membros da equação diferencial obtida no Passo 3, considerando condições iniciais nulas ($\mathcal{L}\{\ddot{v}_C\} = s^2 V_C(s)$, $\mathcal{L}\{\dot{v}_C\} = s V_C(s)$ e $\mathcal{L}\{\dot{i}_C\} = s I_C(s)$):

$\mathcal{L}\left\{ \ddot{v}_C + \dot{v}_C \frac{(n^2 Z_0 + R)}{n^2 R Z_0 C} + \frac{v_C}{LC} \right\} = \mathcal{L}\left\{ \frac{\dot{i}_C}{C} \right\}$

$s^2 V_C(s) + s \frac{(n^2 Z_0 + R)}{n^2 R Z_0 C} V_C(s) + \frac{1}{LC} V_C(s) = \frac{s}{C} I_C(s)$

Coloca-se $V_C(s)$ em evidência no membro esquerdo:

$V_C(s) \left[ s^2 + s \frac{(n^2 Z_0 + R)}{n^2 R Z_0 C} + \frac{1}{LC} \right] = \frac{s}{C} I_C(s)$

Isolando a razão $\frac{V_C(s)}{I_C(s)}$, obtém-se a função de transferência:

$\frac{V_C(s)}{I_C(s)} = \frac{s/C}{s^2 + s(n^2 Z_o + R)/n^2 R Z_o C + 1/LC}$

Esta expressão é a função de transferência da impedância equivalente vista pela corrente de excitação, tendo a forma canónica de um filtro passa-banda de 2.ª ordem centrado na frequência de ressonância $\omega_0 = 1/\sqrt{LC}$.

# Interpretação como um filtro de 2ª ordem

Para entender por que essa função de transferência representa exatamente um **filtro passa-banda de 2.ª ordem** centrado em $\omega_0 = 1/\sqrt{LC}$, podemos analisar o problema por dois caminhos: a **forma matemática canônica** e a **física intuitiva do circuito elétrico**.

### A Comparação com a Forma Canônica

Na teoria clássica de sistemas e processamento de sinais, a função de transferência de um **filtro passa-banda (band-pass) de 2.ª ordem** é padronizada como:

$H_{BP}(s) = \frac{K \cdot s}{s^2 + 2\zeta\omega_0 s + \omega_0^2} \quad \text{ou} \quad H_{BP}(s) = \frac{K \cdot s}{s^2 + \frac{\omega_0}{Q} s + \omega_0^2} = \frac{K \cdot s}{s^2 + 2\omega_{1/2} s + \omega_0^2}$

Onde:

- $\omega_0$ é a frequência natural não amortecida (frequência de ressonância ou central).
- $\zeta$ é o fator de amortecimento, e $Q$ é o fator de qualidade ($Q = \frac{1}{2\zeta}$).
- $2\omega_{1/2} = \frac{\omega_0}{Q}$ é a largura de banda ($\text{BW}$) do filtro.
- $s$ **no numerador** garante que existirá um zero na origem ($s = 0$).

Agora compare diretamente com a equação obtida para a cavidade:

$\frac{V_C(s)}{I_C(s)} = \frac{\frac{1}{C} \cdot s}{s^2 + \left[\frac{n^2 Z_0 + R}{n^2 R Z_0 C}\right] s + \frac{1}{LC}}$

As correspondências termo a termo são imediatas:

1. **Termo constante no denominador:**
    
    $\omega_0^2 = \frac{1}{LC} \implies \omega_0 = \frac{1}{\sqrt{LC}}$
    
2. **Termo linear em** $s$ **no denominador (amortecimento / largura de banda):**
    
    $2\omega_{1/2} = \frac{n^2 Z_0 + R}{n^2 R Z_0 C}$
    
3. **Numerador proporcional a** $s$**:**
    
    $K = \frac{1}{C}$
    

Logo, a estrutura matemática é idêntica à forma canônica de um passa-banda.

### Análise da Resposta em Frequência

Podemos avaliar o que acontece com a magnitude da impedância equivalente $Z(j\omega) = \frac{V_C(j\omega)}{I_C(j\omega)}$ em três regiões distintas:

#### A. Em frequência muito baixa

Substituindo $s = j\omega \approx 0$:

$Z(j0) \approx \frac{\frac{1}{C} (0)}{0 + 0 + \omega_0^2} = 0$

- **Fisicamente no circuito:** Em corrente contínua ($\omega = 0$), o indutor $L$ se comporta como um curto-circuito para o terra ($Z_L = j\omega L \to 0$). Toda a corrente vai para o terra através do indutor sem gerar tensão ($v_C \to 0$). **O sinal em baixa frequência é bloqueado.**

#### B. Em frequência muito alta

Dividindo o numerador e denominador por $s^2$ quando $s \to \infty$:

$\lim_{s \to \infty} \frac{s/C}{s^2} = \lim_{s \to \infty} \frac{1}{sC} = 0$

- **Fisicamente no circuito:** Em frequências infinitamente altas, o capacitor $C$ vira um curto-circuito para o terra ($Z_C = \frac{1}{j\omega C} \to 0$). Novamente, a corrente escoa para a referência sem criar queda de tensão. **O sinal em alta frequência é bloqueado.**

#### C. Na frequência de ressonância

Substituindo $s = j\omega_0$ no denominador:

$s^2 + \omega_0^2 = (j\omega_0)^2 + \omega_0^2 = -\omega_0^2 + \omega_0^2 = 0$

Os termos de 2.ª ordem e ordem zero cancelam-se perfeitamente. Sobra apenas o termo linear no meio:

$Z(j\omega_0) = \frac{j\omega_0 / C}{j\omega_0 \cdot \left[\frac{n^2 Z_0 + R}{n^2 R Z_0 C}\right]} = \frac{1}{\frac{n^2 Z_0 + R}{n^2 R Z_0}} = R \mathbin{/\mkern-1mu/} (n^2 Z_0)$

- **Fisicamente no circuito:** Na ressonância, a susceptância indutiva anula exatamente a susceptância capacitiva ($\frac{1}{j\omega_0 L} + j\omega_0 C = 0$). O indutor e o capacitor formam juntos um circuito aberto. A corrente que entra encontra apenas as resistências puras em paralelo, gerando a **máxima tensão possível**.

### Resumo

Como a resposta é:

- Nula em $\omega = 0$
- Máxima em $\omega = \omega_0 = 1/\sqrt{LC}$
- Nula quando $\omega \to \infty$

O circuito permite a passagem e o acúmulo de energia apenas em torno da vizinhança de $\omega_0$, atenuando todas as outras frequências. Por definição, trata-se de um **filtro passa-banda de 2.ª ordem**.