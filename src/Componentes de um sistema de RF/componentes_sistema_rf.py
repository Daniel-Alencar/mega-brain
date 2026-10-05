# -*- coding: utf-8 -*-
"""
Componentes de um sistema de RF: a malha LLRF, da FPGA à cavidade e de volta
============================================================================

Renderização (a partir da raiz do repositório):
    manim -pql "src/Componentes de um sistema de RF/componentes_sistema_rf.py" ComponentesSistemaRF   # rascunho
    manim -pqh "src/Componentes de um sistema de RF/componentes_sistema_rf.py" ComponentesSistemaRF   # final

Requer LaTeX (MathTex).

Roteiro (segue "docs/Componentes de um sistema de RF"):
    Abertura
    Cena 1  - A malha completa: LLRF, conversores, mixers, filtros, amplificação, fontes e linhas
    Cena 2  - LLRF: o PI mantém o campo dentro de 0,1 % e 0,1°
    Cena 3  - Conversores: ADC (14 bits, 125 MSps) e DAC (16 bits, 250 MSps)
    Cena 4  - Matemática do down-conversion: 500 MHz × 480 MHz → 20 MHz + 980 MHz
    Cena 5  - Por que 20 MHz: jitter, 5 amostras por período, offset DC e ruído 1/f
    Cena 6  - Matemática do up-conversion: 20 MHz × 480 MHz → 500 MHz + 460 MHz
    Cena 7  - Por que 500 MHz: ressonância da cavidade e sincronismo com o feixe
    Cena 8  - Onde ficam a desmodulação e a modulação IQ: dentro da FPGA
    Cena 9  - Cadeia de potência: pré-amplificador, SSAMP, fontes e linhas
    Cena 10 - Largura de banda do controle × ripple das fontes
    Resumo
"""

import numpy as np
from manim import *

# Paleta didática (fixa em todas as cenas)
COR_RF = BLUE            # sinal de RF (500 MHz)
COR_IF = GOLD            # sinal de IF (20 MHz)
COR_LO = GREY_A          # oscilador local
COR_ESPURIO = RED        # produtos indesejados, ruído, erro
COR_DIGITAL = TEAL       # FPGA / domínio digital
COR_FILTRO = PINK
COR_POTENCIA = ORANGE    # amplificação e fontes
COR_CAV = "#c87533"      # cavidade (cobre)
COR_I = GOLD
COR_Q = GREEN
COR_OK = GREEN
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
    """Fórmula multicolorida. partes = [(tex, cor), ...]."""
    m = MathTex(*[p[0] for p in partes], font_size=tamanho)
    for sub, p in zip(m, partes):
        sub.set_color(p[1])
    return m


def seta(a, b, cor, largura=6):
    if np.linalg.norm(b - a) < 1e-3:
        return VMobject()
    return Arrow(a, b, buff=0, color=cor, stroke_width=largura,
                 max_tip_length_to_length_ratio=0.18, max_stroke_width_to_length_ratio=12)


def fio(pontos, cor=WHITE, largura=3, com_seta=True):
    g = VGroup(*[Line(pontos[k], pontos[k + 1], color=cor, stroke_width=largura)
                 for k in range(len(pontos) - (2 if com_seta else 1))])
    if com_seta:
        g.add(Arrow(pontos[-2], pontos[-1], buff=0, color=cor, stroke_width=largura,
                    max_tip_length_to_length_ratio=0.25, max_stroke_width_to_length_ratio=10))
    return g


def caminho(pontos):
    return VMobject().set_points_as_corners(pontos)


def eixos_tempo(centro, largura, altura, x_range, y_range):
    return Axes(x_range=x_range, y_range=y_range, x_length=largura, y_length=altura,
                axis_config=EIXO_CFG).move_to(centro)


def rotulo_eixo(ax, mob):
    """Coloca um rótulo acima do canto esquerdo de um eixo."""
    return mob.next_to(ax, UP, buff=0.04).align_to(ax, LEFT)


def marcar_x(ax, valores, rotulos, tamanho=16):
    return VGroup(*[Text(r, font_size=tamanho, color=COR_EIXO).next_to(ax.c2p(v, 0), DOWN, buff=0.1)
                    for v, r in zip(valores, rotulos)])


def haste(ax, x, y, cor, raio=0.06, largura=2):
    return VGroup(Line(ax.c2p(x, 0), ax.c2p(x, y), color=cor, stroke_width=largura),
                  Dot(ax.c2p(x, y), radius=raio, color=cor))


def raia(ax, f, altura, cor, largura=6):
    return seta(ax.c2p(f, 0), ax.c2p(f, altura), cor, largura)


# ------------------------------------------------------------ blocos do diagrama
def caixa(rotulo, largura=1.2, altura=0.7, cor=WHITE, tamanho=20):
    r = RoundedRectangle(corner_radius=0.08, width=largura, height=altura, color=cor, stroke_width=3)
    return VGroup(r, Text(rotulo, font_size=tamanho, color=cor).move_to(r))


def conversor(rotulo, cor=WHITE, invertido=False):
    """Trapézio do ADC/DAC (lado largo = lado analógico)."""
    a, b = 0.42, 0.26
    pts = [P(-0.38, a), P(0.38, b), P(0.38, -b), P(-0.38, -a)] if not invertido else \
          [P(-0.38, b), P(0.38, a), P(0.38, -a), P(-0.38, -b)]
    return VGroup(Polygon(*pts, color=cor, stroke_width=3), Text(rotulo, font_size=18, color=cor))


def mixer(cor=WHITE, raio=0.3):
    c = Circle(radius=raio, color=cor, stroke_width=3)
    d = raio * 0.7
    return VGroup(c, VGroup(Line(P(-d, d), P(d, -d)), Line(P(-d, -d), P(d, d))).set_stroke(cor, 3))


def filtro_icone(tipo, cor=COR_FILTRO):
    q = Square(side_length=0.75, color=cor, stroke_width=3)
    if tipo == "bp":
        pts = [P(-0.28, -0.2), P(-0.12, -0.2), P(-0.05, 0.15), P(0.05, 0.15), P(0.12, -0.2), P(0.28, -0.2)]
    else:
        pts = [P(-0.28, 0.15), P(0.0, 0.15), P(0.1, -0.2), P(0.28, -0.2)]
    return VGroup(q, VMobject().set_points_as_corners(pts).set_stroke(cor, 2.5))


def amplificador(cor=COR_POTENCIA):
    return Triangle(color=cor, stroke_width=3).rotate(-PI / 2).scale(0.42)


def atenuador(cor=GREY_A):
    r = Rectangle(width=1.0, height=0.5, color=cor, stroke_width=3)
    pts = [P(-0.35, 0)] + [P(-0.35 + 0.1 * (k + 0.5), 0.1 if k % 2 == 0 else -0.1) for k in range(7)] + [P(0.35, 0)]
    return VGroup(r, VMobject().set_points_as_corners(pts).set_stroke(cor, 2.5))


def tag(numero, cor=YELLOW):
    c = Circle(radius=0.17, color=cor, stroke_width=2, fill_color=FUNDO, fill_opacity=1)
    return VGroup(c, Text(str(numero), font_size=16, color=cor, weight=BOLD).move_to(c))


# =============================================================================
# Cena
# =============================================================================
class ComponentesSistemaRF(Scene):
    def construct(self):
        self.camera.background_color = FUNDO
        self.abertura()
        self.cena_malha()
        self.cena_llrf()
        self.cena_conversores()
        self.cena_down()
        self.cena_jitter()
        self.cena_sincronismo()
        self.cena_ruido_dc()
        self.cena_up()
        self.cena_por_que_500()
        self.cena_iq_fpga()
        self.cena_potencia()
        self.cena_ripple()
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
            self.play(FadeOut(anterior, shift=UP * 0.2), FadeIn(nova, shift=UP * 0.2), run_time=0.7)
        return nova

    def limpar(self):
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
        self.wait(0.2)

    def espectro(self, centro, fmax, largura=12.0, altura=1.9, passo=100, rotulo="f (MHz)"):
        ax = Axes(x_range=[0, fmax, passo], y_range=[0, 1.25, 0.5], x_length=largura, y_length=altura,
                  axis_config={"include_tip": True, "stroke_width": 2, "color": COR_EIXO},
                  y_axis_config={"include_tip": False}).move_to(centro)
        vals = list(range(0, int(fmax) + 1, passo))
        marcas = marcar_x(ax, vals, [str(v) for v in vals])
        nome = Text(rotulo, font_size=16, color=COR_EIXO).next_to(ax.x_axis.get_end(), UP, buff=0.1)
        return ax, VGroup(marcas, nome)

    # ---------------------------------------------------------------- abertura
    def abertura(self):
        titulo = Text("Componentes de um sistema de RF", font_size=52, weight=BOLD)
        sub = Text("A malha LLRF: da FPGA até a cavidade e de volta", font_size=30, color=GREY_A)
        cadeia = Text("FPGA → DAC → mixer → filtro → amplificador → cavidade → mixer → filtro → ADC → FPGA",
                      font_size=20, color=COR_DIGITAL)
        g = VGroup(titulo, sub, cadeia).arrange(DOWN, buff=0.35)
        self.play(Write(titulo), run_time=1.5)
        self.play(FadeIn(sub, shift=UP * 0.2), FadeIn(cadeia, shift=UP * 0.2))
        self.wait(1.2)
        self.play(FadeOut(g))

    # ================================================================== CENA 1
    def cena_malha(self):
        self.titulo_cena("1 · A malha de RF completa")
        yt, yb = 1.45, -1.55
        fpga = VGroup(RoundedRectangle(corner_radius=0.15, width=1.5, height=3.8, color=COR_DIGITAL, stroke_width=4),
                      Text("LLRF\n(FPGA)", font_size=22, color=COR_DIGITAL, weight=BOLD)).move_to(P(-6.0, -0.05))
        dac = conversor("DAC").move_to(P(-4.35, yt))
        mx_up = mixer().move_to(P(-2.95, yt))
        lo_up = VGroup(Arrow(P(-2.95, yt + 0.95), P(-2.95, yt + 0.3), buff=0, color=COR_LO, stroke_width=3,
                             max_tip_length_to_length_ratio=0.3), Text("LO", font_size=16, color=COR_LO)
                       .move_to(P(-2.95, yt + 1.08)))
        bpf = filtro_icone("bp").move_to(P(-1.55, yt))
        amp = amplificador().move_to(P(0.05, yt))
        fonte_dc = caixa("Fontes DC", 1.3, 0.5, COR_POTENCIA, 16).move_to(P(0.05, yt + 1.1))
        w_fonte = DashedLine(fonte_dc.get_bottom(), amp.get_top(), color=COR_POTENCIA, stroke_width=2)
        linha_tx = caixa("Linhas de\ntransmissão", 1.5, 0.75, GREY_A, 15).move_to(P(1.85, yt))
        cav = VGroup(Ellipse(width=1.5, height=0.85, color=COR_CAV, stroke_width=4),
                     Text("Cavidade", font_size=16, color=COR_CAV)).move_to(P(4.3, -0.05))
        aten = atenuador().move_to(P(2.6, yb))
        r_aten = Text("Atenuadores", font_size=15, color=GREY_A).next_to(aten, UP, buff=0.08)
        mx_dn = mixer().move_to(P(1.05, yb))
        lo_dn = VGroup(Arrow(P(1.05, yb - 0.95), P(1.05, yb - 0.3), buff=0, color=COR_LO, stroke_width=3,
                             max_tip_length_to_length_ratio=0.3), Text("LO", font_size=16, color=COR_LO)
                       .move_to(P(1.05, yb - 1.08)))
        lpf = filtro_icone("lp").move_to(P(-0.55, yb))
        adc = conversor("ADC", invertido=True).move_to(P(-2.3, yb))

        fios = VGroup(
            fio([P(-5.25, yt), dac.get_left()], WHITE),
            fio([dac.get_right(), mx_up.get_left()], COR_IF),
            fio([mx_up.get_right(), bpf.get_left()], COR_RF),
            fio([bpf.get_right(), amp.get_left()], COR_RF),
            fio([amp.get_right(), linha_tx.get_left()], COR_RF, 6),
            fio([linha_tx.get_right(), P(4.3, yt), cav.get_top()], COR_RF, 6),
            fio([cav.get_bottom(), P(4.3, yb), aten.get_right()], COR_RF),
            fio([aten.get_left(), mx_dn.get_right()], COR_RF),
            fio([mx_dn.get_left(), lpf.get_right()], COR_IF),
            fio([lpf.get_left(), adc.get_right()], COR_IF),
            fio([adc.get_left(), P(-5.25, yb)], WHITE),
        )
        sinais = VGroup(
            tex(r"V_{act}", WHITE, 22).next_to(P(-5.0, yt), UP, buff=0.08),
            Text("IF", font_size=16, color=COR_IF).next_to(P(-3.65, yt), UP, buff=0.08),
            Text("RF", font_size=16, color=COR_RF).next_to(P(-0.8, yt), UP, buff=0.08),
            Text("IF", font_size=16, color=COR_IF).next_to(P(0.25, yb), DOWN, buff=0.08),
            tex(r"V_{cav}", WHITE, 22).next_to(P(-4.0, yb), DOWN, buff=0.08),
        )
        blocos = {"llrf": fpga, "conv": VGroup(dac, adc), "mix": VGroup(mx_up, mx_dn, lo_up, lo_dn),
                  "filt": VGroup(bpf, lpf), "amp": amp, "fonte": VGroup(fonte_dc, w_fonte),
                  "linhas": VGroup(linha_tx, aten, r_aten)}
        tags = VGroup(
            tag(1).next_to(fpga, UP, buff=0.1),
            tag(2).next_to(dac, UP, buff=0.1), tag(2).next_to(adc, UP, buff=0.1),
            tag(3).next_to(mx_up, DL, buff=0.02), tag(3).next_to(mx_dn, UL, buff=0.02),
            tag(4).next_to(bpf, UP, buff=0.1), tag(4).next_to(lpf, UP, buff=0.1),
            tag(5).next_to(amp, DOWN, buff=0.1),
            tag(6).next_to(fonte_dc, LEFT, buff=0.1),
            tag(7).next_to(linha_tx, DOWN, buff=0.1),
        )
        infos = [
            ("llrf", "1 · LLRF: controle em malha fechada do sinal fraco (mW),\nPI digital em I e Q dentro de uma FPGA", COR_DIGITAL),
            ("conv", "2 · Conversores: o ADC digitaliza a IF que volta da cavidade;\no DAC gera a IF de comando", WHITE),
            ("mix", "3 · Mixers: transladam o espectro\n(500 MHz ↔ 20 MHz) usando o LO", COR_LO),
            ("filt", "4 · Filtros: removem a frequência imagem\nque todo mixer gera", COR_FILTRO),
            ("amp", "5 · Amplificação: de mW até dezenas ou\ncentenas de kW", COR_POTENCIA),
            ("fonte", "6 · Fontes DC: alimentam os transistores;\nseu ripple modula a amplitude da RF", COR_POTENCIA),
            ("linhas", "7 · Linhas: coaxiais de 50 Ω (baixa potência)\ne guias de onda (alta potência)", GREY_A),
        ]

        leg = self.legenda("Uma malha fechada: a FPGA comanda a cavidade e mede o que acontece nela")
        self.play(FadeIn(fpga), FadeIn(cav))
        self.play(LaggedStart(*[FadeIn(m) for m in (dac, mx_up, lo_up, bpf, amp, linha_tx)], lag_ratio=0.15),
                  run_time=1.5)
        self.play(LaggedStart(*[FadeIn(m) for m in (aten, r_aten, mx_dn, lo_dn, lpf, adc)], lag_ratio=0.15),
                  run_time=1.5)
        self.play(FadeIn(fonte_dc), Create(w_fonte))
        self.play(LaggedStart(*[Create(f) for f in fios], lag_ratio=0.1), FadeIn(sinais), run_time=2.5)
        laco = caminho([P(-5.25, yt), dac.get_center(), mx_up.get_center(), bpf.get_center(), amp.get_center(),
                        linha_tx.get_center(), P(4.3, yt), cav.get_center(), P(4.3, yb), aten.get_center(),
                        mx_dn.get_center(), lpf.get_center(), adc.get_center(), P(-5.25, yb)])
        self.play(ShowPassingFlash(laco.copy().set_stroke(WHITE, 8), time_width=0.3), run_time=3)
        self.play(FadeIn(tags))

        info = None
        for chave, texto, cor in infos:
            novo = Text(texto, font_size=19, color=cor, line_spacing=1.15).move_to(P(-0.75, -0.05))
            leg = self.legenda(texto.split(":")[0], leg, cor)
            anims = [Indicate(blocos[chave], color=YELLOW, scale_factor=1.15)]
            anims.append(FadeIn(novo) if info is None else ReplacementTransform(info, novo))
            self.play(*anims, run_time=1.0)
            info = novo
            self.wait(1.6)
        leg = self.legenda("A seguir, cada parte em detalhe", leg)
        self.play(ShowPassingFlash(laco.copy().set_stroke(YELLOW, 8), time_width=0.3), run_time=3)
        self.limpar()

    # ================================================================== CENA 2
    def cena_llrf(self):
        self.titulo_cena("2 · LLRF: controle em malha fechada")
        eixos = Axes(x_range=[-0.2, 1.3, 0.5], y_range=[-0.2, 1.1, 0.5], x_length=5.4, y_length=4.7,
                     axis_config={"include_tip": True, "stroke_width": 2, "color": COR_EIXO}).move_to(P(-3.4, -0.45))
        r_i = Text("I", font_size=28, color=COR_I).next_to(eixos.x_axis.get_end(), DOWN, buff=0.12)
        r_q = Text("Q", font_size=28, color=COR_Q).next_to(eixos.y_axis.get_end(), LEFT, buff=0.12)
        o = eixos.c2p(0, 0)
        alvo = np.array([0.95, 0.6])
        r0, th0 = np.hypot(*alvo), np.arctan2(alvo[1], alvo[0])
        esc = eixos.c2p(1, 0)[0] - o[0]
        tolerancia = AnnularSector(inner_radius=(r0 - 0.07) * esc, outer_radius=(r0 + 0.07) * esc,
                                   angle=np.deg2rad(8), start_angle=th0 - np.deg2rad(4), arc_center=o,
                                   color=COR_OK, fill_opacity=0.3, stroke_width=0)
        r_tol = Text("faixa permitida\n(exagerada)", font_size=16, color=COR_OK).next_to(tolerancia, RIGHT, buff=0.15)
        ref = DashedLine(o, eixos.c2p(*alvo), color=GREY_A, stroke_width=2)
        dx, dy = ValueTracker(0.0), ValueTracker(0.0)

        def medido():
            return alvo + np.array([dx.get_value(), dy.get_value()])

        fasor = always_redraw(lambda: seta(o, eixos.c2p(*medido()), COR_RF, 6))
        erro = always_redraw(lambda: DashedLine(eixos.c2p(*medido()), eixos.c2p(*alvo), color=COR_ESPURIO,
                                                stroke_width=3) if np.hypot(dx.get_value(), dy.get_value()) > 0.02
                             else VMobject())

        painel = VGroup(
            Text("FPGA Xilinx Virtex-6 (PicoDigitizer)", font_size=20, color=COR_DIGITAL),
            Text("PI e defasadores digitais em I e Q", font_size=20, color=WHITE),
            Text("correções em microssegundos", font_size=20, color=WHITE),
            Text("largura de banda de dezenas de kHz", font_size=20, color=WHITE),
            Text("meta: < 0,1 % em amplitude e < 0,1° em fase", font_size=20, color=COR_OK),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to(P(3.6, 0.9))
        malha = VGroup(caixa("referência", 1.5, 0.5, GREY_A, 16), caixa("PI", 0.8, 0.5, COR_DIGITAL, 18),
                       caixa("cavidade", 1.3, 0.5, COR_CAV, 16)).arrange(RIGHT, buff=0.45).move_to(P(3.6, -1.5))
        setas_m = VGroup(fio([malha[0].get_right(), malha[1].get_left()], GREY_A, 2),
                         fio([malha[1].get_right(), malha[2].get_left()], GREY_A, 2),
                         fio([malha[2].get_bottom(), malha[2].get_bottom() + DOWN * 0.45,
                              malha[1].get_bottom() + DOWN * 0.45, malha[1].get_bottom()], GREY_A, 2))
        r_med = Text("medida", font_size=14, color=GREY_A).next_to(setas_m[2], DOWN, buff=0.05)

        leg = self.legenda("O LLRF trabalha só com o sinal fraco, antes dos amplificadores de potência")
        self.play(Create(eixos), FadeIn(r_i), FadeIn(r_q))
        self.play(Create(ref), FadeIn(tolerancia), FadeIn(r_tol))
        self.add(fasor, erro)
        self.play(LaggedStart(*[FadeIn(p, shift=LEFT * 0.2) for p in painel], lag_ratio=0.25), run_time=2.5)
        self.play(FadeIn(malha), Create(setas_m), FadeIn(r_med))
        leg = self.legenda("Feixe e fontes perturbam o campo; o PI mede o erro e corrige em µs", leg, COR_DIGITAL)
        for kx, ky in ((0.22, -0.15), (-0.18, 0.2), (0.12, 0.25), (-0.25, -0.1)):
            self.play(dx.animate.set_value(kx), dy.animate.set_value(ky), run_time=0.25, rate_func=rush_from)
            self.play(dx.animate.set_value(0), dy.animate.set_value(0), run_time=1.1, rate_func=smooth)
        leg = self.legenda("O campo volta sempre à faixa permitida em torno da referência", leg, COR_OK)
        self.wait(1.5)
        self.limpar()

    # ================================================================== CENA 3
    def cena_conversores(self):
        self.titulo_cena("3 · Conversores de dados: ADC e DAC")
        niveis = 8
        f = lambda x: 0.9 * np.sin(TAU * x / 4 + 0.3)

        def quant(v):
            passo = 2.0 / niveis
            return np.clip(np.round(v / passo) * passo, -1, 1)

        # ADC
        ax_a = eixos_tempo(P(-3.5, -0.3), 5.8, 3.0, [0, 8, 1], [-1.1, 1.1, 0.25])
        cab_a = Text("ADC: analógico → digital", font_size=24, color=COR_IF, weight=BOLD).next_to(ax_a, UP, buff=0.35)
        grade_a = VGroup(*[DashedLine(ax_a.c2p(0, v), ax_a.c2p(8, v), color=GREY_D, stroke_width=1)
                           for v in np.linspace(-1, 1, niveis + 1)])
        onda_a = ax_a.plot(f, x_range=[0, 8, 0.02], color=COR_IF, stroke_width=3)
        amos = VGroup(*[haste(ax_a, x, quant(f(x)), WHITE, 0.07) for x in np.arange(0, 8.01, 0.5)])
        nota_a = Text("14 bits · até 125 MSps (placa FMC)", font_size=20, color=COR_IF).next_to(ax_a, DOWN, buff=0.25)

        # DAC
        ax_d = eixos_tempo(P(3.5, -0.3), 5.8, 3.0, [0, 8, 1], [-1.1, 1.1, 0.25])
        cab_d = Text("DAC: digital → analógico", font_size=24, color=COR_DIGITAL, weight=BOLD).next_to(ax_d, UP, buff=0.35)
        xs = np.arange(0, 8.01, 0.5)
        nums = VGroup(*[Dot(ax_d.c2p(x, quant(f(x))), radius=0.07, color=WHITE) for x in xs])
        pts = []
        for x in xs[:-1]:
            pts += [ax_d.c2p(x, quant(f(x))), ax_d.c2p(x + 0.5, quant(f(x)))]
        escada = VMobject().set_points_as_corners(pts).set_stroke(COR_DIGITAL, 3)
        suave = ax_d.plot(lambda x: f(x - 0.25), x_range=[0.25, 8, 0.02], color=COR_IF, stroke_width=3)
        nota_d = Text("16 bits · até 250 MSps", font_size=20, color=COR_DIGITAL).next_to(ax_d, DOWN, buff=0.25)

        leg = self.legenda("Os conversores são a ponte entre a física contínua e a lógica discreta da FPGA")
        self.play(FadeIn(cab_a), Create(ax_a), FadeIn(grade_a))
        self.play(Create(onda_a), run_time=1.5)
        leg = self.legenda("ADC: amostras periódicas, arredondadas para o nível mais próximo (aqui só 3 bits)", leg,
                           COR_IF)
        self.play(LaggedStart(*[GrowFromPoint(a, a[0].get_start()) for a in amos], lag_ratio=0.08), run_time=2)
        self.play(FadeIn(nota_a))
        leg = self.legenda("DAC: os números calculados pela FPGA viram uma tensão contínua", leg, COR_DIGITAL)
        self.play(FadeIn(cab_d), Create(ax_d))
        self.play(LaggedStart(*[GrowFromCenter(d) for d in nums], lag_ratio=0.06), run_time=1.5)
        self.play(Create(escada), run_time=2)
        leg = self.legenda("Cada valor é mantido até o próximo; um filtro suaviza a escada", leg)
        self.play(Create(suave), run_time=1.5)
        self.play(FadeIn(nota_d))
        self.wait(1.5)
        self.limpar()

    # ================================================================== CENA 4
    def cena_down(self):
        self.titulo_cena("4 · Down-conversion: de 500 MHz para 20 MHz")
        e1 = VGroup(tex(r"v_{RF}(t) = A(t)\cos\big(\omega_{RF}t + \phi(t)\big)", COR_RF, 28),
                    tex(r"v_{LO}(t) = \cos(\omega_{LO}t + \theta_{LO})", COR_LO, 28)).arrange(RIGHT, buff=0.8
                                                                                           ).move_to(P(0, 2.45))
        e2 = tex(r"\cos a\cos b = \tfrac{1}{2}\big[\cos(a - b) + \cos(a + b)\big]", GREY_A, 26).move_to(P(0, 1.75))
        e3 = tex_partes([(r"v_{mix} = ", WHITE),
                         (r"\tfrac{1}{2}A\cos\big((\omega_{RF} - \omega_{LO})t + \phi - \theta_{LO}\big)", COR_IF),
                         (r" + ", WHITE),
                         (r"\tfrac{1}{2}A\cos\big((\omega_{RF} + \omega_{LO})t + \phi + \theta_{LO}\big)", COR_ESPURIO)],
                        26).move_to(P(0, 1.0))
        e4 = tex(r"v_{IF}(t) = \tfrac{1}{2}A(t)\cos\big(\omega_{IF}t + \phi(t) - \theta_{LO}\big)", COR_IF, 30
                 ).move_to(P(0, 0.2))

        ax, deco = self.espectro(P(0, -1.75), 1100, 12.2, 1.8)
        r_rf = raia(ax, 500, 1.0, COR_RF)
        rr_rf = Text("RF 500", font_size=16, color=COR_RF).next_to(ax.c2p(500, 1.0), UP, buff=0.05)
        l_lo = DashedLine(ax.c2p(480, 0), ax.c2p(480, 1.15), color=COR_LO, stroke_width=3)
        rr_lo = Text("LO 480", font_size=16, color=COR_LO).next_to(ax.c2p(480, 0.85), LEFT, buff=0.08)
        r_dif = raia(ax, 20, 0.6, COR_IF)
        r_soma = raia(ax, 980, 0.6, COR_ESPURIO)
        rr_dif = Text("20 MHz (diferença)", font_size=16, color=COR_IF).next_to(ax.c2p(20, 0.6), RIGHT, buff=0.1)
        rr_soma = Text("980 MHz (soma)", font_size=16, color=COR_ESPURIO).next_to(ax.c2p(980, 0.6), UP, buff=0.05)
        mascara = Polygon(ax.c2p(0, 0), ax.c2p(0, 1.15), ax.c2p(120, 1.15), ax.c2p(120, 0), color=COR_FILTRO,
                          stroke_width=3, fill_color=COR_FILTRO, fill_opacity=0.12)
        r_lpf = Text("passa-baixa", font_size=16, color=COR_FILTRO).next_to(ax.c2p(120, 1.15), RIGHT, buff=0.08)

        leg = self.legenda("O mixer é um multiplicador: sinal da cavidade × oscilador local")
        self.play(Create(ax), FadeIn(deco))
        self.play(Write(e1), GrowArrow(r_rf), FadeIn(rr_rf), run_time=1.5)
        self.play(Create(l_lo), FadeIn(rr_lo))
        leg = self.legenda("Produto de cossenos: aparecem a diferença e a soma das frequências", leg)
        self.play(FadeIn(e2, shift=UP * 0.1))
        self.play(Write(e3), ReplacementTransform(r_rf, VGroup(r_dif, r_soma)), FadeOut(rr_rf), run_time=2.2)
        self.play(FadeIn(rr_dif), FadeIn(rr_soma))
        leg = self.legenda("O filtro passa-baixa elimina a soma (980 MHz) e entrega só a IF ao ADC", leg, COR_FILTRO)
        self.play(FadeIn(mascara), FadeIn(r_lpf))
        self.play(FadeOut(r_soma), FadeOut(rr_soma))
        self.play(Write(e4), run_time=1.5)
        nota = Text("A(t) e φ(t) chegam intactos: só uma rotação fixa θ_LO e o ganho de conversão do mixer",
                    font_size=19, color=COR_IF).move_to(P(0, -0.4))
        leg = self.legenda("A informação lenta de amplitude e fase foi preservada", leg, COR_IF)
        self.play(FadeIn(nota))
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 5
    def cena_jitter(self):
        self.titulo_cena("5 · Por que 20 MHz? (1) jitter do relógio")
        ax = eixos_tempo(P(-1.3, -0.3), 8.6, 4.0, [0, 2, 0.5], [-1.2, 1.2, 0.5])
        r_t = Text("tempo (ns) →", font_size=18, color=COR_EIXO).next_to(ax, DOWN, buff=0.05).align_to(ax, RIGHT)
        marcas = marcar_x(ax, [0, 0.5, 1, 1.5, 2], ["0", "0,5", "1", "1,5", "2"])
        rf = ax.plot(lambda t: np.sin(TAU * 0.5 * (t - 1)), x_range=[0, 2, 0.005], color=COR_RF, stroke_width=4)
        fi = ax.plot(lambda t: np.sin(TAU * 0.02 * (t - 1)), x_range=[0, 2, 0.005], color=COR_IF, stroke_width=4)
        r_rf = Text("500 MHz", font_size=20, color=COR_RF).next_to(ax.c2p(0.5, 1), UP, buff=0.05)
        r_fi = Text("20 MHz", font_size=20, color=COR_IF).next_to(ax.c2p(1.8, 0.03), UP, buff=0.15)
        dt = 0.06
        faixa = Polygon(ax.c2p(1 - dt, -1.2), ax.c2p(1 - dt, 1.2), ax.c2p(1 + dt, 1.2), ax.c2p(1 + dt, -1.2),
                        stroke_width=0, fill_color=WHITE, fill_opacity=0.12)
        r_faixa = Text("incerteza Δt do instante\nde amostragem (jitter)", font_size=16, color=GREY_A
                       ).next_to(ax.c2p(1 + dt, 1.1), RIGHT, buff=0.1)
        e_rf = np.sin(TAU * 0.5 * dt)
        e_if = np.sin(TAU * 0.02 * dt)
        barra_rf = DoubleArrow(ax.c2p(1 + dt + 0.04, -e_rf), ax.c2p(1 + dt + 0.04, e_rf), buff=0, color=COR_ESPURIO,
                               stroke_width=4, max_tip_length_to_length_ratio=0.12)
        r_err = Text("erro de amplitude\nno sinal de 500 MHz", font_size=16, color=COR_ESPURIO
                     ).next_to(barra_rf, RIGHT, buff=0.1).shift(DOWN * 0.7)
        painel = VGroup(
            tex(r"\Delta v \approx \frac{dv}{dt}\,\Delta t", WHITE, 32),
            Text("500 MHz → 20 MHz:", font_size=20, color=GREY_A),
            Text("dv/dt cai 25 vezes", font_size=22, color=COR_OK),
            Text("leitura com 14 bits efetivos", font_size=18, color=GREY_A),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(P(5.3, 0.0))

        leg = self.legenda("Amostrar 500 MHz direto exigiria GSps e reduziria os bits efetivos (ENOB)")
        self.play(Create(ax), FadeIn(marcas), FadeIn(r_t))
        self.play(Create(rf), FadeIn(r_rf), Create(fi), FadeIn(r_fi), run_time=2)
        leg = self.legenda("O relógio do ADC nunca é perfeito: o instante de amostragem treme um pouco", leg)
        self.play(FadeIn(faixa), FadeIn(r_faixa))
        leg = self.legenda("O mesmo Δt gera um erro proporcional à inclinação do sinal", leg, COR_ESPURIO)
        self.play(GrowFromCenter(barra_rf), FadeIn(r_err))
        self.play(Write(painel[0]))
        self.play(LaggedStart(*[FadeIn(p) for p in painel[1:]], lag_ratio=0.3))
        leg = self.legenda("Na IF de 20 MHz o sinal varia devagar: o jitter quase não importa", leg, COR_OK)
        self.play(Indicate(fi, color=COR_IF, scale_factor=1.02))
        self.wait(1.5)
        self.limpar()

    def cena_sincronismo(self):
        self.titulo_cena("5 · Por que 20 MHz? (2) amostragem síncrona")
        ax = eixos_tempo(P(0, -0.6), 11.5, 3.2, [0, 100, 10], [-1.2, 1.2, 0.5])
        marcas = marcar_x(ax, range(0, 101, 10), [str(v) for v in range(0, 101, 10)])
        r_t = Text("tempo (ns) →", font_size=18, color=COR_EIXO).next_to(ax, DOWN, buff=0.05).align_to(ax, RIGHT)
        onda = ax.plot(lambda t: np.sin(TAU * 0.02 * t + 0.4), x_range=[0, 100, 0.2], color=COR_IF, stroke_width=4)
        amos = VGroup(*[haste(ax, t, np.sin(TAU * 0.02 * t + 0.4), WHITE, 0.08, 3) for t in range(0, 101, 10)])
        formula = tex(r"\frac{f_s}{f_{IF}} = \frac{100\ \text{MSps}}{20\ \text{MHz}} = 5\ \text{amostras por período}",
                      COR_DIGITAL, 32).move_to(P(0, 2.45))
        periodo = BraceBetweenPoints(ax.c2p(0, 1.15), ax.c2p(50, 1.15), UP, color=GREY_A)
        r_per = Text("1 período de IF = 50 ns", font_size=18, color=GREY_A).next_to(periodo, UP, buff=0.05)

        leg = self.legenda("O ADC roda a uma taxa fixa (100 ou 125 MSps)")
        self.play(Create(ax), FadeIn(marcas), FadeIn(r_t))
        self.play(Create(onda), run_time=2)
        leg = self.legenda("Com 100 MSps e IF de 20 MHz, a razão é um inteiro exato", leg, COR_DIGITAL)
        self.play(LaggedStart(*[GrowFromPoint(a, a[0].get_start()) for a in amos], lag_ratio=0.12), run_time=2)
        self.play(GrowFromCenter(periodo), FadeIn(r_per))
        self.play(Write(formula), run_time=1.5)
        leg = self.legenda("Fases conhecidas a cada amostra: I e Q saem com aritmética simples e baixa latência", leg,
                           COR_DIGITAL)
        self.wait(2)
        self.limpar()

    def cena_ruido_dc(self):
        self.titulo_cena("5 · Por que 20 MHz? (3) offset DC e ruído 1/f")
        ax, deco = self.espectro(P(0, -0.4), 40, 11.5, 3.4, passo=5)
        ruido = ax.plot(lambda f: min(0.08 + 0.35 / max(f, 0.1), 1.2), x_range=[0.3, 40, 0.05], color=COR_ESPURIO,
                        stroke_width=3)
        area = ax.get_area(ruido, x_range=[0.3, 40], color=COR_ESPURIO, opacity=0.18)
        offset = raia(ax, 0.15, 1.1, COR_ESPURIO, 7)
        r_ruido = Text("offset DC, deriva térmica e ruído 1/f", font_size=18, color=COR_ESPURIO
                       ).next_to(ax.c2p(1.5, 1.0), RIGHT, buff=0.1)
        sinal_if = raia(ax, 20, 0.95, COR_IF, 7)
        r_if = Text("IF = 20 MHz: longe da sujeira", font_size=18, color=COR_IF).next_to(ax.c2p(20, 0.8), RIGHT, buff=0.15)
        fantasma = raia(ax, 0.5, 0.95, COR_IF, 5).set_opacity(0.5)
        r_fant = Text("zero-IF: o sinal cairia aqui", font_size=16, color=COR_IF).next_to(ax.c2p(0.5, 0.6), RIGHT,
                                                                                          buff=0.25)

        leg = self.legenda("Por que não descer direto para 0 Hz (zero-IF)?")
        self.play(Create(ax), FadeIn(deco))
        self.play(GrowArrow(offset), Create(ruido), FadeIn(area), FadeIn(r_ruido), run_time=1.5)
        leg = self.legenda("Perto de DC moram o offset dos amplificadores, as derivas lentas e o ruído 1/f", leg,
                           COR_ESPURIO)
        self.play(GrowArrow(fantasma), FadeIn(r_fant))
        self.wait(1)
        leg = self.legenda("Em 20 MHz a portadora fica limpa e esses ruídos são rejeitados antes do ADC", leg, COR_IF)
        self.play(FadeOut(fantasma), FadeOut(r_fant), GrowArrow(sinal_if), FadeIn(r_if))
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 6
    def cena_up(self):
        self.titulo_cena("6 · Up-conversion: de 20 MHz para 500 MHz")
        e1 = VGroup(tex(r"v_{IF}(t) = A_{act}(t)\cos\big(\omega_{IF}t + \phi_{act}(t)\big)", COR_IF, 28),
                    tex(r"v_{LO}(t) = \cos(\omega_{LO}t + \theta_{LO})", COR_LO, 28)).arrange(RIGHT, buff=0.8
                                                                                           ).move_to(P(0, 2.45))
        e3 = tex_partes([(r"v_{mix} = ", WHITE),
                         (r"\tfrac{1}{2}A_{act}\cos\big((\omega_{LO} + \omega_{IF})t + \phi_{act} + \theta_{LO}\big)",
                          COR_RF), (r" + ", WHITE),
                         (r"\tfrac{1}{2}A_{act}\cos\big((\omega_{LO} - \omega_{IF})t - \phi_{act} + \theta_{LO}\big)",
                          COR_ESPURIO)], 26).move_to(P(0, 1.6))
        e4 = tex(r"v_{RF}(t) = \tfrac{1}{2}A_{act}(t)\cos\big(\omega_{RF}t + \phi_{act}(t) + \theta_{LO}\big)", COR_RF,
                 30).move_to(P(0, 0.75))

        ax, deco = self.espectro(P(0, -1.6), 600, 12.2, 2.1, passo=100)
        r_if = raia(ax, 20, 1.0, COR_IF)
        rr_if = Text("IF 20", font_size=16, color=COR_IF).next_to(ax.c2p(20, 1.0), RIGHT, buff=0.08)
        l_lo = raia(ax, 480, 0.35, COR_LO, 4)
        rr_lo = Text("vazamento do LO (480)", font_size=14, color=COR_LO).next_to(ax.c2p(480, 0.35), LEFT, buff=0.08)
        r_usb = raia(ax, 500, 0.6, COR_RF)
        r_lsb = raia(ax, 460, 0.6, COR_ESPURIO)
        rr_usb = Text("500 (soma)", font_size=16, color=COR_RF).next_to(ax.c2p(500, 0.6), UR, buff=0.05)
        rr_lsb = Text("460 (imagem)", font_size=16, color=COR_ESPURIO).next_to(ax.c2p(460, 0.6), UL, buff=0.05)
        mascara = Polygon(ax.c2p(488, 0), ax.c2p(488, 1.15), ax.c2p(512, 1.15), ax.c2p(512, 0), color=COR_FILTRO,
                          stroke_width=3, fill_color=COR_FILTRO, fill_opacity=0.15)
        r_bpf = Text("passa-banda em 500 MHz", font_size=16, color=COR_FILTRO).next_to(ax.c2p(512, 1.15), RIGHT,
                                                                                      buff=0.05)

        leg = self.legenda("O DAC sintetiza a IF de comando; o mixer de subida a multiplica pelo LO")
        self.play(Create(ax), FadeIn(deco))
        self.play(Write(e1), GrowArrow(r_if), FadeIn(rr_if), run_time=1.5)
        leg = self.legenda("De novo, soma e diferença: 480 + 20 = 500 MHz e 480 − 20 = 460 MHz", leg)
        self.play(Write(e3), ReplacementTransform(r_if, VGroup(r_usb, r_lsb)), FadeOut(rr_if), run_time=2.2)
        self.play(FadeIn(rr_usb), FadeIn(rr_lsb), GrowArrow(l_lo), FadeIn(rr_lo))
        leg = self.legenda("O passa-banda em 500 MHz remove a imagem de 460 e o vazamento do LO", leg, COR_FILTRO)
        self.play(FadeIn(mascara), FadeIn(r_bpf))
        self.play(FadeOut(VGroup(r_lsb, rr_lsb, l_lo, rr_lo)))
        self.play(Write(e4), run_time=1.5)
        leg = self.legenda("A modulação calculada na FPGA chega a 500 MHz, só com ganho e rotação fixa", leg, COR_RF)
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 7
    def cena_por_que_500(self):
        self.titulo_cena("7 · Por que subir para 500 MHz?")
        ax = eixos_tempo(P(-3.4, -0.4), 6.0, 3.6, [0, 600, 100], [0, 1.1, 0.5])
        marcas = marcar_x(ax, range(0, 601, 100), [str(v) for v in range(0, 601, 100)])
        r_f = Text("f (MHz)", font_size=16, color=COR_EIXO).next_to(marcas, DOWN, buff=0.05).align_to(ax, RIGHT)
        r_ax = rotulo_eixo(ax, Text("|Z| da cavidade (normalizado)", font_size=18, color=COR_CAV))
        q = 40

        def z(f):
            w = max(f, 1e-3) / 500
            return abs(1 / (1 + 1j * q * (w - 1 / w)))

        curva = ax.plot(z, x_range=[1, 600, 0.5], color=COR_CAV, stroke_width=4)
        p20 = Dot(ax.c2p(20, z(20)), radius=0.09, color=COR_IF)
        r20 = Text("20 MHz: |Z| ≈ 0\n(o indutor vira curto)", font_size=16, color=COR_IF).next_to(
            ax.c2p(20, 0.25), RIGHT, buff=0.1)
        p500 = Dot(ax.c2p(500, 1), radius=0.09, color=COR_RF)
        r500 = Text("500 MHz: ressonância TM₀₁₀\n|Z| máxima", font_size=16, color=COR_RF).next_to(
            ax.c2p(500, 1), LEFT, buff=0.15)

        ax_b = eixos_tempo(P(3.6, -0.4), 6.0, 3.0, [0, 4, 1], [-1.2, 1.2, 0.5])
        r_axb = rotulo_eixo(ax_b, Text("campo acelerador na fenda da cavidade", font_size=18, color=COR_RF))
        r_tb = Text("tempo (períodos de RF) →", font_size=16, color=COR_EIXO).next_to(ax_b, DOWN, buff=0.05
                                                                                       ).align_to(ax_b, RIGHT)
        campo = ax_b.plot(lambda t: np.cos(TAU * t), x_range=[0, 4, 0.01], color=COR_RF, stroke_width=3)
        pacotes = VGroup(*[Ellipse(width=0.25, height=0.14, color=PINK, fill_opacity=0.95).move_to(ax_b.c2p(k, 1))
                           for k in range(5)])
        r_pac = Text("cada pacote chega na crista do campo", font_size=16, color=PINK).next_to(ax_b, DOWN, buff=0.4)

        leg = self.legenda("A cavidade foi construída para ressoar em 500 MHz")
        self.play(Create(ax), FadeIn(marcas), FadeIn(r_f), FadeIn(r_ax))
        self.play(Create(curva), run_time=2)
        self.play(GrowFromCenter(p20), FadeIn(r20))
        self.play(GrowFromCenter(p500), FadeIn(r500))
        leg = self.legenda("Só perto de 500 MHz a cavidade acumula centenas de kV para acelerar o feixe", leg, COR_RF)
        self.wait(1)
        leg = self.legenda("Os elétrons passam em pacotes, sincronizados com a frequência de RF", leg, PINK)
        self.play(Create(ax_b), FadeIn(r_axb), FadeIn(r_tb), Create(campo))
        self.play(LaggedStart(*[FadeIn(p, shift=RIGHT * 0.3) for p in pacotes], lag_ratio=0.25), FadeIn(r_pac))
        leg = self.legenda("A volta no anel é múltipla do período de RF: fase síncrona estável", leg, PINK)
        self.wait(1.2)
        leg = self.legenda("E sintetizar 500 MHz direto exigiria DACs de vários GSps: por isso o mixer analógico", leg)
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 8
    def cena_iq_fpga(self):
        self.titulo_cena("8 · Onde ficam a desmodulação e a modulação IQ")
        y0 = 1.9
        adc = conversor("ADC", invertido=True).move_to(P(-5.8, y0))
        chip = RoundedRectangle(corner_radius=0.2, width=9.0, height=1.5, color=COR_DIGITAL, stroke_width=4
                                ).move_to(P(-0.2, y0))
        r_chip = Text("FPGA", font_size=18, color=COR_DIGITAL, weight=BOLD).next_to(chip.get_corner(UL), DR, buff=0.08)
        demod = caixa("desmodulação\nIQ", 1.9, 0.8, COR_I, 16).move_to(P(-3.0, y0 - 0.1))
        pi = caixa("PI", 1.0, 0.8, WHITE, 20).move_to(P(-0.2, y0 - 0.1))
        mod = caixa("modulação IQ\n(NCO)", 1.9, 0.8, COR_Q, 16).move_to(P(2.6, y0 - 0.1))
        dac = conversor("DAC").move_to(P(5.4, y0))
        fios = VGroup(fio([adc.get_right(), demod.get_left()], COR_IF), fio([demod.get_right(), pi.get_left()], GREY_A),
                      fio([pi.get_right(), mod.get_left()], GREY_A), fio([mod.get_right(), dac.get_left()], COR_IF))
        r_iq1 = tex(r"I, Q", WHITE, 22).next_to(fios[1], UP, buff=0.05)
        r_iq2 = tex(r"I_{act}, Q_{act}", WHITE, 22).next_to(fios[2], UP, buff=0.05)

        ax = eixos_tempo(P(-3.4, -1.3), 5.8, 2.4, [0, 2, 0.25], [-1.2, 1.2, 0.5])
        r_ax = rotulo_eixo(ax, tex(r"v_{IF} = I\cos\omega t - Q\sin\omega t,\ \ f_s = 4 f_{IF}", COR_IF, 24))
        fi = np.deg2rad(35)
        I0, Q0 = np.cos(fi), np.sin(fi)
        onda = ax.plot(lambda x: I0 * np.cos(TAU * x) - Q0 * np.sin(TAU * x), x_range=[0, 2, 0.01], color=COR_IF,
                       stroke_width=3).set_stroke(opacity=0.6)
        nomes = [("I", COR_I), ("-Q", COR_Q), ("-I", COR_I), ("Q", COR_Q)]
        amos = VGroup()
        for k in range(9):
            y = I0 * np.cos(TAU * k / 4) - Q0 * np.sin(TAU * k / 4)
            nome, cor = nomes[k % 4]
            amos.add(VGroup(haste(ax, k / 4, y, cor, 0.07, 3),
                            tex(nome, cor, 24).next_to(ax.c2p(k / 4, y), UP if y >= 0 else DOWN, buff=0.08)))
        r_dem = Text("amostras a cada 90°: basta reordenar e trocar o sinal", font_size=18, color=COR_I
                     ).next_to(ax, DOWN, buff=0.15)
        f_mod = tex(r"V_{act}[n] = I_{act}[n]\cos(\omega_{IF} n T_s) - Q_{act}[n]\sin(\omega_{IF} n T_s)", COR_Q, 28
                    ).move_to(P(3.4, -0.6))
        r_mod = Text("uma única palavra digital por amostra entra no DAC", font_size=18, color=COR_Q
                     ).next_to(f_mod, DOWN, buff=0.2)

        leg = self.legenda("Tanto a desmodulação quanto a modulação acontecem dentro da FPGA")
        self.play(FadeIn(adc), Create(chip), FadeIn(r_chip), FadeIn(dac))
        self.play(FadeIn(demod), FadeIn(pi), FadeIn(mod), Create(fios), FadeIn(r_iq1), FadeIn(r_iq2), run_time=1.5)
        p = caminho([adc.get_center(), demod.get_center(), pi.get_center(), mod.get_center(), dac.get_center()])
        self.play(ShowPassingFlash(p.set_stroke(WHITE, 7), time_width=0.4), run_time=1.5)
        leg = self.legenda("Logo após o ADC: a IF de 20 MHz vira I e Q em banda base", leg, COR_I)
        self.play(Indicate(demod, color=COR_I))
        self.play(Create(ax), FadeIn(r_ax), Create(onda))
        self.play(LaggedStart(*[FadeIn(a) for a in amos], lag_ratio=0.15), run_time=2)
        self.play(FadeIn(r_dem))
        leg = self.legenda("Logo antes do DAC: as correções I e Q modulam uma portadora digital (NCO)", leg, COR_Q)
        self.play(Indicate(mod, color=COR_Q))
        self.play(Write(f_mod), run_time=1.8)
        self.play(FadeIn(r_mod))
        leg = self.legenda("O ADC e o DAC só lidam com a senoide de 20 MHz; I e Q vivem na lógica digital", leg)
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 9
    def cena_potencia(self):
        self.titulo_cena("9 · Cadeia de potência: amplificadores, fontes e linhas")
        y0 = 0.9
        llrf = caixa("LLRF", 1.1, 0.7, COR_DIGITAL, 20).move_to(P(-5.9, y0))
        pre = VGroup(amplificador().scale(0.75), Text("PreAmp", font_size=16, color=COR_POTENCIA)).move_to(P(-3.6, y0))
        pre[1].next_to(pre[0], DOWN, buff=0.15)
        ssa = VGroup(amplificador().scale(1.3), Text("SSAMP", font_size=18, color=COR_POTENCIA)).move_to(P(-0.6, y0))
        ssa[1].next_to(ssa[0], DOWN, buff=0.15)
        guia = VGroup(Rectangle(width=2.2, height=0.55, color=GREY_A, stroke_width=4),
                      Text("guia de onda", font_size=16, color=GREY_A)).move_to(P(2.6, y0))
        cav = VGroup(Ellipse(width=1.5, height=0.85, color=COR_CAV, stroke_width=4),
                     Text("Cavidade", font_size=16, color=COR_CAV)).move_to(P(5.6, y0))
        f1 = fio([llrf.get_right(), pre[0].get_left()], COR_RF, 2)
        f2 = fio([pre[0].get_right(), ssa[0].get_left()], COR_RF, 4)
        f3 = fio([ssa[0].get_right(), guia.get_left()], COR_RF, 9)
        f4 = fio([guia.get_right(), cav.get_left()], COR_RF, 9)
        niveis = VGroup(
            Text("dezenas de mW", font_size=18, color=COR_DIGITAL).next_to(f1, UP, buff=0.2),
            Text("nível de excitação", font_size=18, color=COR_POTENCIA).next_to(f2, UP, buff=0.35),
            Text("dezenas a centenas de kW", font_size=18, color=COR_POTENCIA).next_to(guia, UP, buff=0.3),
        )
        fontes = caixa("Fontes de alimentação (CA → CC)", 3.6, 0.6, COR_POTENCIA, 16).move_to(P(-0.6, -1.0))
        w_f = DashedLine(fontes.get_top(), ssa[1].get_bottom(), color=COR_POTENCIA, stroke_width=3)
        notas = VGroup(
            Text("SSAMP: centenas de transistores de RF combinados", font_size=18, color=COR_POTENCIA),
            Text("Ripple das fontes (60 Hz, 120 Hz, 360 Hz, kHz de chaveamento) modula o ganho", font_size=18,
                 color=COR_ESPURIO),
            Text("Coaxial 50 Ω: sinais fracos, clock, LO e medidas · Guia de onda: a potência alta", font_size=18,
                 color=GREY_A),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(P(0, -2.2))

        leg = self.legenda("O sinal que sai do LLRF tem dezenas de mW: incapaz de acelerar o feixe")
        self.play(FadeIn(llrf), FadeIn(cav))
        self.play(FadeIn(pre), Create(f1), FadeIn(niveis[0]))
        leg = self.legenda("Pré-amplificador: estágio linear que leva o sinal ao nível de excitação", leg, COR_POTENCIA)
        self.play(Create(f2), FadeIn(niveis[1]))
        leg = self.legenda("Amplificador de estado sólido: a etapa final, em quilowatts", leg, COR_POTENCIA)
        self.play(FadeIn(ssa), Create(f3))
        self.play(FadeIn(notas[0]))
        leg = self.legenda("Cabos coaxiais derreteriam: a alta potência vai por guias de onda até o acoplador", leg)
        self.play(FadeIn(guia), Create(f4), FadeIn(niveis[2]))
        self.play(FadeIn(notas[2]))
        leg = self.legenda("As fontes convertem a rede em CC estável, mas sempre sobra um ripple", leg, COR_ESPURIO)
        self.play(FadeIn(fontes), Create(w_f))
        self.play(FadeIn(notas[1]))
        p = caminho([llrf.get_center(), pre[0].get_center(), ssa[0].get_center(), guia.get_center(), cav.get_center()])
        self.play(ShowPassingFlash(p.set_stroke(WHITE, 9), time_width=0.4), run_time=1.8)
        self.wait(1.5)
        self.limpar()

    # ================================================================== CENA 10
    def cena_ripple(self):
        self.titulo_cena("10 · Largura de banda do controle × ripple")
        s_formula = tex(r"S(s) = \frac{1}{1 + C(s)H(s)}", WHITE, 32).move_to(P(-4.3, 2.45))
        modelo = Text("(modelo simples: C(s)H(s) ≈ ω_BW / s)", font_size=16, color=GREY_A).next_to(s_formula, DOWN,
                                                                                                    buff=0.1)
        ax = Axes(x_range=[2, 6, 1], y_range=[0, 1.1, 0.5], x_length=6.2, y_length=2.6,
                  axis_config=EIXO_CFG).move_to(P(-3.4, -0.6))
        marcas = marcar_x(ax, [2, 3, 4, 5, 6], ["100 Hz", "1 kHz", "10 kHz", "100 kHz", "1 MHz"])
        r_ax = rotulo_eixo(ax, Text("|S| = fração da perturbação que sobra", font_size=18, color=GREY_A))

        def s_mod(logf, bw):
            f = 10 ** logf
            return f / np.hypot(f, bw)

        lento = ax.plot(lambda x: s_mod(x, 1e3), x_range=[2, 6, 0.01], color=COR_ESPURIO, stroke_width=4)
        rapido = ax.plot(lambda x: s_mod(x, 5e4), x_range=[2, 6, 0.01], color=COR_OK, stroke_width=4)
        r_lento = Text("BW = 1 kHz", font_size=18, color=COR_ESPURIO).next_to(ax.c2p(2.9, 0.75), UP, buff=0.05)
        r_rapido = Text("BW = 50 kHz", font_size=18, color=COR_OK).next_to(ax.c2p(4.75, 0.45), RIGHT, buff=0.1)
        l10k = DashedLine(ax.c2p(4, 0), ax.c2p(4, 1.1), color=COR_POTENCIA, stroke_width=3)
        r10k = Text("ripple de 10 kHz", font_size=16, color=COR_POTENCIA).next_to(ax.c2p(4, 0.75), RIGHT, buff=0.1)
        d_lento = Dot(ax.c2p(4, s_mod(4, 1e3)), radius=0.09, color=COR_ESPURIO)
        d_rapido = Dot(ax.c2p(4, s_mod(4, 5e4)), radius=0.09, color=COR_OK)

        ax_t = eixos_tempo(P(3.6, -0.6), 5.8, 2.6, [0, 0.5, 0.1], [0.7, 1.3, 0.1])
        r_axt = rotulo_eixo(ax_t, Text("amplitude do campo na cavidade", font_size=18, color=GREY_A))
        r_tt = Text("tempo (ms) →", font_size=16, color=COR_EIXO).next_to(ax_t, DOWN, buff=0.05).align_to(ax_t, RIGHT)
        amp_r = 0.2
        t_lento = ax_t.plot(lambda t: 1 + amp_r * s_mod(4, 1e3) * np.sin(TAU * 10 * t), x_range=[0, 0.5, 0.001],
                            color=COR_ESPURIO, stroke_width=3)
        t_rapido = ax_t.plot(lambda t: 1 + amp_r * s_mod(4, 5e4) * np.sin(TAU * 10 * t), x_range=[0, 0.5, 0.001],
                             color=COR_OK, stroke_width=4)

        leg = self.legenda("A rejeição de uma perturbação depende da função de sensibilidade")
        self.play(Write(s_formula), FadeIn(modelo))
        self.play(Create(ax), FadeIn(marcas), FadeIn(r_ax))
        self.play(Create(lento), FadeIn(r_lento), Create(rapido), FadeIn(r_rapido), run_time=2)
        leg = self.legenda("Abaixo da banda |S| ≪ 1: o controle cancela a perturbação; acima |S| ≈ 1: ele fica cego",
                           leg)
        self.wait(1.2)
        leg = self.legenda("Exemplo: ripple de chaveamento em 10 kHz", leg, COR_POTENCIA)
        self.play(Create(l10k), FadeIn(r10k))
        self.play(GrowFromCenter(d_lento), GrowFromCenter(d_rapido))
        v1 = Text(f"sobra {100 * s_mod(4, 1e3):.0f} %", font_size=18, color=COR_ESPURIO).next_to(d_lento, DR, buff=0.08)
        v2 = Text(f"sobra {100 * s_mod(4, 5e4):.0f} %", font_size=18, color=COR_OK).next_to(d_rapido, RIGHT, buff=0.1)
        self.play(FadeIn(v1), FadeIn(v2))
        leg = self.legenda("LLRF lento (1 kHz): o ripple passa direto para o campo e perturba o feixe", leg, COR_ESPURIO)
        self.play(Create(ax_t), FadeIn(r_axt), FadeIn(r_tt))
        self.play(Create(t_lento), run_time=2)
        leg = self.legenda("LLRF rápido (50 kHz): o PI rastreia e contra-modula o ripple ciclo a ciclo", leg, COR_OK)
        self.play(Create(t_rapido), run_time=2)
        leg = self.legenda("O controle precisa ser mais rápido que as perturbações das fontes e do feixe", leg)
        self.wait(1.8)
        self.limpar()

    # ================================================================== RESUMO
    def cena_resumo(self):
        self.titulo_cena("Resumo")
        itens = VGroup(*[Text(t, font_size=22, color=c) for t, c in [
            ("• LLRF: PI digital em I e Q numa FPGA, sinal fraco, correções em µs", COR_DIGITAL),
            ("• ADC (14 bits, 125 MSps) e DAC (16 bits, 250 MSps): pontes analógico ↔ digital", WHITE),
            ("• Mixers com LO de 480 MHz: 500 MHz ↔ 20 MHz; filtros removem a imagem", COR_LO),
            ("• 20 MHz: menos jitter, 5 amostras por período, longe do offset e do ruído 1/f", COR_IF),
            ("• 500 MHz: ressonância da cavidade e sincronismo com os pacotes do feixe", COR_RF),
            ("• PreAmp + SSAMP até kW; guias de onda levam a potência à cavidade", COR_POTENCIA),
            ("• Banda do controle acima das frequências de ripple das fontes", COR_OK),
        ]]).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(P(0, -0.2))
        self.play(LaggedStart(*[FadeIn(t, shift=RIGHT * 0.2) for t in itens], lag_ratio=0.3), run_time=4)
        self.wait(3)
        self.limpar()
