# -*- coding: utf-8 -*-
"""
Mixer de RF: por que a multiplicação cria uma família inteira de espúrios
=========================================================================

Renderização (a partir da raiz do repositório):
    manim -pql "src/Signal Conditioning and Down Conversion/Mixer/Mixer.py" Mixer   # rascunho
    manim -pqh "src/Signal Conditioning and Down Conversion/Mixer/Mixer.py" Mixer   # final

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

A simulação numérica correspondente (espectros em matplotlib, tabela de
espúrios e atraso de grupo) está em Mixer_plot.py, na mesma pasta.
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
COR_IMG = ORANGE         # frequência imagem
COR_FPGA = PURPLE_B
COR_OK = GREEN_B
COR_EIXO = GREY_B
FUNDO = "#0e1117"

EIXO_CFG = {"include_tip": False, "stroke_width": 2, "color": COR_EIXO}

# Mesmos números da simulação Mixer_plot.py, em MHz
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
    return mob.next_to(ax, UP, buff=0.05).align_to(ax, LEFT)


def polilinha(ax, xs, ys, cor, largura=3):
    return (VMobject()
            .set_points_as_corners([ax.c2p(a, b) for a, b in zip(xs, ys)])
            .set_stroke(cor, largura))


def curva(ax, func, cor, largura=3, n=600):
    xs = np.linspace(ax.x_range[0], ax.x_range[1], n)
    return polilinha(ax, xs, func(xs), cor, largura)


def haste(ax, x, y, cor, piso, largura=4):
    return Line(ax.c2p(x, piso), ax.c2p(x, y), color=cor, stroke_width=largura)


def marcar_x(ax, valores, y_base, tamanho=18):
    return VGroup(*[Text(f"{int(v)}", font_size=tamanho, color=GREY_B)
                    .next_to(ax.c2p(v, y_base), DOWN, buff=0.1)
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


def nivel(f_alvo):
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
        self.play(Write(t), Create(linha), run_time=1)
        return VGroup(t, linha)

    def legenda(self, texto, anterior=None, cor=GREY_A):
        nova = Text(texto, font_size=24, color=cor).to_edge(DOWN, buff=0.3)
        if anterior is None:
            self.play(FadeIn(nova, shift=UP * 0.2), run_time=0.7)
        else:
            self.play(FadeOut(anterior, shift=UP * 0.2),
                      FadeIn(nova, shift=UP * 0.2), run_time=0.7)
        return nova

    def limpar(self):
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
        self.wait(0.2)

    def eixo_espectro(self, centro=P(0, -0.3), largura=11.5, altura=3.6,
                      piso=-80, topo=10):
        ax = eixos(centro, largura, altura, [0, F_MAX, 100], [piso, topo, 20])
        rot_x = Text("frequência [MHz]", font_size=20, color=GREY_A).next_to(
            ax, DOWN, buff=0.35)
        rot_y = Text("amplitude [dB]", font_size=20, color=GREY_A).rotate(
            PI / 2).next_to(ax, LEFT, buff=0.15)
        return ax, VGroup(rot_x, rot_y, marcar_x(ax, [0, 100, 200, 300, 400, 500],
                                                 piso))

    def crescer_raias(self, ax, pares, piso, tamanho=15, destaque=None):
        """Desenha e anima as raias (m,n) pedidas sobre um eixo de espectro."""
        grupo = VGroup()
        for m, n in pares:
            f = abs(m * F_RF + n * F_LO)
            db = max(nivel(f), piso + 5)
            cor = cor_raia(m, n)
            rot = Text(rotular(m, n), font_size=tamanho, color=cor)
            grupo.add(VGroup(haste(ax, f, db, cor, piso),
                             rot.next_to(ax.c2p(f, db), UP, buff=0.06)))
        self.play(LaggedStart(*[AnimationGroup(GrowFromEdge(g[0], DOWN),
                                               FadeIn(g[1]))
                                for g in grupo], lag_ratio=0.25), run_time=1.1)
        if destaque is not None:
            self.play(*[Indicate(g[0], color=destaque, scale_factor=1.15)
                        for g in grupo], run_time=0.8)
        return grupo

    # ---------------------------------------------------------------- abertura
    def abertura(self):
        titulo = Text("Mixer de RF", font_size=64, weight=BOLD)
        sub = Text("por que multiplicar dois sinais cria uma família inteira "
                   "de espúrios", font_size=28, color=GREY_A)
        eq = tex_partes([(r"v_{IF}(t) = ", WHITE), (r"v_{RF}(t)", COR_RF),
                         (r"\cdot", WHITE), (r"v_{LO}(t)", COR_LO)], 42)
        g = VGroup(titulo, sub, eq).arrange(DOWN, buff=0.45)
        self.play(Write(titulo), run_time=1.5)
        self.play(FadeIn(sub, shift=UP * 0.2), FadeIn(eq, shift=UP * 0.2))
        self.wait(1.4)
        self.play(FadeOut(g))

    # ================================================================== CENA 1
    def cena_ideal(self):
        self.titulo_cena("1 · O mixer ideal: multiplicação pura")

        # Diagrama RF x LO -> IF
        mix = multiplicador().move_to(P(-4.6, 1.2))
        e_rf = tex(r"v_{RF}", COR_RF, 30).next_to(mix, LEFT, buff=0.9)
        e_lo = tex(r"v_{LO}", COR_LO, 30).next_to(mix, DOWN, buff=0.9)
        s_if = tex(r"v_{IF}", COR_IF, 30).next_to(mix, RIGHT, buff=0.9)
        fios = VGroup(
            fio([e_rf.get_right() + RIGHT * 0.15, mix.get_left()], COR_RF),
            fio([e_lo.get_top() + UP * 0.15, mix.get_bottom()], COR_LO),
            fio([mix.get_right(), s_if.get_left() + LEFT * 0.15], COR_IF))
        diagrama = VGroup(mix, e_rf, e_lo, s_if, fios)

        leg = self.legenda("O mixer entrega o produto ponto a ponto dos dois sinais")
        self.play(FadeIn(diagrama, shift=RIGHT * 0.2), run_time=1.2)

        # As duas entradas e o produto
        ax_rf = eixos(P(2.1, 2.5), 6.6, 1.0, [0, 4, 1], [-1.2, 1.2, 1])
        ax_lo = eixos(P(2.1, 1.1), 6.6, 1.0, [0, 4, 1], [-1.2, 1.2, 1])
        ax_if = eixos(P(0.6, -1.1), 9.6, 1.9, [0, 4, 1], [-1.2, 1.2, 1])
        o_rf = curva(ax_rf, lambda x: np.cos(2 * np.pi * FD_RF * x), COR_RF)
        o_lo = curva(ax_lo, lambda x: np.cos(2 * np.pi * FD_LO * x), COR_LO)
        o_if = curva(ax_if, lambda x: (np.cos(2 * np.pi * FD_RF * x)
                                       * np.cos(2 * np.pi * FD_LO * x)), COR_IF)
        rots = VGroup(rotulo_eixo(ax_rf, tex(r"v_{RF}(t)", COR_RF, 24)),
                      rotulo_eixo(ax_lo, tex(r"v_{LO}(t)", COR_LO, 24)),
                      rotulo_eixo(ax_if, tex(r"v_{RF}\cdot v_{LO}", COR_IF, 24)))

        self.play(Create(ax_rf), Create(ax_lo), FadeIn(rots[0]), FadeIn(rots[1]),
                  run_time=1.0)
        self.play(Create(o_rf), Create(o_lo), run_time=1.6)
        leg = self.legenda("Multiplicando ponto a ponto, aparece um batimento", leg)
        self.play(Create(ax_if), FadeIn(rots[2]), run_time=0.8)
        self.play(Create(o_if), run_time=1.8)
        self.wait(0.6)

        # A pergunta que importa: que frequências existem aí dentro?
        leg = self.legenda("Mas que frequências existem dentro desse batimento?",
                           leg, COR_LO)
        self.play(FadeOut(VGroup(diagrama, ax_rf, ax_lo, o_rf, o_lo, rots[0],
                                 rots[1])),
                  VGroup(ax_if, o_if, rots[2]).animate.move_to(P(0, 1.5)),
                  run_time=1.2)

        # Decomposição: o produto é a SOMA de duas senoides novas
        ax_d = eixos(P(0, -1.0), 9.6, 1.9, [0, 4, 1], [-1.2, 1.2, 1])
        c_dif = curva(ax_d, lambda x: 0.5 * np.cos(2 * np.pi * FD_IF * x),
                      COR_IF, 3)
        c_som = curva(ax_d, lambda x: 0.5 * np.cos(2 * np.pi * FD_SOMA * x),
                      COR_SOMA, 3)
        r_dif = Text("½·cos[(ω_LO − ω_RF)t]   ← a IF, lenta",
                     font_size=20, color=COR_IF).move_to(P(-2.6, -2.25))
        r_som = Text("½·cos[(ω_LO + ω_RF)t]   ← a soma, rápida",
                     font_size=20, color=COR_SOMA).move_to(P(2.9, -2.25))

        leg = self.legenda("Duas, e apenas duas: uma lenta e uma rápida", leg)
        self.play(Create(ax_d), run_time=0.6)
        self.play(Create(c_dif), FadeIn(r_dif), run_time=1.3)
        self.play(Create(c_som), FadeIn(r_som), run_time=1.3)

        leg = self.legenda("Somando as duas, reconstruímos exatamente o produto",
                           leg, COR_IF)
        soma = VGroup(c_dif.copy(), c_som.copy())
        self.play(soma.animate.move_to(ax_if.c2p(2, 0)), run_time=1.4)
        self.play(FadeOut(soma, scale=0.9), Indicate(o_if, color=COR_IF,
                                                     scale_factor=1.05),
                  Flash(ax_if.c2p(2, 0), color=COR_IF, line_length=0.3),
                  run_time=1.4)

        ident = tex_partes([
            (r"\cos(\omega_{RF}t)\cos(\omega_{LO}t)", WHITE),
            (r"=\tfrac{1}{2}\cos[(\omega_{LO}-\omega_{RF})t]", COR_IF),
            (r"+\tfrac{1}{2}\cos[(\omega_{LO}+\omega_{RF})t]", COR_SOMA)],
            32).move_to(P(0, 2.9))
        self.play(Write(ident), run_time=2.0)
        self.wait(1.2)

        # O mesmo fato, visto no espectro
        leg = self.legenda("No espectro, isso é o retrato mais simples possível",
                           leg)
        self.play(FadeOut(VGroup(ax_if, o_if, rots[2], ax_d, c_dif, c_som,
                                 r_dif, r_som)),
                  ident.animate.scale(0.9).move_to(P(0, 2.9)), run_time=1.0)
        ax, rotulos = self.eixo_espectro(P(0, -0.4), 11.0, 3.2)
        self.play(Create(ax), FadeIn(rotulos), run_time=1.0)
        self.crescer_raias(ax, [(1, -1), (1, 1)], -80, tamanho=20)
        etiq = VGroup(
            Text("30 MHz", font_size=20, color=COR_IF)
            .next_to(ax.c2p(F_IF, nivel(F_IF)), UP, buff=0.45),
            Text("230 MHz", font_size=20, color=COR_SOMA)
            .next_to(ax.c2p(F_RF + F_LO, nivel(F_RF + F_LO)), UP, buff=0.45))
        self.play(FadeIn(etiq), run_time=0.7)
        leg = self.legenda("Esse é o alvo. Agora: o hardware consegue fazer isso?",
                           leg, COR_LO)
        self.wait(1.6)
        self.limpar()

    # ================================================================== CENA 2
    def cena_diodo(self):
        self.titulo_cena("2 · Nenhum componente analógico multiplica tensões")

        ax = eixos(P(-3.8, 0.2), 5.0, 3.8, [-1, 2.2, 1], [-0.5, 3.0, 1])
        rot = VGroup(tex(r"i", COR_EIXO, 26).next_to(ax, UP, buff=0.05)
                     .align_to(ax, LEFT),
                     tex(r"v", COR_EIXO, 26).next_to(ax, RIGHT, buff=0.1))
        k = 1.6
        diodo = curva(ax, lambda x: np.clip(np.exp(k * x) - 1, -0.5, 3.0),
                      COR_VAZA, 4)
        eq_diodo = tex(r"i = I_s\left(e^{v/V_T}-1\right)", COR_VAZA, 26)\
            .next_to(ax, DOWN, buff=0.35)

        leg = self.legenda("O que existe de verdade é uma curva suave, "
                           "não um multiplicador")
        self.play(Create(ax), FadeIn(rot), run_time=0.9)
        self.play(Create(diodo), run_time=1.6)
        self.play(Write(eq_diodo), run_time=1.0)

        # Ponto de operação e aproximações sucessivas
        vq = 0.9
        iq = math.exp(k * vq) - 1
        ponto = Dot(ax.c2p(vq, iq), color=COR_LO, radius=0.09)
        rot_q = tex(r"Q", COR_LO, 26).next_to(ponto, UR, buff=0.08)
        leg = self.legenda("Em torno do ponto de operação, expandimos em "
                           "série de Taylor", leg)
        self.play(FadeIn(ponto, scale=0.4), Write(rot_q), run_time=0.8)

        def taylor(ordem):
            def f(x):
                d = x - vq
                y = -np.ones_like(d)
                for j in range(ordem + 1):
                    y = y + (iq + 1) * (k * d) ** j / math.factorial(j)
                return np.clip(y, -0.5, 3.0)
            return f

        aprox = curva(ax, taylor(1), COR_LO, 3)
        rotulo_ap = Text("ordem 1: só uma reta", font_size=20, color=COR_LO)\
            .move_to(P(-3.8, 2.6))
        self.play(Create(aprox), FadeIn(rotulo_ap), run_time=1.2)
        for ordem, nome in [(2, "ordem 2: já acompanha a curvatura"),
                            (3, "ordem 3: acompanha melhor ainda")]:
            self.play(Transform(aprox, curva(ax, taylor(ordem), COR_LO, 3)),
                      Transform(rotulo_ap, Text(nome, font_size=20, color=COR_LO)
                                .move_to(P(-3.8, 2.6))),
                      run_time=1.2)

        eq = tex_partes([(r"v_{out} = ", WHITE), (r"a\,v_{in}", COR_VAZA),
                         (r" + b\,v_{in}^2", COR_IF), (r" + c\,v_{in}^3", COR_IMD),
                         (r" + \dots", WHITE)], 32).move_to(P(3.0, 2.5))
        self.play(Write(eq), run_time=1.6)

        # O que a curva faz com uma soma de dois tons
        leg = self.legenda("Veja o que essa curva faz com a soma dos dois sinais",
                           leg, COR_LO)
        ax_in = eixos(P(3.3, 0.9), 6.4, 1.3, [0, 4, 1], [-2.4, 2.4, 1])
        ax_out = eixos(P(3.3, -1.3), 6.4, 1.8, [0, 4, 1], [-1.5, 4.5, 1])

        def v_in(x):
            return np.cos(2 * np.pi * FD_RF * x) + np.cos(2 * np.pi * FD_LO * x)

        def v_out(x):
            v = v_in(x)
            return sum(c * v ** (j + 1) for j, c in enumerate(COEFS[:3]))

        o_in = curva(ax_in, v_in, COR_RF)
        o_out = curva(ax_out, v_out, COR_IMD)
        r_in = rotulo_eixo(ax_in, tex_partes([(r"v_{in} = ", WHITE),
                                              (r"v_{RF}", COR_RF), (r"+", WHITE),
                                              (r"v_{LO}", COR_LO)], 22))
        r_out = rotulo_eixo(ax_out, tex(r"v_{out} = a v_{in} + b v_{in}^2 "
                                        r"+ c v_{in}^3", COR_IMD, 22))
        self.play(Create(ax_in), FadeIn(r_in), run_time=0.7)
        self.play(Create(o_in), run_time=1.3)
        self.play(Create(ax_out), FadeIn(r_out), run_time=0.7)
        self.play(TransformFromCopy(o_in, o_out), run_time=2.2)

        nota = Text("a forma mudou → há frequências novas lá dentro",
                    font_size=24, color=COR_OK).move_to(P(0, -2.9))
        self.play(FadeIn(nota, shift=UP * 0.15), run_time=0.8)
        leg = self.legenda("Entraram somados; saíram deformados. "
                           "A mistura é efeito colateral da deformação.",
                           leg, COR_IF)
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 3
    def cena_termos(self):
        self.titulo_cena("3 · Quem gera o quê")

        cab = tex_partes([(r"v_{out} = a(", WHITE), (r"v_{RF}", COR_RF),
                          (r"\!+\!", WHITE), (r"v_{LO}", COR_LO),
                          (r") + b(", WHITE), (r"v_{RF}", COR_RF),
                          (r"\!+\!", WHITE), (r"v_{LO}", COR_LO),
                          (r")^2 + c(", WHITE), (r"v_{RF}", COR_RF),
                          (r"\!+\!", WHITE), (r"v_{LO}", COR_LO),
                          (r")^3", WHITE)], 30).move_to(P(0, 3.05))
        self.play(Write(cab), run_time=2.0)

        # Mini-espectro que vai sendo preenchido termo a termo
        piso = -60
        ax = eixos(P(0, -2.0), 11.0, 1.5, [0, F_MAX, 100], [piso, 10, 20])
        marcas = VGroup(marcar_x(ax, [0, 100, 200, 300, 400, 500], piso, 16),
                        Text("espectro de saída [MHz]", font_size=18,
                             color=GREY_A).next_to(ax, UP, buff=0.06)
                        .align_to(ax, LEFT))
        self.play(Create(ax), FadeIn(marcas), run_time=0.9)

        # --- termo linear ----------------------------------------------------
        leg = self.legenda("Termo linear: o que entra, sai — nenhuma "
                           "frequência nova")
        t1 = tex_partes([(r"a\,v_{in} = ", COR_VAZA),
                         (r"a\cos\omega_{RF}t", COR_RF), (r"\;+\;", WHITE),
                         (r"a\cos\omega_{LO}t", COR_LO)], 34).move_to(P(0, 1.5))
        n1 = Text("vazamento das portadoras para a saída", font_size=24,
                  color=COR_VAZA).move_to(P(0, 0.75))
        self.play(Write(t1), run_time=1.4)
        self.play(FadeIn(n1, shift=UP * 0.15), run_time=0.7)
        self.crescer_raias(ax, [(1, 0), (0, -1)], piso)
        self.wait(0.6)

        # --- termo quadrático ------------------------------------------------
        leg = self.legenda("Termo quadrático: é aqui, e só aqui, que nasce "
                           "a multiplicação", leg, COR_IF)
        t2 = tex_partes([(r"b\,v_{in}^2 = b\,v_{RF}^2", WHITE),
                         (r"\;+\;2b\,v_{RF}v_{LO}", COR_IF),
                         (r"\;+\;b\,v_{LO}^2", WHITE)], 34).move_to(P(0, 1.5))
        self.play(FadeOut(n1), ReplacementTransform(t1, t2), run_time=1.2)
        cx = SurroundingRectangle(t2[1], color=COR_IF, buff=0.08,
                                  corner_radius=0.06)
        self.play(Create(cx), run_time=0.7)
        t2b = tex_partes([(r"2b\cos\omega_{RF}t\,\cos\omega_{LO}t = ", WHITE),
                          (r"b\cos(\omega_{LO}\!-\!\omega_{RF})t", COR_IF),
                          (r"\;+\;b\cos(\omega_{LO}\!+\!\omega_{RF})t", COR_SOMA)],
                         28).move_to(P(0, 0.7))
        self.play(Write(t2b), run_time=1.8)
        self.crescer_raias(ax, [(1, -1), (1, 1)], piso, destaque=COR_IF)
        n2 = Text("os quadrados dos termos isolados viram DC e 2º harmônico",
                  font_size=22, color=GREY_A).move_to(P(0, 0.0))
        self.play(FadeIn(n2), run_time=0.7)
        self.crescer_raias(ax, [(2, 0), (0, -2)], piso)
        self.wait(0.6)

        # --- termo cúbico ----------------------------------------------------
        leg = self.legenda("Termo cúbico: intermodulação — os espúrios que "
                           "mais incomodam", leg, COR_IMD)
        t3 = tex_partes([(r"c\,v_{in}^3 = v_{RF}^3", WHITE),
                         (r"\;+\;3v_{RF}^2v_{LO}", COR_IMD),
                         (r"\;+\;3v_{RF}v_{LO}^2", COR_IMD),
                         (r"\;+\;v_{LO}^3", WHITE)], 32).move_to(P(0, 1.5))
        self.play(FadeOut(VGroup(cx, t2b, n2)),
                  ReplacementTransform(t2, t3), run_time=1.2)
        n3 = VGroup(
            Text("produtos cruzados  →  2f_LO ± f_RF  e  2f_RF ± f_LO",
                 font_size=23, color=COR_IMD),
            Text("cubos isolados  →  3f_RF  e  3f_LO", font_size=23,
                 color=COR_VAZA),
            Text("e parte volta a cair sobre f_RF e f_LO → compressão de ganho "
                 "(P1dB)", font_size=23, color=COR_LO),
        ).arrange(DOWN, buff=0.2).move_to(P(0, 0.35))
        self.play(LaggedStart(*[FadeIn(i, shift=RIGHT * 0.2) for i in n3],
                              lag_ratio=0.35), run_time=2.0)
        self.crescer_raias(ax, [(2, -1), (1, -2), (3, 0), (0, -3)], piso)
        leg = self.legenda("Cada potência do polinômio abre um novo grupo "
                           "de frequências", leg)
        self.wait(1.6)
        self.limpar()

    # ================================================================== CENA 4
    def cena_familia(self):
        self.titulo_cena("4 · A família  m·f_RF ± n·f_LO")

        regra = tex(r"f_{esp\acute{u}rio} = |\,m\,f_{RF} \pm n\,f_{LO}\,|,"
                    r"\qquad \text{ordem} = m+|n|", WHITE, 32).move_to(P(0, 2.9))
        ax, rotulos = self.eixo_espectro(P(0, -0.5), 11.0, 3.4)
        self.play(Write(regra), run_time=1.4)
        self.play(Create(ax), FadeIn(rotulos), run_time=1.0)

        legenda_cores = VGroup(*[
            VGroup(Dot(color=c, radius=0.07),
                   Text(t, font_size=17, color=c)).arrange(RIGHT, buff=0.12)
            for c, t in [(COR_IF, "IF e harmônicos"),
                         (COR_SOMA, "banda soma"),
                         (COR_VAZA, "vazamento / harmônico puro"),
                         (COR_IMD, "intermodulação")]
        ]).arrange(DOWN, aligned_edge=LEFT, buff=0.1).to_corner(UR, buff=0.35)
        self.play(FadeIn(legenda_cores), run_time=0.8)

        descricao = {1: "ordem 1 — o que simplesmente vazou da entrada",
                     2: "ordem 2 — a IF útil, a banda soma e os 2º harmônicos",
                     3: "ordem 3 — intermodulação: caem perto e são difíceis "
                        "de filtrar",
                     4: "ordem 4 — mais fracas, mas a família não tem fim"}
        leg = self.legenda("Vamos construir o espectro real, ordem por ordem")
        tudo = VGroup()
        for ordem in (1, 2, 3, 4):
            grupo = VGroup()
            for f, m, n in familia(ordem):
                db = nivel(f)
                if db < -78:
                    continue
                cor = cor_raia(m, n)
                rot = Text(rotular(m, n), font_size=16, color=cor)\
                    .next_to(ax.c2p(f, db), UP, buff=0.07)
                if ordem >= 3:
                    rot.scale(0.85).set_opacity(0.85)
                grupo.add(VGroup(haste(ax, f, db, cor, -80), rot))
            leg = self.legenda(descricao[ordem], leg,
                               COR_IF if ordem == 2 else GREY_A)
            self.play(LaggedStart(*[GrowFromEdge(g[0], DOWN) for g in grupo],
                                  lag_ratio=0.15), run_time=1.3)
            self.play(LaggedStart(*[FadeIn(g[1]) for g in grupo],
                                  lag_ratio=0.1), run_time=0.9)
            tudo.add(grupo)
            self.wait(0.4)

        leg = self.legenda("Quanto maior a ordem, mais fraca a raia — "
                           "mas há raias por todo o eixo", leg)
        self.wait(1.0)

        alvo = SurroundingRectangle(tudo[1][0], color=COR_IF, buff=0.12,
                                    corner_radius=0.06)
        leg = self.legenda("De tudo isso, uma única raia é o sinal desejado",
                           leg, COR_IF)
        self.play(Create(alvo), *[t.animate.set_opacity(0.3) for t in tudo[2:]],
                  run_time=1.2)
        sfdr = Text("SFDR ≈ 5 dBc — o maior espúrio está quase no nível da IF",
                    font_size=24, color=COR_VAZA).move_to(P(0, -2.9))
        self.play(FadeIn(sfdr), run_time=0.8)
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 5
    def cena_imagem(self):
        self.titulo_cena("5 · A frequência imagem não é defeito do componente")

        ax = eixos(P(0, 1.5), 10.0, 1.6, [0, 220, 50], [0, 1.2, 1])
        rot_x = Text("frequência de entrada [MHz]", font_size=20, color=GREY_A)\
            .next_to(ax, DOWN, buff=0.4)
        self.play(Create(ax), FadeIn(marcar_x(ax, [0, 50, 100, 150, 200], 0)),
                  FadeIn(rot_x), run_time=1.0)

        h_lo = haste(ax, F_LO, 1.1, COR_LO, 0, largura=5)
        h_rf = haste(ax, F_RF, 0.8, COR_RF, 0, largura=5)
        h_im = haste(ax, F_IMG, 0.8, COR_IMG, 0, largura=5)
        e_lo = Text("LO (130)", font_size=20, color=COR_LO)\
            .next_to(ax.c2p(F_LO, 1.1), UP, buff=0.08)
        e_rf = Text("RF desejado (100)", font_size=20, color=COR_RF)\
            .next_to(ax.c2p(F_RF, 0.8), UP, buff=0.08).shift(LEFT * 0.5)
        e_im = Text("imagem (160)", font_size=20, color=COR_IMG)\
            .next_to(ax.c2p(F_IMG, 0.8), UP, buff=0.08).shift(RIGHT * 0.4)

        leg = self.legenda("Duas entradas simétricas em torno do LO")
        self.play(GrowFromEdge(h_lo, DOWN), FadeIn(e_lo), run_time=0.7)
        self.play(GrowFromEdge(h_rf, DOWN), FadeIn(e_rf), run_time=0.7)
        self.play(GrowFromEdge(h_im, DOWN), FadeIn(e_im), run_time=0.7)

        d1 = DoubleArrow(ax.c2p(F_RF, 0.35), ax.c2p(F_LO, 0.35), buff=0,
                         color=COR_RF, stroke_width=3,
                         max_tip_length_to_length_ratio=0.1)
        d2 = DoubleArrow(ax.c2p(F_LO, 0.35), ax.c2p(F_IMG, 0.35), buff=0,
                         color=COR_IMG, stroke_width=3,
                         max_tip_length_to_length_ratio=0.1)
        t1 = Text("30", font_size=18, color=COR_RF).next_to(d1, DOWN, buff=0.05)
        t2 = Text("30", font_size=18, color=COR_IMG).next_to(d2, DOWN, buff=0.05)
        self.play(GrowArrow(d1), GrowArrow(d2), FadeIn(t1), FadeIn(t2),
                  run_time=1.0)

        ax2 = eixos(P(0, -1.2), 4.4, 0.9, [0, 60, 30], [0, 1.4, 1])
        h_if = haste(ax2, 30, 1.3, COR_IF, 0, largura=6)
        e_if = Text("IF = 30 MHz", font_size=20, color=COR_IF)\
            .next_to(ax2.c2p(30, 1.3), RIGHT, buff=0.25)
        c1 = CurvedArrow(ax.c2p(F_RF, 0.1), ax2.c2p(30, 1.35), color=COR_RF,
                         angle=0.7, stroke_width=3, tip_length=0.18)
        c2 = CurvedArrow(ax.c2p(F_IMG, 0.1), ax2.c2p(30, 1.35), color=COR_IMG,
                         angle=-0.7, stroke_width=3, tip_length=0.18)
        leg = self.legenda("As duas caem exatamente na mesma IF — e se somam lá",
                           leg, COR_IMG)
        self.play(Create(ax2), run_time=0.5)
        self.play(Create(c1), Create(c2), run_time=1.4)
        self.play(GrowFromEdge(h_if, DOWN), FadeIn(e_if), run_time=0.8)
        eq = tex(r"|f_{LO}-f_{RF}| = |f_{LO}-f_{IM}| = 30\ \text{MHz}",
                 WHITE, 30).move_to(P(0, -2.4))
        self.play(Write(eq), run_time=1.4)
        self.wait(1.2)

        # Por quê: o cosseno é a soma de dois fasores girando em sentidos opostos
        leg = self.legenda("Por que isso acontece? Olhe o que é um cosseno real",
                           leg, COR_LO)
        self.play(FadeOut(VGroup(ax, ax2, rot_x, h_lo, h_rf, h_im, e_lo, e_rf,
                                 e_im, d1, d2, t1, t2, h_if, e_if, c1, c2, eq)),
                  run_time=0.8)

        centro = P(-3.6, 0.2)
        circ = Circle(radius=1.5, color=COR_EIXO, stroke_width=2)\
            .move_to(centro)
        ex = Line(centro + LEFT * 1.8, centro + RIGHT * 1.8, color=COR_EIXO,
                  stroke_width=2)
        ey = Line(centro + DOWN * 1.8, centro + UP * 1.8, color=COR_EIXO,
                  stroke_width=2)
        ang = PI / 5
        f_pos = Arrow(centro, centro + 1.5 * np.array([np.cos(ang), np.sin(ang), 0]),
                      buff=0, color=COR_RF, stroke_width=5,
                      max_tip_length_to_length_ratio=0.15)
        f_neg = Arrow(centro, centro + 1.5 * np.array([np.cos(-ang), np.sin(-ang), 0]),
                      buff=0, color=COR_IMG, stroke_width=5,
                      max_tip_length_to_length_ratio=0.15)
        r_pos = tex(r"e^{+j\omega t}", COR_RF, 26)\
            .move_to(centro + UP * 1.9 + RIGHT * 1.3)
        r_neg = tex(r"e^{-j\omega t}", COR_IMG, 26)\
            .move_to(centro + DOWN * 1.9 + RIGHT * 1.3)
        eq_euler = tex(r"\cos\omega t = \tfrac{1}{2}\left(e^{+j\omega t}"
                       r" + e^{-j\omega t}\right)", WHITE, 32)\
            .move_to(P(2.9, 1.9))
        self.play(Create(circ), Create(ex), Create(ey), run_time=0.9)
        self.play(GrowArrow(f_pos), GrowArrow(f_neg), FadeIn(r_pos), FadeIn(r_neg),
                  run_time=1.0)
        self.play(Write(eq_euler), run_time=1.6)
        leg = self.legenda("Um LO real gira nos DOIS sentidos ao mesmo tempo",
                           leg, COR_IMG)
        self.play(Rotate(f_pos, TAU, about_point=centro, rate_func=linear),
                  Rotate(f_neg, -TAU, about_point=centro, rate_func=linear),
                  run_time=3.0)

        conclusao = VGroup(
            Text("o fasor +ω desloca o espectro para baixo", font_size=23,
                 color=COR_RF),
            Text("o fasor −ω desloca para cima", font_size=23, color=COR_IMG),
            Text("os dois deslocamentos se sobrepõem na IF → imagem",
                 font_size=23, color=COR_VAZA),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to(P(2.9, 0.0))
        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT * 0.2) for c in conclusao],
                              lag_ratio=0.35), run_time=2.0)
        self.wait(1.0)

        sol = VGroup(
            tex(r"e^{-j\omega_{LO}t} = \cos\omega_{LO}t - j\sin\omega_{LO}t",
                COR_FPGA, 30),
            Text("usar só um dos sentidos: dois multiplicadores, I e Q",
                 font_size=23, color=GREY_A),
            Text("a imagem é rejeitada por construção", font_size=24,
                 color=COR_OK),
        ).arrange(DOWN, buff=0.25).move_to(P(2.9, -2.1))
        leg = self.legenda("A solução: um LO que gira num sentido só — "
                           "é o que o DDC faz", leg, COR_FPGA)
        self.play(LaggedStart(*[FadeIn(s, shift=UP * 0.2) for s in sol],
                              lag_ratio=0.3), run_time=2.2)
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 6
    def cena_digital(self):
        self.titulo_cena("6 · No FPGA a multiplicação é de verdade")

        y = 2.0
        adc = caixa_texto("ADC", 1.3, 0.7, COR_RF, 22).move_to(P(-5.2, y))
        mult = multiplicador(COR_FPGA).move_to(P(-2.9, y))
        cic = caixa_texto("CIC", 1.2, 0.7, COR_IMD, 22).move_to(P(-0.6, y))
        fir = caixa_texto("FIR", 1.2, 0.7, COR_IF, 22).move_to(P(1.6, y))
        saida = tex(r"I,\;Q", COR_OK, 28).move_to(P(3.6, y))
        acc = caixa_texto("acumulador\nde fase", 1.9, 0.9, COR_LO, 18)\
            .move_to(P(-5.0, 0.3))
        lut = caixa_texto("LUT\ncos/sen", 1.5, 0.9, COR_LO, 18)\
            .move_to(P(-2.9, 0.3))
        fios = VGroup(
            fio([adc.get_right(), mult.get_left()], COR_RF),
            fio([mult.get_right(), cic.get_left()], COR_FPGA),
            fio([cic.get_right(), fir.get_left()], COR_IMD),
            fio([fir.get_right(), saida.get_left() + LEFT * 0.15], COR_IF),
            fio([acc.get_right(), lut.get_left()], COR_LO),
            fio([lut.get_top(), mult.get_bottom()], COR_LO))
        dds = Text("DDS", font_size=22, color=COR_LO)\
            .next_to(VGroup(acc, lut), DOWN, buff=0.2)
        diagrama = VGroup(adc, mult, cic, fir, saida, acc, lut, fios, dds)

        leg = self.legenda("O produto é feito num DSP slice: aritmética exata, "
                           "sem ponto de polarização")
        self.play(LaggedStart(FadeIn(adc), FadeIn(mult), FadeIn(cic),
                              FadeIn(fir), FadeIn(saida), lag_ratio=0.25),
                  run_time=1.8)
        self.play(FadeIn(acc), FadeIn(lut), FadeIn(dds), run_time=1.0)
        self.play(Create(fios), run_time=1.6)

        ganhos = VGroup(
            Text("sem termo linear   →  nenhum vazamento de LO ou RF",
                 font_size=23, color=COR_OK),
            Text("sem termo cúbico   →  nenhuma intermodulação, nenhum P1dB",
                 font_size=23, color=COR_OK),
            Text("27×18 bits guardados em 48  →  produto bit-exato",
                 font_size=23, color=COR_OK),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.26).move_to(P(1.8, -0.6))
        self.play(LaggedStart(*[FadeIn(g, shift=RIGHT * 0.2) for g in ganhos],
                              lag_ratio=0.35), run_time=2.0)
        leg = self.legenda("A Cena 4 inteira desaparece: não há o que filtrar",
                           leg, COR_OK)
        self.wait(1.4)

        # De onde vêm, então, os espúrios digitais
        leg = self.legenda("Mas 'preciso' não é 'perfeito'. Olhe dentro do DDS.",
                           leg, COR_LO)
        self.play(FadeOut(VGroup(diagrama, ganhos)), run_time=0.8)

        ax_f = eixos(P(-3.5, 1.2), 5.4, 1.7, [0, 4, 1], [0, 1.15, 1])
        ax_c = eixos(P(3.3, 1.2), 5.4, 1.7, [0, 4, 1], [-1.2, 1.2, 1])
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
                  run_time=0.9)
        self.play(Create(c_rampa), run_time=1.2)
        self.play(Create(c_ideal), run_time=1.2)
        leg = self.legenda("A fase tem 32 bits, mas só os 14 de cima endereçam "
                           "a LUT", leg)
        self.play(Create(c_degrau), run_time=1.3)
        self.play(Create(c_quant), run_time=1.3)
        leg = self.legenda("O erro de truncamento é periódico — "
                           "e tudo que é periódico vira raia", leg, COR_IMD)

        quant = VGroup(
            tex(r"\text{SFDR} \approx -6{,}02 \times B_{\text{end}}\ "
                r"\text{dBc}", COR_IMD, 34),
            Text("14 bits de endereço  →  −84 dBc", font_size=24, color=COR_OK),
            Text("é exatamente o que a simulação mediu: 84,1 dBc",
                 font_size=22, color=GREY_A),
            Text("espúrio projetado no papel, não dependente de temperatura",
                 font_size=22, color=COR_OK),
        ).arrange(DOWN, buff=0.26).move_to(P(0, -1.5))
        self.play(LaggedStart(*[FadeIn(q, shift=UP * 0.15) for q in quant],
                              lag_ratio=0.3), run_time=2.4)
        self.wait(1.6)

        # O caso f_s/4
        leg = self.legenda("E há um caso em que nem multiplicador é preciso",
                           leg, COR_FPGA)
        self.play(FadeOut(VGroup(ax_f, ax_c, r_f, r_c, c_rampa, c_degrau,
                                 c_ideal, c_quant, quant)), run_time=0.8)

        centro = P(-3.6, 0.1)
        circ = Circle(radius=1.5, color=COR_EIXO, stroke_width=2).move_to(centro)
        eixos_c = VGroup(
            Line(centro + LEFT * 1.9, centro + RIGHT * 1.9, color=COR_EIXO,
                 stroke_width=2),
            Line(centro + DOWN * 1.9, centro + UP * 1.9, color=COR_EIXO,
                 stroke_width=2))
        pontos, rotp = VGroup(), VGroup()
        for j, (dx, dy, txt) in enumerate([(1, 0, "cos = 1\nsen = 0"),
                                           (0, 1, "cos = 0\nsen = 1"),
                                           (-1, 0, "cos = −1\nsen = 0"),
                                           (0, -1, "cos = 0\nsen = −1")]):
            pos = centro + 1.5 * np.array([dx, dy, 0.0])
            pontos.add(Dot(pos, color=COR_FPGA, radius=0.11))
            rotp.add(Text(txt, font_size=17, color=COR_LO, line_spacing=0.8)
                     .move_to(centro + 2.35 * np.array([dx, dy, 0.0])))
        self.play(Create(circ), Create(eixos_c), run_time=0.8)
        self.play(LaggedStart(*[AnimationGroup(GrowFromCenter(p), FadeIn(r))
                                for p, r in zip(pontos, rotp)], lag_ratio=0.3),
                  run_time=2.0)

        fs4 = VGroup(
            tex(r"f_{LO} = f_s/4", COR_FPGA, 38),
            Text("4 amostras por volta, sempre nos mesmos 4 pontos",
                 font_size=23, color=GREY_A),
            tex(r"\cos \to \{1,\,0,\,-1,\,0\}", COR_LO, 30),
            tex(r"\sin \to \{0,\,1,\,0,\,-1\}", COR_LO, 30),
            Text("multiplicar por 0 ou ±1 é trocar sinal e multiplexar:\n"
                 "exato, sem LUT e sem DSP slice",
                 font_size=23, color=COR_OK, line_spacing=0.9),
        ).arrange(DOWN, buff=0.3).move_to(P(3.1, 0.1))
        self.play(LaggedStart(*[FadeIn(f, shift=UP * 0.2) for f in fs4],
                              lag_ratio=0.3), run_time=2.6)
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

        ax = eixos(P(-1.0, 0.1), 8.0, 3.6, [0, 120, 20], [0, 140, 40])
        marcas_y = VGroup(*[Text(f"{v}", font_size=18, color=GREY_B)
                            .next_to(ax.c2p(0, v), LEFT, buff=0.1)
                            for v in [0, 40, 80, 120]])
        rot_x = Text("frequência [MHz]", font_size=20, color=GREY_A)\
            .next_to(ax, DOWN, buff=0.4)
        rot_y = Text("atraso de grupo [ns]", font_size=20, color=GREY_A)\
            .rotate(PI / 2).next_to(ax, LEFT, buff=0.45)
        self.play(Create(ax), FadeIn(marcar_x(ax, [0, 20, 40, 60, 80, 100, 120], 0)),
                  FadeIn(marcas_y), FadeIn(rot_x), FadeIn(rot_y), run_time=1.2)

        c_el = polilinha(ax, f_mhz, np.clip(tau, 0, 140), COR_VAZA, 4)
        r_el = Text("elíptico analógico\nordem 7", font_size=19, color=COR_VAZA,
                    line_spacing=0.85).move_to(ax.c2p(85, 55))
        leg = self.legenda("Filtro com corte abrupto: o atraso dispara perto "
                           "da banda")
        self.play(Create(c_el), FadeIn(r_el), run_time=2.0)

        linha_if = DashedLine(ax.c2p(30, 0), ax.c2p(30, 140), color=GREY_B,
                              stroke_width=2)
        rot_if = Text("IF", font_size=18, color=GREY_A)\
            .next_to(ax.c2p(30, 140), UP, buff=0.06)
        self.play(Create(linha_if), FadeIn(rot_if), run_time=0.7)
        var = Text("varia 2,3× dentro da própria banda\n→ deforma o envelope",
                   font_size=20, color=COR_VAZA, line_spacing=0.85)\
            .move_to(ax.c2p(70, 120))
        self.play(FadeIn(var), run_time=0.9)
        self.wait(0.8)

        plano = Line(ax.c2p(0, 104), ax.c2p(120, 104), color=COR_IF,
                     stroke_width=4)
        r_fir = Text("FIR de fase linear, 53 taps", font_size=19, color=COR_IF)\
            .next_to(ax.c2p(60, 104), UP, buff=0.1)
        leg = self.legenda("O FIR não é mais rápido — é plano e previsível", leg,
                           COR_IF)
        self.play(Create(plano), FadeIn(r_fir), run_time=1.4)
        eq_tau = tex(r"\tau_g = \frac{N-1}{2}\,T_s", COR_IF, 30)\
            .move_to(P(4.6, 2.1))
        self.play(Write(eq_tau), run_time=1.2)

        leg = self.legenda("Numa malha de realimentação, atraso é margem "
                           "de fase perdida", leg, COR_LO)
        custo = VGroup(
            tex(r"\Delta\phi = -\,\omega\,\tau", COR_LO, 34),
            tex(r"f_{BW} \lesssim \frac{1}{10\,\tau_{total}}", COR_LO, 30),
            Text("cada ns gasto filtrando\né banda de controle perdida",
                 font_size=20, color=GREY_A, line_spacing=0.85),
        ).arrange(DOWN, buff=0.3).move_to(P(4.6, 0.0))
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.15) for c in custo],
                              lag_ratio=0.3), run_time=2.0)
        leg = self.legenda("O mixer digital ganha aqui: quase não há espúrio "
                           "para filtrar", leg, COR_OK)
        self.wait(2.0)
        self.limpar()

    # ================================================================== RESUMO
    def cena_resumo(self):
        titulo = Text("Resumo", font_size=44, weight=BOLD).move_to(P(0, 3.1))
        self.play(Write(titulo), run_time=1.0)

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
        g = VGroup(*[Text(t, font_size=26 if c != GREY_A else 22, color=c)
                     for t, c in linhas])
        for k, item in enumerate(g):
            if linhas[k][1] == GREY_A:
                item.shift(RIGHT * 0.4)
        g.arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to(P(0, 0.0))

        self.play(LaggedStart(*[FadeIn(i, shift=RIGHT * 0.2) for i in g],
                              lag_ratio=0.25), run_time=4.0)
        self.wait(2.0)

        fecho = Text("empurre o ADC para mais perto do pickup: cada mixer "
                     "analógico a menos\né uma família inteira de espúrios "
                     "a menos", font_size=24, color=COR_OK, line_spacing=0.9)\
            .move_to(P(0, -3.0))
        self.play(FadeIn(fecho), run_time=1.0)
        self.wait(2.5)
        self.limpar()
