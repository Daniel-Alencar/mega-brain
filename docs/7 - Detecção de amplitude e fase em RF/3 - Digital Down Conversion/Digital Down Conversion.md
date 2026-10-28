# Digital Down Conversion

# IQ Modulation

## Por que usar IQ para transmitir e receber sinais

A base da modulação IQ depende de uma conversão de coordenadas polares (amplitude e fase) para coordenadas retangulares (eixos I e Q), utilizando uma identidade trigonométrica clássica.

Qualquer sinal de rádio modulado pode ser descrito genericamente alterando sua amplitude $A(t)$ e sua fase $\phi(t)$ ao longo do tempo, em uma frequência de portadora fixa $f_c$:

$s(t) = A(t) \cos(2\pi f_c t + \phi(t))$

Para implementar isso em hardware, esbarramos em um problema: alterar a fase $\phi(t)$ de um oscilador de alta frequência de forma rápida e precisa é extremamente difícil e instável.

É aqui que entra a matemática para salvar o design do hardware, usando a identidade trigonométrica da soma de arcos:

$\cos(\alpha + \beta) = \cos(\alpha)\cos(\beta) - \sin(\alpha)\sin(\beta)$

Substituindo $\alpha = 2\pi f_c t$ (a nossa onda portadora) e $\beta = \phi(t)$ (a informação da fase), expandimos a equação do nosso sinal:

$s(t) = A(t) [ \cos(2\pi f_c t) \cos(\phi(t)) - \sin(2\pi f_c t) \sin(\phi(t)) ]$

$s(t) = [A(t) \cos(\phi(t))] \cos(2\pi f_c t) - [A(t) \sin(\phi(t))] \sin(2\pi f_c t)$

Neste ponto, isolamos os termos entre colchetes e os definimos como nossos sinais de informação em banda base **I** (Em Fase) e **Q** (Em Quadratura):

- $I(t) = A(t) \cos(\phi(t))$
- $Q(t) = A(t) \sin(\phi(t))$

O que simplifica nossa onda de rádio final para uma soma de duas ondas ortogonais:

$s(t) = I(t) \cos(2\pi f_c t) - Q(t) \sin(2\pi f_c t)$

Matematicamente, provamos que variar a amplitude e a fase de uma única onda é **exatamente igual** a somar uma onda cosseno e uma onda seno, alterando apenas a amplitude delas ($I$ e $Q$). A relação reversa, para encontrar a amplitude e fase finais a partir de I e Q, é feita por Pitágoras e trigonometria básica:

- **Amplitude:** $A(t) = \sqrt{I(t)^2 + Q(t)^2}$
- **Fase:** $\phi(t) = \arctan\left(\frac{Q(t)}{I(t)}\right)$

## Modulação e Demodulação IQ

### Modulando o Sinal

O sinal de rádio frequência $s(t)$ que sai da antena é a soma dos nossos dois sinais, multiplicados pelas portadoras ortogonais (cosseno e seno) em uma frequência $\omega_c$ (onde $\omega_c = 2\pi f_c$):

$s(t) = I(t)\cos(\omega_c t) - Q(t)\sin(\omega_c t)$

Este sinal viaja pelo espaço e atinge a antena receptora. Para simplificar, vamos assumir um canal perfeito, sem ruído, de modo que o sinal recebido seja exatamente $s(t)$.

### Demodulando o Canal I

No receptor, precisamos isolar o $I(t)$ original e destruir o $Q(t)$. Para isso, pegamos o sinal recebido e o **multiplicamos localmente** por uma onda cosseno gerada pelo próprio receptor:

$X_I(t) = s(t) \cdot \cos(\omega_c t)$

Substituindo $s(t)$ pela nossa primeira equação:

$X_I(t) = [I(t)\cos(\omega_c t) - Q(t)\sin(\omega_c t)] \cdot \cos(\omega_c t)$

Distribuindo a multiplicação:

$X_I(t) = I(t)\cos^2(\omega_c t) - Q(t)\sin(\omega_c t)\cos(\omega_c t)$

Aqui a mágica acontece graças a duas identidades trigonométricas clássicas ($\cos^2(x) = \frac{1 + \cos(2x)}{2}$ e $\sin(x)\cos(x) = \frac{\sin(2x)}{2}$):

$X_I(t) = I(t)\left[ \frac{1}{2} + \frac{\cos(2\omega_c t)}{2} \right] - Q(t)\left[ \frac{\sin(2\omega_c t)}{2} \right]$

Reorganizando os termos:

$X_I(t) = \frac{I(t)}{2} + \frac{I(t)\cos(2\omega_c t)}{2} - \frac{Q(t)\sin(2\omega_c t)}{2}$

**A Filtragem:** Observe os três termos da equação acima. O primeiro é apenas o nosso sinal de informação original $I(t)$ dividido por 2. Os dois últimos termos estão multiplicados por $\cos(2\omega_c t)$ e $\sin(2\omega_c t)$. Ou seja, estão oscilando no **dobro da frequência** da portadora.

Se passarmos esse resultado por um **Filtro Passa-Baixa**, as componentes de alta frequência ($2\omega_c$) são completamente eliminadas. Na prática de sistemas embarcados, após a amostragem por um ADC, esse filtro é frequentemente implementado de forma digital (como um filtro FIR) rodando acelerado no hardware do FPGA. O que sobra após o filtro é puro ouro:

$X_{I\_filtrado}(t) = \frac{I(t)}{2}$

Recuperamos o dado! A amplitude cai pela metade, mas isso é facilmente corrigido com um multiplicador (amplificador).

### Demodulando o Canal Q

Para isolar o Q, fazemos o processo espelhado, multiplicando o sinal recebido pelo oscilador local em quadratura, $-\sin(\omega_c t)$:

$X_Q(t) = s(t) \cdot (-\sin(\omega_c t))$

$X_Q(t) = [I(t)\cos(\omega_c t) - Q(t)\sin(\omega_c t)] \cdot (-\sin(\omega_c t))$

$X_Q(t) = -I(t)\sin(\omega_c t)\cos(\omega_c t) + Q(t)\sin^2(\omega_c t)$

Usando as identidades ($\sin^2(x) = \frac{1 - \cos(2x)}{2}$ e $\sin(x)\cos(x) = \frac{\sin(2x)}{2}$):

$X_Q(t) = -I(t)\left[ \frac{\sin(2\omega_c t)}{2} \right] + Q(t)\left[ \frac{1}{2} - \frac{\cos(2\omega_c t)}{2} \right]$

$X_Q(t) = -\frac{I(t)\sin(2\omega_c t)}{2} + \frac{Q(t)}{2} - \frac{Q(t)\cos(2\omega_c t)}{2}$

Aplicando o mesmo Filtro Passa-Baixa para matar os termos com $2\omega_c$, sobra apenas:

$X_{Q\_filtrado}(t) = \frac{Q(t)}{2}$

### Atraso de Fase

E se o oscilador local do receptor não estiver perfeitamente cravado com o do transmissor?

O sinal perfeito que viaja pelo ar e chega à antena do receptor é o nosso conhecido:

$s(t) = I \cos(\omega_c t) - Q \sin(\omega_c t)$

*(Vou omitir o $(t)$ do $I$ e do $Q$ para deixar a notação mais limpa, mas lembre-se que eles representam a informação mudando no tempo, e $\omega_c$ é a frequência da portadora).*

O problema começa dentro do receptor. Para ler o canal I, o receptor gera sua própria onda cosseno local para multiplicar pelo sinal que chegou. Porém, esse oscilador local tem um **erro de fase**, que chamaremos de $\Delta\theta$.

Vamos assumir que o receptor está gerando a onda: $\cos(\omega_c t - \Delta\theta)$.

**Expandindo o Oscilador do Receptor:**

Para podermos multiplicar as coisas facilmente, precisamos abrir essa onda do receptor usando a identidade trigonométrica da subtração de arcos ($\cos(A - B) = \cos(A)\cos(B) + \sin(A)\sin(B)$):

$Oscilador\_Local_I = \cos(\omega_c t)\cos(\Delta\theta) + \sin(\omega_c t)\sin(\Delta\theta)$

**O Misturador:**

Agora, o hardware do receptor multiplica o sinal que chegou pelo oscilador local defeituoso:

$X_I = s(t) \cdot Oscilador\_Local_I$

$X_I = [I \cos(\omega_c t) - Q \sin(\omega_c t)] \cdot [\cos(\omega_c t)\cos(\Delta\theta) + \sin(\omega_c t)\sin(\Delta\theta)]$

Temos que aplicar a propriedade distributiva (multiplicar tudo por tudo). Isso vai gerar 4 termos separados:

1. $I \cos(\omega_c t) \cdot \cos(\omega_c t)\cos(\Delta\theta) = \mathbf{I \cos^2(\omega_c t)\cos(\Delta\theta)}$
2. $I \cos(\omega_c t) \cdot \sin(\omega_c t)\sin(\Delta\theta) = \mathbf{I \cos(\omega_c t)\sin(\omega_c t)\sin(\Delta\theta)}$
3. $-Q \sin(\omega_c t) \cdot \cos(\omega_c t)\cos(\Delta\theta) = \mathbf{-Q \sin(\omega_c t)\cos(\omega_c t)\cos(\Delta\theta)}$
4. $-Q \sin(\omega_c t) \cdot \sin(\omega_c t)\sin(\Delta\theta) = \mathbf{-Q \sin^2(\omega_c t)\sin(\Delta\theta)}$

**A Filtragem:**

Esse sinal gigante entra no **Filtro Passa-Baixa**. O filtro tem uma regra simples: tudo o que oscilar rápido (alta frequência) é destruído. Tudo o que for constante ou lento (baixa frequência) passa.

Vamos olhar para a trigonometria de cada termo para ver o que sobrevive ao filtro:

- **Termos 2 e 3:** Eles contêm a multiplicação $\sin(\omega_c t)\cos(\omega_c t)$. Pela trigonometria, isso é igual a $\frac{\sin(2\omega_c t)}{2}$. Ou seja, eles estão oscilando no **dobro** da frequência da portadora (altíssima frequência). O filtro **zera** esses dois termos completamente.
- **Termo 1:** Contém $\cos^2(\omega_c t)$. A identidade diz que isso é $\frac{1 + \cos(2\omega_c t)}{2}$. O pedaço com $2\omega_c t$ morre no filtro, mas a constante $\frac{1}{2}$ sobrevive! O resultado que passa é $\frac{1}{2} I \cos(\Delta\theta)$.
- **Termo 4:** Contém $\sin^2(\omega_c t)$. A identidade diz que isso é $\frac{1 - \cos(2\omega_c t)}{2}$. Novamente, a parte de alta frequência morre, e a constante $\frac{1}{2}$ sobrevive. O resultado que passa é $-\frac{1}{2} Q \sin(\Delta\theta)$.

**O Sinal Recuperado:**

Juntando os dois termos que sobreviveram ao filtro, chegamos à equação exata do que o conversor analógico-digital vai ler no final da trilha de cobre:

$X_{I\_recuperado} = \frac{I \cos(\Delta\theta)}{2} - \frac{Q \sin(\Delta\theta)}{2}$

**O que essa equação nos diz na prática?**

Se não houvesse erro de fase ($\Delta\theta = 0^\circ$):

- $\cos(0^\circ) = 1$
- $\sin(0^\circ) = 0$
- O termo $Q$ inteiro é multiplicado por zero e desaparece. O resultado seria perfeitamente $X_I = I/2$.

Como existe um erro de fase, o $\sin(\Delta\theta)$ não é mais zero. Isso liga uma "ponte matemática" que pega um pedaço do valor da voltagem de $Q$ e injeta dentro da trilha do $I$, subtraindo ou somando do valor real que você queria ler.

# Digital Down Conversion

A técnica de **Digital Down Conversion (DDC)** — por vezes designada por *Digital Drop Receiver* (DDR) — é um método puramente digital para extrair a amplitude e a fase (ou as componentes em quadratura $I$ e $Q$) de um sinal de portadora digitalizado.

### 1. O Princípio Fundamental e a Motivação

Em muitas aplicações de RF em aceleradores, a informação útil está concentrada numa banda estreita em torno da frequência portadora ou da Frequência Intermediária ($IF$).

- **O Problema da Taxa Excessiva:**
    
    Pelo teorema de Nyquist clássico, amostrar uma portadora de banda limitada exige uma taxa superior ao dobro da frequência analógica mais elevada. Por exemplo, para um sinal centrado em $40\text{ MHz}$ com $1\text{ MHz}$ de largura de banda, a amostragem com sobreamostragem (*oversampling*) requereria pelo menos $82\text{ MSps}$. Processar esse fluxo brutal de dados na lógica digital exige enormes recursos computacionais e consumo energético.
    
- **A Solução DDC:**
    
    O teorema de Nyquist–Shannon afirma que a taxa de amostragem só necessita de ser, no mínimo, o dobro da **largura de banda da informação**. O DDC pega no sinal digitalizado a alta velocidade, translada a banda de interesse diretamente para a banda base ($0\text{ Hz}$) e, em seguida, reduz a taxa de amostragem (*decimação*) preservando toda a informação original. No exemplo de $1\text{ MHz}$ de banda, uma taxa de saída de apenas $2\text{ MSps}$ em banda base torna-se plenamente suficiente.
    

### 2. Os Três Blocos Estruturais do DDC

O DDC é tipicamente implementado dentro de FPGAs ou ASICs e é composto por três blocos fundamentais:

![DDC.drawio(1).png](Digital%20Down%20Conversion/DDC.drawio(1).png)

#### A. Misturadores Digitais (Multiplicadores)

Atuam exatamente como misturadores ideais. O sinal digitalizado vindo do ADC é multiplicado simultaneamente por duas portadoras digitais ortogonais ($\cos$ e $-\sin$). Tal como na trigonometria analógica, esta multiplicação gera duas frequências: a diferença ($f_{in} - f_{NCO}$, que cai em banda base quando as frequências coincidem) e a soma ($f_{in} + f_{NCO}$, de frequência dupla).

#### B. Oscilador Controlado Numericamente (NCO)

Gera os fluxos de amostras discretas de seno e cosseno para alimentar os multiplicadores digitais.

- **Sincronismo Perfeito:** Como os canais de seno e cosseno derivam do mesmo relógio digital interno, a quadratura de $90^\circ$ é rigorosamente exata, eliminando os desbalanços analógicos de fase e de ganho.
- **Princípio de Funcionamento:** É constituído por um **acumulador de fase** e um bloco de **conversão de fase para amplitude** (tabela de consulta / *lookup table* em memória). A cada ciclo de *clock*, soma-se uma palavra de sintonização binária $M$ (*tuning word*). A frequência de saída é dada por:
    
    $f_{out} = \frac{M}{2^N} f_{CLK}$
    
    (Com um acumulador de 32 bits a $50\text{ MHz}$, atinge-se uma resolução de sintonização extremamente fina de $\Delta f = 12\text{ mHz}$).
    
- **Truncação de Fase:** Para não exigir memórias gigantescas de consulta (o que exigiria gigabytes), a fase calculada no acumulador é truncada para os bits mais significativos antes da leitura na tabela. Essa aproximação pode introduzir pequenos espúrios periódicos no espetro (*phase truncation spurs*), reduzindo a gama dinâmica livre de espúrios (SFDR).

#### C. Filtros Passa-Baixo de Decimação (CIC / FIR)

A jusante dos multiplicadores, este filtro cumpre duas funções cruciais:

1. **Eliminar a frequência somada** de alta frequência gerada na multiplicação.
2. **Atuar como filtro anti-aliasing** estrito antes do descarte de amostras (*downsampling* por um fator $R$, $\downarrow R$).

### 3. Filtros CIC (*Cascaded Integrator Comb*)

Para fatores de decimação elevados ($R > 32$, aplicações de banda estreita), implementar filtros FIR tradicionais exigiria centenas de coeficientes e multiplicadores na FPGA. A solução padrão é o uso de filtros **CIC (Hogenauer)**, cuja vantagem primordial é **não necessitar de nenhum multiplicador digital**, operando exclusivamente com adições e subtrações.

- **Estrutura Básica:**
    
    Consiste numa cascata de $M$ estágios **integradores** (filtros IIR a operar à taxa de entrada rápida $f_{in}$), seguidos pelo bloco de decimação ($\downarrow R$), e finalizados por $M$ estágios **pente (*comb*)** (filtros que subtraem amostras atrasadas por um atraso diferencial $D$, operando à taxa reduzida $f_{out} = f_{in}/R$).
    
- **Relação com Médias Móveis:**
    
    Um filtro CIC de 1.ª ordem é matematicamente idêntico a um filtro de média móvel recursivo (*running-sum* ou *box-car filter*), cuja função de transferência é uma resposta do tipo sinc:
    
    $\vert{}H(f)\vert{} = \left\vert{} \frac{\sin(\pi D \frac{f}{f_{out}})}{\sin(\frac{\pi}{R} \frac{f}{f_{out}})} \right\vert{}^M$
    
- **Crescimento de Registo e Compensação:**
    
    O ganho DC de um decimador CIC é $(R \cdot D)^M$. Isso exige alargar a largura de bits dos registos internos ($\log_2(RD)$ bits por estágio) para acomodar o crescimento numérico e evitar transbordamentos destrutivos. Como a resposta sinc introduz uma ligeira atenuação na borda da banda passante (*passband droop*), costuma-se colocar um pequeno filtro FIR de compensação após o CIC para aplanar o espetro útil.
    

### 4. DDC vs. IQ Sampling Clássico

Diferenças cruciais entre a amostragem síncrona simples e o DDC:

| **Característica** | **IQ Demodulation (fs=4fIF)** | **Digital Down Conversion (DDC)** |
| --- | --- | --- |
| **Latência / Atraso de Grupo** | **Mínima** (cálculo quase instantâneo)    | **Elevada** (devido aos taps dos filtros CIC/FIR)    |
| **Flexibilidade de Frequência** | Rígida ($f_s$ tem de estar trancado em $4 f_{IF}$)    | **Total** (o NCO pode seguir qualquer frequência)    |
| **Relação Sinal-Ruído (SNR)** | Mais sensível a ruído e espúrios    | **Excelente** (o ganho de processamento e a decimação reduzem o ruído)    |
| **Aplicação Principal** | Malhas rápidas de realimentação de cavidade (LLRF fechado)    | Diagnóstico de feixe (BPM), monitorização e malhas lentas |

# Outros assuntos

[Decimador](https://app.notion.com/p/Decimador-3ed93844ea7780c8bbb7cd6db4d49187?pvs=21)

[Filtro CIC](https://app.notion.com/p/Filtro-CIC-3ed93844ea77808da33ef3e88d1abdde?pvs=21)

[Filtro FIR](https://app.notion.com/p/Filtro-FIR-3ed93844ea7780268055dfa4be6afea0?pvs=21)