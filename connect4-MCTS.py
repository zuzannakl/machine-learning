import sys
import math
import random
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QMessageBox, QStackedWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

liczba_rzedow = 6
liczba_kolumn = 7
gracz = 'X'
ai = 'O'
puste_pole = '.'
ai_kolor = "#ea2f1a"

def czy_wygrana(plansza, zeton):
    # poziomo
    for r in range(liczba_rzedow):
        for k in range(liczba_kolumn - 3):
            if all(plansza[r][k+i] == zeton for i in range(4)): return True
    # pionowo
    for k in range(liczba_kolumn):
        for r in range(liczba_rzedow - 3):
            if all(plansza[r+i][k] == zeton for i in range(4)): return True
    # na skos w dół
    for r in range(liczba_rzedow - 3):
        for k in range(liczba_kolumn - 3):
            if all(plansza[r+i][k+i] == zeton for i in range(4)): return True
    # na skos w górę
    for r in range(3, liczba_rzedow):
        for k in range(liczba_kolumn - 3):
            if all(plansza[r-i][k+i] == zeton for i in range(4)): return True
    return False

def mozliwe_ruchy(plansza):
    ruchy = []
    for k in range(liczba_kolumn):
        if plansza[0][k] == puste_pole:
            ruchy.append(k)
    return ruchy

def ktory_wiersz(plansza, k):
    for r in reversed(range(liczba_rzedow)):
        if plansza[r][k] == puste_pole:
            return r
    return None

def najlepszy_ruch(plansza):
    ruchy = mozliwe_ruchy(plansza)
    for k in ruchy:
        r = ktory_wiersz(plansza, k)
        plansza[r][k] = ai
        if czy_wygrana(plansza, ai):
            plansza[r][k] = puste_pole
            return k
        plansza[r][k] = puste_pole
    for k in ruchy:
        r = ktory_wiersz(plansza, k)
        plansza[r][k] = gracz
        if czy_wygrana(plansza, gracz):
            plansza[r][k] = puste_pole
            return k
        plansza[r][k] = puste_pole
    return None

class MCTSNode:
    def __init__(self, plansza, parent = None, ruch = None, tura = ai):
        self.plansza = plansza
        self.parent = parent
        self.ruch = ruch
        self.tura = tura
        self.dzieci = []
        self.wizyty = 0
        self.wygrane = 0
        self.nieodkryte_ruchy = mozliwe_ruchy(plansza)

    def uct(self, eksploracja = 1.41):
        if self.wizyty == 0:
            return float('inf')
        return (self.wygrane / self.wizyty) + eksploracja * math.sqrt(math.log(self.parent.wizyty) / self.wizyty)
    def wybierz_najlepsze_dziecko(self):
        return max(self.dzieci, key = lambda n: n.uct())

def mcts(plansza_startowa, iteracje = 8000):
    korzen = MCTSNode([row[:] for row in plansza_startowa], tura = ai)

    for i in range(iteracje):
        node = korzen
        plansza_ak = [row[:] for row in korzen.plansza]

        while not node.nieodkryte_ruchy and node.dzieci:
            node = node.wybierz_najlepsze_dziecko()
            r = ktory_wiersz(plansza_ak, node.ruch)
            plansza_ak[r][node.ruch] = node.parent.tura

        if node.nieodkryte_ruchy:
            k = random.choice(node.nieodkryte_ruchy)
            node.nieodkryte_ruchy.remove(k)
            r = ktory_wiersz(plansza_ak, k)
            plansza_ak[r][k] = node.tura
            nowa_tura = gracz if node.tura == ai else ai
            nowy_node = MCTSNode([row[:] for row in plansza_ak], parent = node, ruch = k, tura = nowa_tura)
            node.dzieci.append(nowy_node)
            node = nowy_node

        sim_plansza = [row[:] for row in plansza_ak]
        obecna_tura = node.tura
        wynik = 0

        while True:
            if czy_wygrana(sim_plansza, gracz):
                wynik = -1; break
            if czy_wygrana(sim_plansza, ai):
                wynik = 1; break
            ruchy = mozliwe_ruchy(sim_plansza)
            if not ruchy: break
            k = random.choice(ruchy)
            r = ktory_wiersz(sim_plansza, k)
            sim_plansza[r][k] = obecna_tura
            obecna_tura = gracz if obecna_tura == ai else ai

        while node is not None:
            node.wizyty += 1
            if wynik == 1:
                node.wygrane += 1
            elif wynik == -1:
                node.wygrane -= 1
            node = node.parent

    najlepsze_opcje = sorted(korzen.dzieci, key = lambda n: n.wizyty, reverse = True)

    for opcja in najlepsze_opcje:
        test_k = opcja.ruch
        test_r = ktory_wiersz(plansza_startowa, test_k)
        
        kopia_p = [row[:] for row in plansza_startowa]
        kopia_p[test_r][test_k] = ai
        
        bezpieczny = True
        ruchy_gracza = mozliwe_ruchy(kopia_p)
        for kg in ruchy_gracza:
            rg = ktory_wiersz(kopia_p, kg)
            kopia_p[rg][kg] = gracz
            if czy_wygrana(kopia_p, gracz):
                bezpieczny = False
                break
            kopia_p[rg][kg] = puste_pole
        
        if bezpieczny:
            return test_k

    return najlepsze_opcje[0].ruch if najlepsze_opcje else random.choice(mozliwe_ruchy(plansza_startowa))

class gra(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Czwórki - Monte Carlo Tree Search")
        self.setFixedSize(600, 750)
        self.setStyleSheet("background-color: #293138;")
        self.plansza = [[puste_pole for i in range(liczba_kolumn)] for j in range(liczba_rzedow)]
        self.game_over = False
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        self.init_ekran_startowy()
        self.init_wybor_koloru()
        self.init_wybor_zaczynajacego()
        self.init_ekran_gry()
        self.stacked_widget.setCurrentIndex(0)

    def init_ekran_startowy(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tytul = QLabel("Witaj w grze w Czwórki! - MCTS")
        tytul.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        tytul.setStyleSheet("color: white; margin-bottom: 25px;")
        zasady = QLabel(
            "ZASADY:\n\n"
            "1. Pierwszy gracz wrzuca swój żeton do wybranej przez niego kolumny.\n\n"
            "2. Gracze wrzucają swoje żetony na przemian, aż jeden z nich ułoży cztery żetony "
            "w poziomie, pionie lub ukosie.\n\n"
            "3. Wygrywa ten gracz, który zrobi to jako pierwszy.\n\n"
            "4. Jeżeli natomiast plansza się zapełni, a nie utworzy się żadna czwórka, jest remis.\n\n"
            "5. Komputer gra kolorem czerwonym."
        )
        zasady.setFont(QFont("Arial", 15))
        zasady.setStyleSheet("color: #bdc3c7;")
        zasady.setAlignment(Qt.AlignmentFlag.AlignCenter)
        zasady.setWordWrap(True)
        zasady.setFixedWidth(500)
        przycisk = QPushButton("Dalej")
        przycisk.setFixedSize(200, 60)
        przycisk.setStyleSheet("background-color: #e693c0; color: white; border-radius: 10px; font-weight: bold;")
        przycisk.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        layout.addWidget(tytul, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(zasady, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(40)
        layout.addWidget(przycisk, alignment=Qt.AlignmentFlag.AlignCenter)
        self.stacked_widget.addWidget(page)

    def init_wybor_koloru(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label = QLabel("Wybierz swój kolor:")
        label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        label.setStyleSheet("color: white; margin-bottom: 30px;")
        layout.addWidget(label, alignment = Qt.AlignmentFlag.AlignCenter)
        przycisk_box = QHBoxLayout()

        for n, c in [("Zielony", "#1bc361"), ("Niebieski", "#2b94da"), ("Żółty", "#ecc115")]:
            b = QPushButton(n)
            b.setFixedSize(120, 120)
            b.setStyleSheet(f"background-color: {c}; border-radius: 60px; color: white; font-weight: bold;")
            b.clicked.connect(lambda ch, col = c: self.ustawienie_koloru(col))
            przycisk_box.addWidget(b)
        layout.addLayout(przycisk_box)
        self.stacked_widget.addWidget(page)

    def ustawienie_koloru(self, color):
        self.gracz_color = color
        self.stacked_widget.setCurrentIndex(2)

    def init_wybor_zaczynajacego(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label = QLabel("Wybierz kto ma zacząć grę:")
        label.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        label.setStyleSheet("color: white; margin-bottom: 40px;")
        layout.addWidget(label, alignment = Qt.AlignmentFlag.AlignCenter)
        przycisk_box = QHBoxLayout()
        gracz_p = QPushButton("Gracz")
        gracz_p.setFixedSize(180, 80)
        gracz_p.setStyleSheet("background-color: #34495e; color: white; border-radius: 10px; font-weight: bold;")
        gracz_p.clicked.connect(lambda: self.start_game("PLAYER"))
        ai_p = QPushButton("Komputer")
        ai_p.setFixedSize(180, 80)
        ai_p.setStyleSheet("background-color: #f54550; color: white; border-radius: 10px; font-weight: bold;")
        ai_p.clicked.connect(lambda: self.start_game("AI"))
        przycisk_box.addWidget(gracz_p)
        przycisk_box.addWidget(ai_p)
        layout.addLayout(przycisk_box)
        self.stacked_widget.addWidget(page)

    def init_ekran_gry(self):
        self.game_page = QWidget()
        layout = QVBoxLayout(self.game_page)
        self.status_label = QLabel("Start gry")
        self.status_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.status_label.setStyleSheet("color: white;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        self.grid = QGridLayout()
        self.grid.setSpacing(10)
        self.przyciski = []
        for r in range(liczba_rzedow):
            row_przyciski = []
            for c in range(liczba_kolumn):
                b = QPushButton()
                b.setFixedSize(70, 70)
                b.setStyleSheet(self.get_style(puste_pole))
                b.clicked.connect(lambda ch, col=c: self.ruch_gracza(col))
                self.grid.addWidget(b, r, c)
                row_przyciski.append(b)
            self.przyciski.append(row_przyciski)
        layout.addLayout(self.grid)
        exit_przycisk = QPushButton("Wyjdź do menu")
        exit_przycisk.clicked.connect(self.reset_menu)
        exit_przycisk.setStyleSheet("color: #7f8c8d; background: transparent;")
        layout.addWidget(exit_przycisk, alignment = Qt.AlignmentFlag.AlignCenter)
        self.stacked_widget.addWidget(self.game_page)

    def start_game(self, starter):
        self.reset_game_plansza()
        self.stacked_widget.setCurrentIndex(3)
        if starter == "AI":
            self.status_label.setText("Komputer zaczyna")
            QApplication.processEvents()
            self.ruch_komputera()
        else:
            self.status_label.setText("Twoja tura")

    def get_style(self, zeton):
        c = self.gracz_color if zeton == gracz else (ai_kolor if zeton == ai else "#2c3e50")
        return f"background-color: {c}; border: 4px solid #1a252f; border-radius: 35px;"
    
    def ruch_gracza(self, col):
        if self.game_over: return
        row = ktory_wiersz(self.plansza, col)
        if row is not None:
            self.ruch(row, col, gracz)
            if czy_wygrana(self.plansza, gracz):
                self.koniec_gry("Wygrałeś!")
                return
            if not mozliwe_ruchy(self.plansza):
                self.koniec_gry("Remis!"); return
            QApplication.processEvents()
            self.ruch_komputera()

    def ruch_komputera(self):
        self.status_label.setText("Tura komputera")
        QApplication.processEvents()
        col = najlepszy_ruch(self.plansza)
        if col is None:
            col = mcts(self.plansza, iteracje=8000)
        if col is not None:
            row = ktory_wiersz(self.plansza, col)
            self.ruch(row, col, ai)
            if czy_wygrana(self.plansza, ai):
                self.koniec_gry("Komputer wygrał")
            elif not mozliwe_ruchy(self.plansza):
                self.koniec_gry("Remis!")
            else:
                self.status_label.setText("Twoja tura")

    def ruch(self, r, c, z):
        self.plansza[r][c] = z
        self.przyciski[r][c].setStyleSheet(self.get_style(z))

    def koniec_gry(self, msg):
        self.game_over = True
        self.status_label.setText(msg)
        QMessageBox.information(self, "Koniec", msg)

    def reset_game_plansza(self):
        self.plansza = [[puste_pole for i in range(liczba_kolumn)] for j in range(liczba_rzedow)]
        self.game_over = False
        for r in range(liczba_rzedow):
            for c in range(liczba_kolumn):
                self.przyciski[r][c].setStyleSheet(self.get_style(puste_pole))

    def reset_menu(self):
        self.stacked_widget.setCurrentIndex(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = gra()
    win.show()
    sys.exit(app.exec())