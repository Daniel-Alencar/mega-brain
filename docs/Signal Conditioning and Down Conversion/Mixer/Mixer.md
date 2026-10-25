# Mixer

O misturador (*mixer*) é o componente que move um sinal de uma frequência para outra, preservando amplitude e fase. É a peça central da conversão para baixo (*down-conversion*) que antecede o ADC e da conversão para cima (*up-conversion*) que segue o DAC.

O texto responde a uma pergunta só: **por que um componente cuja função é multiplicar dois sinais acaba produzindo uma família inteira de frequências indesejadas** — e o que muda quando a mesma operação é feita dentro de um FPGA.

Exemplo numérico usado em todo o documento e na animação: $f_{RF} = 100$ MHz, $f_{LO} = 130$ MHz, portanto $f_{IF} = 30$ MHz.

### 1. O mixer ideal

O mixer ideal entrega o produto ponto a ponto dos dois sinais de entrada:

$v_{IF}(t) = v_{RF}(t) \cdot v_{LO}(t)$

O produto de dois cossenos não é um sinal novo qualquer: pela identidade trigonométrica, ele é a **soma de exatamente duas senoides**.

$\cos(\omega_{RF}t)\cos(\omega_{LO}t) = \tfrac{1}{2}\cos[(\omega_{LO}-\omega_{RF})t] + \tfrac{1}{2}\cos[(\omega_{LO}+\omega_{RF})t]$

No espectro, isso é o retrato mais simples possível: duas raias, em $|f_{LO} - f_{RF}| = 30$ MHz e em $f_{LO} + f_{RF} = 230$ MHz. Nenhum harmônico, nenhum vazamento das portadoras originais.

Esse é o alvo. A questão é se o hardware consegue atingi-lo.

### 2. Nenhum componente analógico multiplica tensões

Não existe componente passivo que multiplique duas tensões. O que existe são dispositivos com curvas características $I \times V$ suaves — exponenciais em diodos e transistores bipolares, quadráticas em FETs:

$i = I_s\left(e^{v/V_T} - 1\right)$

Expandindo essa curva em série de Taylor em torno de um ponto de operação DC, obtém-se um polinômio:

$v_{out}(t) = a\,v_{in}(t) + b\,v_{in}^2(t) + c\,v_{in}^3(t) + \dots$

E — este é o ponto decisivo — os dois sinais entram na não linearidade **somados**, nunca multiplicados:

$v_{in} = v_{RF} + v_{LO}$

A mistura que se deseja aparecerá como **efeito colateral** da deformação que a curva impõe à soma.

### 3. Quem gera o quê

Cada potência do polinômio é responsável por um grupo específico de frequências na saída.

#### Termo linear: $a\,v_{in}$ — vazamento

$a(v_{RF} + v_{LO}) = a\cos(\omega_{RF}t) + a\cos(\omega_{LO}t)$

Não cria frequência nova: é a causa física do **vazamento das portadoras** para a saída (as raias em 100 e 130 MHz). Num mixer ideal, nada disso deveria aparecer.

#### Termo quadrático: $b\,v_{in}^2$ — a mistura desejada

$b(v_{RF} + v_{LO})^2 = b\,v_{RF}^2 + 2b\,(v_{RF}\,v_{LO}) + b\,v_{LO}^2$

O termo do meio é a multiplicação pura, e dele sai o sinal útil:

$2b\cos(\omega_{RF}t)\cos(\omega_{LO}t) = b\cos[(\omega_{LO}-\omega_{RF})t] + b\cos[(\omega_{LO}+\omega_{RF})t]$

Os outros dois termos, pela identidade $\cos^2 x = \frac{1+\cos 2x}{2}$, geram tensão DC (offset) e os segundos harmônicos em $2f_{RF}$ e $2f_{LO}$.

> É o termo **quadrático** que produz a IF. A multiplicação não é a operação do componente: é um subproduto de ordem 2 da sua não linearidade.

#### Termo cúbico: $c\,v_{in}^3$ — intermodulação e compressão

$(v_{RF} + v_{LO})^3 = v_{RF}^3 + 3v_{RF}^2v_{LO} + 3v_{RF}v_{LO}^2 + v_{LO}^3$

- os produtos cruzados geram $2f_{LO} \pm f_{RF}$ e $2f_{RF} \pm f_{LO}$ — no exemplo, $2(130) - 100 = \mathbf{160}$ MHz;
- os cubos isolados geram os terceiros harmônicos $3f_{RF}$ e $3f_{LO}$;
- parte do termo cúbico cai **de volta sobre as fundamentais**, somando-se em contrafase ao sinal. Como $c < 0$ em dispositivos reais, o ganho cai à medida que a potência de entrada sobe: é a **compressão de ganho**, parametrizada pelo P1dB.

### 4. A família $m f_{RF} \pm n f_{LO}$

Generalizando, a expansão de ordem $k$ produz

$(v_{RF} + v_{LO})^k = \sum_{m+n=k} \binom{k}{m} v_{RF}^m\,v_{LO}^n$

e cada parcela cai em

$f_{esp\acute{u}rio} = |\,m\,f_{RF} \pm n\,f_{LO}\,|, \qquad \text{ordem} = m + |n|$

Como o diodo real é exponencial (série infinita), $m$ e $n$ não param em 3: a família é infinita, limitada apenas pelo piso de ruído. As amplitudes decaem com a ordem, mas há raias por todo o eixo.

| Raia | $(m,n)$ | Origem | Status |
|---|---|---|---|
| IF (30 MHz) | $(1,-1)$ | termo quadrático | **sinal útil** |
| RF, LO | $(1,0)$, $(0,-1)$ | termo linear | vazamento |
| soma (230 MHz) | $(1,1)$ | termo quadrático | banda soma |
| 2RF, 2LO | $(2,0)$, $(0,-2)$ | termo quadrático | harmônicos + DC |
| 2RF−LO (70 MHz) | $(2,-1)$ | termo cúbico | IMD3 — a mais próxima da IF |
| 3RF, 3LO | $(3,0)$, $(0,-3)$ | termo cúbico | terceiros harmônicos |
| 2IF, 3IF | $(2,-2)$, $(3,-3)$ | ordens 4 e 6 | harmônicos da própria IF |

Com os coeficientes usados na simulação, o SFDR resultante é de apenas **≈ 5 dBc**: o maior espúrio (o vazamento de LO) está quase no nível da IF. Tudo o que não é a raia útil precisa ser filtrado depois.

#### Formas usuais de reduzir os espúrios

1. **Mixer duplamente balanceado** — a simetria do quarteto de diodos cancela por construção os termos de LO e RF isolados, dando 30–40 dB de isolamento sem custo de filtro.
2. **Planejamento de frequências** (*spur chart*) — escolher $f_{LO}$ e $f_{IF}$ de modo que os espúrios de ordem baixa caiam fora da banda de interesse. É projeto, não filtragem: custo zero em latência.
3. **Recuo do P1dB** — operar bem abaixo da compressão reduz os termos de ordem alta mais rápido que o fundamental (o IMD3 cai 3 dB por dB de recuo), ao custo de SNR.

### 5. A frequência imagem não é defeito do componente

Considere dois sinais de entrada simétricos em torno do LO: o desejado em 100 MHz e outro em $2f_{LO} - f_{RF} = 160$ MHz. Ambos distam 30 MHz do LO, portanto:

$|f_{LO} - f_{RF}| = |f_{LO} - f_{IM}| = 30\ \text{MHz}$

Os dois caem exatamente sobre a mesma IF e se somam lá. **Nenhum filtro após o mixer os separa** — eles estão na mesma frequência.

O ponto essencial: isso acontece mesmo no multiplicador matematicamente perfeito. Não é um defeito de linearidade, e sim consequência de a mistura ser **real**. Um cosseno é a soma de dois fasores girando em sentidos opostos:

$\cos\omega t = \tfrac{1}{2}\left(e^{+j\omega t} + e^{-j\omega t}\right)$

O fasor $+\omega$ desloca o espectro para um lado, o $-\omega$ para o outro, e os dois deslocamentos se sobrepõem na IF. A imagem nasce do fasor negativo.

A solução é usar um LO que gire num sentido só — $e^{-j\omega_{LO}t}$ —, o que exige dois multiplicadores, produzindo os canais I e Q. É o que a mistura complexa do DDC faz, e por construção a imagem é rejeitada. Alternativamente, filtra-se a imagem **antes** do mixer, com um filtro de imagem na entrada de RF.

| Efeito | Causa | Existe no mixer ideal? | Existe na mistura I/Q? |
|---|---|---|---|
| soma e diferença | trigonometria | sim | sim (só uma delas) |
| frequência imagem | mistura **real** | **sim** | não |
| vazamento, harmônicos, IMD | **não linearidade** | não | não |

### 6. No FPGA a multiplicação é de verdade

No domínio digital o sinal já é um número inteiro, e a multiplicação é feita por um bloco aritmético dedicado — o DSP slice (DSP48E2 na Xilinx, DSP block na Intel), um multiplicador de 27×18 bits com acumulador de 48 bits. Guardando o produto completo, o resultado é **bit-exato**: não há ponto de polarização, não há P1dB, não há IP3.

A cadeia típica de um DDC é:

```
ADC ──► [ × ] ──► CIC ──► FIR ──► I, Q
           ▲
         DDS (acumulador de fase + LUT cos/sen)
```

Da família da seção 4, nada sobrevive: sem termo linear não há vazamento, sem termo cúbico não há intermodulação nem compressão. Restam apenas os dois produtos que a trigonometria exige.

#### Mas "preciso" não é "perfeito"

As imperfeições mudam de natureza: saem da física do semicondutor e vão para a **aritmética finita**.

| Fonte | Efeito | Ordem de grandeza |
|---|---|---|
| truncamento de fase do DDS | raias discretas | $\approx -6{,}02\,B$ dBc, $B$ = bits de endereço da LUT |
| quantização de amplitude da LUT | piso de ruído | $\approx -(6{,}02W + 1{,}76)$ dB |
| truncamento do produto | ruído de quantização | somável por estágio |
| overflow sem saturação | *wrap-around*, distorção grosseira | evitar com guard bits |

Com acumulador de 32 bits, 14 bits de endereço e 16 bits de amplitude, a simulação numérica mede **SFDR ≈ 84 dBc** — exatamente os $-6{,}02 \times 14 = -84{,}3$ dBc previstos pela teoria de truncamento de fase. O espúrio digital é projetado no papel e não depende de temperatura nem de dispersão de fabricação.

#### O caso $f_{LO} = f_s/4$

Escolhendo o LO em exatamente um quarto da taxa de amostragem, as sequências do oscilador degeneram:

$\cos(2\pi n/4) = \{1, 0, -1, 0\}, \qquad \sin(2\pi n/4) = \{0, 1, 0, -1\}$

Multiplicar por 0 ou $\pm 1$ é trocar sinal e multiplexar: a mistura fica exata, sem LUT e sem DSP slice. É prática comum em front-ends de BPM e LLRF amarrar o clock do ADC a $4\times$ a IF por esse motivo.

### 7. O preço da limpeza: atraso de grupo

Todo espúrio que existe precisa ser filtrado, e filtrar custa atraso:

$\tau_g(\omega) = -\frac{d\phi(\omega)}{d\omega}$

Filtros com corte abrupto (elíptico, Chebyshev de ordem alta) apresentam **picos de atraso de grupo perto da banda de passagem**, e um atraso que varia com a frequência deforma o envelope do sinal. Na simulação, um elíptico analógico de ordem 7 (80 dB em 60 MHz) atrasa 40 ns na IF, mas chega a 91 ns no pico — variação de 2,3× dentro da própria banda.

Um FIR de fase linear tem atraso de grupo **constante e conhecido antes da síntese**:

$\tau_g = \frac{N-1}{2}\,T_s$

Vale registrar com honestidade: o FIR não é necessariamente mais rápido. Na mesma especificação, a cadeia CIC + FIR do DDC totaliza 113 ns contra os 40 ns do elíptico na IF. A vantagem não é latência menor, e sim **atraso plano e previsível**, que não deforma o envelope.

Isso importa porque, numa malha de realimentação (FOFB, LLRF), o atraso entra direto na estabilidade:

$\Delta\phi = -\omega\,\tau, \qquad f_{BW} \lesssim \frac{1}{10\,\tau_{total}}$

Cada nanossegundo gasto filtrando é banda de controle perdida. E é justamente aqui que o mixer digital ganha: **o que não existe não precisa ser filtrado**.

---

**Conclusão prática.** O polinômio de Taylor nunca desaparece do sistema completo — ele apenas deixa de estar no estágio de mistura, migrando para o front-end analógico e para a não linearidade do próprio ADC (que tipicamente limita o SFDR do sistema em 70–85 dBc). Por isso a arquitetura moderna empurra o ADC o mais perto possível do pickup: cada mixer analógico eliminado é uma família inteira de espúrios a menos para filtrar, e um filtro a menos no orçamento de latência da malha.

**Animação correspondente:** [`Mixer.py`](../../../src/Signal%20Conditioning%20and%20Down%20Conversion/Mixer/Mixer.py), cena `Mixer`.

**Simulação numérica:** [`Mixer_plot.py`](../../../src/Signal%20Conditioning%20and%20Down%20Conversion/Mixer/Mixer_plot.py) gera os quatro espectros, identifica automaticamente o par $(m,n)$ de cada raia e mede o SFDR e o atraso de grupo.
