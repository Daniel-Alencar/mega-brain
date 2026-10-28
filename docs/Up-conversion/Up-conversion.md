# Up-conversion

Baseado na seção 4 de T. Schilcher, *RF applications in digital signal processing*
([books/Schilcher.pdf](../../books/Schilcher.pdf), p. 266–268, Figs. 21 a 24).

Em sistemas de controle de RF (realimentação ou *feed-forward*) é preciso fazer o
caminho inverso da detecção: converter um sinal digital de banda base em um sinal
de RF real, com amplitude e fase exatas. Esse caminho é a **up-conversion**.

O ideal seria um único DAC sintetizando diretamente a portadora (*Direct Digital
Synthesis*, DDS). Só que os DACs de hoje não entregam, ao mesmo tempo, a precisão
e a velocidade exigidas por sinais de centenas de MHz. Na prática se usa uma
combinação de DACs e mixers, em um de dois arranjos: **homodino** (direto) ou
**heteródino** (por uma frequência intermediária).

Exemplo numérico usado aqui e na animação: $f_{IF} = 20$ MHz, $f_{LO} = 480$ MHz,
$f_{RF} = 500$ MHz e, portanto, imagem em 460 MHz.

## 1. A ideia que sustenta tudo: I e Q são as coordenadas do fasor

Uma portadora qualquer pode ser decomposta em suas componentes seno e cosseno:

$$RF_{out}(t) = I \cdot A_{LO}\sin\omega t + Q \cdot A_{LO}\cos\omega t = A_{out}\sin(\omega t + \varphi_0)$$

Somar duas portadoras de mesma frequência em quadratura **não** gera duas ondas:
gera uma só, cuja amplitude e fase são

$$A_{out} = A_{RF}\sqrt{I^2 + Q^2} \qquad \varphi_0 = \arctan\!\left(\frac{Q}{I}\right)$$

Ou seja: mexer em dois números é mexer na amplitude e na fase de uma única
portadora — exatamente as duas grandezas que o LLRF precisa controlar. As duas
modulações clássicas saem do mesmo par de entradas:

| | I(t) | Q(t) | efeito no fasor |
| --- | --- | --- | --- |
| **amplitude** | $A_0(t)\cos\varphi_0$ | $A_0(t)\sin\varphi_0$ | estica e encolhe, sem girar |
| **fase** | $A_0\cos\varphi_0(t)$ | $A_0\sin\varphi_0(t)$ | gira, com comprimento fixo |

## 2. Homodino (direto): o modulador vetorial

No arranjo homodino — também chamado direto ou de banda base — os sinais I e Q
são convertidos para analógico e multiplicados pelas componentes em fase e em
quadratura de um oscilador local. O LO é dividido por um **híbrido de 90°**, que
gera o seno para um ramo e o cosseno para o outro; os dois ramos são somados e o
resultado é o RF de saída. O bloco inteiro é conhecido como **modulador vetorial**
(Fig. 21).

Características:

- a frequência do LO **é** a frequência de RF desejada: não existe IF;
- no espectro, a banda base sobe inteira para a portadora — uma banda só,
  **sem frequência imagem** para filtrar;
- os mixers funcionam como **elementos de controle de amplitude**: I e Q dosam
  diretamente a amplitude de cada ramo;
- é o arranjo mais simples e mais barato, e por isso o mais difundido.

### Os erros que vêm junto

O preço é que tudo acontece em componentes analógicos, com as suas variações de
peça para peça e não linearidades — e todos esses erros entram **depois** do DAC,
onde o digital já não alcança:

| erro | o que acontece | como aparece no plano I-Q |
| --- | --- | --- |
| **offset de DC** em I ou Q | vazamento de portadora (*carrier leakage*): sai portadora mesmo com $I = Q = 0$ | o círculo sai do centro |
| **desbalanço de ganho** | um ramo amplifica mais que o outro; a fase passa a mexer na amplitude (*phase-to-amplitude modulation*) | o círculo vira elipse |
| **skew de quadratura** | o híbrido não entrega 90° exatos, e I e Q passam a se misturar | os eixos deixam de ser perpendiculares |
| **ruído de fase do LO** | a fase da portadora treme sozinha | o ponto deixa de ficar parado |

### Pré-distorção do skew

O skew é geométrico e previsível, então pode ser compensado no digital, antes dos
DACs. Chamando de $\varphi_S$ o desvio em relação aos 90°:

$$\begin{pmatrix} I_{out} \\ Q_{out} \end{pmatrix} = \frac{1}{\cos\varphi_S}
\begin{pmatrix} \cos\varphi_S & -\sin\varphi_S \\ 0 & 1 \end{pmatrix} \cdot
\begin{pmatrix} I_{in} \\ Q_{in} \end{pmatrix}$$

isto é, $I_{out} = I_{in} - \tan\varphi_S \cdot Q_{in}$ e $Q_{out} = Q_{in}/\cos\varphi_S$.
A entrada já sai "torta" do jeito certo para o analógico entortá-la de volta ao
lugar. É o primeiro exemplo de uma ideia recorrente no LLRF: **calibrar no
digital o defeito do analógico**.

## 3. Heteródino (IF up-conversion): banda dupla

No arranjo heteródino, a translação de I e Q para uma **frequência intermediária
acontece digitalmente**: um NCO fornece o seno e o cosseno de $f_{IF}$, os dois
canais são multiplicados e somados ainda dentro da FPGA, e um **único DAC**
entrega o sinal já modulado, centrado na IF (Fig. 22). Daí para frente é
analógico: um mixer e um LO levam a IF até o RF, com

$$f_{RF} = f_{LO} + f_{IF}$$

Só que multiplicar duas senoides sempre dá a soma **e** a diferença:

$$s_{IF}(t)\cdot\cos\omega_{LO}t = \tfrac{1}{2}\sin\big((\omega_{LO}+\omega_{IF})t+\varphi\big)
- \tfrac{1}{2}\sin\big((\omega_{LO}-\omega_{IF})t-\varphi\big)$$

Nasce então uma **frequência imagem** em $f_{LO} - f_{IF}$ (460 MHz no exemplo).
Por gerar as duas bandas, o esquema é chamado de **modulador de banda dupla**
(*double-sideband*), e exige um filtro passa-faixa que suprima a imagem — daí o
nome **método da filtragem**.

A troca em relação ao homodino:

- **a favor:** a quadratura é feita no digital, então não há desbalanço de ganho
  nem skew de quadratura para corrigir;
- **contra:** o DAC precisa de muito mais banda, ficando mais exposto a distorção
  harmônica e a *ripple* na banda de passagem.

## 4. Banda lateral única: cancelar em vez de filtrar

A alternativa para não precisar do filtro é o **modulador de banda lateral única**
(*single-sideband*, Fig. 23): I e Q sobem para a IF no digital, **cada um no seu
DAC**, e os dois sinais analógicos $I_{IF}$ e $Q_{IF}$ entram em um modulador
vetorial comum.

Cada ramo, sozinho, ainda gera as duas bandas:

$$\cos\omega_{IF}t \cdot \sin\omega_{LO}t = \tfrac{1}{2}\big[\sin(\omega_{LO}+\omega_{IF})t + \sin(\omega_{LO}-\omega_{IF})t\big]$$
$$\sin\omega_{IF}t \cdot \cos\omega_{LO}t = \tfrac{1}{2}\big[\sin(\omega_{LO}+\omega_{IF})t - \sin(\omega_{LO}-\omega_{IF})t\big]$$

A diferença está no sinal: a banda de baixo do ramo Q nasce **180° fora de fase**
em relação à do ramo I. Somando os dois no fim do modulador vetorial, as duas
bandas inferiores se cancelam e as superiores se reforçam (Fig. 24):

$$\text{soma} = \sin(\omega_{LO}+\omega_{IF})t$$

Na prática o cancelamento nunca é perfeito — desbalanço de ganho e skew de
quadratura voltam a atrapalhar, e sobra um resto em $f_{LO} - f_{IF}$. A razão
entre a banda desejada e esse resto é a **supressão de banda lateral**, medida em
[dBc].

## 5. Os três lado a lado

| | Homodino | Heteródino (banda dupla) | Banda lateral única |
| --- | --- | --- | --- |
| LO fica em | $f_{RF}$ = 500 MHz | $f_{LO}$ = 480 MHz | $f_{LO}$ = 480 MHz |
| imagem | não existe | sim, em 460 MHz | cancelada, sobra um resto |
| erros analógicos | ganho, skew e offset | só os do DAC | ganho e skew de novo |
| banda do DAC | banda base (folgada) | até a IF (apertada) | dois DACs, até a IF |
| filtro na saída | pouco exigente | obrigatório | leve |

Escolher entre eles é decidir onde se prefere pagar: em erro analógico depois do
DAC, ou em banda e linearidade dentro do próprio DAC.
