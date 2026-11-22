# -*- coding: utf-8 -*-
"""
Decibéis: como ler um gráfico que vai de 1 a 0,00001
====================================================

Renderização (a partir da raiz do repositório):
    make Decibeis                 # rascunho 480p
    make Decibeis Q=h             # final 1080p
    manim -pql "src/9 - Decibéis/decibeis.py" Decibeis

Requer LaTeX (MathTex).

Roteiro:
    Abertura
    Cena 1 - Por que uma escala logarítmica: a mesma curva, linear e em dB
    Cena 2 - O decibel é uma razão: fatores de 10 viram passos de 10 dB
    Cena 3 - Potência ou amplitude: o 10 e o 20
    Cena 4 - A tabela de bolso: 0, −3, −6, −10, −20, −40, −60 dB
    Cena 5 - Ganhos em cascata viram soma
    Cena 6 - dB com sobrenome: dBm, dBc e dBFS
    Cena 7 - Lendo um gráfico de verdade: o FIR de 11, 31 e 101 taps
    Resumo

O gráfico da cena 7 é o da cena "O custo" de filtro_fir.py (assunto 7.3.3):
mesmo projeto (janela de Hamming, corte em 0,15·f_s) e os mesmos três N.

Layout: a tela é dividida em faixas fixas para que nada se sobreponha.
    y > 3.0          : título da cena (canto superior esquerdo)
    [Y_BASE, Y_TOPO] : área de desenho
    y ~ -3.6         : narração, uma linha por vez
"""

import numpy as np
from manim import *

# Paleta didática
COR_LIN = BLUE_C         # escala linear
COR_DB = GOLD            # escala em dB
COR_POT = ORANGE         # potência
COR_AMP = TEAL           # amplitude
COR_OK = GREEN_B         # conclusões
COR_ERRO = RED           # alertas
COR_N11 = "#F0883E"      # FIR de 11 taps (mesmas cores do vídeo do FIR)
COR_N31 = GOLD           # FIR de 31 taps
COR_N101 = GREEN         # FIR de 101 taps
COR_EIXO = GREY_B
FUNDO = "#0e1117"

EIXO_CFG = {"include_tip": False, "stroke_width": 2, "color": COR_EIXO}

# Faixas de layout (a tela vai de -4 a 4 em y e de -7.1 a 7.1 em x)
Y_TOPO = 2.70
Y_BASE = -2.55
LARG_MAX = 12.8

F_CORTE = 0.15           # corte do FIR, em ciclos por amostra (× f_s)
PISO = -90.0             # o gráfico em dB corta aqui (log 0 = −∞)


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


def caixa_texto(rotulo, largura, altura, cor, tamanho=22):
    """Caixa com texto de várias linhas, cada linha centralizada.

    Um Text com quebras alinha tudo à esquerda e encosta a primeira linha
    na borda de cima; montar linha a linha mantém o bloco no meio da caixa.
    """
    r = RoundedRectangle(corner_radius=0.08, width=largura, height=altura,
                         color=cor, stroke_width=3)
    linhas = VGroup(*[Text(t, font_size=tamanho, color=cor)
                      for t in rotulo.split("\n")]).arrange(DOWN, buff=0.1)
    ajustar(linhas, largura - 0.3)
    if linhas.height > altura - 0.24:
        linhas.scale((altura - 0.24) / linhas.height)
    return VGroup(r, linhas.move_to(r))


def seta(a, b, cor=GREY_B, largura=3):
    return Arrow(a, b, buff=0, color=cor, stroke_width=largura,
                 max_tip_length_to_length_ratio=0.2,
                 max_stroke_width_to_length_ratio=10)


def polilinha(ax, xs, ys, cor, largura=3):
    return (VMobject()
            .set_points_as_corners([ax.c2p(a, b) for a, b in zip(xs, ys)])
            .set_stroke(cor, largura))


# ------------------------------------------- o filtro do vídeo do FIR (7.3.3)
def passa_baixa_janelado(N, fc=F_CORTE):
    """FIR passa-baixa por janela de Hamming (sinc truncado), fc em ciclos/amostra."""
    n = np.arange(N) - (N - 1) / 2
    h = 2 * fc * np.sinc(2 * fc * n) * np.hamming(N)
    return h / h.sum()


def resposta(h, f):
    """|H(f)| linear."""
    k = np.arange(len(h))
    return np.abs(np.exp(-2j * np.pi * np.outer(f, k)) @ h)


def em_db(x):
    return 20 * np.log10(np.maximum(x, 1e-6))


F_EIXO = np.linspace(0, 0.5, 900)
RESP = {N: resposta(passa_baixa_janelado(N), F_EIXO) for N in (11, 31, 101)}


def valor_db(N, f):
    """|H| em dB do FIR de N taps na frequência f (× f_s)."""
    return float(em_db(resposta(passa_baixa_janelado(N), np.array([f])))[0])


# =============================================================================
# Cena
# =============================================================================
class Decibeis(Scene):
    def construct(self):
        self.camera.background_color = FUNDO
        self.abertura()
        self.cena_por_que()
        self.cena_razao()
        self.cena_dez_ou_vinte()
        self.cena_tabela()
        self.cena_cascata()
        self.cena_sobrenomes()
        self.cena_leitura()
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

    def revelar(self, itens, pausa=1.0, desloc=RIGHT * 0.2, run_time=0.8):
        """Mostra uma lista item a item, com pausa para leitura."""
        for item in itens:
            self.play(FadeIn(item, shift=desloc), run_time=run_time)
            self.wait(pausa)

    # --------------------------------------------------- eixos do filtro
    def eixo_db(self, centro, largura, altura):
        """Eixo |H| em dB de 0 a f_s/2, com a base desenhada no piso.

        Com o eixo y indo de −90 a +5 dB, o Manim poria o eixo x em 0 dB, no
        topo do gráfico. Ele fica invisível; a base é desenhada no piso.
        """
        ax = Axes(x_range=[0, 0.5, 0.125], y_range=[PISO, 5, 30],
                  x_length=largura, y_length=altura,
                  axis_config=EIXO_CFG).move_to(centro)
        ax.x_axis.set_opacity(0)
        base = Line(ax.c2p(0, PISO), ax.c2p(0.5, PISO), color=COR_EIXO,
                    stroke_width=2)
        num_y = VGroup(*[Text(f"{v}", font_size=18, color=GREY_B)
                         .next_to(ax.c2p(0, v), LEFT, buff=0.15)
                         for v in (0, -30, -60, -90)])
        rot_y = Text("|H| (dB)", font_size=19, color=COR_DB)\
            .next_to(ax.c2p(0, 5), UP, buff=0.12)
        return ax, VGroup(base, num_y, rot_y)

    def marcas_f(self, ax, y, com_corte=True):
        marcas = [(0, "0"), (0.25, "f_s/4"), (0.5, "f_s/2")]
        if com_corte:
            marcas.insert(1, (F_CORTE, "corte"))
        return VGroup(*[Text(t, font_size=18, color=GREY_B)
                        .next_to(ax.c2p(x, y), DOWN, buff=0.15)
                        for x, t in marcas])

    # ---------------------------------------------------------------- abertura
    def abertura(self):
        titulo = Text("Decibéis", font_size=64, weight=BOLD)
        sub = Text("como ler um gráfico que vai de 1 a 0,00001",
                   font_size=28, color=GREY_A)
        eq = tex_partes([(r"\text{dB} = 20\,\log_{10}", COR_DB),
                         (r"\frac{A_{\text{sa\'ida}}}{A_{\text{entrada}}}",
                          WHITE)], 42)
        g = VGroup(titulo, sub, eq).arrange(DOWN, buff=0.5)
        self.play(Write(titulo), run_time=1.6)
        self.play(FadeIn(sub, shift=UP * 0.2), run_time=1.0)
        self.wait(1.2)
        self.play(FadeIn(eq, shift=UP * 0.2), run_time=1.0)
        self.wait(2.0)
        self.play(FadeOut(g), run_time=0.9)

    # ================================================================== CENA 1
    def cena_por_que(self):
        self.titulo_cena("1 · Por que uma escala logarítmica")

        # A resposta do FIR de 31 taps, primeiro em escala linear
        ax = Axes(x_range=[0, 0.5, 0.125], y_range=[0, 1.1, 0.5],
                  x_length=10.4, y_length=4.2,
                  axis_config=EIXO_CFG).move_to(P(0.2, -0.05))
        num_y = VGroup(*[Text(t, font_size=18, color=GREY_B)
                         .next_to(ax.c2p(0, v), LEFT, buff=0.15)
                         for v, t in [(0, "0"), (0.5, "0,5"), (1, "1")]])
        rot_y = Text("|H| (linear)", font_size=19, color=COR_LIN)\
            .next_to(ax.c2p(0, 1.1), UP, buff=0.12)
        marcas = self.marcas_f(ax, 0)
        curva_lin = polilinha(ax, F_EIXO, RESP[31], COR_LIN, 4)

        leg = self.legenda("Este é um filtro passa-baixa: quanto de cada "
                           "frequência ele deixa passar")
        self.play(Create(ax), FadeIn(num_y), FadeIn(rot_y), FadeIn(marcas),
                  run_time=1.2)
        self.play(Create(curva_lin), run_time=2.4)
        self.wait(1.2)
        leg = self.legenda("1 significa passar inteira; 0 significa "
                           "bloquear por completo", leg, COR_LIN)
        self.wait(1.4)

        # O que se esconde na faixa de rejeição
        zona = Rectangle(width=ax.c2p(0.5, 0)[0] - ax.c2p(0.2, 0)[0],
                         height=0.32, color=COR_ERRO, stroke_width=2,
                         fill_color=COR_ERRO, fill_opacity=0.12)
        zona.move_to(ax.c2p(0.35, 0) + UP * 0.16)
        aviso = VGroup(
            Text("aqui a curva NÃO é zero:", font_size=22, color=COR_ERRO),
            Text("há lóbulos de 0,001 e de 0,0001", font_size=22,
                 color=COR_ERRO),
            Text("— menores que um pixel da tela", font_size=20,
                 color=GREY_A),
        ).arrange(DOWN, buff=0.14).move_to(ax.c2p(0.35, 0.62))
        leg = self.legenda("Mas o que acontece depois do corte? Pela figura, "
                           "nada.", leg, COR_ERRO)
        self.play(Create(zona), run_time=0.9)
        self.revelar(aviso, pausa=1.1, desloc=UP * 0.15)
        self.wait(1.2)
        leg = self.legenda("E é justamente ali que se decide se o filtro é "
                           "bom ou ruim", leg, COR_ERRO)
        self.wait(1.4)

        # A mesma curva, em dB
        leg = self.legenda("Agora a MESMA curva, com o eixo vertical em "
                           "decibéis", leg, COR_DB)
        ax_db, deco_db = self.eixo_db(P(0.2, -0.05), 10.4, 4.2)
        marcas_db = self.marcas_f(ax_db, PISO)
        curva_db = polilinha(ax_db, F_EIXO,
                             np.clip(em_db(RESP[31]), PISO, 5), COR_DB, 4)
        self.play(FadeOut(VGroup(zona, aviso, num_y, rot_y, marcas, ax)),
                  run_time=0.8)
        self.play(FadeIn(ax_db), FadeIn(deco_db), FadeIn(marcas_db),
                  run_time=0.9)
        self.play(ReplacementTransform(curva_lin, curva_db), run_time=2.6)
        self.wait(1.4)
        leg = self.legenda("Os lóbulos aparecem: cada fator de 10 ganha o "
                           "mesmo espaço na tela", leg, COR_DB)
        self.wait(1.6)
        nota = Text("0 dB = 1      −20 dB = 0,1      −40 dB = 0,01      "
                    "−60 dB = 0,001", font_size=22, color=COR_DB)\
            .move_to(P(0.2, Y_TOPO - 0.05))
        ajustar(nota, 12.0)
        self.play(FadeIn(nota, shift=DOWN * 0.15), run_time=1.0)
        self.wait(2.4)
        self.limpar()

    # ================================================================== CENA 2
    def cena_razao(self):
        self.titulo_cena("2 · O decibel é uma razão")

        ent = Text("entrada", font_size=24, color=GREY_A).move_to(P(-4.6, 1.9))
        sis = caixa_texto("sistema\n(filtro, cabo,\namplificador)", 2.8, 1.2,
                          COR_EIXO, 20).move_to(P(0, 1.9))
        sai = Text("saída", font_size=24, color=GREY_A).move_to(P(4.6, 1.9))
        fios = VGroup(seta(ent.get_right() + RIGHT * 0.2, sis.get_left()),
                      seta(sis.get_right(), sai.get_left() + LEFT * 0.2))
        leg = self.legenda("Um dB nunca é um valor sozinho: ele compara "
                           "duas grandezas")
        self.play(FadeIn(VGroup(ent, sis, sai, fios)), run_time=1.2)
        self.wait(1.2)

        eq = tex_partes([(r"\text{dB} = 10\,\log_{10}", COR_DB),
                         (r"\frac{P_{\text{sa\'ida}}}{P_{\text{entrada}}}",
                          COR_POT)], 38).move_to(P(0, 0.35))
        leg = self.legenda("Na origem, a razão é entre POTÊNCIAS, passada "
                           "por um logaritmo de base 10", leg, COR_POT)
        self.play(Write(eq), run_time=2.0)
        self.wait(1.8)

        # Duas réguas: razão de potência embaixo de dB
        razoes = ["0,0001", "0,001", "0,01", "0,1", "1", "10", "100"]
        dbs = ["−40", "−30", "−20", "−10", "0", "+10", "+20"]
        # o nome de cada régua fica à esquerda dela: em cima ou embaixo,
        # cairia na mesma fileira dos números
        xs = np.linspace(-3.9, 5.9, 7)
        y_r, y_d = -0.95, -2.15
        regua_r = Line(P(-4.5, y_r), P(6.4, y_r), color=COR_POT, stroke_width=2)
        regua_d = Line(P(-4.5, y_d), P(6.4, y_d), color=COR_DB, stroke_width=2)
        rot_r = Text("razão de\npotência", font_size=19, color=COR_POT,
                     line_spacing=0.85).next_to(regua_r, LEFT, buff=0.25)
        rot_d = Text("em dB", font_size=19, color=COR_DB)\
            .next_to(regua_d, LEFT, buff=0.25)
        t_r = VGroup(*[Text(r, font_size=19, color=COR_POT)
                       .next_to(P(x, y_r), UP, buff=0.08)
                       for x, r in zip(xs, razoes)])
        t_d = VGroup(*[Text(d, font_size=19, color=COR_DB)
                       .next_to(P(x, y_d), DOWN, buff=0.08)
                       for x, d in zip(xs, dbs)])
        pontes = VGroup(*[seta(P(x, y_r - 0.08), P(x, y_d + 0.08), GREY_B, 2)
                          for x in xs])
        leg = self.legenda("O log conta QUANTOS fatores de 10 cabem na "
                           "razão", leg, COR_DB)
        self.play(Create(regua_r), FadeIn(rot_r), run_time=0.9)
        self.play(Create(regua_d), FadeIn(rot_d), run_time=0.9)
        for k in (4, 5, 6, 3, 2, 1, 0):
            self.play(FadeIn(t_r[k]), GrowArrow(pontes[k]), FadeIn(t_d[k]),
                      run_time=0.6)
            self.wait(0.4)
        self.wait(1.0)
        leg = self.legenda("Multiplicar por 10 é somar 10 dB; dividir por 10 "
                           "é subtrair 10 dB", leg, COR_OK)
        self.wait(1.6)
        leg = self.legenda("Uma razão de 1 — nada mudou — é exatamente 0 dB",
                           leg, COR_OK)
        self.play(Indicate(VGroup(t_r[4], t_d[4]), color=COR_OK), run_time=1.2)
        self.wait(1.6)
        self.limpar()

    # ================================================================== CENA 3
    def cena_dez_ou_vinte(self):
        self.titulo_cena("3 · Potência ou amplitude: o 10 e o 20")

        leg = self.legenda("Num gráfico de filtro, o que se mede é a "
                           "AMPLITUDE (tensão), não a potência")
        rel = tex_partes([(r"P \propto A^2", COR_POT),
                          (r"\qquad\left(P = \frac{V^2}{R}\right)", GREY_A)],
                         36).move_to(P(0, 2.2))
        self.play(Write(rel), run_time=1.6)
        self.wait(1.4)

        passos = VGroup(
            tex_partes([(r"10\,\log_{10}", COR_DB),
                        (r"\frac{P_{s}}{P_{e}}", COR_POT)], 34),
            tex_partes([(r"=\;10\,\log_{10}", COR_DB),
                        (r"\left(\frac{A_{s}}{A_{e}}\right)^{2}", COR_AMP)], 34),
            tex_partes([(r"=\;20\,\log_{10}", COR_DB),
                        (r"\frac{A_{s}}{A_{e}}", COR_AMP)], 34),
        ).arrange(RIGHT, buff=0.35).move_to(P(0, 0.85))
        ajustar(passos, 12.4)
        leg = self.legenda("O quadrado sai do log como um fator 2: daí o 20",
                           leg, COR_AMP)
        self.revelar(passos, pausa=1.3, desloc=RIGHT * 0.15)
        self.wait(1.0)

        esq = VGroup(
            Text("amplitude cai à metade", font_size=23, color=COR_AMP),
            tex(r"20\,\log_{10}(0{,}5) = -6{,}02\ \text{dB}", COR_AMP, 32),
        ).arrange(DOWN, buff=0.25)
        dir_ = VGroup(
            Text("potência cai a um quarto", font_size=23, color=COR_POT),
            tex(r"10\,\log_{10}(0{,}25) = -6{,}02\ \text{dB}", COR_POT, 32),
        ).arrange(DOWN, buff=0.25)
        exemplo = VGroup(esq, dir_).arrange(RIGHT, buff=1.0).move_to(P(0, -0.75))
        ajustar(exemplo, 12.4)
        leg = self.legenda("Teste: o mesmo sinal, medido pelas duas "
                           "grandezas", leg)
        self.play(FadeIn(esq, shift=UP * 0.15), run_time=1.0)
        self.wait(1.4)
        self.play(FadeIn(dir_, shift=UP * 0.15), run_time=1.0)
        self.wait(1.0)
        leg = self.legenda("O mesmo número. As duas fórmulas concordam — "
                           "por construção", leg, COR_OK)
        self.wait(1.6)

        regra = VGroup(
            Text("potência  →  10 · log", font_size=26, color=COR_POT),
            Text("amplitude (tensão, corrente, |H|)  →  20 · log",
                 font_size=26, color=COR_AMP),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to(P(0, -2.2))
        moldura = SurroundingRectangle(regra, color=COR_EIXO, buff=0.18,
                                       corner_radius=0.08)
        self.play(Create(moldura), run_time=0.8)
        self.revelar(regra, pausa=1.2)
        self.wait(1.6)
        self.limpar()

    # ================================================================== CENA 4
    def cena_tabela(self):
        self.titulo_cena("4 · A tabela de bolso")

        linhas = [("0", "1", "1", 1.0),
                  ("−3", "0,707", "0,5", 0.7071),
                  ("−6", "0,5", "0,25", 0.5),
                  ("−10", "0,316", "0,1", 0.3162),
                  ("−20", "0,1", "0,01", 0.1),
                  ("−40", "0,01", "0,0001", 0.01),
                  ("−60", "0,001", "0,000001", 0.001)]
        x_db, x_amp, x_pot, x_bar = -5.6, -3.7, -1.5, 1.0
        larg_bar = 5.4
        y0, passo = 1.95, 0.55

        cab = VGroup(
            Text("dB", font_size=24, color=COR_DB, weight=BOLD)
            .move_to(P(x_db, y0 + 0.6)),
            Text("amplitude", font_size=24, color=COR_AMP, weight=BOLD)
            .move_to(P(x_amp, y0 + 0.6)),
            Text("potência", font_size=24, color=COR_POT, weight=BOLD)
            .move_to(P(x_pot, y0 + 0.6)),
            Text("amplitude que sobra", font_size=22, color=COR_AMP)
            .move_to(P(x_bar + larg_bar / 2, y0 + 0.6)),
        )
        traco = Line(P(-6.5, y0 + 0.3), P(6.6, y0 + 0.3), color=COR_EIXO,
                     stroke_width=1.5)
        leg = self.legenda("Sete linhas resolvem quase toda leitura de "
                           "gráfico em dB")
        self.play(FadeIn(cab), Create(traco), run_time=1.0)

        corpo = VGroup()
        for i, (d, a, p, v) in enumerate(linhas):
            y = y0 - i * passo
            fila = VGroup(
                Text(d, font_size=24, color=COR_DB).move_to(P(x_db, y)),
                Text(a, font_size=24, color=COR_AMP).move_to(P(x_amp, y)),
                Text(p, font_size=24, color=COR_POT).move_to(P(x_pot, y)),
            )
            comp = larg_bar * v
            if comp > 0.04:
                barra = Rectangle(width=comp, height=0.26, stroke_width=0,
                                  fill_color=COR_AMP, fill_opacity=0.8)
                barra.move_to(P(x_bar + comp / 2, y))
                fila.add(barra)
            else:
                fila.add(Text("menor que um pixel", font_size=18,
                              color=GREY_B).move_to(P(x_bar + 1.2, y)))
            corpo.add(fila)
            self.play(FadeIn(fila, shift=RIGHT * 0.2), run_time=0.7)
            self.wait(1.1)
        self.wait(1.0)

        leg = self.legenda("Três regras saem dessa tabela", leg, COR_OK)
        self.play(FadeOut(VGroup(cab[3], *[f[3] for f in corpo])),
                  run_time=0.8)
        regras = VGroup(
            Text("−6 dB  →  amplitude ÷ 2", font_size=25, color=COR_AMP),
            Text("−20 dB  →  amplitude ÷ 10", font_size=25, color=COR_AMP),
            Text("−3 dB  →  potência ÷ 2", font_size=25, color=COR_POT),
            Text("(é o −3 dB que define a", font_size=20, color=GREY_A),
            Text(" frequência de corte de um filtro)", font_size=20,
                 color=GREY_A),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.24).move_to(P(3.6, 0.3))
        for k in (2, 4, 1):
            self.play(Indicate(corpo[k][0], color=COR_OK), run_time=0.6)
        self.revelar(regras, pausa=1.0)
        self.wait(1.0)
        leg = self.legenda("E o sinal: 0 dB não mexe, negativo atenua, "
                           "positivo amplifica", leg, COR_OK)
        self.wait(2.0)
        self.limpar()

    # ================================================================== CENA 5
    def cena_cascata(self):
        self.titulo_cena("5 · Ganhos em cascata viram soma")

        y = 1.55
        ent = Text("1 mW", font_size=24, color=COR_POT).move_to(P(-6.0, y))
        blocos = VGroup(
            caixa_texto("amplificador\n+20 dB", 2.4, 1.0, COR_OK, 21),
            caixa_texto("cabo\n−3 dB", 2.0, 1.0, COR_ERRO, 21),
            caixa_texto("atenuador\n−10 dB", 2.2, 1.0, COR_ERRO, 21),
        )
        for b, x in zip(blocos, (-3.6, -0.3, 2.9)):
            b.move_to(P(x, y))
        sai = Text("? mW", font_size=24, color=COR_POT).move_to(P(5.9, y))
        nos = [ent.get_right() + RIGHT * 0.15, blocos[0].get_left(),
               blocos[0].get_right(), blocos[1].get_left(),
               blocos[1].get_right(), blocos[2].get_left(),
               blocos[2].get_right(), sai.get_left() + LEFT * 0.15]
        fios = VGroup(*[seta(nos[2 * k], nos[2 * k + 1], GREY_B, 3)
                        for k in range(4)])
        leg = self.legenda("Uma cadeia de três blocos. Quanto sai no fim?")
        self.play(FadeIn(ent), run_time=0.6)
        for k in range(3):
            self.play(GrowArrow(fios[k]), FadeIn(blocos[k]), run_time=0.8)
        self.play(GrowArrow(fios[3]), FadeIn(sai), run_time=0.8)
        self.wait(1.2)

        # Em escala linear: multiplicar
        lin = VGroup(
            Text("em escala linear, multiplicar:", font_size=23, color=COR_LIN),
            tex(r"1\ \text{mW}\times 100 \times 0{,}5 \times 0{,}1 "
                r"= 5\ \text{mW}", COR_LIN, 34),
        ).arrange(DOWN, buff=0.22).move_to(P(0, -0.1))
        leg = self.legenda("Em escala linear, cada bloco é uma "
                           "multiplicação", leg, COR_LIN)
        self.revelar(lin, pausa=1.4, desloc=UP * 0.15)

        # Em dB: somar
        em_db_ = VGroup(
            Text("em dB, somar:", font_size=23, color=COR_DB),
            tex(r"0\ \text{dBm} + 20 - 3 - 10 = 7\ \text{dBm}", COR_DB, 34),
        ).arrange(DOWN, buff=0.22).move_to(P(0, -1.75))
        leg = self.legenda("Em dB, cada bloco é uma soma — dá para fazer "
                           "de cabeça", leg, COR_DB)
        self.revelar(em_db_, pausa=1.4, desloc=UP * 0.15)
        confere = Text("e 7 dBm é exatamente 5 mW", font_size=22,
                       color=COR_OK).next_to(em_db_, DOWN, buff=0.25)
        self.play(FadeIn(confere), run_time=0.8)
        self.wait(1.4)
        leg = self.legenda("É por isso que orçamentos de enlace e cadeias "
                           "de RF são feitos em dB", leg, COR_OK)
        self.wait(2.0)
        self.limpar()

    # ================================================================== CENA 6
    def cena_sobrenomes(self):
        self.titulo_cena("6 · dB com sobrenome: dBm, dBc e dBFS")

        leg = self.legenda("Às vezes a referência é fixa — e aí o dB "
                           "ganha uma letra")
        intro = Text("a letra diz contra o que se está comparando",
                     font_size=26, color=GREY_A).move_to(P(0, 1.6))
        self.play(FadeIn(intro), run_time=0.9)
        self.wait(1.6)
        self.play(FadeOut(intro), run_time=0.6)

        # --- dBm: uma régua de potência absoluta -----------------------------
        leg = self.legenda("dBm: comparado com 1 miliwatt. Vira uma unidade "
                           "de potência.", leg, COR_POT)
        x_r = -1.2
        regua = Line(P(x_r, 2.2), P(x_r, -2.1), color=COR_POT, stroke_width=3)
        pontos = [(80, "+80 dBm", "100 kW", "ordem de um amplificador de RF"),
                  (30, "+30 dBm", "1 W", ""),
                  (0, "0 dBm", "1 mW", "a referência"),
                  (-30, "−30 dBm", "1 µW", ""),
                  (-90, "−90 dBm", "1 pW", "um sinal fraco num receptor")]
        y_de = lambda d: -2.1 + (d + 90) / 170 * 4.3
        self.play(Create(regua), run_time=0.9)
        marcas = VGroup()
        for d, a, b, c in pontos:
            yy = y_de(d)
            g = VGroup(
                Line(P(x_r - 0.12, yy), P(x_r + 0.12, yy), color=COR_POT,
                     stroke_width=3),
                Text(a, font_size=21, color=COR_DB)
                .next_to(P(x_r - 0.2, yy), LEFT, buff=0.1),
                Text(b, font_size=21, color=COR_POT)
                .next_to(P(x_r + 0.2, yy), RIGHT, buff=0.1),
            )
            if c:
                g.add(Text(c, font_size=18, color=GREY_A)
                      .next_to(P(x_r + 1.6, yy), RIGHT, buff=0.1))
            marcas.add(g)
            self.play(FadeIn(g, shift=RIGHT * 0.15), run_time=0.7)
            self.wait(0.7)
        leg = self.legenda("De 1 pW a 100 kW são 17 fatores de 10 — e cabem "
                           "numa régua de 170 dB", leg, COR_DB)
        self.wait(2.0)
        self.play(FadeOut(VGroup(regua, marcas)), run_time=0.8)

        # --- dBc: relativo à portadora ---------------------------------------
        leg = self.legenda("dBc: comparado com a portadora (o sinal que "
                           "interessa)", leg, COR_OK)
        ax = Axes(x_range=[0, 10, 1], y_range=[-60, 5, 20], x_length=6.4,
                  y_length=3.4, axis_config=EIXO_CFG).move_to(P(-2.8, -0.1))
        ax.x_axis.set_opacity(0)
        base = Line(ax.c2p(0, -60), ax.c2p(10, -60), color=COR_EIXO,
                    stroke_width=2)
        num_y = VGroup(*[Text(f"{v}", font_size=17, color=GREY_B)
                         .next_to(ax.c2p(0, v), LEFT, buff=0.12)
                         for v in (0, -20, -40, -60)])
        rot_y = Text("dBc", font_size=19, color=COR_OK)\
            .next_to(ax.c2p(0, 5), UP, buff=0.1)
        port = Line(ax.c2p(3, -60), ax.c2p(3, 0), color=COR_OK, stroke_width=5)
        esp = Line(ax.c2p(7, -60), ax.c2p(7, -40), color=COR_ERRO,
                   stroke_width=5)
        r_port = Text("portadora: 0 dBc", font_size=19, color=COR_OK)\
            .next_to(port, UP, buff=0.12)
        r_esp = Text("espúrio: −40 dBc", font_size=19, color=COR_ERRO)\
            .next_to(esp, UP, buff=0.12)
        self.play(Create(ax), Create(base), FadeIn(num_y), FadeIn(rot_y),
                  run_time=0.9)
        self.play(GrowFromEdge(port, DOWN), FadeIn(r_port), run_time=0.8)
        self.play(GrowFromEdge(esp, DOWN), FadeIn(r_esp), run_time=0.8)
        explica = VGroup(
            Text("−40 dBc  =  1% da amplitude", font_size=23, color=COR_ERRO),
            Text("da portadora", font_size=23, color=COR_ERRO),
            Text("no IQ sampling (7.1), uma 3ª", font_size=20, color=GREY_A),
            Text("harmônica assim vira 0,57°", font_size=20, color=GREY_A),
            Text("de erro de fase", font_size=20, color=GREY_A),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.16).move_to(P(3.7, 0.0))
        self.revelar(explica, pausa=0.8)
        self.wait(1.4)
        self.play(FadeOut(VGroup(ax, base, num_y, rot_y, port, esp, r_port,
                                 r_esp, explica)), run_time=0.8)

        # --- dBFS: relativo ao fundo de escala do ADC -------------------------
        leg = self.legenda("dBFS: comparado com o maior sinal que o ADC "
                           "consegue representar", leg, COR_AMP)
        fs = VGroup(
            Text("0 dBFS = fundo de escala do conversor", font_size=25,
                 color=COR_AMP),
            tex(r"\text{SQNR} \approx 6{,}02\,B + 1{,}76\ \text{dB}",
                COR_DB, 36),
            Text("ADC de 16 bits  →  piso de ruído em ≈ −98 dBFS",
                 font_size=25, color=COR_AMP),
            Text("(é o 6,02·B do assunto 3 e o SFDR do DDS no assunto 6)",
                 font_size=20, color=GREY_A),
        ).arrange(DOWN, buff=0.35).move_to(P(0, 0.2))
        self.revelar(fs, pausa=1.3, desloc=UP * 0.15)
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 7
    def cena_leitura(self):
        self.titulo_cena("7 · Lendo um gráfico de verdade")

        ax, deco = self.eixo_db(P(-2.45, -0.25), 7.6, 4.2)
        marcas = self.marcas_f(ax, PISO)
        curvas = {N: polilinha(ax, F_EIXO,
                               np.clip(em_db(RESP[N]), PISO, 5), cor, 3)
                  for N, cor in ((11, COR_N11), (31, COR_N31),
                                 (101, COR_N101))}
        nomes = VGroup(*[Text(f"N = {N} taps", font_size=22, color=cor)
                         for N, cor in ((11, COR_N11), (31, COR_N31),
                                        (101, COR_N101))])\
            .arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(P(4.4, 1.85))

        leg = self.legenda("Este é o gráfico do vídeo do filtro FIR (7.3.3). "
                           "Vamos lê-lo por partes.")
        self.play(FadeIn(ax), FadeIn(deco), FadeIn(marcas), run_time=1.0)
        for N, nome in zip((11, 31, 101), nomes):
            self.play(Create(curvas[N]), FadeIn(nome), run_time=1.4)
        self.wait(1.4)

        # 1) faixa de passagem
        # por baixo da faixa de passagem: ali a área está vazia (as curvas
        # estão todas em 0 dB), e por cima ficaria colada no rótulo do eixo
        x0, x1 = ax.c2p(0, 0)[0] + 0.12, ax.c2p(F_CORTE, 0)[0] - 0.05
        y_ch = ax.c2p(0, -4)[1]
        chave = BraceBetweenPoints(P(x0, y_ch), P(x1, y_ch), DOWN,
                                   color=COR_OK)
        r_ch = Text("0 dB: passa\ninteiro", font_size=19, color=COR_OK,
                    line_spacing=0.85).next_to(chave, DOWN, buff=0.1)
        leg = self.legenda("Antes do corte, as três curvas estão em 0 dB: "
                           "o sinal útil passa intacto", leg, COR_OK)
        self.play(GrowFromCenter(chave), FadeIn(r_ch), run_time=1.0)
        self.wait(1.6)

        # 2) o corte
        p_corte = Dot(ax.c2p(F_CORTE, valor_db(101, F_CORTE)), radius=0.08,
                      color=WHITE)
        leg = self.legenda("No corte, as três passam por −6 dB: metade da "
                           "amplitude", leg, COR_AMP)
        info_corte = Text("no corte: −6 dB  →  amplitude ÷ 2", font_size=21,
                          color=COR_AMP).move_to(P(4.4, 0.75))
        self.play(GrowFromCenter(p_corte), FadeIn(info_corte), run_time=0.9)
        self.wait(1.8)

        # 3) uma frequência indesejada em f_s/4
        linha = DashedLine(ax.c2p(0.25, PISO), ax.c2p(0.25, 0),
                           color=GREY_B, stroke_width=2)
        pts = VGroup(*[Dot(ax.c2p(0.25, valor_db(N, 0.25)), radius=0.08,
                           color=cor)
                       for N, cor in ((11, COR_N11), (31, COR_N31),
                                      (101, COR_N101))])
        leg = self.legenda("Agora uma interferência em f_s/4: quanto dela "
                           "sobra na saída?", leg)
        self.play(Create(linha), run_time=0.8)
        self.play(LaggedStart(*[GrowFromCenter(p) for p in pts],
                              lag_ratio=0.3), run_time=1.2)
        leituras = VGroup(*[
            Text(f"N = {N}:  {v:.0f} dB  →  {pct}".replace("-", "−"),
                 font_size=21, color=cor)
            for N, v, pct, cor in (
                (11, valor_db(11, 0.25), "8 %", COR_N11),
                (31, valor_db(31, 0.25), "0,11 %", COR_N31),
                (101, valor_db(101, 0.25), "0,065 %", COR_N101))
        ]).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to(P(4.4, -0.45))
        rot_f4 = Text("em f_s/4 sobra:", font_size=20, color=GREY_A)\
            .next_to(leituras, UP, buff=0.18).align_to(leituras, LEFT)
        self.play(FadeOut(info_corte), FadeIn(rot_f4), run_time=0.7)
        self.revelar(leituras, pausa=1.2)
        exemplo = VGroup(
            Text("1 V de interferência sai com:", font_size=20, color=GREY_A),
            Text("79 mV   ·   1,1 mV   ·   0,65 mV", font_size=21,
                 color=WHITE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.14).move_to(P(4.4, -1.85))
        leg = self.legenda("Em números concretos, para uma interferência "
                           "de 1 volt", leg)
        self.revelar(exemplo, pausa=1.4)
        self.wait(1.0)

        # 4) os espetos para baixo
        leg = self.legenda("E os espetos que descem até −90 dB?", leg,
                           COR_ERRO)
        f_nulo = F_EIXO[np.argmin(em_db(RESP[31])[F_EIXO > 0.3])
                        + np.searchsorted(F_EIXO, 0.3)]
        alvo = ax.c2p(f_nulo, PISO + 3)
        nulo = VGroup(
            Text("frequências em que |H| = 0:", font_size=19, color=COR_ERRO),
            Text("log(0) = −∞, o gráfico corta", font_size=19,
                 color=COR_ERRO),
        ).arrange(DOWN, buff=0.1).move_to(ax.c2p(0.4, -3))
        seta_n = seta(nulo.get_bottom() + DOWN * 0.08, alvo, COR_ERRO, 2)
        self.play(FadeIn(nulo), GrowArrow(seta_n), run_time=1.0)
        self.wait(1.8)
        leg = self.legenda("Não são picos negativos: são pontos em que "
                           "nada passa", leg, COR_ERRO)
        self.wait(2.0)
        self.limpar()

    # ================================================================== RESUMO
    def cena_resumo(self):
        titulo = Text("Resumo", font_size=44, weight=BOLD).move_to(P(0, 3.2))
        self.play(Write(titulo), run_time=1.2)
        self.wait(0.5)

        linhas = [
            ("o dB é uma razão em escala logarítmica", COR_DB),
            ("cada fator de 10 ocupa o mesmo espaço na tela", GREY_A),
            ("potência → 10·log;  amplitude → 20·log", COR_AMP),
            ("as duas dão o mesmo número de dB para o mesmo sinal", GREY_A),
            ("0 dB não mexe;  −6 dB = metade;  −20 dB = um décimo", COR_OK),
            ("−3 dB = metade da potência: a frequência de corte", GREY_A),
            ("ganhos em cascata se somam em dB", COR_POT),
            ("dBm, dBc e dBFS: a letra é a referência", GREY_A),
            ("espetos até o piso são zeros, não picos negativos", COR_ERRO),
        ]
        g = VGroup(*[Text(t, font_size=25 if c != GREY_A else 21, color=c)
                     for t, c in linhas])
        for k, item in enumerate(g):
            if linhas[k][1] == GREY_A:
                item.shift(RIGHT * 0.4)
        g.arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to(P(0, 0.2))
        ajustar(g, 12.6)
        for k in range(0, len(g), 2):
            bloco = g[k:k + 2]
            self.play(LaggedStart(*[FadeIn(i, shift=RIGHT * 0.2)
                                    for i in bloco], lag_ratio=0.4),
                      run_time=1.2)
            self.wait(1.5)
        self.wait(2.5)
        self.limpar()
