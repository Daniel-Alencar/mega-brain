# -*- coding: utf-8 -*-
"""
DSP 1/7 — Fundamentos de Sinais e Sistemas Discretos no Tempo
=============================================================

Renderização (a partir da raiz do repositório):
    manim -pql "src/DSP/1 - Fundamentos de Sinais e Sistemas Discretos/fundamentos_sinais_discretos.py" FundamentosSinaisDiscretos
    manim -pqh "src/DSP/1 - Fundamentos de Sinais e Sistemas Discretos/fundamentos_sinais_discretos.py" FundamentosSinaisDiscretos

Requer LaTeX (MathTex).

Roteiro (segue "docs/DSP/Tópicos/Tópicos.md", seção 1):
    Abertura
    Cena 1 - Do contínuo ao discreto: x[n] e o índice inteiro
    Cena 2 - Impulso e degrau: δ[n], u[n] e a relação entre os dois
    Cena 3 - Exponenciais e senoides discretas: as duas armadilhas
    Cena 4 - Decomposição em impulsos: x[n] = Σ x[k]·δ[n−k]
    Cena 5 - Linearidade e invariância no tempo (com contraexemplos)
    Cena 6 - Causalidade e estabilidade BIBO
    Cena 7 - Resposta ao impulso e convolução (flip-and-slide)
    Cena 8 - Equações às diferenças (LCCDE): FIR × IIR
    Resumo

Layout: a tela é dividida em faixas fixas para que nada se sobreponha.
    y > 3.0            : título da cena (canto superior esquerdo)
    [Y_BASE, Y_TOPO]   : área de conteúdo
    y ≈ -3.5           : narração, uma linha por vez
"""

import numpy as np
from manim import *

# Paleta didática (fixa em todas as cenas)
COR_X = BLUE_C           # entrada x[n]
COR_Y = GREEN            # saída y[n]
COR_H = GOLD             # resposta ao impulso h[n]
COR_IMP = PURPLE_B       # impulso unitário
COR_DEG = TEAL           # degrau unitário
COR_ERRO = RED           # contraexemplos
COR_OK = GREEN_B         # conclusões
COR_EIXO = GREY_B
FUNDO = "#0e1117"

EIXO_CFG = {"include_tip": False, "stroke_width": 2, "color": COR_EIXO}

Y_TOPO = 2.70            # nada acima disto: a linha do título mora em ~3.1
Y_BASE = -2.55           # nada abaixo disto: a narração mora em ~-3.5
LARG_MAX = 12.6


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


def caixa_texto(rotulo, largura=1.8, altura=0.8, cor=WHITE, tamanho=24):
    r = RoundedRectangle(corner_radius=0.08, width=largura, height=altura,
                         color=cor, stroke_width=3)
    return VGroup(r, Text(rotulo, color=cor, font_size=tamanho).move_to(r))


def caixa_tex(rotulo, largura=1.8, altura=0.8, cor=WHITE, tamanho=28):
    r = RoundedRectangle(corner_radius=0.08, width=largura, height=altura,
                         color=cor, stroke_width=3)
    return VGroup(r, tex(rotulo, cor, tamanho).move_to(r))


def fio(a, b, cor=WHITE, largura=3):
    return Arrow(a, b, buff=0, color=cor, stroke_width=largura,
                 max_tip_length_to_length_ratio=0.25,
                 max_stroke_width_to_length_ratio=10)


def eixo_n(centro, largura, altura, n0, n1, ymin, ymax):
    """Eixo para sequências: n inteiro no eixo horizontal."""
    return Axes(x_range=[n0, n1, 1], y_range=[ymin, ymax, 1],
                x_length=largura, y_length=altura,
                axis_config=EIXO_CFG).move_to(centro)


def marcar_n(ax, ns, tamanho=17, y=0):
    return VGroup(*[Text(str(int(n)), font_size=tamanho, color=GREY_B)
                    .next_to(ax.c2p(n, y), DOWN, buff=0.14) for n in ns])


def haste(ax, n, valor, cor, raio=0.07, largura=3):
    """Uma amostra: traço vertical mais bolinha na ponta."""
    return VGroup(Line(ax.c2p(n, 0), ax.c2p(n, valor), color=cor,
                       stroke_width=largura),
                  Dot(ax.c2p(n, valor), radius=raio, color=cor))


def hastes(ax, ns, valores, cor, raio=0.07, largura=3):
    return VGroup(*[haste(ax, n, v, cor, raio, largura)
                    for n, v in zip(ns, valores)])


def curva(ax, func, cor, largura=3, n=500):
    xs = np.linspace(ax.x_range[0], ax.x_range[1], n)
    return (VMobject()
            .set_points_as_corners([ax.c2p(a, b) for a, b in zip(xs, func(xs))])
            .set_stroke(cor, largura))


def convolucao(x, h):
    """Convolução linear discreta, do jeito mais literal possível."""
    y = np.zeros(len(x) + len(h) - 1)
    for k, xk in enumerate(x):
        for j, hj in enumerate(h):
            y[k + j] += xk * hj
    return y


# =============================================================================
# Cena
# =============================================================================
class FundamentosSinaisDiscretos(Scene):
    def construct(self):
        self.camera.background_color = FUNDO
        self.abertura()
        self.cena_discreto()
        self.cena_impulso_degrau()
        self.cena_exponenciais()
        self.cena_decomposicao()
        self.cena_linearidade()
        self.cena_causal_estavel()
        self.cena_convolucao()
        self.cena_lccde()
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
        """Narração no rodapé, com tempo de leitura antes de prosseguir."""
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

    def revelar(self, itens, pausa=0.9, desloc=RIGHT * 0.2, run_time=0.8):
        """Mostra uma lista item a item, com pausa para leitura."""
        for item in itens:
            self.play(FadeIn(item, shift=desloc), run_time=run_time)
            self.wait(pausa)

    # ---------------------------------------------------------------- abertura
    def abertura(self):
        serie = Text("DSP · 1 de 7", font_size=26, color=GREY_A)
        titulo = Text("Fundamentos de Sinais\ne Sistemas Discretos",
                      font_size=56, weight=BOLD, line_spacing=0.9)
        eq = tex_partes([(r"y[n] = \sum_{k} ", WHITE), (r"h[k]", COR_H),
                         (r"\,", WHITE), (r"x[n-k]", COR_X)], 40)
        g = VGroup(serie, titulo, eq).arrange(DOWN, buff=0.5)
        self.play(FadeIn(serie), run_time=0.8)
        self.play(Write(titulo), run_time=2.0)
        self.wait(1.0)
        self.play(FadeIn(eq, shift=UP * 0.2), run_time=1.2)
        self.wait(2.2)
        self.play(FadeOut(g), run_time=0.9)

    # ================================================================== CENA 1
    def cena_discreto(self):
        self.titulo_cena("1 · Do contínuo ao discreto")

        ax_c = eixo_n(P(0.2, 1.55), 11.0, 1.8, 0, 12, -1.3, 1.3)
        rot_c = Text("x(t): existe em todo instante", font_size=21,
                     color=GREY_A).next_to(ax_c, UP, buff=0.1)\
            .align_to(ax_c, LEFT)
        onda = curva(ax_c, lambda t: np.sin(2 * np.pi * t / 8), COR_X, 4)

        leg = self.legenda("No mundo analógico, o sinal tem um valor para "
                           "cada instante de tempo")
        self.play(Create(ax_c), FadeIn(rot_c), run_time=1.0)
        self.play(Create(onda), run_time=2.2)
        self.wait(1.4)

        leg = self.legenda("O ADC só olha o sinal de tempos em tempos, "
                           "a cada período T", leg, COR_H)
        ns = np.arange(0, 13)
        vals = np.sin(2 * np.pi * ns / 8)
        marcas_t = VGroup(*[DashedLine(ax_c.c2p(n, 0), ax_c.c2p(n, v),
                                       color=COR_H, stroke_width=2)
                            for n, v in zip(ns, vals)])
        pontos = VGroup(*[Dot(ax_c.c2p(n, v), radius=0.07, color=COR_H)
                          for n, v in zip(ns, vals)])
        self.play(LaggedStart(*[Create(m) for m in marcas_t], lag_ratio=0.12),
                  run_time=2.0)
        self.play(LaggedStart(*[GrowFromCenter(p) for p in pontos],
                              lag_ratio=0.12), run_time=1.6)
        self.wait(1.2)

        ax_d = eixo_n(P(0.2, -1.35), 11.0, 1.8, 0, 12, -1.3, 1.3)
        rot_d = Text("x[n]: só existe para n inteiro", font_size=21,
                     color=COR_X).next_to(ax_d, UP, buff=0.1)\
            .align_to(ax_d, LEFT)
        num_n = marcar_n(ax_d, ns)
        seq = hastes(ax_d, ns, vals, COR_X)

        leg = self.legenda("O que sobra é uma sequência de números, "
                           "indexada por n", leg, COR_X)
        self.play(Create(ax_d), FadeIn(rot_d), FadeIn(num_n), run_time=1.0)
        self.play(LaggedStart(*[TransformFromCopy(p, s)
                                for p, s in zip(pontos, seq)], lag_ratio=0.12),
                  run_time=2.4)
        self.wait(1.5)

        eq = tex_partes([(r"x[n] = x(nT)", WHITE), (r"\qquad f_s = 1/T", COR_H)],
                        32).move_to(P(0, Y_BASE + 0.1))
        self.play(Write(eq), run_time=1.4)
        self.wait(1.4)

        alerta = VGroup(
            Text("n é um ÍNDICE, não um tempo: é sempre inteiro",
                 font_size=23, color=COR_OK),
            Text("entre duas amostras não existe \"nada\" — "
                 "x[1,5] não tem significado", font_size=23, color=COR_ERRO),
        ).arrange(DOWN, buff=0.22).move_to(P(0, Y_BASE + 0.1))
        leg = self.legenda("Duas consequências que costumam escapar", leg,
                           COR_OK)
        self.play(FadeOut(eq), run_time=0.5)
        self.revelar(alerta, pausa=1.5)
        self.wait(1.6)
        self.limpar()

    # ================================================================== CENA 2
    def cena_impulso_degrau(self):
        self.titulo_cena("2 · Os dois sinais elementares")

        n0, n1 = -5, 7
        ns = np.arange(n0, n1 + 1)
        ax = eixo_n(P(0, 0.9), 11.0, 2.4, n0, n1, 0, 1.4)
        num = marcar_n(ax, ns)

        # --- impulso unitário -----------------------------------------------
        delta = np.where(ns == 0, 1.0, 0.0)
        h_delta = hastes(ax, ns, delta, COR_IMP, largura=4)
        eq_delta = tex(r"\delta[n] = \begin{cases} 1, & n = 0 \\ "
                       r"0, & n \neq 0 \end{cases}", COR_IMP, 32)\
            .move_to(P(-3.6, -1.9))

        leg = self.legenda("O impulso unitário: vale 1 em n = 0 e zero "
                           "em todo o resto")
        self.play(Create(ax), FadeIn(num), run_time=1.0)
        self.play(LaggedStart(*[GrowFromPoint(h, ax.c2p(n, 0))
                                for h, n in zip(h_delta, ns)], lag_ratio=0.1),
                  run_time=1.8)
        self.play(Write(eq_delta), run_time=1.6)
        self.wait(1.6)
        nota = Text("é a peça de montar do DSP:\ntudo será escrito "
                    "em função dele", font_size=22, color=COR_OK,
                    line_spacing=0.9).move_to(P(3.4, -1.9))
        self.play(FadeIn(nota, shift=UP * 0.15), run_time=0.9)
        leg = self.legenda("Ele não tem nada de misterioso: é só "
                           "\"um\" num lugar só", leg, COR_IMP)
        self.wait(1.8)

        # --- degrau unitário -------------------------------------------------
        leg = self.legenda("O degrau unitário: liga em n = 0 e fica ligado "
                           "para sempre", leg, COR_DEG)
        degrau = np.where(ns >= 0, 1.0, 0.0)
        h_deg = hastes(ax, ns, degrau, COR_DEG, largura=4)
        eq_deg = tex(r"u[n] = \begin{cases} 1, & n \geq 0 \\ "
                     r"0, & n < 0 \end{cases}", COR_DEG, 32)\
            .move_to(P(-3.6, -1.9))
        self.play(FadeOut(nota), run_time=0.5)
        self.play(ReplacementTransform(h_delta, h_deg),
                  ReplacementTransform(eq_delta, eq_deg), run_time=1.6)
        self.wait(1.6)

        # --- a relação entre os dois ----------------------------------------
        leg = self.legenda("Os dois são o mesmo sinal, visto de duas "
                           "maneiras", leg, COR_OK)
        rel = VGroup(
            tex_partes([(r"\delta[n]", COR_IMP), (r" = ", WHITE),
                        (r"u[n] - u[n-1]", COR_DEG)], 32),
            Text("a diferença do degrau é o impulso", font_size=21,
                 color=GREY_A),
            tex_partes([(r"u[n]", COR_DEG), (r" = ", WHITE),
                        (r"\sum_{k=-\infty}^{n} \delta[k]", COR_IMP)], 32),
            Text("a soma acumulada do impulso é o degrau", font_size=21,
                 color=GREY_A),
        ).arrange(DOWN, buff=0.24).move_to(P(3.3, -1.75))
        ajustar(rel, 7.0)
        self.play(FadeOut(eq_deg), run_time=0.5)
        self.revelar(rel, pausa=1.2)
        self.wait(1.0)
        leg = self.legenda("Derivada e integral do cálculo viram diferença "
                           "e soma acumulada", leg, COR_OK)
        self.wait(2.2)
        self.limpar()

    # ================================================================== CENA 3
    def cena_exponenciais(self):
        self.titulo_cena("3 · Exponenciais e senoides discretas")

        n0, n1 = 0, 14
        ns = np.arange(n0, n1 + 1)
        ax = eixo_n(P(-0.2, 1.3), 10.4, 2.2, n0, n1, 0, 2.2)
        num = marcar_n(ax, ns[::2])
        eq = tex_partes([(r"x[n] = ", WHITE), (r"a^{\,n}", COR_X)], 34)\
            .move_to(P(0, Y_TOPO))

        leg = self.legenda("A exponencial real é só uma razão constante entre "
                           "amostras vizinhas")
        self.play(Create(ax), FadeIn(num), Write(eq), run_time=1.4)
        dec = hastes(ax, ns, 2.0 * 0.82 ** ns, COR_X, largura=3)
        rot_dec = Text("a = 0,82  →  decai", font_size=22, color=COR_X)\
            .move_to(P(3.6, 2.0))
        self.play(LaggedStart(*[GrowFromPoint(h, ax.c2p(n, 0))
                                for h, n in zip(dec, ns)], lag_ratio=0.1),
                  run_time=1.8)
        self.play(FadeIn(rot_dec), run_time=0.7)
        self.wait(1.4)
        cre = hastes(ax, ns, 0.25 * 1.12 ** ns, COR_ERRO, largura=3)
        rot_cre = Text("a = 1,12  →  cresce sem limite", font_size=22,
                       color=COR_ERRO).move_to(P(3.3, 1.3))
        self.play(LaggedStart(*[GrowFromPoint(h, ax.c2p(n, 0))
                                for h, n in zip(cre, ns)], lag_ratio=0.1),
                  run_time=1.8)
        self.play(FadeIn(rot_cre), run_time=0.7)
        leg = self.legenda("Guarde isto: |a| < 1 decai, |a| > 1 explode. "
                           "Vai voltar na estabilidade.", leg, COR_OK)
        self.wait(2.0)

        # --- exponencial complexa -------------------------------------------
        leg = self.legenda("Trocando a base real por uma complexa de módulo 1, "
                           "ela gira", leg, COR_H)
        self.play(FadeOut(VGroup(ax, num, dec, cre, rot_dec, rot_cre, eq)),
                  run_time=0.9)

        centro = P(-4.0, 0.3)
        R = 1.5
        circ = Circle(radius=R, color=COR_EIXO, stroke_width=2).move_to(centro)
        eixos_c = VGroup(
            Line(centro + LEFT * (R + 0.4), centro + RIGHT * (R + 0.4),
                 color=COR_EIXO, stroke_width=2),
            Line(centro + DOWN * (R + 0.4), centro + UP * (R + 0.4),
                 color=COR_EIXO, stroke_width=2))
        eq_c = tex_partes([(r"x[n] = e^{\,j\omega n}", COR_H)], 34)\
            .move_to(P(-4.0, Y_TOPO))
        ax_s = eixo_n(P(2.8, 0.3), 7.4, 2.6, 0, 8, -1.3, 1.3)
        num_s = marcar_n(ax_s, np.arange(0, 9))
        rot_s = Text("parte real: cos(ωn)", font_size=21, color=COR_H)\
            .next_to(ax_s, UP, buff=0.12).align_to(ax_s, LEFT)

        w = PI / 4
        self.play(Create(circ), Create(eixos_c), Write(eq_c), run_time=1.4)
        self.play(Create(ax_s), FadeIn(num_s), FadeIn(rot_s), run_time=1.0)
        leg = self.legenda("A cada passo de n, o fasor avança o mesmo ângulo ω",
                           leg, COR_H)

        seta = Arrow(centro, centro + R * RIGHT, buff=0, color=COR_H,
                     stroke_width=5, max_tip_length_to_length_ratio=0.15)
        self.play(GrowArrow(seta), run_time=0.7)
        amostras = VGroup()
        for n in range(0, 9):
            if n > 0:
                self.play(Rotate(seta, w, about_point=centro), run_time=0.55)
            h = haste(ax_s, n, np.cos(w * n), COR_H, largura=3)
            amostras.add(h)
            self.play(GrowFromPoint(h, ax_s.c2p(n, 0)), run_time=0.35)
        self.wait(1.4)

        # --- as duas armadilhas ---------------------------------------------
        leg = self.legenda("Aqui moram as duas armadilhas do tempo discreto",
                           leg, COR_ERRO)
        self.play(FadeOut(VGroup(circ, eixos_c, seta, eq_c)), run_time=0.8)
        self.play(VGroup(ax_s, num_s, rot_s, amostras).animate
                  .move_to(P(0, 1.2)), run_time=1.0)

        arm1 = VGroup(
            Text("1 · ω e ω + 2π dão a MESMA sequência", font_size=25,
                 color=COR_ERRO),
            tex(r"e^{\,j(\omega + 2\pi)n} = e^{\,j\omega n}e^{\,j2\pi n} "
                r"= e^{\,j\omega n}", WHITE, 30),
            Text("só faz sentido falar de ω entre −π e π: "
                 "é a raiz do aliasing", font_size=22, color=GREY_A),
        ).arrange(DOWN, buff=0.22).move_to(P(0, -1.35))
        ajustar(arm1, 12.0)
        self.revelar(arm1, pausa=1.4)
        self.wait(1.6)

        leg = self.legenda("A segunda é ainda mais estranha", leg, COR_ERRO)
        self.play(FadeOut(arm1), run_time=0.6)
        arm2 = VGroup(
            Text("2 · uma senoide discreta pode NÃO ser periódica",
                 font_size=25, color=COR_ERRO),
            tex(r"\cos(\omega n)\ \text{é periódica} \iff "
                r"\frac{\omega}{2\pi} \in \mathbb{Q}", WHITE, 30),
            Text("ω = 1 rad/amostra: ω/2π ≈ 0,159…, irracional → "
                 "nunca se repete", font_size=22, color=GREY_A),
        ).arrange(DOWN, buff=0.22).move_to(P(0, -1.35))
        ajustar(arm2, 12.0)
        self.revelar(arm2, pausa=1.4)
        leg = self.legenda("No contínuo, todo cosseno é periódico. "
                           "No discreto, não.", leg, COR_OK)
        self.wait(2.2)
        self.limpar()

    # ================================================================== CENA 4
    def cena_decomposicao(self):
        self.titulo_cena("4 · Toda sequência é uma soma de impulsos")

        x = [2.0, 5.0, 1.0, 4.0, 3.0]
        ns = np.arange(0, 5)
        ax = eixo_n(P(-3.6, 0.9), 4.4, 2.2, -1, 5, 0, 5.6)
        num = marcar_n(ax, ns)
        seq = hastes(ax, ns, x, COR_X, largura=4)
        rot = Text("x[n]", font_size=24, color=COR_X)\
            .next_to(ax, UP, buff=0.12).align_to(ax, LEFT)

        leg = self.legenda("Pegue uma sequência qualquer, com cinco amostras")
        self.play(Create(ax), FadeIn(num), FadeIn(rot), run_time=1.0)
        self.play(LaggedStart(*[GrowFromPoint(h, ax.c2p(n, 0))
                                for h, n in zip(seq, ns)], lag_ratio=0.2),
                  run_time=1.8)
        self.wait(1.2)

        leg = self.legenda("Cada amostra é um impulso, deslocado para o seu "
                           "lugar e com a sua altura", leg, COR_IMP)
        mini = VGroup()
        for k in range(5):
            axk = eixo_n(P(1.1 + 0.0, 2.3 - 1.05 * k), 4.6, 0.8, -1, 5, 0, 5.6)
            hk = haste(axk, k, x[k], COR_IMP, raio=0.06, largura=3)
            rotk = tex(rf"{int(x[k])}\,\delta[n-{k}]", COR_IMP, 24)\
                .next_to(axk, RIGHT, buff=0.25)
            mini.add(VGroup(axk, hk, rotk))
        for item in mini:
            self.play(Create(item[0]), GrowFromPoint(item[1], item[0].c2p(0, 0)),
                      FadeIn(item[2]), run_time=0.75)
            self.wait(0.35)
        self.wait(1.2)

        eq = ajustar(tex_partes([(r"x[n] = \sum_{k=-\infty}^{\infty} ", WHITE),
                                 (r"x[k]", COR_X), (r"\,", WHITE),
                                 (r"\delta[n-k]", COR_IMP)], 34), 9.0)\
            .move_to(P(0, Y_BASE - 0.1))
        leg = self.legenda("Somando os cinco, voltamos à sequência original",
                           leg, COR_OK)
        self.play(Write(eq), run_time=2.0)
        self.wait(1.6)
        leg = self.legenda("Parece trivial — e é a ideia mais importante "
                           "de toda a teoria LTI", leg, COR_OK)
        self.wait(1.2)
        porque = Text("se o sistema é linear e invariante, basta saber "
                      "o que ele faz com UM impulso", font_size=23,
                      color=COR_H).move_to(P(0, Y_BASE - 0.75))
        self.play(FadeIn(porque, shift=UP * 0.15), run_time=1.0)
        self.wait(2.4)
        self.limpar()

    # ================================================================== CENA 5
    def cena_linearidade(self):
        self.titulo_cena("5 · Linearidade e invariância no tempo")

        # --- linearidade -----------------------------------------------------
        caixa = caixa_texto("S", 1.3, 1.0, COR_H, 34).move_to(P(0, 1.5))
        ent = tex(r"x[n]", COR_X, 28).next_to(caixa, LEFT, buff=1.3)
        sai = tex(r"y[n]", COR_Y, 28).next_to(caixa, RIGHT, buff=1.3)
        fios = VGroup(fio(ent.get_right() + RIGHT * 0.15, caixa.get_left(), COR_X),
                      fio(caixa.get_right(), sai.get_left() + LEFT * 0.15, COR_Y))
        leg = self.legenda("Um sistema é uma regra que transforma "
                           "uma sequência em outra")
        self.play(FadeIn(VGroup(caixa, ent, sai, fios)), run_time=1.2)
        self.wait(1.2)

        leg = self.legenda("Linearidade: a resposta à soma é a soma "
                           "das respostas", leg, COR_OK)
        lin = ajustar(tex_partes([
            (r"a\,x_1[n] + b\,x_2[n]", COR_X), (r"\;\longrightarrow\;", WHITE),
            (r"a\,y_1[n] + b\,y_2[n]", COR_Y)], 32), 11.0).move_to(P(0, 0.1))
        self.play(Write(lin), run_time=2.0)
        self.wait(1.8)

        leg = self.legenda("Um contraexemplo vale mais que a definição", leg,
                           COR_ERRO)
        contra = VGroup(
            tex_partes([(r"y[n] = x^2[n]", COR_ERRO)], 32),
            Text("entrada 1  →  saída 1          entrada 2  →  saída 4",
                 font_size=23, color=GREY_A),
            Text("entrada 1 + 2 = 3  →  saída 9", font_size=23, color=COR_ERRO),
            Text("mas 1 + 4 = 5 ≠ 9   →   não é linear", font_size=24,
                 color=COR_ERRO),
        ).arrange(DOWN, buff=0.24).move_to(P(0, -1.6))
        ajustar(contra, 12.0)
        self.revelar(contra, pausa=1.3)
        self.wait(1.6)

        # --- invariância no tempo -------------------------------------------
        leg = self.legenda("Invariância no tempo: atrasar a entrada só "
                           "atrasa a saída", leg, COR_OK)
        self.play(FadeOut(VGroup(lin, contra)), run_time=0.8)
        inv = ajustar(tex_partes([
            (r"x[n - n_0]", COR_X), (r"\;\longrightarrow\;", WHITE),
            (r"y[n - n_0]", COR_Y)], 32), 11.0).move_to(P(0, 0.1))
        self.play(Write(inv), run_time=1.8)
        self.wait(1.4)
        nota_inv = Text("o sistema não muda de comportamento com o relógio",
                        font_size=22, color=GREY_A).move_to(P(0, -0.65))
        self.play(FadeIn(nota_inv), run_time=0.8)
        self.wait(1.2)

        contra2 = VGroup(
            tex_partes([(r"y[n] = n\,x[n]", COR_ERRO)], 32),
            Text("o ganho depende de QUANDO a amostra chega",
                 font_size=23, color=GREY_A),
            Text("atrase a entrada e a saída muda de forma, "
                 "não só de posição", font_size=23, color=COR_ERRO),
        ).arrange(DOWN, buff=0.24).move_to(P(0, -1.75))
        ajustar(contra2, 12.0)
        self.revelar(contra2, pausa=1.3)
        self.wait(1.4)

        leg = self.legenda("Quem tem as duas propriedades é um sistema LTI",
                           leg, COR_OK)
        self.play(FadeOut(VGroup(inv, nota_inv, contra2)), run_time=0.8)
        lti = VGroup(
            Text("LTI  =  Linear  +  Invariante no Tempo", font_size=30,
                 color=COR_OK),
            Text("é a classe inteira que a teoria de DSP sabe resolver",
                 font_size=23, color=GREY_A),
            Text("e para ela vale: basta conhecer h[n]", font_size=24,
                 color=COR_H),
        ).arrange(DOWN, buff=0.3).move_to(P(0, -1.0))
        self.revelar(lti, pausa=1.5)
        self.wait(2.0)
        self.limpar()

    # ================================================================== CENA 6
    def cena_causal_estavel(self):
        self.titulo_cena("6 · Causalidade e estabilidade")

        # --- causalidade -----------------------------------------------------
        n0, n1 = -5, 5
        ns = np.arange(n0, n1 + 1)
        ax = eixo_n(P(0, 1.2), 10.0, 1.8, n0, n1, 0, 1.3)
        num = marcar_n(ax, ns)
        passado = Polygon(ax.c2p(n0, 0), ax.c2p(n0, 1.25), ax.c2p(0, 1.25),
                          ax.c2p(0, 0), stroke_width=0, fill_color=COR_OK,
                          fill_opacity=0.14)
        futuro = Polygon(ax.c2p(0, 0), ax.c2p(0, 1.25), ax.c2p(n1, 1.25),
                         ax.c2p(n1, 0), stroke_width=0, fill_color=COR_ERRO,
                         fill_opacity=0.14)
        r_pas = Text("passado e presente", font_size=20, color=COR_OK)\
            .move_to(ax.c2p(-2.5, 1.55))
        r_fut = Text("futuro", font_size=20, color=COR_ERRO)\
            .move_to(ax.c2p(2.5, 1.55))

        leg = self.legenda("Causalidade: a saída de agora não pode depender "
                           "do que ainda não chegou")
        self.play(Create(ax), FadeIn(num), run_time=1.0)
        self.play(FadeIn(passado), FadeIn(r_pas), run_time=0.8)
        self.play(FadeIn(futuro), FadeIn(r_fut), run_time=0.8)
        self.wait(1.4)

        exemplos = VGroup(
            tex_partes([(r"y[n] = x[n] + x[n-1]", COR_OK),
                        (r"\quad \text{causal}", COR_OK)], 30),
            tex_partes([(r"y[n] = x[n] + x[n+1]", COR_ERRO),
                        (r"\quad \text{n\~ao causal}", COR_ERRO)], 30),
            Text("em tempo real, x[n+1] simplesmente não existe ainda",
                 font_size=22, color=GREY_A),
            Text("para um sistema LTI:  h[n] = 0 para n < 0", font_size=24,
                 color=COR_H),
        ).arrange(DOWN, buff=0.26).move_to(P(0, -1.2))
        ajustar(exemplos, 12.0)
        self.revelar(exemplos, pausa=1.3)
        self.wait(1.6)

        # --- estabilidade BIBO ----------------------------------------------
        leg = self.legenda("Estabilidade BIBO: entrada limitada tem que "
                           "produzir saída limitada", leg, COR_OK)
        self.play(FadeOut(VGroup(ax, num, passado, futuro, r_pas, r_fut,
                                 exemplos)), run_time=0.9)

        criterio = tex_partes([(r"\sum_{n=-\infty}^{\infty} |h[n]| < \infty",
                                COR_H)], 38).move_to(P(0, Y_TOPO - 0.15))
        self.play(Write(criterio), run_time=1.8)
        self.wait(1.4)

        nsb = np.arange(0, 13)
        ax_e = eixo_n(P(-3.3, -0.3), 5.0, 2.6, 0, 12, 0, 2.6)
        ax_i = eixo_n(P(3.3, -0.3), 5.0, 2.6, 0, 12, 0, 2.6)
        he = 0.8 ** nsb
        hi = 0.25 * 1.25 ** nsb
        g_e = hastes(ax_e, nsb, he, COR_OK, raio=0.055, largura=3)
        g_i = hastes(ax_i, nsb, np.clip(hi, 0, 2.6), COR_ERRO, raio=0.055,
                     largura=3)
        r_e = VGroup(tex(r"h[n] = 0{,}8^{\,n}u[n]", COR_OK, 26),
                     Text("soma = 5  →  estável", font_size=21, color=COR_OK)
                     ).arrange(DOWN, buff=0.14).next_to(ax_e, DOWN, buff=0.3)
        r_i = VGroup(tex(r"h[n] = 1{,}25^{\,n}u[n]", COR_ERRO, 26),
                     Text("soma = ∞  →  instável", font_size=21,
                          color=COR_ERRO)
                     ).arrange(DOWN, buff=0.14).next_to(ax_i, DOWN, buff=0.3)

        self.play(Create(ax_e), Create(ax_i), run_time=0.9)
        self.play(LaggedStart(*[GrowFromPoint(h, ax_e.c2p(n, 0))
                                for h, n in zip(g_e, nsb)], lag_ratio=0.1),
                  run_time=1.6)
        self.play(FadeIn(r_e), run_time=0.8)
        self.wait(1.4)
        self.play(LaggedStart(*[GrowFromPoint(h, ax_i.c2p(n, 0))
                                for h, n in zip(g_i, nsb)], lag_ratio=0.1),
                  run_time=1.6)
        self.play(FadeIn(r_i), run_time=0.8)
        leg = self.legenda("É o mesmo |a| < 1 da cena 3, agora com "
                           "nome e critério", leg, COR_OK)
        self.wait(2.2)
        self.limpar()

    # ================================================================== CENA 7
    def cena_convolucao(self):
        self.titulo_cena("7 · A convolução, passo a passo")

        x = [1.0, 2.0, 3.0]
        h = [1.0, 1.0, 1.0]
        y = convolucao(x, h)

        eq = ajustar(tex_partes([(r"y[n] = ", COR_Y),
                                 (r"\sum_{k} x[k]\,h[n-k]", WHITE)], 36), 9.0)\
            .move_to(P(0, Y_TOPO))
        leg = self.legenda("Se vale a decomposição em impulsos e o sistema "
                           "é LTI, a saída é esta soma")
        self.play(Write(eq), run_time=2.0)
        self.wait(1.6)

        ax_x = eixo_n(P(-3.8, 1.25), 4.6, 1.5, -3, 5, 0, 3.4)
        ax_h = eixo_n(P(2.6, 1.25), 4.6, 1.5, -3, 5, 0, 3.4)
        r_x = Text("x[n] = 1, 2, 3", font_size=22, color=COR_X)\
            .next_to(ax_x, UP, buff=0.1).align_to(ax_x, LEFT)
        r_h = Text("h[n] = 1, 1, 1  (média móvel)", font_size=22, color=COR_H)\
            .next_to(ax_h, UP, buff=0.1).align_to(ax_h, LEFT)
        g_x = hastes(ax_x, [0, 1, 2], x, COR_X, largura=4)
        g_h = hastes(ax_h, [0, 1, 2], h, COR_H, largura=4)
        self.play(Create(ax_x), FadeIn(r_x), Create(ax_h), FadeIn(r_h),
                  run_time=1.0)
        self.play(LaggedStart(*[GrowFromPoint(s, ax_x.c2p(k, 0))
                                for k, s in enumerate(g_x)], lag_ratio=0.2),
                  LaggedStart(*[GrowFromPoint(s, ax_h.c2p(k, 0))
                                for k, s in enumerate(g_h)], lag_ratio=0.2),
                  run_time=1.6)
        self.wait(1.4)

        leg = self.legenda("A receita tem três passos: inverter, deslizar "
                           "e somar os produtos", leg, COR_H)
        ax_y = eixo_n(P(0, -1.75), 9.0, 1.7, -1, 6, 0, 6.5)
        num_y = marcar_n(ax_y, np.arange(0, 6))
        r_y = Text("y[n]", font_size=24, color=COR_Y)\
            .next_to(ax_y, UP, buff=0.1).align_to(ax_y, LEFT)
        self.play(Create(ax_y), FadeIn(num_y), FadeIn(r_y), run_time=1.0)

        contas = {
            0: "n = 0:   1·1                     = 1",
            1: "n = 1:   1·1 + 2·1              = 3",
            2: "n = 2:   1·1 + 2·1 + 3·1       = 6",
            3: "n = 3:            2·1 + 3·1     = 5",
            4: "n = 4:                     3·1  = 3",
        }
        conta_mob, g_y = None, VGroup()
        for n in range(5):
            txt = Text(contas[n], font_size=24, color=COR_Y)\
                .move_to(P(0, -0.35))
            if conta_mob is None:
                conta_mob = txt
                self.play(FadeIn(conta_mob), run_time=0.7)
            else:
                self.play(Transform(conta_mob, txt), run_time=0.7)
            s = haste(ax_y, n, y[n], COR_Y, largura=4)
            g_y.add(s)
            self.play(GrowFromPoint(s, ax_y.c2p(n, 0)), run_time=0.7)
            self.wait(1.0)

        self.play(FadeOut(conta_mob), run_time=0.5)
        leg = self.legenda("Três amostras convoluídas com três amostras "
                           "dão cinco: N + M − 1", leg, COR_OK)
        self.wait(1.8)
        nota = Text("a saída é mais longa que a entrada — "
                    "o filtro \"espalha\" cada amostra", font_size=23,
                    color=COR_OK).move_to(P(0, -0.35))
        self.play(FadeIn(nota, shift=UP * 0.15), run_time=0.9)
        self.wait(2.2)
        self.limpar()

    # ================================================================== CENA 8
    def cena_lccde(self):
        self.titulo_cena("8 · Equações às diferenças (LCCDE)")

        eq = ajustar(tex_partes([
            (r"y[n] = ", COR_Y), (r"\sum_{k=0}^{M} b_k\,x[n-k]", COR_X),
            (r"\;-\;", WHITE), (r"\sum_{k=1}^{N} a_k\,y[n-k]", COR_Y)], 34),
            11.5).move_to(P(0, Y_TOPO))
        leg = self.legenda("Na prática, o sistema não é descrito por h[n], "
                           "e sim por uma receita de cálculo")
        self.play(Write(eq), run_time=2.4)
        self.wait(1.8)

        partes = VGroup(
            Text("os b: pesos sobre entradas atuais e passadas",
                 font_size=23, color=COR_X),
            Text("os a: pesos sobre SAÍDAS passadas — realimentação",
                 font_size=23, color=COR_Y),
        ).arrange(DOWN, buff=0.26).move_to(P(0, 1.5))
        self.revelar(partes, pausa=1.4)
        self.wait(1.0)

        # FIR x IIR
        leg = self.legenda("A presença ou não dos a separa o mundo "
                           "em dois", leg, COR_OK)
        nsb = np.arange(0, 13)
        ax_f = eixo_n(P(-3.4, -0.9), 4.8, 2.0, 0, 12, 0, 1.3)
        ax_i = eixo_n(P(3.4, -0.9), 4.8, 2.0, 0, 12, 0, 1.3)
        hf = np.where(nsb < 4, 1.0, 0.0)
        hi = 0.8 ** nsb
        g_f = hastes(ax_f, nsb, hf, COR_X, raio=0.055, largura=3)
        g_i = hastes(ax_i, nsb, hi, COR_Y, raio=0.055, largura=3)
        t_f = VGroup(Text("FIR: sem os a", font_size=24, color=COR_X),
                     tex(r"y[n] = \tfrac{1}{4}\sum_{k=0}^{3} x[n-k]", COR_X, 26),
                     Text("h[n] acaba depois de 4 amostras", font_size=20,
                          color=GREY_A)
                     ).arrange(DOWN, buff=0.16).next_to(ax_f, UP, buff=0.25)
        t_i = VGroup(Text("IIR: com realimentação", font_size=24, color=COR_Y),
                     tex(r"y[n] = 0{,}8\,y[n-1] + x[n]", COR_Y, 26),
                     Text("h[n] = 0,8ⁿ — nunca chega a zero", font_size=20,
                          color=GREY_A)
                     ).arrange(DOWN, buff=0.16).next_to(ax_i, UP, buff=0.25)

        self.play(Create(ax_f), FadeIn(t_f), run_time=1.0)
        self.play(LaggedStart(*[GrowFromPoint(s, ax_f.c2p(n, 0))
                                for s, n in zip(g_f, nsb)], lag_ratio=0.1),
                  run_time=1.5)
        self.wait(1.4)
        self.play(Create(ax_i), FadeIn(t_i), run_time=1.0)
        self.play(LaggedStart(*[GrowFromPoint(s, ax_i.c2p(n, 0))
                                for s, n in zip(g_i, nsb)], lag_ratio=0.1),
                  run_time=1.5)
        self.wait(1.6)

        leg = self.legenda("A realimentação dá muito filtro com pouca conta — "
                           "mas pode instabilizar", leg, COR_ERRO)
        nota = Text("com 0,8 decai e é estável; com 1,2 explode: "
                    "é o critério BIBO de novo", font_size=23, color=COR_H)\
            .move_to(P(0, Y_BASE - 0.2))
        self.play(FadeIn(nota, shift=UP * 0.15), run_time=1.0)
        self.wait(2.4)
        self.limpar()

    # ================================================================== RESUMO
    def cena_resumo(self):
        titulo = Text("Resumo", font_size=44, weight=BOLD).move_to(P(0, 3.2))
        self.play(Write(titulo), run_time=1.2)
        self.wait(0.5)

        linhas = [
            ("x[n] é uma sequência: n é índice inteiro, não tempo", COR_X),
            ("entre amostras não existe nada", GREY_A),
            ("δ[n] é a peça de montar; u[n] é a sua soma acumulada", COR_IMP),
            ("toda sequência é uma soma de impulsos deslocados", GREY_A),
            ("no discreto, ω só faz sentido entre −π e π", COR_H),
            ("e uma senoide pode não ser periódica", GREY_A),
            ("LTI = linear + invariante no tempo", COR_OK),
            ("para essa classe, h[n] descreve o sistema inteiro", GREY_A),
            ("causal: h[n] = 0 para n < 0.   estável: Σ|h[n]| < ∞", COR_Y),
            ("a saída é a convolução; a receita prática é a LCCDE", GREY_A),
        ]
        g = VGroup(*[Text(t, font_size=25 if c != GREY_A else 21, color=c)
                     for t, c in linhas])
        for k, item in enumerate(g):
            if linhas[k][1] == GREY_A:
                item.shift(RIGHT * 0.4)
        g.arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to(P(0, 0.3))
        ajustar(g, 12.6)

        for k in range(0, len(g), 2):
            bloco = g[k:k + 2]
            self.play(LaggedStart(*[FadeIn(i, shift=RIGHT * 0.2)
                                    for i in bloco], lag_ratio=0.4),
                      run_time=1.2)
            self.wait(1.5)
        self.wait(1.5)

        fecho = Text("a seguir:  2 · Teoria de Amostragem e Reconstrução",
                     font_size=25, color=COR_H).move_to(P(0, -3.0))
        self.play(FadeIn(fecho), run_time=1.2)
        self.wait(2.8)
        self.limpar()
