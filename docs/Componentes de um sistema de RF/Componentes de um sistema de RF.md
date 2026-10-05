# Componentes de um sistema de RF

# Componentes de um sistema de RF

![image.png](Componentes%20de%20um%20sistema%20de%20RF/image.png)

### 1. Low Level Radio Frequency (LLRF)

O **LLRF** é o núcleo de processamento e controle em malha fechada do sistema de RF.

- Este bloco manipula o sinal de radiofrequência exclusivamente na sua forma de sinal fraco (baixa potência, tipicamente na ordem de miliwatts ou poucos volts), antes de ser enviado aos amplificadores de potência.
- **Como funciona na prática:** No Sirius, o LLRF é implementado digitalmente utilizando uma plataforma integrada (PicoDigitizer) equipada com uma **FPGA Xilinx Virtex-6**. A FPGA executa em tempo real o algoritmo de controle proporcional-integral (PI) e desfasadores digitais nas componentes em quadratura ($I$ e $Q$).
- **Função no sistema:** O feixe de eletrões e as fontes de potência provocam perturbações contínuas na cavidade. A FPGA calcula o erro entre o campo eletromagnético medido e a referência desejada, aplicando correções em microssegundos com largura de banda de dezenas de kHz para manter o campo elétrico com desvios inferiores a 0,1% em amplitude e 0,1° em fase.

### 2. Conversores de Dados

Os conversores são as pontes de comunicação direta entre a física analógica contínua da planta e a lógica digital discreta da FPGA.

- **ADC (Analog-to-Digital Converter):**
    - Recebe a tensão analógica contínua vinda da cavidade (após ser rebaixada para frequência intermediária) e recolhe amostras periódicas a alta velocidade.
    - No Sirius, são utilizadas placas FMC com ADCs de 14 bits operando a taxas de até 125 Msps (milhões de amostras por segundo). A relação entre a taxa de amostragem e a frequência recebida é sincronizada para permitir a decomposição direta do sinal nas suas componentes $I$ e $Q$ (amostragem IQ).
- **DAC (Digital-to-Analog Converter):**
    - Recebe os números digitais binários processados pelo algoritmo de controle da FPGA e gera uma tensão analógica contínua na saída.
    - No sistema do Sirius, são empregues DACs de 16 bits capazes de operar a 250 Msps, reconstruindo o sinal analógico que excitará o restante circuito de transmissão.

### 3. Misturadores de Frequência

Os misturadores são componentes não lineares de três portas (RF, LO e IF) que utilizam o produto de dois sinais para efetuar translação de bandas no espetro eletromagnético:

- **Down-Conversion (Detetor / Entrada):**
    - A cavidade do Sirius opera a aproximadamente $500\text{ MHz}$. Amostrar diretamente uma portadora de $500\text{ MHz}$ exigiria conversores ADC e circuitos de clock de custo extremo e sujeitos a elevado ruído de fase (*jitter*).
    - O misturador de entrada multiplica a portadora da cavidade por Oscilador Local ($LO$) para baixar a informação útil para uma Frequência Intermediária ($IF$) de $20\text{ MHz}$, onde a amostragem pelo ADC ocorre de forma confortável e com elevada resolução.
- **Up-Conversion (Atuador / Saída):**
    - Após o processamento na FPGA, o sinal de controlo corrigido é sintetizado pelo DAC na banda intermediária ($20\text{ MHz}$).
    - O misturador de subida multiplica este sinal analógico de $20\text{ MHz}$ por um sinal de $LO$, convertendo-o de volta para a frequência nominal de $500\text{ MHz}$ necessária para alimentar a cavidade.

### 4. Filtros Passa-Baixas e Passa-Bandas

Sempre que um misturador realiza a multiplicação entre a portadora e o $LO$ ($y_{RF} \cdot y_{LO}$), a trigonometria obriga à geração de duas frequências espelhadas: a soma ($f_{LO} + f_{RF}$) e a diferença ($\vert{}f_{LO} - f_{RF}\vert{}$).

- **Filtros Passa-Baixas na Down-Conversion:** Após o primeiro misturador, o filtro rejeita a frequência da soma (que fica em alta frequência) e deixa passar apenas a frequência da diferença ($f_{IF} = 20\text{ MHz}$), entregando uma sinusóide limpa e sem *aliasing* ao conversor ADC.
- **Filtros Passa-Bandas na Up-Conversion:** Após o misturador de subida, o filtro seleciona estritamente a banda centrada em $500\text{ MHz}$ e suprime qualquer resíduo do oscilador local e da banda lateral espúria antes que o sinal entre nos estágios de amplificação.

### 5. Cadeia de Amplificação

O sinal de RF que sai do LLRF e dos filtros de reconstrução possui uma potência ínfima (na ordem de dezenas de miliwatts), incapaz de acelerar diretamente o feixe. Para atingir os níveis de potência necessários (dezenas ou centenas de quilowatts), utilizam-se dois estágios:

- **Pré-Amplificador (PreAmp):** Um primeiro estágio de amplificação linear de pequenos sinais que eleva o nível de tensão para que ele atinja o patamar de excitação exigido pela entrada dos grandes amplificadores.
- **Amplificador de Potência em Estado Sólido (SSAMP - Solid State Amplifier):** É a etapa de potência final. É composto por centenas de transistores de potência de RF de alta frequência combinados internamente para gerar quilowatts de potência contínua, atuando como o motor elétrico que empurra a cavidade.

### 6. Fontes de Alimentação

São as unidades elétricas que convertem a corrente alternada da rede elétrica geral em corrente contínua (DC) estável e regulada para alimentar os transistores dos amplificadores de potência.

- **Importância para o LLRF:** Flutuações térmicas e pequenas oscilações de tensão residuais (*ripple*) geradas pela retificação dessas fontes introduzem modulações espúrias de amplitude no sinal de saída do amplificador. O sistema de LLRF precisa de ter largura de banda rápida o suficiente para detetar e rejeitar ativamente essas perturbações de fonte antes que elas afetem a energia dos eletrões.

### 7. Linhas de Transmissão

São os meios físicos por onde os campos eletromagnéticos confinados viajam entre as salas técnicas e o túnel do acelerador:

- **Cabos Coaxiais de Precisão:** Cabos blindados com impedância característica padrão ($50\,\Omega$) utilizados para os caminhos de baixa potência, transporte de sinais de clock, referência de oscilador local e medições de leitura enviadas da cavidade de volta ao LLRF.
- **Guias de Onda:** Tubos metálicos ocos (geralmente retangulares de alumínio ou cobre) com dimensões físicas específicas para a frequência de $500\text{ MHz}$. Cabos coaxiais comuns derreteriam ou sofreriam perdas inaceitáveis se submetidos a dezenas de quilowatts contínuos; por isso, a potência maciça que sai do amplificador SSAMP é transportada até ao acoplador da cavidade ressonante através de guias de onda rígidos.

# Matemática do Down-Conversion

### A Matemática do *Down-Conversion*

O misturador (*mixer*) opera essencialmente como um multiplicador analógico entre o sinal vindo da cavidade de RF e um sinal de referência gerado por um Oscilador Local ($LO$).

Considere o sinal de tensão da cavidade modulado em amplitude e fase:

$v_{RF}(t) = A(t) \cos(\omega_{RF} t + \phi(t))$

O oscilador local fornece uma sinusóide pura com frequência angular $\omega_{LO}$ e fase fixa $\theta_{LO}$:

$v_{LO}(t) = \cos(\omega_{LO} t + \theta_{LO})$

O misturador multiplica os dois sinais no domínio do tempo:

$v_{mix}(t) = v_{RF}(t) \cdot v_{LO}(t) = A(t) \cos(\omega_{RF} t + \phi(t)) \cdot \cos(\omega_{LO} t + \theta_{LO})$

Aplicando a identidade trigonométrica do produto de dois cossenos, $\cos(a)\cos(b) = \frac{1}{2}[\cos(a - b) + \cos(a + b)]$:

$v_{mix}(t) = \frac{1}{2} A(t) \cos\big( (\omega_{RF} - \omega_{LO})t + \phi(t) - \theta_{LO} \big) + \frac{1}{2} A(t) \cos\big( (\omega_{RF} + \omega_{LO})t + \phi(t) + \theta_{LO} \big)$

Esta operação gera duas componentes espectrais bem definidas:

1. **Componente de Soma (**$\omega_{RF} + \omega_{LO}$**):** Fica situada numa frequência muito elevada (em torno de $500\text{ MHz} + 480\text{ MHz} = 980\text{ MHz}$).
2. **Componente de Diferença (**$\omega_{RF} - \omega_{LO}$**):** Fica situada exatamente na frequência pretendida:
    
    $\omega_{IF} = \omega_{RF} - \omega_{LO} \implies 500\text{ MHz} - 480\text{ MHz} = 20\text{ MHz}$
    

O sinal passa de seguida pelo **filtro passa-baixo**, que suprime totalmente o termo a $980\text{ MHz}$. O sinal entregue à entrada do conversor analógico-digital (ADC) é unicamente:

$v_{IF}(t) = \frac{1}{2} A(t) \cos(\omega_{IF} t + \phi(t) - \theta_{LO})$

> **Observação crucial:** Toda a dinâmica lenta de amplitude $A(t)$ e fase $\phi(t)$ da cavidade foi preservada de forma intacta, sofrendo apenas uma rotação angular estática constante ($\theta_{LO}$) e uma divisão de amplitude (o ganho de conversão $g_M$ do mixer).
> 

### Por que transladar para $20\text{ MHz}$?

A escolha da frequência intermediária ($f_{IF} = 20\text{ MHz}$) resulta de três restrições técnicas do sistema LLRF do Sirius:

#### Limitações Físicas do ADC

Amostrar diretamente uma sinusóide a $500\text{ MHz}$ exigiria conversores de gigasamples por segundo (Gsps).

- Conversores operando a frequências ultra-elevadas possuem um número efetivo de bits (ENOB) reduzido, perdendo resolução de amplitude.
- Pequenas incertezas temporais no relógio de amostragem (*aperture jitter*) degradam severamente a relação sinal-ruído (SNR) quando a derivada $\frac{dv}{dt}$ do sinal é muito elevada. Ao descer a frequência de $500\text{ MHz}$ para $20\text{ MHz}$, a velocidade de variação do sinal decai 25 vezes, permitindo leituras analógicas com precisão de 14 bits na placa FMC.

#### Sincronismo para a Desmodulação IQ

No LLRF, o ADC opera a uma taxa de amostragem fixa de $f_s = 100\text{ MSps}$ ou $125\text{ MSps}$. Quando $f_s = 100\text{ MSps}$ e $f_{IF} = 20\text{ MHz}$, a relação é uma razão inteira exata:

$\frac{f_s}{f_{IF}} = \frac{100\text{ MSps}}{20\text{ MHz}} = 5 \text{ amostras por período}$

Com uma amostragem síncrona conhecida em relação ao ciclo da onda intermediária, o cálculo das componentes em quadratura ($I$ e $Q$) no interior da FPGA torna-se aritmeticamente simplificado, reduzindo o tempo de latência de cálculo digital e o atraso de transporte em malha fechada.

#### Isolamento de Offset DC e Ruído de Baixa Frequência

Poder-se-ia questionar por que razão o sinal não é descido diretamente para $0\text{ Hz}$ (*Direct Conversion* ou *Zero-IF*).

- Se $\omega_{LO} = \omega_{RF}$, o sinal resultante cairia em corrente contínua ($0\text{ Hz}$). Em sistemas de instrumentação de alta precisão, o regime DC é problemático devido a tensões de desvio térmico (*DC offset* dos amplificadores operacionais), derivas lentas e ruído de cintilação (*ruído* $1/f$).
- Ao manter o sinal numa portadora intermediária limpa de $20\text{ MHz}$, esses ruídos de baixa frequência são facilmente rejeitados antes da digitalização, garantindo a estabilidade de amplitude necessária para o feixe do acelerador.

# Matemática do Up-Conversion

### A Matemática do *Up-Conversion*

O misturador de subida (*Up-Converter*) realiza a operação inversa do *Down-Converter*, multiplicando a onda de Frequência Intermediária gerada pelo conversor digital-analógico (DAC) por um sinal de referência em alta frequência proveniente do Oscilador Local ($LO$).

O sinal analógico sintetizado pelo DAC na frequência intermediária ($\omega_{IF} \approx 2\pi \times 20\text{ MHz}$) contém a amplitude $A_{act}(t)$ e a fase $\phi_{act}(t)$ calculadas pelo controlador digital:

$v_{IF}(t) = A_{act}(t) \cos(\omega_{IF} t + \phi_{act}(t))$

O oscilador local injeta uma portadora pura em alta frequência ($\omega_{LO} \approx 2\pi \times 480\text{ MHz}$) com fase estática $\theta_{LO}$:

$v_{LO}(t) = \cos(\omega_{LO} t + \theta_{LO})$

O mixer multiplica esses dois termos no domínio do tempo:

$v_{mix}(t) = v_{IF}(t) \cdot v_{LO}(t) = A_{act}(t) \cos(\omega_{IF} t + \phi_{act}(t)) \cdot \cos(\omega_{LO} t + \theta_{LO})$

Pela relação trigonométrica do produto de cossenos ($\cos(a)\cos(b) = \frac{1}{2}[\cos(a+b) + \cos(a-b)]$):

$v_{mix}(t) = \frac{1}{2} A_{act}(t) \cos\big( (\omega_{LO} + \omega_{IF})t + \phi_{act}(t) + \theta_{LO} \big) + \frac{1}{2} A_{act}(t) \cos\big( (\omega_{LO} - \omega_{IF})t - \phi_{act}(t) + \theta_{LO} \big)$

A multiplicação gera duas raias espectrais distintas:

1. **Banda Lateral Superior (Soma):**
    
    $\omega_{RF} = \omega_{LO} + \omega_{IF} \implies 480\text{ MHz} + 20\text{ MHz} = \mathbf{500\text{ MHz}}$
    
2. **Banda Lateral Inferior (Diferença / Imagem Espúria):**
    
    $\omega_{esp} = \omega_{LO} - \omega_{IF} \implies 480\text{ MHz} - 20\text{ MHz} = 460\text{ MHz}$
    

O sinal passa pelo **filtro passa-bandas** sintonizado em $500\text{ MHz}$. Esse filtro rejeita o termo indesejado de $460\text{ MHz}$ e eventuais vazamentos do oscilador local em $480\text{ MHz}$.

O sinal resultante entregue aos pré-amplificadores é estritamente:

$v_{RF}(t) = \frac{1}{2} A_{act}(t) \cos(\omega_{RF} t + \phi_{act}(t) + \theta_{LO})$

Toda a modulação de amplitude $A_{act}(t)$ e fase $\phi_{act}(t)$ sintetizada na FPGA foi transladada para o canal de $500\text{ MHz}$, sofrendo apenas uma atenuação/ganho $g_M$ e uma rotação fixa de fase $\theta_M = \theta_{LO}$.

### Por que o sinal tem de ser transladado para 500 MHz?

A translação para $500\text{ MHz}$ decorre de restrições da física dos aceleradores de partículas e da cavidade ressonante do Sirius:

#### A Frequência de Ressonância da Cavidade

A cavidade de RF do anel de armazenamento do Sirius é uma estrutura metálica oca cujas dimensões geométricas foram construídas para ressoar no modo fundamental $TM_{010}$ exatamente em $500\text{ MHz}$.

- Se você injetar um sinal a $20\text{ MHz}$ na cavidade, ele se deparará com uma impedância praticamente nula (fora da ressonância, o indutor do circuito equivalente vira um curto-circuito para frequências baixas).
- Apenas em torno de $500\text{ MHz}$ a cavidade atinge a ressonância paralela, onde sua impedância $Z \approx R_L$ é máxima, acumulando campos elétricos longitudinais de centenas de quilovolts necessários para acelerar as partículas.

#### Sincronismo com o Feixe de Elétrons

No anel de armazenamento, os elétrons viajam a velocidades ultrarrelativísticas (praticamente à velocidade da luz, $c$).

- Eles não circulam de forma uniforme e contínua, mas agrupados em pacotes discretos (*bunches*).
- Para que os elétrons ganhem energia e compensem a perda contínua por radiação síncrotron, cada pacote precisa atravessar a fenda da cavidade exatamente no instante em que o campo elétrico atinge o pico acelerador.
- Como a circunferência do anel e o tempo de revolução das partículas são múltiplos harmônicos exatos de $500\text{ MHz}$, a portadora de RF deve operar sintonizada a essa frequência para manter a condição de estabilidade de fase do feixe (*fase síncrona*).

#### Limitações de Síntese Direta pelos DACs

Os conversores digitais-analógicos (DACs) comerciais de alta precisão (16 bits) operam com taxas de amostragem confortáveis na faixa de dezenas a centenas de megasamples por segundo ($250\text{ MSps}$). Sintetizar digitalmente uma onda de $500\text{ MHz}$ com alta pureza espectral e baixo ruído exigiria amostragem no patamar de vários gigasamples por segundo, o que aumentaria a complexidade e deterioraria a faixa dinâmica da malha.

O *Up-Conversion* permite à FPGA e ao DAC trabalharem na banda intermediária de $20\text{ MHz}$ e realizarem a translação final para os $500\text{ MHz}$ da física da cavidade por via analógica pura.

# Onde ocorre a modulação e demodulação IQ

Tanto a **desmodulação** (extração de $I$ e $Q$) quanto a **modulação** (reconstrução a partir de $I$ e $Q$) acontecem **no domínio digital, dentro da FPGA**, imediatamente após o ADC e imediatamente antes do DAC.

Para entender o fluxo completo, dividimos em duas etapas:

### Onde o sinal é desmodulado

O sinal analógico vindo da cavidade é rebaixado pelo mixer para a Frequência Intermediária ($IF \approx 20\text{ MHz}$) e entra no ADC:

$v_{IF}(t) = I(t)\cos(\omega_{IF}t) - Q(t)\sin(\omega_{IF}t)$

Quando o sinal atravessa o bloco **ADC** no final da linha:

- O ADC colhe amostras discretas a uma taxa síncrona conhecida $f_s$.
- **Imediatamente na entrada digital da FPGA** (após o ADC), o sinal é desmodulado em $I$ e $Q$.

#### Como funciona a "Amostragem IQ" direta:

Em sistemas como o do Sirius, a taxa de amostragem do ADC é sincronizada de modo que haja um número exato de amostras por ciclo da senoide de $IF$.

Um exemplo clássico e intuitivo é quando $f_s = 4 \times f_{IF}$ (amostragem a cada quarto de período, $\Delta t = \frac{T_{IF}}{4}$, correspondendo a saltos de $90^\circ$ ou $\pi/2\text{ rad}$):

- Na amostra $k=0$ ($\text{fase } 0^\circ$): $\cos(0) = 1$ e $\sin(0) = 0 \implies \mathbf{Amostra_0 = I}$
- Na amostra $k=1$ ($\text{fase } 90^\circ$): $\cos(90^\circ) = 0$ e $\sin(90^\circ) = 1 \implies \mathbf{Amostra_1 = -Q}$
- Na amostra $k=2$ ($\text{fase } 180^\circ$): $\cos(180^\circ) = -1$ e $\sin(180^\circ) = 0 \implies \mathbf{Amostra_2 = -I}$
- Na amostra $k=3$ ($\text{fase } 270^\circ$): $\cos(270^\circ) = 0$ e $\sin(270^\circ) = -1 \implies \mathbf{Amostra_3 = Q}$

Com essa sincronização, a FPGA não precisa de multiplicadores senoidais complexos: basta intercalar as amostras do ADC com trocas de sinal para obter as séries temporais de $I$ e $Q$ em banda base.

### Onde o sinal é modulado

O processo inverso ocorre na saída do controlador PI:

- O algoritmo de controle na FPGA calcula as correções necessárias diretamente como dois números digitais: $I_{act}$ e $Q_{act}$.
- Ainda **dentro da FPGA**, antes do bloco **DAC**, esses dois valores modulam digitalmente uma portadora em frequência intermediária através de um oscilador local digital (DDS/NCO):
    
    $V_{act}[n] = I_{act}[n]\cos(\omega_{IF} n T_s) - Q_{act}[n]\sin(\omega_{IF} n T_s)$
    
- O fluxo resultante $V_{act}[n]$ é uma única palavra digital que entra no **DAC**.
- O **DAC** converte essa sequência de números na onda analógica contínua em $20\text{ MHz}$ ($IF$), que segue então para o mixer de subida ($Up-Conversion$) em direção aos $500\text{ MHz}$.

### Resumo do Posicionamento

- **Desmodulação IQ:** Ocorre **na FPGA**, logo após a digitalização pelo **ADC**. O ADC apenas digitaliza a senoide rápida de $20\text{ MHz}$; quem a separa nas coordenadas $I$ e $Q$ de banda base é a lógica digital interna.
- **Modulação IQ:** Ocorre **na FPGA**, imediatamente antes do **DAC**. A lógica digital junta as correções $I$ e $Q$ numa portadora digital de $20\text{ MHz}$, e o DAC sintetiza o sinal analógico $IF$ correspondente.

# Sobre largura de banda para controle das fontes

A **largura de banda** de um sistema de controle em malha fechada é a medida direta da sua **velocidade de reação**: ela dita a frequência máxima de oscilação que o controlador consegue enxergar e corrigir antes que a perturbação se propague pela planta.

A relação entre a largura de banda e a rejeição do ruído das fontes pode ser compreendida através dos seguintes pontos:

### O que é a perturbação da fonte

As fontes de alimentação dos amplificadores de potência retificam a rede elétrica alternada (60 Hz no Brasil).

- Mesmo com filtros capacitivos e indutivos pesados, sempre sobra um resíduo periódico de tensão contínua conhecido como **ripple** (típico em 60 Hz, 120 Hz, 360 Hz, ou harmônicos de chaveamento de fontes chaveadas em dezenas de kHz).
- Como o ganho dos transistores de potência de RF depende diretamente da tensão DC de alimentação, esse *ripple* oscila o ganho do amplificador, modulando a amplitude do sinal de RF que excita a cavidade.
- Se a amplitude da cavidade oscilar nessas frequências, os elétrons do feixe recebem empurrões desiguais a cada volta, o que desestabiliza a órbita das partículas e degrada o feixe de luz síncrotron.

### O papel da Largura de Banda do Controlador

Em teoria de controle clássico, a capacidade de **rejeição de perturbações** de uma malha fechada depende da função de sensibilidade $S(s) = \frac{1}{1 + C(s)H(s)}$:

- **Abaixo da frequência de corte da malha (**$\omega < BW$**):**
    
    O ganho de malha aberta $\vert{}C(s)H(s)\vert{}$ é muito alto. A função de sensibilidade $\vert{}S(s)\vert{} \ll 1$ é próxima de zero. Isso significa que **o controlador atenua e cancela quase 100% da perturbação**. Se a tensão da fonte cair e ameaçar reduzir o campo, o LLRF detecta a queda em fração de microssegundo e aumenta o sinal do DAC na mesma proporção contrária, mantendo o campo na cavidade plano e constante.
    
- **Acima da frequência de corte da malha (**$\omega > BW$**):**
    
    O controlador "não tem velocidade" para acompanhar. O ganho de malha cai ($\vert{}C(s)H(s)\vert{} \to 0$) e a sensibilidade vai para 1 ($\vert{}S(s)\vert{} \approx 1$). O controlador torna-se "cego" para variações que ocorram mais rápido do que a sua banda passante, deixando o ruído passar livremente para o feixe.
    

### Exemplo Prático com Números

Imagine que a fonte de alimentação do amplificador apresente um ruído residual de chaveamento a $10\text{ kHz}$:

- **Cenário A: LLRF com largura de banda de** $1\text{ kHz}$ **(lento):**
    
    O LLRF só consegue agir eficazmente sobre variações que ocorram abaixo de 1 kHz. Quando o ruído de 10 kHz oscilar a potência do amplificador, a malha de controle não terá tempo hábil de reagir (o atraso de cálculo e de resposta faz com que a correção chegue atrasada no tempo). A oscilação atinge a cavidade e perturba o feixe.
    
- **Cenário B: LLRF com largura de banda de** $50\text{ kHz}$ **a** $100\text{ kHz}$ **(rápido):**
    
    Como a banda de controle é significativamente maior do que a frequência do ruído (10 kHz $\ll$ 50 kHz), o algoritmo PI dentro da FPGA rastreia a oscilação ciclo a ciclo e injeta uma contra-modulação exata em oposição de fase, suprimindo o ruído antes que ele altere a tensão líquida na cavidade.
    

### Em Resumo

Dizer que o LLRF precisa de uma **"largura de banda rápida o suficiente"** significa que a sua velocidade de amostragem, cálculo e atuação em malha fechada deve ser mais veloz do que a taxa de variação dos ruídos gerados pelas fontes e pelo feixe, garantindo que o controlador consiga anular essas oscilações ativamente em tempo real.