# Filtro CIC

Na eletrônica e telecomunicações, o filtro CIC (*Cascaded Integrator-Comb*) é uma classe especial de filtro que altera a taxa de amostragem de um sinal (diminuindo ou aumentando). Ele opera sem usar multiplicadores, o que o torna incrivelmente eficiente em hardware (como chips FPGA ou ASICs) para aplicações de rádio digital e processamento de áudio. 

**Função principal:** Realizar *decimation* (redução da taxa de amostragem) ou *interpolation* (aumento da taxa de amostragem).

**Como funciona:** Ele é composto por duas partes em cascata: uma parte integradora e uma parte pente (*comb*). Geralmente, reduz taxas de amostragem muito altas para valores intermediários, economizando poder computacional antes do uso de filtros FIR tradicionais.

## 1. O Integrador

O Integrador é o bloco que faz o trabalho bruto de guardar absolutamente tudo o que entra. Matematicamente, ele é a soma contínua de todo o histórico do sinal desde que o sistema foi ligado.

- **No exemplo:** Quando o sinal chega no instante 4, o integrador pegou a amostra nova ($x[4]$) e somou com todo o seu passado:
    
    $I[4] = x[4] + x[3] + x[2] + x[1] + x[0]$
    
- **O seu papel:** Sozinho, o integrador não filtra nada. Ele apenas acumula os dados em alta velocidade, deixando o valor crescer indefinidamente (causando um *overflow* proposital no limite de bits do hardware).

## 2. O Comb

O Comb (pente) é o bloco que "puxa o freio". A função dele é olhar para o valor gigante acumulado do Integrador agora e subtrair o valor que ele tinha no passado (neste caso, 4 amostras atrás).

- **No exemplo:** A equação $y[n] = I[n] - I[n-4]$ atua como uma tesoura.
- **O seu papel:** Ao fazer a equação $(x[4] + x[3] + x[2] + x[1] + x[0]) - (x[0])$, ele anula o $x[0]$ e corta o passado distante. Ele transforma aquela acumulação infinita em uma **janela limitada e precisa de 4 amostras**:
    
    $y[4] = x[4] + x[3] + x[2] + x[1]$
    

## 3. O Efeito de Filtragem (A Média Móvel)

É aqui que a mágica acontece. O Integrador e o Comb, trabalhando juntos, formaram um somatório de uma janela fechada (uma média móvel). E é essa janela que atua como o **filtro passa-baixa**, distinguindo o que é ruído do que é sinal útil.

### Destruindo o Ruído (Cenário de Alta Frequência)

O ruído de alta frequência varia muito rápido. A cada instante ele muda de fase (sobe e desce).

- **Entrada rápida:** `+1, -1, +1, -1`
- **Ação dos blocos:** Como a janela matemática do CIC é obrigada a somar esses 4 itens juntos, os picos positivos encontram os vales negativos no mesmo exato momento dentro da equação.
- **Resultado ($0$):** O ruído se auto-cancela. O filtro barrou com sucesso a alta frequência.

### Preservando o Sinal (Cenário de Baixa Frequência)

O seu sinal útil (a banda base onde está a informação que você quer demodular) varia de forma extremamente lenta. O "topo" de uma onda de baixa frequência dura dezenas ou centenas de amostras.

- **Entrada lenta:** `+1, +1, +1, +1`
- **Ação dos blocos:** Como a onda quase não mudou de valor durante essas 4 amostras, não há nada negativo para cancelar a soma.
- **Resultado ($4$):** A soma se acumula perfeitamente. O sinal sobrevive ao filtro. Ele sai 4 vezes maior (o que chamamos de *ganho intrínseco* do filtro), mas a forma da onda e a informação continuam intactas.

> **E como a Decimação se encaixa nesse exemplo?**
> 
> 
> No exemplo, assumimos um atraso de $D=4$ para o bloco Comb. Em um hardware real (como no FPGA), nós inserimos o **Decimador** entre o Integrador e o Comb e reduzimos a taxa de amostragem (velocidade do clock) em 4 vezes.
> 
> Isso faz com que o Comb, mesmo olhando apenas $1$ amostra para trás no seu novo "tempo lento", esteja na verdade subtraindo um valor de $4$ amostras atrás do "tempo rápido" original. O resultado da equação e o efeito de cancelamento das ondas ficam exatamente idênticos aos do seu exemplo matemático.
>