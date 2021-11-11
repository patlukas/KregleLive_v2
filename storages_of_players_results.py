"""Moduł służy do przechowywania danych, wyników graczy i drużyn"""

import copy
from search_players_rows import _CellInRow


class StorageOfAllPlayersScore:
    """
    Klasa przechowuje wyniki wszystkich graczy oraz drużyn.

    on_data_initialization(int, int) -> None - tworzy nową strukturę obiektu, jest wywoływana przy tworzeniu obiektu

    """
    def __init__(self, *, numer_of_team: int = 1, number_of_player_in_team: int = 1) -> None:
        """
        :param numer_of_team - ilość drużyn
        :param number_of_player_in_team - ilość graczy w drużynie

        teams - lista przechowująca wyniki graczy i drużyn
        number_of_teams - ilość drużyn
        number_of_players_in_team - ilość graczy w drużynie
        """
        self.teams: list[_StorageOfAllTeamResults] = []
        self.number_of_teams: int = 0
        self.number_of_players_in_team: int = 0
        self.on_data_initialization(numer_of_team, number_of_player_in_team)

    def on_data_initialization(self, numer_of_team: int, number_of_player_in_team: int) -> None:
        """
        Funkcja tworzy puste kontenery na dane.

        Funkcja w self.teams dodaje tyle elementów ile jest drużyn, i w każdym tworzy tyle elementów do przechowywania
        danych graczy ile jest graczy w drużynie. Dodatkowo ustawaia zmienne obeiktu do przechowywania ile jest drużyn
        i graczy w drużynie.
        """
        self.number_of_teams = numer_of_team
        self.number_of_players_in_team = number_of_player_in_team
        self.teams = [_StorageOfAllTeamResults for _ in range(numer_of_team)]

    def update_coord_cell(self, all_coord_cell: list[list[_CellInRow]]) -> bool:
        """
        Aktualizuje współrzędne graczy.

        Funkcja aktualizuje listę zawierającą współrzędne komórek z danymi graczy na obrazie tabeli.
        :param all_coord_cell - zawiera obiekty ze współrzędnymi podzielone odpowiednio na drużyny
        :return - bool - czy udało się zaaktualizować
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
                elif not difference_sum_ps and sum_ps > 0:
                    difference_sum_team = players[j].result_main.suma - players[k].result_main.suma
                    pd = 1 if difference_sum_team > 0 else 0 if difference_sum_team < 0 else 0.5
                list_sum_pd[j] += pd
                players[j].update_league_points(pd, sum_ps, league_results[j]["list_ps"])

        list_sum_team = (self.teams[0].team_results.suma, self.teams[0].team_results.suma)
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
    def __init__(self, number_of_players: int) -> None:
        self.players_results: list[_StorageOfPlayerResults] = []
        self.team_results: _StorageOfTeamResults = _StorageOfTeamResults()
        for i in range(number_of_players):
            self.players_results.append(_StorageOfPlayerResults())


class _StorageOfTeamResults:
    def __init__(self) -> None:
        self.suma: int = 0
        self.pelne: int = 0
        self.zbierane: int = 0
        self.dziur: int = 0
        self.number_of_rzut: int = 0
        self.PD: int = 0
        self.PS: int = 0
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
        self.cell_in_row: _CellInRow
        self.tor_number: int = 0
        self.number_of_tor: int = 0
        self.number_of_rzut_in_tor: int = 0
        self.result_tory: list[_StorageDataTor] = [
            _StorageDataTor(),
            _StorageDataTor(),
            _StorageDataTor(),
            _StorageDataTor()
        ]
        self.result_main: _StorageDataBasic = _StorageDataBasic()

    def __repr__(self):
        return f"""
            Numer toru: {self.tor_number}, który tor: {self.number_of_tor},  \
            rzut na torze: {self.number_of_rzut_in_tor}
            Tory: {self.result_tory.__repr__()}
            Główne: {self.result_main.__repr__()}
                Pełne: {self.get_list_pelne()}
                Zbierane: {self.get_list_zbierane()}
                Suma: {self.get_list_suma()}
        """

    def get_list_pelne(self) -> list[int]:
        """Zwraca listę z wynikami osiągniętymi w pełnych."""
        list_pelne = []
        for tor in self.result_tory:
            list_pelne += tor.list_pelne
        return list_pelne

    def get_list_zbierane(self):
        """Zwraca listę z wynikami osiągniętymi w zbieranych."""
        list_zbierane = []
        for tor in self.result_tory:
            list_zbierane += tor.list_zbierane
        return list_zbierane

    def get_list_suma(self):
        """Zwraca listę z wynikami osiągniętymi w całej grze."""
        list_pelne = []
        for tor in self.result_tory:
            list_pelne += tor.get_list_suma()
        return list_pelne

    def update_data(self, tor_number=None, number_of_rzut_in_tor=0, result_in_last_rzut=0):
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

    def get_cell(self, index_column, img):
        """
        Funkcja zwraca współrzędne komórki

        :param index_column: (int) index komórki do zwrócenia, czyli numer kolumny
        :param img: (np.ndarray) obraz z którego zostanie wycięta komórka
        :return: (np.ndarray) wycięta komórka
                (bool) jeżeli nie m ustawionych współrzędnych
        """
        if self.cell_in_row is None:
            return []
        y0, y1 = self.cell_in_row.get_coord_y()
        x0, x1 = self.cell_in_row.get_coord_x(index_column)
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
        def __init__(self):
            self.__series_length_for_the_same_type_of_game = 15
            self.number_of_rzut = 0
            self.pelne = 0
            self.zbierane = 0
            self.dziur = 0
            self.suma = 0
            self.sum_of_eliminations_and_final = 0
            self.PS = 0
            self.PD = 0

        def __repr__(self):
            return f"""
                Rzut: {self.number_of_rzut}, Pełne: {self.pelne}, Zbierane: {self.zbierane}, Dziur: {self.dziur}
            """

        def update_data(self, number_of_rzut, new_value):
            self.number_of_rzut = number_of_rzut
            if new_value == 0:
                self.dziur += 1
                return
            if (number_of_rzut - 1) % 30 < self.__series_length_for_the_same_type_of_game:
                self.pelne += new_value
            else:
                self.zbierane += new_value
            self.suma += new_value


class _StorageDataTor:
    def __init__(self):
        self.number_of_rzut = 0
        self.pelne = 0
        self.zbierane = 0
        self.dziur = 0
        self.suma = 0
        self.PS = 0
        self.list_pelne = [None] * 15
        self.list_zbierane = [None] * 15

    def __repr__(self):
        return f"""
            Rzut: {self.number_of_rzut}, Pełne: {self.pelne}, Zbierane: {self.zbierane}, Dziur: {self.dziur}
            List pełne: {self.list_pelne}
            List zbierane: {self.list_zbierane}
            List suma: {self.get_list_suma()}
        """

    def update_data(self, number_of_rzut, new_value):
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

    def get_list_suma(self):
        return self.list_pelne + self.list_zbierane