# Decibéis

Quase todo gráfico de espectro deste repositório tem o eixo vertical em decibéis: a resposta do FIR, os lóbulos do CIC, a família de espúrios do Mixer, o SFDR. Este texto explica o que o dB é, de onde vêm os fatores 10 e 20, e como ler um desses gráficos sem tropeçar.

### 1. Por que uma escala logarítmica

Um filtro passa-baixa deixa passar a amplitude 1 na faixa de passagem e algo como 0,001 ou 0,0001 na faixa de rejeição. Num eixo linear de 0 a 1, tudo abaixo de 0,01 vira uma linha colada no zero: os lóbulos da faixa de rejeição — justamente o que diz se o filtro é bom ou ruim — ficam menores que um pixel.

A escala logarítmica resolve isso dando **o mesmo espaço na tela a cada fator de 10**: de 1 a 0,1 ocupa tanto quanto de 0,001 a 0,0001. Assim, a faixa de passagem e a de rejeição cabem lado a lado, ambas legíveis.

### 2. O decibel é uma razão

Um dB nunca é um valor sozinho: ele **compara** duas grandezas. Na definição original, a razão é entre potências:

$\text{dB} = 10\,\log_{10}\dfrac{P_{\text{saída}}}{P_{\text{entrada}}}$

O logaritmo de base 10 conta **quantos fatores de 10** cabem na razão:

| razão de potência | 0,0001 | 0,001 | 0,01 | 0,1 | 1 | 10 | 100 |
|---|---|---|---|---|---|---|---|
| em dB | −40 | −30 | −20 | −10 | **0** | +10 | +20 |

Multiplicar por 10 é somar 10 dB; dividir por 10 é subtrair 10 dB. Uma razão igual a 1 — nada mudou — é exatamente **0 dB**. Valores negativos significam atenuação; positivos, ganho. A grandeza medida (potência, amplitude, $|H|$) nunca é negativa; o que fica negativo é o logaritmo de um número menor que 1.

### 3. Potência ou amplitude: o 10 e o 20

Num gráfico de filtro mede-se a **amplitude** (tensão), não a potência. Como a potência é proporcional ao quadrado da amplitude ($P = V^2/R$):

$10\,\log_{10}\dfrac{P_s}{P_e} = 10\,\log_{10}\left(\dfrac{A_s}{A_e}\right)^2 = 20\,\log_{10}\dfrac{A_s}{A_e}$

O quadrado sai do logaritmo como um fator 2. Daí a regra:

- **potência** → $10\cdot\log_{10}$;
- **amplitude** (tensão, corrente, $|H|$) → $20\cdot\log_{10}$.

As duas fórmulas dão **o mesmo número de dB para o mesmo sinal**. Se a amplitude cai à metade, a potência cai a um quarto: $20\log_{10}(0{,}5) = 10\log_{10}(0{,}25) = -6{,}02$ dB. Usar a fórmula errada é um erro comum — e dá exatamente a metade (ou o dobro) dos dB certos.

### 4. A tabela de bolso

| dB | amplitude | potência |
|---|---|---|
| 0 | 1 | 1 |
| −3 | 0,707 | 0,5 |
| −6 | 0,5 | 0,25 |
| −10 | 0,316 | 0,1 |
| −20 | 0,1 | 0,01 |
| −40 | 0,01 | 0,0001 |
| −60 | 0,001 | 0,000001 |

Três regras saem dela e resolvem quase toda leitura:

- **−6 dB → amplitude ÷ 2**;
- **−20 dB → amplitude ÷ 10** (então −60 dB é ÷ 1000);
- **−3 dB → potência ÷ 2** — é o critério usual da **frequência de corte** de um filtro.

### 5. Ganhos em cascata viram soma

Numa cadeia de blocos, os ganhos lineares se **multiplicam**; em dB, se **somam**. Exemplo com 1 mW de entrada, um amplificador de +20 dB, um cabo de −3 dB e um atenuador de −10 dB:

- linear: $1\ \text{mW}\times 100 \times 0{,}5 \times 0{,}1 = 5\ \text{mW}$;
- em dB: $0\ \text{dBm} + 20 - 3 - 10 = 7\ \text{dBm}$ — e 7 dBm é exatamente 5 mW.

É por isso que cadeias de RF e orçamentos de enlace são feitos em dB: a conta se faz de cabeça.

### 6. dB com sobrenome: dBm, dBc e dBFS

Quando a referência é fixa, o dB ganha uma letra que diz **contra o que** se compara:

- **dBm** — relativo a 1 mW. Vira uma unidade de potência: 0 dBm = 1 mW, +30 dBm = 1 W, −30 dBm = 1 µW. De 1 pW (−90 dBm, um sinal fraco num receptor) a 100 kW (+80 dBm, a ordem de um amplificador de potência de RF) são 17 fatores de 10, que cabem numa régua de 170 dB.
- **dBc** — relativo à portadora, o sinal que interessa. Um espúrio em −40 dBc tem 1% da amplitude da portadora. É a unidade do SFDR do [Mixer](../6%20-%20Mixer/Mixer.md), e no [IQ sampling](../7%20-%20Detecção%20de%20amplitude%20e%20fase%20em%20RF/1%20-%20IQ%20sampling/IQ%20sampling.md) uma 3ª harmônica em −40 dBc vira 0,57° de erro de fase.
- **dBFS** — relativo ao fundo de escala (*full scale*) do conversor. Com a relação sinal-ruído de quantização $\text{SQNR} \approx 6{,}02\,B + 1{,}76$ dB, um ADC de 16 bits tem o piso de ruído em ≈ −98 dBFS.

### 7. Lendo um gráfico de verdade

O gráfico da cena "O custo" do [Filtro FIR](../7%20-%20Detecção%20de%20amplitude%20e%20fase%20em%20RF/3%20-%20Digital%20Down%20Conversion/3%20-%20Filtro%20FIR/Filtro%20FIR.md) mostra o mesmo passa-baixa (janela de Hamming, corte em $0{,}15\,f_s$) com 11, 31 e 101 coeficientes. Lido por partes:

| | antes do corte | no corte | em $f_s/4$ | em $f_s/2$ |
|---|---|---|---|---|
| N = 11 | 0 dB | −6 dB | **−22 dB** (sobra 8%) | −46 dB |
| N = 31 | 0 dB | −6 dB | **−59 dB** (sobra 0,11%) | −56 dB |
| N = 101 | 0 dB | −6 dB | **−64 dB** (sobra 0,065%) | −72 dB |

1. **Faixa de passagem** — as três curvas em 0 dB: o sinal útil passa intacto.
2. **Corte** — as três passam por −6 dB, ou seja, metade da amplitude. É uma característica do projeto por janela.
3. **Transição** — o de 101 taps despenca logo depois do corte; o de 11 desce devagar e ainda deixa passar 8% da amplitude em $f_s/4$. Em números concretos, uma interferência de 1 V em $f_s/4$ sai com 79 mV, 1,1 mV e 0,65 mV, respectivamente. É o "custo" do título: corte abrupto exige muitos taps.
4. **Faixa de rejeição** — as ondulações são lóbulos; o que importa é o topo deles, o pior caso.
5. **Espetos até o piso** — não são "picos negativos": são frequências em que a resposta vale exatamente zero. Como $\log(0) = -\infty$, o gráfico corta no piso (−90 dB).

---

**Animação correspondente:** [`decibeis.py`](../../src/9%20-%20Decibéis/decibeis.py), cena `Decibeis`.
