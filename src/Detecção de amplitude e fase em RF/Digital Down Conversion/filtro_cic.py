# -*- coding: utf-8 -*-
"""
Filtro CIC: integrador + pente = média móvel sem multiplicadores
================================================================

Renderização (a partir da raiz do repositório):
    manim -pql "src/Detecção de amplitude e fase em RF/Digital Down Conversion/filtro_cic.py" FiltroCIC   # rascunho
    manim -pqh "src/Detecção de amplitude e fase em RF/Digital Down Conversion/filtro_cic.py" FiltroCIC   # final

Requer LaTeX (MathTex).

Roteiro (segue "docs/Detecção de amplitude e fase em RF/Digital Down Conversion/Filtro CIC"):
    Abertura
    Cena 1 - Estrutura: integrador (acumula) e comb (subtrai o passado), sem multiplicadores
    Cena 2 - O integrador: soma de todo o histórico, I[4] = x[4] + … + x[0]
    Cena 3 - O comb: y[n] = I[n] − I[n−4] corta o passado e deixa uma janela de 4 amostras
    Cena 4 - O efeito de filtragem: +1 −1 +1 −1 → 0 e +1 +1 +1 +1 → 4
    Cena 5 - Média móvel na prática: sinal ruidoso, saída suave e resposta em frequência
    Cena 6 - Com o decimador entre os dois: o comb olha 1 amostra lenta = 4 rápidas
    Resumo

Exemplo usado em todas as cenas: atraso do comb D = 4 (janela de 4 amostras).
"""

import numpy as np
from manim import *

# Paleta didática (fixa em todas as cenas)
COR_X = BLUE             # entrada x[n]
COR_INT = GOLD           # integrador I[n]
COR_COMB = TEAL          # comb / saída y[n]
COR_JANELA = YELLOW      # janela de 4 amostras
COR_RUIDO = RED          # alta frequência / ruído
COR_LENTO = GREEN        # baixa frequência / sinal útil
COR_DEC = PINK           # decimador
COR_EIXO = GREY_B
FUNDO = "#0e1117"

EIXO_CFG = {"include_tip": False, "stroke_width": 2, "color": COR_EIXO}
D = 4                                    # atraso diferencial do comb
X_EXEMPLO = [2, 1, 3, 1, 2, 3, 1, 2]     # entrada numérica das cenas 2 e 3


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
    g = VGroup(*[Line(pontos[k], pontos[k + 1], color=cor, stroke_width=largura) for k in range(len(pontos) - 2)])
    g.add(Arrow(pontos[-2], pontos[-1], buff=0, color=cor, stroke_width=largura,
                max_tip_length_to_length_ratio=0.25, max_stroke_width_to_length_ratio=10))
    return g


def caminho(pontos):
    return VMobject().set_points_as_corners(pontos)


def caixa(rotulo, largura=1.6, altura=0.8, cor=WHITE, tamanho=22):
    r = RoundedRectangle(corner_radius=0.1, width=largura, height=altura, color=cor, stroke_width=3)
    return VGroup(r, Text(rotulo, font_size=tamanho, color=cor).move_to(r))


def caixa_tex(rotulo, largura=1.0, altura=0.7, cor=WHITE, tamanho=30):
    r = RoundedRectangle(corner_radius=0.1, width=largura, height=altura, color=cor, stroke_width=3)
    return VGroup(r, tex(rotulo, cor, tamanho).move_to(r))


def somador(sinais="++", cor=WHITE, raio=0.28):
    c = Circle(radius=raio, color=cor, stroke_width=3)
    return VGroup(c, tex(r"\Sigma", cor, 26).move_to(c))


def eixos_tempo(centro, largura, altura, x_range, y_range):
    return Axes(x_range=x_range, y_range=y_range, x_length=largura, y_length=altura,
                axis_config=EIXO_CFG).move_to(centro)


def rotulo_eixo(ax, mob):
    """Coloca um rótulo acima do canto esquerdo de um eixo."""
    return mob.next_to(ax, UP, buff=0.04).align_to(ax, LEFT)


def haste(ax, x, y, cor, raio=0.06, largura=2):
    return VGroup(Line(ax.c2p(x, 0), ax.c2p(x, y), color=cor, stroke_width=largura),
                  Dot(ax.c2p(x, y), radius=raio, color=cor))


def integrar(x):
    return list(np.cumsum(x))


def comb(I, d=D):
    return [I[n] - (I[n - d] if n >= d else 0) for n in range(len(I))]


# =============================================================================
# Cena
# =============================================================================
class FiltroCIC(Scene):
    def construct(self):
        self.camera.background_color = FUNDO
        self.abertura()
        self.cena_estrutura()
        self.cena_integrador()
        self.cena_comb()
        self.cena_cancelamento()
        self.cena_media_movel()
        self.cena_decimacao()
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

    def tabela(self, linhas, x0=-4.7, dx=1.2, y0=2.35, dy=0.62):
        """Tabela de valores por instante n. linhas = [(rotulo_tex, cor, valores ou None), ...]."""
        n_col = len(X_EXEMPLO)
        cab = VGroup(*[tex(f"{n}", GREY_B, 26).move_to(P(x0 + dx * n, y0)) for n in range(n_col)])
        r_cab = tex("n", GREY_B, 26).move_to(P(x0 - 1.3, y0))
        rotulos, celulas = VGroup(r_cab), [cab]
        for k, (rot, cor, vals) in enumerate(linhas):
            y = y0 - dy * (k + 1)
            rotulos.add(tex(rot, cor, 26).move_to(P(x0 - 1.3, y)))
            celulas.append(VGroup(*[tex(f"{v}", cor, 28).move_to(P(x0 + dx * n, y)) for n, v in enumerate(vals)])
                           if vals is not None else VGroup())
        sep = Line(P(x0 - 1.8, y0 - dy / 2), P(x0 + dx * (n_col - 0.5), y0 - dy / 2), color=COR_EIXO, stroke_width=1.5)
        return rotulos, celulas, sep

    # ---------------------------------------------------------------- abertura
    def abertura(self):
        titulo = Text("Filtro CIC", font_size=64, weight=BOLD)
        sub = Text("Cascaded Integrator–Comb: média móvel sem nenhum multiplicador", font_size=28, color=GREY_A)
        cadeia = VGroup(tex(r"x[n]", COR_X, 32), tex(r"\rightarrow", GREY_A, 32),
                        caixa("Integrador", 1.9, 0.6, COR_INT, 20), tex(r"\rightarrow", GREY_A, 32),
                        caixa("Comb", 1.3, 0.6, COR_COMB, 20), tex(r"\rightarrow", GREY_A, 32),
                        tex(r"y[n]", COR_COMB, 32)).arrange(RIGHT, buff=0.25)
        g = VGroup(titulo, sub, cadeia).arrange(DOWN, buff=0.4)
        self.play(Write(titulo), run_time=1.5)
        self.play(FadeIn(sub, shift=UP * 0.2), FadeIn(cadeia, shift=UP * 0.2))
        self.wait(1.2)
        self.play(FadeOut(g))

    # ================================================================== CENA 1
    def cena_estrutura(self):
        self.titulo_cena("1 · Estrutura: integrador + comb")
        y0 = 0.9
        x_in = tex(r"x[n]", COR_X, 32).move_to(P(-6.2, y0))
        s_int = somador().move_to(P(-4.3, y0))
        no_int = Dot(P(-2.7, y0), radius=0.06, color=COR_INT)
        z1 = caixa_tex(r"z^{-1}", 1.0, 0.6, COR_INT, 28).move_to(P(-3.5, -0.4))
        f_int = VGroup(
            fio([x_in.get_right() + RIGHT * 0.1, s_int.get_left()], COR_X),
            Line(s_int.get_right(), no_int.get_center(), color=COR_INT, stroke_width=3),
            fio([no_int.get_center(), P(-2.7, -0.4), z1.get_right()], COR_INT),
            fio([z1.get_left(), P(-4.3, -0.4), s_int.get_bottom()], COR_INT),
        )
        r_i = tex(r"I[n]", COR_INT, 28).next_to(no_int, UP, buff=0.12)
        caixa_int = DashedVMobject(RoundedRectangle(corner_radius=0.15, width=3.3, height=2.6), num_dashes=50
                                   ).set_stroke(COR_INT, 2).move_to(P(-3.6, 0.3))
        cab_int = Text("Integrador", font_size=22, color=COR_INT, weight=BOLD).next_to(caixa_int, UP, buff=0.08)
        eq_int = tex(r"I[n] = I[n-1] + x[n]", COR_INT, 30).next_to(caixa_int, DOWN, buff=0.25)

        s_comb = VGroup(Circle(radius=0.28, color=COR_COMB, stroke_width=3), tex(r"\Sigma", COR_COMB, 26)
                        ).move_to(P(2.4, y0))
        no_comb = Dot(P(0.2, y0), radius=0.06, color=COR_INT)
        zd = caixa_tex(r"z^{-4}", 1.0, 0.6, COR_COMB, 28).move_to(P(1.3, -0.4))
        y_out = tex(r"y[n]", COR_COMB, 32).move_to(P(4.3, y0))
        f_comb = VGroup(
            fio([no_int.get_center(), no_comb.get_center()], COR_INT),
            fio([no_comb.get_center(), s_comb.get_left()], COR_INT),
            fio([no_comb.get_center(), P(0.2, -0.4), zd.get_left()], COR_INT),
            fio([zd.get_right(), P(2.4, -0.4), s_comb.get_bottom()], COR_INT),
            fio([s_comb.get_right(), y_out.get_left() + LEFT * 0.1], COR_COMB),
        )
        sinais = VGroup(tex("+", WHITE, 26).move_to(s_comb.get_center() + P(-0.45, 0.28)),
                        tex("-", COR_RUIDO, 34).move_to(s_comb.get_center() + P(-0.3, -0.45)))
        caixa_comb = DashedVMobject(RoundedRectangle(corner_radius=0.15, width=3.4, height=2.6), num_dashes=50
                                    ).set_stroke(COR_COMB, 2).move_to(P(1.4, 0.3))
        cab_comb = Text("Comb (pente)", font_size=22, color=COR_COMB, weight=BOLD).next_to(caixa_comb, UP, buff=0.08)
        eq_comb = tex(r"y[n] = I[n] - I[n-4]", COR_COMB, 30).next_to(caixa_comb, DOWN, buff=0.25)
        destaque = Text("só somas, subtrações e atrasos: nenhum multiplicador", font_size=22, color=COR_JANELA
                        ).move_to(P(0, -2.65))

        leg = self.legenda("Duas partes em cascata: um integrador seguido de um comb")
        self.play(FadeIn(x_in), FadeIn(s_int), Create(f_int), FadeIn(no_int), FadeIn(z1), FadeIn(r_i), run_time=1.5)
        self.play(Create(caixa_int), FadeIn(cab_int), Write(eq_int))
        leg = self.legenda("O integrador acumula: soma a entrada nova ao valor anterior", leg, COR_INT)
        self.play(ShowPassingFlash(caminho([no_int.get_center(), P(-2.7, -0.4), P(-4.3, -0.4),
                                            s_int.get_center(), no_int.get_center()]).set_stroke(YELLOW, 6),
                                   time_width=0.5), run_time=1.5)
        leg = self.legenda("O comb subtrai do valor atual o valor de 4 amostras atrás", leg, COR_COMB)
        self.play(FadeIn(no_comb), FadeIn(s_comb), Create(f_comb), FadeIn(zd), FadeIn(sinais), FadeIn(y_out),
                  run_time=1.5)
        self.play(Create(caixa_comb), FadeIn(cab_comb), Write(eq_comb))
        leg = self.legenda("Por isso é tão barato em FPGA e ASIC: decima (ou interpola) antes dos filtros FIR", leg)
        self.play(Write(destaque))
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 2
    def cena_integrador(self):
        self.titulo_cena("2 · O integrador: guarda tudo o que entra")
        I = integrar(X_EXEMPLO)
        rotulos, celulas, sep = self.tabela([(r"x[n]", COR_X, X_EXEMPLO), (r"I[n]", COR_INT, I)])
        self.play(FadeIn(rotulos[0]), FadeIn(celulas[0]), Create(sep))
        self.play(FadeIn(rotulos[1]), LaggedStart(*[FadeIn(c, shift=DOWN * 0.1) for c in celulas[1]], lag_ratio=0.1))
        self.play(FadeIn(rotulos[2]))

        base_y, esc = -2.55, 0.15
        x0, dx = -4.7, 1.2
        barras = VGroup()
        limite = DashedLine(P(-5.4, base_y + 12 * esc), P(4.4, base_y + 12 * esc), color=COR_RUIDO, stroke_width=2)
        r_lim = Text("limite do registrador", font_size=16, color=COR_RUIDO).next_to(limite, RIGHT, buff=0.1)
        chao = Line(P(-5.4, base_y), P(4.4, base_y), color=COR_EIXO, stroke_width=2)

        leg = self.legenda("A cada instante: valor anterior + amostra nova")
        self.play(Create(chao))
        for n in range(len(X_EXEMPLO)):
            b = Rectangle(width=0.6, height=max(I[n] * esc, 0.01), stroke_width=0, fill_color=COR_INT,
                          fill_opacity=0.8).move_to(P(x0 + dx * n, base_y), aligned_edge=DOWN)
            barras.add(b)
            anims = [FadeIn(celulas[2][n], shift=DOWN * 0.1), GrowFromEdge(b, DOWN)]
            if n > 0:
                anims.append(Indicate(celulas[2][n - 1], color=WHITE, scale_factor=1.2))
            self.play(*anims, Indicate(celulas[1][n], color=WHITE, scale_factor=1.2), run_time=0.7)
            if n == 4:
                caixa4 = SurroundingRectangle(VGroup(celulas[1][0], celulas[1][4]), color=COR_JANELA, buff=0.12)
                f4 = tex(r"I[4] = x[4] + x[3] + x[2] + x[1] + x[0] = 9", COR_INT, 32).move_to(P(3.0, 0.15))
                leg = self.legenda("I[4] é a soma de todo o passado desde que o sistema ligou", leg, COR_INT)
                self.play(Create(caixa4), Write(f4))
                self.wait(1)
                self.play(FadeOut(caixa4))
        leg = self.legenda("Sozinho ele não filtra nada: só cresce sem parar", leg, COR_RUIDO)
        self.play(Create(limite), FadeIn(r_lim))
        nota = Text("o estouro (overflow) é proposital: em aritmética de complemento de dois\n"
                    "o comb desfaz o estouro e a saída final continua correta", font_size=18, color=GREY_A
                    ).move_to(P(0, 0.15))
        leg = self.legenda("Em hardware o acumulador transborda de propósito no limite de bits", leg)
        self.play(FadeOut(f4), FadeIn(nota))
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 3
    def cena_comb(self):
        self.titulo_cena("3 · O comb: puxa o freio")
        I = integrar(X_EXEMPLO)
        y = comb(I)
        rotulos, celulas, sep = self.tabela([(r"x[n]", COR_X, X_EXEMPLO), (r"I[n]", COR_INT, I),
                                             (r"y[n]", COR_COMB, y)])
        self.play(FadeIn(rotulos[:3]), FadeIn(celulas[0]), FadeIn(celulas[1]), FadeIn(celulas[2]), Create(sep))
        self.play(FadeIn(rotulos[3]))

        d1 = tex(r"y[n] = I[n] - I[n-4]", COR_COMB, 34).move_to(P(0, -0.35))
        d2 = tex_partes([(r"y[4] = ", WHITE), (r"(x_4 + x_3 + x_2 + x_1 + x_0)", COR_INT), (r" - ", WHITE),
                         (r"(x_0)", COR_INT)], 34).move_to(P(0, -1.15))
        d3 = tex(r"y[4] = x_4 + x_3 + x_2 + x_1", COR_COMB, 34).move_to(P(0, -1.95))

        leg = self.legenda("O comb olha o valor acumulado agora e subtrai o de 4 amostras atrás")
        self.play(Write(d1))
        self.play(Write(d2), run_time=1.5)
        risco = VGroup(Line(d2[1][-3].get_corner(DL), d2[1][-3].get_corner(UR), color=COR_RUIDO, stroke_width=4),
                       Line(d2[3][1:3].get_corner(DL), d2[3][1:3].get_corner(UR), color=COR_RUIDO, stroke_width=4))
        leg = self.legenda("O x[0] aparece dos dois lados e se anula: o passado distante é cortado", leg, COR_RUIDO)
        self.play(Create(risco))
        self.play(TransformFromCopy(d2, d3), run_time=1.5)
        leg = self.legenda("Sobra uma janela limitada e precisa de 4 amostras", leg, COR_JANELA)
        self.play(Create(SurroundingRectangle(d3, color=COR_COMB, buff=0.12)))

        x0, dx, y0, dy = -4.7, 1.2, 2.35, 0.62
        janela = Rectangle(width=dx * 4 - 0.2, height=0.55, color=COR_JANELA, stroke_width=3)
        janela.move_to(P(x0 + dx * 1.5, y0 - dy))
        self.play(Create(janela))
        for n in range(3, len(X_EXEMPLO)):
            self.play(janela.animate.move_to(P(x0 + dx * (n - 1.5), y0 - dy)), run_time=0.5)
            self.play(FadeIn(celulas[3][n], shift=DOWN * 0.1), Indicate(celulas[3][n], color=COR_JANELA), run_time=0.6)
        self.play(FadeIn(celulas[3][:3]))
        leg = self.legenda("Cada saída é a soma das 4 entradas dentro da janela", leg, COR_COMB)
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 4
    def cena_cancelamento(self):
        self.titulo_cena("4 · O efeito de filtragem")
        casos = [
            ("Ruído de alta frequência", [1, -1, 1, -1, 1, -1, 1, -1, 1, -1, 1, -1], COR_RUIDO, 1.2),
            ("Sinal de baixa frequência", [1] * 12, COR_LENTO, -1.55),
        ]
        grupos = []
        for nome, seq, cor, yc in casos:
            ax = eixos_tempo(P(-1.6, yc), 8.6, 1.8, [0, 12, 1], [-1.3, 1.3, 1])
            cab = Text(nome, font_size=22, color=cor, weight=BOLD).next_to(ax, UP, buff=0.08).align_to(ax, LEFT)
            hs = VGroup(*[haste(ax, n + 0.5, v, cor, 0.07, 3) for n, v in enumerate(seq)])
            grupos.append((ax, cab, hs, seq, cor, yc))

        leg = self.legenda("A janela de 4 amostras soma o que está dentro dela")
        for ax, cab, hs, seq, cor, yc in grupos:
            self.play(Create(ax), FadeIn(cab), LaggedStart(*[GrowFromPoint(h, h[0].get_start()) for h in hs],
                                                           lag_ratio=0.06), run_time=1.5)

        trackers = []
        for ax, cab, hs, seq, cor, yc in grupos:
            pos = ValueTracker(3)
            trackers.append(pos)

            def janela(ax=ax, pos=pos):
                p = int(round(pos.get_value()))
                return Rectangle(width=ax.c2p(4, 0)[0] - ax.c2p(0, 0)[0], height=1.95, color=COR_JANELA,
                                 stroke_width=3).move_to(P((ax.c2p(p - 3, 0)[0] + ax.c2p(p + 1, 0)[0]) / 2,
                                                           ax.get_center()[1]))

            def soma(ax=ax, pos=pos, seq=seq, cor=cor, yc=yc):
                p = int(round(pos.get_value()))
                s = sum(seq[p - 3:p + 1])
                termos = " ".join(f"{v:+d}" for v in seq[p - 3:p + 1])
                return VGroup(Text(f"{termos}", font_size=22, color=cor),
                              Text(f"= {s}", font_size=34, color=COR_JANELA, weight=BOLD)
                              ).arrange(DOWN, buff=0.15).move_to(P(5.0, yc))

            self.add(always_redraw(janela), always_redraw(soma))
        leg = self.legenda("Alternância rápida: picos e vales entram juntos na soma e se cancelam (0)", leg, COR_RUIDO)
        self.wait(1)
        leg = self.legenda("Variação lenta: nada para cancelar; a soma acumula (4 = ganho intrínseco)", leg, COR_LENTO)
        self.wait(1)
        leg = self.legenda("A janela desliza e o resultado não muda: o ruído é barrado, o sinal passa", leg)
        self.play(*[t.animate.set_value(11) for t in trackers], run_time=4, rate_func=linear)
        self.wait(1.2)
        self.limpar()

    # ================================================================== CENA 5
    def cena_media_movel(self):
        self.titulo_cena("5 · Uma média móvel: um passa-baixa")
        rng = np.random.default_rng(5)
        nmax = 60
        n = np.arange(nmax)
        lento = 1.0 * np.sin(TAU * n / 40)
        x = lento + 0.45 * rng.standard_normal(nmax)
        y = np.array([x[max(0, k - D + 1):k + 1].sum() for k in range(nmax)]) / D
        ax = eixos_tempo(P(-3.1, 0.1), 7.4, 3.6, [0, 60, 10], [-2.2, 2.2, 1])
        r_ax = rotulo_eixo(ax, Text("entrada ruidosa (azul) e saída do CIC ÷ 4 (verde)", font_size=18, color=GREY_A))
        c_x = VMobject().set_points_as_corners([ax.c2p(k, v) for k, v in zip(n, x)]).set_stroke(COR_X, 2)
        c_y = VMobject().set_points_as_corners([ax.c2p(k, v) for k, v in zip(n, y)]).set_stroke(COR_LENTO, 5)

        ax_f = Axes(x_range=[0, 0.5, 0.125], y_range=[0, 4.4, 1], x_length=4.6, y_length=3.0,
                    axis_config=EIXO_CFG).move_to(P(4.3, 0.1))
        r_axf = rotulo_eixo(ax_f, tex(r"|H(f)| = \left|\frac{\sin(4\pi f)}{\sin(\pi f)}\right|", WHITE, 26))
        marcas = VGroup(*[Text(t, font_size=14, color=COR_EIXO).next_to(ax_f.c2p(v, 0), DOWN, buff=0.08)
                          for v, t in [(0, "0"), (0.25, "f_s/4"), (0.5, "f_s/2")]])
        resp = ax_f.plot(lambda f: abs(np.sin(4 * PI * f) / np.sin(PI * f)) if f > 1e-4 else 4.0,
                         x_range=[0, 0.5, 0.002], color=COR_COMB, stroke_width=4)
        p_dc = VGroup(Dot(ax_f.c2p(0, 4), radius=0.08, color=COR_LENTO),
                      Text("+1 +1 +1 +1 → 4", font_size=14, color=COR_LENTO).next_to(ax_f.c2p(0, 4), RIGHT, buff=0.1))
        p_n = VGroup(Dot(ax_f.c2p(0.5, 0), radius=0.08, color=COR_RUIDO),
                     Text("+1 −1 +1 −1 → 0", font_size=14, color=COR_RUIDO).move_to(ax_f.c2p(0.42, 1.5)))
        p_q = VGroup(Dot(ax_f.c2p(0.25, 0), radius=0.08, color=COR_RUIDO),
                     Text("+1 0 −1 0 → 0", font_size=14, color=COR_RUIDO).move_to(ax_f.c2p(0.2, 2.3)))

        leg = self.legenda("Integrador + comb formam uma soma em janela: uma média móvel")
        self.play(Create(ax), FadeIn(r_ax))
        self.play(Create(c_x), run_time=2)
        leg = self.legenda("Os espinhos rápidos se diluem na soma; a variação lenta sobrevive", leg, COR_LENTO)
        self.play(Create(c_y), run_time=2.5)
        leg = self.legenda("Na frequência: ganho 4 em DC e zeros onde o padrão se cancela na janela", leg, COR_COMB)
        self.play(Create(ax_f), FadeIn(r_axf), FadeIn(marcas))
        self.play(Create(resp), run_time=2)
        self.play(FadeIn(p_dc), FadeIn(p_n), FadeIn(p_q))
        leg = self.legenda("É um filtro passa-baixa feito só de somas e subtrações", leg)
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 6
    def cena_decimacao(self):
        self.titulo_cena("6 · E onde entra o decimador?")
        y0 = 2.2
        x_in = tex(r"x[n]", COR_X, 28).move_to(P(-6.3, y0))
        integ = caixa("Integrador\n(rápido: f_s)", 2.0, 0.8, COR_INT, 16).move_to(P(-4.2, y0))
        dec = caixa_tex(r"\downarrow 4", 1.0, 0.8, COR_DEC, 30).move_to(P(-1.9, y0))
        cb = caixa("Comb com z⁻¹\n(lento: f_s/4)", 2.2, 0.8, COR_COMB, 16).move_to(P(0.6, y0))
        y_out = tex(r"y[m]", COR_COMB, 28).move_to(P(2.6, y0))
        fios = VGroup(fio([x_in.get_right() + RIGHT * 0.08, integ.get_left()]), fio([integ.get_right(), dec.get_left()]),
                      fio([dec.get_right(), cb.get_left()]), fio([cb.get_right(), y_out.get_left() + LEFT * 0.08]))
        eq = tex(r"I_{lento}[m] - I_{lento}[m-1] = I[4m] - I[4m-4]", COR_COMB, 30).move_to(P(0, 1.1))

        rng = np.random.default_rng(2)
        xs = list(rng.integers(0, 4, 16))
        I = integrar(xs)
        ax = eixos_tempo(P(-0.6, -1.05), 11.8, 2.6, [0, 16, 1], [0, max(I) + 2, 5])
        r_ax = rotulo_eixo(ax, Text("I[n] no tempo rápido (todas as amostras)", font_size=18, color=COR_INT))
        hs = VGroup(*[haste(ax, k + 1, I[k], COR_INT, 0.06, 3) for k in range(16)])
        lentas = [k for k in range(16) if (k + 1) % 4 == 0]

        leg = self.legenda("Em hardware, o decimador fica entre o integrador e o comb")
        self.play(FadeIn(x_in), FadeIn(integ), FadeIn(dec), FadeIn(cb), FadeIn(y_out), Create(fios), run_time=1.5)
        leg = self.legenda("O integrador acumula na taxa rápida", leg, COR_INT)
        self.play(Create(ax), FadeIn(r_ax))
        self.play(LaggedStart(*[GrowFromPoint(h, ax.c2p(k + 1, 0)) for k, h in enumerate(hs)], lag_ratio=0.06),
                  run_time=1.8)
        leg = self.legenda("↓4: o comb só enxerga 1 de cada 4 valores (tempo lento)", leg, COR_DEC)
        self.play(*[hs[k].animate.set_opacity(0.15) for k in range(16) if k not in lentas],
                  *[hs[k].animate.set_color(COR_DEC) for k in lentas], run_time=1.2)
        leg = self.legenda("Olhando só 1 amostra lenta para trás, ele subtrai 4 amostras rápidas atrás", leg, COR_COMB)
        self.play(Write(eq), run_time=1.5)
        blocos = VGroup()
        for j, k in enumerate(lentas):
            ini = k - 3
            chave = BraceBetweenPoints(ax.c2p(ini + 0.6, -0.3), ax.c2p(k + 1.4, -0.3), DOWN, color=COR_COMB)
            soma = sum(xs[ini:k + 1])
            r = tex(rf"y[{j}] = {soma}", COR_COMB, 24).next_to(chave, DOWN, buff=0.05)
            blocos.add(VGroup(chave, r))
            dif = Arrow(ax.c2p(k + 1, I[k - 4] if k >= 4 else 0), ax.c2p(k + 1, I[k]), buff=0, color=COR_COMB,
                        stroke_width=4, max_tip_length_to_length_ratio=0.15)
            self.play(GrowArrow(dif), FadeIn(blocos[-1]), run_time=0.8)
        leg = self.legenda("Cada saída é a soma de um bloco de 4 entradas: o mesmo resultado, a 1/4 da taxa", leg,
                           COR_COMB)
        self.wait(1.2)
        leg = self.legenda("Na interpolação a ordem se inverte: comb → ↑R → integrador", leg, GREY_A)
        self.wait(1.8)
        self.limpar()

    # ================================================================== RESUMO
    def cena_resumo(self):
        self.titulo_cena("Resumo")
        itens = VGroup(*[Text(t, font_size=23, color=c) for t, c in [
            ("• CIC = integrador + comb em cascata, sem multiplicadores", WHITE),
            ("• Integrador: soma todo o histórico, I[n] = I[n−1] + x[n]", COR_INT),
            ("• Comb: y[n] = I[n] − I[n−D] corta o passado e deixa uma janela de D amostras", COR_COMB),
            ("• Janela = média móvel: +1 −1 +1 −1 → 0, +1 +1 +1 +1 → 4", COR_JANELA),
            ("• Passa-baixa com ganho D em DC e zeros em múltiplos de f_s/D", COR_LENTO),
            ("• Decimador entre os dois: o comb roda na taxa lenta com atraso de 1", COR_DEC),
        ]]).arrange(DOWN, aligned_edge=LEFT, buff=0.32).move_to(P(0, -0.2))
        self.play(LaggedStart(*[FadeIn(t, shift=RIGHT * 0.2) for t in itens], lag_ratio=0.3), run_time=3.5)
        self.wait(3)
        self.limpar()
