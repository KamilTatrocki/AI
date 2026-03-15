"""
Wykorzystuj  ̨ac dostarczony zbiór danych GTFS, zaimplementuj wyszukiwanie najkrótszej  ́scie ̇zki z po-
danego przystanku A, odwiedzaj  ̨acej wszystkie przystanki z listy L= A2, . . . , An, i wracaj  ̨acej do A.
Jako funkcj  ̨e kosztu zastosuj (w zale ̇zno ́sci od decyzji u ̇zytkownika) czas przejazdu z A do B lub liczb  ̨e
przesiadek.
Aplikacja powinna przyjmowa ́c dane wej ́sciowe składaj  ̨ace si  ̨e z 4 zmiennych:
(a) przystanek pocz  ̨atkowy A
(b) lista przystanków do odwiedzenia oddzielona  ́srednikiem L
(c) kryterium optymalizacji: warto ́s ́c t oznacza minimalizacj  ̨e czasu przejazdu, warto ́s ́c p oznacza
minimalizacj  ̨e liczby przesiadek
(d) czas rozpocz ̨ecia podró ̇zy
Rozwi  ̨azanie powinno wypisywa ́c na standardowe wyj ́scie, w kolejnych wierszach, szczegółowe infor-
macje o  ́scie ̇zce, w tym przystanek pocz  ̨atkowy, przystanek ko  ́ncowy, nazw  ̨e wykorzystanej linii, czas
rozpocz ̨ecia, czas zako  ́nczenia, a na standardowe wyj ́scie bł  ̨edów warto ́s ́c minimalizowanego kryte-
rium oraz czas potrzebny do obliczenia najkrótszej  ́scie ̇zki.
Punktacja:
(a) algorytm wyszukiwania najkrótszej  ́scie ̇zki mi  ̨edzy wierzchołkami oparty na Tabu Search bez ogra-
niczania rozmiaru T (10 punktów)
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.tabu_search import TabuSearch

def start():
    A= "Szklarska Poręba Dolna"
    # L= "Mirków;Wrocław Główny;Wałbrzych Główny;Zgorzelec"
    L= "Zgorzelec;Wrocław Główny;Mirków;Wałbrzych Główny"
    # L="Wrocław Główny;Zgorzelec;Mirków;Wałbrzych Główny"
    criteria= "p"
    start_time_str= "2026-03-08 8:00"


    #ANOTHER SETTINGS
    #modyfikacja algorytmu (a) ze zmiennym rozmiarem T, zale˙znym od długo´sci L, w celu minimalizacji funkcji kosztu (5 punktów)
    is_dynamic_tabu_size_B = True

    # modyfikacja algorytmu (a) z dodaniem kryterium aspiracji, w celu minimalizacji funkcji kosztu (5punktów)
    is_aspiration_criterion_C = True

    # modyfikacja algorytmu (a) z dodaniem strategii próbkowania s ˛asiedztwa, w celu minimalizacji funkcji kosztu i skrócenia czasu oblicze´n (10 punktów)
    is_neighborhood_sampling_D = True

    tabu_search = TabuSearch(A, L, criteria, start_time_str, is_dynamic_tabu_size_B, is_aspiration_criterion_C, is_neighborhood_sampling_D)
    tabu_search.search()

if __name__ == "__main__":
    start()