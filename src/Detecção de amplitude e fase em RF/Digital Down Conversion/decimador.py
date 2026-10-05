# -*- coding: utf-8 -*-
"""
Decimador: reduzir a taxa de amostragem sem perder a informação
===============================================================

Renderização (a partir da raiz do repositório):
    manim -pql "src/Detecção de amplitude e fase em RF/Digital Down Conversion/decimador.py" Decimador   # rascunho
    manim -pqh "src/Detecção de amplitude e fase em RF/Digital Down Conversion/decimador.py" Decimador   # final

Requer LaTeX (MathTex).

Roteiro (segue "docs/Detecção de amplitude e fase em RF/Digital Down Conversion/Decimador"):
    Abertura
    Cena 1 - O que é decimar: manter 1 amostra a cada M (f_s → f_s/M)
    Cena 2 - As duas etapas obrigatórias: FIR passa-baixa e downsampling ↓M
    Cena 3 - Por que filtrar antes: aliasing no espectro e no tempo
    Cena 4 - Downsampling: quais amostras ficam e quais saem
    Cena 5 - Por que isso é crucial em FPGAs: DSP slices, timing e energia
    Cena 6 - Estrutura polifásica: só calcular o que vai ser mantido
    Resumo
"""

import numpy as np
from manim import *

# Paleta didática (fixa em todas as cenas)
COR_SINAL = BLUE         # sinal útil
COR_MANTIDA = WHITE      # amostras mantidas
COR_DESCARTE = GREY_D    # amostras descartadas
COR_RUIDO = RED          # ruído de alta frequência / aliasing / desperdício
COR_FIR = PINK           # filtro FIR anti-aliasing
COR_DEC = TEAL           # downsampling / taxa reduzida
COR_FPGA = PURPLE_B
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


def seta(a, b, cor, largura=6):
    if np.linalg.norm(b - a) < 1e-3:
        return VMobject()
    return Arrow(a, b, buff=0, color=cor, stroke_width=largura,
                 max_tip_length_to_length_ratio=0.18, max_stroke_width_to_length_ratio=12)


def fio(pontos, cor=WHITE, largura=3):
    g = VGroup(*[Line(pontos[k], pontos[k + 1], color=cor, stroke_width=largura) for k in range(len(pontos) - 2)])
    g.add(Arrow(pontos[-2], pontos[-1], buff=0, color=cor, stroke_width=largura,
                max_tip_length_to_length_ratio=0.25, max_stroke_width_to_length_ratio=10))
    return g


def caminho(pontos):
    return VMobject().set_points_as_corners(pontos)


def caixa(rotulo, largura=1.6, altura=0.8, cor=WHITE, tamanho=22):
    r = RoundedRectangle(corner_radius=0.1, width=largura, height=altura, color=cor, stroke_width=3)
    return VGroup(r, Text(rotulo, font_size=tamanho, color=cor).move_to(r))


def caixa_tex(rotulo, largura=1.2, altura=0.8, cor=WHITE, tamanho=32):
    r = RoundedRectangle(corner_radius=0.1, width=largura, height=altura, color=cor, stroke_width=3)
    return VGroup(r, tex(rotulo, cor, tamanho).move_to(r))


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


def sinal_util(n):
    """Sinal lento usado nas cenas (unidade de tempo = amostras)."""
    return np.sin(TAU * n / 30) + 0.3 * np.sin(TAU * n / 75 + 0.8)


def relogio(x0, x1, y, periodo, cor, altura=0.35):
    """Onda quadrada de clock entre x0 e x1 (unidades da tela)."""
    pts = [P(x0, y)]
    x, alto = x0, False
    while x < x1:
        x2 = min(x + periodo / 2, x1)
        yy = y + altura if alto else y
        pts += [P(x, yy), P(x2, yy)]
        alto = not alto
        x = x2
    return VMobject().set_points_as_corners(pts).set_stroke(cor, 3)


# =============================================================================
# Cena
# =============================================================================
class Decimador(Scene):
    def construct(self):
        self.camera.background_color = FUNDO
        self.abertura()
        self.cena_o_que_e()
        self.cena_duas_etapas()
        self.cena_aliasing()
        self.cena_downsampling()
        self.cena_fpga()
        self.cena_polifasico()
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

    def limpar(self):
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
        self.wait(0.2)

    # ---------------------------------------------------------------- abertura
    def abertura(self):
        titulo = Text("Decimador", font_size=64, weight=BOLD)
        sub = Text("Reduzir a taxa de amostragem sem perder a informação", font_size=30, color=GREY_A)
        cadeia = VGroup(tex(r"x[n]", WHITE, 34), tex(r"\rightarrow", GREY_A, 34),
                        caixa("FIR", 1.0, 0.6, COR_FIR, 20), tex(r"\rightarrow", GREY_A, 34),
                        caixa_tex(r"\downarrow M", 1.0, 0.6, COR_DEC, 28), tex(r"\rightarrow", GREY_A, 34),
                        tex(r"y[m]", WHITE, 34)).arrange(RIGHT, buff=0.25)
        g = VGroup(titulo, sub, cadeia).arrange(DOWN, buff=0.4)
        self.play(Write(titulo), run_time=1.5)
        self.play(FadeIn(sub, shift=UP * 0.2), FadeIn(cadeia, shift=UP * 0.2))
        self.wait(1.2)
        self.play(FadeOut(g))

    # ================================================================== CENA 1
    def cena_o_que_e(self):
        self.titulo_cena("1 · O que é decimar")
        ax = eixos_tempo(P(0, 0.35), 12.2, 3.4, [0, 60, 10], [-1.5, 1.5, 0.5])
        marcas = marcar_x(ax, range(0, 61, 10), [str(v) for v in range(0, 61, 10)])
        r_t = Text("tempo (amostras) →", font_size=18, color=COR_EIXO).next_to(ax, DOWN, buff=0.35).align_to(ax, RIGHT)
        curva = ax.plot(sinal_util, x_range=[0, 60, 0.1], color=COR_SINAL, stroke_width=3)
        todas = VGroup(*[Dot(ax.c2p(n, sinal_util(n)), radius=0.05, color=GREY_B) for n in range(61)])
        M = ValueTracker(1)

        def m():
            return int(round(M.get_value()))

        mantidas = always_redraw(lambda: VGroup(*[
            Dot(ax.c2p(n, sinal_util(n)), radius=0.1, color=COR_MANTIDA).set_stroke(COR_SINAL, 3)
            for n in range(0, 61, m())]))
        painel = always_redraw(lambda: VGroup(
            Text(f"Fator de decimação M = {m()}", font_size=24, color=COR_DEC),
            Text(f"amostras mantidas: 1 a cada {m()}", font_size=22, color=WHITE),
            Text(f"nova taxa: {100 / m():.1f} % da original", font_size=22, color=WHITE),
        ).arrange(RIGHT, buff=0.6).move_to(P(0, -2.3)))
        formula = tex(r"f_s' = \frac{f_s}{M}", COR_DEC, 40).move_to(P(4.9, 2.6))

        leg = self.legenda("Um ADC a 100 MHz gera 100 milhões de números por segundo")
        self.play(Create(ax), FadeIn(marcas), FadeIn(r_t))
        self.play(Create(curva), LaggedStart(*[GrowFromCenter(d) for d in todas], lag_ratio=0.02), run_time=2)
        leg = self.legenda("Se a informação útil varia lentamente (≈ 1 MHz), quase todas são redundantes", leg)
        self.wait(1)
        self.add(mantidas)
        self.play(FadeIn(painel))
        leg = self.legenda("Decimar: manter só 1 amostra a cada M", leg, COR_DEC)
        for k in (2, 4, 6):
            self.play(M.animate.set_value(k), run_time=1.2)
            self.wait(0.6)
        self.play(Write(formula))
        leg = self.legenda("A forma do sinal continua visível com bem menos pontos", leg, COR_OK)
        self.play(M.animate.set_value(10), run_time=1.2)
        self.play(M.animate.set_value(6), run_time=1)
        self.wait(1.2)
        self.limpar()

    # ================================================================== CENA 2
    def cena_duas_etapas(self):
        self.titulo_cena("2 · As duas etapas obrigatórias")
        y0 = 0.9
        x_in = tex(r"x[n]", WHITE, 36).move_to(P(-5.8, y0))
        fir = caixa("FIR passa-baixa\n(anti-aliasing)", 2.8, 1.2, COR_FIR, 22).move_to(P(-2.4, y0))
        dec = caixa_tex(r"\downarrow M", 1.6, 1.2, COR_DEC, 40).move_to(P(1.5, y0))
        y_out = tex(r"y[m]", WHITE, 36).move_to(P(4.9, y0))
        fios = VGroup(fio([x_in.get_right() + RIGHT * 0.1, fir.get_left()]), fio([fir.get_right(), dec.get_left()]),
                      fio([dec.get_right(), y_out.get_left() + LEFT * 0.1]))
        taxas = VGroup(
            tex(r"f_s", GREY_A, 30).next_to(fios[0], UP, buff=0.1),
            tex(r"f_s", GREY_A, 30).next_to(fios[1], UP, buff=0.1),
            tex(r"f_s/M", COR_DEC, 30).next_to(fios[2], UP, buff=0.1),
        )
        n1 = VGroup(Text("1 · Filtragem", font_size=24, color=COR_FIR, weight=BOLD),
                    Text("remove as altas frequências\nque iriam se dobrar", font_size=20, color=GREY_A)
                    ).arrange(DOWN, buff=0.15).next_to(fir, DOWN, buff=0.4)
        n2 = VGroup(Text("2 · Downsampling", font_size=24, color=COR_DEC, weight=BOLD),
                    Text("descarta M − 1 de cada\nM amostras", font_size=20, color=GREY_A)
                    ).arrange(DOWN, buff=0.15).next_to(dec, DOWN, buff=0.4)

        leg = self.legenda("A decimação real sempre tem duas etapas, nesta ordem")
        self.play(FadeIn(x_in), Create(fios[0]), FadeIn(taxas[0]))
        self.play(FadeIn(fir), Create(fios[1]), FadeIn(taxas[1]))
        self.play(FadeIn(n1, shift=UP * 0.1))
        self.play(FadeIn(dec), Create(fios[2]), FadeIn(taxas[2]), FadeIn(y_out))
        self.play(FadeIn(n2, shift=UP * 0.1))
        p = caminho([x_in.get_right(), fir.get_center(), dec.get_center(), y_out.get_left()])
        self.play(ShowPassingFlash(p.set_stroke(WHITE, 7), time_width=0.4), run_time=1.5)
        leg = self.legenda("A primeira metade de um decimador é quase sempre um filtro FIR passa-baixa", leg, COR_FIR)
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 3
    def cena_aliasing(self):
        titulo = self.titulo_cena("3 · Por que filtrar antes: aliasing")
        M = 4
        f_util, f_ruido = 0.02, 0.3     # ciclos por amostra
        ax = Axes(x_range=[0, 0.5, 0.05], y_range=[0, 1.2, 0.5], x_length=11.5, y_length=2.0,
                  axis_config={"include_tip": True, "stroke_width": 2, "color": COR_EIXO},
                  y_axis_config={"include_tip": False}).move_to(P(0, 1.35))
        vals = [0, 0.125, 0.25, 0.375, 0.5]
        marcas = marcar_x(ax, vals, ["0", "f_s/8", "f_s/4", "3f_s/8", "f_s/2"])
        rot_f = Text("frequência", font_size=16, color=COR_EIXO).next_to(ax.x_axis.get_end(), UP, buff=0.1)
        r_util = raia(ax, f_util, 1.0, COR_SINAL)
        rr_util = Text("sinal útil", font_size=18, color=COR_SINAL).next_to(ax.c2p(f_util, 1.0), RIGHT, buff=0.1)
        r_ruido = raia(ax, f_ruido, 0.6, COR_RUIDO)
        rr_ruido = Text("ruído de alta frequência", font_size=18, color=COR_RUIDO).next_to(ax.c2p(f_ruido, 0.6),
                                                                                         UP, buff=0.08)
        nova = Polygon(ax.c2p(0, 0), ax.c2p(0, 1.15), ax.c2p(0.125, 1.15), ax.c2p(0.125, 0), stroke_width=0,
                       fill_color=COR_DEC, fill_opacity=0.15)
        l_nova = DashedLine(ax.c2p(0.125, 0), ax.c2p(0.125, 1.15), color=COR_DEC, stroke_width=3)
        r_nova = Text("nova faixa útil após ↓4: até f_s/(2M)", font_size=18, color=COR_DEC
                      ).next_to(ax.c2p(0.13, 1.15), RIGHT, buff=0.1)
        f_alias = abs(f_ruido - round(f_ruido * M) / M)    # 0,05
        r_alias = raia(ax, f_alias, 0.6, COR_RUIDO)
        rr_alias = Text("alias!", font_size=20, color=COR_RUIDO, weight=BOLD).next_to(ax.c2p(f_alias, 0.6), UP,
                                                                                      buff=0.08)

        ax_t = eixos_tempo(P(0, -1.65), 11.5, 1.9, [0, 40, 4], [-1.6, 1.6, 0.5])
        r_t = Text("n →", font_size=16, color=COR_EIXO).next_to(ax_t, DOWN, buff=0.05).align_to(ax_t, RIGHT)

        def x_sujo(n):
            return np.sin(TAU * f_util * n) + 0.6 * np.cos(TAU * f_ruido * n)

        sujo = ax_t.plot(x_sujo, x_range=[0, 40, 0.02], color=GREY_B, stroke_width=1.5).set_stroke(opacity=0.6)
        util = ax_t.plot(lambda n: np.sin(TAU * f_util * n), x_range=[0, 40, 0.05], color=COR_SINAL, stroke_width=3)
        h_sujo = VGroup(*[haste(ax_t, n, x_sujo(n), WHITE, 0.05) for n in range(41)])
        rot_t = rotulo_eixo(ax_t, Text("sinal útil (azul) + ruído rápido, amostrado", font_size=18, color=GREY_A))

        leg = self.legenda("O espectro do sinal amostrado: sinal útil em baixa frequência e ruído em alta")
        self.play(Create(ax), FadeIn(marcas), FadeIn(rot_f))
        self.play(GrowArrow(r_util), FadeIn(rr_util), GrowArrow(r_ruido), FadeIn(rr_ruido))
        leg = self.legenda("Após ↓4, só cabe de 0 a f_s/8: o resto tem de se dobrar para dentro", leg, COR_DEC)
        self.play(FadeIn(nova), Create(l_nova), FadeIn(r_nova))
        leg = self.legenda("Sem filtro, o ruído em 0,3·f_s dobra e cai em 0,05·f_s: em cima da banda útil", leg,
                           COR_RUIDO)
        self.play(ReplacementTransform(r_ruido.copy(), r_alias, path_arc=PI / 2), FadeOut(rr_ruido), run_time=2.5)
        self.play(FadeIn(rr_alias), Indicate(r_alias, color=COR_RUIDO))

        self.play(Create(ax_t), FadeIn(r_t), FadeIn(rot_t))
        self.play(Create(util), Create(sujo), run_time=1.5)
        self.play(LaggedStart(*[GrowFromPoint(h, ax_t.c2p(n, 0)) for n, h in enumerate(h_sujo)], lag_ratio=0.03))
        leg = self.legenda("Jogando fora 3 de cada 4 amostras sem filtrar…", leg)
        self.play(VGroup(*[h for n, h in enumerate(h_sujo) if n % M]).animate.set_opacity(0.1), run_time=1.2)
        guardadas = [n for n in range(41) if n % M == 0]
        falso = VMobject().set_points_smoothly([ax_t.c2p(n, x_sujo(n)) for n in guardadas]).set_stroke(COR_RUIDO, 4)
        leg = self.legenda("…as amostras restantes desenham uma onda que não é o sinal útil: ele foi destruído", leg,
                           COR_RUIDO)
        self.play(Create(falso), run_time=2)
        self.wait(1)

        self.trocar_titulo(titulo, "3 · Com o FIR antes do ↓M")
        leg = self.legenda("Com o passa-baixa primeiro, o ruído some antes do descarte", leg, COR_FIR)
        self.play(FadeOut(VGroup(r_ruido, r_alias, rr_alias)), FadeOut(VGroup(falso, sujo, h_sujo)))
        limpos = VGroup(*[haste(ax_t, n, np.sin(TAU * f_util * n), WHITE if n % M == 0 else COR_DESCARTE, 0.06)
                          for n in range(41)])
        self.play(LaggedStart(*[GrowFromPoint(h, ax_t.c2p(n, 0)) for n, h in enumerate(limpos)], lag_ratio=0.03))
        leg = self.legenda("As amostras mantidas seguem o sinal útil: a informação passou intacta", leg, COR_OK)
        self.play(Indicate(util, color=COR_SINAL, scale_factor=1.02))
        self.wait(1.5)
        self.limpar()

    # ================================================================== CENA 4
    def cena_downsampling(self):
        self.titulo_cena("4 · Downsampling: quais amostras ficam")
        M = 4
        n_tot = 16
        dx = 0.78
        x0 = -5.85
        caixas = VGroup()
        for n in range(n_tot):
            q = Square(side_length=0.6, color=COR_EIXO, stroke_width=2).move_to(P(x0 + dx * n, 1.4))
            caixas.add(VGroup(q, tex(f"x_{{{n}}}", WHITE, 24).move_to(q)))
        rot_entrada = Text(f"entrada filtrada (taxa f_s)", font_size=20, color=GREY_A).next_to(caixas, UP, buff=0.25
                                                                                              ).align_to(caixas, LEFT)
        mantidas = [c for n, c in enumerate(caixas) if n % M == 0]
        descartadas = [c for n, c in enumerate(caixas) if n % M]
        xis = VGroup(*[Cross(c, stroke_color=COR_RUIDO, stroke_width=4, scale_factor=0.6) for c in descartadas])
        saida = VGroup(*[VGroup(Square(side_length=0.6, color=COR_DEC, stroke_width=3),
                                tex(f"y_{{{k}}}", COR_DEC, 24)).move_to(P(x0 + dx * M * k, -0.9))
                         for k in range(len(mantidas))])
        for s in saida:
            s[1].move_to(s[0])
        rot_saida = Text("saída (taxa f_s / M)", font_size=20, color=COR_DEC).next_to(saida, DOWN, buff=0.25
                                                                                     ).align_to(caixas, LEFT)
        relacao = tex(r"y[m] = x[m\,M]", COR_DEC, 36).move_to(P(3.6, -2.2))

        leg = self.legenda(f"Fator de decimação M = {M}")
        self.play(LaggedStart(*[FadeIn(c, shift=DOWN * 0.1) for c in caixas], lag_ratio=0.06), FadeIn(rot_entrada))
        leg = self.legenda("Mantém a 1ª, descarta a 2ª, 3ª e 4ª, mantém a 5ª, e assim por diante", leg, COR_DEC)
        for k in range(len(mantidas)):
            grupo_desc = [descartadas[3 * k + j] for j in range(3) if 3 * k + j < len(descartadas)]
            self.play(Indicate(mantidas[k], color=COR_DEC, scale_factor=1.25), run_time=0.5)
            self.play(*[Create(xis[3 * k + j]) for j in range(len(grupo_desc))],
                      *[c.animate.set_opacity(0.3) for c in grupo_desc], run_time=0.5)
        self.play(*[TransformFromCopy(mantidas[k], saida[k]) for k in range(len(mantidas))], FadeIn(rot_saida),
                  run_time=1.5)
        self.play(Write(relacao))
        leg = self.legenda("A nova taxa de amostragem é a original dividida por M", leg)
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 5
    def cena_fpga(self):
        self.titulo_cena("5 · Por que isso é crucial em FPGAs")
        # DSP slices: um multiplicador atende M contas
        cab1 = Text("Economia de DSP slices", font_size=24, color=COR_FPGA, weight=BOLD).move_to(P(-4.5, 2.5))
        mult = VGroup(Circle(radius=0.38, color=COR_FPGA, stroke_width=3), tex(r"\times", COR_FPGA, 36)
                      ).move_to(P(-4.5, 1.1))
        contas = VGroup(*[Text(f"conta {k + 1}", font_size=16, color=GREY_A).move_to(P(-6.0 + k * 1.0, -0.15))
                          for k in range(4)])
        braco = Line(mult.get_bottom(), contas[0].get_top(), color=COR_FPGA, stroke_width=3)
        n1 = Text("taxa M vezes menor: o mesmo\nmultiplicador atende M contas", font_size=18, color=GREY_A
                  ).move_to(P(-4.5, -0.9))

        # Timing: relógios
        cab2 = Text("Fechamento de timing", font_size=24, color=COR_DEC, weight=BOLD).move_to(P(0.6, 2.5))
        rapido = relogio(-1.5, 2.7, 1.2, 0.42, COR_RUIDO)
        lento = relogio(-1.5, 2.7, 0.1, 1.68, COR_OK)
        r_rap = Text("200 MHz: 5 ns por ciclo", font_size=16, color=COR_RUIDO).next_to(rapido, UP, buff=0.1)
        r_len = Text("50 MHz: 20 ns por ciclo", font_size=16, color=COR_OK).next_to(lento, UP, buff=0.1)
        n2 = Text("depois de decimar, o resto da lógica\nroda num clock lento e folgado", font_size=18,
                  color=GREY_A).move_to(P(0.6, -0.9))

        # Energia
        cab3 = Text("Menor consumo", font_size=24, color=COR_OK, weight=BOLD).move_to(P(5.2, 2.5))
        barras = VGroup(
            Rectangle(width=0.7, height=2.2, stroke_width=0, fill_color=COR_RUIDO, fill_opacity=0.8),
            Rectangle(width=0.7, height=0.55, stroke_width=0, fill_color=COR_OK, fill_opacity=0.8),
        ).arrange(RIGHT, buff=0.6, aligned_edge=DOWN).move_to(P(5.2, 0.6))
        r_barras = VGroup(Text("f_s", font_size=16, color=COR_RUIDO).next_to(barras[0], DOWN, buff=0.1),
                          Text("f_s/M", font_size=16, color=COR_OK).next_to(barras[1], DOWN, buff=0.1))
        n3 = Text("menos transições lógicas\npor segundo = menos calor", font_size=18, color=GREY_A
                  ).move_to(P(5.2, -1.25))

        leg = self.legenda("Num chip, os recursos são finitos: decimar cedo libera todos eles")
        self.play(FadeIn(cab1), FadeIn(mult), FadeIn(contas), Create(braco))
        for k in range(1, 4):
            self.play(braco.animate.put_start_and_end_on(mult.get_bottom(), contas[k].get_top()), run_time=0.35)
        self.play(braco.animate.put_start_and_end_on(mult.get_bottom(), contas[0].get_top()), FadeIn(n1), run_time=0.5)
        leg = self.legenda("Blocos DSP (ex.: DSP48 da Xilinx) reaproveitados em sequência: menos área", leg, COR_FPGA)
        self.wait(1)
        self.play(FadeIn(cab2), Create(rapido), FadeIn(r_rap), Create(lento), FadeIn(r_len), run_time=1.5)
        self.play(FadeIn(n2))
        leg = self.legenda("Com 20 ns por ciclo fica muito mais fácil garantir que os dados cheguem a tempo", leg,
                           COR_DEC)
        self.wait(1)
        self.play(FadeIn(cab3), GrowFromEdge(barras[0], DOWN), GrowFromEdge(barras[1], DOWN), FadeIn(r_barras))
        self.play(FadeIn(n3))
        leg = self.legenda("Menos amostras por segundo: menos área, timing folgado e menos energia", leg, COR_OK)
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 6
    def cena_polifasico(self):
        self.titulo_cena("6 · A estrutura polifásica")
        Ntaps, M = 16, 4
        # Implementação ingênua
        cab_a = Text("Ingênua: FIR completo e depois ↓M", font_size=22, color=COR_RUIDO, weight=BOLD
                     ).move_to(P(-3.4, 2.55))
        fir = caixa("FIR (16 taps)\na f_s", 2.0, 0.9, COR_FIR, 18).move_to(P(-4.6, 1.5))
        dec = caixa_tex(r"\downarrow 4", 1.0, 0.9, COR_DEC, 30).move_to(P(-2.1, 1.5))
        f1 = fio([fir.get_right(), dec.get_left()])
        saidas = VGroup()
        for n in range(12):
            d = Dot(P(-5.8 + 0.4 * n, 0.45), radius=0.09, color=WHITE if n % M == 0 else COR_RUIDO)
            saidas.add(d)
        xis = VGroup(*[Cross(saidas[n], stroke_color=COR_RUIDO, stroke_width=3, scale_factor=1.6)
                       for n in range(12) if n % M])
        r_saidas = Text("saídas calculadas: 3 de cada 4 vão para o lixo", font_size=16, color=COR_RUIDO
                        ).next_to(saidas, DOWN, buff=0.15).align_to(saidas, LEFT)
        conta_a = tex(r"N = 16\ \text{multiplicações por amostra de entrada}", COR_RUIDO, 24).move_to(P(-3.4, -0.6))

        # Polifásica
        cab_b = Text("Polifásica: só o que será mantido", font_size=22, color=COR_OK, weight=BOLD).move_to(P(3.5, 2.55))
        cx, cy = 1.0, 0.0
        x_in = tex(r"x[n]", WHITE, 28).move_to(P(cx - 0.9, cy + 0.6))
        pivo = Dot(P(cx, cy), radius=0.07, color=WHITE)
        ys = [1.55, 0.55, -0.45, -1.45]
        ramos = VGroup(*[caixa_tex(rf"E_{k}:\ h[4j+{k}]", 2.0, 0.6, COR_OK, 22).move_to(P(3.2, y))
                         for k, y in enumerate(ys)])
        contatos = [P(1.9, y) for y in ys]
        soma = VGroup(Circle(radius=0.25, color=WHITE, stroke_width=3), tex(r"\Sigma", WHITE, 26)).move_to(P(5.0, 0.05))
        fios_r = VGroup(*[Line(r.get_right(), P(4.75, r.get_center()[1]), color=GREY_A, stroke_width=2) for r in ramos],
                        *[Line(P(4.75, y), soma.get_center() + 0.25 * (P(4.75, y) - soma.get_center()) /
                               np.linalg.norm(P(4.75, y) - soma.get_center()), color=GREY_A, stroke_width=2) for y in ys])
        y_out = tex(r"y[m]", COR_DEC, 28).next_to(soma, RIGHT, buff=0.5)
        f_out = fio([soma.get_right(), y_out.get_left() + LEFT * 0.05], COR_DEC, 3)
        terminais = VGroup(*[Line(c, r.get_left(), color=GREY_A, stroke_width=2) for c, r in zip(contatos, ramos)])
        braco = Line(P(cx, cy), contatos[0], color=YELLOW, stroke_width=5)
        r_ramos = Text("cada sub-filtro roda a f_s/M", font_size=16, color=COR_OK).next_to(ramos, DOWN, buff=0.15)
        conta_b = tex(r"N/M = 4\ \text{multiplicações por amostra de entrada}", COR_OK, 24).move_to(P(3.5, -2.6))

        leg = self.legenda("Implementação ingênua: o FIR calcula todas as saídas")
        self.play(FadeIn(cab_a), FadeIn(fir), Create(f1), FadeIn(dec))
        self.play(LaggedStart(*[GrowFromCenter(d) for d in saidas], lag_ratio=0.08))
        leg = self.legenda("…e o ↓M joga fora M − 1 delas: multiplicações desperdiçadas", leg, COR_RUIDO)
        self.play(Create(xis), FadeIn(r_saidas))
        self.play(Write(conta_a))
        leg = self.legenda("Polifásica: os 16 coeficientes são divididos em M = 4 sub-filtros", leg, COR_OK)
        self.play(FadeIn(cab_b), FadeIn(x_in), FadeIn(pivo), LaggedStart(*[FadeIn(r) for r in ramos], lag_ratio=0.2))
        self.play(Create(terminais), Create(fios_r), FadeIn(soma), Create(f_out), FadeIn(y_out), FadeIn(r_ramos))
        self.add(braco)
        leg = self.legenda("Um comutador entrega cada amostra de entrada a um ramo diferente", leg)
        for volta in range(2):
            for k in range(1, 5):
                alvo = contatos[k % 4]
                self.play(braco.animate.put_start_and_end_on(P(cx, cy), alvo), run_time=0.4)
            self.play(Flash(soma, color=COR_DEC), run_time=0.5)
        self.play(Write(conta_b))
        leg = self.legenda("As multiplicações só acontecem para as saídas mantidas: M vezes menos trabalho", leg,
                           COR_OK)
        self.wait(1)
        leg = self.legenda("Ferramentas como o FIR Compiler do Vivado geram essa estrutura automaticamente", leg)
        self.wait(1.8)
        self.limpar()

    # ================================================================== RESUMO
    def cena_resumo(self):
        self.titulo_cena("Resumo")
        itens = VGroup(*[Text(t, font_size=23, color=c) for t, c in [
            ("• Decimar = reduzir a taxa de amostragem: f_s → f_s/M", COR_DEC),
            ("• Etapa 1: filtro FIR passa-baixa (anti-aliasing)", COR_FIR),
            ("• Etapa 2: downsampling, manter 1 amostra a cada M", COR_DEC),
            ("• Sem o filtro, o ruído alto se dobra sobre a banda útil (aliasing)", COR_RUIDO),
            ("• Em FPGA: menos DSP slices, timing folgado e menos energia", COR_FPGA),
            ("• Polifásico: só calcula as saídas que serão mantidas (N/M por amostra)", COR_OK),
        ]]).arrange(DOWN, aligned_edge=LEFT, buff=0.32).move_to(P(0, -0.2))
        self.play(LaggedStart(*[FadeIn(t, shift=RIGHT * 0.2) for t in itens], lag_ratio=0.3), run_time=3.5)
        self.wait(3)
        self.limpar()
