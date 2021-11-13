"""Moduł służy do przechowywania danych, wyników graczy i drużyn"""

import copy
from typing import Union
import numpy as np

from search_players_rows import _CellInRow


class StorageOfAllPlayersScore:
    """
    Klasa przechowuje wyniki wszystkich graczy oraz drużyn.

    on_data_initialization(int, int) -> None - tworzy nową strukturę obiektu, jest wywoływana przy tworzeniu obiektu

    """
    def __init__(self, *, number_of_team: int = 1, number_of_player_in_team: int = 1) -> None:
        """
        :param number_of_team - ilość drużyn
        :param number_of_player_in_team - ilość graczy w drużynie

        teams - lista przechowująca wyniki graczy i drużyn
        number_of_teams - ilość drużyn
        number_of_players_in_team - ilość graczy w drużynie
        """
        self.teams: list[_StorageOfAllTeamResults] = []
        self.number_of_teams: int = 0
        self.number_of_players_in_team: int = 0
        self.on_data_initialization(number_of_team, number_of_player_in_team)

    def on_data_initialization(self, number_of_team: int, number_of_player_in_team: int) -> None:
        """
        Funkcja tworzy puste kontenery na dane.

        Funkcja w self.teams dodaje tyle elementów ile jest drużyn, i w każdym tworzy tyle elementów do przechowywania
        danych graczy ile jest graczy w drużynie. Dodatkowo ustawaia zmienne obeiktu do przechowywania ile jest drużyn
        i graczy w drużynie.
        """
        self.number_of_teams = number_of_team
        self.number_of_players_in_team = number_of_player_in_team
        self.teams = [_StorageOfAllTeamResults for _ in range(numer_of_team)]

    def update_coord_cell(self, all_coord_cell: list[list[_CellInRow]]) -> bool:
        """
        Aktualizuje współrzędne graczy.

        Funkcja aktualizuje listę zawierającą współrzędne komórek z danymi graczy na obrazie tabeli.
        :param all_coord_cell - zawiera obiekty ze współrzędnymi podzielone odpowiednio na drużyny
        :return - czy udało się zaaktualizować
        """
        if len(all_coord_cell) != self.number_of_teams or len(all_coord_cell[0]) != self.number_of_players_in_team:
            return False
        for i, team in enumerate(self.teams):
            for j, player in enumerate(team.players_results):
                player.cell_in_row = all_coord_cell[i][j]
        return True

    def calculate_league_points(self) -> bool:
        """
        Funkcja wyzncza punkty ligowe poszczególnych graczy i drużyn.
        """
        if self.number_of_teams != 2:
            return False

        list_sum_pd, list_sum_ps = [0, 0], [0, 0]
        for i in range(self.number_of_players_in_team):
            league_results = [{"list_ps": [0, 0, 0, 0], "sum_ps": 0}, {"list_ps": [0, 0, 0, 0], "sum_ps": 0}]
            players = [self.teams[0].players_results[i], self.teams[1].players_results[i]]
            for nr_tor in range(4):
                results = [players[0].result_tory[nr_tor].suma, players[1].result_tory[nr_tor].suma]
                for j, k in ((0, 1), (1, 0)):
                    ps = 1 if results[j] > results[k] else 0.5 if (results[j] == results[k] and results[j] > 0) else 0
                    league_results[j]["list_ps"][nr_tor] = ps
                    league_results[j]["sum_ps"] += ps
                    list_sum_ps[j] += ps

            for j, k in ((0, 1), (1, 0)):
                sum_ps = league_results[j]["sum_ps"]
                difference_sum_ps = sum_ps - league_results[k]["sum_ps"]
                pd = 0
                if difference_sum_ps > 0:
                    pd = 1
                elif difference_sum_ps == 0 and sum_ps > 0:
                    difference_sum_player = players[j].result_main.suma - players[k].result_main.suma
                    pd = 1 if difference_sum_player > 0 else 0 if difference_sum_player < 0 else 0.5
                list_sum_pd[j] += pd
                players[j].update_league_points(pd, sum_ps, league_results[j]["list_ps"])

        list_sum_team = (self.teams[0].team_results.suma, self.teams[1].team_results.suma)
        point_for_suma = (0, 0)
        if list_sum_team[0] > list_sum_team[1]:
            point_for_suma = (2, 0)
        elif list_sum_team[0] == list_sum_team[1] and list_sum_team[0] > 0:
            point_for_suma = (1, 1)
        elif list_sum_team[0] < list_sum_team[1]:
            point_for_suma = (0, 2)
        sum_difference = [list_sum_team[0] - list_sum_team[1], list_sum_team[1] - list_sum_team[0]]
        for i in range(2):
            sum_pd = list_sum_pd[i]+point_for_suma[i]
            self.teams[i].team_results.update_league_points(sum_pd, list_sum_ps[i], sum_difference[i])
        return True


class _StorageOfAllTeamResults:
    """
    Przechowuje dane drużyny: dane poszczególnych graczy i całej drużyny.

    Funkcja jest pośrednikiem między 'StorageOfAllPlayersScore' który przechowuje dane wszystkich drużyn,
    a "_StorageOfTeamResults" i "_StorageOfPlayerResults" które przechowują dane albo tylko graczy albo drużyn.

    players_results: przechowuje dane graczt
    team_results: przechowuje dane drużyny
    """
    def __init__(self, number_of_players: int) -> None:
        self.players_results: list[_StorageOfPlayerResults] = []
        self.team_results: _StorageOfTeamResults = _StorageOfTeamResults()
        for i in range(number_of_players):
            self.players_results.append(_StorageOfPlayerResults())


class _StorageOfTeamResults:
    """
    Klasa do przechowywania zsumowanych wyników całej drużyny.

    update_league_points(int, int, int): None - aktualizuje PD, PS i różnicę między drużynami
    suma - zsumowany wynik
    pelne - zsumowane pelne
    zbierane - zsumowane zbierane
    dziur - zsumowana ilość rzutów wadliwych
    number_of_rzut - zsumowana ilość rzutów drużyny
    PD - zsumowana ilość punktów drużyny
    PS - zsumowana ilość punktów setowych
    sum_difference -różnica między tą drużyną a przeciwnikiem (this - opposit)
    """
    def __init__(self) -> None:
        self.suma: int = 0
        self.pelne: int = 0
        self.zbierane: int = 0
        self.dziur: int = 0
        self.number_of_rzut: int = 0
        self.PD: float = 0
        self.PS: float = 0
        self.sum_difference: int = 0

    def update_league_points(self, sum_pd: int, sum_ps: int, sum_difference: int) -> None:
        """
        Aktualizuje ligowe punkty drużyny.

        :param sum_pd - suma punktów drużynowych
        :param sum_ps - suma zdobytych punktów setowych w pojedynkach
        :param sum_difference - różnica sum drużyn
        """
        self.PD = sum_pd
        self.PS = sum_ps
        self.sum_difference = sum_difference


class _StorageOfPlayerResults:
    """
    Tworzy obiekt do przechowywania wyniku pojedyńczego gracza.

    Klasa tworzy obiekty służące do przechowywania:
        - wyników całego startu (ilość rzutów, pełnych, zbieranych, itp)
        - wyników na poszczególnych torach, w tablicy cztero elementowaj przechowuje oddzielnie info o każdym torze
        - wyniki z ligii
        - współrzędne komórek należącyhc do gracza

    tor_number - index toru, na ktrym gra zawodnik (w Gostyniu od 1 do 6)
    coord_in_row - obiekt z danymi gdzie na obrazie znajdują się komórki z danymi o graczach
    number_of_tor - numer touru podczas gry (od 0 do 4) - 4 oznacza koniec gry
    number_of_rzut_in_tor - numer rzutu na torze
    result_tory - przechowuje pod każdym indeksem informacje o jednym torze
    result_main - przechowuje podsumowanie o grze
    """
    def __init__(self) -> None:
        """
        __game_is_end: czy zawodnik zakończył już grę
        """
        self.__game_is_end: bool = False
        self.cell_in_row: Union[_CellInRow, None] = None
        self.tor_number: Union[int, None] = 0
        self.number_of_tor: int = 0
        self.number_of_rzut_in_tor: int = 0
        self.result_tory: list[_StorageDataTor] = [
            _StorageDataTor(),
            _StorageDataTor(),
            _StorageDataTor(),
            _StorageDataTor()
        ]
        self.result_main: _StorageDataBasic = _StorageDataBasic()

    def __repr__(self) -> str:
        return f"""
            Numer toru: {self.tor_number}, który tor: {self.number_of_tor},  \
            rzut na torze: {self.number_of_rzut_in_tor}
            Tory: {self.result_tory.__repr__()}
            Główne: {self.result_main.__repr__()}
                Pełne: {self.get_list_pelne()}
                Zbierane: {self.get_list_zbierane()}
                Suma: {self.get_list_suma()}
                {self.cell_in_row}
        """

    def get_list_pelne(self) -> list[int]:
        """Zwraca listę z wynikami osiągniętymi w pełnych."""
        list_pelne = []
        for tor in self.result_tory:
            list_pelne += tor.list_pelne
        return list_pelne

    def get_list_zbierane(self) -> list[int]:
        """Zwraca listę z wynikami osiągniętymi w zbieranych."""
        list_zbierane = []
        for tor in self.result_tory:
            list_zbierane += tor.list_zbierane
        return list_zbierane

    def get_list_suma(self) -> list[int]:
        """Zwraca listę z wynikami osiągniętymi w całej grze."""
        list_pelne = []
        for tor in self.result_tory:
            list_pelne += tor.get_list_suma()
        return list_pelne

    def update_data(self, tor_number: Union[int, None] = None,
                    number_of_rzut_in_tor: int = 0, result_in_last_rzut: int = 0) -> None:
        """
        Funkcja do aktualizacji danych.

        :param tor_number: numer toru na którym gra zawodnik (w dostyniu 1-6 lub None jeżeli aktualnie nie gra)
        :param number_of_rzut_in_tor: numer rzutu na torze
        :param result_in_last_rzut: wynik w ostatnim rzucie
        """
        if self.__game_is_end:
            return
        self.tor_number = tor_number
        if number_of_rzut_in_tor == 0 and self.number_of_rzut_in_tor != 0:
            self.number_of_tor += 1
        elif number_of_rzut_in_tor == self.number_of_rzut_in_tor and result_in_last_rzut == 0:
            return
        self.number_of_rzut_in_tor = number_of_rzut_in_tor
        if self.number_of_tor == 4:
            self.__game_is_end = True
            return
        if number_of_rzut_in_tor:
            self.result_tory[self.number_of_tor].update_data(number_of_rzut_in_tor, result_in_last_rzut)
            self.result_main.update_data(number_of_rzut_in_tor + self.number_of_tor*30, result_in_last_rzut)

    def get_cell(self, index_column: int, img: np.ndarray) -> np.ndarray:
        """
        Funkcja zwraca wyciętą komórkę z przekazanego obrazu.

        :param index_column: index komórki do zwrócenia, czyli numer kolumny
        :param img: obraz z którego zostanie wycięta komórka
        :return: (np.ndarray) wycięta komórka
                (bool) jeżeli nie m ustawionych współrzędnych
        :raise: podane zbyt duży numer kolumny
        :raise: jest za mały obraz
        """
        if self.cell_in_row is None:
            raise IndexError("Column no exist")
        y0, y1 = self.cell_in_row.get_coord_y()
        x0, x1 = self.cell_in_row.get_coord_x(index_column)
        if len(img) <= y1 or len(img[0]) <= x1:
            raise IndexError("Image is too small")
        else:
            return img[y0:y1, x0:x1]

    def update_league_points(self, pd: int, sum_ps: int, list_ps: list[int]) -> None:
        """
        Aktualizuje ligowe punkty gracza.

        :param pd - rezultat pojedynku
        :param sum_ps - suma zdobytych punktó setowych w pojedunku
        :param list_ps - rezultaty na poszczególnych torach
        """
        for nr_tor, tor in enumerate(self.result_tory):
            tor.PS = list_ps[nr_tor]
        self.result_main.PS = sum_ps
        self.result_main.PD = pd


class _StorageDataBasic:
    """
    Klasa do przechoywania głównych wyników gracza (sum pełnych, zbieranych, itp).

    update_data(int, int): None - służy do aktualizacji danych
    number_of_rzut - numer rzutu gracza
    pelne - ilość pełnych
    zbierane - ilość zbieranych
    dziur - ilość dziur
    suma - ilość zbitych kręgli w grze
    suma_of_eliminations_and_final - suma gracza razem wyniku z eliminacji i finału
    PS - ilość zdobytych punktów setowych
    PD - ilość zdobytych punktów drużynowych
    """
    def __init__(self) -> None:
        self.number_of_rzut: int = 0
        self.pelne: int = 0
        self.zbierane: int = 0
        self.dziur: int = 0
        self.suma: int = 0
        self.sum_of_eliminations_and_final: int = 0
        self.PS: float = 0
        self.PD: float = 0

    def __repr__(self) -> str:
        return f"""Rzut: {self.number_of_rzut}, Pełne: {self.pelne}, Zbierane: {self.zbierane}, Dziur: {self.dziur}"""

    def update_data(self, number_of_rzut: int, new_value: int) -> None:
        """
        Funkcja do aktualizowania danych.

        Jeżeli nowa wartość jest rówana 0 to zwiększana jest ilość rzutów, w innym przypadku zwiększany jest wynik
        pełnych/zbieranych i suma.
        """
        self.number_of_rzut = number_of_rzut
        if new_value == 0:
            self.dziur += 1
            return
        if (number_of_rzut - 1) % 30 < 15:
            self.pelne += new_value
        else:
            self.zbierane += new_value
        self.suma += new_value


class _StorageDataTor:
    """
    Klasa przechowuje wyniki pojedyńczego toru.

    update_data(int, int): None - aktualizuje wynik pojedyńczego rzutu i sumę pełnych/zbieranych i sumę ogólną
    number_of_rzut - numer rzutu
    pelne - suma pełnych
    zbierane - suma zbieranych
    dziur - ilość dziur
    suma - suma
    PS - ilość zdobytych punktów setowych na torze
    list_pelne - wyniki w poszczególnych rzutach do pełnych
    list_zbierane - wyniki w poszczególnych rzutach do zbieranych
    """
    def __init__(self) -> None:
        self.number_of_rzut: int = 0
        self.pelne: int = 0
        self.zbierane: int = 0
        self.dziur: int = 0
        self.suma: int = 0
        self.PS: float = 0
        self.list_pelne: list[Union[None, int]] = [None] * 15
        self.list_zbierane: list[Union[None, int]] = [None] * 15

    def __repr__(self) -> str:
        return f"""
            Rzut: {self.number_of_rzut}, Pełne: {self.pelne}, Zbierane: {self.zbierane}, Dziur: {self.dziur}
            List pełne: {self.list_pelne}
            List zbierane: {self.list_zbierane}
            List suma: {self.get_list_suma()}
        """

    def update_data(self, number_of_rzut: int, new_value: int) -> bool:
        """
        Funkcja do wpisywania dopisywania ilości zbitych kręgli do obiektu.

        Funkcja zarówno zwiększa sumę jak i zapisuje wynik w pojedyńczym rzucie.
        :param number_of_rzut: - numer aktualnego rzutu na torze
        :param new_value: - wartość w rzucie
        """
        if number_of_rzut > len(self.list_pelne) + len(self.list_zbierane):
            return False
        self.number_of_rzut = number_of_rzut
        index_in_list = number_of_rzut - 1
        if index_in_list < len(self.list_pelne):
            self.list_pelne[index_in_list] = new_value
            self.pelne += new_value
        else:
            index_in_list -= len(self.list_pelne)
            self.list_zbierane[index_in_list] = new_value
            self.zbierane += new_value
        self.suma += new_value

        if new_value == 0:
            self.dziur += 1

    def get_list_suma(self) -> list[int]:
        """Funkcja zwraca listę 30 elementów zawierającą poszczególne rzuty z pełnych i zbieranych."""
        return self.list_pelne + self.list_zbierane
