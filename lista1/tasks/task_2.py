import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.tabu_search import TabuSearch

def start():
    """
    uv run tasks/task_2.py
    """
    A= "Szklarska Poręba Dolna"
    L= "Mirków;Wrocław Główny;Wałbrzych Główny;Zgorzelec"
    # L= "Sobótka;Zgorzelec;Wrocław Główny;Świdnica Miasto"
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