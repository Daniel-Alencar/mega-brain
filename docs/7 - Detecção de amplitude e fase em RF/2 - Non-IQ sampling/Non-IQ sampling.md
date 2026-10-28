# Non-IQ sampling

A técnica de **Non-IQ sampling** foi concebida especificamente para superar a principal vulnerabilidade do *IQ sampling* tradicional: a contaminação do sinal útil por harmônicos que sofrem *aliasing* diretamente sobre a frequência portadora.

### 1. A Motivação do Problema

No *IQ sampling* clássico com passos de $90^\circ$ ($f_s = 4 \cdot f_{IF}$), os harmônicos ímpares (3º, 5º, etc.) gerados por distorções não lineares de mixers e ADCs dobram no espectro e caem exatamente em cima da frequência intermediária fundamental ($f_{IF}$). Como ocupam a mesma frequência no sinal digitalizado, torna-se impossível distingui-los ou filtrá-los.

### 2. O Conceito Fundamental

Em vez de impor uma relação inteira rígida de quatro amostras por ciclo, a frequência de amostragem $f_s$ é configurada de modo que $N$ amostras sejam distribuídas ao longo de $M$ períodos sucessivos da onda de $IF$:

$\frac{f_s}{f_{IF}} = \frac{N}{M} \iff N \cdot T_s = M \cdot T_{IF} \quad (M, N \in \mathbb{Z})$

Com essa relação, o avanço angular entre duas amostras consecutivas do ADC passa a ser:

$\Delta\varphi = \omega_{IF} T_s = 2\pi \frac{T_s}{T_{IF}} = 2\pi \frac{M}{N}$

- As amostras não caem sempre nos mesmos quatro pontos do ciclo.
- O círculo no plano I/Q é amostrado em vários locais distintos, e o padrão de amostragem só volta a repetir-se após $M$ períodos de $IF$.

### 3. A Matemática da Estimação por Mínimos Quadrados (LMS)

As $N$ leituras sucessivas do ADC formam um sistema linear de equações:

$y_i = I \cdot \sin(\varphi_i) + Q \cdot \cos(\varphi_i), \quad \text{onde } \varphi_i = i \cdot \Delta\varphi = i \cdot 2\pi \frac{M}{N} \quad (i = 0, 1, \dots, N-1)$

Na presença de ruído, quantização do ADC e jitter de clock, este sistema de $N$ equações torna-se sobre-determinado. Para extrair a melhor estimativa de $I$ e $Q$, aplica-se o método dos **Mínimos Quadrados (Least Mean Square - LMS)**, minimizando a função de erro quadrático:

$f(I, Q) = \sum_{i=0}^{N-1} \big( I \cdot \sin\varphi_i + Q \cdot \cos\varphi_i - y_i \big)^2$

Igualando as derivadas parciais a zero ($\frac{\partial f}{\partial I} = 0$ e $\frac{\partial f}{\partial Q} = 0$), obtém-se o sistema matricial:

$\begin{pmatrix} p_{11} & p_{12} \\ p_{21} & p_{22} \end{pmatrix} \begin{pmatrix} I \\ Q \end{pmatrix} = \begin{pmatrix} s_1 \\ s_2 \end{pmatrix}$

onde:

- $s_1 = \sum_{i=0}^{N-1} y_i \sin\varphi_i$ e $s_2 = \sum_{i=0}^{N-1} y_i \cos\varphi_i$
- Devido à simetria ortogonal da soma trigonométrica ao longo do ciclo completo, os termos cruzados anulam-se identicamente:
    
    $p_{12} = p_{21} = \frac{1}{2}\sum_{i=0}^{N-1} \sin(2\varphi_i) = 0$
    
- Os termos da diagonal principal reduzem-se a:
    
    $p_{11} = p_{22} = \frac{N}{2}$
    

Graças a essas simplificações analíticas, as equações finais para o cálculo de $I$ e $Q$ resultam em médias ponderadas:

$I = \frac{2}{N} \sum_{i=0}^{N-1} y_i \cdot \sin(i \cdot \Delta\varphi)$

$Q = \frac{2}{N} \sum_{i=0}^{N-1} y_i \cdot \cos(i \cdot \Delta\varphi)$

*(Os coeficientes de seno e cosseno dependem apenas de constantes conhecidas previamente e são pré-calculados em tabelas de busca / lookup tables dentro da FPGA)*.

### 4. Vantagens do Non-IQ Sampling

- **Deslocamento dos Harmônicos:** Ao mudar a razão de amostragem, os harmônicos de ordens superiores deixam de dobrar sobre a frequência fundamental $f_{IF}$. Eles são distribuídos para outras posições do espectro onde podem ser isolados e removidos por filtros digitais.
- **Rejeição de Ruído e Incertezas:** Como o cálculo faz a média sobre $N$ pontos distintos do círculo de fase, os erros de não linearidade do ADC (DNL/INL), ruídos de quantização, offset DC e jitter de clock são fortemente atenuados estatisticamente.

### 5. O Preço a Pagar: Latência vs. Linearidade

O principal compromisso (*trade-off*) do *Non-IQ sampling* é a **latência temporal**:

- No *IQ sampling* tradicional, bastam 2 amostras consecutivas para estimar $I$ e $Q$ instantaneamente.
- No *Non-IQ sampling*, o algoritmo necessita aguardar o acúmulo de todas as $N$ amostras para calcular o somatório e entregar o valor de $I$ e $Q$.
- Além disso, a filtragem digital necessária para remover os harmônicos espalhados introduz atraso de grupo adicional na malha.

Por essa razão, em malhas de controle ultrarrápidas onde a latência mínima de atraso puro é o fator crítico de estabilidade, o *IQ sampling* de $90^\circ$ ainda é frequentemente preferido; quando se exige máxima precisão linear e rejeição de harmônicos à custa de alguma velocidade de resposta, utiliza-se o *Non-IQ sampling*.