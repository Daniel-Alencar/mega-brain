# Filtros

# Ordem de filtros

A **ordem de um filtro** é definida, matematicamente, pelo **grau do polinômio do denominador** da sua função de transferência $H(s)$ (o que equivale ao número de polos do sistema ou à ordem da equação diferencial que rege o circuito).

Fisicamente, em circuitos elétricos passivos concentrados, a ordem corresponde ao **número de elementos armazenadores de energia independentes** (capacitores e indutores).

### Filtro de 1.ª Ordem

- **Matemática:** O denominador tem $s^1$ como maior potência:
    
    $H(s) = \frac{N(s)}{a_1 s + a_0}$
    
- **Polos:** Possui exatamente **1 polo**.
- **Elementos físicos:** Utiliza apenas **1 elemento reativo** independente (circuito $RC$ ou $RL$).
- **Taxa de atenuação (Roll-off):** Na região de corte, a atenuação do sinal decai a uma taxa de $20\text{ dB/década}$ (ou $6\text{ dB/oitava}$).
- **Comportamento dinâmico:** Não apresenta ressonância nem oscilações intrínsecas (não há troca de energia entre dois armazenadores diferentes); a resposta ao degrau é sempre puramente exponencial e suave.
- **Tipos possíveis:** Apenas passa-baixas e passa-altas simples.

### Filtro de 2.ª Ordem

- **Matemática:** O denominador tem $s^2$ como maior potência:
    
    $H(s) = \frac{N(s)}{b_2 s^2 + b_1 s + b_0}$
    
- **Polos:** Possui **2 polos** (que podem ser reais ou um par de complexos conjugados).
- **Elementos físicos:** Utiliza **2 elementos reativos** de naturezas distintas ou independentes (por exemplo, um indutor $L$ e um capacitor $C$, como no circuito $RLC$).
- **Taxa de atenuação (Roll-off):** A atenuação nas bandas de rejeição é o dobro da primeira ordem, caindo a $40\text{ dB/década}$ (ou $12\text{ dB/oitava}$).
- **Comportamento dinâmico:** Como há transferência mútua de energia entre o campo elétrico ($C$) e o campo magnético ($L$), o sistema pode apresentar **ressonância**, sobressinais (*overshoot*) e comportamento oscilatório dependendo do fator de amortecimento ($\zeta$) ou fator de qualidade ($Q$). **Tipos possíveis:** Passa-baixas, passa-altas, passa-banda e rejeita-banda (*notch*).

# Filtro de 1ª ordem

## Características gerais

Nos filtros de 1.ª ordem, a função de transferência é governada por um polinômio no denominador onde $s^1$ é a maior potência, assumindo a forma matemática $H(s)=\frac{N(s)}{a_1 s+a_0}$.

- **Elementos físicos e Polos:** O circuito possui exatamente um polo e requer apenas um elemento reativo independente para armazenar energia, originando as topologias clássicas RC ou RL.
- **Comportamento dinâmico:** Por não existirem dois elementos de naturezas distintas para trocar energia entre si, o sistema é incapaz de entrar em ressonância. A sua resposta temporal a um degrau é sempre puramente exponencial e suave, sem qualquer ocorrência de sobressinais (*overshoot*).
- **Taxa de atenuação (*Roll-off*):** Na banda de rejeição, a capacidade de atenuar o sinal decai a uma taxa fixa de $20\text{ dB/década}$ (o equivalente a $6\text{ dB/oitava}$).

## Passa-baixo e passa-alto

O que define se o filtro de 1.ª ordem atua como passa-baixo ou passa-alto é exclusivamente o polinómio do numerador $N(s)$. Adotando $\omega_c$ como a frequência de corte angular do circuito (onde $\omega_c = \frac{1}{RC}$ num circuito RC, ou $\omega_c = \frac{R}{L}$ num circuito RL), as equações assumem as seguintes formas canónicas:

#### 1. Filtro Passa-Baixo de 1.ª Ordem (*Low-Pass*)

A função de transferência possui apenas um ganho constante no numerador, sem qualquer zero (variável $s$):

$H_{LP}(s) = \frac{K \cdot \omega_c}{s + \omega_c}$

- **Comportamento em baixa frequência (**$s = j\omega \to 0$**):**
    
    $H_{LP}(0) = \frac{K \cdot \omega_c}{\omega_c} = K$
    
    O sinal contínuo (DC) e as baixas frequências passam pelo filtro com o ganho intacto.
    
- **Comportamento em alta frequência (**$s = j\omega \to \infty$**):**
    
    À medida que $s$ cresce no denominador, a fração tende para zero:
    
    $\lim_{\omega \to \infty} \vert{}H_{LP}(j\omega)\vert{} = 0$
    
    Os sinais de alta frequência são progressivamente bloqueados.
    
- **Exemplo físico clássico:** A tensão medida aos terminais de um condensador num circuito RC série.

#### 2. Filtro Passa-Alto de 1.ª Ordem (*High-Pass*)

A função de transferência possui a variável $s$ no numerador, o que introduz um zero na origem ($s = 0$):

$H_{HP}(s) = \frac{K \cdot s}{s + \omega_c}$

- **Comportamento em baixa frequência (**$s = j\omega \to 0$**):**
    
    Devido ao zero no numerador, quando a frequência é nula:
    
    $H_{HP}(0) = 0$
    
    O filtro bloqueia totalmente os sinais de corrente contínua (DC).
    
- **Comportamento em alta frequência (**$s = j\omega \to \infty$**):**
    
    A variável $s$ domina tanto o numerador como o denominador, anulando o efeito da constante $\omega_c$:
    
    $\lim_{\omega \to \infty} H_{HP}(j\omega) = K$
    
    As altas frequências atravessam o filtro livremente.
    
- **Exemplo físico clássico:** A tensão medida aos terminais da resistência num circuito RC série.

# Filtro de 2ª ordem

## Características gerais

Em filtros de 2.ª ordem, o **denominador é sempre idêntico** — ele define os polos, a frequência natural de corte/ressonância ($\omega_0$) e o amortecimento:

$D(s) = s^2 + \frac{\omega_0}{Q}s + \omega_0^2 \quad \text{ou} \quad D(s) = s^2 + 2\zeta\omega_0 s + \omega_0^2$

O que determina se o filtro é **passa-baixa**, **passa-alta** ou **passa-banda** é exclusivamente a potência da variável $s$ no **numerador** (ou seja, a posição dos zeros no plano complexo).

### 1. Filtro Passa-Baixa de 2.ª Ordem (Low-Pass)

A equação canônica tem apenas uma **constante no numerador** (nenhum zero em $s$):

$H_{LP}(s) = \frac{K \cdot \omega_0^2}{s^2 + \frac{\omega_0}{Q}s + \omega_0^2}$

- **Comportamento em baixa frequência (**$s = j\omega \to 0$**):**
    
    $H_{LP}(0) = \frac{K \cdot \omega_0^2}{\omega_0^2} = K \quad (\text{ganho DC constante, o sinal passa sem atenuação})$
    
- **Comportamento em alta frequência (**$s = j\omega \to \infty$**):**
    
    O termo $s^2$ no denominador cresce muito mais rápido que o numerador constante:
    
    $\lim_{\omega \to \infty} \vert{}H_{LP}(j\omega)\vert{} \to 0$
    
- **Taxa de queda (Roll-off):** Cai a $-40\text{ dB/década}$ para frequências bem acima de $\omega_0$.
- **Exemplo físico clássico:** A tensão sobre o capacitor em um circuito série $RLC$.

### 2. Filtro Passa-Alta de 2.ª Ordem (High-Pass)

A equação canônica tem um termo em $s^2$ **no numerador** (dois zeros na origem, em $s = 0$):

$H_{HP}(s) = \frac{K \cdot s^2}{s^2 + \frac{\omega_0}{Q}s + \omega_0^2}$

- **Comportamento em baixa frequência (**$s = j\omega \to 0$**):**
    
    Como o numerador é $s^2$, quando $\omega = 0$:
    
    $H_{HP}(0) = 0 \quad (\text{bloqueia totalmente DC})$
    
- **Comportamento em alta frequência (**$s = j\omega \to \infty$**):**
    
    Para frequências muito altas, o termo $s^2$ domina tanto o numerador quanto o denominador:
    
    $\lim_{\omega \to \infty} H_{HP}(j\omega) = \frac{K \cdot s^2}{s^2} = K \quad (\text{o sinal de alta frequência passa livremente})$
    
- **Taxa de subida:** Sobe a $+40\text{ dB/década}$ desde as baixas frequências até atingir $\omega_0$.
- **Exemplo físico clássico:** A tensão sobre o indutor em um circuito série $RLC$.

### Resumo Comparativo das Formas de 2.ª Ordem

| **Tipo de Filtro** | **Numerador N(s)** | **Ganho em ω→0** | **Ganho em ω=ω0** | **Ganho em ω→∞** |
| --- | --- | --- | --- | --- |
| **Passa-Baixa (LP)** | $K \omega_0^2$ (termo constante) | $K$ **(máximo)** | Depende de $Q$ | $0$ |
| **Passa-Banda (BP)**
    | $K \frac{\omega_0}{Q} s$ (termo em $s^1$)    | $0$ | $K$ **(pico)** | $0$ |
| **Passa-Alta (HP)** | $K s^2$ (termo em $s^2$) | $0$ | Depende de $Q$ | $K$ **(máximo)** |

## Passa-baixa, passa-alta e passa-banda

Considerando um circuito RLC série, ele pode desempenhar papéis de **passa-baixa**, **passa-alta**, **passa-banda** ou até **rejeita-banda (notch)**, dependendo exclusivamente de **onde você aplica o sinal de entrada** e de **onde você mede o sinal de saída**.

### Passo 1: A Corrente Única do Circuito

Num circuito com três componentes em série ($R$, $L$ e $C$) alimentados por uma fonte $V_{in}(s)$, a corrente $I(s)$ que atravessa todos eles é exatamente a mesma.

A impedância equivalente total da malha série ($Z_{total}$) é a soma direta das impedâncias de cada ramo:

$Z_R(s) = R$

$Z_L(s) = sL$

$Z_C(s) = \frac{1}{sC}$

$Z_{total}(s) = R + sL + \frac{1}{sC}$

Pela Lei de Ohm elementar ($V_{in} = Z_{total} \cdot I$), a corrente é dada por:

$I(s) = \frac{V_{in}(s)}{Z_{total}(s)} = \frac{V_{in}(s)}{sL + R + \frac{1}{sC}}$

Para eliminar a fração $\frac{1}{sC}$ do denominador, reduz-se toda a expressão ao mesmo denominador comum ($sC$):

$sL + R + \frac{1}{sC} = \frac{(sL \cdot sC) + (R \cdot sC) + 1}{sC} = \frac{s^2 LC + sRC + 1}{sC}$

Invertendo e multiplicando pelo numerador:

$I(s) = \frac{sC}{s^2 LC + sRC + 1} V_{in}(s)$

Para isolar o termo $s^2$ (forma canónica unitária), divide-se o numerador e o denominador por $LC$:

$I(s) = \frac{\frac{sC}{LC}}{\frac{s^2 LC}{LC} + \frac{sRC}{LC} + \frac{1}{LC}} V_{in}(s)$

Simplificando os termos ($C$ corta no numerador e no termo do meio):

$I(s) = \frac{\frac{s}{L}}{s^2 + \frac{R}{L}s + \frac{1}{LC}} V_{in}(s)$

### Passo 2: Dedução de cada Tensão de Saída

A tensão sobre qualquer componente individual é simplesmente a corrente $I(s)$ multiplicada pela impedância $Z_k(s)$ desse componente:

$V_{out}(s) = I(s) \cdot Z_k(s)$

A função de transferência $\frac{V_{out}(s)}{V_{in}(s)}$ obtém-se substituindo a expressão de $I(s)$:

$\frac{V_{out}(s)}{V_{in}(s)} = Z_k(s) \cdot \left[ \frac{\frac{s}{L}}{s^2 + \frac{R}{L}s + \frac{1}{LC}} \right]$

#### Saída sobre o Condensador (capacitor)

A impedância do condensador é $Z_C(s) = \frac{1}{sC}$:

$\frac{V_C(s)}{V_{in}(s)} = \left(\frac{1}{sC}\right) \cdot \left[ \frac{\frac{s}{L}}{s^2 + \frac{R}{L}s + \frac{1}{LC}} \right]$

Multiplicando os numeradores:

$\frac{1}{sC} \cdot \frac{s}{L} = \frac{s}{s \cdot LC} = \frac{1}{LC}$

O termo $s$ cancela-se completamente, restando uma constante:

$\frac{V_C(s)}{V_{in}(s)} = \frac{\frac{1}{LC}}{s^2 + \frac{R}{L}s + \frac{1}{LC}}$

- **Interpretação:** Não existe $s$ no numerador. Em DC ($s = j0$), o ganho é $\frac{1/LC}{1/LC} = 1$; para frequências altas ($s \to \infty$), o denominador cresce com $s^2$ e o ganho vai para zero. Trata-se de um **passa-baixo**.

#### 2. Saída sobre a Bobina/Indutor

A impedância da bobina é $Z_L(s) = sL$:

$\frac{V_L(s)}{V_{in}(s)} = (sL) \cdot \left[ \frac{\frac{s}{L}}{s^2 + \frac{R}{L}s + \frac{1}{LC}} \right]$

Multiplicando os numeradores:

$(sL) \cdot \left(\frac{s}{L}\right) = s^2 \cdot \frac{L}{L} = s^2$

O valor $L$ cancela-se, restando $s^2$:

$\frac{V_L(s)}{V_{in}(s)} = \frac{s^2}{s^2 + \frac{R}{L}s + \frac{1}{LC}}$

- **Interpretação:** Em DC ($s = 0$), o numerador anula o ganho ($0$); em frequências infinitas ($s \to \infty$), o numerador $s^2$ equipara-se ao denominador $s^2$ e o ganho tende para $1$. Trata-se de um **passa-alto**.

#### 3. Saída sobre a Resistência

A impedância da resistência é simplesmente $Z_R(s) = R$:

$\frac{V_R(s)}{V_{in}(s)} = R \cdot \left[ \frac{\frac{s}{L}}{s^2 + \frac{R}{L}s + \frac{1}{LC}} \right]$

Multiplicando a constante pelo numerador:

$\frac{V_R(s)}{V_{in}(s)} = \frac{\frac{R}{L}s}{s^2 + \frac{R}{L}s + \frac{1}{LC}}$

- **Interpretação:** Contém o termo linear $s^1$ no numerador. Em DC ($s = 0$) o ganho é zero; em altas frequências ($s \to \infty$) o denominador de 2.º grau domina e o ganho também cai para zero. O ganho só é máximo no ponto intermédio onde $s^2 + \frac{1}{LC} = 0$ ($\omega_0 = 1/\sqrt{LC}$). Trata-se de um **passa-banda**.

#### 4. Saída sobre o conjunto Bobina + Condensador

A impedância da associação série de $L$ e $C$ é $Z_{LC}(s) = sL + \frac{1}{sC}$:

Reduzindo ao mesmo denominador comum ($sC$):

$Z_{LC}(s) = \frac{s^2 LC + 1}{sC}$

Multiplicando por $I(s)$:

$\frac{V_{LC}(s)}{V_{in}(s)} = \left( \frac{s^2 LC + 1}{sC} \right) \cdot \left[ \frac{\frac{s}{L}}{s^2 + \frac{R}{L}s + \frac{1}{LC}} \right]$

Multiplicando as frações dos numeradores:

$\left( \frac{s^2 LC + 1}{sC} \right) \cdot \left(\frac{s}{L}\right) = \frac{(s^2 LC + 1) \cdot s}{s \cdot LC} = \frac{s^2 LC + 1}{LC}$

Dividindo individualmente cada parcela por $LC$:

$\frac{s^2 LC}{LC} + \frac{1}{LC} = s^2 + \frac{1}{LC}$

Substituindo de volta na fração completa:

$\frac{V_{LC}(s)}{V_{in}(s)} = \frac{s^2 + \frac{1}{LC}}{s^2 + \frac{R}{L}s + \frac{1}{LC}}$

- **Interpretação:** Na frequência de ressonância exata $\omega_0 = 1/\sqrt{LC}$, o termo $s^2 + \frac{1}{LC} = (j\omega_0)^2 + \omega_0^2 = -\omega_0^2 + \omega_0^2 = 0$. O numerador anula-se precisamente nessa frequência, gerando um "buraco" de transmissão nula. Trata-se de um filtro **rejeita-banda (notch)**.

## Diferença entre RLC série e RLC paralelo

No circuito série e no circuito paralelo, o que muda fundamentalmente é a **dualidade elétrica** entre corrente e tensão:

### 1. No Circuito RLC Série

- **O que acontece na ressonância (**$\omega_0$**)?** As reatâncias anulam-se mutuamente ($j\omega_0 L + \frac{1}{j\omega_0 C} = 0$). O ramo $L$-$C$ comporta-se como um curto-circuito.
- **Corrente:** A impedância total atinge o seu valor **mínimo** ($Z_{s\acute{e}rie} = R$). Logo, a **corrente no circuito é máxima**:
    
    $I(\omega_0) = \frac{V_{in}}{R}$
    
- **Tensão no Resistor:** Pela Lei de Ohm ($V_R = R \cdot I$), como a corrente é máxima, a tensão sobre o resistor também atinge o pico e torna-se igual à tensão de entrada ($V_R = V_{in}$).
- Portanto, no circuito série, **a corrente máxima e a tensão máxima sobre o resistor ocorrem juntas** em $\omega_0$.

### 2. No Circuito RLC Paralelo

- **O que acontece na ressonância (**$\omega_0$**)?** As susceptâncias anulam-se mutuamente ($\frac{1}{j\omega_0 L} + j\omega_0 C = 0$). O conjunto $L\mathbin{/\mkern-1mu/}C$ comporta-se como um circuito aberto (impedância infinita).
- **Impedância Equivalente:** A impedância total atinge o seu valor **máximo** ($Z_{paralelo} = R$).
- **Tensão:** Como o circuito é alimentado por uma fonte de corrente $I_C$ (vinda do amplificador/feixe), a tensão resultante nos nós é:
    
    $V_C(\omega_0) = Z_{paralelo} \cdot I_C = R \cdot I_C$
    
    A **tensão atinge o seu valor máximo possível** em $\omega_0$.
    
- **Corrente no Resistor:** Como o ramo $L\mathbin{/\mkern-1mu/}C$ abre, toda a corrente externa injetada $I_C$ é forçada a passar exclusivamente pelo resistor $R$:
    
    $I_R(\omega_0) = \frac{V_C(\omega_0)}{R} = I_C$
    
    Fora da ressonância, a corrente é desviada para o terra através do indutor (em baixa frequência) ou do capacitor (em alta frequência).
    

### Resumo da Dualidade

| **Configuração** | **Impedância Total em ω0** | **O que gera o pico passa-banda?** |
| --- | --- | --- |
| **RLC Série** (fonte de tensão) | **Mínima** ($Z = R$) | A corrente atinge o pico máximo e, por consequência, a queda de tensão no resistor $V_R = R \cdot I$ é máxima. |
| **RLC Paralelo** (fonte de corrente)    | **Máxima** ($Z = R$) | A tensão $V_C$ atinge o pico máximo porque a corrente externa não consegue escapar por $L$ e $C$, fluindo inteiramente por $R$. |

Portanto, em ambos os casos, tanto a corrente no resistor quanto a tensão no resistor atingem o seu máximo em $\omega_0$. A distinção é que o circuito paralelo atinge o pico através da **maximização da impedância** (impedância infinita em $L\mathbin{/\mkern-1mu/}C$), enquanto o série atinge o pico através da **minimização da impedância** (curto-circuito em $L\text{--}C$).