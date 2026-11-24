# -*- coding: utf-8 -*-
"""
Filtro CIC: integrador + pente = média móvel sem multiplicadores
================================================================

Renderização (a partir da raiz do repositório):
    manim -pql "src/7 - Detecção de amplitude e fase em RF/3 - Digital Down Conversion/2 - Filtro CIC/filtro_cic.py" FiltroCIC   # rascunho
    manim -pqh "src/7 - Detecção de amplitude e fase em RF/3 - Digital Down Conversion/2 - Filtro CIC/filtro_cic.py" FiltroCIC   # final

Requer LaTeX (MathTex).

Roteiro (segue "docs/7 - Detecção de amplitude e fase em RF/3 - Digital Down Conversion/2 - Filtro CIC/Filtro CIC"):
    Abertura: o que é um CIC e os três parâmetros R, D e M
    Cena  1 - Lendo um diagrama de blocos: seta, somador, registrador z^-1 e nó
    Cena  2 - A estrutura: integrador (realimentado) e comb (só para frente)
    Cena  3 - O integrador ciclo a ciclo: o laço que guarda tudo
    Cena  4 - O comb ciclo a ciclo: z^-4 é uma fila de quatro registradores
    Cena  5 - Os dois juntos: uma janela de R·D amostras que desliza
    Cena  6 - Por que isso filtra: o rápido se cancela, o lento se soma
    Cena  7 - Medindo a resposta em frequência: uma senoide de cada vez
    Cena  8 - Lendo o gráfico |H(f)|: eixos, ganho D, zeros e lóbulos
    Cena  9 - Agora decimando: R = 2, 4, 8 e 16 (D = 1), na frequência e no tempo
    Cena 10 - Decimar sem aliasing: os zeros caem onde as bandas dobram
    Cena 11 - Onde o decimador entra: integrador rápido, comb lento
    Cena 12 - D, o atraso diferencial do comb: com R fixo, a janela é R·D
    Cena 13 - M, o número de estágios: o que é um estágio, o que M faz com a
              janela, com |H(f)| (linear e em dB) e com o sinal
    Resumo

Notação (a de Hogenauer, usada em todo o arquivo):

    R  fator de decimação       quantas amostras se descarta
    D  atraso diferencial       quantos registradores o comb tem (z^-D)
    M  número de estágios       quantas vezes o filtro é repetido (N em
                               parte da literatura)

A janela do filtro tem R·D amostras, e os três valores em uso aparecem o vídeo
inteiro num selo no alto à direita (método parametros()). O exemplo evolui assim:

    abertura a cena 8   R = 1, D = 4, M = 1   janela 4, sem decimar
    cena  9             R = 2/4/8/16, D = 1   o filtro passa a decimar
    cenas 10 e 11       R = 4, D = 1, M = 1   janela 4 de novo: o exemplo do vídeo
    cena 12             R = 4, D = 1/2/4      só o D muda; a taxa de saída não
    cena 13             R = 4, D = 1, M = 1..4

Nenhuma cena cita outra pelo número: as referências são sempre ao que foi visto
("o mesmo gráfico de antes"), para o vídeo poder ser assistido sem índice.
"""

import numpy as np
from manim import *

# Paleta didática (fixa em todas as cenas)
COR_X = BLUE             # entrada x[n]
COR_INT = GOLD           # integrador I[n]
COR_COMB = TEAL          # comb / saída y[n]
COR_JANELA = YELLOW      # janela de D amostras / valor guardado
COR_RUIDO = RED          # alta frequência / ruído / aliasing
COR_LENTO = GREEN        # baixa frequência / sinal útil
COR_DEC = PINK           # decimador
COR_EIXO = GREY_B
FUNDO = "#0e1117"

EIXO_CFG = {"include_tip": False, "stroke_width": 2, "color": COR_EIXO}
D = 4                                    # janela do exemplo: R·D = 4 amostras
X_EXEMPLO = [2, 1, 3, 1, 2, 3, 1, 2]     # entrada numérica das cenas 3 a 5
X_LONGO = X_EXEMPLO * 2                  # 16 amostras, para mostrar o acumulador crescendo


# =============================================================================
# Utilitários de construção
# =============================================================================
def P(x, y):
    return np.array([x, y, 0.0])


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


def somador(cor=WHITE, raio=0.28):
    c = Circle(radius=raio, color=cor, stroke_width=3)
    return VGroup(c, tex(r"\Sigma", cor, 26).move_to(c))


def pacote(valor, cor, tamanho=26):
    """Uma amostra viajando pelo diagrama: um número dentro de uma cápsula."""
    t = tex(str(valor), cor, tamanho)
    c = RoundedRectangle(corner_radius=0.1, width=max(0.52, t.width + 0.3), height=0.46,
                         color=cor, stroke_width=2, fill_color=FUNDO, fill_opacity=1)
    return VGroup(c, t.move_to(c))


def eixos_tempo(centro, largura, altura, x_range, y_range):
    return Axes(x_range=x_range, y_range=y_range, x_length=largura, y_length=altura,
                axis_config=EIXO_CFG).move_to(centro)


def rotulo_eixo(ax, mob):
    """Coloca um rótulo acima do canto esquerdo de um eixo."""
    return mob.next_to(ax, UP, buff=0.04).align_to(ax, LEFT)


def marcar_x(ax, valores, rotulos, tamanho=15, buff=0.1):
    return VGroup(*[Text(r, font_size=tamanho, color=COR_EIXO).next_to(ax.c2p(v, 0), DOWN, buff=buff)
                    for v, r in zip(valores, rotulos)])


def haste(ax, x, y, cor, raio=0.06, largura=2):
    return VGroup(Line(ax.c2p(x, 0), ax.c2p(x, y), color=cor, stroke_width=largura),
                  Dot(ax.c2p(x, y), radius=raio, color=cor))


def integrar(x):
    return list(np.cumsum(x))


def comb(I, d=D):
    return [I[n] - (I[n - d] if n >= d else 0) for n in range(len(I))]


def media_movel(x, d=D):
    """Soma de janela de d amostras (sem dividir), já alinhada com a entrada."""
    return np.array([np.sum(x[max(0, k - d + 1):k + 1]) for k in range(len(x))])


def resposta(f, d=D):
    """H(f) complexo do somatório de d amostras. f em unidades de f_s."""
    return np.sum(np.exp(-1j * TAU * f * np.arange(d)))


def ganho(f, d=D):
    """|H(f)| = |sin(pi d f) / sin(pi f)|, com o limite d em f = 0."""
    s = np.sin(PI * f)
    return float(d) if abs(s) < 1e-9 else float(abs(np.sin(PI * d * f) / s))


def ganho_db(f, d=D, n=1, piso=-80.0):
    g = (ganho(f, d) / d) ** n
    return max(20 * np.log10(g), piso) if g > 1e-9 else piso


# =============================================================================
# Cena
# =============================================================================
class FiltroCIC(Scene):
    def construct(self):
        self.camera.background_color = FUNDO
        self.selo = None          # o selo de parâmetros, fixo no alto à direita
        self.selo_vals = None
        self.abertura()
        self.cena_simbolos()
        self.cena_estrutura()
        self.cena_integrador()
        self.cena_comb()
        self.cena_janela()
        self.cena_filtragem()
        self.cena_resposta()
        self.cena_ler_grafico()
        self.cena_outros_fatores()
        self.cena_aliasing()
        self.cena_decimacao()
        self.cena_atraso_comb()
        self.cena_estagios()
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
        """Limpa a tela, menos o selo de parâmetros, que atravessa o vídeo."""
        alvos = [m for m in self.mobjects if m is not self.selo]
        for m in alvos:
            m.clear_updaters()
        if alvos:
            self.play(*[FadeOut(m) for m in alvos], run_time=0.8)
        self.wait(0.2)

    def parametros(self, R=None, D=None, M=None):
        """Selo no alto à direita com os três parâmetros do exemplo em uso.

        Sem argumentos, retira o selo. R e D são inteiros (a janela R·D é
        calculada); M pode ser texto, para as cenas que comparam vários M.
        """
        if R is None:
            if self.selo is not None:
                self.play(FadeOut(self.selo), run_time=0.4)
                self.selo, self.selo_vals = None, None
            return
        if (R, D, M) == self.selo_vals:
            return

        def par(letra, valor, cor):
            return VGroup(tex(letra, cor, 26), txt(f"= {valor}", 17, GREY_A)).arrange(RIGHT, buff=0.1)

        novo = VGroup(VGroup(par("R", R, COR_DEC), par("D", D, COR_COMB), par("M", M, COR_JANELA)
                             ).arrange(RIGHT, buff=0.3),
                      txt(f"janela R·D = {R * D}", 17, GREY_B)
                      ).arrange(DOWN, buff=0.1, aligned_edge=RIGHT).to_corner(UR, buff=0.26)
        self.selo_vals = (R, D, M)
        if self.selo is None:
            self.selo = novo
            self.play(FadeIn(novo, shift=DOWN * 0.15), run_time=0.6)
        else:
            self.play(Transform(self.selo, novo), run_time=0.5)

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
        nota = Text("vamos ler o diagrama símbolo por símbolo, seguir as amostras ciclo a ciclo\n"
                    "e entender o gráfico da resposta em frequência",
                    font_size=22, color=GREY_B, line_spacing=0.8)
        g = VGroup(titulo, sub, cadeia, nota).arrange(DOWN, buff=0.45)
        self.play(Write(titulo), run_time=1.5)
        self.play(FadeIn(sub, shift=UP * 0.2), FadeIn(cadeia, shift=UP * 0.2))
        self.play(FadeIn(nota, shift=UP * 0.2))
        self.wait(1.8)
        self.play(FadeOut(g))

        # --- os três parâmetros, antes de qualquer outra coisa ---------------
        cab = Text("Três números definem um CIC", font_size=34, weight=BOLD).move_to(P(0, 2.7))
        letras = VGroup()
        for k, (sig, nome, oque, cor) in enumerate([
                ("R", "fator de decimação", "de quanto a taxa de amostragem cai", COR_DEC),
                ("D", "atraso diferencial", "quantos registradores o comb tem", COR_COMB),
                ("M", "número de estágios", "quantas vezes o filtro é repetido", COR_JANELA)]):
            y = 1.6 - 0.62 * k
            letras.add(tex(sig, cor, 34).move_to(P(-5.2, y)))
            letras.add(txt(nome, 22, cor).move_to(P(-4.7, y), aligned_edge=LEFT))
            letras.add(txt(oque, 21, GREY_B).move_to(P(0.3, y), aligned_edge=LEFT))
        janela = tex_partes([(r"\text{a janela do filtro tem }", WHITE), (r"R", COR_DEC), (r"\cdot", WHITE),
                             (r"D", COR_COMB), (r"\text{ amostras}", WHITE)], 32).move_to(P(0, -0.85))
        exemplo = txt("o exemplo deste vídeo começa com R = 1, D = 4 e M = 1: uma janela de 4 amostras",
                      22, COR_JANELA).move_to(P(0, -1.75))
        onde = txt("os três ficam no canto da tela o vídeo inteiro, e mudam quando o exemplo mudar",
                   21, GREY_B).move_to(P(0, -2.55))
        self.play(FadeIn(cab), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(m, shift=RIGHT * 0.15) for m in letras], lag_ratio=0.07), run_time=1.9)
        self.play(Write(janela), run_time=1.2)
        self.wait(0.9)
        self.play(FadeIn(exemplo, shift=UP * 0.15))
        self.wait(1.2)
        self.play(FadeIn(onde, shift=UP * 0.15))
        self.parametros(1, 4, 1)
        self.wait(1.8)
        self.play(FadeOut(VGroup(cab, letras, janela, exemplo, onde)), run_time=0.8)

    # ================================================================== CENA 1
    def cena_simbolos(self):
        """Antes de explicar o CIC, ensinar a ler o desenho."""
        self.titulo_cena("1 · Lendo um diagrama de blocos")
        xs, xt = -5.5, -4.3
        ys = [2.25, 0.95, -0.5, -2.05]

        # 1) seta
        s1 = VGroup(Arrow(P(xs - 0.7, ys[0]), P(xs + 0.7, ys[0]), buff=0, color=COR_X, stroke_width=4,
                          max_tip_length_to_length_ratio=0.2),
                    tex(r"x[n]", COR_X, 22).next_to(P(xs, ys[0]), UP, buff=0.12))
        t1 = txt("seta: o caminho por onde as amostras andam —\n"
                 "uma amostra nova a cada ciclo de clock", 21, line_spacing=0.8)

        # 2) somador
        s2 = VGroup(somador(WHITE).move_to(P(xs, ys[1])),
                    Arrow(P(xs - 1.0, ys[1]), P(xs - 0.32, ys[1]), buff=0, color=GREY_A, stroke_width=3,
                          max_tip_length_to_length_ratio=0.3),
                    Arrow(P(xs, ys[1] - 0.95), P(xs, ys[1] - 0.32), buff=0, color=GREY_A, stroke_width=3,
                          max_tip_length_to_length_ratio=0.3),
                    tex("+", WHITE, 24).move_to(P(xs - 0.45, ys[1] + 0.26)),
                    tex("-", COR_RUIDO, 32).move_to(P(xs - 0.28, ys[1] - 0.48)))
        t2 = txt("somador: junta o que chega pelas setas;\n"
                 "o + ou o − ao lado de cada entrada diz o sinal", 21, line_spacing=0.8)

        # 3) registrador
        s3 = caixa_tex(r"z^{-1}", 1.1, 0.64, COR_INT, 28).move_to(P(xs, ys[2]))
        t3 = txt("registrador (atraso): guarda a amostra de agora e\n"
                 "a devolve no ciclo seguinte. Quatro em fila = atraso de 4", 21, line_spacing=0.8)

        # 4) nó
        s4 = VGroup(Line(P(xs - 0.8, ys[3] + 0.25), P(xs + 0.8, ys[3] + 0.25), color=COR_INT, stroke_width=3),
                    Line(P(xs, ys[3] + 0.25), P(xs, ys[3] - 0.45), color=COR_INT, stroke_width=3),
                    Line(P(xs, ys[3] - 0.45), P(xs + 0.8, ys[3] - 0.45), color=COR_INT, stroke_width=3),
                    Dot(P(xs, ys[3] + 0.25), radius=0.08, color=COR_INT))
        t4 = txt("nó: o mesmo valor segue por dois caminhos ao mesmo\n"
                 "tempo — ele é copiado, não é dividido", 21, line_spacing=0.8)

        for t, y in zip((t1, t2, t3, t4), ys):
            t.move_to(P(xt, y), aligned_edge=LEFT)

        leg = self.legenda("Quatro símbolos: com eles dá para ler o CIC inteiro")
        for s, t in ((s1, t1), (s2, t2), (s3, t3), (s4, t4)):
            self.play(FadeIn(s, shift=RIGHT * 0.2), FadeIn(t, shift=RIGHT * 0.2), run_time=0.9)
            self.wait(0.9)

        leg = self.legenda("O registrador é a memória do circuito: é dele que vem todo o comportamento", leg, COR_INT)
        y_demo = ys[2] - 0.62
        amostra = pacote(7, COR_JANELA).move_to(P(-6.8, y_demo))
        ciclo = txt("ciclo n: a amostra entra e fica guardada", 18, COR_JANELA).move_to(P(-0.9, y_demo))
        self.play(FadeIn(amostra, scale=0.6), run_time=0.4)
        self.play(MoveAlongPath(amostra, caminho([P(-6.8, y_demo), P(xs, y_demo), s3.get_center()])),
                  FadeIn(ciclo), s3[1].animate.set_opacity(0.12), run_time=1.1)
        self.wait(0.9)
        self.play(MoveAlongPath(amostra, caminho([s3.get_center(), P(xs, y_demo), P(-4.1, y_demo)])),
                  s3[1].animate.set_opacity(1.0),
                  Transform(ciclo, txt("ciclo n+1: ela sai, atrasada de um ciclo", 18, COR_JANELA
                                       ).move_to(P(-0.9, y_demo))), run_time=1.2)
        self.wait(1.6)
        self.limpar()

    # ================================================================== CENA 2
    def cena_estrutura(self):
        self.titulo_cena("2 · A estrutura: integrador + comb")
        y0 = 0.9
        x_in = tex(r"x[n]", COR_X, 32).move_to(P(-6.2, y0))
        s_int = somador(WHITE).move_to(P(-4.3, y0))
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
        nota_int = txt("o fio volta: realimentação", 19, COR_INT).move_to(P(-3.6, -2.05))

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
        nota_comb = txt("nenhum fio volta: só para frente", 19, COR_COMB).move_to(P(1.4, -2.05))
        destaque = Text("só somas, subtrações e registradores: nenhum multiplicador", font_size=22, color=WHITE
                        ).move_to(P(0, -2.8))

        leg = self.legenda("Duas partes em cascata: um integrador seguido de um comb")
        self.play(FadeIn(x_in), FadeIn(s_int), Create(f_int), FadeIn(no_int), FadeIn(z1), FadeIn(r_i), run_time=1.5)
        self.play(Create(caixa_int), FadeIn(cab_int), Write(eq_int))
        leg = self.legenda("Integrador: o somador pega a amostra nova e o que o registrador guardou", leg, COR_INT)
        self.wait(0.8)
        self.play(ShowPassingFlash(caminho([no_int.get_center(), P(-2.7, -0.4), P(-4.3, -0.4),
                                            s_int.get_center(), no_int.get_center()]).set_stroke(YELLOW, 6),
                                   time_width=0.5), run_time=1.6)
        leg = self.legenda("Esse laço fechado é o que faz o integrador lembrar de tudo o que já passou", leg, COR_INT)
        self.play(FadeIn(nota_int, shift=UP * 0.15))
        self.wait(1.2)
        leg = self.legenda("Comb: o mesmo I[n] vai direto ao somador e, por baixo, atrasado de 4 amostras", leg,
                           COR_COMB)
        self.play(FadeIn(no_comb), FadeIn(s_comb), Create(f_comb), FadeIn(zd), FadeIn(sinais), FadeIn(y_out),
                  run_time=1.6)
        self.play(Create(caixa_comb), FadeIn(cab_comb), Write(eq_comb))
        leg = self.legenda("Repare no sinal −: o ramo de baixo é subtraído do de cima", leg, COR_RUIDO)
        self.play(Indicate(sinais[1], color=COR_RUIDO, scale_factor=2), run_time=1.2)
        self.play(FadeIn(nota_comb, shift=UP * 0.15))
        leg = self.legenda("Por isso é tão barato em FPGA e ASIC: decima (ou interpola) antes dos filtros FIR", leg)
        self.play(Write(destaque))
        self.wait(2.0)
        self.limpar()

    # ================================================================== CENA 3
    def cena_integrador(self):
        """Seguir as amostras dentro do laço, um ciclo de clock de cada vez."""
        titulo = self.titulo_cena("3 · O integrador, ciclo a ciclo")
        I = integrar(X_EXEMPLO)
        yD, yR = 2.0, 0.6
        x_e, x_s, x_no, x_reg = -6.3, -5.0, -3.0, -4.0

        rot_in = tex(r"x[n]", COR_X, 30).move_to(P(x_e, yD))
        s = somador(COR_INT).move_to(P(x_s, yD))
        no = Dot(P(x_no, yD), radius=0.07, color=COR_INT)
        reg = caixa_tex(r"z^{-1}", 1.1, 0.62, COR_INT, 28).move_to(P(x_reg, yR))
        rot_out = tex(r"I[n]", COR_INT, 30).move_to(P(-1.4, yD))
        fios = VGroup(
            fio([P(x_e + 0.45, yD), P(x_s - 0.3, yD)], COR_X),
            Line(P(x_s + 0.28, yD), P(x_no, yD), color=COR_INT, stroke_width=3),
            fio([P(x_no, yD), P(-1.85, yD)], COR_INT),
            fio([P(x_no, yD), P(x_no, yR), P(x_reg + 0.57, yR)], COR_INT),
            fio([P(x_reg - 0.57, yR), P(x_s, yR), P(x_s, yD - 0.3)], COR_INT),
        )
        guarda = VGroup(txt("guarda:", 17, GREY_B), tex("0", COR_JANELA, 28)).arrange(RIGHT, buff=0.15)
        guarda.next_to(reg, DOWN, buff=0.24)
        val_reg = guarda[1]
        diagrama = VGroup(rot_in, s, no, reg, rot_out, fios, guarda)

        colx = [0.5, 1.9, 3.5, 5.4]
        cabs = VGroup(tex("n", GREY_B, 26).move_to(P(colx[0], 2.95)),
                      tex(r"x[n]", COR_X, 26).move_to(P(colx[1], 2.95)),
                      tex(r"z^{-1}", COR_JANELA, 26).move_to(P(colx[2], 2.95)),
                      tex(r"I[n]", COR_INT, 26).move_to(P(colx[3], 2.95)))
        sep = Line(P(-0.1, 2.66), P(6.2, 2.66), color=COR_EIXO, stroke_width=1.5)
        eq = tex(r"I[n] = I[n-1] + x[n]", COR_INT, 32).move_to(P(-3.3, -1.3))

        leg = self.legenda("O circuito de agora há pouco, com números passando por ele")
        self.play(FadeIn(diagrama), run_time=1.2)
        self.play(FadeIn(cabs), Create(sep), Write(eq))
        leg = self.legenda("Ciclo 0: o registrador começa zerado, então ele entrega 0 ao somador", leg, COR_JANELA)

        ant = 0
        for n in range(5):
            if n == 1:
                leg = self.legenda("Ciclo 1: o resultado de ontem voltou pelo laço e entra na soma de hoje",
                                   leg, COR_INT)
            if n == 4:
                leg = self.legenda("Repare: nada nunca sai do laço — ele só vai somando", leg, COR_INT)
            y_lin = 2.3 - 0.55 * n

            p_in = pacote(X_EXEMPLO[n], COR_X).move_to(P(x_e, yD))
            self.play(FadeIn(p_in, scale=0.6), run_time=0.35)
            p_reg = pacote(ant, COR_JANELA).move_to(reg)
            self.play(p_in.animate.move_to(P(x_s - 0.85, yD)),
                      MoveAlongPath(p_reg, caminho([reg.get_center(), P(x_s, yR), P(x_s, yD - 0.8)])),
                      run_time=0.7)
            res = pacote(I[n], COR_INT).move_to(s)
            self.play(FadeOut(p_in, scale=0.3), FadeOut(p_reg, scale=0.3), FadeIn(res, scale=1.5),
                      Flash(s, color=COR_INT, flash_radius=0.45), run_time=0.6)
            linha = VGroup(tex(str(n), GREY_B, 26).move_to(P(colx[0], y_lin)),
                           tex(str(X_EXEMPLO[n]), COR_X, 26).move_to(P(colx[1], y_lin)),
                           tex(str(ant), COR_JANELA, 26).move_to(P(colx[2], y_lin)),
                           tex(str(I[n]), COR_INT, 26).move_to(P(colx[3], y_lin)))
            nova_eq = tex(rf"I[{n}] = {ant} + {X_EXEMPLO[n]} = {I[n]}", COR_INT, 32).move_to(eq)
            self.play(res.animate.move_to(P(x_no, yD + 0.55)), FadeIn(linha, shift=LEFT * 0.2),
                      Transform(eq, nova_eq), run_time=0.7)
            copia = pacote(I[n], COR_JANELA).move_to(res)
            self.play(MoveAlongPath(copia, caminho([res.get_center(), P(x_no, yD), P(x_no, yR), reg.get_center()])),
                      FadeOut(res), run_time=0.7)
            self.play(Transform(val_reg, tex(str(I[n]), COR_JANELA, 28).move_to(val_reg)),
                      FadeOut(copia, scale=0.4), run_time=0.4)
            self.wait(0.3 if n > 1 else 0.7)
            ant = I[n]

        soma = tex(r"I[4] = x[4] + x[3] + x[2] + x[1] + x[0] = 2+1+3+1+2 = 9", COR_INT, 28).move_to(P(-1.2, -2.25))
        leg = self.legenda("I[4] é a soma de todo o passado desde que o sistema ligou", leg, COR_INT)
        self.play(Write(soma), run_time=1.5)
        self.wait(1.6)

        # --- o acumulador cresce sem parar ------------------------------------
        self.trocar_titulo(titulo, "3 · O integrador sozinho só cresce")
        self.play(FadeOut(diagrama), FadeOut(eq), FadeOut(soma), run_time=0.8)
        IL = integrar(X_LONGO)
        ax = eixos_tempo(P(-3.4, 1.0), 6.0, 3.0, [0, 16, 4], [0, 34, 10])
        r_ax = rotulo_eixo(ax, txt("I[n] com a mesma entrada se repetindo", 18, COR_INT))
        hs = VGroup(*[haste(ax, k + 1, IL[k], COR_INT, 0.06, 3) for k in range(16)])
        limite = DashedLine(ax.c2p(0, 24), ax.c2p(16, 24), color=COR_RUIDO, stroke_width=2)
        r_lim = txt("limite do registrador", 16, COR_RUIDO).next_to(limite, UP, buff=0.08).align_to(limite, LEFT)
        nota = txt("em hardware o acumulador transborda (overflow) de propósito:\n"
                   "em aritmética de complemento de dois o comb desfaz o estouro\n"
                   "e a saída final continua correta", 20, line_spacing=0.85).move_to(P(-1.0, -2.05))

        leg = self.legenda("Sem ninguém para segurar, I[n] cresce para sempre", leg, COR_INT)
        self.play(Create(ax), FadeIn(r_ax))
        self.play(LaggedStart(*[GrowFromPoint(h, ax.c2p(k + 1, 0)) for k, h in enumerate(hs)], lag_ratio=0.08),
                  run_time=2.2)
        self.play(Create(limite), FadeIn(r_lim))
        leg = self.legenda("Em uma FPGA isso estoura o número de bits — e tudo bem", leg)
        self.play(FadeIn(nota, shift=UP * 0.2))
        self.wait(2.2)
        leg = self.legenda("Quem transforma esse acumulador em filtro é o próximo bloco", leg)
        self.wait(1.4)
        self.limpar()

    # ================================================================== CENA 4
    def cena_comb(self):
        """z^-4 aberto em quatro registradores, para ver de onde vem o 'quatro'."""
        titulo = self.titulo_cena("4 · O comb, ciclo a ciclo")
        I = integrar(X_EXEMPLO)
        yD, yR = 2.0, 0.5
        x_e, x_no, x_sig = -6.5, -5.4, 2.9
        cel_x = [-4.1, -2.95, -1.8, -0.65]

        rot_in = tex(r"I[n]", COR_INT, 30).move_to(P(x_e, yD))
        no = Dot(P(x_no, yD), radius=0.07, color=COR_INT)
        s = VGroup(Circle(radius=0.28, color=COR_COMB, stroke_width=3),
                   tex(r"\Sigma", COR_COMB, 26)).move_to(P(x_sig, yD))
        rot_out = tex(r"y[n]", COR_COMB, 30).move_to(P(4.4, yD))
        cels = VGroup(*[RoundedRectangle(corner_radius=0.08, width=1.0, height=0.62, color=COR_COMB,
                                         stroke_width=2.5).move_to(P(cx, yR)) for cx in cel_x])
        labs = [tex("0", GREY_B, 26).move_to(P(cx, yR)) for cx in cel_x]
        ligacoes = VGroup(*[Arrow(P(cel_x[k] + 0.5, yR), P(cel_x[k + 1] - 0.5, yR), buff=0, color=COR_COMB,
                                  stroke_width=3, max_tip_length_to_length_ratio=0.4) for k in range(3)])
        fios = VGroup(
            fio([P(x_e + 0.45, yD), P(x_no, yD)], COR_INT),
            fio([P(x_no, yD), P(x_sig - 0.3, yD)], COR_INT),
            fio([P(x_no, yD), P(x_no, yR), P(cel_x[0] - 0.52, yR)], COR_INT),
            fio([P(cel_x[3] + 0.52, yR), P(x_sig, yR), P(x_sig, yD - 0.3)], COR_COMB),
            fio([P(x_sig + 0.3, yD), P(4.0, yD)], COR_COMB),
        )
        sinais = VGroup(tex("+", WHITE, 26).move_to(P(x_sig - 0.5, yD + 0.3)),
                        tex("-", COR_RUIDO, 34).move_to(P(x_sig - 0.34, yD - 0.52)))
        chave = BraceBetweenPoints(P(cel_x[0] - 0.55, yR - 0.4), P(cel_x[3] + 0.55, yR - 0.4), DOWN, color=COR_COMB)
        r_chave = VGroup(tex(r"z^{-4}", COR_COMB, 30),
                         txt("quatro registradores em fila: o valor leva\n4 ciclos para atravessar", 19,
                             line_spacing=0.8)).arrange(DOWN, buff=0.12).next_to(chave, DOWN, buff=0.12)
        diagrama = VGroup(rot_in, no, s, rot_out, cels, *labs, ligacoes, fios, sinais, chave, r_chave)
        conta = tex(r"y[n] = I[n] - I[n-4]", COR_COMB, 28).move_to(P(4.8, 0.7))

        leg = self.legenda("O comb recebe o I[n] do integrador e o manda por dois caminhos")
        self.play(FadeIn(diagrama), FadeIn(conta), run_time=1.5)
        leg = self.legenda("Por cima vai direto ao somador; por baixo entra na fila de registradores", leg, COR_COMB)
        self.wait(1.4)
        leg = self.legenda("Ciclo 0: a fila ainda está vazia, não há nada para subtrair", leg, COR_COMB)

        vals = [0, 0, 0, 0]
        for n in range(6):
            if n == 3:
                leg = self.legenda("A fila encheu: no próximo ciclo o primeiro valor cai pela ponta", leg, COR_COMB)
            if n == 4:
                leg = self.legenda("Agora sim: sai o I[0] = 2 e ele é subtraído do I[4] = 9", leg, COR_COMB)
            p_cima = pacote(I[n], COR_INT).move_to(no)
            p_baixo = pacote(I[n], COR_INT).move_to(no)
            velho, v_velho = labs[3], vals[3]
            anims = [MoveAlongPath(p_cima, caminho([P(x_no, yD), P(x_sig - 0.8, yD)])),
                     MoveAlongPath(p_baixo, caminho([P(x_no, yD), P(x_no, yR), P(cel_x[0], yR)])),
                     MoveAlongPath(velho, caminho([P(cel_x[3], yR), P(x_sig, yR), P(x_sig, yD - 0.8)]))]
            anims += [labs[k].animate.move_to(P(cel_x[k + 1], yR)) for k in (2, 1, 0)]
            self.play(*anims, run_time=1.0 if n < 2 else 0.8)

            novo = tex(str(I[n]), COR_COMB, 26).move_to(P(cel_x[0], yR))
            saida = I[n] - v_velho
            res = pacote(saida, COR_COMB).move_to(P(3.9, yD))
            nova_conta = tex(rf"y[{n}] = {I[n]} - {v_velho} = {saida}", COR_COMB, 28).move_to(P(4.8, 0.7))
            self.play(FadeOut(p_cima, scale=0.3), FadeOut(p_baixo, scale=0.3), FadeOut(velho, scale=0.3),
                      FadeIn(novo, scale=1.3), FadeIn(res, scale=1.4),
                      Transform(conta, nova_conta), Flash(s, color=COR_COMB, flash_radius=0.45), run_time=0.7)
            labs = [novo] + labs[:3]
            vals = [I[n]] + vals[:3]
            self.wait(0.5 if n < 2 else 0.25)
            self.play(FadeOut(res, scale=0.4), run_time=0.3)

        leg = self.legenda("Daqui para frente é sempre assim: o valor de agora menos o de 4 ciclos atrás",
                           leg, COR_COMB)
        self.wait(1.6)

        # --- o que a subtração faz com a soma acumulada -----------------------
        self.trocar_titulo(titulo, "4 · O que a subtração realmente corta")
        self.play(FadeOut(VGroup(diagrama, *labs)), FadeOut(conta), run_time=0.8)
        d1 = tex(r"y[4] = I[4] - I[0]", COR_COMB, 36).move_to(P(0, 1.7))
        d2 = tex_partes([(r"y[4] = ", WHITE), (r"(x_4 + x_3 + x_2 + x_1 + x_0)", COR_INT), (r" - ", WHITE),
                         (r"(x_0)", COR_INT)], 36).move_to(P(0, 0.5))
        d3 = tex(r"y[4] = x_4 + x_3 + x_2 + x_1", COR_COMB, 36).move_to(P(0, -0.8))
        final = txt("a janela tem sempre 4 amostras, não importa há quanto tempo o sistema está ligado",
                    22).move_to(P(0, -2.1))

        leg = self.legenda("Cada I é uma soma do passado inteiro — e uma contém a outra", leg, COR_INT)
        self.play(Write(d1))
        self.play(Write(d2), run_time=1.8)
        risco = VGroup(Line(d2[1][-3].get_corner(DL), d2[1][-3].get_corner(UR), color=COR_RUIDO, stroke_width=4),
                       Line(d2[3][1:3].get_corner(DL), d2[3][1:3].get_corner(UR), color=COR_RUIDO, stroke_width=4))
        leg = self.legenda("O x[0] aparece dos dois lados e se anula: o passado distante é cortado", leg, COR_RUIDO)
        self.play(Create(risco), run_time=1.2)
        self.play(TransformFromCopy(d2, d3), run_time=1.8)
        self.play(Create(SurroundingRectangle(d3, color=COR_COMB, buff=0.14)))
        leg = self.legenda("Integrador + comb = a soma de uma janela de 4 amostras", leg, COR_COMB)
        self.play(FadeIn(final, shift=UP * 0.2))
        self.wait(2.2)
        self.limpar()

    # ================================================================== CENA 5
    def cena_janela(self):
        self.titulo_cena("5 · Os dois juntos: uma janela que desliza")
        I = integrar(X_EXEMPLO)
        y = comb(I)
        rotulos, celulas, sep = self.tabela([(r"x[n]", COR_X, X_EXEMPLO), (r"I[n]", COR_INT, I),
                                             (r"y[n]", COR_COMB, y)])
        x0, dx, y0, dy = -4.7, 1.2, 2.35, 0.62

        leg = self.legenda("A mesma entrada de antes, agora com as três linhas juntas")
        self.play(FadeIn(rotulos[:3]), FadeIn(celulas[0]), FadeIn(celulas[1]), FadeIn(celulas[2]), Create(sep))
        self.play(FadeIn(rotulos[3]))
        leg = self.legenda("A janela amarela mostra quais entradas estão dentro da soma naquele instante",
                           leg, COR_JANELA)

        janela = Rectangle(width=dx * 4 - 0.2, height=0.55, color=COR_JANELA, stroke_width=3)
        janela.move_to(P(x0 + dx * 1.5, y0 - dy))
        self.play(Create(janela))
        for n in range(3, len(X_EXEMPLO)):
            self.play(janela.animate.move_to(P(x0 + dx * (n - 1.5), y0 - dy)), run_time=0.55)
            self.play(FadeIn(celulas[3][n], shift=DOWN * 0.1), Indicate(celulas[3][n], color=COR_JANELA),
                      run_time=0.65)
        self.play(FadeIn(celulas[3][:3]))
        leg = self.legenda("Cada saída é a soma das 4 entradas que estão dentro da janela", leg, COR_COMB)
        self.wait(1.2)

        f1 = tex(r"y[n] = x[n] + x[n-1] + x[n-2] + x[n-3]", COR_COMB, 34).move_to(P(0, -0.45))
        f2 = tex(r"\frac{y[n]}{4} = \text{média das 4 últimas amostras}", COR_JANELA, 32).move_to(P(0, -1.5))
        self.play(Write(f1), run_time=1.5)
        leg = self.legenda("Dividindo por 4, é literalmente uma média móvel de 4 amostras", leg, COR_JANELA)
        self.play(Write(f2), run_time=1.5)
        self.wait(1.4)

        self.play(FadeOut(VGroup(rotulos, celulas[0], celulas[1], celulas[2], celulas[3], sep, janela, f2)),
                  f1.animate.move_to(P(0, 2.4)), run_time=1.0)
        ax = eixos_tempo(P(-4.0, 0.7), 3.4, 1.4, [0, 6, 1], [0, 1.4, 1])
        hs = VGroup(*[haste(ax, k, 1, COR_COMB, 0.07, 4) for k in range(4)])
        r_ax = rotulo_eixo(ax, txt("resposta ao impulso: 1 1 1 1", 18, COR_COMB))
        nota = txt("é um filtro FIR de 4 coeficientes, todos iguais a 1 —\n"
                   "a diferença é que ele não usa nenhum multiplicador\n"
                   "para calcular essa soma, só um somador e registradores",
                   21, line_spacing=0.85).move_to(P(-1.9, 0.55), aligned_edge=LEFT)
        leg = self.legenda("Se entrar um único 1, saem quatro 1: essa é a resposta ao impulso", leg, COR_COMB)
        self.play(Create(ax), FadeIn(r_ax))
        self.play(LaggedStart(*[GrowFromPoint(h, ax.c2p(k, 0)) for k, h in enumerate(hs)], lag_ratio=0.2),
                  run_time=1.2)
        self.play(FadeIn(nota, shift=RIGHT * 0.2))
        self.wait(2.4)
        self.limpar()

    # ================================================================== CENA 6
    def cena_filtragem(self):
        titulo = self.titulo_cena("6 · Por que essa soma filtra")
        casos = [
            ("Entrada rápida: muda de sinal a cada amostra", [1, -1, 1, -1, 1, -1, 1, -1, 1, -1, 1, -1],
             COR_RUIDO, 1.3),
            ("Entrada lenta: quase não muda em 4 amostras", [1] * 12, COR_LENTO, -1.5),
        ]
        grupos = []
        for nome, seq, cor, yc in casos:
            ax = eixos_tempo(P(-1.6, yc), 8.6, 1.8, [0, 12, 1], [-1.3, 1.3, 1])
            cab = Text(nome, font_size=21, color=cor, weight=BOLD).next_to(ax, UP, buff=0.08).align_to(ax, LEFT)
            hs = VGroup(*[haste(ax, n + 0.5, v, cor, 0.07, 3) for n, v in enumerate(seq)])
            grupos.append((ax, cab, hs, seq, cor, yc))

        leg = self.legenda("Duas entradas extremas, a mesma janela de 4 amostras")
        for ax, cab, hs, seq, cor, yc in grupos:
            self.play(Create(ax), FadeIn(cab), LaggedStart(*[GrowFromPoint(h, h[0].get_start()) for h in hs],
                                                           lag_ratio=0.06), run_time=1.4)

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
        leg = self.legenda("Rápida: picos e vales entram juntos na mesma soma e se cancelam (0)", leg, COR_RUIDO)
        self.wait(1.6)
        leg = self.legenda("Lenta: não há nada negativo para cancelar, a soma acumula (4)", leg, COR_LENTO)
        self.wait(1.6)
        leg = self.legenda("E a janela pode deslizar: o resultado não muda em nenhuma das duas", leg)
        self.play(*[t.animate.set_value(11) for t in trackers], run_time=4.5, rate_func=linear)
        self.wait(1.2)
        leg = self.legenda("Barrar o rápido e deixar passar o lento é exatamente um filtro passa-baixa", leg)
        self.wait(1.6)
        self.limpar()

        # --- a mesma ideia com um sinal de verdade ---------------------------
        self.titulo_cena("6 · O mesmo efeito em um sinal ruidoso")
        rng = np.random.default_rng(5)
        nmax = 60
        n = np.arange(nmax)
        lento = 1.0 * np.sin(TAU * n / 40)
        x = lento + 0.45 * rng.standard_normal(nmax)
        y = media_movel(x) / D
        ax = eixos_tempo(P(-1.0, 0.5), 10.4, 3.6, [0, 60, 10], [-2.2, 2.2, 1])
        r_ax = rotulo_eixo(ax, txt("entrada ruidosa (azul) e saída do CIC dividida por 4 (verde)", 19))
        r_t = txt("tempo (amostras) →", 17, COR_EIXO).next_to(ax, DOWN, buff=0.25).align_to(ax, RIGHT)
        c_x = VMobject().set_points_as_corners([ax.c2p(k, v) for k, v in zip(n, x)]).set_stroke(COR_X, 2)
        c_y = VMobject().set_points_as_corners([ax.c2p(k, v) for k, v in zip(n, y)]).set_stroke(COR_LENTO, 5)
        nota = txt("a saída foi dividida por 4 (o ganho intrínseco da janela)\n"
                   "só para poder ser comparada com a entrada na mesma escala",
                   20, line_spacing=0.85).move_to(P(0, -2.5))

        leg = self.legenda("Um seno lento afundado em ruído: é o caso real depois do ADC")
        self.play(Create(ax), FadeIn(r_ax), FadeIn(r_t))
        self.play(Create(c_x), run_time=2.2)
        leg = self.legenda("Os espinhos rápidos se diluem na soma; a variação lenta sobrevive", leg, COR_LENTO)
        self.play(Create(c_y), run_time=2.8)
        self.play(FadeIn(nota, shift=UP * 0.2))
        self.wait(1.4)
        leg = self.legenda("Mas quanto exatamente cada frequência é atenuada? É o que vamos medir agora", leg)
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 7
    def cena_resposta(self):
        """Construir o gráfico |H(f)| medindo uma senoide de cada vez."""
        self.titulo_cena("7 · Medindo a resposta em frequência")
        ax_t = eixos_tempo(P(-3.7, 0.8), 6.2, 3.0, [0, 24, 8], [-4.6, 4.6, 2])
        r_t = rotulo_eixo(ax_t, txt("entra uma senoide (azul), sai a soma das 4 últimas (verde)", 17))
        ax_f = Axes(x_range=[0, 0.5, 0.125], y_range=[0, 4.6, 1], x_length=5.0, y_length=3.0,
                    axis_config=EIXO_CFG).move_to(P(4.1, 0.8))
        r_f = rotulo_eixo(ax_f, txt("o ganho medido, frequência por frequência", 17))
        marcas = marcar_x(ax_f, [0, 0.125, 0.25, 0.375, 0.5], ["0", "f_s/8", "f_s/4", "3f_s/8", "f_s/2"], 14)
        fv = ValueTracker(0.004)

        def entrada():
            f = fv.get_value()
            return ax_t.plot(lambda t: np.cos(TAU * f * t), x_range=[0, 24, 0.04], color=COR_X, stroke_width=2)

        def amostras():
            f = fv.get_value()
            return VGroup(*[Dot(ax_t.c2p(k, np.cos(TAU * f * k)), radius=0.05, color=COR_X) for k in range(25)])

        def saida():
            f = fv.get_value()
            h = resposta(f)
            a, ph = abs(h), np.angle(h)
            return ax_t.plot(lambda t: a * np.cos(TAU * f * t + ph), x_range=[0, 24, 0.04],
                             color=COR_LENTO, stroke_width=4)

        def envelope():
            a = abs(resposta(fv.get_value()))
            return VGroup(*[DashedLine(ax_t.c2p(0, v * a), ax_t.c2p(24, v * a), color=COR_JANELA,
                                       stroke_width=1.5, dash_length=0.07) for v in (1, -1)])

        def curva():
            f = max(fv.get_value(), 0.004)
            return ax_f.plot(ganho, x_range=[0.0008, f, 0.0015], color=COR_COMB, stroke_width=4)

        def ponto():
            f = fv.get_value()
            g = ganho(f)
            return VGroup(DashedLine(ax_f.c2p(f, 0), ax_f.c2p(f, g), color=COR_JANELA, stroke_width=1.5),
                          Dot(ax_f.c2p(f, g), radius=0.09, color=COR_JANELA))

        leitura_f = VGroup(txt("f =", 20), DecimalNumber(0, num_decimal_places=3, font_size=30, color=COR_X),
                           txt("· f_s", 20)).arrange(RIGHT, buff=0.16).move_to(P(4.1, -1.35))
        leitura_f[1].add_updater(lambda m: m.set_value(fv.get_value()))
        leitura_g = VGroup(txt("ganho =", 20), DecimalNumber(4, num_decimal_places=2, font_size=30, color=COR_COMB)
                           ).arrange(RIGHT, buff=0.16).move_to(P(4.1, -1.95))
        leitura_g[1].add_updater(lambda m: m.set_value(ganho(fv.get_value())))
        leitura_n = VGroup(txt("amostras por período:", 20),
                           DecimalNumber(250, num_decimal_places=1, font_size=30, color=COR_JANELA)
                           ).arrange(RIGHT, buff=0.16).move_to(P(-3.7, -1.95))
        leitura_n[1].add_updater(lambda m: m.set_value(1.0 / max(fv.get_value(), 1e-3)))

        def marcar(rotulo):
            p1, p2 = ax_t.c2p(-0.25, 1.6), ax_t.c2p(3.25, -1.6)
            r = Rectangle(width=p2[0] - p1[0], height=p1[1] - p2[1], color=COR_JANELA,
                          stroke_width=3).move_to((p1 + p2) / 2)
            return VGroup(r, txt(rotulo, 19, COR_JANELA).move_to(P(-3.7, -1.25)))

        leg = self.legenda("A receita é sempre a mesma: entra uma senoide pura, mede-se a amplitude que sai")
        self.play(Create(ax_t), FadeIn(r_t), Create(ax_f), FadeIn(r_f), FadeIn(marcas), run_time=1.5)
        self.add(always_redraw(entrada), always_redraw(amostras), always_redraw(saida), always_redraw(envelope),
                 always_redraw(curva), always_redraw(ponto), leitura_f, leitura_g, leitura_n)
        self.wait(0.6)
        leg = self.legenda("Quase DC: 250 amostras por período, as 4 da janela são iguais → ganho 4", leg, COR_LENTO)
        self.wait(2.0)

        leg = self.legenda("Subindo a frequência: a senoide já curva dentro da janela e o ganho cai", leg, COR_COMB)
        self.play(fv.animate.set_value(0.0625), run_time=2.0, rate_func=smooth)
        self.wait(1.4)
        self.play(fv.animate.set_value(0.125), run_time=1.6, rate_func=smooth)
        leg = self.legenda("8 amostras por período: ganho 2,61 — já perdeu mais de um terço", leg, COR_COMB)
        self.wait(1.6)

        self.play(fv.animate.set_value(0.25), run_time=2.0, rate_func=smooth)
        m1 = marcar("+1  0  −1  0   →   soma 0")
        leg = self.legenda("f_s/4: exatamente 4 amostras por período — um período inteiro na janela", leg, COR_JANELA)
        self.play(Create(m1), run_time=1.0)
        self.wait(1.8)
        leg = self.legenda("A soma dá zero e a saída some: o primeiro zero do filtro", leg, COR_JANELA)
        self.wait(1.6)
        self.play(FadeOut(m1), run_time=0.5)

        self.play(fv.animate.set_value(0.375), run_time=1.8, rate_func=smooth)
        leg = self.legenda("Entre os zeros a soma não cancela tudo: sobra um resto (ganho ≈ 1,1)", leg, COR_JANELA)
        self.wait(1.8)

        self.play(fv.animate.set_value(0.5), run_time=1.8, rate_func=smooth)
        m2 = marcar("+1  −1  +1  −1   →   soma 0")
        leg = self.legenda("f_s/2: 2 amostras por período, dois períodos inteiros na janela → zero de novo",
                           leg, COR_JANELA)
        self.play(Create(m2), run_time=1.0)
        self.wait(2.0)
        self.play(FadeOut(m2), run_time=0.5)
        leg = self.legenda("Varrendo todas as frequências, o rastro do ponto é a resposta em frequência", leg,
                           COR_COMB)
        self.play(fv.animate.set_value(0.004), run_time=1.0)
        self.play(fv.animate.set_value(0.5), run_time=6.0, rate_func=linear)
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 8
    def cena_ler_grafico(self):
        """O gráfico que aparece em todo artigo sobre CIC, lido pedaço por pedaço."""
        self.titulo_cena("8 · Lendo o gráfico |H(f)|")
        ax = Axes(x_range=[0, 0.5, 0.125], y_range=[0, 4.6, 1], x_length=6.2, y_length=3.4,
                  axis_config=EIXO_CFG).move_to(P(-3.4, 0.6))
        curva = ax.plot(ganho, x_range=[0.0008, 0.5, 0.0015], color=COR_COMB, stroke_width=4)
        marcas = marcar_x(ax, [0, 0.125, 0.25, 0.375, 0.5], ["0", "f_s/8", "f_s/4", "3f_s/8", "f_s/2"], 15)
        r_y = txt("ganho", 17, COR_EIXO).next_to(ax.c2p(0, 4.6), UP, buff=0.08).shift(RIGHT * 0.3)
        r_x = txt("frequência do sinal de entrada →", 16, COR_EIXO).next_to(ax, DOWN, buff=1.25).align_to(ax, RIGHT)

        p_dc = VGroup(Dot(ax.c2p(0, 4), radius=0.09, color=COR_LENTO),
                      tex("4", COR_LENTO, 30).next_to(ax.c2p(0, 4), UR, buff=0.04))
        p_z1 = Dot(ax.c2p(0.25, 0), radius=0.09, color=COR_RUIDO)
        p_z2 = Dot(ax.c2p(0.5, 0), radius=0.09, color=COR_RUIDO)
        n_z1 = txt("1 período inteiro\nna janela", 14, COR_RUIDO, line_spacing=0.7
                   ).next_to(ax.c2p(0.25, 0), DOWN, buff=0.45)
        n_z2 = txt("2 períodos inteiros\nna janela", 14, COR_RUIDO, line_spacing=0.7
                   ).next_to(ax.c2p(0.5, 0), DOWN, buff=0.45).shift(LEFT * 0.35)
        area_p = ax.get_area(curva, x_range=[0.002, 0.2495], color=COR_LENTO, opacity=0.18)
        area_s = ax.get_area(curva, x_range=[0.2505, 0.4995], color=COR_RUIDO, opacity=0.25)
        p_lob = VGroup(Dot(ax.c2p(0.366, 1.089), radius=0.07, color=COR_RUIDO),
                       txt("1,1", 16, COR_RUIDO).next_to(ax.c2p(0.366, 1.089), UR, buff=0.06))

        itens = VGroup(
            txt("eixo x: a frequência da senoide que entra,\nde 0 (DC) até f_s/2, o limite de Nyquist",
                19, line_spacing=0.8),
            txt("eixo y: o ganho — por quanto a amplitude\ndaquela frequência é multiplicada", 19, line_spacing=0.8),
            txt("em DC o ganho é D = 4: o ganho intrínseco", 19, COR_LENTO),
            txt("zeros em f_s/4 e f_s/2: os múltiplos de f_s/D", 19, COR_RUIDO),
            txt("lóbulo principal: a banda que passa", 19, COR_LENTO),
            txt("lóbulo lateral: o que escapa (1,1 contra 4,\nou cerca de −11 dB)", 19, COR_RUIDO, line_spacing=0.8),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.34).move_to(P(1.05, 0.75), aligned_edge=LEFT)

        leg = self.legenda("Este é o gráfico que acabamos de construir, ponto a ponto")
        self.play(Create(ax), FadeIn(marcas), FadeIn(r_x), FadeIn(r_y))
        self.play(Create(curva), run_time=2.0)
        self.wait(0.8)

        passos = [(itens[0], None), (itens[1], None), (itens[2], p_dc), (itens[3], VGroup(p_z1, p_z2, n_z1, n_z2)),
                  (itens[4], area_p), (itens[5], VGroup(area_s, p_lob))]
        legendas = [
            ("Primeiro os eixos: o horizontal é a frequência do sinal que entra", GREY_A),
            ("O vertical é o ganho: 4 significa sair com 4 vezes a amplitude", GREY_A),
            ("Em DC as 4 amostras da janela são iguais e se somam: ganho D", COR_LENTO),
            ("Os zeros são as frequências que cabem inteiras na janela", COR_RUIDO),
            ("O lóbulo principal é a banda que o filtro deixa passar", COR_LENTO),
            ("No lóbulo lateral o cancelamento é parcial: é o ponto fraco do CIC", COR_RUIDO),
        ]
        for (item, marca), (texto, cor) in zip(passos, legendas):
            leg = self.legenda(texto, leg, cor)
            if marca is None:
                self.play(FadeIn(item, shift=RIGHT * 0.2), run_time=0.8)
            else:
                self.play(FadeIn(item, shift=RIGHT * 0.2), FadeIn(marca), run_time=0.9)
            self.wait(1.3)

        # --- a fórmula fechada -----------------------------------------------
        leg = self.legenda("Somar D senoides defasadas tem forma fechada — é esta fórmula", leg, COR_COMB)
        self.play(FadeOut(itens), run_time=0.7)
        form = tex_partes([(r"|H(f)| = \left|\frac{", WHITE), (r"\sin(\pi D f / f_s)", COR_RUIDO),
                           (r"}{", WHITE), (r"\sin(\pi f / f_s)", COR_LENTO), (r"}\right|", WHITE)], 34
                          ).move_to(P(3.9, 1.6))
        exp1 = txt("o numerador zera sempre que D·f/f_s é inteiro:\n"
                   "são os zeros, em f_s/D, 2f_s/D, 3f_s/D …", 19, COR_RUIDO, line_spacing=0.8).move_to(P(3.9, 0.2))
        exp2 = txt("em f = 0 numerador e denominador zeram juntos\ne a razão vale exatamente D = 4",
                   19, COR_LENTO, line_spacing=0.8).move_to(P(3.9, -1.0))
        exp3 = txt("é o mesmo formato de um sinc, mas amostrado:\no \"sinc digital\" (núcleo de Dirichlet)",
                   19, GREY_A, line_spacing=0.8).move_to(P(3.9, -2.2))
        self.play(Write(form), run_time=1.6)
        self.play(FadeIn(exp1, shift=UP * 0.15))
        self.wait(1.4)
        self.play(FadeIn(exp2, shift=UP * 0.15))
        self.wait(1.4)
        self.play(FadeIn(exp3, shift=UP * 0.15))
        leg = self.legenda("Com a janela R·D no lugar de 4, ela descreve qualquer CIC de um estágio", leg, COR_COMB)
        self.wait(2.2)
        self.limpar()

    # ================================================================== CENA 9
    def cena_outros_fatores(self):
        """O mesmo filtro com D = 2, 4, 8 e 16: na frequência e no tempo."""
        titulo = self.titulo_cena("9 · Agora decimando: R = 2, 4, 8, 16")
        ax = Axes(x_range=[0, 0.5, 0.125], y_range=[0, 1.15, 0.25], x_length=7.0, y_length=3.2,
                  axis_config=EIXO_CFG).move_to(P(-2.4, 0.7))
        marcas = marcar_x(ax, [0, 0.125, 0.25, 0.375, 0.5], ["0", "f_s/8", "f_s/4", "3f_s/8", "f_s/2"], 15)
        r_ax = rotulo_eixo(ax, txt("ganho dividido por R·D, para as curvas ficarem comparáveis", 17))

        def curva_de(d):
            return ax.plot(lambda f: ganho(f, d) / d, x_range=[0.0008, 0.5, 0.0012], color=COR_COMB, stroke_width=4)

        def zeros_de(d):
            return VGroup(*[Dot(ax.c2p(k / d, 0), radius=0.07, color=COR_RUIDO)
                            for k in range(1, int(0.5 * d) + 1)])

        def painel_de(d):
            return VGroup(tex(rf"R = {d}", COR_DEC, 38),
                          txt(f"janela R·D = {d} amostras", 20, WHITE),
                          txt(f"ganho em DC = {d}", 20, WHITE),
                          txt(f"primeiro zero = f_s/{d}", 20, COR_RUIDO),
                          txt(f"taxa de saída = f_s/{d}", 20, WHITE),
                          txt(f"banda útil ≈ f_s/{2 * d}", 20, WHITE),
                          ).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(P(1.9, 0.7), aligned_edge=LEFT)

        curva, zeros, painel = curva_de(2), zeros_de(2), painel_de(2)
        leg = self.legenda("Até aqui a janela de 4 vinha do comb: R = 1, D = 4, sem jogar nenhuma amostra fora")
        self.play(Create(ax), FadeIn(marcas), FadeIn(r_ax))
        leg = self.legenda("Agora o CIC decima: a janela passa a vir do R, e o comb fica com D = 1", leg, COR_DEC)
        self.parametros(2, 1, 1)
        self.play(Create(curva), FadeIn(zeros), FadeIn(painel), run_time=1.5)
        leg = self.legenda("Com R = 2 a janela é mínima: filtro larguíssimo, quase não filtra", leg, COR_COMB)
        self.wait(1.8)
        for d, texto, cor in [(4, "R = 4: a mesma janela de 4 do nosso exemplo — zeros em f_s/4 e f_s/2",
                               COR_COMB),
                              (8, "R = 8: o dobro de zeros e metade da banda", COR_COMB),
                              (16, "R = 16: estreitíssimo — e a saída sai 16 vezes mais devagar", COR_COMB)]:
            leg = self.legenda(texto, leg, cor)
            self.parametros(d, 1, 1)
            self.play(Transform(curva, curva_de(d)), Transform(zeros, zeros_de(d)),
                      Transform(painel, painel_de(d)), run_time=1.6)
            self.wait(1.6)
        leg = self.legenda("A regra é sempre a mesma: primeiro zero em f_s/(R·D) e ganho R·D em DC", leg)
        self.wait(1.8)
        self.play(FadeOut(VGroup(ax, marcas, r_ax, curva, zeros, painel)), run_time=0.8)

        # --- o mesmo sinal, quatro fatores -----------------------------------
        self.trocar_titulo(titulo, "9 · O mesmo sinal com quatro fatores")
        self.parametros(2, 1, 1)
        rng = np.random.default_rng(11)
        nmax = 160
        n = np.arange(nmax)
        x = np.sin(TAU * n / 40) + 0.5 * rng.standard_normal(nmax)
        ys = [2.55, 1.45, 0.35, -0.75, -1.85]

        def linha(yc, dados, cor, d=None):
            a = eixos_tempo(P(-1.6, yc), 8.6, 0.85, [0, nmax, 40], [-2.3, 2.3, 2])
            c = VMobject().set_points_as_corners([a.c2p(k, v) for k, v in zip(n, dados)])
            c.set_stroke(cor, 2 if d is None else 1.5, opacity=1 if d is None else 0.45)
            g = VGroup(a, c)
            if d is not None:
                guardadas = [k for k in range(nmax) if (k + 1) % d == 0]
                g.add(VMobject().set_points_as_corners([a.c2p(k, dados[k]) for k in guardadas]
                                                       ).set_stroke(COR_LENTO, 3.5))
                g.add(VGroup(*[Dot(a.c2p(k, dados[k]), radius=0.055, color=COR_LENTO) for k in guardadas]))
            return g

        rotulos = []
        grupos = [linha(ys[0], x, COR_X)]
        rotulos.append(txt("entrada em f_s\n160 amostras", 16, COR_X, line_spacing=0.75
                           ).move_to(P(3.3, ys[0]), aligned_edge=LEFT))
        for k, d in enumerate([2, 4, 8, 16]):
            grupos.append(linha(ys[k + 1], media_movel(x, d) / d, GREY_B, d))
            rotulos.append(txt(f"R = {d}\n{nmax // d} amostras (f_s/{d})", 16, COR_LENTO, line_spacing=0.75
                               ).move_to(P(3.3, ys[k + 1]), aligned_edge=LEFT))

        leg = self.legenda("A mesma entrada ruidosa passando por quatro CICs diferentes", leg)
        self.play(Create(grupos[0][0]), FadeIn(rotulos[0]))
        self.play(Create(grupos[0][1]), run_time=1.6)
        for k, d in enumerate([2, 4, 8, 16]):
            leg = self.legenda({2: "R = 2: quase nada muda, só duas amostras somadas",
                                4: "R = 4: o ruído já cai bastante e a onda continua inteira",
                                8: "R = 8: bem mais limpo, com 1 amostra de saída a cada 8",
                                16: "R = 16: liso, mas a própria onda já perdeu cerca de 24% da amplitude"
                                }[d], leg, COR_LENTO)
            self.parametros(d, 1, 1)
            self.play(FadeIn(grupos[k + 1], shift=UP * 0.1), FadeIn(rotulos[k + 1]), run_time=1.2)
            self.wait(1.4)
        leg = self.legenda("Esse é o compromisso: mais suave e mais barato, porém mais lento e com droop", leg)
        self.wait(2.2)
        self.limpar()

    # ================================================================= CENA 10
    def cena_aliasing(self):
        """Por que justamente o CIC é o filtro certo para decimar."""
        self.titulo_cena("10 · Por que o CIC serve para decimar")
        self.parametros(4, 1, 1)
        ax = Axes(x_range=[0, 1, 0.25], y_range=[0, 1.15, 1], x_length=11.6, y_length=2.4,
                  axis_config=EIXO_CFG).move_to(P(-0.3, 1.3))
        marcas = marcar_x(ax, [0, 0.25, 0.5, 0.75, 1.0], ["0", "f_s/4", "f_s/2", "3f_s/4", "f_s"], 16)
        r_ax = rotulo_eixo(ax, txt("espectro do sinal que chega ao CIC", 18))

        util = ax.plot(lambda f: np.exp(-(f / 0.035) ** 2) + np.exp(-((f - 1) / 0.035) ** 2),
                       x_range=[0, 1, 0.002], color=COR_LENTO, stroke_width=3)
        area_util = ax.get_area(util, x_range=[0, 0.1], color=COR_LENTO, opacity=0.35)
        r_util = txt("sinal útil", 17, COR_LENTO).next_to(ax.c2p(0.03, 1.0), UR, buff=0.06)
        ruido = Rectangle(width=ax.c2p(1, 0)[0] - ax.c2p(0, 0)[0],
                          height=ax.c2p(0, 0.32)[1] - ax.c2p(0, 0)[1],
                          stroke_width=0, fill_color=GREY_B, fill_opacity=0.3
                          ).move_to((ax.c2p(0, 0) + ax.c2p(1, 0.32)) / 2)
        r_ruido = txt("ruído e sinais indesejados espalhados por toda a banda", 17, GREY_B
                      ).move_to(ax.c2p(0.55, 0.55))

        def banda(c):
            return Rectangle(width=ax.c2p(0.07, 0)[0] - ax.c2p(0, 0)[0],
                             height=ax.c2p(0, 0.32)[1] - ax.c2p(0, 0)[1],
                             color=COR_RUIDO, stroke_width=2, fill_color=COR_RUIDO, fill_opacity=0.45
                             ).move_to((ax.c2p(c, 0) + ax.c2p(c, 0.32)) / 2)

        bandas = VGroup(*[banda(c) for c in (0.25, 0.5, 0.75)])
        setas = VGroup(*[CurvedArrow(ax.c2p(c, 0) + DOWN * 0.6, ax.c2p(0.02, 0) + DOWN * 0.6,
                                     angle=0.55, color=COR_RUIDO, stroke_width=3, tip_length=0.18)
                         for c in (0.25, 0.5, 0.75)])
        resp = ax.plot(lambda f: ganho(f) / D, x_range=[0.0008, 0.9992, 0.0015], color=COR_COMB, stroke_width=3.5)
        r_resp = txt("resposta do CIC, janela R·D = 4", 18, COR_COMB).next_to(ax.c2p(0.13, 0.75), RIGHT, buff=0.1)

        nota = txt("decimar por 4 = ficar com 1 amostra a cada 4. No espectro, tudo o que estiver em torno de\n"
                   "f_s/4, f_s/2 e 3f_s/4 dobra para cima da banda base — e aí não há mais como separar",
                   20, line_spacing=0.85).move_to(P(0, -2.0))
        nota2 = txt("os zeros do CIC caem exatamente no centro dessas bandas:\n"
                    "ele é o filtro anti-aliasing sob medida para decimar por R",
                    21, COR_COMB, line_spacing=0.85).move_to(P(0, -2.0))
        nota3 = txt("nas bordas dessas bandas a atenuação é bem menor:\n"
                    "o resto é limpo depois por um FIR, já na taxa baixa",
                    21, line_spacing=0.85).move_to(P(0, -2.0))

        leg = self.legenda("O que chega ao CIC: o sinal útil na banda base e lixo no resto")
        self.play(Create(ax), FadeIn(marcas), FadeIn(r_ax))
        self.play(FadeIn(ruido), FadeIn(r_ruido), Create(util), FadeIn(area_util), FadeIn(r_util), run_time=1.6)
        leg = self.legenda("Jogar amostras fora dobra o espectro: as bandas marcadas caem em cima do sinal",
                           leg, COR_RUIDO)
        self.play(FadeIn(bandas), run_time=1.0)
        self.play(FadeIn(nota, shift=UP * 0.15), LaggedStart(*[Create(s) for s in setas], lag_ratio=0.3),
                  run_time=2.0)
        self.wait(2.2)
        leg = self.legenda("Agora o detalhe bonito: olhe onde estão os zeros do CIC", leg, COR_COMB)
        self.play(Create(resp), FadeIn(r_resp), run_time=2.0)
        self.play(FadeOut(nota), FadeIn(nota2, shift=UP * 0.15))
        self.wait(1.4)
        self.play(*[Indicate(b, color=COR_COMB, scale_factor=1.1) for b in bandas], run_time=1.2)
        leg = self.legenda("O que ia dobrar para cima do sinal é justamente o que o CIC apaga", leg, COR_COMB)
        self.play(*[b.animate.stretch_to_fit_height(0.12).set_fill(opacity=0.35).move_to(ax.c2p(c, 0) + UP * 0.12)
                    for b, c in zip(bandas, (0.25, 0.5, 0.75))],
                  FadeOut(setas), run_time=1.5)
        self.wait(1.6)
        self.play(FadeOut(nota2), FadeIn(nota3, shift=UP * 0.15))
        leg = self.legenda("Por isso a cadeia padrão é CIC primeiro, FIR depois", leg)
        self.wait(2.2)
        self.limpar()

    # ================================================================= CENA 11
    def cena_decimacao(self):
        """Onde o decimador entra na cadeia e por que o comb pode ser z^-1."""
        titulo = self.titulo_cena("11 · Onde o decimador entra")
        self.parametros(4, 1, 1)
        yA, yB = 2.55, 1.25
        x_in_a = tex(r"x[n]", COR_X, 24).move_to(P(-6.5, yA))
        int_a = caixa("Integrador\nf_s", 1.9, 0.72, COR_INT, 15).move_to(P(-5.0, yA))
        comb_a = caixa("Comb  z⁻⁴\nf_s", 2.0, 0.72, COR_COMB, 15).move_to(P(-2.7, yA))
        dec_a = caixa_tex(r"\downarrow 4", 0.8, 0.72, COR_DEC, 26).move_to(P(-0.6, yA))
        out_a = tex(r"y[m]", COR_COMB, 24).move_to(P(0.75, yA))
        fios_a = VGroup(fio([P(-6.15, yA), P(-5.95, yA)]), fio([P(-4.05, yA), P(-3.7, yA)]),
                        fio([P(-1.7, yA), P(-1.0, yA)]), fio([P(-0.2, yA), P(0.4, yA)]))
        nota_a = txt("o comb trabalha em f_s e 3 de cada\n4 resultados vão direto para o lixo",
                     17, line_spacing=0.8).move_to(P(1.5, yA), aligned_edge=LEFT)

        x_in_b = tex(r"x[n]", COR_X, 24).move_to(P(-6.5, yB))
        int_b = caixa("Integrador\nf_s", 1.9, 0.72, COR_INT, 15).move_to(P(-5.0, yB))
        dec_b = caixa_tex(r"\downarrow 4", 0.8, 0.72, COR_DEC, 26).move_to(P(-2.9, yB))
        comb_b = caixa("Comb  z⁻¹\nf_s/4", 2.0, 0.72, COR_COMB, 15).move_to(P(-1.0, yB))
        out_b = tex(r"y[m]", COR_COMB, 24).move_to(P(0.9, yB))
        fios_b = VGroup(fio([P(-6.15, yB), P(-5.95, yB)]), fio([P(-4.05, yB), P(-3.3, yB)]),
                        fio([P(-2.5, yB), P(-2.0, yB)]), fio([P(0.0, yB), P(0.55, yB)]))
        nota_b = txt("o comb trabalha em f_s/4 e só\ncalcula o que vai ser usado",
                     17, line_spacing=0.8).move_to(P(1.5, yB), aligned_edge=LEFT)

        equiv = VGroup(txt("no tempo lento,", 20), tex(r"z^{-1}", COR_COMB, 30), txt("já é", 20),
                       tex(r"z^{-4}", COR_INT, 30), txt("no tempo rápido", 20)
                       ).arrange(RIGHT, buff=0.2).move_to(P(0, 0.35))

        leg = self.legenda("O caminho óbvio: filtrar tudo e só então jogar amostras fora")
        self.play(FadeIn(VGroup(x_in_a, int_a, comb_a, dec_a, out_a, fios_a)), run_time=1.3)
        self.play(FadeIn(nota_a, shift=RIGHT * 0.2))
        self.wait(1.6)
        leg = self.legenda("O truque de Hogenauer: colocar o decimador no meio do CIC", leg, COR_DEC)
        self.play(FadeIn(VGroup(x_in_b, int_b, dec_b, comb_b, out_b, fios_b)), run_time=1.3)
        self.play(FadeIn(nota_b, shift=RIGHT * 0.2))
        self.wait(1.4)
        leg = self.legenda("E o comb passa a precisar de 1 único registrador, não de 4", leg, COR_COMB)
        self.play(FadeIn(equiv, shift=UP * 0.2), run_time=1.2)
        self.wait(2.0)

        # --- a prova no tempo -------------------------------------------------
        self.trocar_titulo(titulo, "11 · Por que dá no mesmo")
        self.play(FadeOut(VGroup(nota_a, nota_b)), equiv.animate.move_to(P(3.3, 0.4)), run_time=0.8)
        rng = np.random.default_rng(2)
        xs = list(rng.integers(0, 4, 16))
        I = integrar(xs)
        ax = eixos_tempo(P(-0.6, -0.95), 11.6, 2.0, [0, 16, 1], [0, max(I) + 2, 10])
        r_ax = rotulo_eixo(ax, txt("I[n] no tempo rápido (todas as amostras)", 17, COR_INT))
        hs = VGroup(*[haste(ax, k + 1, I[k], COR_INT, 0.06, 3) for k in range(16)])
        lentas = [k for k in range(16) if (k + 1) % 4 == 0]

        leg = self.legenda("O integrador continua acumulando na taxa rápida, amostra por amostra", leg, COR_INT)
        self.play(Create(ax), FadeIn(r_ax))
        self.play(LaggedStart(*[GrowFromPoint(h, ax.c2p(k + 1, 0)) for k, h in enumerate(hs)], lag_ratio=0.07),
                  run_time=2.0)
        leg = self.legenda("O decimador deixa o comb ver só 1 de cada 4 desses valores", leg, COR_DEC)
        self.play(*[hs[k].animate.set_opacity(0.15) for k in range(16) if k not in lentas],
                  *[hs[k].animate.set_color(COR_DEC) for k in lentas], run_time=1.4)
        self.wait(1.2)
        leg = self.legenda("Para o comb, a amostra anterior é a de 4 ciclos rápidos atrás", leg, COR_COMB)
        blocos = VGroup()
        for j, k in enumerate(lentas):
            ini = k - 3
            chave = BraceBetweenPoints(ax.c2p(ini + 0.6, -0.3), ax.c2p(k + 1.4, -0.3), DOWN, color=COR_COMB)
            soma = sum(xs[ini:k + 1])
            r = tex(rf"y[{j}] = {soma}", COR_COMB, 24).next_to(chave, DOWN, buff=0.05)
            blocos.add(VGroup(chave, r))
            dif = Arrow(ax.c2p(k + 1, I[k - 4] if k >= 4 else 0), ax.c2p(k + 1, I[k]), buff=0, color=COR_COMB,
                        stroke_width=4, max_tip_length_to_length_ratio=0.15)
            self.play(GrowArrow(dif), FadeIn(blocos[-1]), run_time=0.9)
            self.wait(0.3)
        leg = self.legenda("Cada saída é a soma de um bloco de 4 entradas: o mesmo resultado, a 1/4 da taxa",
                           leg, COR_COMB)
        self.wait(2.0)
        leg = self.legenda("Na interpolação a ordem se inverte: comb → ↑R → integrador", leg, GREY_A)
        self.wait(1.8)
        self.limpar()

    # ================================================================= CENA 12
    def cena_atraso_comb(self):
        """D, o atraso diferencial, com o decimador no meio: a janela vale R·D."""
        titulo = self.titulo_cena("12 · O atraso diferencial D")
        R_DEC = 4

        # --- A: as três letras, e a janela como produto R·D ------------------
        cadeia = VGroup(tex(r"x[n]", COR_X, 24), tex(r"\rightarrow", GREY_A, 24),
                        caixa("Integrador\nf_s", 1.8, 0.72, COR_INT, 15), tex(r"\rightarrow", GREY_A, 24),
                        caixa_tex(r"\downarrow R", 0.85, 0.72, COR_DEC, 24), tex(r"\rightarrow", GREY_A, 24),
                        caixa("Comb  z⁻ᴰ\nf_s/R", 1.8, 0.72, COR_COMB, 15), tex(r"\rightarrow", GREY_A, 24),
                        tex(r"y[m]", COR_COMB, 24)).arrange(RIGHT, buff=0.2).move_to(P(0, 2.15))
        realce = SurroundingRectangle(cadeia[6], color=COR_COMB, buff=0.1, corner_radius=0.1)
        nota_d = txt("o comb da taxa lenta ficou com um registrador só, ou seja D = 1 — "
                     "mas ele pode ter z⁻ᴰ", 22).move_to(P(0, 1.15))
        relacao = tex_partes([(r"\text{janela no tempo rápido} = ", WHITE), (r"R", COR_DEC),
                              (r"\cdot", WHITE), (r"D", COR_COMB), (r"\text{ amostras}", WHITE)], 34
                             ).move_to(P(0, 1.0))

        # a mesma janela de 4, obtida de dois jeitos: é o que fecha a ideia
        col_x, lin_y = [0.1, 1.5, 3.2], [0.0, -0.7, -1.4]
        tabela = VGroup(Line(P(-3.5, -0.35), P(3.9, -0.35), color=COR_EIXO, stroke_width=1.5))
        for k, (sig, cor) in enumerate([("R", COR_DEC), ("D", COR_COMB), (r"R \cdot D", COR_JANELA)]):
            tabela.add(tex(sig, cor, 32).move_to(P(col_x[k], lin_y[0])))
        for j, (rot, vr, vd) in enumerate([("sem decimar", 1, 4), ("decimando por 4", 4, 1)], start=1):
            tabela.add(txt(rot, 21, GREY_B).move_to(P(-0.9, lin_y[j]), aligned_edge=RIGHT))
            for k, (v, cor) in enumerate([(vr, COR_DEC), (vd, COR_COMB), (vr * vd, COR_JANELA)]):
                tabela.add(tex(str(v), cor, 30).move_to(P(col_x[k], lin_y[j])))
        nota_tab = txt("a mesma janela de 4 amostras, vinda de dois lugares diferentes", 21, COR_JANELA
                       ).next_to(tabela, DOWN, buff=0.45)
        bloco = VGroup(tabela, nota_tab).move_to(P(0, -1.25))

        leg = self.legenda("Dos três parâmetros, o D é o único que ainda não mexemos")
        self.play(FadeIn(cadeia), run_time=1.2)
        self.play(Create(realce), FadeIn(nota_d))
        leg = self.legenda("D é o atraso diferencial: quantos registradores o comb tem na taxa lenta",
                           leg, COR_COMB)
        self.wait(2.0)
        leg = self.legenda("E como cada passo lento vale R rápidos, a janela equivalente é R·D", leg)
        self.play(FadeOut(nota_d, shift=UP * 0.2), run_time=0.5)
        self.play(Write(relacao), run_time=1.3)
        self.wait(1.6)
        leg = self.legenda("A janela do nosso exemplo é 4 desde o começo: só mudou de onde ela vem",
                           leg, COR_JANELA)
        self.play(FadeIn(tabela, shift=UP * 0.15), run_time=1.0)
        self.wait(1.2)
        self.play(FadeIn(nota_tab, shift=UP * 0.15), run_time=0.8)
        self.wait(2.2)
        self.play(FadeOut(VGroup(cadeia, realce, relacao, bloco)), run_time=0.8)

        # --- B: o que D faz com o gráfico, com R fixo ------------------------
        self.trocar_titulo(titulo, "12 · O que D faz com o gráfico")
        ax = Axes(x_range=[0, 0.5, 0.125], y_range=[0, 1.15, 0.25], x_length=7.3, y_length=2.9,
                  axis_config=EIXO_CFG).move_to(P(-2.4, 0.55))
        marcas = marcar_x(ax, [0, 0.0625, 0.125, 0.25, 0.375, 0.5],
                          ["0", "f_s/16", "f_s/8", "f_s/4", "3f_s/8", "f_s/2"], 14, 0.12)

        def faixa(a, b, cor, op=0.2):
            return Polygon(ax.c2p(a, 0), ax.c2p(b, 0), ax.c2p(b, 1.12), ax.c2p(a, 1.12),
                           stroke_width=0).set_fill(cor, opacity=op)

        util = faixa(0, 0.0625, COR_LENTO, 0.22)
        r_util = txt("banda\nútil", 16, COR_LENTO, line_spacing=0.8).next_to(ax.c2p(0.031, 1.12), UP, buff=0.08)
        dobram = VGroup(faixa(0.1875, 0.3125, COR_RUIDO, 0.17), faixa(0.4375, 0.5, COR_RUIDO, 0.17))
        r_dobram = txt("faixas que dobram ao decimar por 4", 16, COR_RUIDO
                       ).next_to(ax.c2p(0.33, 1.12), UP, buff=0.08)
        nyq = DashedLine(ax.c2p(0.125, 0), ax.c2p(0.125, 1.12), color=COR_JANELA, stroke_width=3,
                         dash_length=0.1)

        def curva_de(d):
            L = R_DEC * d
            return ax.plot(lambda f, L=L: ganho(f, L) / L, x_range=[0.0006, 0.5, 0.0006],
                           color=COR_COMB, stroke_width=4)

        def zeros_de(d):
            L = R_DEC * d
            return VGroup(*[Dot(ax.c2p(k / L, 0), radius=0.065, color=COR_RUIDO)
                            for k in range(1, L // 2 + 1)])

        def topo_banda(d):
            g = ganho(0.0625, R_DEC * d) / (R_DEC * d)
            if g < 1e-6:
                return "zero"
            return f"{20 * np.log10(g):.1f} dB".replace(".", ",").replace("-", "−")

        def painel_de(d):
            L = R_DEC * d
            return VGroup(tex(rf"D = {d}", COR_COMB, 38),
                          txt(f"janela R·D = {L} amostras", 19, WHITE),
                          txt(f"1º zero em f_s/{L}", 19, COR_RUIDO),
                          txt(f"topo da banda útil: {topo_banda(d)}", 19, COR_LENTO),
                          txt(f"registradores no comb: {d}", 19, WHITE),
                          ).arrange(DOWN, aligned_edge=LEFT, buff=0.36).move_to(P(1.4, 0.5), aligned_edge=LEFT)

        curva, zeros, painel = curva_de(1), zeros_de(1), painel_de(1)
        leg = self.legenda("R continua 4: a taxa de saída é a mesma nos três casos — só o filtro muda", leg)
        self.parametros(4, 1, 1)
        self.play(Create(ax), FadeIn(marcas))
        self.play(FadeIn(util), FadeIn(r_util), FadeIn(dobram), FadeIn(r_dobram), Create(nyq))
        leg = self.legenda("Em verde o que queremos guardar; em vermelho o que vai dobrar por cima", leg)
        self.wait(1.4)
        self.play(Create(curva), FadeIn(zeros), FadeIn(painel), run_time=1.5)
        leg = self.legenda("D = 1: um zero no centro de cada faixa vermelha — é o nosso exemplo", leg, COR_COMB)
        self.wait(2.0)

        leg = self.legenda("D = 2: o dobro de zeros, e o primeiro cai exatamente no tracejado", leg, COR_COMB)
        self.parametros(4, 2, 1)
        self.play(Transform(curva, curva_de(2)), Transform(zeros, zeros_de(2)),
                  Transform(painel, painel_de(2)), run_time=1.8)
        r_nyq = txt("Nyquist da saída", 16, COR_JANELA).next_to(marcas[2], DOWN, buff=0.14)
        self.play(FadeIn(r_nyq), nyq.animate.set_stroke(width=5))
        leg = self.legenda("É o limite natural: o zero pousa na borda do que a saída consegue representar",
                           leg, COR_JANELA)
        self.wait(2.2)

        leg = self.legenda("D = 4: os zeros continuam andando para a esquerda — e invadem o verde", leg, COR_RUIDO)
        self.parametros(4, 4, 1)
        self.play(Transform(curva, curva_de(4)), Transform(zeros, zeros_de(4)),
                  Transform(painel, painel_de(4)), run_time=1.8)
        self.wait(2.4)
        leg = self.legenda("O filtro passou a apagar o próprio sinal que deveria preservar", leg, COR_RUIDO)
        self.wait(2.0)
        self.play(FadeOut(VGroup(ax, marcas, util, r_util, dobram, r_dobram, nyq, r_nyq,
                                 curva, zeros, painel)), run_time=0.8)

        # --- C: o veredito ----------------------------------------------------
        self.trocar_titulo(titulo, "12 · Por que D real é 1 ou 2")
        col_x = [1.6, 3.5, 5.4]
        lin_y = [1.95, 1.2, 0.45, -0.3, -1.05]
        tab = VGroup()
        for k, d in enumerate((1, 2, 4)):
            tab.add(tex(rf"D = {d}", COR_COMB if d < 4 else COR_RUIDO, 30).move_to(P(col_x[k], lin_y[0])))
        for c, (rot, vals) in enumerate([
                ("janela equivalente R·D", ["4 amostras", "8 amostras", "16 amostras"]),
                ("1º zero", ["f_s/4", "f_s/8", "f_s/16"]),
                ("topo da banda útil", ["−0,9 dB", "−3,9 dB", "zero"]),
                ("pior vazamento ao decimar", ["−9,9 dB", "−13,0 dB", "−20,1 dB"])], start=1):
            tab.add(txt(rot, 19, GREY_B).move_to(P(0.5, lin_y[c]), aligned_edge=RIGHT))
            for k, v in enumerate(vals):
                cor = COR_RUIDO if (c == 3 and k == 2) else WHITE
                tab.add(txt(v, 19, cor).move_to(P(col_x[k], lin_y[c])))

        vereditos = VGroup(
            txt("D = 2 põe o primeiro zero exatamente no Nyquist da saída: é o limite natural,\n"
                "e compra 3 dB de rejeição a mais no que vai dobrar", 21, COR_JANELA, line_spacing=0.85),
            txt("D = 4 rejeita ainda melhor, mas põe um zero dentro da banda útil —\n"
                "por isso um CIC real usa D = 1 ou D = 2, e para rejeitar mais aumenta-se M", 21, COR_RUIDO,
                line_spacing=0.85),
        ).arrange(DOWN, buff=0.4).move_to(P(0, -2.4))

        moldura_ex = RoundedRectangle(corner_radius=0.12, width=1.75, height=3.7, stroke_width=2,
                                      color=COR_JANELA).move_to(P(col_x[0], 0.45))
        r_ex = txt("o exemplo do vídeo", 17, COR_JANELA).move_to(P(col_x[0], 2.55))

        leg = self.legenda("Lado a lado, com R = 4 fixo e a mesma banda útil", leg)
        self.parametros(4, 1, 1)
        self.play(FadeIn(tab), run_time=1.4)
        self.wait(1.2)
        leg = self.legenda("A primeira coluna é o CIC que o vídeo usou o tempo todo: janela R·D = 4",
                           leg, COR_JANELA)
        self.play(Create(moldura_ex), FadeIn(r_ex), run_time=1.0)
        self.wait(1.8)
        leg = self.legenda("Mais D é mais rejeição, pago em banda útil", leg)
        self.play(FadeIn(vereditos[0], shift=UP * 0.15))
        self.wait(2.0)
        self.play(FadeIn(vereditos[1], shift=UP * 0.15))
        self.wait(2.8)
        self.limpar()

    # ================================================================= CENA 13
    def cena_estagios(self):
        """O número de estágios M: o que é, o que faz com a janela, com |H(f)| e com o sinal."""
        titulo = self.titulo_cena("13 · O número de estágios M")
        self.parametros(4, 1, 1)

        # --- A: um estágio é um CIC inteiro; M estágios é repeti-lo ----------
        um = VGroup(tex(r"x[n]", COR_X, 26), tex(r"\rightarrow", GREY_A, 26),
                    caixa("Integrador", 1.9, 0.6, COR_INT, 19), tex(r"\rightarrow", GREY_A, 26),
                    caixa("Comb", 1.3, 0.6, COR_COMB, 19), tex(r"\rightarrow", GREY_A, 26),
                    tex(r"y[n]", COR_COMB, 26)).arrange(RIGHT, buff=0.22).move_to(P(0, 2.15))
        moldura = SurroundingRectangle(VGroup(um[2], um[4]), color=COR_JANELA, buff=0.18, corner_radius=0.1)
        r_um = txt("um estágio = um integrador + um comb", 19, COR_JANELA).next_to(moldura, UP, buff=0.14)

        casc = VGroup(tex(r"x[n]", COR_X, 24), tex(r"\rightarrow", GREY_A, 24),
                      caixa("estágio 1", 1.75, 0.6, COR_JANELA, 18), tex(r"\rightarrow", GREY_A, 24),
                      caixa("estágio 2", 1.75, 0.6, COR_JANELA, 18), tex(r"\rightarrow", GREY_A, 24),
                      caixa("estágio 3", 1.75, 0.6, COR_JANELA, 18), tex(r"\rightarrow", GREY_A, 24),
                      tex(r"y[n]", COR_COMB, 24)).arrange(RIGHT, buff=0.18).move_to(P(0, 0.6))
        r_casc = txt("M estágios: a saída de um é a entrada do seguinte", 19).next_to(casc, DOWN, buff=0.2)
        nota_n = txt("parte da literatura chama esse número de N — é o mesmo parâmetro", 18, GREY_B
                     ).next_to(r_casc, DOWN, buff=0.14)

        yh = -1.55
        xs_i, xs_c = [-3.15, -2.25, -1.35], [0.95, 1.85, 2.75]
        hog = VGroup(tex(r"x[n]", COR_X, 22).move_to(P(-4.2, yh)),
                     *[caixa("I", 0.75, 0.58, COR_INT, 19).move_to(P(x, yh)) for x in xs_i],
                     caixa_tex(r"\downarrow R", 0.85, 0.58, COR_DEC, 22).move_to(P(-0.2, yh)),
                     *[caixa("C", 0.75, 0.58, COR_COMB, 19).move_to(P(x, yh)) for x in xs_c],
                     tex(r"y[m]", COR_COMB, 22).move_to(P(3.85, yh)))
        ch_i = BraceBetweenPoints(P(-3.55, yh - 0.36), P(-0.95, yh - 0.36), DOWN, color=COR_INT)
        r_i = txt("M integradores", 16, COR_INT).next_to(ch_i, DOWN, buff=0.06)
        ch_c = BraceBetweenPoints(P(0.55, yh - 0.36), P(3.15, yh - 0.36), DOWN, color=COR_COMB)
        r_c = txt("M combs", 16, COR_COMB).next_to(ch_c, DOWN, buff=0.06)

        leg = self.legenda("Tudo até aqui foi um CIC de um estágio só: M = 1")
        self.play(FadeIn(um), run_time=1.0)
        self.play(Create(moldura), FadeIn(r_um))
        leg = self.legenda("Um CIC de verdade repete esse bloco: é o \"Cascaded\" do nome", leg, COR_JANELA)
        self.play(FadeIn(casc, shift=DOWN * 0.15), run_time=1.2)
        self.play(FadeIn(r_casc), FadeIn(nota_n))
        self.wait(1.2)
        leg = self.legenda("Como integrar e decimar comutam, os blocos iguais podem ser agrupados", leg)
        self.play(FadeIn(hog, shift=UP * 0.15), run_time=1.2)
        self.play(FadeIn(ch_i), FadeIn(r_i), FadeIn(ch_c), FadeIn(r_c))
        leg = self.legenda("É o mesmo filtro, redesenhado: M integradores, o decimador, M combs", leg)
        self.wait(2.0)
        self.play(FadeOut(VGroup(um, moldura, r_um, casc, r_casc, nota_n, hog, ch_i, r_i, ch_c, r_c)),
                  run_time=0.8)

        # --- B: o que M faz com a janela -------------------------------------
        self.trocar_titulo(titulo, "13 · O que M faz com a janela")
        self.parametros(4, 1, "1, 2, 3")
        h1 = np.array([1, 1, 1, 1])
        janelas = [h1, np.convolve(h1, h1), np.convolve(np.convolve(h1, h1), h1)]
        nomes = ["retangular", "triangular", "um sino"]
        grupos, rotulos, pesos = VGroup(), VGroup(), VGroup()
        for k, h in enumerate(janelas):
            cx = -4.45 + 4.45 * k
            a = Axes(x_range=[-0.5, 10.5, 2], y_range=[0, 0.3, 0.1], x_length=3.7, y_length=1.7,
                     axis_config=EIXO_CFG).move_to(P(cx, 0.85))
            g = VGroup(a, *[haste(a, n, v / h.sum(), COR_JANELA, 0.055, 3) for n, v in enumerate(h)])
            grupos.add(g)
            rotulos.add(VGroup(tex(rf"M = {k + 1}", COR_JANELA, 30),
                               txt(nomes[k], 19)).arrange(DOWN, buff=0.12).move_to(P(cx, 2.3)))
            pesos.add(VGroup(txt(" ".join(str(v) for v in h), 20, WHITE),
                             txt(f"{len(h)} amostras", 17, GREY_B)
                             ).arrange(DOWN, buff=0.12).move_to(P(cx, -0.5)))

        conta = tex(r"h_M = h_1 * h_1 * \cdots * h_1 \quad (M \text{ vezes})", WHITE, 30).move_to(P(0, -1.55))
        porque = txt("fazer a média das médias: as amostras do meio entram em várias janelas\n"
                     "e passam a pesar mais que as das pontas", 21, GREY_B, line_spacing=0.85
                     ).move_to(P(0, -2.45))

        leg = self.legenda("Para ver o que M faz com o sinal, olhe a janela que o filtro aplica", leg)
        self.play(FadeIn(grupos[0]), FadeIn(rotulos[0]), FadeIn(pesos[0]), run_time=1.2)
        leg = self.legenda("Com um estágio a janela é plana: as 4 amostras pesam igual", leg, COR_JANELA)
        self.wait(1.4)
        leg = self.legenda("O segundo estágio filtra a saída do primeiro — e a janela deixa de ser plana", leg)
        self.play(FadeIn(grupos[1]), FadeIn(rotulos[1]), FadeIn(pesos[1]), run_time=1.2)
        self.play(Write(conta), run_time=1.2)
        self.wait(1.2)
        self.play(FadeIn(grupos[2]), FadeIn(rotulos[2]), FadeIn(pesos[2]), run_time=1.2)
        leg = self.legenda("Com três, já é quase um sino: transição suave em vez de corte seco", leg, COR_JANELA)
        self.play(FadeIn(porque, shift=UP * 0.15))
        self.wait(1.8)
        leg = self.legenda("E a janela fica mais longa: M·(R·D−1)+1 amostras, logo mais atraso", leg)
        self.wait(1.8)
        self.play(FadeOut(VGroup(grupos, rotulos, pesos, conta, porque)), run_time=0.8)

        cores = [COR_COMB, COR_JANELA, COR_LENTO, COR_DEC]

        # --- C: o gráfico da cena 8, agora com M = 4 --------------------------
        self.trocar_titulo(titulo, "13 · O mesmo gráfico com M = 4")
        self.parametros(4, 1, "1, 2, 4")
        ax = Axes(x_range=[0, 0.5, 0.125], y_range=[0, 1.15, 0.25], x_length=6.1, y_length=3.0,
                  axis_config=EIXO_CFG).move_to(P(-3.35, 0.55))
        marcas = marcar_x(ax, [0, 0.125, 0.25, 0.375, 0.5], ["0", "f_s/8", "f_s/4", "3f_s/8", "f_s/2"], 14)
        r_ax = rotulo_eixo(ax, txt("a janela continua R·D = 4 nos três; ganho normalizado para 1 em DC", 16))

        def lin(f, m):
            return (ganho(f, D) / D) ** m

        F_LOB = 0.3660                                  # pico do lóbulo lateral de D = 4
        ms = (1, 2, 4)
        curvas = [ax.plot(lambda f, m=m: lin(f, m), x_range=[0.0006, 0.5, 0.0006],
                          color=[COR_COMB, COR_JANELA, COR_DEC][k], stroke_width=4)
                  for k, m in enumerate(ms)]
        pontos = [Dot(ax.c2p(F_LOB, lin(F_LOB, m)), radius=0.07,
                      color=[COR_COMB, COR_JANELA, COR_DEC][k]) for k, m in enumerate(ms)]
        vert = DashedLine(ax.c2p(F_LOB, 0), ax.c2p(F_LOB, lin(F_LOB, 1) + 0.12), color=GREY_B,
                          stroke_width=1.5, dash_length=0.07)
        zeros = VGroup(Dot(ax.c2p(0.25, 0), radius=0.075, color=COR_RUIDO),
                       Dot(ax.c2p(0.5, 0), radius=0.075, color=COR_RUIDO))
        r_zeros = txt("os zeros não se movem:\nquem os posiciona é D", 15, COR_RUIDO, line_spacing=0.75
                      ).move_to(ax.c2p(0.30, 0.62))

        def num(v, casas):
            return f"{v:.{casas}f}".replace(".", ",")

        def dbn(v):
            return f"{20 * np.log10(v):.0f}".replace("-", "−")

        col_x = [3.95, 5.15, 6.35]
        lin_y = [2.0, 1.25, 0.6, -0.05, -0.7]
        cores_m = [COR_COMB, COR_JANELA, COR_DEC]
        cabs = VGroup(*[tex(rf"M = {m}", cores_m[k], 30).move_to(P(col_x[k], lin_y[0]))
                        for k, m in enumerate(ms)])
        linhas = [
            ("pico do lóbulo lateral", [num(lin(F_LOB, m), 4 if m > 2 else 3) for m in ms], COR_RUIDO),
            ("o mesmo em dB", [dbn(lin(F_LOB, m)) for m in ms], COR_RUIDO),
            ("ganho em f_s/16", [num(lin(0.0625, m), 2) for m in ms], COR_LENTO),
            ("ordem dos zeros", [str(m) for m in ms], WHITE),
        ]
        rot_linhas, colunas = VGroup(), [VGroup(), VGroup(), VGroup()]
        for c, (rot, vals, cor) in enumerate(linhas, start=1):
            rot_linhas.add(txt(rot, 17, GREY_B).move_to(P(3.3, lin_y[c]), aligned_edge=RIGHT))
            for k, v in enumerate(vals):
                colunas[k].add(txt(v, 18, cor).move_to(P(col_x[k], lin_y[c])))

        elevar = tex(r"|H(f)|^M", WHITE, 32).move_to(P(4.9, -1.6))
        r_elevar = txt("os estágios são iguais, então\nas respostas se multiplicam", 17, GREY_B,
                       line_spacing=0.8).move_to(P(4.9, -2.4))

        leg = self.legenda("É o mesmo gráfico de |H(f)| de antes, normalizado para valer 1 em DC", leg)
        self.play(Create(ax), FadeIn(marcas), FadeIn(r_ax))
        self.play(Create(curvas[0]), FadeIn(cabs[0]), run_time=1.3)
        self.play(FadeIn(vert), FadeIn(pontos[0]), FadeIn(colunas[0]), FadeIn(rot_linhas), run_time=0.9)
        leg = self.legenda("Com M = 1: zeros em f_s/4 e f_s/2, e o lóbulo lateral valendo 0,27", leg, COR_COMB)
        self.wait(1.8)
        leg = self.legenda("Com M estágios iguais em cascata, a curva inteira é elevada a M", leg)
        self.play(Write(elevar), FadeIn(r_elevar), run_time=1.2)
        self.wait(1.4)

        for k in (1, 2):
            leg = self.legenda(f"M = {ms[k]}: a curva toda abaixa, porque 0,27 elevado a {ms[k]} é bem menor",
                               leg, cores_m[k])
            self.play(Create(curvas[k]), run_time=1.2)
            self.play(FadeIn(pontos[k]), FadeIn(cabs[k]), FadeIn(colunas[k]), run_time=0.7)
            self.wait(1.3)

        leg = self.legenda("Os zeros ficam onde estavam: quem os posiciona é D, não M", leg, COR_RUIDO)
        self.play(FadeIn(zeros), FadeIn(r_zeros), run_time=0.9)
        self.wait(1.6)
        leg = self.legenda("O que muda neles é a ordem: a curva passa a encostar no eixo e ficar rente a ele",
                           leg, COR_RUIDO)
        self.wait(1.8)
        leg = self.legenda("E o lóbulo lateral, que era 0,27, praticamente desaparece: 0,0055 com M = 4",
                           leg, COR_DEC)
        self.wait(1.8)
        leg = self.legenda("O preço está na banda útil: em f_s/16 o ganho cai de 0,91 para 0,67", leg, COR_LENTO)
        self.wait(1.8)
        leg = self.legenda("Na escala linear o lóbulo de M = 4 já não se vê — então vamos para dB", leg)
        self.wait(1.6)
        self.play(FadeOut(VGroup(ax, marcas, r_ax, *curvas, *pontos, vert, zeros, r_zeros,
                                 cabs, rot_linhas, *colunas, elevar, r_elevar)), run_time=0.8)

        # --- D: o mesmo em dB, de M = 1 a 4 -----------------------------------
        self.trocar_titulo(titulo, "13 · Em dB: o lóbulo cai 11 dB por estágio")
        self.parametros(4, 1, "1 a 4")
        ax = Axes(x_range=[0, 0.5, 0.125], y_range=[-80, 5, 20], x_length=6.5, y_length=3.0,
                  axis_config=EIXO_CFG).move_to(P(-3.25, 0.15))
        marcas = marcar_x(ax, [0, 0.125, 0.25, 0.375, 0.5], ["0", "f_s/8", "f_s/4", "3f_s/8", "f_s/2"], 14)
        marcas_y = VGroup(*[txt(t, 14, COR_EIXO).next_to(ax.c2p(0, v), LEFT, buff=0.12)
                            for v, t in [(0, "0 dB"), (-20, "−20"), (-40, "−40"), (-60, "−60"), (-80, "−80")]])
        r_ax = rotulo_eixo(ax, txt("em decibéis: a mesma curva, com os lóbulos visíveis", 16))
        curvas = [ax.plot(lambda f, k=k: ganho_db(f, D, k + 1), x_range=[0.0008, 0.5, 0.0012],
                          color=cores[k], stroke_width=3.5) for k in range(4)]

        lin_y = [1.45, 0.72, -0.01, -0.74, -1.47]
        tab = VGroup()
        for c, (rot, vals) in enumerate([("", ["M = 1", "M = 2", "M = 3", "M = 4"]),
                                         ("lóbulo lateral", ["−11", "−23", "−34", "−45"]),
                                         ("droop em f_s/8", ["−3,7", "−7,4", "−11,1", "−14,8"]),
                                         ("atraso (amostras)", ["1,5", "3,0", "4,5", "6,0"]),
                                         ("bits a mais", ["+2", "+4", "+6", "+8"])]):
            if rot:
                tab.add(txt(rot, 16, GREY_B).move_to(P(2.45, lin_y[c]), aligned_edge=RIGHT))
            for k, v in enumerate(vals):
                tab.add(txt(v, 17, cores[k] if c == 0 else WHITE).move_to(P(3.3 + 0.95 * k, lin_y[c])))
        unidade = txt("lóbulo e droop em dB", 15, GREY_B).move_to(P(4.1, -2.1))

        leg = self.legenda("A mesma multiplicação, vista em dB, vira uma soma: M vezes a curva de um estágio",
                           leg)
        self.play(Create(ax), FadeIn(marcas), FadeIn(marcas_y), FadeIn(r_ax))
        self.play(FadeIn(VGroup(*tab[:4])))
        for k in range(4):
            self.play(Create(curvas[k]), run_time=1.1)
            self.play(FadeIn(VGroup(*[m for m in tab[4:] if abs(m.get_center()[0] - (3.3 + 0.95 * k)) < 0.4])),
                      run_time=0.5)
            self.wait(0.9)
        self.play(FadeIn(VGroup(*[m for m in tab[4:] if m.get_center()[0] < 2.6])), FadeIn(unidade))
        leg = self.legenda("Para baixo é ótimo: o lóbulo cai ~11 dB por estágio", leg, COR_LENTO)
        self.wait(1.6)
        leg = self.legenda("Mas a banda útil afunda junto: o droop também multiplica", leg, COR_RUIDO)
        self.wait(1.8)
        leg = self.legenda("E cada estágio cobra atraso e registrador mais largo: log₂(R·D) bits a mais", leg)
        self.wait(1.8)
        self.play(FadeOut(VGroup(ax, marcas, marcas_y, r_ax, *curvas, tab, unidade)), run_time=0.8)

        # --- E: o mesmo sinal com M = 1, 2, 3 e 4 -----------------------------
        self.trocar_titulo(titulo, "13 · O mesmo sinal com 1, 2, 3 e 4 estágios")
        rng = np.random.default_rng(11)
        nmax = 160
        n = np.arange(nmax)
        x = np.sin(TAU * n / 40) + 0.5 * rng.standard_normal(nmax)

        def cascata(dados, k, d=D):
            y = np.asarray(dados, dtype=float)
            for _ in range(k):
                y = media_movel(y, d) / d
            return y

        # desvio do ruído na saída, exato: a entrada tem sigma 0,5 e um filtro de
        # janela w multiplica o desvio de um ruído branco por sqrt(soma de w ao quadrado)
        h1, hm, sigmas = np.ones(D), np.ones(D), []
        for _ in range(4):
            w = hm / hm.sum()
            sigmas.append(0.5 * float(np.sqrt((w ** 2).sum())))
            hm = np.convolve(hm, h1)

        ys = [2.5, 1.4, 0.3, -0.8, -1.9]

        def linha(yc, dados, cor, largura=2):
            a = eixos_tempo(P(-1.9, yc), 8.2, 0.85, [0, nmax, 40], [-2.3, 2.3, 2])
            c = VMobject().set_points_as_corners([a.c2p(k, v) for k, v in zip(n, dados)])
            return VGroup(a, c.set_stroke(cor, largura))

        grupos = [linha(ys[0], x, COR_X)]
        rotulos = [txt("entrada\nruidosa", 16, COR_X, line_spacing=0.75
                       ).move_to(P(2.9, ys[0]), aligned_edge=LEFT)]
        for k in range(4):
            grupos.append(linha(ys[k + 1], cascata(x, k + 1), cores[k]))
            rotulos.append(txt(f"M = {k + 1}\nσ do ruído = {sigmas[k]:.2f}".replace(".", ","),
                               16, cores[k], line_spacing=0.75).move_to(P(2.9, ys[k + 1]), aligned_edge=LEFT))

        leg = self.legenda("A mesma entrada passando por 1, 2, 3 e 4 estágios, com a janela R·D = 4", leg)
        self.play(Create(grupos[0][0]), FadeIn(rotulos[0]))
        self.play(Create(grupos[0][1]), run_time=1.4)
        for k, texto in enumerate([
                "M = 1: o ruído já cai pela metade",
                "M = 2: mais liso — mas repare que a onda começou a atrasar",
                "M = 3: o ganho em suavidade é bem menor que do primeiro para o segundo",
                "M = 4: quase idêntico ao M = 3, e já com 6 amostras de atraso"]):
            leg = self.legenda(texto, leg, cores[k])
            self.play(FadeIn(grupos[k + 1], shift=UP * 0.1), FadeIn(rotulos[k + 1]), run_time=1.2)
            self.wait(1.5)

        fecho = txt("de 1 para 4 estágios o ruído cai só de 0,25 para 0,18 — o ganho de verdade\n"
                    "está no que o lóbulo rejeita, e isso só aparece na hora de decimar",
                    21, COR_LENTO, line_spacing=0.85).move_to(P(0, -3.0))
        leg = self.legenda("Então por que usar mais estágios, se o sinal mal fica mais liso?", leg)
        self.wait(1.4)
        self.play(FadeIn(fecho, shift=UP * 0.15))
        self.wait(2.6)
        self.limpar()

    # ================================================================== RESUMO
    def cena_resumo(self):
        self.titulo_cena("Resumo")
        self.parametros()
        # cor só nos nomes dos blocos, no mesmo código de cores usado nas cenas
        itens = VGroup(*[Text(t, font_size=21, color=WHITE, t2c=c) for t, c in [
            ("• Três parâmetros: R (decimação), D (atraso do comb) e M (estágios) — a janela é R·D", {}),
            ("• No diagrama: Σ soma, z⁻¹ guarda uma amostra, o nó copia o valor", {}),
            ("• Integrador: tem realimentação, soma tudo — I[n] = I[n−1] + x[n]", {"Integrador": COR_INT}),
            ("• Comb: só para frente, y[n] = I[n] − I[n−D]; z⁻ᴰ são D registradores em fila",
             {"Comb": COR_COMB}),
            ("• Juntos: a soma de uma janela de R·D amostras — uma média móvel sem multiplicador",
             {"janela de R·D amostras": COR_JANELA}),
            ("• |H(f)| = |sin(πR·Df/f_s) / sin(πf/f_s)|: ganho R·D em DC, zeros em múltiplos de f_s/(R·D)", {}),
            ("• Janela maior: mais suave e mais lenta, com droop na banda útil (gráfico mais estreito)", {}),
            ("• Os zeros caem onde o espectro dobra ao decimar por R: anti-aliasing sob medida", {}),
            ("• Decimador entre integrador e comb: o comb roda a f_s/R com z⁻¹, ou seja D = 1",
             {"Decimador": COR_DEC}),
            ("• M estágios: a janela vira um sino; −11 dB de lóbulo por estágio, e droop igual", {}),
        ]]).arrange(DOWN, aligned_edge=LEFT, buff=0.28).move_to(P(0, -0.25))
        self.play(LaggedStart(*[FadeIn(t, shift=RIGHT * 0.2) for t in itens], lag_ratio=0.3), run_time=4.5)
        self.wait(4)
        self.limpar()
