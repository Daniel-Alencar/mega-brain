# -*- coding: utf-8 -*-
"""
Mixer de RF: por que a multiplicação cria uma família inteira de espúrios
=========================================================================

Renderização (a partir da raiz do repositório):
    manim -pql "src/Signal Conditioning and Down Conversion/Mixer/mixer.py" Mixer   # rascunho
    manim -pqh "src/Signal Conditioning and Down Conversion/Mixer/mixer.py" Mixer   # final

Requer LaTeX (MathTex).

Roteiro:
    Abertura
    Cena 1 - O mixer ideal: o batimento É a soma de duas senoides novas
    Cena 2 - Nenhum componente analógico multiplica tensões (curva e Taylor)
    Cena 3 - Quem gera o quê: cada termo do polinômio preenche o espectro
    Cena 4 - A família m·f_RF ± n·f_LO, construída ordem por ordem
    Cena 5 - A frequência imagem: culpa do fasor negativo, não do componente
    Cena 6 - No FPGA a multiplicação é de verdade (DDS, quantização, f_s/4)
    Cena 7 - O preço da limpeza: atraso de grupo
    Resumo

Layout: a tela é dividida em faixas fixas para que nada se sobreponha.
    y > 3.0   : título da cena (canto superior esquerdo)
    Y_TOPO    : primeira linha de conteúdo (equação de cabeçalho)
    [Y_BASE, Y_TOPO] : área de desenho
    Y_LEGENDA : narração, uma linha por vez
"""

import math

import numpy as np
from manim import *
from scipy import signal as sig

# Paleta didática (fixa em todas as cenas)
COR_RF = BLUE_C          # sinal de RF
COR_LO = GOLD            # oscilador local
COR_IF = GREEN           # produto útil (IF e seus harmônicos)
COR_SOMA = TEAL          # banda soma
COR_VAZA = RED           # vazamento e harmônicos puros (m = 0 ou n = 0)
COR_IMD = BLUE_B         # intermodulação (m, n ≠ 0)
COR_IMG = ORANGE         # frequência imagem / sinal distorcido
COR_FPGA = PURPLE_B
COR_OK = GREEN_B
COR_EIXO = GREY_B
FUNDO = "#0e1117"

EIXO_CFG = {"include_tip": False, "stroke_width": 2, "color": COR_EIXO}

# Faixas de layout (unidades de cena; a tela vai de -4 a 4 em y)
Y_TOPO = 2.70            # nada de conteúdo acima disto: a linha do título mora em ~3.1
Y_BASE = -2.55           # nada de conteúdo abaixo disto: a narração mora em ~-3.5
LARG_MAX = 12.6          # largura máxima de qualquer fórmula

# Frequências do exemplo, em MHz
F_RF, F_LO, FS = 100.0, 130.0, 2000.0
F_IF = abs(F_LO - F_RF)          # 30 MHz
F_IMG = 2 * F_LO - F_RF          # 160 MHz
F_MAX = 500.0
N_FFT = 20000
COEFS = [0.1, 0.5, 0.08, 0.02, 0.006]    # a, b, c, d, e

# Frequências didáticas das cenas no domínio do tempo (ciclos por unidade de x).
# Guardam a mesma razão do caso real (100 e 130 MHz), mas desenháveis na tela.
FD_RF, FD_LO = 2.0, 2.6
FD_IF, FD_SOMA = FD_LO - FD_RF, FD_LO + FD_RF


# =============================================================================
# Utilitários de construção
# =============================================================================
def P(x, y):
    return np.array([x, y, 0.0])


def ajustar(m, largura=LARG_MAX):
    """Encolhe o mobject se ele for largo demais para a tela."""
    if m.width > largura:
        m.scale(largura / m.width)
    return m


def tex(s, cor=WHITE, tamanho=34):
    return MathTex(s, color=cor, font_size=tamanho)


def tex_partes(partes, tamanho=34):
    """Fórmula multicolorida. partes = [(tex, cor), ...]."""
    m = MathTex(*[p[0] for p in partes], font_size=tamanho)
    for sub, p in zip(m, partes):
        sub.set_color(p[1])
    return m


def fio(pontos, cor=WHITE, largura=3):
    g = VGroup(*[Line(pontos[k], pontos[k + 1], color=cor, stroke_width=largura)
                 for k in range(len(pontos) - 2)])
    g.add(Arrow(pontos[-2], pontos[-1], buff=0, color=cor, stroke_width=largura,
                max_tip_length_to_length_ratio=0.25,
                max_stroke_width_to_length_ratio=10))
    return g


def caixa_texto(rotulo, largura=1.6, altura=0.7, cor=WHITE, tamanho=20):
    r = RoundedRectangle(corner_radius=0.08, width=largura, height=altura,
                         color=cor, stroke_width=3)
    return VGroup(r, Text(rotulo, color=cor, font_size=tamanho).move_to(r))


def multiplicador(cor=WHITE, raio=0.32):
    """Símbolo do mixer: círculo com X."""
    c = Circle(radius=raio, color=cor, stroke_width=3)
    d = raio * 0.62
    x = VGroup(Line(P(-d, -d), P(d, d), color=cor, stroke_width=3),
               Line(P(-d, d), P(d, -d), color=cor, stroke_width=3))
    return VGroup(c, x.move_to(c))


def eixos(centro, largura, altura, x_range, y_range):
    return Axes(x_range=x_range, y_range=y_range, x_length=largura,
                y_length=altura, axis_config=EIXO_CFG).move_to(centro)


def rotulo_eixo(ax, mob):
    return mob.next_to(ax, UP, buff=0.08).align_to(ax, LEFT)


def polilinha(ax, xs, ys, cor, largura=3):
    return (VMobject()
            .set_points_as_corners([ax.c2p(a, b) for a, b in zip(xs, ys)])
            .set_stroke(cor, largura))


def curva(ax, func, cor, largura=3, n=600, x0=None, x1=None):
    a = ax.x_range[0] if x0 is None else x0
    b = ax.x_range[1] if x1 is None else x1
    xs = np.linspace(a, b, n)
    return polilinha(ax, xs, func(xs), cor, largura)


def haste(ax, x, y, cor, piso, largura=4):
    return Line(ax.c2p(x, piso), ax.c2p(x, y), color=cor, stroke_width=largura)


def marcar_x(ax, valores, y_base, tamanho=18):
    return VGroup(*[Text(f"{int(v)}", font_size=tamanho, color=GREY_B)
                    .next_to(ax.c2p(v, y_base), DOWN, buff=0.12)
                    for v in valores])


# ----------------------------------------------------- espectro do polinômio
def espectro(coefs):
    """Espectro em dB do polinômio aplicado a v_RF + v_LO."""
    t = np.arange(N_FFT) / FS
    v = np.cos(2 * np.pi * F_RF * t) + np.cos(2 * np.pi * F_LO * t)
    y = sum(c * v ** (k + 1) for k, c in enumerate(coefs))
    espec = np.abs(np.fft.rfft(y * np.hanning(N_FFT))) / (N_FFT / 4)
    return np.fft.rfftfreq(N_FFT, 1 / FS), 20 * np.log10(np.maximum(espec, 1e-9))


F_EIXO, DB_EIXO = espectro(COEFS)


def nivel_db(f_alvo):
    """Nível em dB da raia mais próxima de f_alvo."""
    return float(DB_EIXO[np.argmin(np.abs(F_EIXO - f_alvo))])


def rotular(m, n):
    """Nome usual da raia a partir do par (m, n)."""
    k = abs(n)
    if m == k and n < 0:
        return "IF" if m == 1 else f"{m}IF"
    if m == 0:
        return "LO" if k == 1 else f"{k}LO"
    if n == 0:
        return "RF" if m == 1 else f"{m}RF"
    t_rf = ("" if m == 1 else str(m)) + "RF"
    t_lo = ("" if k == 1 else str(k)) + "LO"
    return t_rf + ("+" if n > 0 else "−") + t_lo


def cor_raia(m, n):
    if m == abs(n) and n < 0:          # IF e seus harmônicos
        return COR_IF
    if (m, n) == (1, 1):               # banda soma
        return COR_SOMA
    if m == 0 or n == 0:               # vazamento e harmônicos puros
        return COR_VAZA
    return COR_IMD                     # intermodulação


def familia(ordem):
    """Raias (f, m, n) de uma dada ordem m + |n|, dentro do eixo, sem repetir."""
    vistas, saida = set(), []
    for m in range(ordem + 1):
        for n in range(-ordem, ordem + 1):
            if m + abs(n) != ordem or (m == 0 and n == 0):
                continue
            f = round(abs(m * F_RF + n * F_LO), 1)
            if f <= 1.0 or f > F_MAX or f in vistas:
                continue
            vistas.add(f)
            saida.append((f, m, n))
    return sorted(saida)


# =============================================================================
# Cena
# =============================================================================
class Mixer(Scene):
    def construct(self):
        self.camera.background_color = FUNDO
        self.abertura()
        self.cena_ideal()
        self.cena_diodo()
        self.cena_termos()
        self.cena_familia()
        self.cena_imagem()
        self.cena_digital()
        self.cena_filtro()
        self.cena_resumo()

    # ------------------------------------------------------------- utilidades
    def titulo_cena(self, texto):
        t = Text(texto, font_size=32, weight=BOLD).to_corner(UL, buff=0.35)
        linha = Line(t.get_corner(DL), t.get_corner(DR), color=COR_EIXO,
                     stroke_width=2).shift(DOWN * 0.12)
        self.play(Write(t), Create(linha), run_time=1.0)
        self.wait(0.5)
        return VGroup(t, linha)

    def legenda(self, texto, anterior=None, cor=GREY_A, pausa=None):
        """Narração no rodapé. Espera o tempo de leitura antes de prosseguir."""
        nova = ajustar(Text(texto, font_size=24, color=cor), 13.2)\
            .to_edge(DOWN, buff=0.35)
        if anterior is None:
            self.play(FadeIn(nova, shift=UP * 0.2), run_time=0.8)
        else:
            self.play(FadeOut(anterior, shift=UP * 0.2),
                      FadeIn(nova, shift=UP * 0.2), run_time=0.8)
        self.wait(pausa if pausa is not None else 0.5 + 0.024 * len(texto))
        return nova

    def limpar(self):
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.9)
        self.wait(0.3)

    # --------------------------------------------------- eixos de espectro
    def eixo_espectro(self, centro, largura=11.4, altura=3.0, piso=-80, topo=10,
                      rot_x=True, rot_y=True, tamanho=18):
        """Eixo de espectro em dB, com a linha de base no PISO.

        Com o eixo y indo de −80 a +10 dB, o Manim desenha o eixo x em 0 dB,
        isto é, no topo do gráfico — e ele cortava os rótulos das raias. Aqui
        o eixo automático fica invisível e a base é desenhada no piso.
        """
        ax = eixos(centro, largura, altura, [0, F_MAX, 100], [piso, topo, 20])
        ax.x_axis.set_opacity(0)
        base = Line(ax.c2p(0, piso), ax.c2p(F_MAX, piso), color=COR_EIXO,
                    stroke_width=2)
        tiques = VGroup(*[Line(ax.c2p(f, piso), ax.c2p(f, piso) + DOWN * 0.1,
                               color=COR_EIXO, stroke_width=2)
                          for f in range(0, int(F_MAX) + 1, 100)])
        marcas = VGroup(*[Text(f"{f}", font_size=tamanho, color=GREY_B)
                          .next_to(ax.c2p(f, piso), DOWN, buff=0.18)
                          for f in range(0, int(F_MAX) + 1, 100)])
        deco = VGroup(base, tiques, marcas)
        if rot_x:
            deco.add(Text("frequência [MHz]", font_size=20, color=GREY_A)
                     .next_to(marcas, DOWN, buff=0.12))
        if rot_y:
            deco.add(Text("amplitude [dB]", font_size=19, color=GREY_A)
                     .rotate(PI / 2).next_to(ax, LEFT, buff=0.12))
        ax.ocupado = []      # rótulos já postos na faixa: (x0, x1, nível)
        ax.guias = []        # linhas-guia já postas: (x, nível do rótulo)
        return ax, deco

    def reservar(self, ax, x0, x1, niveis, passo=0.3):
        """Marca um trecho da faixa de rótulos como ocupado (ex.: um título)."""
        base = ax.c2p(0, ax.y_range[1])[1] + 0.3
        ax.ocupado.append((x0, x1, base - 0.2, base + niveis * passo))

    def desenhar_raias(self, ax, itens, piso, tamanho=16, destaque=None,
                       opacidade=1.0, max_niveis=3, passo=0.3):
        """Raias com os rótulos numa faixa ACIMA do gráfico.

        Cada rótulo procura uma posição livre: primeiro com linha-guia
        vertical, no nível mais baixo possível; se nenhuma servir, desloca o
        rótulo para o lado com a guia inclinada. Uma posição só é aceita se
          - a caixa do rótulo não encosta em nada já ocupado (rótulos,
            reservas, hastes);
          - a guia não atravessa nenhum rótulo nem haste vizinha;
          - nenhuma guia já existente atravessa a caixa do rótulo.
        O estado fica guardado no eixo: chamadas sucessivas no mesmo gráfico
        (ordem 1, depois 2, ...) também respeitam o que já está lá. Se não
        houver lugar, a raia fica sem rótulo em vez de escrever por cima.
        """
        def sobrepoe(a, b):
            return a[0] < b[1] and b[0] < a[1] and a[2] < b[3] and b[2] < a[3]

        def cruza(p0, p1, caixa, folga=0.03):
            x0, x1, y0, y1 = caixa
            for t in np.linspace(0, 1, 30):
                x = p0[0] + t * (p1[0] - p0[0])
                y = p0[1] + t * (p1[1] - p0[1])
                if x0 - folga < x < x1 + folga and y0 - folga < y < y1 + folga:
                    return True
            return False

        base = ax.c2p(0, ax.y_range[1])[1] + 0.3
        x_min, x_max = ax.c2p(0, piso)[0], ax.c2p(F_MAX, piso)[0]
        y_piso = ax.c2p(0, piso)[1]
        grupo = VGroup()
        for f, m, n in sorted(itens):
            db = max(nivel_db(f), piso + 4)
            if db < piso + 2:
                continue
            cor = cor_raia(m, n)
            ponta = ax.c2p(f, db)
            x = ponta[0]
            rot = Text(rotular(m, n), font_size=tamanho, color=cor)
            meia, meia_h = rot.width / 2 + 0.07, rot.height / 2 + 0.04
            escolhido = None
            for dx in (0.0, 0.32, -0.32, 0.64, -0.64):
                for nivel in range(max_niveis):
                    xc, y = x + dx, base + nivel * passo
                    caixa = (xc - meia, xc + meia, y - meia_h, y + meia_h)
                    if caixa[0] < x_min - 0.2 or caixa[1] > x_max + 0.4:
                        continue
                    pe = (xc, y - meia_h)
                    if any(sobrepoe(caixa, c) for c in ax.ocupado):
                        continue
                    if any(cruza(ponta, pe, c) for c in ax.ocupado):
                        continue
                    if any(cruza(g0, g1, caixa) for g0, g1 in ax.guias):
                        continue
                    escolhido = (xc, y, caixa, pe)
                    break
                if escolhido:
                    break
            partes = [haste(ax, f, db, cor, piso)]
            if escolhido:
                xc, y, caixa, pe = escolhido
                rot.move_to([xc, y, 0])
                ax.ocupado.append(caixa)
                ax.guias.append((ponta, pe))
                partes.append(Line(ponta, np.array([pe[0], pe[1], 0.0]),
                                   color=cor, stroke_width=1.2).set_opacity(0.45))
                partes.append(rot)
            # a haste também passa a ser obstáculo para as guias seguintes
            ax.ocupado.append((x - 0.03, x + 0.03, y_piso, ponta[1]))
            grupo.add(VGroup(*partes))
        if opacidade < 1.0:
            grupo.set_opacity(opacidade)
        self.play(LaggedStart(*[AnimationGroup(
            GrowFromEdge(g[0], DOWN),
            *([Create(g[1]), FadeIn(g[2])] if len(g) > 1 else []))
            for g in grupo], lag_ratio=0.3),
            run_time=0.5 + 0.35 * len(grupo))
        if destaque is not None:
            self.play(*[Indicate(g[0], color=destaque, scale_factor=1.12)
                        for g in grupo], run_time=1.0)
        return grupo

    # ---------------------------------------------------------------- abertura
    def abertura(self):
        titulo = Text("Mixer de RF", font_size=64, weight=BOLD)
        sub = Text("por que multiplicar dois sinais cria uma família inteira "
                   "de espúrios", font_size=28, color=GREY_A)
        eq = tex_partes([(r"v_{IF}(t) = ", WHITE), (r"v_{RF}(t)", COR_RF),
                         (r"\cdot", WHITE), (r"v_{LO}(t)", COR_LO)], 42)
        g = VGroup(titulo, sub, eq).arrange(DOWN, buff=0.5)
        self.play(Write(titulo), run_time=1.6)
        self.play(FadeIn(sub, shift=UP * 0.2), run_time=1.0)
        self.wait(1.2)
        self.play(FadeIn(eq, shift=UP * 0.2), run_time=1.0)
        self.wait(2.0)
        self.play(FadeOut(g), run_time=0.9)

    # ================================================================== CENA 1
    def cena_ideal(self):
        self.titulo_cena("1 · O mixer ideal: multiplicação pura")

        # --- Etapa A: o diagrama, sozinho e centralizado --------------------
        mix = multiplicador().move_to(P(0, 0.4))
        e_rf = tex(r"v_{RF}", COR_RF, 34).next_to(mix, LEFT, buff=1.6)
        e_lo = tex(r"v_{LO}", COR_LO, 34).next_to(mix, DOWN, buff=1.5)
        s_if = tex(r"v_{IF}", COR_IF, 34).next_to(mix, RIGHT, buff=1.6)
        fios = VGroup(
            fio([e_rf.get_right() + RIGHT * 0.2, mix.get_left()], COR_RF),
            fio([e_lo.get_top() + UP * 0.2, mix.get_bottom()], COR_LO),
            fio([mix.get_right(), s_if.get_left() + LEFT * 0.2], COR_IF))
        r_rf = Text("o sinal que chegou da antena", font_size=20, color=COR_RF)\
            .next_to(e_rf, UP, buff=0.3)
        r_lo = Text("um oscilador que nós controlamos", font_size=20,
                    color=COR_LO).next_to(e_lo, DOWN, buff=0.3)
        r_if = Text("o mesmo sinal, em outra frequência", font_size=20,
                    color=COR_IF).next_to(s_if, UP, buff=0.3)
        diagrama = VGroup(mix, e_rf, e_lo, s_if, fios, r_rf, r_lo, r_if)

        leg = self.legenda("O mixer existe para mover um sinal de frequência, "
                           "sem perder amplitude nem fase")
        self.play(FadeIn(VGroup(mix, e_rf, fios[0]), shift=RIGHT * 0.2),
                  run_time=1.0)
        self.play(FadeIn(r_rf), run_time=0.7)
        self.wait(1.0)
        self.play(FadeIn(VGroup(e_lo, fios[1]), shift=UP * 0.2), run_time=1.0)
        self.play(FadeIn(r_lo), run_time=0.7)
        self.wait(1.0)
        self.play(FadeIn(VGroup(s_if, fios[2]), shift=RIGHT * 0.2), run_time=1.0)
        self.play(FadeIn(r_if), run_time=0.7)
        leg = self.legenda("Na forma ideal, ele entrega o produto ponto a ponto "
                           "dos dois sinais", leg, COR_IF)
        self.wait(1.2)

        # --- Etapa B: o produto no tempo ------------------------------------
        leg = self.legenda("Vamos ver o que esse produto é, no tempo", leg)
        self.play(FadeOut(diagrama), run_time=0.9)

        ax_rf = eixos(P(0.4, 2.15), 10.4, 0.95, [0, 4, 1], [-1.2, 1.2, 1])
        ax_lo = eixos(P(0.4, 0.85), 10.4, 0.95, [0, 4, 1], [-1.2, 1.2, 1])
        ax_if = eixos(P(0.4, -1.35), 10.4, 1.7, [0, 4, 1], [-1.2, 1.2, 1])
        o_rf = curva(ax_rf, lambda x: np.cos(2 * np.pi * FD_RF * x), COR_RF)
        o_lo = curva(ax_lo, lambda x: np.cos(2 * np.pi * FD_LO * x), COR_LO)
        o_if = curva(ax_if, lambda x: (np.cos(2 * np.pi * FD_RF * x)
                                       * np.cos(2 * np.pi * FD_LO * x)), COR_IF)
        r1 = rotulo_eixo(ax_rf, tex(r"v_{RF}(t)", COR_RF, 24))
        r2 = rotulo_eixo(ax_lo, tex(r"v_{LO}(t)", COR_LO, 24))
        r3 = rotulo_eixo(ax_if, tex(r"v_{RF}(t)\cdot v_{LO}(t)", COR_IF, 24))

        self.play(Create(ax_rf), FadeIn(r1), run_time=0.8)
        self.play(Create(o_rf), run_time=1.4)
        self.play(Create(ax_lo), FadeIn(r2), run_time=0.8)
        self.play(Create(o_lo), run_time=1.4)
        self.wait(0.8)
        leg = self.legenda("Multiplicando amostra por amostra, aparece "
                           "um batimento", leg)
        self.play(Create(ax_if), FadeIn(r3), run_time=0.8)
        self.play(Create(o_if), run_time=2.2)
        self.wait(1.5)

        # --- Etapa C: o batimento é a soma de duas senoides -----------------
        leg = self.legenda("Essa forma estranha esconde algo simples: "
                           "ela é a soma de só duas senoides", leg, COR_LO)
        self.play(FadeOut(VGroup(ax_rf, ax_lo, o_rf, o_lo, r1, r2)),
                  VGroup(ax_if, o_if, r3).animate.shift(UP * 2.9), run_time=1.3)
        self.wait(0.6)

        ax_d = eixos(P(0.4, -0.6), 10.4, 1.7, [0, 4, 1], [-1.2, 1.2, 1])
        c_dif = curva(ax_d, lambda x: 0.5 * np.cos(2 * np.pi * FD_IF * x),
                      COR_IF, 4)
        c_som = curva(ax_d, lambda x: 0.5 * np.cos(2 * np.pi * FD_SOMA * x),
                      COR_SOMA, 3)
        r_dif = Text("½·cos[(ω_LO − ω_RF)·t]  →  a IF, lenta", font_size=21,
                     color=COR_IF).move_to(P(-3.0, -2.15))
        r_som = Text("½·cos[(ω_LO + ω_RF)·t]  →  a soma, rápida", font_size=21,
                     color=COR_SOMA).move_to(P(3.3, -2.15))

        self.play(Create(ax_d), run_time=0.7)
        leg = self.legenda("A primeira é lenta: sua frequência é a DIFERENÇA "
                           "das duas", leg, COR_IF)
        self.play(Create(c_dif), run_time=1.6)
        self.play(FadeIn(r_dif, shift=UP * 0.15), run_time=0.8)
        self.wait(1.4)
        leg = self.legenda("A segunda é rápida: sua frequência é a SOMA "
                           "das duas", leg, COR_SOMA)
        self.play(Create(c_som), run_time=1.6)
        self.play(FadeIn(r_som, shift=UP * 0.15), run_time=0.8)
        self.wait(1.4)

        leg = self.legenda("Somando as duas, reconstruímos exatamente "
                           "o batimento lá de cima", leg, COR_IF)
        copia = VGroup(c_dif.copy(), c_som.copy())
        self.play(copia.animate.move_to(ax_if.c2p(2, 0)), run_time=1.8)
        self.play(FadeOut(copia, scale=0.9),
                  Indicate(o_if, color=COR_IF, scale_factor=1.04),
                  Flash(ax_if.c2p(2, 0), color=COR_IF, line_length=0.3),
                  run_time=1.6)
        self.wait(1.2)

        ident = ajustar(tex_partes([
            (r"\cos(\omega_{RF}t)\cos(\omega_{LO}t)", WHITE),
            (r"=\tfrac{1}{2}\cos[(\omega_{LO}-\omega_{RF})t]", COR_IF),
            (r"+\tfrac{1}{2}\cos[(\omega_{LO}+\omega_{RF})t]", COR_SOMA)],
            30)).move_to(P(0, Y_TOPO))
        leg = self.legenda("É uma identidade trigonométrica — nada além disso",
                           leg)
        # o espectro vem depois: TUDO o que é do domínio do tempo sai agora
        self.play(FadeOut(VGroup(ax_if, o_if, r3, ax_d, c_dif, c_som,
                                 r_dif, r_som)), run_time=0.9)
        self.play(Write(ident), run_time=2.4)
        self.wait(2.2)

        # --- Etapa D: o mesmo fato, no espectro -----------------------------
        leg = self.legenda("No espectro, o mixer ideal é o retrato mais simples "
                           "possível", leg)
        ax, deco = self.eixo_espectro(P(0, -0.6), 11.4, 2.6)
        self.play(Create(ax), FadeIn(deco), run_time=1.1)
        raias = self.desenhar_raias(ax, [(F_IF, 1, -1), (F_RF + F_LO, 1, 1)],
                                    -80, tamanho=22)
        self.wait(1.0)
        nums = VGroup(
            Text("30 MHz", font_size=21, color=COR_IF)
            .next_to(raias[0][2], RIGHT, buff=0.2),
            Text("230 MHz", font_size=21, color=COR_SOMA)
            .next_to(raias[1][2], RIGHT, buff=0.2))
        self.play(FadeIn(nums), run_time=0.8)
        leg = self.legenda("Duas raias e nada mais: nenhum harmônico, "
                           "nenhum vazamento", leg, COR_IF)
        self.wait(1.6)
        leg = self.legenda("Esse é o alvo. Agora a pergunta: o hardware "
                           "consegue fazer isso?", leg, COR_LO)
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 2
    def cena_diodo(self):
        self.titulo_cena("2 · Nenhum componente analógico multiplica tensões")

        leg = self.legenda("Para multiplicar duas tensões seria preciso um "
                           "componente que fizesse isso. Ele não existe.")

        ax = eixos(P(-4.0, -0.1), 4.8, 4.2, [-1.2, 1.6, 1], [-0.6, 3.2, 1])
        rot_i = tex(r"i", COR_EIXO, 26).next_to(ax, UP, buff=0.06)\
            .align_to(ax, LEFT)
        rot_v = tex(r"v", COR_EIXO, 26).next_to(ax, RIGHT, buff=0.12)
        k = 1.6
        diodo = curva(ax, lambda x: np.clip(np.exp(k * x) - 1, -0.6, 3.2),
                      COR_VAZA, 4)
        eq_diodo = tex(r"i = I_s\left(e^{v/V_T}-1\right)", COR_VAZA, 26)\
            .next_to(ax, DOWN, buff=0.3)

        leg = self.legenda("O que existe é isto: uma curva suave, exponencial",
                           leg)
        self.play(Create(ax), FadeIn(rot_i), FadeIn(rot_v), run_time=1.0)
        self.play(Create(diodo), run_time=2.0)
        self.play(Write(eq_diodo), run_time=1.2)
        self.wait(1.5)

        # Ponto de operação dentro do eixo (vq menor que antes: Q ficava fora)
        vq = 0.55
        iq = math.exp(k * vq) - 1
        ponto = Dot(ax.c2p(vq, iq), color=COR_LO, radius=0.1)
        rot_q = tex(r"Q", COR_LO, 28).next_to(ponto, RIGHT, buff=0.12)
        leg = self.legenda("Escolhemos um ponto de operação e olhamos a curva "
                           "só na vizinhança dele", leg, COR_LO)
        self.play(FadeIn(ponto, scale=0.4), Write(rot_q), run_time=0.9)
        self.wait(1.0)

        def taylor(ordem):
            def f(x):
                d = x - vq
                y = -np.ones_like(d)
                for j in range(ordem + 1):
                    y = y + (iq + 1) * (k * d) ** j / math.factorial(j)
                return np.clip(y, -0.6, 3.2)
            return f

        # Só perto de Q: longe disso a série diverge e o traço vira um artefato
        x0, x1 = vq - 1.5, vq + 0.85
        rotulo_ap = Text("ordem 1: só a reta tangente", font_size=21,
                         color=COR_LO).move_to(P(-4.0, Y_TOPO))
        aprox = curva(ax, taylor(1), COR_LO, 3, x0=x0, x1=x1)
        leg = self.legenda("Perto de Q, a curva é bem descrita por um polinômio "
                           "— a série de Taylor", leg)
        self.play(Create(aprox), FadeIn(rotulo_ap), run_time=1.4)
        self.wait(1.3)
        for ordem, nome in [(2, "ordem 2: acompanha a curvatura"),
                            (3, "ordem 3: acompanha melhor ainda")]:
            self.play(Transform(aprox, curva(ax, taylor(ordem), COR_LO, 3,
                                             x0=x0, x1=x1)),
                      Transform(rotulo_ap,
                                Text(nome, font_size=21, color=COR_LO)
                                .move_to(P(-4.0, Y_TOPO))),
                      run_time=1.5)
            self.wait(1.2)

        eq = ajustar(tex_partes([(r"v_{out} = ", WHITE), (r"a\,v_{in}", COR_VAZA),
                                 (r" + b\,v_{in}^2", COR_IF),
                                 (r" + c\,v_{in}^3", COR_IMD),
                                 (r" + \dots", WHITE)], 32), 6.6)\
            .move_to(P(3.3, Y_TOPO))
        leg = self.legenda("Qualquer não linearidade vira, então, "
                           "este polinômio", leg, COR_IF)
        self.play(Write(eq), run_time=1.8)
        self.wait(1.6)

        # O que a curva faz com a soma dos dois tons
        leg = self.legenda("E repare como os dois sinais entram: SOMADOS, "
                           "nunca multiplicados", leg, COR_LO)
        ax_in = eixos(P(3.3, 1.05), 6.6, 1.5, [0, 4, 1], [-2.4, 2.4, 1])
        ax_out = eixos(P(3.3, -1.45), 6.6, 1.8, [0, 4, 1], [-1.5, 4.5, 1])

        def v_in(x):
            return np.cos(2 * np.pi * FD_RF * x) + np.cos(2 * np.pi * FD_LO * x)

        def v_out(x):
            v = v_in(x)
            return sum(c * v ** (j + 1) for j, c in enumerate(COEFS[:3]))

        o_in = curva(ax_in, v_in, COR_RF)
        o_out = curva(ax_out, v_out, COR_IMG)       # cor bem distinta da entrada
        r_in = rotulo_eixo(ax_in, tex_partes([(r"v_{in} = ", WHITE),
                                              (r"v_{RF}", COR_RF), (r"+", WHITE),
                                              (r"v_{LO}", COR_LO)], 22))
        r_out = rotulo_eixo(ax_out, tex(r"v_{out}", COR_IMG, 24))
        self.play(Create(ax_in), FadeIn(r_in), run_time=0.8)
        self.play(Create(o_in), run_time=1.6)
        self.wait(1.2)
        leg = self.legenda("A soma atravessa a curva… e sai deformada", leg)
        self.play(Create(ax_out), FadeIn(r_out), run_time=0.8)
        self.play(TransformFromCopy(o_in, o_out), run_time=2.6)
        self.wait(1.5)

        nota = Text("mudou a forma  →  há frequências novas lá dentro",
                    font_size=24, color=COR_OK).move_to(P(0, Y_BASE))
        self.play(FadeIn(nota, shift=UP * 0.15), run_time=0.9)
        leg = self.legenda("A mistura que queremos é efeito colateral "
                           "dessa deformação", leg, COR_IF)
        self.wait(2.2)
        self.limpar()

    # ================================================================== CENA 3
    def cena_termos(self):
        self.titulo_cena("3 · Quem gera o quê")

        cab = ajustar(tex_partes([(r"v_{out} = a(", WHITE), (r"v_{RF}", COR_RF),
                                  (r"\!+\!", WHITE), (r"v_{LO}", COR_LO),
                                  (r") + b(", WHITE), (r"v_{RF}", COR_RF),
                                  (r"\!+\!", WHITE), (r"v_{LO}", COR_LO),
                                  (r")^2 + c(", WHITE), (r"v_{RF}", COR_RF),
                                  (r"\!+\!", WHITE), (r"v_{LO}", COR_LO),
                                  (r")^3", WHITE)], 30), 11.0)\
            .move_to(P(0, Y_TOPO))
        leg = self.legenda("Vamos abrir o polinômio termo a termo e ver "
                           "o que cada um produz")
        self.play(Write(cab), run_time=2.4)
        self.wait(1.2)

        # faixas: equações em 1,8 / 1,0 / 0,35; rótulos das raias de −1,0 a
        # −0,3; gráfico de −1,3 a −2,6; números abaixo dele
        piso = -60
        ax, deco = self.eixo_espectro(P(0, -1.95), 11.0, 1.3, piso, 10,
                                      rot_x=False, rot_y=False, tamanho=16)
        # curto e encostado à direita: a raia mais alta em frequência (3LO,
        # 390 MHz) precisa da faixa livre acima dela
        rot_sp = Text("espectro [MHz]", font_size=16, color=GREY_A)
        rot_sp.move_to([ax.c2p(F_MAX, 0)[0] - rot_sp.width / 2,
                        ax.c2p(0, 10)[1] + 0.6, 0])
        self.reservar(ax, rot_sp.get_left()[0] - 0.1,
                      rot_sp.get_right()[0] + 0.1, 3)
        self.play(Create(ax), FadeIn(deco), FadeIn(rot_sp), run_time=1.0)

        # --- termo linear ----------------------------------------------------
        leg = self.legenda("Termo linear: o que entra, sai. Nenhuma "
                           "frequência nova.", leg)
        t1 = tex_partes([(r"a\,v_{in} = ", COR_VAZA),
                         (r"a\cos\omega_{RF}t", COR_RF), (r"\;+\;", WHITE),
                         (r"a\cos\omega_{LO}t", COR_LO)], 34).move_to(P(0, 1.95))
        n1 = Text("as portadoras vazam direto para a saída", font_size=24,
                  color=COR_VAZA).move_to(P(0, 1.0))
        self.play(Write(t1), run_time=1.8)
        self.wait(1.2)
        self.play(FadeIn(n1, shift=UP * 0.15), run_time=0.8)
        self.desenhar_raias(ax, [(F_RF, 1, 0), (F_LO, 0, -1)], piso)
        self.wait(1.6)

        # --- termo quadrático ------------------------------------------------
        leg = self.legenda("Termo quadrático: é aqui, e só aqui, que nasce "
                           "a multiplicação", leg, COR_IF)
        t2 = tex_partes([(r"b\,v_{in}^2 = b\,v_{RF}^2", WHITE),
                         (r"\;+\;2b\,v_{RF}v_{LO}", COR_IF),
                         (r"\;+\;b\,v_{LO}^2", WHITE)], 34).move_to(P(0, 1.95))
        self.play(FadeOut(n1), ReplacementTransform(t1, t2), run_time=1.4)
        self.wait(1.2)
        cx = SurroundingRectangle(t2[1], color=COR_IF, buff=0.1,
                                  corner_radius=0.06)
        leg = self.legenda("Olhe o termo do meio: ele é o produto dos "
                           "dois sinais", leg, COR_IF)
        self.play(Create(cx), run_time=0.9)
        self.wait(1.0)
        t2b = ajustar(tex_partes([
            (r"2b\cos\omega_{RF}t\,\cos\omega_{LO}t = ", WHITE),
            (r"b\cos(\omega_{LO}\!-\!\omega_{RF})t", COR_IF),
            (r"\;+\;b\cos(\omega_{LO}\!+\!\omega_{RF})t", COR_SOMA)], 28), 11.5)\
            .move_to(P(0, 1.0))
        self.play(Write(t2b), run_time=2.2)
        self.wait(1.0)
        self.desenhar_raias(ax, [(F_IF, 1, -1), (F_RF + F_LO, 1, 1)], piso,
                            destaque=COR_IF)
        self.wait(1.4)
        n2 = Text("e os quadrados dos termos isolados viram DC "
                  "e 2º harmônico", font_size=22, color=GREY_A)\
            .move_to(P(0, 0.35))
        self.play(FadeIn(n2), run_time=0.8)
        self.desenhar_raias(ax, [(2 * F_RF, 2, 0), (2 * F_LO, 0, -2)], piso)
        self.wait(1.6)

        # --- termo cúbico ----------------------------------------------------
        leg = self.legenda("Termo cúbico: a intermodulação, que é o que "
                           "mais incomoda", leg, COR_IMD)
        self.play(FadeOut(VGroup(cx, t2b, n2)), run_time=0.8)   # some ANTES
        t3 = ajustar(tex_partes([(r"c\,v_{in}^3 = v_{RF}^3", WHITE),
                                 (r"\;+\;3v_{RF}^2v_{LO}", COR_IMD),
                                 (r"\;+\;3v_{RF}v_{LO}^2", COR_IMD),
                                 (r"\;+\;v_{LO}^3", WHITE)], 32), 11.0)\
            .move_to(P(0, 1.95))
        self.play(ReplacementTransform(t2, t3), run_time=1.4)
        self.wait(1.4)
        n3 = VGroup(
            Text("produtos cruzados  →  2f_LO ± f_RF   e   2f_RF ± f_LO",
                 font_size=23, color=COR_IMD),
            Text("cubos isolados  →  3f_RF  e  3f_LO", font_size=23,
                 color=COR_VAZA),
            Text("e parte cai de volta sobre f_RF e f_LO  →  "
                 "compressão de ganho (P1dB)", font_size=23, color=COR_LO),
        ).arrange(DOWN, buff=0.26).move_to(P(0, 0.72))
        for item in n3:
            self.play(FadeIn(item, shift=RIGHT * 0.2), run_time=0.8)
            self.wait(0.9)
        self.desenhar_raias(ax, [(abs(2 * F_RF - F_LO), 2, -1),
                                 (abs(F_RF - 2 * F_LO), 1, -2),
                                 (3 * F_RF, 3, 0), (3 * F_LO, 0, -3)], piso)
        leg = self.legenda("Cada potência do polinômio abre um grupo novo "
                           "de frequências", leg)
        self.wait(2.2)
        self.limpar()

    # ================================================================== CENA 4
    def cena_familia(self):
        self.titulo_cena("4 · A família  m·f_RF ± n·f_LO")

        regra = ajustar(tex(r"f_{esp\acute{u}rio} = |\,m\,f_{RF} \pm n\,f_{LO}\,|,"
                            r"\qquad \text{ordem} = m+|n|", WHITE, 32), 9.5)\
            .move_to(P(0, Y_TOPO))
        leg = self.legenda("Juntando tudo: existe uma raia para cada par "
                           "de inteiros (m, n)")
        self.play(Write(regra), run_time=2.0)
        self.wait(1.6)

        # Legenda de cores numa linha só, fora da área do gráfico
        cores = VGroup(*[
            VGroup(Dot(color=c, radius=0.07),
                   Text(t, font_size=17, color=c)).arrange(RIGHT, buff=0.1)
            for c, t in [(COR_IF, "IF e harmônicos"),
                         (COR_SOMA, "banda soma"),
                         (COR_VAZA, "vazamento / harmônico puro"),
                         (COR_IMD, "intermodulação")]
        ]).arrange(RIGHT, buff=0.5).move_to(P(0, 2.0))
        ajustar(cores, 12.4)
        self.play(FadeIn(cores), run_time=0.9)

        # gráfico de −2,25 a −0,05; faixa de rótulos (5 níveis) até ~1,5
        ax, deco = self.eixo_espectro(P(0, -1.15), 11.4, 2.2)
        self.play(Create(ax), FadeIn(deco), run_time=1.0)

        descricao = {
            1: "ordem 1 — o que simplesmente vazou da entrada",
            2: "ordem 2 — a IF útil, a banda soma e os segundos harmônicos",
            3: "ordem 3 — intermodulação: caem perto da IF e são difíceis "
               "de filtrar",
            4: "ordem 4 — mais fracas, mas a família não tem fim",
        }
        leg = self.legenda("Vamos construir o espectro real, ordem por ordem",
                           leg)
        tudo = VGroup()
        for ordem in (1, 2, 3, 4):
            itens = [(f, m, n) for f, m, n in familia(ordem)
                     if nivel_db(f) >= -78]
            leg = self.legenda(descricao[ordem], leg,
                               COR_IF if ordem == 2 else GREY_A)
            tudo.add(self.desenhar_raias(ax, itens, -80,
                                         tamanho=16 if ordem < 3 else 14,
                                         opacidade=1.0 if ordem < 3 else 0.8,
                                         max_niveis=5, passo=0.28))
            self.wait(1.4)

        leg = self.legenda("Quanto maior a ordem, mais fraca a raia — mas "
                           "há raias por todo o eixo", leg)
        self.wait(1.6)

        alvo = SurroundingRectangle(tudo[1][0][0], color=COR_IF, buff=0.14,
                                    corner_radius=0.06)
        leg = self.legenda("De tudo isso, uma única raia é o sinal desejado",
                           leg, COR_IF)
        self.play(Create(alvo),
                  *[g.animate.set_opacity(0.25) for g in tudo[2:]],
                  run_time=1.4)
        self.wait(1.4)
        # a linha das cores dá lugar ao SFDR: embaixo não há espaço livre
        sfdr = Text("SFDR ≈ 5 dBc — o maior espúrio está quase no nível da IF",
                    font_size=24, color=COR_VAZA).move_to(P(0, 2.0))
        self.play(FadeOut(cores), FadeIn(sfdr), run_time=0.9)
        leg = self.legenda("Tudo o que não é essa raia precisa ser filtrado "
                           "depois", leg, COR_VAZA)
        self.wait(2.0)
        self.limpar()

    # ================================================================== CENA 5
    def cena_imagem(self):
        self.titulo_cena("5 · A frequência imagem não é defeito do componente")

        ax = eixos(P(0, 1.35), 9.6, 1.5, [0, 220, 50], [0, 1.2, 1])
        # só 0, 50 e 200: 100 e 150 ficariam no caminho das setas curvas, e as
        # raias já trazem as próprias frequências no rótulo
        marcas = marcar_x(ax, [0, 50, 200], 0)
        rot_x = VGroup(
            Text("entrada", font_size=20, color=GREY_A)
            .next_to(ax, UP, buff=0.05).align_to(ax, LEFT),
            Text("MHz", font_size=18, color=GREY_A)
            .next_to(ax.x_axis.get_end(), RIGHT, buff=0.15))
        leg = self.legenda("Voltemos ao mixer ideal e olhemos a ENTRADA")
        self.play(Create(ax), FadeIn(marcas), FadeIn(rot_x), run_time=1.0)

        h_lo = haste(ax, F_LO, 1.1, COR_LO, 0, largura=5)
        h_rf = haste(ax, F_RF, 0.8, COR_RF, 0, largura=5)
        h_im = haste(ax, F_IMG, 0.8, COR_IMG, 0, largura=5)
        e_lo = Text("LO (130)", font_size=20, color=COR_LO)\
            .next_to(ax.c2p(F_LO, 1.1), UP, buff=0.1)
        e_rf = Text("RF desejado (100)", font_size=20, color=COR_RF)\
            .next_to(ax.c2p(F_RF, 0.8), UP, buff=0.1).shift(LEFT * 0.7)
        e_im = Text("imagem (160)", font_size=20, color=COR_IMG)\
            .next_to(ax.c2p(F_IMG, 0.8), UP, buff=0.1).shift(RIGHT * 0.6)

        self.play(GrowFromEdge(h_lo, DOWN), FadeIn(e_lo), run_time=0.8)
        self.play(GrowFromEdge(h_rf, DOWN), FadeIn(e_rf), run_time=0.8)
        self.wait(1.0)
        leg = self.legenda("Agora suponha que exista OUTRO sinal, do outro "
                           "lado do LO, à mesma distância", leg, COR_IMG)
        self.play(GrowFromEdge(h_im, DOWN), FadeIn(e_im), run_time=0.9)
        self.wait(1.2)

        d1 = DoubleArrow(ax.c2p(F_RF, 0.35), ax.c2p(F_LO, 0.35), buff=0,
                         color=COR_RF, stroke_width=3,
                         max_tip_length_to_length_ratio=0.1)
        d2 = DoubleArrow(ax.c2p(F_LO, 0.35), ax.c2p(F_IMG, 0.35), buff=0,
                         color=COR_IMG, stroke_width=3,
                         max_tip_length_to_length_ratio=0.1)
        t1 = Text("30", font_size=18, color=COR_RF).next_to(d1, DOWN, buff=0.06)
        t2 = Text("30", font_size=18, color=COR_IMG).next_to(d2, DOWN, buff=0.06)
        self.play(GrowArrow(d1), GrowArrow(d2), FadeIn(t1), FadeIn(t2),
                  run_time=1.2)
        self.wait(1.0)

        ax2 = eixos(P(-1.6, -1.6), 3.8, 0.9, [0, 60, 30], [0, 1.4, 1])
        rot2 = Text("saída (IF)", font_size=19, color=GREY_A)\
            .next_to(ax2, DOWN, buff=0.15)
        h_if = haste(ax2, 30, 1.3, COR_IF, 0, largura=6)
        # à esquerda: as duas setas chegam pela direita
        e_if = Text("30 MHz", font_size=20, color=COR_IF)\
            .next_to(ax2.c2p(30, 1.3), LEFT, buff=0.3)
        c1 = CurvedArrow(ax.c2p(F_RF, 0.08), ax2.c2p(30, 1.4), color=COR_RF,
                         angle=0.8, stroke_width=3, tip_length=0.18)
        c2 = CurvedArrow(ax.c2p(F_IMG, 0.08), ax2.c2p(30, 1.4), color=COR_IMG,
                         angle=-0.8, stroke_width=3, tip_length=0.18)
        leg = self.legenda("Depois da mistura, as duas caem na MESMA IF — "
                           "e se somam lá", leg, COR_IMG)
        self.play(Create(ax2), FadeIn(rot2), run_time=0.7)
        self.play(Create(c1), run_time=1.0)
        self.play(Create(c2), run_time=1.0)
        self.play(GrowFromEdge(h_if, DOWN), FadeIn(e_if), run_time=0.9)
        eq = ajustar(tex(r"|f_{LO}-f_{RF}| = |f_{LO}-f_{IM}| = 30\ \text{MHz}",
                         WHITE, 28), 6.0).move_to(P(3.4, -2.2))
        self.play(Write(eq), run_time=1.6)
        self.wait(1.6)
        leg = self.legenda("Nenhum filtro depois do mixer separa as duas: "
                           "elas estão na mesma frequência", leg, COR_VAZA)
        self.wait(2.0)

        # Por quê: o cosseno real é a soma de dois fasores opostos
        leg = self.legenda("Por que isso acontece até no multiplicador "
                           "perfeito?", leg, COR_LO)
        self.play(FadeOut(VGroup(ax, ax2, marcas, rot_x, rot2, h_lo, h_rf, h_im,
                                 e_lo, e_rf, e_im, d1, d2, t1, t2, h_if, e_if,
                                 c1, c2, eq)), run_time=1.0)

        centro = P(-3.9, -0.1)
        R = 1.45
        circ = Circle(radius=R, color=COR_EIXO, stroke_width=2).move_to(centro)
        eixos_c = VGroup(
            Line(centro + LEFT * (R + 0.35), centro + RIGHT * (R + 0.35),
                 color=COR_EIXO, stroke_width=2),
            Line(centro + DOWN * (R + 0.35), centro + UP * (R + 0.35),
                 color=COR_EIXO, stroke_width=2))
        ang = PI / 5
        f_pos = Arrow(centro, centro + R * np.array([np.cos(ang), np.sin(ang), 0]),
                      buff=0, color=COR_RF, stroke_width=5,
                      max_tip_length_to_length_ratio=0.15)
        f_neg = Arrow(centro, centro + R * np.array([np.cos(-ang), np.sin(-ang), 0]),
                      buff=0, color=COR_IMG, stroke_width=5,
                      max_tip_length_to_length_ratio=0.15)
        r_pos = tex(r"e^{+j\omega t}", COR_RF, 26)\
            .move_to(centro + UP * (R + 0.5) + RIGHT * 0.9)
        r_neg = tex(r"e^{-j\omega t}", COR_IMG, 26)\
            .move_to(centro + DOWN * (R + 0.5) + RIGHT * 0.9)
        eq_euler = ajustar(tex(r"\cos\omega t = \tfrac{1}{2}\left(e^{+j\omega t}"
                               r" + e^{-j\omega t}\right)", WHITE, 30), 6.4)\
            .move_to(P(3.2, Y_TOPO - 0.1))

        self.play(Create(circ), Create(eixos_c), run_time=1.0)
        self.play(Write(eq_euler), run_time=1.8)
        self.wait(1.4)
        leg = self.legenda("Um cosseno real é a soma de DOIS fasores, girando "
                           "em sentidos opostos", leg, COR_IMG)
        self.play(GrowArrow(f_pos), FadeIn(r_pos), run_time=0.9)
        self.play(GrowArrow(f_neg), FadeIn(r_neg), run_time=0.9)
        self.wait(1.0)
        self.play(Rotate(f_pos, TAU, about_point=centro, rate_func=linear),
                  Rotate(f_neg, -TAU, about_point=centro, rate_func=linear),
                  run_time=4.5)
        self.wait(0.8)

        conclusao = VGroup(
            Text("o fasor +ω desloca o espectro para um lado", font_size=22,
                 color=COR_RF),
            Text("o fasor −ω desloca para o outro", font_size=22, color=COR_IMG),
            Text("os dois deslocamentos se sobrepõem na IF", font_size=22,
                 color=COR_VAZA),
            Text("→ é daí que vem a imagem", font_size=23, color=COR_VAZA),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.24).move_to(P(3.2, 0.25))
        for item in conclusao:
            self.play(FadeIn(item, shift=RIGHT * 0.2), run_time=0.7)
            self.wait(0.8)
        self.wait(1.2)

        sol = VGroup(
            tex(r"e^{-j\omega_{LO}t}", COR_FPGA, 36),
            Text("usar um sentido só: dois multiplicadores, I e Q",
                 font_size=21, color=GREY_A),
            Text("a imagem é rejeitada por construção", font_size=22,
                 color=COR_OK),
        ).arrange(DOWN, buff=0.22).move_to(P(3.2, -1.9))
        leg = self.legenda("A saída é um LO que gira num sentido só — "
                           "é exatamente o que o DDC faz", leg, COR_FPGA)
        self.play(FadeIn(sol, shift=UP * 0.2), run_time=1.4)
        self.wait(2.4)
        self.limpar()

    # ================================================================== CENA 6
    def cena_digital(self):
        self.titulo_cena("6 · No FPGA a multiplicação é de verdade")

        y = 1.75
        adc = caixa_texto("ADC", 1.3, 0.7, COR_RF, 22).move_to(P(-5.2, y))
        mult = multiplicador(COR_FPGA).move_to(P(-2.9, y))
        cic = caixa_texto("CIC", 1.2, 0.7, COR_IMD, 22).move_to(P(-0.6, y))
        fir = caixa_texto("FIR", 1.2, 0.7, COR_IF, 22).move_to(P(1.6, y))
        saida = tex(r"I,\;Q", COR_OK, 28).move_to(P(3.6, y))
        acc = caixa_texto("acumulador\nde fase", 1.9, 0.9, COR_LO, 18)\
            .move_to(P(-5.0, 0.15))
        lut = caixa_texto("LUT\ncos/sen", 1.5, 0.9, COR_LO, 18)\
            .move_to(P(-2.9, 0.15))
        fios = VGroup(
            fio([adc.get_right(), mult.get_left()], COR_RF),
            fio([mult.get_right(), cic.get_left()], COR_FPGA),
            fio([cic.get_right(), fir.get_left()], COR_IMD),
            fio([fir.get_right(), saida.get_left() + LEFT * 0.15], COR_IF),
            fio([acc.get_right(), lut.get_left()], COR_LO),
            fio([lut.get_top(), mult.get_bottom()], COR_LO))
        dds = Text("DDS", font_size=22, color=COR_LO)\
            .next_to(VGroup(acc, lut), DOWN, buff=0.18)
        diagrama = VGroup(adc, mult, cic, fir, saida, acc, lut, fios, dds)

        leg = self.legenda("No digital, o sinal já é um número inteiro")
        self.play(LaggedStart(FadeIn(adc), FadeIn(mult), FadeIn(cic),
                              FadeIn(fir), FadeIn(saida), lag_ratio=0.3),
                  run_time=2.0)
        self.play(FadeIn(acc), FadeIn(lut), FadeIn(dds), run_time=1.1)
        self.play(Create(fios), run_time=1.8)
        leg = self.legenda("O produto é feito num DSP slice: aritmética exata, "
                           "sem ponto de polarização", leg, COR_FPGA)
        self.wait(1.6)

        # Texto abaixo do diagrama: antes ele batia na caixa da LUT
        ganhos = VGroup(
            Text("sem termo linear   →   nenhum vazamento de LO ou RF",
                 font_size=23, color=COR_OK),
            Text("sem termo cúbico   →   nenhuma intermodulação, nenhum P1dB",
                 font_size=23, color=COR_OK),
            Text("27×18 bits guardados em 48   →   produto bit-exato",
                 font_size=23, color=COR_OK),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(P(0, -1.85))
        for item in ganhos:
            self.play(FadeIn(item, shift=RIGHT * 0.2), run_time=0.8)
            self.wait(1.0)
        leg = self.legenda("A Cena 4 inteira desaparece: não há o que filtrar",
                           leg, COR_OK)
        self.wait(2.0)

        # De onde vêm, então, os espúrios digitais
        leg = self.legenda("Mas 'preciso' não é 'perfeito'. Olhe dentro do DDS.",
                           leg, COR_LO)
        self.play(FadeOut(VGroup(diagrama, ganhos)), run_time=0.9)

        ax_f = eixos(P(-3.5, 1.35), 5.4, 1.7, [0, 4, 1], [0, 1.15, 1])
        ax_c = eixos(P(3.3, 1.35), 5.4, 1.7, [0, 4, 1], [-1.2, 1.2, 1])
        r_f = rotulo_eixo(ax_f, Text("fase acumulada", font_size=20,
                                     color=COR_LO))
        r_c = rotulo_eixo(ax_c, Text("saída da LUT", font_size=20, color=COR_LO))

        incl, niveis = 0.9, 8
        xs = np.linspace(0, 4, 900)
        rampa = (xs * incl) % 1.0
        degrau = np.floor(rampa * niveis) / niveis
        c_rampa = polilinha(ax_f, xs, rampa, COR_LO, 3)
        c_degrau = polilinha(ax_f, xs, degrau, COR_IMD, 3)
        c_ideal = polilinha(ax_c, xs, np.cos(2 * np.pi * rampa), COR_LO, 3)
        c_quant = polilinha(ax_c, xs, np.cos(2 * np.pi * degrau), COR_IMD, 3)

        self.play(Create(ax_f), FadeIn(r_f), Create(ax_c), FadeIn(r_c),
                  run_time=1.0)
        leg = self.legenda("O acumulador produz uma rampa de fase; a LUT "
                           "devolve o cosseno dela", leg)
        self.play(Create(c_rampa), run_time=1.5)
        self.play(Create(c_ideal), run_time=1.5)
        self.wait(1.4)
        leg = self.legenda("Mas a fase tem 32 bits e só os 14 de cima "
                           "endereçam a LUT", leg, COR_IMD)
        self.play(Create(c_degrau), run_time=1.6)
        self.play(Create(c_quant), run_time=1.6)
        self.wait(1.4)
        leg = self.legenda("O erro de truncamento é periódico — e tudo que "
                           "é periódico vira raia", leg, COR_IMD)
        self.wait(1.6)

        quant = VGroup(
            tex(r"\text{SFDR} \approx -6{,}02 \times B_{\text{end}}\ "
                r"\text{dBc}", COR_IMD, 34),
            Text("14 bits de endereço   →   −84 dBc", font_size=24,
                 color=COR_OK),
            Text("a simulação mediu 84,1 dBc: a teoria fecha no dígito",
                 font_size=22, color=GREY_A),
        ).arrange(DOWN, buff=0.28).move_to(P(0, -1.6))
        for item in quant:
            self.play(FadeIn(item, shift=UP * 0.15), run_time=0.8)
            self.wait(1.0)
        leg = self.legenda("Espúrio que se projeta no papel, e não depende "
                           "de temperatura", leg, COR_OK)
        self.wait(2.0)

        # O caso f_s/4
        leg = self.legenda("E há um caso em que nem multiplicador é preciso",
                           leg, COR_FPGA)
        self.play(FadeOut(VGroup(ax_f, ax_c, r_f, r_c, c_rampa, c_degrau,
                                 c_ideal, c_quant, quant)), run_time=0.9)

        centro = P(-4.0, -0.2)
        R = 1.4
        circ = Circle(radius=R, color=COR_EIXO, stroke_width=2).move_to(centro)
        eixos_c = VGroup(
            Line(centro + LEFT * (R + 0.2), centro + RIGHT * (R + 0.2),
                 color=COR_EIXO, stroke_width=2),
            Line(centro + DOWN * (R + 0.2), centro + UP * (R + 0.2),
                 color=COR_EIXO, stroke_width=2))
        pontos, rotp = VGroup(), VGroup()
        for dx, dy, txt in [(1, 0, "cos = 1\nsen = 0"), (0, 1, "cos = 0\nsen = 1"),
                            (-1, 0, "cos = −1\nsen = 0"),
                            (0, -1, "cos = 0\nsen = −1")]:
            pontos.add(Dot(centro + R * np.array([dx, dy, 0.0]),
                           color=COR_FPGA, radius=0.11))
            rotp.add(Text(txt, font_size=17, color=COR_LO, line_spacing=0.8)
                     # os rótulos de 2 linhas são mais largos que altos:
                     # nas laterais precisam de mais distância
                     .move_to(centro + (R + (0.85 if dx else 0.62))
                              * np.array([dx, dy, 0.0])))
        self.play(Create(circ), Create(eixos_c), run_time=0.9)
        for p, r in zip(pontos, rotp):
            self.play(GrowFromCenter(p), FadeIn(r), run_time=0.55)
        self.wait(1.2)

        fs4 = VGroup(
            tex(r"f_{LO} = f_s/4", COR_FPGA, 38),
            Text("4 amostras por volta, sempre nos mesmos 4 pontos",
                 font_size=22, color=GREY_A),
            tex(r"\cos \to \{1,\,0,\,-1,\,0\}", COR_LO, 30),
            tex(r"\sin \to \{0,\,1,\,0,\,-1\}", COR_LO, 30),
            Text("multiplicar por 0 ou ±1 é trocar sinal e multiplexar",
                 font_size=22, color=COR_OK),
            Text("exato, sem LUT e sem DSP slice", font_size=22, color=COR_OK),
        ).arrange(DOWN, buff=0.26).move_to(P(3.1, -0.2))
        ajustar(fs4, 7.6)
        for item in fs4:
            self.play(FadeIn(item, shift=UP * 0.15), run_time=0.6)
            self.wait(0.7)
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 7
    def cena_filtro(self):
        self.titulo_cena("7 · O preço da limpeza: atraso de grupo")

        b, a = sig.ellip(7, 0.1, 80, 2 * np.pi * 35e6, analog=True)
        w = 2 * np.pi * np.linspace(1e6, 120e6, 600)
        _, h = sig.freqs(b, a, worN=w)
        tau = -np.gradient(np.unwrap(np.angle(h)), w) * 1e9      # ns
        f_mhz = w / (2 * np.pi) / 1e6

        ax = eixos(P(-1.6, -0.15), 7.6, 3.4, [0, 120, 20], [0, 140, 40])
        marcas_x = marcar_x(ax, [0, 20, 40, 60, 80, 100, 120], 0)
        marcas_y = VGroup(*[Text(f"{v}", font_size=18, color=GREY_B)
                            .next_to(ax.c2p(0, v), LEFT, buff=0.12)
                            for v in [0, 40, 80, 120]])
        rot_x = Text("frequência [MHz]", font_size=20, color=GREY_A)\
            .next_to(marcas_x, DOWN, buff=0.12)
        rot_y = Text("atraso de grupo [ns]", font_size=19, color=GREY_A)\
            .rotate(PI / 2).next_to(marcas_y, LEFT, buff=0.12)

        leg = self.legenda("Todo espúrio que existe precisa ser filtrado. "
                           "E filtrar custa caro.")
        self.play(Create(ax), FadeIn(marcas_x), FadeIn(marcas_y),
                  FadeIn(rot_x), FadeIn(rot_y), run_time=1.3)

        c_el = polilinha(ax, f_mhz, np.clip(tau, 0, 140), COR_VAZA, 4)
        leg = self.legenda("Um filtro com corte abrupto atrasa o sinal — "
                           "e não atrasa por igual", leg, COR_VAZA)
        self.play(Create(c_el), run_time=2.4)
        r_el = Text("elíptico analógico, ordem 7", font_size=19,
                    color=COR_VAZA).move_to(ax.c2p(84, 52))
        self.play(FadeIn(r_el), run_time=0.8)
        self.wait(1.4)

        linha_if = DashedLine(ax.c2p(30, 0), ax.c2p(30, 140), color=GREY_B,
                              stroke_width=2)
        rot_if = Text("IF", font_size=18, color=GREY_A)\
            .next_to(ax.c2p(30, 140), UP, buff=0.08)
        seta_pico = Arrow(ax.c2p(62, 92), ax.c2p(39, 91), buff=0.1,
                          color=COR_VAZA, stroke_width=3,
                          max_tip_length_to_length_ratio=0.2)
        var = Text("pico de 91 ns:\nvaria 2,3× dentro da banda",
                   font_size=19, color=COR_VAZA, line_spacing=0.85)\
            .next_to(seta_pico, RIGHT, buff=0.12)
        self.play(Create(linha_if), FadeIn(rot_if), run_time=0.8)
        self.play(GrowArrow(seta_pico), FadeIn(var), run_time=1.0)
        leg = self.legenda("Atraso que varia com a frequência deforma "
                           "o envelope do sinal", leg, COR_VAZA)
        self.wait(2.0)

        plano = Line(ax.c2p(0, 104), ax.c2p(120, 104), color=COR_IF,
                     stroke_width=4)
        r_fir = Text("FIR de fase linear, 53 taps", font_size=19, color=COR_IF)\
            .move_to(ax.c2p(60, 128))
        leg = self.legenda("O FIR digital não é mais rápido — mas é plano "
                           "e previsível", leg, COR_IF)
        self.play(Create(plano), run_time=1.6)
        self.play(FadeIn(r_fir), run_time=0.8)
        eq_tau = tex(r"\tau_g = \frac{N-1}{2}\,T_s", COR_IF, 30)\
            .move_to(P(4.6, 1.9))
        self.play(Write(eq_tau), run_time=1.4)
        self.wait(1.8)

        leg = self.legenda("E numa malha de realimentação, atraso é margem "
                           "de fase perdida", leg, COR_LO)
        custo = VGroup(
            tex(r"\Delta\phi = -\,\omega\,\tau", COR_LO, 34),
            tex(r"f_{BW} \lesssim \frac{1}{10\,\tau_{total}}", COR_LO, 30),
            Text("cada ns gasto filtrando\né banda de controle perdida",
                 font_size=19, color=GREY_A, line_spacing=0.85),
        ).arrange(DOWN, buff=0.35).move_to(P(4.6, -0.6))
        for item in custo:
            self.play(FadeIn(item, shift=UP * 0.15), run_time=0.7)
            self.wait(0.9)
        leg = self.legenda("É aqui que o mixer digital ganha: quase não há "
                           "espúrio para filtrar", leg, COR_OK)
        self.wait(2.4)
        self.limpar()

    # ================================================================== RESUMO
    def cena_resumo(self):
        titulo = Text("Resumo", font_size=44, weight=BOLD).move_to(P(0, 3.2))
        self.play(Write(titulo), run_time=1.2)
        self.wait(0.6)

        linhas = [
            ("No analógico, a multiplicação é subproduto de uma não linearidade",
             COR_VAZA),
            ("o termo quadrático gera a IF; o linear e o cúbico geram o lixo",
             GREY_A),
            ("Resultado: a família inteira  m·f_RF ± n·f_LO", COR_IMD),
            ("vazamento, harmônicos, intermodulação, compressão de ganho",
             GREY_A),
            ("A frequência imagem é outra coisa: vem do fasor negativo",
             COR_IMG),
            ("só se resolve antes do mixer, ou com mistura complexa I/Q",
             GREY_A),
            ("No FPGA o produto é aritmético e exato", COR_OK),
            ("os espúrios passam a vir da quantização: previsíveis e projetáveis",
             GREY_A),
            ("Filtrar custa atraso; o que não existe não precisa ser filtrado",
             COR_LO),
        ]
        g = VGroup(*[Text(t, font_size=25 if c != GREY_A else 21, color=c)
                     for t, c in linhas])
        for k, item in enumerate(g):
            if linhas[k][1] == GREY_A:
                item.shift(RIGHT * 0.4)
        g.arrange(DOWN, aligned_edge=LEFT, buff=0.24).move_to(P(0, 0.35))
        ajustar(g, 12.6)

        for k in range(0, len(g), 2):
            bloco = g[k:k + 2]
            self.play(LaggedStart(*[FadeIn(i, shift=RIGHT * 0.2) for i in bloco],
                                  lag_ratio=0.4), run_time=1.2)
            self.wait(1.5)
        self.wait(1.5)

        fecho = Text("empurre o ADC para mais perto do pickup: cada mixer "
                     "analógico a menos\né uma família inteira de espúrios "
                     "a menos", font_size=23, color=COR_OK, line_spacing=0.9)\
            .move_to(P(0, -3.0))
        self.play(FadeIn(fecho), run_time=1.2)
        self.wait(3.0)
        self.limpar()
