# -*- coding: utf-8 -*-
"""
Up-conversion: do I/Q digital até a portadora de RF
===================================================

Renderização (a partir da raiz do repositório):
    manim -pql "src/Up-conversion/up_conversion.py" UpConversion   # rascunho
    manim -pqh "src/Up-conversion/up_conversion.py" UpConversion   # final

Requer LaTeX (MathTex).

Segue a seção 4 (Up-conversion) de T. Schilcher, "RF applications in digital
signal processing" (books/Schilcher.pdf, p. 266-268), incluindo as Figs. 21 a 24.

Roteiro:
    Abertura
    Cena 1 - O problema: a FPGA tem I e Q, a cavidade quer 500 MHz
    Cena 2 - I e Q constroem qualquer portadora
    Cena 3 - Modulador vetorial: up-conversion homodina (Fig. 21)
    Cena 4 - Com os mesmos dois botões: modulação de amplitude e de fase
    Cena 5 - O preço do caminho analógico: offset, ganho, skew e ruído de fase
    Cena 6 - Pré-distorção digital do skew de quadratura
    Cena 7 - Heteródino: subir primeiro para uma IF digital (Fig. 22)
    Cena 8 - Banda lateral única: cancelando a imagem (Figs. 23 e 24)
    Cena 9 - Comparando os três esquemas
    Resumo

Exemplo numérico usado em todas as cenas (o mesmo do resto do repositório):
    f_IF = 20 MHz, f_LO = 480 MHz, f_RF = 500 MHz, imagem em 460 MHz.

Layout: a tela é dividida em faixas fixas para que nada se sobreponha.
    y > 3.0          : título da cena (canto superior esquerdo)
    [Y_BASE, Y_TOPO] : área de desenho
    y ~ -3.6         : narração, uma linha por vez
"""

import numpy as np
from manim import *

# Paleta didática (mesma convenção das outras animações do repositório)
COR_I = GOLD             # canal I
COR_Q = GREEN            # canal Q
COR_RF = BLUE            # portadora / sinal de RF
COR_LO = GREY_A          # oscilador local
COR_DIG = TEAL           # domínio digital (FPGA, NCO, DDS)
COR_IF = ORANGE          # sinal de frequência intermediária
COR_ERRO = RED           # imagem, vazamento e erros
COR_FILTRO = PINK        # filtros
COR_EIXO = GREY_B
FUNDO = "#0e1117"

EIXO_CFG = {"include_tip": False, "stroke_width": 2, "color": COR_EIXO}

# Faixas de layout (a tela vai de -4 a 4 em y e de -7.1 a 7.1 em x)
Y_TOPO = 2.70
Y_BASE = -2.55
LARG_MAX = 12.8

# Frequências do exemplo, em MHz
F_IF, F_LO = 20.0, 480.0
F_RF = F_LO + F_IF        # 500 MHz
F_IMG = F_LO - F_IF       # 460 MHz


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


def txt(s, tamanho=22, cor=GREY_A, **kw):
    return Text(s, font_size=tamanho, color=cor, **kw)


def tex_partes(partes, tamanho=34):
    """Fórmula multicolorida. partes = [(tex, cor), ...]."""
    m = MathTex(*[p[0] for p in partes], font_size=tamanho)
    for sub, p in zip(m, partes):
        sub.set_color(p[1])
    return m


def fio(pontos, cor=WHITE, largura=3):
    """Caminho em segmentos retos terminando em seta."""
    g = VGroup(*[Line(pontos[k], pontos[k + 1], color=cor, stroke_width=largura)
                 for k in range(len(pontos) - 2)])
    g.add(Arrow(pontos[-2], pontos[-1], buff=0, color=cor, stroke_width=largura,
                max_tip_length_to_length_ratio=0.3, max_stroke_width_to_length_ratio=10))
    return g


def linha(pontos, cor=WHITE, largura=3):
    return VMobject().set_points_as_corners(pontos).set_stroke(cor, largura)


def caixa(rotulo, largura=1.6, altura=0.7, cor=WHITE, tamanho=20):
    r = RoundedRectangle(corner_radius=0.08, width=largura, height=altura, color=cor, stroke_width=3)
    return VGroup(r, Text(rotulo, color=cor, font_size=tamanho).move_to(r))


def caixa_tex(rotulo, largura=1.0, altura=0.7, cor=WHITE, tamanho=28):
    r = RoundedRectangle(corner_radius=0.08, width=largura, height=altura, color=cor, stroke_width=3)
    return VGroup(r, tex(rotulo, cor, tamanho).move_to(r))


def multiplicador(cor=WHITE, raio=0.3):
    """Símbolo do mixer: círculo com X."""
    c = Circle(radius=raio, color=cor, stroke_width=3)
    d = raio * 0.62
    x = VGroup(Line(P(-d, -d), P(d, d), color=cor, stroke_width=3),
               Line(P(-d, d), P(d, -d), color=cor, stroke_width=3))
    return VGroup(c, x.move_to(c))


def somador(cor=WHITE, raio=0.3):
    c = Circle(radius=raio, color=cor, stroke_width=3)
    return VGroup(c, tex(r"\Sigma", cor, 28).move_to(c))


def oscilador(cor=COR_LO, raio=0.3):
    """Símbolo de fonte senoidal: círculo com um til."""
    c = Circle(radius=raio, color=cor, stroke_width=3)
    onda = FunctionGraph(lambda t: 0.11 * np.sin(TAU * t), x_range=[-0.17, 0.17, 0.01],
                         color=cor, stroke_width=3).scale(1.0).move_to(c)
    return VGroup(c, onda)


def eixos(centro, largura, altura, x_range, y_range):
    return Axes(x_range=x_range, y_range=y_range, x_length=largura, y_length=altura,
                axis_config=EIXO_CFG).move_to(centro)


def rotulo_eixo(ax, mob, buff=0.08):
    return mob.next_to(ax, UP, buff=buff).align_to(ax, LEFT)


def polilinha(ax, xs, ys, cor, largura=3):
    return linha([ax.c2p(a, b) for a, b in zip(xs, ys)], cor, largura)


def curva(ax, func, cor, largura=3, n=500, x0=None, x1=None):
    a = ax.x_range[0] if x0 is None else x0
    b = ax.x_range[1] if x1 is None else x1
    xs = np.linspace(a, b, n)
    return polilinha(ax, xs, func(xs), cor, largura)


def raia(ax, f, altura, cor, largura=6, base=0.0):
    """Seta vertical no espectro (para cima se altura > 0)."""
    return Arrow(ax.c2p(f, base), ax.c2p(f, altura), buff=0, color=cor, stroke_width=largura,
                 max_tip_length_to_length_ratio=0.22, max_stroke_width_to_length_ratio=14)


def banda(ax, f, meia, altura, cor, opacidade=0.5):
    """Bloco trapezoidal em uma frequência. `meia` e `altura` em unidades de tela.

    Os espectros destas cenas são esquemáticos (como nas figuras do livro): o
    que importa é onde cada banda cai, não a sua largura real.
    """
    c = ax.c2p(f, 0)
    pts = [c + LEFT * meia, c + LEFT * meia * 0.5 + UP * altura,
           c + RIGHT * meia * 0.5 + UP * altura, c + RIGHT * meia]
    return Polygon(*pts, color=cor, stroke_width=2).set_fill(cor, opacity=opacidade)


def marcar_x(ax, valores, rotulos, tamanho=16, buff=0.12):
    return VGroup(*[Text(r, font_size=tamanho, color=GREY_B).next_to(ax.c2p(v, 0), DOWN, buff=buff)
                    for v, r in zip(valores, rotulos)])


def plano_iq(centro, lado, alcance=1.45, tamanho=20):
    """Plano I-Q quadrado, com os eixos rotulados."""
    ax = Axes(x_range=[-alcance, alcance, 0.5], y_range=[-alcance, alcance, 0.5],
              x_length=lado, y_length=lado, axis_config=EIXO_CFG)
    ax.move_to(centro)
    rot = VGroup(tex("I", COR_I, tamanho).next_to(ax.c2p(alcance, 0), RIGHT, buff=0.08),
                 tex("Q", COR_Q, tamanho).next_to(ax.c2p(0, alcance), UP, buff=0.08))
    return ax, rot


def fasor(ax, i, q, cor=COR_RF, largura=5):
    return Arrow(ax.c2p(0, 0), ax.c2p(i, q), buff=0, color=cor, stroke_width=largura,
                 max_tip_length_to_length_ratio=0.18)


# =============================================================================
# Cena
# =============================================================================
class UpConversion(Scene):
    def construct(self):
        self.camera.background_color = FUNDO
        self.abertura()
        self.cena_problema()
        self.cena_iq()
        self.cena_vetorial()
        self.cena_am_pm()
        self.cena_erros()
        self.cena_predistorcao()
        self.cena_heterodino()
        self.cena_ssb()
        self.cena_comparacao()
        self.cena_resumo()

    # ------------------------------------------------------------- utilidades
    def titulo_cena(self, texto):
        t = Text(texto, font_size=32, weight=BOLD).to_corner(UL, buff=0.35)
        ln = Line(t.get_corner(DL), t.get_corner(DR), color=COR_EIXO,
                  stroke_width=2).shift(DOWN * 0.12)
        self.play(Write(t), Create(ln), run_time=1.0)
        self.wait(0.4)
        return VGroup(t, ln)

    def trocar_titulo(self, titulo, texto):
        novo = Text(texto, font_size=32, weight=BOLD).to_corner(UL, buff=0.35)
        ln = Line(novo.get_corner(DL), novo.get_corner(DR), color=COR_EIXO,
                  stroke_width=2).shift(DOWN * 0.12)
        self.play(Transform(titulo[0], novo), Transform(titulo[1], ln), run_time=0.8)

    def legenda(self, texto, anterior=None, cor=GREY_A, pausa=None):
        """Narração no rodapé. Espera o tempo de leitura antes de prosseguir."""
        nova = ajustar(Text(texto, font_size=24, color=cor), 13.2).to_edge(DOWN, buff=0.35)
        if anterior is None:
            self.play(FadeIn(nova, shift=UP * 0.2), run_time=0.8)
        else:
            self.play(FadeOut(anterior, shift=UP * 0.2), FadeIn(nova, shift=UP * 0.2), run_time=0.8)
        self.wait(pausa if pausa is not None else 0.5 + 0.022 * len(texto))
        return nova

    def limpar(self):
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.9)
        self.wait(0.25)

    # ---------------------------------------------------------------- abertura
    def abertura(self):
        titulo = Text("Up-conversion", font_size=64, weight=BOLD)
        sub = Text("do I e Q digitais até a portadora que excita a cavidade",
                   font_size=28, color=GREY_A)
        cadeia = VGroup(tex(r"I, Q", COR_DIG, 32), tex(r"\rightarrow", GREY_A, 30),
                        caixa("DAC", 1.1, 0.6, WHITE, 20), tex(r"\rightarrow", GREY_A, 30),
                        multiplicador(COR_LO, 0.28), tex(r"\rightarrow", GREY_A, 30),
                        tex(r"RF", COR_RF, 32)).arrange(RIGHT, buff=0.28)
        nota = Text("dois caminhos clássicos: homodino (direto) e heteródino (por uma IF)",
                    font_size=22, color=GREY_B)
        g = VGroup(titulo, sub, cadeia, nota).arrange(DOWN, buff=0.5)
        self.play(Write(titulo), run_time=1.5)
        self.play(FadeIn(sub, shift=UP * 0.2), FadeIn(cadeia, shift=UP * 0.2))
        self.play(FadeIn(nota, shift=UP * 0.2))
        self.wait(1.8)
        self.play(FadeOut(g))

    # ================================================================== CENA 1
    def cena_problema(self):
        self.titulo_cena("1 · O problema: dois mundos nas pontas")
        fpga = caixa("FPGA\nI e Q em banda base", 3.6, 1.1, COR_DIG, 19).move_to(P(-4.3, 1.8))
        cav = caixa("cavidade\n500 MHz, amplitude e fase exatas", 4.4, 1.1, COR_RF, 17).move_to(P(3.6, 1.8))
        seta = fio([P(-2.4, 1.8), P(1.3, 1.8)], GREY_A)
        duvida = tex("?", COR_ERRO, 44).move_to(P(-0.55, 2.25))

        dds = caixa("um único DAC gerando 500 MHz (DDS)", 5.8, 0.8, GREY_B, 19).move_to(P(-3.6, 0.1))
        risco = VGroup(Line(dds.get_corner(DL), dds.get_corner(UR), color=COR_ERRO, stroke_width=5),
                       Line(dds.get_corner(UL), dds.get_corner(DR), color=COR_ERRO, stroke_width=5))
        porque = txt("os DACs de hoje não alcançam, juntas,\n"
                     "a precisão e a velocidade exigidas\n"
                     "em centenas de MHz", 19, line_spacing=0.85).move_to(P(3.3, 0.1))

        rota1 = caixa("Homodino (direto)\no LO já está em f_RF", 5.4, 1.2, COR_RF, 19).move_to(P(-3.6, -1.7))
        rota2 = caixa("Heteródino (por uma IF)\nsobe em dois passos: IF e depois RF", 6.2, 1.2, COR_IF, 17
                      ).move_to(P(3.3, -1.7))

        leg = self.legenda("De um lado números; do outro, uma onda de verdade em 500 MHz")
        self.play(FadeIn(fpga, shift=RIGHT * 0.2), FadeIn(cav, shift=LEFT * 0.2), run_time=1.2)
        self.play(Create(seta), FadeIn(duvida, scale=0.6))
        leg = self.legenda("O caminho ideal seria um DAC sintetizando o RF direto (DDS)", leg)
        self.play(FadeIn(dds))
        leg = self.legenda("Mas isso ainda não existe com a qualidade que o LLRF precisa", leg, COR_ERRO)
        self.play(Create(risco), run_time=0.8)
        self.play(FadeIn(porque, shift=RIGHT * 0.2))
        leg = self.legenda("Na prática: DACs em banda base ou em IF, mais mixers para subir a frequência", leg)
        self.play(FadeIn(rota1, shift=UP * 0.2), FadeIn(rota2, shift=UP * 0.2), run_time=1.2)
        leg = self.legenda("São os dois esquemas que vamos construir e comparar", leg)
        self.wait(0.8)
        self.limpar()

    # ================================================================== CENA 2
    def cena_iq(self):
        self.titulo_cena("2 · Dois números constroem qualquer portadora")
        eq1 = tex_partes([(r"RF_{out}(t) = ", WHITE), (r"I", COR_I), (r"\cdot A_{LO}\sin\omega t", WHITE),
                          (r" + ", WHITE), (r"Q", COR_Q), (r"\cdot A_{LO}\cos\omega t", WHITE)], 34
                         ).move_to(P(0, 2.5))
        eq2 = tex_partes([(r"= A_{out}\,", COR_RF), (r"\sin(\omega t + \varphi_0)", COR_RF)], 34
                         ).move_to(P(0, 1.98))

        ax_iq, rot_iq = plano_iq(P(-4.4, -0.25), 3.4)
        circ = Circle(radius=(ax_iq.c2p(1, 0) - ax_iq.c2p(0, 0))[0], color=GREY_D,
                      stroke_width=2).move_to(ax_iq.c2p(0, 0))
        ax_t = eixos(P(2.6, 0.1), 8.0, 2.8, [0, 3, 1], [-1.7, 1.7, 1])
        r_t = txt("as duas portadoras e a soma", 18).next_to(ax_t, UP, buff=0.08).align_to(ax_t, RIGHT)

        vi, vq = ValueTracker(1.0), ValueTracker(0.0)

        def c_i():
            return curva(ax_t, lambda t: vi.get_value() * np.sin(TAU * t), COR_I, 3)

        def c_q():
            return curva(ax_t, lambda t: vq.get_value() * np.cos(TAU * t), COR_Q, 3)

        def c_s():
            return curva(ax_t, lambda t: (vi.get_value() * np.sin(TAU * t)
                                          + vq.get_value() * np.cos(TAU * t)), COR_RF, 5)

        def v_fasor():
            return fasor(ax_iq, vi.get_value(), vq.get_value())

        def arco():
            a = np.arctan2(vq.get_value(), vi.get_value())
            if abs(a) < 0.04:
                return VGroup()
            return Arc(radius=0.45, start_angle=0, angle=a, color=COR_RF,
                       stroke_width=3).move_arc_center_to(ax_iq.c2p(0, 0))

        leitura = VGroup(txt("A =", 20), DecimalNumber(1.0, num_decimal_places=2, font_size=30, color=COR_RF),
                         txt("     φ₀ [°] =", 20),
                         DecimalNumber(0.0, num_decimal_places=0, font_size=30, color=COR_RF)
                         ).arrange(RIGHT, buff=0.14).move_to(P(2.6, -1.95))
        leitura[1].add_updater(lambda m: m.set_value(np.hypot(vi.get_value(), vq.get_value())))
        leitura[3].add_updater(lambda m: m.set_value(np.degrees(np.arctan2(vq.get_value(), vi.get_value()))))

        leg = self.legenda("Uma portadora tem amplitude e fase; I e Q são as duas coordenadas dela")
        self.play(Write(eq1), run_time=1.5)
        self.play(FadeIn(ax_iq), FadeIn(rot_iq), FadeIn(circ), Create(ax_t), FadeIn(r_t), run_time=1.3)
        self.add(always_redraw(c_i), always_redraw(c_q), always_redraw(c_s),
                 always_redraw(v_fasor), always_redraw(arco), leitura)
        leg = self.legenda("Só com I: um seno puro, fase zero", leg, COR_I)
        self.wait(0.8)
        self.play(vi.animate.set_value(0.0), vq.animate.set_value(1.0), run_time=2.0)
        leg = self.legenda("Só com Q: a mesma portadora, mas 90° adiantada", leg, COR_Q)
        self.wait(0.8)
        self.play(vi.animate.set_value(0.8), vq.animate.set_value(0.6), run_time=2.0)
        self.play(Write(eq2), run_time=1.2)
        leg = self.legenda("Com os dois juntos, a soma continua sendo UMA senoide — nem mais nem menos", leg,
                           COR_RF)
        self.wait(0.8)
        self.play(vi.animate.set_value(-0.5), vq.animate.set_value(0.95), run_time=2.2)
        self.wait(0.6)
        self.play(vi.animate.set_value(1.25), vq.animate.set_value(-0.45), run_time=2.2)
        leg = self.legenda("O comprimento do fasor vira a amplitude; o ângulo vira a fase", leg, COR_RF)
        self.wait(0.6)
        formulas = tex_partes([(r"A_{out} = A_{RF}\sqrt{I^2 + Q^2}", COR_RF), (r"\qquad", WHITE),
                               (r"\varphi_0 = \arctan(Q/I)", COR_RF)], 30)
        self.play(FadeIn(ajustar(formulas, 5.3).move_to(P(-4.2, -2.3)), shift=UP * 0.15))
        leg = self.legenda("Mexer em I e Q é mexer na amplitude e na fase do RF: é disso que o LLRF precisa", leg)
        self.wait(0.8)
        self.limpar()

    # ================================================================== CENA 3
    def cena_vetorial(self):
        """Fig. 21 do Schilcher: o modulador vetorial, montado peça por peça."""
        self.titulo_cena("3 · Modulador vetorial: a up-conversion homodina")
        # --- oscilador local e híbrido de 90°
        rot_lo = tex(r"LO", COR_LO, 30).move_to(P(-6.55, 1.45))
        hib = VGroup(RoundedRectangle(corner_radius=0.08, width=1.15, height=1.5,
                                      color=COR_LO, stroke_width=3).move_to(P(-5.1, 1.45)),
                     txt("0°", 18, COR_LO).move_to(P(-5.1, 1.9)),
                     txt("90°", 18, COR_LO).move_to(P(-5.1, 1.0)))
        f_lo = fio([P(-6.2, 1.45), P(-5.72, 1.45)], COR_LO)
        mix_i = multiplicador(COR_I).move_to(P(-3.4, 1.9))
        mix_q = multiplicador(COR_Q).move_to(P(-1.8, 1.0))
        f_sin = fio([P(-4.52, 1.9), P(-3.75, 1.9)], COR_LO)
        f_cos = fio([P(-4.52, 1.0), P(-2.15, 1.0)], COR_LO)
        r_sin = txt("sin", 17, COR_LO).move_to(P(-4.15, 2.14))
        r_cos = txt("cos", 17, COR_LO).move_to(P(-4.15, 1.24))

        # --- conversores e os dois canais
        dac_i = caixa("DAC", 1.0, 0.6, COR_I, 17).move_to(P(-3.4, -0.75))
        dac_q = caixa("DAC", 1.0, 0.6, COR_Q, 17).move_to(P(-1.8, -0.75))
        f_i = fio([P(-3.4, -0.45), P(-3.4, 1.55)], COR_I)
        f_q = fio([P(-1.8, -0.45), P(-1.8, 0.65)], COR_Q)
        rot_i = tex("I", COR_I, 32).move_to(P(-3.4, -1.45))
        rot_q = tex("Q", COR_Q, 32).move_to(P(-1.8, -1.45))

        # --- somador e saída
        soma = VGroup(RoundedRectangle(corner_radius=0.08, width=0.7, height=1.3,
                                       color=WHITE, stroke_width=3).move_to(P(0.5, 1.45)),
                      tex(r"\Sigma", WHITE, 30).move_to(P(0.5, 1.45)))
        f_s1 = fio([P(-3.1, 1.9), P(0.12, 1.9)], COR_I)
        f_s2 = fio([P(-1.5, 1.0), P(0.12, 1.0)], COR_Q)
        f_out = fio([P(0.85, 1.45), P(1.45, 1.45)], COR_RF)
        rot_out = tex(r"RF_{out}", COR_RF, 30).move_to(P(2.1, 1.45))

        cx_ana = DashedVMobject(RoundedRectangle(corner_radius=0.12, width=7.0, height=1.8),
                                num_dashes=60).set_stroke(GREY_B, 2).move_to(P(-2.45, 1.45))
        r_ana = txt("analógico", 18, GREY_A).move_to(P(-5.3, 2.52))
        cx_dig = DashedVMobject(RoundedRectangle(corner_radius=0.12, width=3.4, height=1.55),
                                num_dashes=46).set_stroke(COR_DIG, 2).move_to(P(-2.6, -1.07))
        r_dig = txt("digital", 18, COR_DIG).move_to(P(-5.3, -1.07))

        # --- espectro esquemático
        ax_e = eixos(P(4.8, 0.6), 4.2, 1.6, [0, 600, 600], [0, 1.2, 1])
        bb = banda(ax_e, 30, 0.35, 0.75, COR_DIG)
        rf = banda(ax_e, 500, 0.35, 0.75, COR_RF)
        lo_r = raia(ax_e, 500, 1.05, COR_LO, 5)
        r_bb = txt("banda base", 14, GREY_B).next_to(ax_e.c2p(30, 0), DOWN, buff=0.14)
        r_rf = txt("f_LO = f_RF", 14, GREY_B).next_to(ax_e.c2p(500, 0), DOWN, buff=0.14)
        sobe = Arrow(ax_e.c2p(30, 0) + UP * 0.95 + RIGHT * 0.45, ax_e.c2p(500, 0) + UP * 0.95 + LEFT * 0.45,
                     buff=0, color=GREY_A, stroke_width=3, max_tip_length_to_length_ratio=0.1)
        r_esp = txt("espectro", 17, GREY_A).move_to(P(3.35, 1.62))
        nota_e = txt("a banda base inteira sobe\npara a frequência do LO", 18, line_spacing=0.85
                     ).move_to(P(4.8, -1.3))

        leg = self.legenda("O bloco que faz tudo isso em um passo só se chama modulador vetorial")
        self.play(FadeIn(rot_lo), Create(f_lo), FadeIn(hib), run_time=1.2)
        leg = self.legenda("O LO entra e é dividido por um híbrido de 90°: um ramo seno, outro cosseno",
                           leg, COR_LO)
        self.play(Create(f_sin), Create(f_cos), FadeIn(r_sin), FadeIn(r_cos), run_time=1.2)
        self.play(FadeIn(mix_i), FadeIn(mix_q))
        leg = self.legenda("Cada ramo encontra um mixer; é por baixo que chegam os canais I e Q", leg)
        self.play(FadeIn(dac_i), FadeIn(dac_q), FadeIn(rot_i), FadeIn(rot_q),
                  Create(f_i), Create(f_q), run_time=1.4)
        self.play(Create(cx_dig), FadeIn(r_dig))
        leg = self.legenda("Aqui os mixers trabalham como controles de amplitude: I e Q dosam cada ramo", leg)
        self.wait(0.6)
        self.play(Create(f_s1), Create(f_s2), FadeIn(soma), run_time=1.2)
        self.play(Create(f_out), FadeIn(rot_out))
        self.play(Create(cx_ana), FadeIn(r_ana))
        leg = self.legenda("A soma dos dois ramos é a portadora da cena anterior, agora em hardware", leg,
                           COR_RF)
        self.wait(0.6)
        leg = self.legenda("No espectro: o LO está na própria frequência de RF — não existe IF", leg)
        self.play(Create(ax_e), FadeIn(r_esp), FadeIn(bb), FadeIn(r_bb), run_time=1.2)
        self.play(FadeIn(lo_r), FadeIn(r_rf), GrowArrow(sobe), FadeIn(rf), run_time=1.4)
        self.play(FadeIn(nota_e, shift=UP * 0.15))
        leg = self.legenda("Uma banda só, nenhuma imagem para filtrar: é a grande vantagem do homodino", leg,
                           COR_RF)
        self.wait(0.8)
        self.limpar()

    # ================================================================== CENA 4
    def cena_am_pm(self):
        """Os mesmos dois botões fazem modulação de amplitude e de fase."""
        titulo = self.titulo_cena("4 · Modulando amplitude com I e Q")
        ax_iq, rot_iq = plano_iq(P(-4.4, 0.35), 3.3)
        circ = Circle(radius=(ax_iq.c2p(1, 0) - ax_iq.c2p(0, 0))[0], color=GREY_D,
                      stroke_width=2).move_to(ax_iq.c2p(0, 0))
        ax_t = eixos(P(2.4, 0.9), 8.4, 2.2, [0, 8, 2], [-1.6, 1.6, 1])
        r_t = rotulo_eixo(ax_t, txt("a portadora que sai do modulador", 18))
        tau = ValueTracker(0.0)
        fase0 = np.radians(35)

        def a0(t):
            return 1.0 + 0.45 * np.sin(TAU * t / 8.0)

        onda_am = curva(ax_t, lambda t: a0(t) * np.sin(TAU * 1.5 * t + fase0), COR_RF, 3, n=900)
        env = VGroup(*[DashedVMobject(curva(ax_t, lambda t, s=s: s * a0(t), COR_I, 2, n=300), num_dashes=60)
                       for s in (1, -1)])

        def ponto_am():
            t = tau.get_value()
            return Dot(ax_t.c2p(t, a0(t) * np.sin(TAU * 1.5 * t + fase0)), radius=0.07, color=COR_RF)

        def fasor_am():
            t = tau.get_value()
            return VGroup(fasor(ax_iq, a0(t) * np.cos(fase0), a0(t) * np.sin(fase0)),
                          Dot(ax_iq.c2p(a0(t) * np.cos(fase0), a0(t) * np.sin(fase0)),
                              radius=0.05, color=COR_RF))

        eq_am = tex_partes([(r"I(t) = A_0(t)\cos\varphi_0", COR_I), (r"\qquad", WHITE),
                            (r"Q(t) = A_0(t)\sin\varphi_0", COR_Q)], 28).move_to(P(2.4, -1.0))
        cap_am = txt("o fasor estica e encolhe,\nmas não gira", 18, line_spacing=0.85).move_to(P(-4.4, -1.85))

        leg = self.legenda("Para modular só a amplitude, I e Q sobem e descem juntos")
        self.play(FadeIn(ax_iq), FadeIn(rot_iq), FadeIn(circ), Create(ax_t), FadeIn(r_t), run_time=1.3)
        self.play(Create(onda_am), run_time=2.0)
        self.play(FadeIn(env), FadeIn(eq_am), run_time=1.0)
        viva_am = VGroup(always_redraw(ponto_am), always_redraw(fasor_am))
        self.add(viva_am)
        self.play(FadeIn(cap_am))
        self.play(tau.animate.set_value(8.0), run_time=7.0, rate_func=linear)
        leg = self.legenda("A envelope do RF é exatamente o A₀(t) que a FPGA escreveu em I e Q", leg, COR_I)
        self.wait(0.6)

        # --- modulação de fase -----------------------------------------------
        self.trocar_titulo(titulo, "4 · E modulando a fase, com os mesmos botões")
        tau.set_value(0.0)
        onda_pm = curva(ax_t, lambda t: np.sin(TAU * 1.5 * t + TAU * t / 8.0), COR_RF, 3, n=900)
        eq_pm = tex_partes([(r"I(t) = A_0\cos\varphi_0(t)", COR_I), (r"\qquad", WHITE),
                            (r"Q(t) = A_0\sin\varphi_0(t)", COR_Q)], 28).move_to(P(2.4, -1.0))
        cap_pm = txt("agora o fasor gira,\ncom o mesmo comprimento", 18, line_spacing=0.85
                     ).move_to(P(-4.4, -1.85))

        def ponto_pm():
            t = tau.get_value()
            return Dot(ax_t.c2p(t, np.sin(TAU * 1.5 * t + TAU * t / 8.0)), radius=0.07, color=COR_RF)

        def fasor_pm():
            a = TAU * tau.get_value() / 8.0
            return VGroup(fasor(ax_iq, np.cos(a), np.sin(a)),
                          Dot(ax_iq.c2p(np.cos(a), np.sin(a)), radius=0.05, color=COR_RF))

        leg = self.legenda("Agora a amplitude fica fixa e o ângulo é que caminha", leg)
        viva_am.clear_updaters()
        for m in viva_am:
            m.clear_updaters()
        self.play(FadeOut(env), FadeOut(onda_am), FadeOut(eq_am), FadeOut(cap_am),
                  FadeOut(viva_am), run_time=0.7)
        self.remove(viva_am)
        self.play(Create(onda_pm), FadeIn(eq_pm), run_time=2.0)
        self.add(VGroup(always_redraw(ponto_pm), always_redraw(fasor_pm)))
        self.play(FadeIn(cap_pm))
        self.play(tau.animate.set_value(8.0), run_time=7.0, rate_func=linear)
        leg = self.legenda("Amplitude e fase, as duas grandezas que o LLRF controla, saem do mesmo par I/Q",
                           leg, COR_RF)
        self.wait(0.8)
        self.limpar()

    # ================================================================== CENA 5
    def cena_erros(self):
        """O que o caminho analógico do modulador vetorial estraga."""
        self.titulo_cena("5 · O preço de fazer tudo no analógico")
        centros = [P(-5.4, 1.45), P(1.2, 1.45), P(-5.4, -1.25), P(1.2, -1.25)]
        planos, circos = [], []
        for c in centros:
            ax, rot = plano_iq(c, 2.0, 1.55, 16)
            r = (ax.c2p(1, 0) - ax.c2p(0, 0))[0]
            circos.append(DashedVMobject(Circle(radius=r, color=GREY_D, stroke_width=2)
                                         .move_to(ax.c2p(0, 0)), num_dashes=40))
            planos.append((ax, rot))

        t = np.linspace(0, TAU, 240)
        ax0, ax1, ax2, ax3 = [p[0] for p in planos]
        # (a) offset de DC: o círculo sai do centro e sobra portadora na origem
        d_off = VGroup(polilinha(ax0, 0.32 + np.cos(t), 0.24 + np.sin(t), COR_ERRO, 3),
                       fasor(ax0, 0.32, 0.24, COR_ERRO, 4))
        # (b) desbalanço de ganho: o círculo vira elipse
        d_gan = polilinha(ax1, np.cos(t), 0.55 * np.sin(t), COR_ERRO, 3)
        # (c) skew de quadratura: os eixos deixam de ser perpendiculares
        d_skew = VGroup(polilinha(ax2, np.cos(t) + 0.42 * np.sin(t), np.sin(t), COR_ERRO, 3),
                        DashedVMobject(Line(ax2.c2p(-0.42 * 1.3, -1.3), ax2.c2p(0.42 * 1.3, 1.3),
                                            color=COR_ERRO, stroke_width=3), num_dashes=14))
        # (d) ruído de fase: a fase treme e o ponto vira uma nuvem
        tremor = 0.11 * np.sin(7 * t) + 0.07 * np.sin(13 * t + 1.0)
        d_fase = polilinha(ax3, np.cos(t + tremor), np.sin(t + tremor), COR_ERRO, 3)

        def bloco(titulo, corpo, x, y, larg):
            g = VGroup(txt(titulo, 19, COR_ERRO), txt(corpo, 16, GREY_A, line_spacing=0.8)
                       ).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
            return ajustar(g, larg).move_to(P(x, y), aligned_edge=LEFT)

        t_off = bloco("Offset de DC", "um resíduo contínuo em I ou Q\n"
                                      "faz o LO vazar para a saída:\n"
                                      "sai portadora mesmo com I = Q = 0", -4.1, 1.45, 3.7)
        t_gan = bloco("Desbalanço de ganho", "um ramo amplifica mais que o outro:\n"
                                             "o círculo vira elipse e a fase\n"
                                             "passa a mexer na amplitude", 2.5, 1.45, 4.3)
        t_skew = bloco("Skew de quadratura", "o híbrido não dá 90° exatos:\n"
                                             "os eixos deixam de ser\n"
                                             "perpendiculares e I vaza em Q", -4.1, -1.25, 3.7)
        t_fase = bloco("Ruído de fase do LO", "a fase da portadora treme\n"
                                              "sozinha: o ponto deixa de\n"
                                              "ficar parado no plano I-Q", 2.5, -1.25, 4.3)

        leg = self.legenda("No homodino, tudo acontece em componentes analógicos — e eles erram")
        self.play(*[FadeIn(p[0]) for p in planos], *[FadeIn(p[1]) for p in planos],
                  *[Create(c) for c in circos], run_time=1.6)
        leg = self.legenda("Com tudo perfeito, I e Q desenham este círculo cinza", leg)
        self.wait(0.4)
        for desenho, texto, narracao in [
                (d_off, t_off, "Offset de DC: um pedacinho de LO escapa direto para a saída"),
                (d_gan, t_gan, "Desbalanço de ganho: o que era círculo vira elipse"),
                (d_skew, t_skew, "Skew: os eixos I e Q deixam de ser perpendiculares"),
                (d_fase, t_fase, "Ruído de fase do LO: a portadora treme sem ninguém pedir")]:
            leg = self.legenda(narracao, leg, COR_ERRO)
            self.play(Create(desenho), FadeIn(texto, shift=RIGHT * 0.15), run_time=1.3)
            self.wait(0.5)
        leg = self.legenda("Todos esses erros entram DEPOIS do DAC — e por isso incomodam tanto", leg)
        self.wait(0.8)
        self.limpar()

    # ================================================================== CENA 6
    def cena_predistorcao(self):
        """O digital corrige o defeito do analógico (pré-distorção do skew)."""
        self.titulo_cena("6 · Pré-distorção: o digital conserta o analógico")
        ax, rot = plano_iq(P(-4.3, 0.35), 3.4)
        fs = np.radians(28)
        eixo_ideal = DashedVMobject(Line(ax.c2p(0, 0), ax.c2p(0, 1.25), color=COR_Q, stroke_width=4),
                                    num_dashes=12)
        eixo_real = Line(ax.c2p(0, 0), ax.c2p(1.25 * np.sin(fs), 1.25 * np.cos(fs)),
                         color=COR_ERRO, stroke_width=4)
        arco = Arc(radius=0.75, start_angle=PI / 2 - fs, angle=fs, color=COR_ERRO,
                   stroke_width=3).move_arc_center_to(ax.c2p(0, 0))
        r_fs = tex(r"\varphi_S", COR_ERRO, 26).move_to(ax.c2p(0, 0) + 0.95 * np.array(
            [np.cos(PI / 2 - fs / 2), np.sin(PI / 2 - fs / 2), 0.0]))
        r_ideal = txt("Q ideal", 16, COR_Q).next_to(ax.c2p(0, 0.95), LEFT, buff=0.12)
        r_real = txt("Q real", 16, COR_ERRO).next_to(ax.c2p(1.25 * np.sin(fs), 1.25 * np.cos(fs)),
                                                     RIGHT, buff=0.12)

        matriz = tex(r"\begin{pmatrix} I_{out} \\ Q_{out} \end{pmatrix} = "
                     r"\frac{1}{\cos\varphi_S} \begin{pmatrix} \cos\varphi_S & -\sin\varphi_S \\ "
                     r"0 & 1 \end{pmatrix} \cdot \begin{pmatrix} I_{in} \\ Q_{in} \end{pmatrix}",
                     WHITE, 34)
        ajustar(matriz, 8.0).move_to(P(2.5, 1.5))
        l1 = tex(r"I_{out} = I_{in} - \tan\varphi_S \cdot Q_{in}", COR_I, 30).move_to(P(2.5, 0.2))
        l2 = tex(r"Q_{out} = Q_{in} \,/\, \cos\varphi_S", COR_Q, 30).move_to(P(2.5, -0.45))
        nota = txt("a conta é feita no FPGA, antes dos DACs:\n"
                   "a entrada já sai torta do jeito certo para\n"
                   "o analógico entortar de volta ao lugar",
                   19, line_spacing=0.85).move_to(P(2.5, -1.75))

        leg = self.legenda("O skew é o erro mais fácil de corrigir: ele é geométrico e previsível")
        self.play(FadeIn(ax), FadeIn(rot), run_time=0.9)
        self.play(Create(eixo_ideal), FadeIn(r_ideal))
        leg = self.legenda("Se o híbrido erra o ângulo, o eixo Q real encosta no eixo I", leg, COR_ERRO)
        self.play(Create(eixo_real), Create(arco), FadeIn(r_fs), FadeIn(r_real), run_time=1.2)
        leg = self.legenda("Conhecendo o desvio, basta pré-distorcer I e Q antes de enviá-los", leg)
        self.play(Write(matriz), run_time=2.0)
        self.play(FadeIn(l1, shift=UP * 0.12), FadeIn(l2, shift=UP * 0.12), run_time=1.0)
        self.play(FadeIn(nota, shift=UP * 0.15))
        leg = self.legenda("É o primeiro exemplo de uma ideia que volta sempre no LLRF: calibrar no digital",
                           leg)
        self.wait(0.8)
        self.limpar()

    # ================================================================== CENA 7
    def cena_heterodino(self):
        """Fig. 22 do Schilcher: subir primeiro para uma IF, ainda no digital."""
        titulo = self.titulo_cena("7 · Heteródino: primeiro uma IF digital")
        rot_i = tex("I", COR_I, 30).move_to(P(-6.8, 2.25))
        rot_q = tex("Q", COR_Q, 30).move_to(P(-6.8, 0.55))
        mix_i = multiplicador(COR_I).move_to(P(-4.0, 2.25))
        mix_q = multiplicador(COR_Q).move_to(P(-4.0, 0.55))
        nco = oscilador(COR_DIG).move_to(P(-6.1, 1.4))
        r_nco = txt("NCO  f_IF", 15, COR_DIG).move_to(P(-6.05, 0.95))
        hib = VGroup(RoundedRectangle(corner_radius=0.08, width=0.95, height=1.0,
                                      color=COR_DIG, stroke_width=3).move_to(P(-4.9, 1.4)),
                     txt("0°", 14, COR_DIG).move_to(P(-4.9, 1.63)),
                     txt("90°", 14, COR_DIG).move_to(P(-4.9, 1.17)))
        fios_dig = VGroup(fio([P(-6.55, 2.25), P(-4.35, 2.25)], COR_I),
                          fio([P(-6.55, 0.55), P(-4.35, 0.55)], COR_Q),
                          fio([P(-5.8, 1.4), P(-5.42, 1.4)], COR_DIG),
                          fio([P(-4.42, 1.75), P(-4.0, 1.75), P(-4.0, 1.93)], COR_DIG),
                          fio([P(-4.42, 1.05), P(-4.0, 1.05), P(-4.0, 0.87)], COR_DIG))
        soma = VGroup(RoundedRectangle(corner_radius=0.08, width=0.7, height=1.9,
                                       color=COR_DIG, stroke_width=3).move_to(P(-2.6, 1.4)),
                      tex(r"\Sigma", COR_DIG, 30).move_to(P(-2.6, 1.4)))
        f_soma = VGroup(fio([P(-3.7, 2.25), P(-2.98, 2.25)], COR_I),
                        fio([P(-3.7, 0.55), P(-2.98, 0.55)], COR_Q))
        dac = caixa("DAC", 1.0, 0.65, COR_IF, 18).move_to(P(-1.2, 1.4))
        mix_rf = multiplicador(COR_RF).move_to(P(0.5, 1.4))
        lo = oscilador(COR_LO).move_to(P(0.5, 0.45))
        r_lo = txt("LO  480 MHz", 15, COR_LO).move_to(P(1.55, 0.45))
        rot_out = tex(r"RF_{out}", COR_RF, 28).move_to(P(2.2, 1.4))
        fios_ana = VGroup(fio([P(-2.25, 1.4), P(-1.75, 1.4)], COR_DIG),
                          fio([P(-0.7, 1.4), P(0.16, 1.4)], COR_IF),
                          fio([P(0.5, 0.75), P(0.5, 1.06)], COR_LO),
                          fio([P(0.84, 1.4), P(1.5, 1.4)], COR_RF))
        cx_dig = DashedVMobject(RoundedRectangle(corner_radius=0.12, width=6.6, height=2.35),
                                num_dashes=72).set_stroke(COR_DIG, 2).move_to(P(-3.75, 1.38))
        r_dig = txt("digital", 17, COR_DIG).move_to(P(-6.4, 2.62))
        cx_ana = DashedVMobject(RoundedRectangle(corner_radius=0.12, width=3.2, height=2.35),
                                num_dashes=46).set_stroke(GREY_B, 2).move_to(P(1.3, 1.38))
        r_ana = txt("analógico", 17, GREY_A).move_to(P(1.3, 2.62))
        diagrama = VGroup(rot_i, rot_q, mix_i, mix_q, nco, r_nco, hib, fios_dig, soma, f_soma,
                          dac, mix_rf, lo, r_lo, rot_out, fios_ana, cx_dig, r_dig, cx_ana, r_ana)

        # --- os dois espectros
        ax1 = eixos(P(-3.6, -1.45), 5.6, 1.2, [0, 60, 20], [0, 1.2, 1])
        r_ax1 = rotulo_eixo(ax1, txt("o que o DAC entrega: a IF", 17))
        b_if = banda(ax1, 20, 0.3, 0.75, COR_IF)
        m_ax1 = marcar_x(ax1, [0, 20, 40, 60], ["0", "20", "40", "60"], 13)
        u_ax1 = txt("MHz", 13, GREY_B).next_to(ax1.c2p(60, 0), DOWN, buff=0.12).shift(RIGHT * 0.45)

        ax2 = eixos(P(3.6, -1.45), 5.6, 1.2, [400, 560, 40], [0, 1.2, 1])
        r_ax2 = rotulo_eixo(ax2, txt("depois do mixer: duas bandas", 17))
        b_img = banda(ax2, F_IMG, 0.3, 0.75, COR_ERRO)
        b_rf = banda(ax2, F_RF, 0.3, 0.75, COR_RF)
        r_lo2 = raia(ax2, F_LO, 1.05, COR_LO, 5)
        m_ax2 = marcar_x(ax2, [400, 440, 480, 520, 560], ["400", "440", "480", "520", "560"], 13)
        t_img = txt("imagem", 14, COR_ERRO).next_to(ax2.c2p(F_IMG, 0.75), UP, buff=0.06)
        t_rf = txt("RF", 14, COR_RF).next_to(ax2.c2p(F_RF, 0.75), UP, buff=0.06)
        t_lo2 = txt("LO", 14, COR_LO).next_to(ax2.c2p(F_LO, 1.05), UP, buff=0.04)

        leg = self.legenda("A outra rota: subir I e Q para uma IF ainda dentro da FPGA")
        self.play(FadeIn(rot_i), FadeIn(rot_q), FadeIn(nco), FadeIn(r_nco), FadeIn(hib),
                  FadeIn(mix_i), FadeIn(mix_q), Create(fios_dig), run_time=1.8)
        leg = self.legenda("O NCO faz o papel do LO, e a quadratura de 90° agora é um número, não um componente",
                           leg, COR_DIG)
        self.play(FadeIn(soma), Create(f_soma), run_time=1.1)
        self.play(Create(fios_ana[0]), FadeIn(dac), run_time=1.0)
        self.play(Create(cx_dig), FadeIn(r_dig))
        leg = self.legenda("Um único DAC entrega o sinal já modulado, centrado na IF", leg, COR_IF)
        self.play(Create(ax1), FadeIn(r_ax1), FadeIn(m_ax1), FadeIn(u_ax1), FadeIn(b_if), run_time=1.3)
        leg = self.legenda("Daí para frente é analógico: um mixer e um LO levam a IF até o RF", leg)
        self.play(FadeIn(mix_rf), FadeIn(lo), FadeIn(r_lo), Create(fios_ana[1:]), FadeIn(rot_out),
                  run_time=1.5)
        self.play(Create(cx_ana), FadeIn(r_ana))
        self.play(Create(ax2), FadeIn(r_ax2), FadeIn(m_ax2), FadeIn(r_lo2), FadeIn(t_lo2), run_time=1.2)
        self.play(FadeIn(b_rf), FadeIn(t_rf), run_time=0.8)
        leg = self.legenda("Só que o mixer não entrega uma banda: entrega duas", leg, COR_ERRO)
        self.play(FadeIn(b_img), FadeIn(t_img), run_time=0.9)
        self.wait(0.6)

        # --- por que a imagem aparece, e o que se faz com ela
        self.trocar_titulo(titulo, "7 · A imagem e o método da filtragem")
        self.play(FadeOut(diagrama), run_time=0.8)
        ident = tex(r"s_{IF}(t)\cdot\cos\omega_{LO}t \;=\; "
                    r"\tfrac{1}{2}\sin\big((\omega_{LO}+\omega_{IF})t+\varphi\big)"
                    r"\;-\;\tfrac{1}{2}\sin\big((\omega_{LO}-\omega_{IF})t-\varphi\big)", WHITE, 32)
        ajustar(ident, 12.4).move_to(P(0, 2.2))
        leg = self.legenda("Multiplicar duas senoides sempre dá a soma E a diferença das frequências", leg)
        self.play(Write(ident), run_time=2.2)
        self.wait(0.5)
        filtro = VGroup(linha([ax2.c2p(486, 0), ax2.c2p(488, 1.1), ax2.c2p(514, 1.1), ax2.c2p(516, 0)],
                              COR_FILTRO, 3),
                        txt("filtro passa-faixa", 15, COR_FILTRO).move_to(P(4.2, -2.62)))
        leg = self.legenda("Como a imagem está longe do RF, um filtro passa-faixa resolve: é o método da filtragem",
                           leg, COR_FILTRO)
        self.play(Create(filtro), run_time=1.2)
        self.play(b_img.animate.set_opacity(0.12), t_img.animate.set_opacity(0.3), run_time=1.0)
        self.wait(0.4)
        bom = txt("+ a quadratura é feita no digital:\n"
                  "nada de desbalanço de ganho nem skew", 18, line_spacing=0.85).move_to(P(-3.5, 1.1))
        ruim = txt("− o DAC precisa de muito mais banda:\n"
                   "distorção harmônica e ripple na passagem", 18, line_spacing=0.85).move_to(P(3.3, 1.1))
        leg = self.legenda("A troca é clara: ganha-se precisão na quadratura e perde-se folga no DAC", leg)
        self.play(FadeIn(bom, shift=UP * 0.15), FadeIn(ruim, shift=UP * 0.15), run_time=1.2)
        self.wait(1.0)
        self.limpar()

    # ================================================================== CENA 8
    def cena_ssb(self):
        """Figs. 23 e 24: banda lateral única, com a imagem cancelada."""
        titulo = self.titulo_cena("8 · Banda lateral única: cancelar em vez de filtrar")
        # --- estágio digital
        rot_i = tex("I", COR_I, 28).move_to(P(-6.9, 2.3))
        rot_q = tex("Q", COR_Q, 28).move_to(P(-6.9, 0.7))
        mix_i = multiplicador(COR_I, 0.24).move_to(P(-5.3, 2.3))
        mix_q = multiplicador(COR_Q, 0.24).move_to(P(-5.3, 0.7))
        nco = oscilador(COR_DIG, 0.26).move_to(P(-6.3, 1.5))
        r_nco = txt("f_IF", 14, COR_DIG).move_to(P(-6.3, 1.03))
        dac_i = caixa("DAC", 0.85, 0.5, COR_IF, 15).move_to(P(-4.15, 2.3))
        dac_q = caixa("DAC", 0.85, 0.5, COR_IF, 15).move_to(P(-4.15, 0.7))
        f_dig = VGroup(fio([P(-6.65, 2.3), P(-5.6, 2.3)], COR_I),
                       fio([P(-6.65, 0.7), P(-5.6, 0.7)], COR_Q),
                       fio([P(-5.03, 2.3), P(-4.62, 2.3)], COR_I),
                       fio([P(-5.03, 0.7), P(-4.62, 0.7)], COR_Q),
                       fio([P(-6.04, 1.65), P(-5.3, 1.65), P(-5.3, 2.03)], COR_DIG),
                       fio([P(-6.04, 1.35), P(-5.3, 1.35), P(-5.3, 0.97)], COR_DIG))
        r_sin1 = txt("sin", 13, COR_DIG).move_to(P(-5.72, 1.86))
        r_cos1 = txt("cos", 13, COR_DIG).move_to(P(-5.72, 1.14))

        # --- modulador vetorial analógico
        lo = oscilador(COR_LO, 0.26).move_to(P(-3.0, 1.5))
        r_lo = txt("LO", 14, COR_LO).move_to(P(-3.0, 1.03))
        hib = VGroup(RoundedRectangle(corner_radius=0.07, width=0.75, height=0.85,
                                      color=COR_LO, stroke_width=3).move_to(P(-2.0, 1.5)),
                     txt("0°", 13, COR_LO).move_to(P(-2.0, 1.68)),
                     txt("90°", 13, COR_LO).move_to(P(-2.0, 1.32)))
        mix2_i = multiplicador(COR_RF, 0.24).move_to(P(-0.3, 2.3))
        mix2_q = multiplicador(COR_RF, 0.24).move_to(P(-0.3, 0.7))
        soma = VGroup(RoundedRectangle(corner_radius=0.08, width=0.65, height=1.9,
                                       color=WHITE, stroke_width=3).move_to(P(1.0, 1.5)),
                      tex(r"\Sigma", WHITE, 28).move_to(P(1.0, 1.5)))
        rot_out = tex(r"RF_{out}", COR_RF, 26).move_to(P(2.45, 1.5))
        f_ana = VGroup(fio([P(-3.72, 2.3), P(-0.6, 2.3)], COR_IF),
                       fio([P(-3.72, 0.7), P(-0.6, 0.7)], COR_IF),
                       fio([P(-2.74, 1.5), P(-2.42, 1.5)], COR_LO),
                       fio([P(-1.62, 1.65), P(-0.3, 1.65), P(-0.3, 2.03)], COR_LO),
                       fio([P(-1.62, 1.35), P(-0.3, 1.35), P(-0.3, 0.97)], COR_LO),
                       fio([P(-0.06, 2.3), P(0.63, 2.3)], COR_RF),
                       fio([P(-0.06, 0.7), P(0.63, 0.7)], COR_RF),
                       fio([P(1.33, 1.5), P(1.85, 1.5)], COR_RF))
        cx_dig = DashedVMobject(RoundedRectangle(corner_radius=0.12, width=3.5, height=2.35),
                                num_dashes=50).set_stroke(COR_DIG, 2).move_to(P(-5.3, 1.48))
        r_dig = txt("digital", 15, COR_DIG).move_to(P(-6.55, 0.5))
        cx_ana = DashedVMobject(RoundedRectangle(corner_radius=0.12, width=6.35, height=2.35),
                                num_dashes=76).set_stroke(GREY_B, 2).move_to(P(-0.22, 1.48))
        r_ana = txt("analógico", 15, GREY_A).move_to(P(-2.95, 0.5))
        nota = txt("os dois canais sobem\npara a IF no digital;\n"
                   "só a translação final\né analógica", 17, line_spacing=0.85).move_to(P(5.0, 1.5))
        diagrama = VGroup(rot_i, rot_q, mix_i, mix_q, nco, r_nco, dac_i, dac_q, f_dig, r_sin1, r_cos1,
                          lo, r_lo, hib, mix2_i, mix2_q, soma, rot_out, f_ana,
                          cx_dig, r_dig, cx_ana, r_ana)

        leg = self.legenda("Há um jeito de não precisar filtrar a imagem: fazê-la se cancelar sozinha")
        self.play(FadeIn(VGroup(rot_i, rot_q, mix_i, mix_q, nco, r_nco)), Create(f_dig),
                  FadeIn(r_sin1), FadeIn(r_cos1), run_time=1.8)
        self.play(FadeIn(dac_i), FadeIn(dac_q), Create(cx_dig), FadeIn(r_dig), run_time=1.2)
        leg = self.legenda("Agora são dois DACs: I e Q sobem até a IF separadamente, cada um no seu caminho",
                           leg, COR_IF)
        self.play(FadeIn(VGroup(lo, r_lo, hib, mix2_i, mix2_q, soma, rot_out)), Create(f_ana),
                  run_time=1.8)
        self.play(Create(cx_ana), FadeIn(r_ana), FadeIn(nota, shift=LEFT * 0.2))
        leg = self.legenda("E o que recebe os dois é o modulador vetorial da cena 3", leg)
        self.wait(0.6)

        # --- Fig. 24: o cancelamento, desenhado
        self.trocar_titulo(titulo, "8 · Por que a imagem desaparece")
        self.play(FadeOut(diagrama), FadeOut(nota), run_time=0.8)
        painel = []
        for x, nome, cor in [(-4.6, "I transladado", COR_I), (-0.2, "Q transladado", COR_Q),
                             (4.2, "RF", COR_RF)]:
            ax = eixos(P(x, 0.95), 3.0, 1.7, [440, 520, 40], [-1.2, 1.2, 1])
            cab = txt(nome, 18, cor).move_to(P(x, 2.08))
            rot = VGroup(txt("f_LO−f_IF", 13, GREY_B).next_to(ax.c2p(F_IMG, 0), DOWN, buff=0.52),
                         txt("f_LO+f_IF", 13, GREY_B).next_to(ax.c2p(F_RF, 0), DOWN, buff=0.52))
            painel.append((ax, cab, rot))
        mais = tex("+", WHITE, 44).move_to(P(-2.4, 0.95))
        igual = tex("=", WHITE, 44).move_to(P(2.0, 0.95))

        a_i1 = raia(painel[0][0], F_IMG, 0.8, COR_I, 6)
        a_i2 = raia(painel[0][0], F_RF, 0.8, COR_I, 6)
        a_q1 = raia(painel[1][0], F_IMG, -0.8, COR_Q, 6)
        a_q2 = raia(painel[1][0], F_RF, 0.8, COR_Q, 6)

        eq_i = tex(r"\cos\omega_{IF}t \cdot \sin\omega_{LO}t = \tfrac{1}{2}\big[\sin(\omega_{LO}+\omega_{IF})t"
                   r" + \sin(\omega_{LO}-\omega_{IF})t\big]", COR_I, 28)
        eq_q = tex(r"\sin\omega_{IF}t \cdot \cos\omega_{LO}t = \tfrac{1}{2}\big[\sin(\omega_{LO}+\omega_{IF})t"
                   r" - \sin(\omega_{LO}-\omega_{IF})t\big]", COR_Q, 28)
        eq_s = tex(r"\text{soma} = \sin(\omega_{LO}+\omega_{IF})t", COR_RF, 30)
        for m, y in ((eq_i, -1.15), (eq_q, -1.75), (eq_s, -2.4)):
            ajustar(m, 12.4).move_to(P(0, y))

        leg = self.legenda("Cada ramo, sozinho, ainda gera as duas bandas", leg)
        self.play(*[Create(p[0]) for p in painel], *[FadeIn(p[1]) for p in painel],
                  *[FadeIn(p[2]) for p in painel], FadeIn(mais), FadeIn(igual), run_time=1.6)
        self.play(GrowArrow(a_i1), GrowArrow(a_i2), FadeIn(eq_i), run_time=1.2)
        leg = self.legenda("Mas no ramo Q a banda de baixo nasce 180° fora de fase: ela aponta para baixo",
                           leg, COR_Q)
        self.play(GrowArrow(a_q1), GrowArrow(a_q2), FadeIn(eq_q), run_time=1.2)
        self.wait(0.5)
        leg = self.legenda("Somando os dois ramos no Σ: embaixo uma cancela a outra, em cima elas se reforçam",
                           leg, COR_RF)
        c_i1, c_i2 = a_i1.copy(), a_i2.copy()
        c_q1, c_q2 = a_q1.copy(), a_q2.copy()
        self.add(c_i1, c_i2, c_q1, c_q2)
        self.play(c_i1.animate.move_to(raia(painel[2][0], F_IMG, 0.8, COR_I, 6)),
                  c_q1.animate.move_to(raia(painel[2][0], F_IMG, -0.8, COR_Q, 6)),
                  c_i2.animate.move_to(raia(painel[2][0], F_RF, 0.8, COR_I, 6)),
                  c_q2.animate.move_to(raia(painel[2][0], F_RF, 0.8, COR_Q, 6)), run_time=1.6)
        nada = txt("cancelam", 14, GREY_B).next_to(painel[2][0].c2p(F_IMG, 0), UP, buff=0.12)
        alta = raia(painel[2][0], F_RF, 1.1, COR_RF, 7)
        self.play(FadeOut(c_i1, scale=0.3), FadeOut(c_q1, scale=0.3), FadeIn(nada),
                  FadeOut(c_i2), FadeOut(c_q2), GrowArrow(alta), FadeIn(eq_s), run_time=1.4)
        self.wait(0.8)
        leg = self.legenda("Uma banda lateral só, sem filtro nenhum — essa é a ideia do modulador SSB", leg,
                           COR_RF)
        self.wait(0.6)
        resto = raia(painel[2][0], F_IMG, 0.22, COR_ERRO, 5)
        nota2 = txt("na prática, desbalanço de ganho e skew impedem o cancelamento perfeito:\n"
                    "a razão entre a banda desejada e o resto é a supressão de banda lateral, em dBc",
                    19, line_spacing=0.85).move_to(P(0, -1.85))
        leg = self.legenda("No mundo real sobra sempre um pouquinho", leg, COR_ERRO)
        self.play(FadeOut(eq_i), FadeOut(eq_q), FadeOut(eq_s), FadeOut(nada), run_time=0.7)
        self.play(GrowArrow(resto), FadeIn(nota2, shift=UP * 0.15), run_time=1.3)
        self.wait(1.2)
        self.limpar()

    # ================================================================== CENA 9
    def cena_comparacao(self):
        self.titulo_cena("9 · Os três esquemas lado a lado")
        colx = [-1.95, 1.6, 5.2]
        y_cab = 2.25
        linhas_y = [1.45, 0.75, 0.05, -0.65, -1.35]
        cabs = VGroup(*[Text(t, font_size=20, weight=BOLD, color=WHITE).move_to(P(x, y_cab))
                        for t, x in zip(["Homodino", "Heteródino (banda dupla)", "Banda lateral única"], colx)])
        for c in cabs:
            ajustar(c, 3.3)
        rotulos = VGroup(*[txt(t, 18, GREY_A).move_to(P(-6.9, y), aligned_edge=LEFT)
                           for t, y in zip(["LO fica em", "imagem", "erros analógicos",
                                            "banda do DAC", "filtro na saída"], linhas_y)])
        h_line = Line(P(-7.0, 1.9), P(6.85, 1.9), color=COR_EIXO, stroke_width=2)
        v_line = Line(P(-3.6, 2.5), P(-3.6, -1.75), color=COR_EIXO, stroke_width=2)

        celulas = [
            ["f_RF = 500 MHz", "f_LO = 480 MHz", "f_LO = 480 MHz"],
            ["não existe", "sim, em 460 MHz", "cancelada, sobra um resto"],
            ["ganho, skew e offset", "só os do DAC", "ganho e skew de novo"],
            ["banda base (folgada)", "até a IF (apertada)", "dois DACs, até a IF"],
            ["pouco exigente", "obrigatório", "leve"],
        ]
        cores = [[GREY_A] * 3,
                 [GREEN_B, COR_ERRO, GREEN_B],
                 [COR_ERRO, GREEN_B, COR_ERRO],
                 [GREEN_B, COR_ERRO, COR_ERRO],
                 [GREY_A] * 3]
        grade = VGroup()
        for y, textos, cs in zip(linhas_y, celulas, cores):
            for x, t, c in zip(colx, textos, cs):
                grade.add(ajustar(txt(t, 16, c), 3.1).move_to(P(x, y)))

        fecho = txt("os três convivem no LLRF: escolher é decidir entre erro analógico e banda de DAC",
                    20, COR_EIXO).move_to(P(0, -2.25))

        leg = self.legenda("A mesma tarefa, três arranjos — e nenhum deles é de graça")
        self.play(FadeIn(cabs), Create(h_line), Create(v_line), FadeIn(rotulos), run_time=1.5)
        for k in range(5):
            self.play(FadeIn(grade[3 * k:3 * k + 3], shift=UP * 0.12), run_time=0.8)
            self.wait(0.45)
        leg = self.legenda("No homodino o erro entra depois do DAC; no heteródino, o aperto é no próprio DAC",
                           leg)
        self.wait(0.6)
        self.play(FadeIn(fecho, shift=UP * 0.15))
        leg = self.legenda("E a banda lateral única é o meio-termo: paga um modulador vetorial para não filtrar",
                           leg)
        self.wait(0.8)
        self.limpar()

    # ================================================================== RESUMO
    def cena_resumo(self):
        self.titulo_cena("Resumo")
        # cor só nos nomes dos esquemas, no mesmo código de cores das cenas
        itens = VGroup(*[Text(t, font_size=20, color=WHITE, t2c=c) for t, c in [
            ("• Up-conversion: transformar I e Q digitais em uma portadora de RF de verdade", {}),
            ("• Um DAC sintetizando 500 MHz sozinho (DDS) ainda não tem precisão e velocidade", {}),
            ("• I e Q são as coordenadas do fasor: A = √(I² + Q²) e φ₀ = atan(Q/I)",
             {"I": COR_I, "Q": COR_Q}),
            ("• Homodino = modulador vetorial: LO já em f_RF, uma banda só, sem imagem",
             {"Homodino": COR_RF}),
            ("• O preço é analógico: offset vira vazamento, ganho vira elipse, skew mistura I e Q", {}),
            ("• O skew é previsível: dá para pré-distorcer I e Q no FPGA, antes dos DACs", {}),
            ("• Heteródino: I e Q sobem para uma IF no digital — a quadratura vira número",
             {"Heteródino": COR_IF}),
            ("• Mas o mixer entrega f_LO ± f_IF: a imagem tem de ser filtrada", {}),
            ("• Banda lateral única: dois DACs e um modulador vetorial cancelam a imagem",
             {"Banda lateral única": COR_RF}),
            ("• O que escapa do cancelamento se mede em dBc: a supressão de banda lateral", {}),
        ]]).arrange(DOWN, aligned_edge=LEFT, buff=0.26).move_to(P(0, -0.25))
        ajustar(itens, 13.0)
        self.play(LaggedStart(*[FadeIn(t, shift=RIGHT * 0.2) for t in itens], lag_ratio=0.28),
                  run_time=5.0)
        self.wait(4.5)
        self.limpar()
