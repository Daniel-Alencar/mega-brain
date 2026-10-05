# -*- coding: utf-8 -*-
"""
Digital Down Conversion (DDC): da modulação IQ à extração digital de I e Q
==========================================================================

Renderização (a partir da raiz do repositório):
    manim -pql src/Digital_Down_Conversion/digital_down_conversion.py DigitalDownConversion  # rascunho
    manim -pqh src/Digital_Down_Conversion/digital_down_conversion.py DigitalDownConversion  # final

Requer LaTeX (MathTex).

Roteiro (segue "docs/Detecção de amplitude e fase em RF/Digital Down Conversion"):
    Abertura
    Cena 1  - Amplitude e fase → I e Q (identidade da soma de arcos)
    Cena 2  - Diagrama de modulação e demodulação IQ
    Cena 3  - Demodulação dos canais I e Q: produto, termos em 2ωc e LPF
    Cena 4  - Erro de fase Δθ no oscilador local: Q vaza para I
    Cena 5  - Motivação do DDC: taxa de amostragem × largura de banda
    Cena 6  - Os três blocos do DDC: misturadores, NCO e filtro de decimação
    Cena 7  - NCO: acumulador de fase, LUT, resolução e truncação de fase
    Cena 8  - Mistura digital no espectro, LPF e aliasing na decimação
    Cena 9  - Filtro CIC: estrutura, média móvel e resposta em frequência
    Cena 10 - DDC × IQ sampling clássico
    Resumo

Convenção:
    s(t) = A·cos(ωc·t + φ) = I·cos(ωc·t) − Q·sin(ωc·t),  I = A·cos φ,  Q = A·sin φ
    LPF{s·cos(ωc·t)} = I/2,   LPF{s·(−sin(ωc·t))} = Q/2
    LO com erro de fase: LPF{s·cos(ωc·t − Δθ)} = ½·I·cos Δθ − ½·Q·sin Δθ
"""

import numpy as np
from manim import *

# Paleta didática (fixa em todas as cenas)
COR_RF = BLUE            # sinal de RF / fasor
COR_LO = GREY_A          # oscilador local
COR_I = GOLD             # canal I
COR_Q = GREEN            # canal Q
COR_ALTA = RED           # componentes em 2ωc, espúrios, aliasing
COR_ERRO2 = ORANGE       # valor medido com erro
COR_NCO = TEAL           # NCO / processamento digital
COR_FILTRO = PINK        # filtros
COR_CHIP = PURPLE_B      # FPGA
COR_EIXO = GREY_B
FUNDO = "#0e1117"

EIXO_CFG = {"include_tip": False, "stroke_width": 2, "color": COR_EIXO}


# =============================================================================
# Utilitários de construção
# =============================================================================
def P(x, y):
    return np.array([x, y, 0.0])


def tex(s, cor=WHITE, tamanho=34):
    return MathTex(s, color=cor, font_size=tamanho)


def tex_partes(partes, tamanho=34):
    """Fórmula multicolorida. partes = [(tex, cor), ...]; cada tex deve ser LaTeX balanceado."""
    m = MathTex(*[p[0] for p in partes], font_size=tamanho)
    for sub, p in zip(m, partes):
        sub.set_color(p[1])
    return m


def seta(a, b, cor, largura=6):
    if np.linalg.norm(b - a) < 1e-3:
        return VMobject()
    return Arrow(a, b, buff=0, color=cor, stroke_width=largura,
                 max_tip_length_to_length_ratio=0.18, max_stroke_width_to_length_ratio=12)


def segmento(a, b, cor, largura=6):
    if np.linalg.norm(b - a) < 1e-3:
        return VMobject()
    return Line(a, b, color=cor, stroke_width=largura)


def tracejada(a, b, cor, largura=3):
    if np.linalg.norm(b - a) < 0.05:
        return VMobject()
    return DashedLine(a, b, color=cor, stroke_width=largura, dash_length=0.08)


def arco_angulo(centro, raio, inicio, angulo, cor, largura=3):
    if abs(angulo) < 0.02:
        return VMobject()
    return Arc(radius=raio, start_angle=inicio, angle=angulo, arc_center=centro,
               color=cor, stroke_width=largura)


def bloco(rotulo, largura=1.2, altura=0.7, cor=WHITE, tamanho=24):
    caixa = RoundedRectangle(corner_radius=0.1, width=largura, height=altura,
                             color=cor, stroke_width=3)
    return VGroup(caixa, Text(rotulo, font_size=tamanho, color=cor).move_to(caixa))


def bloco_tex(rotulo, largura=1.2, altura=0.7, cor=WHITE, tamanho=26):
    caixa = RoundedRectangle(corner_radius=0.1, width=largura, height=altura,
                             color=cor, stroke_width=3)
    return VGroup(caixa, tex(rotulo, cor, tamanho).move_to(caixa))


def mixer(cor=WHITE, raio=0.32):
    c = Circle(radius=raio, color=cor, stroke_width=3)
    d = raio * 0.7
    x = VGroup(Line(P(-d, d), P(d, -d)), Line(P(-d, -d), P(d, d))).set_stroke(cor, 3)
    return VGroup(c, x)


def fio(pontos, cor, largura=4):
    """Polilinha terminada em seta (fiação dos diagramas de blocos)."""
    g = VGroup(*[Line(pontos[k], pontos[k + 1], color=cor, stroke_width=largura)
                 for k in range(len(pontos) - 2)])
    g.add(Arrow(pontos[-2], pontos[-1], buff=0, color=cor, stroke_width=largura,
                max_tip_length_to_length_ratio=0.3))
    return g


def caminho(pontos):
    return VMobject().set_points_as_corners(pontos)


def plano(centro, tam=5.6, alcance=1.4):
    eixos = Axes(x_range=[-alcance, alcance, 0.5], y_range=[-alcance, alcance, 0.5],
                 x_length=tam, y_length=tam,
                 axis_config={"include_tip": True, "stroke_width": 2, "color": COR_EIXO})
    eixos.move_to(centro)
    rot_i = Text("I", font_size=30, color=COR_I).next_to(eixos.x_axis.get_end(), DOWN, buff=0.15)
    rot_q = Text("Q", font_size=30, color=COR_Q).next_to(eixos.y_axis.get_end(), LEFT, buff=0.15)
    return eixos, VGroup(rot_i, rot_q)


def eixos_tempo(centro, largura, altura, x_range, y_range):
    return Axes(x_range=x_range, y_range=y_range, x_length=largura, y_length=altura,
                axis_config=EIXO_CFG).move_to(centro)


def rotulo_eixo(ax, mob):
    """Coloca um rótulo acima do canto esquerdo de um eixo."""
    return mob.next_to(ax, UP, buff=0.04).align_to(ax, LEFT)


def marcar_x(ax, valores, rotulos, tamanho=18):
    return VGroup(*[Text(r, font_size=tamanho, color=COR_EIXO).next_to(ax.c2p(v, 0), DOWN, buff=0.12)
                    for v, r in zip(valores, rotulos)])


def haste(ax, x, y, cor, raio=0.05, largura=2):
    return VGroup(Line(ax.c2p(x, 0), ax.c2p(x, y), color=cor, stroke_width=largura),
                  Dot(ax.c2p(x, y), radius=raio, color=cor))


def raia(ax, f, altura, cor, largura=7):
    """Raia espectral (seta vertical) em f."""
    return seta(ax.c2p(f, 0), ax.c2p(f, altura), cor, largura)


def banda(ax, f0, cor, altura=1.0, meia=0.5):
    """Banda de informação estreita (topo plano) centrada em f0."""
    fs = np.linspace(f0 - 1.6 * meia, f0 + 1.6 * meia, 60)
    g = altura * np.exp(-((fs - f0) / meia) ** 6)
    pts = [ax.c2p(fs[0], 0)] + [ax.c2p(f, y) for f, y in zip(fs, g)] + [ax.c2p(fs[-1], 0)]
    return Polygon(*pts, color=cor, stroke_width=2, fill_color=cor, fill_opacity=0.55)


def cic_resposta(f, m, r=16, d=1):
    """|H(f)| do CIC normalizado pelo ganho DC (R·D)^M; f em unidades de f_out."""
    f = np.maximum(np.asarray(f, dtype=float), 1e-6)
    return np.abs(np.sin(np.pi * d * f) / (r * d * np.sin(np.pi * f / r))) ** m


# =============================================================================
# Cena
# =============================================================================
class DigitalDownConversion(Scene):
    def construct(self):
        self.camera.background_color = FUNDO
        self.abertura()
        self.cena_polar_iq()
        self.cena_modem()
        self.cena_demodulacao()
        self.cena_erro_fase()
        self.cena_motivacao()
        self.cena_blocos()
        self.cena_nco()
        self.cena_truncacao()
        self.cena_mistura_decimacao()
        self.cena_cic_estrutura()
        self.cena_cic_frequencia()
        self.cena_comparacao()
        self.cena_resumo()

    # ------------------------------------------------------------- utilidades
    def titulo_cena(self, texto):
        t = Text(texto, font_size=32, weight=BOLD).to_corner(UL, buff=0.35)
        linha = Line(t.get_corner(DL), t.get_corner(DR), color=COR_EIXO,
                     stroke_width=2).shift(DOWN * 0.12)
        self.play(Write(t), Create(linha), run_time=1)
        return VGroup(t, linha)

    def trocar_titulo(self, titulo, texto):
        novo = Text(texto, font_size=32, weight=BOLD).to_corner(UL, buff=0.35)
        linha = Line(novo.get_corner(DL), novo.get_corner(DR), color=COR_EIXO,
                     stroke_width=2).shift(DOWN * 0.12)
        self.play(Transform(titulo[0], novo), Transform(titulo[1], linha), run_time=0.8)

    def legenda(self, texto, anterior=None, cor=GREY_A):
        nova = Text(texto, font_size=24, color=cor).to_edge(DOWN, buff=0.3)
        if anterior is None:
            self.play(FadeIn(nova, shift=UP * 0.2), run_time=0.7)
        else:
            self.play(FadeOut(anterior, shift=UP * 0.2), FadeIn(nova, shift=UP * 0.2), run_time=0.7)
        return nova

    def limpar(self, manter=()):
        for m in self.mobjects:
            m.clear_updaters()
        saem = [m for m in self.mobjects if m not in manter]
        if saem:
            self.play(*[FadeOut(m) for m in saem], run_time=0.8)
        self.wait(0.2)

    # ---------------------------------------------------------------- abertura
    def abertura(self):
        titulo = Text("Digital Down Conversion", font_size=56, weight=BOLD)
        sub = Text("Da modulação IQ à extração digital de amplitude e fase", font_size=30, color=GREY_A)
        cadeia = Text("ADC  →  × NCO  →  CIC / FIR  →  ↓R  →  I, Q", font_size=24, color=COR_NCO)
        g = VGroup(titulo, sub, cadeia).arrange(DOWN, buff=0.35)
        self.play(Write(titulo), run_time=1.5)
        self.play(FadeIn(sub, shift=UP * 0.2), FadeIn(cadeia, shift=UP * 0.2))
        self.wait(1.2)
        self.play(FadeOut(g))

    # ================================================================== CENA 1
    def cena_polar_iq(self):
        self.titulo_cena("1 · Amplitude e fase → I e Q")
        amp = ValueTracker(1.0)
        fi = ValueTracker(np.deg2rad(40))
        W = TAU * 1.5   # 1,5 ciclos de portadora por unidade de tempo na tela

        def I():
            return amp.get_value() * np.cos(fi.get_value())

        def Q():
            return amp.get_value() * np.sin(fi.get_value())

        # Formas de onda (coluna direita)
        cfg = dict(largura=6.2, altura=1.2, x_range=[0, 2, 0.5], y_range=[-1.2, 1.2, 1])
        ax_i = eixos_tempo(P(3.55, 2.0), **cfg)
        ax_q = eixos_tempo(P(3.55, 0.25), **cfg)
        ax_s = eixos_tempo(P(3.55, -1.5), **cfg)
        lab_i = rotulo_eixo(ax_i, tex(r"I\cos\omega_c t", COR_I, 28))
        lab_q = rotulo_eixo(ax_q, tex(r"-Q\sin\omega_c t", COR_Q, 28))
        lab_s = rotulo_eixo(ax_s, tex(r"s(t) = A\cos(\omega_c t + \phi)", COR_RF, 28))

        def f_i():
            return ax_i.plot(lambda x: I() * np.cos(W * x), x_range=[0, 2, 0.01], color=COR_I, stroke_width=3)

        def f_q():
            return ax_q.plot(lambda x: -Q() * np.sin(W * x), x_range=[0, 2, 0.01], color=COR_Q, stroke_width=3)

        def f_s():
            return ax_s.plot(lambda x: amp.get_value() * np.cos(W * x + fi.get_value()),
                             x_range=[0, 2, 0.01], color=COR_RF, stroke_width=6)

        def f_soma():
            return ax_s.plot(lambda x: I() * np.cos(W * x) - Q() * np.sin(W * x),
                             x_range=[0, 2, 0.01], color=WHITE, stroke_width=2.5)

        # Fasor (coluna esquerda, embaixo)
        eixos, rotulos = plano(P(-3.6, -1.85), 3.0, 1.3)
        o = eixos.c2p(0, 0)

        def ponta():
            return eixos.c2p(I(), Q())

        fasor = always_redraw(lambda: seta(o, ponta(), COR_RF, 6))
        seg_i = always_redraw(lambda: segmento(o, eixos.c2p(I(), 0), COR_I, 8))
        seg_q = always_redraw(lambda: segmento(o, eixos.c2p(0, Q()), COR_Q, 8))
        proj_i = always_redraw(lambda: tracejada(ponta(), eixos.c2p(I(), 0), COR_I))
        proj_q = always_redraw(lambda: tracejada(ponta(), eixos.c2p(0, Q()), COR_Q))
        arco = always_redraw(lambda: arco_angulo(o, 0.35, 0, fi.get_value(), WHITE, 2))
        leituras = always_redraw(lambda: VGroup(
            Text(f"I = {I():+.2f}", font_size=20, color=COR_I),
            Text(f"Q = {Q():+.2f}", font_size=20, color=COR_Q),
            Text(f"A = {amp.get_value():.2f}", font_size=20, color=COR_RF),
            Text(f"φ = {np.rad2deg(fi.get_value()):+.0f}°", font_size=20, color=WHITE),
        ).arrange(RIGHT, buff=0.35).move_to(P(-3.6, 0.2)))

        # 1) O sinal modulado
        e1 = tex(r"s(t) = A(t)\cos\big(\omega_c t + \phi(t)\big)", WHITE, 34).move_to(P(-3.6, 2.55))
        self.play(Write(e1))
        leg = self.legenda("Sinal modulado: amplitude A(t) e fase φ(t) sobre uma portadora ωc")
        self.play(Create(ax_s), FadeIn(lab_s))
        curva_s = f_s()
        self.play(Create(curva_s), run_time=1.5)
        self.remove(curva_s)
        curva_s = always_redraw(f_s)
        self.add(curva_s)

        leg = self.legenda("Problema: girar a fase de um oscilador de RF rápido e com precisão é difícil",
                           leg, COR_ALTA)
        self.play(fi.animate.set_value(np.deg2rad(110)), run_time=1.5)
        self.play(fi.animate.set_value(np.deg2rad(40)), run_time=1.2)

        # 2) Identidade da soma de arcos
        e2 = tex(r"\cos(\alpha+\beta) = \cos\alpha\cos\beta - \sin\alpha\sin\beta", GREY_A, 28)
        e2.move_to(P(-3.6, 1.75))
        leg = self.legenda("A saída é matemática: a identidade da soma de arcos", leg)
        self.play(FadeIn(e2, shift=UP * 0.2))
        e3 = tex_partes([(r"s(t) = ", WHITE), (r"[A\cos\phi]", COR_I), (r"\cos\omega_c t", WHITE),
                         (r"-", WHITE), (r"[A\sin\phi]", COR_Q), (r"\sin\omega_c t", WHITE)], 32).move_to(e1)
        self.play(ReplacementTransform(e1, e3), FadeOut(e2), run_time=1.5)

        caixas = VGroup(SurroundingRectangle(e3[1], color=COR_I, buff=0.06),
                        SurroundingRectangle(e3[4], color=COR_Q, buff=0.06))
        defs = VGroup(tex(r"I = A\cos\phi", COR_I, 32), tex(r"Q = A\sin\phi", COR_Q, 32)
                      ).arrange(RIGHT, buff=0.8).move_to(P(-3.6, 1.7))
        leg = self.legenda("Os termos entre colchetes viram as componentes I (em fase) e Q (em quadratura)", leg)
        self.play(Create(caixas))
        self.play(TransformFromCopy(e3[1], defs[0]), TransformFromCopy(e3[4], defs[1]), run_time=1.3)
        e4 = tex_partes([(r"s(t) = ", WHITE), (r"I", COR_I), (r"\cos\omega_c t", WHITE),
                         (r"-", WHITE), (r"Q", COR_Q), (r"\sin\omega_c t", WHITE)], 36).move_to(e3)
        self.play(FadeOut(caixas), ReplacementTransform(e3, e4))

        # 3) Duas ondas ortogonais somadas
        leg = self.legenda("Duas ondas ortogonais (cosseno e seno), cada uma com amplitude fixa I ou Q", leg)
        self.play(Create(ax_i), FadeIn(lab_i), Create(ax_q), FadeIn(lab_q))
        ci, cq = f_i(), f_q()
        self.play(Create(ci), Create(cq), run_time=1.5)
        self.remove(ci, cq)
        ci, cq = always_redraw(f_i), always_redraw(f_q)
        self.add(ci, cq)

        leg = self.legenda("Somando as duas ondas obtemos exatamente A·cos(ωc·t + φ)", leg)
        copia_i, copia_q = f_i(), f_q()
        self.add(copia_i, copia_q)
        self.play(Transform(copia_i, f_soma()), Transform(copia_q, f_soma()), run_time=2)
        self.remove(copia_i, copia_q)
        soma = always_redraw(f_soma)
        self.add(soma)
        self.play(Indicate(e4, color=WHITE, scale_factor=1.08))

        # 4) O fasor (I, Q)
        leg = self.legenda("O ponto (I, Q) é o fasor: A é o comprimento e φ o ângulo", leg)
        self.play(Create(eixos), FadeIn(rotulos))
        self.add(fasor)
        self.play(Create(proj_i), Create(proj_q), Create(seg_i), Create(seg_q), Create(arco), FadeIn(leituras))
        leg = self.legenda("Mudar A e φ equivale a mudar só as amplitudes I e Q", leg)
        self.play(fi.animate.set_value(np.deg2rad(150)), run_time=2.5)
        self.play(amp.animate.set_value(0.6), fi.animate.set_value(np.deg2rad(-60)), run_time=2.5)
        self.play(amp.animate.set_value(1.0), fi.animate.set_value(np.deg2rad(40)), run_time=2)

        inv = VGroup(tex(r"A = \sqrt{I^2 + Q^2}", COR_RF, 32), tex(r"\phi = \arctan(Q/I)", WHITE, 32)
                     ).arrange(RIGHT, buff=0.8).move_to(P(-3.6, 0.95))
        leg = self.legenda("Volta: Pitágoras e trigonometria recuperam A e φ a partir de I e Q", leg)
        self.play(Write(inv), run_time=1.5)
        self.wait(1.5)
        self.limpar()

    # ================================================================== CENA 2
    def cena_modem(self):
        self.titulo_cena("2 · Modulação e demodulação IQ")
        yi, yq = 1.3, -1.3

        # Transmissor
        in_i = tex(r"I(t)", COR_I, 32).move_to(P(-6.35, yi))
        in_q = tex(r"Q(t)", COR_Q, 32).move_to(P(-6.35, yq))
        mt_i = mixer().move_to(P(-5.0, yi))
        mt_q = mixer().move_to(P(-5.0, yq))
        lo_ti = tex(r"\cos\omega_c t", COR_LO, 24).next_to(mt_i, UP, buff=0.12)
        lo_tq = tex(r"\sin\omega_c t", COR_LO, 24).next_to(mt_q, DOWN, buff=0.12)
        soma = VGroup(Circle(radius=0.3, color=WHITE, stroke_width=3),
                      tex(r"\Sigma", WHITE, 30)).move_to(P(-3.5, 0))
        s_mais = tex("+", COR_I, 28).move_to(P(-3.82, 0.48))
        s_menos = tex("-", COR_Q, 32).move_to(P(-3.82, -0.48))
        w_ti = fio([in_i.get_right() + RIGHT * 0.1, mt_i.get_left()], COR_I)
        w_tq = fio([in_q.get_right() + RIGHT * 0.1, mt_q.get_left()], COR_Q)
        w_ti2 = fio([mt_i.get_right(), P(-3.5, yi), soma.get_top()], COR_I)
        w_tq2 = fio([mt_q.get_right(), P(-3.5, yq), soma.get_bottom()], COR_Q)
        caixa_tx = DashedVMobject(RoundedRectangle(corner_radius=0.2, width=4.0, height=4.6),
                                  num_dashes=60).set_stroke(GREY_B, 2).move_to(P(-4.95, 0))
        rot_tx = Text("Transmissor", font_size=20, color=GREY_B).next_to(caixa_tx, UP, buff=0.08)

        # Canal
        no = Dot(P(-0.6, 0), radius=0.07, color=COR_RF)
        w_canal = Line(soma.get_right(), no.get_center(), color=COR_RF, stroke_width=4)
        rot_s = tex(r"s(t)", COR_RF, 30).next_to(w_canal, UP, buff=0.12)
        rot_canal = Text("canal ideal", font_size=18, color=GREY_B).next_to(w_canal, DOWN, buff=0.12)

        # Receptor
        mr_i = mixer().move_to(P(0.9, yi))
        mr_q = mixer().move_to(P(0.9, yq))
        lo_ri = tex(r"\cos\omega_c t", COR_LO, 24).next_to(mr_i, UP, buff=0.12)
        lo_rq = tex(r"-\sin\omega_c t", COR_LO, 24).next_to(mr_q, DOWN, buff=0.12)
        lpf_i = bloco("LPF", 1.0, 0.6, COR_FILTRO).move_to(P(2.6, yi))
        lpf_q = bloco("LPF", 1.0, 0.6, COR_FILTRO).move_to(P(2.6, yq))
        out_i = tex(r"I(t)/2", COR_I, 32).move_to(P(4.55, yi))
        out_q = tex(r"Q(t)/2", COR_Q, 32).move_to(P(4.55, yq))
        w_ri = fio([no.get_center(), P(-0.6, yi), mr_i.get_left()], COR_RF)
        w_rq = fio([no.get_center(), P(-0.6, yq), mr_q.get_left()], COR_RF)
        w_ri2 = fio([mr_i.get_right(), lpf_i.get_left()], COR_I)
        w_rq2 = fio([mr_q.get_right(), lpf_q.get_left()], COR_Q)
        w_ri3 = fio([lpf_i.get_right(), out_i.get_left() + LEFT * 0.1], COR_I)
        w_rq3 = fio([lpf_q.get_right(), out_q.get_left() + LEFT * 0.1], COR_Q)
        caixa_rx = DashedVMobject(RoundedRectangle(corner_radius=0.2, width=6.5, height=4.6),
                                  num_dashes=80).set_stroke(GREY_B, 2).move_to(P(2.15, 0))
        rot_rx = Text("Receptor", font_size=20, color=GREY_B).next_to(caixa_rx, UP, buff=0.08)

        eq_s = tex_partes([(r"s(t) = ", COR_RF), (r"I(t)", COR_I), (r"\cos\omega_c t - ", WHITE),
                           (r"Q(t)", COR_Q), (r"\sin\omega_c t", WHITE)], 32).move_to(P(0, -2.85))

        leg = self.legenda("Transmissor: I e Q multiplicam cosseno e seno da mesma portadora")
        self.play(FadeIn(in_i), FadeIn(in_q), Create(w_ti), Create(w_tq), FadeIn(mt_i), FadeIn(mt_q),
                  FadeIn(lo_ti), FadeIn(lo_tq))
        self.play(Create(w_ti2), Create(w_tq2), FadeIn(soma), FadeIn(s_mais), FadeIn(s_menos))
        self.play(Create(caixa_tx), FadeIn(rot_tx))
        leg = self.legenda("O somador forma o sinal de RF que segue pelo canal", leg)
        self.play(Create(w_canal), FadeIn(no), Write(rot_s), FadeIn(rot_canal))
        self.play(Write(eq_s))
        p_ti = caminho([in_i.get_right(), mt_i.get_left(), mt_i.get_right(), P(-3.5, yi),
                        soma.get_center(), no.get_center()])
        p_tq = caminho([in_q.get_right(), mt_q.get_left(), mt_q.get_right(), P(-3.5, yq),
                        soma.get_center(), no.get_center()])
        self.play(ShowPassingFlash(p_ti.set_stroke(WHITE, 7), time_width=0.4),
                  ShowPassingFlash(p_tq.set_stroke(WHITE, 7), time_width=0.4), run_time=1.5)

        leg = self.legenda("Receptor: multiplica s(t) por cos e −sin locais e filtra (LPF)", leg)
        self.play(Create(w_ri), Create(w_rq), FadeIn(mr_i), FadeIn(mr_q), FadeIn(lo_ri), FadeIn(lo_rq))
        self.play(Create(w_ri2), Create(w_rq2), FadeIn(lpf_i), FadeIn(lpf_q))
        self.play(Create(w_ri3), Create(w_rq3), Write(out_i), Write(out_q))
        self.play(Create(caixa_rx), FadeIn(rot_rx))
        p_ri = caminho([no.get_center(), P(-0.6, yi), mr_i.get_left(), mr_i.get_right(),
                        lpf_i.get_left(), lpf_i.get_right(), out_i.get_left()])
        p_rq = caminho([no.get_center(), P(-0.6, yq), mr_q.get_left(), mr_q.get_right(),
                        lpf_q.get_left(), lpf_q.get_right(), out_q.get_left()])
        for _ in range(2):
            self.play(ShowPassingFlash(p_ri.copy().set_stroke(WHITE, 7), time_width=0.4),
                      ShowPassingFlash(p_rq.copy().set_stroke(WHITE, 7), time_width=0.4), run_time=1.4)
        leg = self.legenda("Na saída, I e Q chegam separados (com fator ½). Vamos ver por quê.", leg)
        self.play(Indicate(out_i, color=COR_I), Indicate(out_q, color=COR_Q))
        self.wait(1.2)
        self.limpar()

    # ================================================================== CENA 3
    def cena_demodulacao(self):
        titulo = self.titulo_cena("3 · Demodulação: canal I")
        W = TAU * 2   # 2 ciclos de portadora por unidade

        def I(x):
            return 0.65 + 0.25 * np.sin(PI * x / 2)

        def Q(x):
            return 0.5 * np.cos(PI * x / 2 + 0.6)

        def s(x):
            return I(x) * np.cos(W * x) - Q(x) * np.sin(W * x)

        xr = [0, 4, 0.005]
        ax_s = eixos_tempo(P(3.5, 2.15), 6.2, 1.1, [0, 4, 1], [-1.3, 1.3, 1])
        ax_lo = eixos_tempo(P(3.5, 0.6), 6.2, 0.9, [0, 4, 1], [-1.2, 1.2, 1])
        ax_x = eixos_tempo(P(3.5, -1.55), 6.2, 2.1, [0, 4, 1], [-1.3, 1.3, 0.5])
        lab_s = rotulo_eixo(ax_s, tex(r"s(t)", COR_RF, 26))
        lab_lo = rotulo_eixo(ax_lo, tex(r"\mathrm{LO}_I = \cos\omega_c t", COR_LO, 26))
        lab_x = rotulo_eixo(ax_x, tex(r"X_I(t) = s(t)\cdot\cos\omega_c t", WHITE, 26))
        curva_s = ax_s.plot(s, x_range=xr, color=COR_RF, stroke_width=3)
        curva_lo = ax_lo.plot(lambda x: np.cos(W * x), x_range=xr, color=COR_LO, stroke_width=3)
        produto = ax_x.plot(lambda x: s(x) * np.cos(W * x), x_range=xr, color=WHITE, stroke_width=2.5)
        saida = ax_x.plot(lambda x: I(x) / 2, x_range=xr, color=COR_I, stroke_width=7)

        # Dedução (coluna esquerda)
        d1 = tex(r"X_I(t) = s(t)\cdot\cos\omega_c t", WHITE, 30)
        d2 = tex(r"X_I = [I\cos\omega_c t - Q\sin\omega_c t]\cos\omega_c t", WHITE, 30)
        d3 = tex(r"X_I = I\cos^2\omega_c t - Q\sin\omega_c t\cos\omega_c t", WHITE, 30)
        dh = tex(r"\cos^2 x = \tfrac{1+\cos 2x}{2},\qquad \sin x\cos x = \tfrac{\sin 2x}{2}", GREY_A, 28)
        d4 = tex_partes([(r"X_I = ", WHITE), (r"\frac{I}{2}", COR_I),
                         (r"+\frac{I}{2}\cos 2\omega_c t", COR_ALTA),
                         (r"-\frac{Q}{2}\sin 2\omega_c t", COR_ALTA)], 30)
        d5 = tex_partes([(r"X_{I,\mathrm{LPF}}(t) = ", WHITE), (r"\frac{I(t)}{2}", COR_I)], 36)
        deducao = VGroup(d1, d2, d3, dh, d4, d5).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        deducao.to_edge(LEFT, buff=0.4).align_to(P(0, 2.9), UP)

        leg = self.legenda("No receptor chega s(t) = I·cos ωc·t − Q·sin ωc·t")
        self.play(Create(ax_s), FadeIn(lab_s))
        self.play(Create(curva_s), run_time=1.5)
        leg = self.legenda("Para isolar I, multiplicamos s(t) por um cosseno gerado localmente", leg)
        self.play(Write(d1))
        self.play(Create(ax_lo), FadeIn(lab_lo), Create(curva_lo), run_time=1.2)
        self.play(Create(ax_x), FadeIn(lab_x))
        self.play(Create(produto), run_time=2.5)

        leg = self.legenda("Substituindo s(t) e distribuindo a multiplicação", leg)
        self.play(Write(d2), run_time=1.3)
        self.play(Write(d3), run_time=1.3)
        leg = self.legenda("Identidades: cos² e sin·cos viram termos em 2ωc", leg)
        self.play(FadeIn(dh, shift=UP * 0.1))
        self.play(Write(d4), run_time=1.5)
        leg = self.legenda("Os termos em vermelho oscilam no DOBRO da frequência da portadora", leg, COR_ALTA)
        self.play(Indicate(d4[2], color=COR_ALTA), Indicate(d4[3], color=COR_ALTA))
        self.play(ShowPassingFlash(produto.copy().set_stroke(COR_ALTA, 5), time_width=0.3), run_time=2)

        leg = self.legenda("Filtro passa-baixa: elimina 2ωc e deixa passar o que varia devagar", leg, COR_FILTRO)
        self.play(produto.animate.set_stroke(opacity=0.3),
                  ReplacementTransform(produto.copy(), saida), run_time=2.2)
        self.play(Write(d5))
        caixa = SurroundingRectangle(d5, color=COR_I, buff=0.1)
        self.play(Create(caixa))
        leg = self.legenda("Recuperamos I(t)! O fator ½ se corrige com um ganho", leg, COR_I)
        self.wait(1.5)

        # Canal Q: o mesmo processo com −sin
        self.trocar_titulo(titulo, "3 · Demodulação: canal Q")
        q1 = tex(r"X_Q(t) = s(t)\cdot(-\sin\omega_c t)", WHITE, 30)
        q2 = tex(r"X_Q = -I\sin\omega_c t\cos\omega_c t + Q\sin^2\omega_c t", WHITE, 30)
        qh = tex(r"\sin^2 x = \tfrac{1-\cos 2x}{2},\qquad \sin x\cos x = \tfrac{\sin 2x}{2}", GREY_A, 28)
        q3 = tex_partes([(r"X_Q = ", WHITE), (r"-\frac{I}{2}\sin 2\omega_c t", COR_ALTA),
                         (r"+\frac{Q}{2}", COR_Q), (r"-\frac{Q}{2}\cos 2\omega_c t", COR_ALTA)], 30)
        q4 = tex_partes([(r"X_{Q,\mathrm{LPF}}(t) = ", WHITE), (r"\frac{Q(t)}{2}", COR_Q)], 36)
        deducao_q = VGroup(q1, q2, qh, q3, q4).arrange(DOWN, aligned_edge=LEFT, buff=0.32)
        deducao_q.to_edge(LEFT, buff=0.4).align_to(P(0, 2.9), UP)

        lab_lo_q = rotulo_eixo(ax_lo, tex(r"\mathrm{LO}_Q = -\sin\omega_c t", COR_LO, 26))
        lab_x_q = rotulo_eixo(ax_x, tex(r"X_Q(t) = s(t)\cdot(-\sin\omega_c t)", WHITE, 26))
        curva_lo_q = ax_lo.plot(lambda x: -np.sin(W * x), x_range=xr, color=COR_LO, stroke_width=3)
        produto_q = ax_x.plot(lambda x: -s(x) * np.sin(W * x), x_range=xr, color=WHITE, stroke_width=2.5)
        saida_q = ax_x.plot(lambda x: Q(x) / 2, x_range=xr, color=COR_Q, stroke_width=7)

        leg = self.legenda("Para isolar Q: o mesmo processo, com o oscilador em quadratura −sin ωc·t", leg)
        self.play(FadeOut(deducao), FadeOut(caixa), FadeOut(saida), FadeOut(produto),
                  Transform(lab_lo, lab_lo_q), Transform(curva_lo, curva_lo_q), Transform(lab_x, lab_x_q))
        self.play(Write(q1))
        self.play(Create(produto_q), run_time=2)
        self.play(Write(q2), run_time=1.2)
        self.play(FadeIn(qh, shift=UP * 0.1))
        self.play(Write(q3), run_time=1.3)
        leg = self.legenda("De novo, os termos em 2ωc são removidos pelo LPF", leg, COR_FILTRO)
        self.play(Indicate(q3[1], color=COR_ALTA), Indicate(q3[3], color=COR_ALTA))
        self.play(produto_q.animate.set_stroke(opacity=0.3),
                  ReplacementTransform(produto_q.copy(), saida_q), run_time=2)
        self.play(Write(q4))
        self.play(Create(SurroundingRectangle(q4, color=COR_Q, buff=0.1)))
        leg = self.legenda("Cada canal recupera a sua componente, sem interferência do outro", leg, COR_Q)
        self.wait(1.5)
        self.limpar()

    # ================================================================== CENA 4
    def cena_erro_fase(self):
        self.titulo_cena("4 · Erro de fase Δθ no oscilador local")
        dth = ValueTracker(0.0)   # graus
        fi0 = np.deg2rad(55)
        I0, Q0 = np.cos(fi0), np.sin(fi0)

        # Geometria (direita)
        eixos, rotulos = plano(P(3.7, -0.85), 4.0, 1.3)
        o = eixos.c2p(0, 0)

        def u():
            d = np.deg2rad(dth.get_value())
            return np.array([np.cos(d), -np.sin(d)])

        def medido():
            return float(np.dot([I0, Q0], u()))

        fasor = seta(o, eixos.c2p(I0, Q0), COR_RF, 6)
        rot_fasor = tex(r"(I, Q)", COR_RF, 26).next_to(eixos.c2p(I0, Q0), UR, buff=0.05)
        seg_real = segmento(o, eixos.c2p(I0, 0), COR_I, 10)
        eixo_med = always_redraw(lambda: DashedLine(eixos.c2p(*(-1.3 * u())), eixos.c2p(*(1.3 * u())),
                                                    color=COR_ALTA, stroke_width=3, dash_length=0.12))
        proj = always_redraw(lambda: tracejada(eixos.c2p(I0, Q0), eixos.c2p(*(medido() * u())), COR_ERRO2))
        seg_med = always_redraw(lambda: segmento(o, eixos.c2p(*(medido() * u())), COR_ERRO2, 5))
        arco = always_redraw(lambda: arco_angulo(o, 1.0, 0, -np.deg2rad(dth.get_value()), COR_ALTA))
        leituras = always_redraw(lambda: VGroup(
            Text(f"Δθ = {dth.get_value():+.0f}°", font_size=22, color=COR_ALTA),
            VGroup(Text(f"I real = {I0:.2f}", font_size=22, color=COR_I),
                   Text(f"I medido = {medido():.2f}", font_size=22, color=COR_ERRO2)).arrange(RIGHT, buff=0.5),
        ).arrange(DOWN, buff=0.15).move_to(P(3.7, 2.35)))

        # Álgebra (esquerda)
        l1 = tex(r"\mathrm{LO}_I = \cos(\omega_c t - \Delta\theta)", COR_LO, 30)
        l2 = tex(r"= \cos\omega_c t\cos\Delta\theta + \sin\omega_c t\sin\Delta\theta", COR_LO, 28)
        cab = Text("Multiplicando s(t) por esse LO, surgem 4 termos:", font_size=22, color=GREY_A)
        termos = VGroup(
            tex(r"1.\;\; I\cos^2\omega_c t\,\cos\Delta\theta", WHITE, 28),
            tex(r"2.\;\; I\cos\omega_c t\sin\omega_c t\,\sin\Delta\theta", WHITE, 28),
            tex(r"3.\;\; -Q\sin\omega_c t\cos\omega_c t\,\cos\Delta\theta", WHITE, 28),
            tex(r"4.\;\; -Q\sin^2\omega_c t\,\sin\Delta\theta", WHITE, 28),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        resultado = tex_partes([(r"X_{I,\mathrm{LPF}} = ", WHITE), (r"\tfrac{1}{2} I\cos\Delta\theta", COR_I),
                                (r"-\tfrac{1}{2} Q\sin\Delta\theta", COR_ALTA)], 34)
        esquerda = VGroup(l1, l2, cab, termos, resultado).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        esquerda.to_edge(LEFT, buff=0.4).align_to(P(0, 2.9), UP)
        l2.shift(RIGHT * 0.6)
        resultado.shift(DOWN * 0.15)

        leg = self.legenda("Ideal: o LO do receptor está alinhado com o do transmissor (Δθ = 0)")
        self.play(Create(eixos), FadeIn(rotulos))
        self.play(GrowArrow(fasor), FadeIn(rot_fasor))
        self.play(Create(seg_real), FadeIn(eixo_med), Create(seg_med), FadeIn(leituras))
        self.add(proj, arco)

        leg = self.legenda("E se o oscilador local tiver um erro de fase Δθ?", leg, COR_ALTA)
        self.play(Write(l1))
        self.play(Write(l2), run_time=1.3)
        leg = self.legenda("Multiplicando tudo por tudo: 4 termos", leg)
        self.play(FadeIn(cab))
        self.play(LaggedStart(*[Write(t) for t in termos], lag_ratio=0.4), run_time=3)

        leg = self.legenda("Termos 2 e 3 contêm sin·cos ⇒ oscilam em 2ωc ⇒ o LPF zera", leg, COR_FILTRO)
        mortos = VGroup()
        for k in (1, 2):
            t = termos[k]
            risco = Line(t.get_left() + LEFT * 0.05, t.get_right() + RIGHT * 0.05, color=COR_ALTA, stroke_width=4)
            nota = Text("2ωc ✗", font_size=20, color=COR_ALTA).next_to(t, RIGHT, buff=0.2)
            mortos.add(risco, nota)
            self.play(Create(risco), FadeIn(nota), t.animate.set_opacity(0.4), run_time=0.8)

        leg = self.legenda("Termos 1 e 4 contêm cos² e sin²: a constante ½ sobrevive ao filtro", leg)
        vivos = VGroup(
            tex(r"\rightarrow \tfrac{1}{2} I\cos\Delta\theta", COR_I, 28).next_to(termos[0], RIGHT, buff=0.2),
            tex(r"\rightarrow -\tfrac{1}{2} Q\sin\Delta\theta", COR_ALTA, 28).next_to(termos[3], RIGHT, buff=0.2),
        )
        self.play(FadeIn(vivos[0], shift=RIGHT * 0.2), FadeIn(vivos[1], shift=RIGHT * 0.2))
        self.play(Write(resultado), run_time=1.5)
        caixa = SurroundingRectangle(resultado[2], color=COR_ALTA, buff=0.08)
        rot_vaz = Text("um pedaço de Q vaza para dentro de I", font_size=20, color=COR_ALTA
                       ).next_to(caixa, DOWN, buff=0.12).align_to(resultado, LEFT)
        self.play(Create(caixa), FadeIn(rot_vaz))

        leg = self.legenda("Geometricamente: o eixo de medição de I gira de Δθ e I medido vira projeção", leg)
        self.play(dth.animate.set_value(20), run_time=2.5)
        self.wait(0.5)
        self.play(dth.animate.set_value(-25), run_time=3)
        self.wait(0.5)
        leg = self.legenda("Com Δθ = 0: cos Δθ = 1, sin Δθ = 0, o termo de Q some e X_I = I/2", leg, COR_I)
        self.play(dth.animate.set_value(0), run_time=2)
        self.play(Indicate(resultado[1], color=COR_I))
        self.wait(1.5)
        self.limpar()

    # ================================================================== CENA 5
    def cena_motivacao(self):
        self.titulo_cena("5 · Por que DDC? Taxa de amostragem × banda")
        ax = Axes(x_range=[-5, 50, 5], y_range=[0, 1.3, 0.5], x_length=12.4, y_length=2.3,
                  axis_config={"include_tip": True, "stroke_width": 2, "color": COR_EIXO},
                  y_axis_config={"include_tip": False}).move_to(P(0, 1.0))
        marcas = marcar_x(ax, [0, 10, 20, 30, 40, 50], ["0", "10", "20", "30", "40", "50"])
        rot_f = Text("f (MHz)", font_size=18, color=COR_EIXO).next_to(ax.x_axis.get_end(), UP, buff=0.12)
        fc = ValueTracker(40.0)
        sinal = always_redraw(lambda: banda(ax, fc.get_value(), COR_RF))
        rot_b = Text("B = 1 MHz", font_size=20, color=COR_RF)
        rot_b.add_updater(lambda m: m.next_to(ax.c2p(fc.get_value(), 1.0), UR, buff=0.08))

        leg = self.legenda("A informação útil ocupa uma banda estreita (1 MHz) em torno de 40 MHz")
        self.play(Create(ax), FadeIn(marcas), FadeIn(rot_f))
        self.play(FadeIn(sinal), FadeIn(rot_b))

        fmax = DoubleArrow(ax.c2p(0, 1.2), ax.c2p(40.5, 1.2), buff=0, color=COR_ALTA, stroke_width=3,
                           max_tip_length_to_length_ratio=0.03)
        rot_fmax = Text("f_max ≈ 40,5 MHz", font_size=20, color=COR_ALTA).next_to(fmax, UP, buff=0.08)
        nyq = tex(r"f_s > 2 f_{max} \;\Rightarrow\; f_s \gtrsim 82\ \mathrm{MSps}", COR_ALTA, 32
                  ).move_to(P(3.3, 2.85))
        leg = self.legenda("Nyquist clássico: amostrar acima do dobro da maior frequência", leg, COR_ALTA)
        self.play(GrowFromCenter(fmax), FadeIn(rot_fmax))
        self.play(Write(nyq))

        escala = 10.5 / 82
        x0 = -5.3
        barra_alta = Rectangle(width=82 * escala, height=0.45, color=COR_ALTA, fill_opacity=0.6,
                               stroke_width=2).move_to(P(x0 + 41 * escala, -1.4))
        rot_alta = Text("82 MSps", font_size=20, color=WHITE).move_to(barra_alta)
        tag_alta = Text("sem DDC", font_size=20, color=COR_ALTA).next_to(barra_alta, LEFT, buff=0.2)
        self.play(GrowFromEdge(barra_alta, LEFT), FadeIn(tag_alta), FadeIn(rot_alta), run_time=1.5)
        leg = self.legenda("Um fluxo enorme de números para a FPGA processar: recursos e consumo", leg)
        self.wait(1)

        nyq2 = tex(r"f_s \geq 2B = 2\ \mathrm{MSps}", COR_I, 32).move_to(nyq)
        leg = self.legenda("Nyquist–Shannon: basta amostrar a 2× a LARGURA DE BANDA da informação", leg, COR_I)
        self.play(FadeOut(fmax), FadeOut(rot_fmax))
        rot_nco = Text("× NCO (40 MHz): translada para 0 Hz", font_size=22, color=COR_NCO).move_to(ax.c2p(20, 0.7))
        seta_desloc = Arrow(ax.c2p(37, 0.4), ax.c2p(3, 0.4), buff=0, color=COR_NCO, stroke_width=4,
                            max_tip_length_to_length_ratio=0.04)
        self.play(FadeIn(rot_nco), GrowArrow(seta_desloc))
        self.play(fc.animate.set_value(0.0), run_time=3, rate_func=smooth)
        self.play(FadeOut(seta_desloc), ReplacementTransform(nyq, nyq2))

        barra_baixa = Rectangle(width=2 * escala, height=0.45, color=COR_I, fill_opacity=0.8,
                                stroke_width=2).move_to(P(x0 + escala, -2.3))
        rot_baixa = Text("2 MSps", font_size=20, color=COR_I).next_to(barra_baixa, RIGHT, buff=0.2)
        tag_baixa = Text("com DDC", font_size=20, color=COR_I).next_to(barra_baixa, LEFT, buff=0.2
                                                                       ).align_to(tag_alta, RIGHT)
        dec = Text("decimação  ↓R", font_size=22, color=COR_FILTRO).move_to(P(2.5, -2.3))
        leg = self.legenda("Em banda base, filtramos e descartamos amostras (decimação)", leg, COR_FILTRO)
        self.play(GrowFromEdge(barra_baixa, LEFT), FadeIn(tag_baixa), FadeIn(rot_baixa), FadeIn(dec))
        leg = self.legenda("Mesma informação, 41× menos números por segundo", leg, COR_I)
        self.play(Indicate(barra_baixa, color=COR_I, scale_factor=1.5))
        self.wait(1.5)
        self.limpar()

    # ================================================================== CENA 6
    def cena_blocos(self):
        self.titulo_cena("6 · Os três blocos do DDC")
        yi, yq = 1.5, -1.5
        adc = bloco("ADC", 1.0, 0.7, WHITE).move_to(P(-6.1, 0))
        no = Dot(P(-4.95, 0), radius=0.07, color=WHITE)
        rot_x = tex(r"x[n]", WHITE, 26).next_to(P(-5.4, 0), UP, buff=0.1)
        m_i = mixer(COR_I).move_to(P(-3.6, yi))
        m_q = mixer(COR_Q).move_to(P(-3.6, yq))
        nco = bloco("NCO", 1.2, 0.8, COR_NCO).move_to(P(-3.6, 0))
        rot_cos = tex(r"\cos[n]", COR_NCO, 22).next_to(P(-3.6, 0.95), RIGHT, buff=0.1)
        rot_sin = tex(r"-\sin[n]", COR_NCO, 22).next_to(P(-3.6, -0.95), RIGHT, buff=0.1)
        f_i = bloco("LPF\nCIC / FIR", 1.5, 0.95, COR_FILTRO, 20).move_to(P(-1.55, yi))
        f_q = bloco("LPF\nCIC / FIR", 1.5, 0.95, COR_FILTRO, 20).move_to(P(-1.55, yq))
        d_i = bloco_tex(r"\downarrow R", 0.9, 0.7, COR_FILTRO, 30).move_to(P(0.25, yi))
        d_q = bloco_tex(r"\downarrow R", 0.9, 0.7, COR_FILTRO, 30).move_to(P(0.25, yq))
        o_i = tex(r"I[m]", COR_I, 32).move_to(P(1.6, yi))
        o_q = tex(r"Q[m]", COR_Q, 32).move_to(P(1.6, yq))
        fpga = DashedVMobject(RoundedRectangle(corner_radius=0.25, width=7.4, height=4.9),
                              num_dashes=80).set_stroke(COR_CHIP, 3).move_to(P(-1.55, 0))
        rot_fpga = Text("FPGA / ASIC", font_size=20, color=COR_CHIP, weight=BOLD).next_to(
            fpga.get_corner(DL), UR, buff=0.12)

        w_adc = fio([adc.get_right(), no.get_center()], WHITE)
        w_i0 = fio([no.get_center(), P(-4.95, yi), m_i.get_left()], WHITE)
        w_q0 = fio([no.get_center(), P(-4.95, yq), m_q.get_left()], WHITE)
        w_ni = fio([nco.get_top(), m_i.get_bottom()], COR_NCO, 3)
        w_nq = fio([nco.get_bottom(), m_q.get_top()], COR_NCO, 3)
        w_i1 = fio([m_i.get_right(), f_i.get_left()], COR_I)
        w_q1 = fio([m_q.get_right(), f_q.get_left()], COR_Q)
        w_i2 = fio([f_i.get_right(), d_i.get_left()], COR_I)
        w_q2 = fio([f_q.get_right(), d_q.get_left()], COR_Q)
        w_i3 = fio([d_i.get_right(), o_i.get_left() + LEFT * 0.1], COR_I)
        w_q3 = fio([d_q.get_right(), o_q.get_left() + LEFT * 0.1], COR_Q)

        tags = VGroup(
            Text("A", font_size=26, color=YELLOW, weight=BOLD).next_to(m_i, UP, buff=0.15),
            Text("B", font_size=26, color=YELLOW, weight=BOLD).next_to(nco, LEFT, buff=0.2),
            Text("C", font_size=26, color=YELLOW, weight=BOLD).next_to(f_i, UP, buff=0.15),
        )
        notas = [
            ("A · Misturadores digitais", "x[n]·cos[n] e x[n]·(−sin[n]):\ndiferença → banda base\nsoma → frequência dupla", COR_I),
            ("B · NCO", "gera cos[n] e −sin[n]\ndo mesmo relógio:\nquadratura de 90° exata", COR_NCO),
            ("C · LPF de decimação", "1) elimina a soma\n2) anti-aliasing antes\n    do descarte (↓R)", COR_FILTRO),
        ]

        def painel(cab, corpo, cor):
            return VGroup(Text(cab, font_size=22, color=cor, weight=BOLD),
                          Text(corpo, font_size=19, color=GREY_A, line_spacing=1.2)
                          ).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to(P(4.5, 0)).align_to(P(2.65, 0), LEFT)

        leg = self.legenda("O sinal sai do ADC e entra na FPGA como uma sequência de números x[n]")
        self.play(FadeIn(adc), Create(w_adc), FadeIn(no), FadeIn(rot_x))
        self.play(Create(fpga), FadeIn(rot_fpga))
        self.play(Create(w_i0), Create(w_q0), FadeIn(m_i), FadeIn(m_q), FadeIn(tags[0]))
        p_a = painel(*notas[0])
        leg = self.legenda("Bloco A: multiplicadores fazem o papel dos mixers", leg, COR_I)
        self.play(FadeIn(p_a, shift=LEFT * 0.2), Indicate(VGroup(m_i, m_q), color=COR_I))

        self.play(FadeIn(nco), Create(w_ni), Create(w_nq), FadeIn(rot_cos), FadeIn(rot_sin), FadeIn(tags[1]))
        p_b = painel(*notas[1])
        leg = self.legenda("Bloco B: o NCO é um oscilador numérico (sem desbalanço de fase/ganho)", leg, COR_NCO)
        self.play(FadeOut(p_a), FadeIn(p_b, shift=LEFT * 0.2), Indicate(nco, color=COR_NCO))

        self.play(Create(w_i1), Create(w_q1), FadeIn(f_i), FadeIn(f_q), FadeIn(tags[2]))
        self.play(Create(w_i2), Create(w_q2), FadeIn(d_i), FadeIn(d_q))
        self.play(Create(w_i3), Create(w_q3), Write(o_i), Write(o_q))
        p_c = painel(*notas[2])
        leg = self.legenda("Bloco C: filtro passa-baixa seguido da redução de taxa ↓R", leg, COR_FILTRO)
        self.play(FadeOut(p_b), FadeIn(p_c, shift=LEFT * 0.2), Indicate(VGroup(f_i, f_q, d_i, d_q), color=COR_FILTRO))

        p_i = caminho([adc.get_right(), no.get_center(), P(-4.95, yi), m_i.get_left(), m_i.get_right(),
                       f_i.get_left(), f_i.get_right(), d_i.get_left(), d_i.get_right(), o_i.get_left()])
        p_q = caminho([adc.get_right(), no.get_center(), P(-4.95, yq), m_q.get_left(), m_q.get_right(),
                       f_q.get_left(), f_q.get_right(), d_q.get_left(), d_q.get_right(), o_q.get_left()])
        leg = self.legenda("Saída: I e Q em banda base, a uma taxa R vezes menor", leg)
        for _ in range(2):
            self.play(ShowPassingFlash(p_i.copy().set_stroke(WHITE, 7), time_width=0.4),
                      ShowPassingFlash(p_q.copy().set_stroke(WHITE, 7), time_width=0.4), run_time=1.6)
        self.wait(1)
        self.limpar()

    # ================================================================== CENA 7
    def cena_nco(self):
        self.titulo_cena("7 · NCO: acumulador de fase + tabela")
        npos = 16
        centro = P(-4.6, -0.4)
        raio = 1.6
        roda = Circle(radius=raio, color=COR_EIXO, stroke_width=3).move_to(centro)

        def direcao(k):
            a = TAU * k / npos
            return np.array([np.cos(a), np.sin(a), 0.0])

        marcas = VGroup(*[Line(centro + 0.9 * raio * direcao(k), centro + raio * direcao(k),
                               color=COR_EIXO, stroke_width=2) for k in range(npos)])
        numeros = VGroup(*[Text(str(k), font_size=16, color=GREY_A).move_to(centro + 1.17 * raio * direcao(k))
                           for k in range(npos)])
        acc = ValueTracker(0.0)
        M = ValueTracker(3)
        ponteiro = always_redraw(lambda: seta(centro, centro + 0.85 * raio * direcao(acc.get_value()), COR_NCO, 6))
        registro = always_redraw(lambda: Text(
            f"fase = {int(round(acc.get_value())) % npos:2d}  ({int(round(acc.get_value())) % npos:04b})",
            font="Monospace", font_size=22, color=COR_NCO).next_to(roda, DOWN, buff=0.45))
        regra = tex(r"\text{fase} \leftarrow (\text{fase} + M) \bmod 2^N", WHITE, 28).move_to(P(-4.6, 2.55))
        params = always_redraw(lambda: Text(f"N = 4 bits  ·  M = {int(M.get_value())}", font_size=22,
                                            color=GREY_A).move_to(P(-4.6, 2.0)))

        lut = bloco("LUT\nfase → cos", 1.4, 1.0, COR_NCO, 20).move_to(P(-1.35, -0.4))
        w_lut = fio([P(-2.55, -0.4), lut.get_left()], COR_NCO, 3)
        ax = eixos_tempo(P(3.85, -0.1), 5.9, 2.6, [0, 16, 1], [-1.2, 1.2, 1])
        w_ax = fio([lut.get_right(), ax.get_left() + LEFT * 0.05], COR_NCO, 3)
        rot_ax = rotulo_eixo(ax, Text("saída: cos[n]", font_size=20, color=COR_NCO))
        rot_n = Text("n (ciclos de clock) →", font_size=18, color=COR_EIXO).next_to(ax, DOWN, buff=0.08
                                                                                     ).align_to(ax, RIGHT)
        f_out = tex(r"f_{out} = \frac{M}{2^N}\, f_{CLK}", WHITE, 34).move_to(P(2.9, -2.1))
        f_val = always_redraw(lambda: tex(rf"= \tfrac{{{int(M.get_value())}}}{{16}}\, f_{{CLK}}", COR_NCO, 32
                                          ).next_to(f_out, RIGHT, buff=0.25))

        leg = self.legenda("Acumulador de fase: um registrador de N bits que dá voltas")
        self.play(Create(roda), Create(marcas), FadeIn(numeros))
        self.add(ponteiro)
        self.play(Write(regra), FadeIn(params), FadeIn(registro))
        leg = self.legenda("A LUT converte a fase em amplitude (cosseno)", leg)
        self.play(Create(w_lut), FadeIn(lut), Create(w_ax), Create(ax), FadeIn(rot_ax), FadeIn(rot_n))

        def rodar(passos, tempo):
            hastes = VGroup()
            for n in range(passos):
                k = int(round(acc.get_value())) % npos
                h = haste(ax, n, np.cos(TAU * k / npos), COR_NCO, 0.06, 3)
                hastes.add(h)
                self.play(GrowFromPoint(h, ax.c2p(n, 0)), run_time=tempo * 0.45)
                self.play(acc.animate.increment_value(M.get_value()), run_time=tempo * 0.55)
            return hastes

        leg = self.legenda("A cada clock soma-se a palavra de sintonia M; a LUT lê o cosseno da fase", leg, COR_NCO)
        h3 = rodar(4, 0.9)
        h3.add(*rodar(12, 0.35))
        guia = DashedVMobject(ax.plot(lambda x: np.cos(TAU * 3 * x / npos), x_range=[0, 15, 0.02],
                                      color=COR_NCO, stroke_width=2), num_dashes=60)
        self.play(Create(guia))
        self.play(Write(f_out), FadeIn(f_val))
        leg = self.legenda("M = 3: a fase dá 3 voltas em 16 clocks ⇒ f_out = 3/16 · f_CLK", leg)
        self.wait(1)

        leg = self.legenda("Mudar M muda a frequência — sem tocar em nenhum circuito analógico", leg, COR_NCO)
        self.play(FadeOut(h3), FadeOut(guia))
        acc.set_value(0)
        M.set_value(1)
        h1 = rodar(16, 0.22)
        guia1 = DashedVMobject(ax.plot(lambda x: np.cos(TAU * x / npos), x_range=[0, 15, 0.02],
                                       color=COR_NCO, stroke_width=2), num_dashes=60)
        self.play(Create(guia1))
        self.wait(0.6)

        res = VGroup(
            tex(r"\Delta f = \frac{f_{CLK}}{2^N}", WHITE, 32),
            tex(r"N = 32,\ f_{CLK} = 50\ \mathrm{MHz} \;\Rightarrow\; \Delta f \approx 0{,}012\ \mathrm{Hz}",
                COR_NCO, 28),
        ).arrange(DOWN, buff=0.25).move_to(P(3.85, -2.4))
        leg = self.legenda("Resolução: o menor passo de frequência é M = 1", leg)
        self.play(FadeOut(VGroup(f_out, f_val)), FadeIn(res, shift=UP * 0.2))
        self.play(Indicate(res[1], color=COR_NCO))
        self.wait(1.5)
        self.limpar()

    def cena_truncacao(self):
        self.titulo_cena("7 · NCO: truncação de fase")
        bits = ValueTracker(3)
        ax = eixos_tempo(P(0, 1.0), 12, 2.4, [0, 2, 0.25], [-1.2, 1.2, 1])
        ax_e = eixos_tempo(P(0, -1.85), 12, 1.4, [0, 2, 0.25], [-0.8, 0.8, 0.4])
        rot_ax = rotulo_eixo(ax, Text("cosseno ideal (branco) × LUT com fase truncada", font_size=20, color=COR_NCO))
        rot_e = rotulo_eixo(ax_e, Text("erro = ideal − truncado", font_size=20, color=COR_ALTA))
        rot_t = Text("fase (voltas) →", font_size=18, color=COR_EIXO).next_to(ax_e, DOWN, buff=0.06
                                                                               ).align_to(ax_e, RIGHT)
        ideal = ax.plot(lambda x: np.cos(TAU * x), x_range=[0, 2, 0.005], color=WHITE, stroke_width=2)

        def niveis():
            return 2 ** int(round(bits.get_value()))

        def escada():
            L = niveis()
            pts = []
            for k in range(2 * L):
                y = np.cos(TAU * k / L)
                pts += [ax.c2p(k / L, y), ax.c2p((k + 1) / L, y)]
            return VMobject().set_points_as_corners(pts).set_stroke(COR_NCO, 4)

        def erro():
            L = niveis()
            pts = []
            for k in range(2 * L):
                xs = np.linspace(k / L, (k + 1) / L, 12)
                ys = np.cos(TAU * xs) - np.cos(TAU * k / L)
                pts += [ax_e.c2p(x, y) for x, y in zip(xs, ys)]
            return VMobject().set_points_as_corners(pts).set_stroke(COR_ALTA, 3)

        leitura = always_redraw(lambda: Text(f"bits de fase na LUT: {int(round(bits.get_value()))}"
                                             f"  ({niveis()} entradas)", font_size=22, color=COR_NCO
                                             ).move_to(P(3.3, 2.85)))

        leg = self.legenda("Uma LUT para 32 bits de fase teria 2³² entradas: memória demais")
        self.play(Create(ax), FadeIn(rot_ax), Create(ideal))
        leg = self.legenda("Solução: usar só os bits mais significativos da fase para ler a LUT", leg, COR_NCO)
        stairs = always_redraw(escada)
        self.play(FadeIn(stairs), FadeIn(leitura))
        leg = self.legenda("A fase truncada gera um erro periódico de amplitude", leg, COR_ALTA)
        self.play(Create(ax_e), FadeIn(rot_e), FadeIn(rot_t))
        err = always_redraw(erro)
        self.play(FadeIn(err))
        leg = self.legenda("Erro periódico ⇒ raias espúrias (phase truncation spurs) ⇒ menor SFDR", leg, COR_ALTA)
        self.play(Indicate(err, color=COR_ALTA))
        leg = self.legenda("Mais bits na LUT: erro menor e espúrios mais baixos (custo: memória)", leg, COR_NCO)
        for b in (4, 5, 6):
            self.play(bits.animate.set_value(b), run_time=1.2)
            self.wait(0.4)
        self.wait(1)
        self.limpar()

    # ================================================================== CENA 8
    def cena_mistura_decimacao(self):
        titulo = self.titulo_cena("8 · Mistura digital e filtragem no espectro")
        ax_f = Axes(x_range=[0, 0.5, 0.1], y_range=[0, 1.25, 0.5], x_length=11, y_length=2.0,
                    axis_config={"include_tip": True, "stroke_width": 2, "color": COR_EIXO},
                    y_axis_config={"include_tip": False}).move_to(P(0, 1.3))
        marcas = marcar_x(ax_f, [0, 0.1, 0.2, 0.3, 0.4, 0.5], ["0", "0,1", "0,2", "0,3", "0,4", "0,5"])
        rot_f = Text("f / f_s", font_size=18, color=COR_EIXO).next_to(ax_f.x_axis.get_end(), UP, buff=0.12)
        f_in, f_nco = 0.21, 0.20
        r_in = raia(ax_f, f_in, 1.0, COR_RF)
        rot_in = tex(r"f_{in}", COR_RF, 28).next_to(ax_f.c2p(f_in, 1.0), UR, buff=0.05)
        lin_nco = DashedLine(ax_f.c2p(f_nco, 0), ax_f.c2p(f_nco, 1.15), color=COR_NCO, stroke_width=3)
        rot_nco = tex(r"f_{NCO}", COR_NCO, 28).next_to(ax_f.c2p(f_nco, 1.15), UL, buff=0.05)
        r_dif = raia(ax_f, f_in - f_nco, 0.5, COR_I)
        r_soma = raia(ax_f, f_in + f_nco, 0.5, COR_ALTA)
        rot_dif = tex(r"f_{in} - f_{NCO} \approx 0", COR_I, 26).next_to(ax_f.c2p(0.06, 0.5), RIGHT, buff=0.15)
        rot_soma = tex(r"f_{in} + f_{NCO}", COR_ALTA, 26).next_to(ax_f.c2p(f_in + f_nco, 0.5), UP, buff=0.1)
        mascara = Polygon(ax_f.c2p(0, 0), ax_f.c2p(0, 1.15), ax_f.c2p(0.06, 1.15), ax_f.c2p(0.06, 0),
                          color=COR_FILTRO, stroke_width=3, fill_color=COR_FILTRO, fill_opacity=0.15)
        rot_lpf = Text("LPF", font_size=20, color=COR_FILTRO).next_to(ax_f.c2p(0.06, 1.15), RIGHT, buff=0.1)

        leg = self.legenda("Entrada: uma componente em f_in; o NCO oscila em f_NCO ≈ f_in")
        self.play(Create(ax_f), FadeIn(marcas), FadeIn(rot_f))
        self.play(GrowArrow(r_in), FadeIn(rot_in))
        self.play(Create(lin_nco), FadeIn(rot_nco))
        leg = self.legenda("O produto x[n]·cos[n] gera a diferença e a soma das frequências", leg)
        self.play(ReplacementTransform(r_in, VGroup(r_dif, r_soma)), FadeOut(rot_in), run_time=2)
        self.play(FadeIn(rot_dif), FadeIn(rot_soma))
        leg = self.legenda("A diferença cai em banda base; a soma fica perto de 2f e precisa sair", leg)
        self.wait(0.8)
        leg = self.legenda("O LPF deixa passar só a banda base", leg, COR_FILTRO)
        self.play(FadeIn(mascara), FadeIn(rot_lpf))
        xis = Cross(VGroup(r_soma, rot_soma), stroke_color=COR_ALTA, stroke_width=5, scale_factor=0.8)
        self.play(Create(xis))
        self.play(FadeOut(r_soma), FadeOut(rot_soma), FadeOut(xis))
        self.wait(0.6)

        # Decimação e aliasing (domínio do tempo)
        self.trocar_titulo(titulo, "8 · Decimação: por que filtrar antes do ↓R")
        ax_t = eixos_tempo(P(0, -1.65), 11.5, 1.9, [0, 32, 4], [-1.2, 1.2, 1])
        rot_n = Text("n →", font_size=18, color=COR_EIXO).next_to(ax_t, DOWN, buff=0.05).align_to(ax_t, RIGHT)
        R = 4
        f_rapida = 0.4
        rapida = ax_t.plot(lambda x: np.cos(TAU * f_rapida * x), x_range=[0, 31, 0.02],
                           color=COR_ALTA, stroke_width=1.5).set_stroke(opacity=0.5)
        h_rapida = VGroup(*[haste(ax_t, n, np.cos(TAU * f_rapida * n), COR_ALTA, 0.05) for n in range(32)])
        rot_t = rotulo_eixo(ax_t, Text("sem filtro: sobrou a componente rápida (soma)", font_size=20,
                                       color=COR_ALTA))

        leg = self.legenda("Suponha que a componente rápida NÃO tenha sido filtrada", leg, COR_ALTA)
        self.play(Create(ax_t), FadeIn(rot_n), FadeIn(rot_t))
        self.play(Create(rapida), LaggedStart(*[GrowFromPoint(h, ax_t.c2p(n, 0)) for n, h in enumerate(h_rapida)],
                                               lag_ratio=0.05), run_time=2)
        leg = self.legenda(f"Decimação ↓{R}: guardamos 1 amostra a cada {R}", leg, COR_FILTRO)
        descartadas = VGroup(*[h for n, h in enumerate(h_rapida) if n % R])
        guardadas = VGroup(*[h for n, h in enumerate(h_rapida) if n % R == 0])
        self.play(descartadas.animate.set_opacity(0.12), guardadas.animate.set_color(WHITE), run_time=1.5)
        alias = DashedVMobject(ax_t.plot(lambda x: np.cos(TAU * 0.1 * x), x_range=[0, 31, 0.02],
                                         color=WHITE, stroke_width=4), num_dashes=50)
        leg = self.legenda("As amostras restantes descrevem uma senoide LENTA que não existia: aliasing", leg, COR_ALTA)
        self.play(Create(alias), run_time=2)
        self.play(Indicate(guardadas, color=COR_ALTA))
        self.wait(0.8)

        lenta = lambda x: 0.85 * np.cos(TAU * 0.03 * x + 0.4)
        curva_lenta = ax_t.plot(lenta, x_range=[0, 31, 0.02], color=COR_I, stroke_width=4)
        h_lenta = VGroup(*[haste(ax_t, n, lenta(n), COR_I, 0.05) for n in range(32)])
        rot_t2 = rotulo_eixo(ax_t, Text("com LPF antes: só a banda base", font_size=20, color=COR_I))
        leg = self.legenda("Com o LPF antes do ↓R, só a banda base chega à decimação", leg, COR_I)
        self.play(FadeOut(VGroup(rapida, h_rapida, alias)), Transform(rot_t, rot_t2))
        self.play(Create(curva_lenta), LaggedStart(*[GrowFromPoint(h, ax_t.c2p(n, 0)) for n, h in enumerate(h_lenta)],
                                                   lag_ratio=0.05), run_time=2)
        self.play(VGroup(*[h for n, h in enumerate(h_lenta) if n % R]).animate.set_opacity(0.12), run_time=1.2)
        leg = self.legenda(f"As amostras guardadas seguem a curva certa, com {R}× menos dados", leg, COR_I)
        self.play(Indicate(curva_lenta, color=COR_I, scale_factor=1.03))
        self.wait(1.5)
        self.limpar()

    # ================================================================== CENA 9
    def cena_cic_estrutura(self):
        titulo = self.titulo_cena("9 · Filtro CIC (Cascaded Integrator–Comb)")
        y0 = 1.6
        integ = VGroup(*[bloco_tex(r"\frac{1}{1 - z^{-1}}", 1.35, 1.05, COR_RF, 30) for _ in range(3)])
        for k, b in enumerate(integ):
            b.move_to(P(-5.1 + 1.55 * k, y0))
        dec = bloco_tex(r"\downarrow R", 0.9, 1.05, COR_FILTRO, 34).move_to(P(-0.45, y0))
        combs = VGroup(*[bloco_tex(r"1 - z^{-D}", 1.35, 1.05, COR_I, 30) for _ in range(3)])
        for k, b in enumerate(combs):
            b.move_to(P(1.1 + 1.55 * k, y0))
        x_in = tex(r"x[n]", WHITE, 30).move_to(P(-6.55, y0))
        y_out = tex(r"y[m]", WHITE, 30).move_to(P(5.6, y0))
        cadeia = [x_in, *integ, dec, *combs, y_out]
        fios = VGroup(*[fio([a.get_right() + RIGHT * 0.03, b.get_left() + LEFT * 0.03], GREY_B, 3)
                        for a, b in zip(cadeia[:-1], cadeia[1:])])
        ch_int = Brace(integ, DOWN, color=COR_RF)
        ch_comb = Brace(combs, DOWN, color=COR_I)
        t_int = VGroup(Text("M integradores · taxa f_in", font_size=20, color=COR_RF),
                       tex(r"y[n] = y[n-1] + x[n]", COR_RF, 28)).arrange(DOWN, buff=0.15).next_to(ch_int, DOWN, buff=0.1)
        t_comb = VGroup(Text("M pentes (comb) · taxa f_in / R", font_size=20, color=COR_I),
                        tex(r"y[m] = x[m] - x[m-D]", COR_I, 28)).arrange(DOWN, buff=0.15).next_to(ch_comb, DOWN, buff=0.1)
        destaque = Text("Só somas, subtrações e atrasos: nenhum multiplicador", font_size=26,
                        color=COR_NCO, weight=BOLD).move_to(P(0, -1.2))
        motivo = Text("Ideal para decimação grande (R > 32), onde um FIR exigiria centenas de coeficientes",
                      font_size=20, color=GREY_A).next_to(destaque, DOWN, buff=0.2)

        leg = self.legenda("Integradores na taxa alta, decimação, depois pentes na taxa baixa")
        self.play(FadeIn(x_in), LaggedStart(*[FadeIn(b) for b in integ], lag_ratio=0.3),
                  Create(VGroup(*fios[:3])), run_time=1.6)
        self.play(GrowFromCenter(ch_int), FadeIn(t_int))
        self.play(FadeIn(dec), Create(fios[3]))
        self.play(LaggedStart(*[FadeIn(b) for b in combs], lag_ratio=0.3), Create(VGroup(*fios[4:])),
                  FadeIn(y_out), run_time=1.6)
        self.play(GrowFromCenter(ch_comb), FadeIn(t_comb))
        p = caminho([x_in.get_right(), y_out.get_left()])
        self.play(ShowPassingFlash(p.set_stroke(WHITE, 7), time_width=0.4), run_time=1.5)
        leg = self.legenda("A grande vantagem: hardware barato e rápido na FPGA", leg, COR_NCO)
        self.play(Write(destaque), run_time=1.5)
        self.play(FadeIn(motivo, shift=UP * 0.1))
        self.wait(1.5)
        self.play(FadeOut(VGroup(*integ, dec, *combs, x_in, y_out, fios, ch_int, ch_comb, t_int, t_comb,
                                 destaque, motivo)), FadeOut(leg))

        # Equivalência com média móvel (box-car)
        self.trocar_titulo(titulo, "9 · CIC de 1ª ordem = média móvel")
        K = 8   # R·D
        rng = np.random.default_rng(7)
        nmax = 40
        xs = 0.6 + 0.3 * np.sin(TAU * np.arange(nmax) / 40) + 0.22 * rng.standard_normal(nmax)
        ys = np.array([xs[max(0, n - K + 1):n + 1].mean() for n in range(nmax)])
        ax_x = eixos_tempo(P(0, 0.75), 12, 1.9, [0, 40, 5], [-0.2, 1.4, 0.5])
        ax_y = eixos_tempo(P(0, -1.95), 12, 1.9, [0, 40, 5], [-0.2, 1.4, 0.5])
        rot_x = rotulo_eixo(ax_x, Text("entrada x[n] (ruidosa)", font_size=20, color=COR_RF))
        rot_y = rotulo_eixo(ax_y, Text("saída: soma das últimas R·D amostras (normalizada)", font_size=20,
                                       color=WHITE))
        formula = tex(r"y[n] = \sum_{k=0}^{RD-1} x[n-k]", WHITE, 32).move_to(P(4.3, 2.75))
        h_x = VGroup(*[haste(ax_x, n, xs[n], COR_RF, 0.045) for n in range(nmax)])
        pos = ValueTracker(K - 1)

        janela = always_redraw(lambda: Rectangle(
            width=ax_x.c2p(K, 0)[0] - ax_x.c2p(0, 0)[0], height=1.95,
            color=COR_NCO, stroke_width=2, fill_color=COR_NCO, fill_opacity=0.18
        ).move_to(P((ax_x.c2p(pos.get_value() - K + 0.5, 0)[0] + ax_x.c2p(pos.get_value() + 0.5, 0)[0]) / 2,
                    ax_x.get_center()[1])))
        saidas = always_redraw(lambda: VGroup(*[haste(ax_y, n, ys[n], WHITE, 0.045)
                                                for n in range(K - 1, int(pos.get_value()) + 1)]))
        guia = ax_y.plot(lambda x: 0.6 + 0.3 * np.sin(TAU * (x - (K - 1) / 2) / 40), x_range=[K - 1, 39, 0.05],
                         color=COR_I, stroke_width=3)

        leg = self.legenda("Integrador seguido de pente = soma das últimas R·D amostras (box-car)")
        self.play(Create(ax_x), FadeIn(rot_x), Write(formula))
        self.play(LaggedStart(*[GrowFromPoint(h, ax_x.c2p(n, 0)) for n, h in enumerate(h_x)], lag_ratio=0.03),
                  run_time=1.5)
        self.play(Create(ax_y), FadeIn(rot_y))
        self.play(FadeIn(janela))
        self.add(saidas)
        leg = self.legenda(f"A janela de {K} amostras desliza: cada saída é a média do que está dentro", leg, COR_NCO)
        self.play(pos.animate.set_value(nmax - 1), run_time=7, rate_func=linear)
        leg = self.legenda("O ruído rápido é atenuado: a média móvel é um filtro passa-baixa", leg, COR_I)
        self.play(Create(guia))
        self.wait(1.5)
        self.limpar()

    def cena_cic_frequencia(self):
        self.titulo_cena("9 · CIC: resposta em frequência")
        R, D = 16, 1
        Mv = ValueTracker(1)
        ax = Axes(x_range=[0, 4, 0.5], y_range=[0, 1.1, 0.25], x_length=8.6, y_length=3.6,
                  axis_config=EIXO_CFG).move_to(P(-2.0, -0.55))
        marcas = marcar_x(ax, [0, 1, 2, 3, 4], ["0", "f_out", "2·f_out", "3·f_out", "4·f_out"])
        rot_y = Text("|H(f)| / ganho DC", font_size=18, color=COR_EIXO).next_to(
            ax.y_axis.get_end(), UP, buff=0.12).align_to(ax.y_axis, LEFT)
        formula = tex(r"|H(f)| = \left|\frac{\sin(\pi D f / f_{out})}{\sin(\pi f / (R f_{out}))}\right|^{M}",
                      WHITE, 30).move_to(P(3.6, 2.6))

        def m():
            return int(round(Mv.get_value()))

        curva = always_redraw(lambda: ax.plot(lambda f: cic_resposta(f, m(), R, D), x_range=[0, 4, 0.004],
                                              color=COR_NCO, stroke_width=4))
        painel = always_redraw(lambda: VGroup(
            Text(f"R = {R},  D = {D},  M = {m()}", font_size=22, color=COR_NCO),
            Text(f"ganho DC = (R·D)^M = {(R * D) ** m()}", font_size=20, color=WHITE),
            Text(f"bits extras = M·log₂(RD) = {m() * int(np.log2(R * D))}", font_size=20, color=COR_ERRO2),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(P(4.8, 0.3)).align_to(P(2.9, 0), LEFT))

        leg = self.legenda("Resposta tipo sinc: passa-baixa com zeros em múltiplos de f_out")
        self.play(Create(ax), FadeIn(marcas), FadeIn(rot_y), Write(formula))
        self.play(Create(curva), FadeIn(painel), run_time=2)
        zeros = VGroup(*[Dot(ax.c2p(k, 0), radius=0.08, color=COR_ALTA) for k in (1, 2, 3, 4)])
        leg = self.legenda("Nos zeros caem justamente as faixas que dobrariam sobre a banda ao decimar", leg, COR_ALTA)
        self.play(LaggedStart(*[GrowFromCenter(z) for z in zeros], lag_ratio=0.2))
        leg = self.legenda("Mais estágios (M): rejeição maior fora da banda", leg, COR_NCO)
        for k in (2, 3, 4):
            self.play(Mv.animate.set_value(k), run_time=1.2)
            self.wait(0.5)

        regiao = Rectangle(width=ax.c2p(0.35, 0)[0] - ax.c2p(0, 0)[0], height=3.6, stroke_width=0,
                           fill_color=COR_I, fill_opacity=0.15)
        regiao.move_to(P((ax.c2p(0, 0)[0] + ax.c2p(0.35, 0)[0]) / 2, ax.get_center()[1]))
        ponto = Dot(ax.c2p(0.35, cic_resposta(0.35, 4, R, D)), radius=0.08, color=COR_ALTA)
        rot_droop = Text("queda na banda\n(passband droop)", font_size=18, color=COR_ALTA
                         ).next_to(ponto, RIGHT, buff=0.25)
        leg = self.legenda("Custo: a própria banda útil é atenuada nas bordas", leg, COR_ALTA)
        self.play(FadeIn(regiao), GrowFromCenter(ponto), FadeIn(rot_droop))
        plano_comp = ax.plot(lambda f: 1.0, x_range=[0, 0.35], color=WHITE, stroke_width=5)
        rot_comp = Text("CIC + FIR de compensação", font_size=18, color=WHITE
                        ).next_to(ax.c2p(0.35, 1.0), RIGHT, buff=0.3)
        leg = self.legenda("Um FIR curto de compensação, após o CIC, aplaina a banda útil", leg)
        self.play(Create(plano_comp), FadeIn(rot_comp))
        leg = self.legenda("E o ganho (R·D)^M exige registradores mais largos para não transbordar", leg, COR_ERRO2)
        painel.clear_updaters()
        self.play(Indicate(painel[1:], color=COR_ERRO2))
        self.wait(1.5)
        self.limpar()

    # ================================================================= CENA 10
    def cena_comparacao(self):
        self.titulo_cena("10 · DDC × IQ sampling clássico")
        xs = [-4.55, -0.55, 4.0]
        cab = VGroup(
            Text("Característica", font_size=22, color=GREY_A, weight=BOLD),
            Text("IQ sampling (f_s = 4·f_IF)", font_size=22, color=COR_ERRO2, weight=BOLD),
            Text("Digital Down Conversion", font_size=22, color=COR_NCO, weight=BOLD),
        )
        for t, x in zip(cab, xs):
            t.move_to(P(x, 2.35))
        linhas_txt = [
            ("Latência /\natraso de grupo", "Mínima\n(cálculo quase instantâneo)", "Elevada\n(taps dos filtros CIC/FIR)"),
            ("Flexibilidade\nde frequência", "Rígida\n(f_s travado em 4·f_IF)", "Total\n(o NCO segue qualquer frequência)"),
            ("Relação\nsinal-ruído", "Mais sensível a\nruído e espúrios", "Excelente (ganho de processamento\ne decimação reduzem o ruído)"),
            ("Aplicação\nprincipal", "Malhas rápidas de\nrealimentação da cavidade", "Diagnóstico de feixe (BPM),\nmonitoração e malhas lentas"),
        ]
        ys = [1.25, 0.0, -1.25, -2.5]
        sep = VGroup(*[Line(P(-6.6, y + 0.62), P(6.6, y + 0.62), color=COR_EIXO, stroke_width=1.5)
                       for y in ys])
        self.play(LaggedStart(*[FadeIn(t, shift=DOWN * 0.1) for t in cab], lag_ratio=0.2))
        leg = self.legenda("Os dois métodos resolvem o mesmo problema com compromissos opostos")
        cores = [GREY_A, COR_ERRO2, COR_NCO]
        for (a, b, c), y, s in zip(linhas_txt, ys, sep):
            linha = VGroup(*[Text(t, font_size=19, color=cor, line_spacing=1.1).move_to(P(x, y))
                             for t, cor, x in zip((a, b, c), cores, xs)])
            self.play(Create(s), FadeIn(linha, shift=UP * 0.1), run_time=0.9)
            self.wait(0.8)
        leg = self.legenda("Malha rápida: IQ sampling. Precisão e flexibilidade: DDC.", leg, WHITE)
        self.wait(2)
        self.limpar()

    # ================================================================== RESUMO
    def cena_resumo(self):
        self.titulo_cena("Resumo")
        blocos = [bloco("ADC", 1.1, 0.7, WHITE, 22), bloco("× NCO", 1.3, 0.7, COR_NCO, 22),
                  bloco("CIC / FIR", 1.6, 0.7, COR_FILTRO, 22), bloco_tex(r"\downarrow R", 1.0, 0.7, COR_FILTRO, 30),
                  tex(r"I[m],\ Q[m]", WHITE, 32), tex(r"A,\ \phi", COR_RF, 34)]
        linha = VGroup(*blocos).arrange(RIGHT, buff=0.75).move_to(P(0, 1.9))
        fios = VGroup(*[fio([a.get_right() + RIGHT * 0.05, b.get_left() + LEFT * 0.05], GREY_B, 3)
                        for a, b in zip(blocos[:-1], blocos[1:])])
        itens = VGroup(*[Text(t, font_size=22, color=c) for t, c in [
            ("• I e Q: amplitude e fase reescritas como duas ondas ortogonais", WHITE),
            ("• Demodular = multiplicar pelo LO e filtrar: os termos em 2ωc somem", COR_I),
            ("• Erro de fase no LO faz Q vazar para I: no digital a quadratura é exata", COR_ALTA),
            ("• DDC: translada para 0 Hz, filtra e decima: R× menos dados", COR_FILTRO),
            ("• NCO e CIC: frequência programável e filtragem sem multiplicadores", COR_NCO),
        ]]).arrange(DOWN, aligned_edge=LEFT, buff=0.28).move_to(P(0, -1.0))

        self.play(LaggedStart(*[FadeIn(b) for b in blocos], lag_ratio=0.2), Create(fios), run_time=2)
        p = caminho([blocos[0].get_left(), blocos[-1].get_right()])
        self.play(ShowPassingFlash(p.set_stroke(WHITE, 7), time_width=0.4), run_time=1.5)
        self.play(LaggedStart(*[FadeIn(t, shift=RIGHT * 0.2) for t in itens], lag_ratio=0.35), run_time=3.5)
        self.wait(3)
        self.limpar()
