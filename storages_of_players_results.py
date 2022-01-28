"""Moduł służy do przechowywania danych, wyników graczy i drużyn"""

from typing import Union
import numpy as np

from search_players_rows import _CellInRow


class StorageOfAllPlayersScore:
    """
    Klasa przechowuje wyniki wszystkich graczy oraz drużyn.

    on_data_initialization(int, int) -> None - tworzy nową strukturę obiektu, jest wywoływana przy tworzeniu obiektu
    calculate_league_points() -> bool - Funkcja zlicza punkty ligowe graczy i drużyn
    get_data_from_player(int, int, str) -> str - funkcja zwraca potrzebny wynik/napis należący do wybranego gracza
    get_data_from_team(int, str) -> str - funkcja zwraca potrzebny wynik/napis należący do wybranego zespołu

    teams - lista przechowująca wyniki graczy i drużyn
    number_of_teams - ilość drużyn
    number_of_players_in_team - ilość graczy w drużynie
    """
    def __init__(self, *, number_of_team: int = 1, number_of_player_in_team: int = 1) -> None:
        """
        :param number_of_team - ilość drużyn
        :param number_of_player_in_team - ilość graczy w drużynie
        """
        self.teams: list[_StorageOfAllTeamResults] = []
        self.number_of_teams: int = 0
        self.number_of_players_in_team: int = 0
        self.on_data_initialization(number_of_team, number_of_player_in_team)

    def __repr__(self) -> str:
        return f"""
            {self.teams=}
            {self.number_of_teams=}
            {self.number_of_players_in_team=}
        """

    def on_data_initialization(self, number_of_team: int, number_of_player_in_team: int) -> None:
        """
        Funkcja tworzy puste kontenery na dane.

        Funkcja w self.teams dodaje tyle elementów ile jest drużyn, i w każdym tworzy tyle elementów do przechowywania
        danych graczy ile jest graczy w drużynie. Dodatkowo ustawaia zmienne obeiktu do przechowywania ile jest drużyn
        i graczy w drużynie.
        """
        self.number_of_teams = number_of_team
        self.number_of_players_in_team = number_of_player_in_team
        self.teams = [_StorageOfAllTeamResults(number_of_player_in_team) for _ in range(number_of_team)]

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

    def get_data_from_player(self, index_team: int, index_player: int, name_result: str) -> str:
        """
        Metoda do pobrania wyniku/napisu dotyczącego gracza do wpisania w komórce.

        :param index_team: numer zespołu do którego należy gracz
        :param index_player: numer gracza w zespole
        :param name_result: nazwa statystyki
        :return: napis/wynik do wpisania w komórce

        Możliwe statystyki:
            1. Nazwy:
                - name - nazwa gracza lub po zmianie inicjał imienia i nazwisko każdego gracza
                - team_name - nazwa drużyny
            2. Główne wyniki (jeżeli numer rzutu == 0 wtedy ""):
                suma, zbierane, pelne, number_of_rzut, dziur, PS, PD
            3. Wyniki na torach (jeżeli gracz nie oddał na tym torze rzutu to ""):
                - "torX_Y" lub "torX_Y_Z"-
                    - zamiast X numer <1,4>
                    - zamiast Y :
                        number_of_rzut, pelne, zbierane, dziur, suma, PS,
                    - zaminiast Z (jak nie spełnione to ""):
                        - win - gracz wygrywa/wygrał tor
                        - draw - gracz remisuje/zremisował tor
                        - lose - gracz przegrywa/przegrał tor
            4. Wyniki w poszczególnych rzutach na torach
                - "torX_rzutN"
                    - zamiast X numer <1,4>
                    - zamiast N numer rzutu na wybranym torze, jak gracz jeszcze nie oddał  tego rztu to ""
            5. Inna nazwa statystyki wtedy ""
        """
        return self.teams[index_team].players_results[index_player].get_data(name_result)

    def get_data_from_team(self, index_team: int, name_result: str) -> str:
        """
        Metoda do pobrania wyniku/napisu dotyczącego drużyny do wpisania w komórce.

        :param index_team: numer zespołu do którego należy gracz
        :param name_result: nazwa statystyki
        :return: napis/wynik do wpisania w komórce

        Możliwe statystyki:
            1. Nazwy:
                - name - nazwa drużyny
            2. Główne wyniki:
                suma, zbierane, pelne, number_of_rzut, dziur, PS, PD, sum_difference
            3. Specjalne:
                sum_difference_non_negative - >= różnica
                sum_difference_positive > różnica
                sum_difference_negative < różnica
            4. Inna nazwa statystyki wtedy ""
        """
        return self.teams[index_team].team_results.get_data(name_result)


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
            self.players_results.append(_StorageOfPlayerResults(self.team_results.update_team_result))

    def __repr__(self) -> str:
        return f"""
            {self.players_results=}
            {self.team_results}
        """


class _StorageOfTeamResults:
    """
    Klasa do przechowywania zsumowanych wyników całej drużyny.

    update_league_points(int, int, int): None - aktualizuje PD, PS i różnicę między drużynami
    set_name(str): None - aktualizuje nazwę drużyny

    name - nazwa drużyny
    suma - zsumowany wynik
    pelne - zsumowane pelne
    zbierane - zsumowane zbierane
    dziur - zsumowana ilość rzutów wadliwych
    number_of_rzut - zsumowana ilość rzutów drużyny
    PD - zsumowana ilość punktów drużyny
    PS - zsumowana ilość punktów setowych
    sum_difference - różnica między tą drużyną a przeciwnikiem (this - opposit)
    """
    def __init__(self) -> None:
        self.name: str = ""
        self.suma: int = 0
        self.pelne: int = 0
        self.zbierane: int = 0
        self.dziur: int = 0
        self.number_of_rzut: int = 0
        self.PD: float = 0
        self.PS: float = 0
        self.sum_difference: int = 0

    def __str__(self) -> str:
        return f"""
            Wyniki drużyny:
                {self.suma=}
                {self.pelne=}
                {self.zbierane=}
                {self.dziur=}
                {self.number_of_rzut=}
                {self.PS=}
                {self.PD=}
                {self.sum_difference=}
        """

    def set_name(self, name: str) -> None:
        """
        Aktualizuje nazwę drużyny.

        :param name - nowa nazwa zespołu
        """
        self.name = name

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

    def update_team_result(self, rzut_difference: int, pelne_difference: int, zbierane_difference: int) -> None:
        """
        Funkcja zwiększa ilość rzutów, pelne, zbierane i dziur drużyny. Otrzymuje różnicę jaką gracz ma w porównaniu
        do przedostatniego rzutu.

        :param rzut_difference: - o ile wzrosła ilość rzutów
        :param pelne_difference: - o ile wzrosłą liczba pełnych gracza
        :param zbierane_difference: - o ile wzrosłą liczba zbieranych
        """
        if rzut_difference == 0 and pelne_difference == 0 and zbierane_difference == 0:
            return
        self.number_of_rzut += rzut_difference
        if pelne_difference == 0 and zbierane_difference == 0:
            self.dziur += 1
            return
        self.pelne += pelne_difference
        self.zbierane += zbierane_difference
        self.suma += pelne_difference + zbierane_difference

    def get_data(self, name_result: str) -> str:
        """
        Metoda do pobrania wyniku/napisu dotyczącego drużyny do wpisania w komórce.

        :param name_result: nazwa statystyki
        :return: napis/wynik do wpisania w komórce

        Możliwe statystyki:
            1. Nazwy:
                - name - nazwa drużyny
            2. Główne wyniki:
                suma, zbierane, pelne, number_of_rzut, dziur, PS, PD, sum_difference
            3. Specjalne:
                sum_difference_non_negative - >= różnica
                sum_difference_positive > różnica
                sum_difference_negative < różnica
            4. Inna nazwa statystyki wtedy ""
        """
        if name_result == "sum_difference_non_negative":
            if self.sum_difference >= 0:
                return str(self.sum_difference)
            else:
                return ""
        if name_result == "sum_difference_positive":
            if self.sum_difference > 0:
                return str(self.sum_difference)
            else:
                return ""
        if name_result == "sum_difference_negative":
            if self.sum_difference < 0:
                return str(self.sum_difference)
            else:
                return ""
        try:
            return str(self.__getattribute__(name_result))
        except AttributeError:
            return ""


class _StorageOfPlayerResults:
    """
    Tworzy obiekt do przechowywania wyniku pojedyńczego gracza.

    Klasa tworzy obiekty służące do przechowywania:
        - wyników całego startu (ilość rzutów, pełnych, zbieranych, itp)
        - wyników na poszczególnych torach, w tablicy cztero elementowaj przechowuje oddzielnie info o każdym torze
        - wyniki z ligii
        - współrzędne komórek należącyhc do gracza

    get_list_pelne() -> list[int]
    get_list_zbierane() -> list[int]
    get_list_suma() -> list[int]
    update_data(Union[int, None], int, int) -> None - aktualizuje wynik
    update_league_points(int, int, list<int>) -> None - aktualizuje wyniki ligowe gracza

    list_name - lista nazw graczy (jeżeli była zmiana to aktualny gracz jest pod ustatnim indeksem)
    list_when_changes - zaiwera info w którym rzucie gracz zaczął grać
    team_name - nazwa drużyny
    tor_number - index toru, na ktrym gra zawodnik (w Gostyniu od 1 do 6)
    coord_in_row - obiekt z danymi gdzie na obrazie znajdują się komórki z danymi o graczach
    number_of_tor - numer touru podczas gry (od 0 do 4) - 4 oznacza koniec gry
    number_of_rzut_in_tor - numer rzutu na torze
    result_tory - przechowuje pod każdym indeksem informacje o jednym torze
    result_main - przechowuje podsumowanie o grze
    """
    def __init__(self, update_team_result) -> None:
        """
        :param update_team_result: func - funkcja z obiektu _StorageOfTeamResults służąca do aktualizacji wyniku drużyny
        __game_is_end: czy zawodnik zakończył już grę
        __update_team_result: matoda z klasy _StorageOfTeamResults do aktualizacji danych drużyny
        """
        self.list_name: list[str] = ["Patryk Ja", "Kwadd", ""]
        self.list_when_changes: list[int] = [0, 2]
        self.team_name: str = ""
        self.__game_is_end: bool = False
        self.__update_team_result = update_team_result
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
            Numer toru: {self.tor_number}, który tor: {self.number_of_tor}, rzut na torze: {self.number_of_rzut_in_tor}
            Tory: {self.result_tory.__repr__()}
            Główne: {self.result_main.__repr__()}
                Pełne: {self.get_list_pelne()}
                Zbierane: {self.get_list_zbierane()}
                Suma: {self.get_list_suma()}
        """

    def set_list_name(self, list_name: list[str], list_when_changes: list[int] = (0)):
        """
        Metoda ustawia nazwę gracza oraz kiedy były zmiany.

        list_name zawiera w komórce pod indexsem -1 aktualnego gracza
        list_when_changes używana w ligowych rozgrywkach, gdy są możliwe zmiany

        :param list_name: lista graczy, w indiwidualnych zawodach len == 1, ale w ligowych po zmienie zaiwera kilka nazw
        :param list_when_changes: pod indeksem 0 jest rzut od którego gracz 0 zaczął (czyli rzut numer 0),
                                  w przypadku zmiany pod indexem 1 kiedy gracz 1 na list_name zaczął
        """
        self.list_name = list_name
        self.list_when_changes = list_when_changes

    def set_team_name(self, team_name: str) -> None:
        """
        Metoda ustawia nazwę drużyny do której gracz należy

        :param team_name: nazwa zespołu do której gracz należy
        """
        self.team_name = team_name

    def get_all_name_to_string(self) -> str:
        """
        Metoda zwraca napis z nazwą gracza, lub skróconą formę w przypadku kilku osób (inicjał imienia)

        :return: Jak len == 1: Imię Nazwisko, jak len > 1: Imicjał imienia. Nazwisko/...
        """
        if len(self.list_name) == 1:
            return self.list_name[0]

        string = ""
        for name in self.list_name:
            list_word = name.split()
            string += "/"
            if len(list_word) == 0:
                continue
            for word in list_word[:-1]:
                string += word[0]+". "
            string += list_word[-1]
        else:
            string = string[1:]
        return string

    def get_name_playing_player(self) -> str:
        """
        Metoda zwraca nazwę aktualnie grającego gracza.
        """
        return self.list_name[-1]

    def get_list_pelne(self) -> list[Union[None, int]]:
        """Zwraca listę z wynikami osiągniętymi w pełnych."""
        list_pelne = []
        for tor in self.result_tory:
            list_pelne += tor.list_pelne
        return list_pelne

    def get_list_zbierane(self) -> list[Union[None, int]]:
        """Zwraca listę z wynikami osiągniętymi w zbieranych."""
        list_zbierane = []
        for tor in self.result_tory:
            list_zbierane += tor.list_zbierane
        return list_zbierane

    def get_list_suma(self) -> list[Union[None, int]]:
        """Zwraca listę z wynikami osiągniętymi w całej grze."""
        list_pelne = []
        for tor in self.result_tory:
            list_pelne += tor.get_list_suma()
        return list_pelne

    def update_data(self, tor_number: Union[str, None] = "", number_of_rzut_in_tor: Union[str, None] = "",
                    result_player: Union[str, None] = "0") -> int:
        """
        Funkcja do aktualizacji danych.

        Jeżeli któraś z podanych wartości to None, to oznacza że nie udało się odczytać odczytać tej wartości.
        :param tor_number: numer toru na którym gra zawodnik (w Gostyniu 1-6), lub "" gdy nie gra obecnie
        :param number_of_rzut_in_tor: numer rzutu na torze
        :param result_player: wynik w całej grze
        :return: 0 - nie było zmian, 1 - były zmiany, -1 - gracz już skończył grę, -2 - któraś wartość była błędna
        """
        if self.__game_is_end:
            return -1
        if tor_number is None or number_of_rzut_in_tor is None or result_player is None \
                or number_of_rzut_in_tor == "" or result_player == "":
            return -2

        tor_number = (None if tor_number == "" else int(tor_number))
        number_of_rzut_in_tor = int(number_of_rzut_in_tor)
        result_player = int(result_player)

        result_in_last_rzut = result_player - self.result_main.suma
        rzut_now = self.number_of_tor*30 + self.number_of_rzut_in_tor
        self.tor_number = tor_number
        if number_of_rzut_in_tor == 0 and self.number_of_rzut_in_tor != 0:
            self.number_of_tor += 1
        elif number_of_rzut_in_tor == self.number_of_rzut_in_tor and result_in_last_rzut == 0:
            return 0
        self.number_of_rzut_in_tor = number_of_rzut_in_tor
        if self.number_of_tor == 4:
            self.__game_is_end = True
            return -1
        if number_of_rzut_in_tor:
            rzut_difference = self.number_of_tor*30 + number_of_rzut_in_tor - rzut_now
            if number_of_rzut_in_tor <= 15:
                self.__update_team_result(rzut_difference, result_in_last_rzut, 0)
            else:
                self.__update_team_result(rzut_difference, 0, result_in_last_rzut)

            self.result_tory[self.number_of_tor].update_data(number_of_rzut_in_tor, result_in_last_rzut)
            self.result_main.update_data(number_of_rzut_in_tor + self.number_of_tor*30, result_in_last_rzut)
        return 1

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

    def get_data(self, name_result: str) -> str:
        """
        Metoda do pobrania wyniku/napisu dotyczącego gracza do wpisania w komórce.

        :param name_result: nazwa statystyki
        :return: napis/wynik do wpisania w komórce

        Możliwe statystyki:
            1. Nazwy:
                - name - nazwa gracza lub po zmianie inicjał imienia i nazwisko każdego gracza
                - team_name - nazwa drużyny
            2. Główne wyniki (jeżeli numer rzutu == 0 wtedy ""):
                suma, zbierane, pelne, number_of_rzut, dziur, PS, PD
            3. Wyniki na torach (jeżeli gracz nie oddał na tym torze rzutu to ""):
                - "torX_Y" lub "torX_Y_Z"-
                    - zamiast X numer <1,4>
                    - zamiast Y :
                        number_of_rzut, pelne, zbierane, dziur, suma, PS,
                    - zaminiast Z (jak nie spełnione to ""):
                        - win - gracz wygrywa/wygrał tor
                        - draw - gracz remisuje/zremisował tor
                        - lose - gracz przegrywa/przegrał tor
            4. Wyniki w poszczególnych rzutach na torach
                - "torX_rzutN"
                    - zamiast X numer <1,4>
                    - zamiast N numer rzutu na wybranym torze, jak gracz jeszcze nie oddał  tego rztu to ""
            5. Inna nazwa statystyki wtedy ""
        """
        player_lanes_results = self.result_tory
        if name_result == "name":
            return self.get_all_name_to_string()
        try:
            if name_result[:3] == "tor":
                index_tor = int(name_result[3]) - 1
                list_word = name_result.split("_")
                kind = list_word[1]
                if player_lanes_results[index_tor].number_of_rzut == 0:
                    return ""
                if kind[:4] == "rzut":
                    result = player_lanes_results[index_tor].get_list_suma()[int(kind[4:]) - 1]
                    return "" if result is None else str(result)
                else:
                    if len(list_word) == 2:
                        return str(player_lanes_results[index_tor].__getattribute__(kind))
                    if player_lanes_results[index_tor].PS == {"win": 1, "draw": 0.5, "lose": 0}[list_word[2]]:
                        return str(player_lanes_results[index_tor].__getattribute__(kind))
                return ""
            if self.result_main.number_of_rzut == 0:
                return ""
            return str(self.result_main.__getattribute__(name_result))
        except AttributeError:
            return ""
        except IndexError:
            return ""


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

    def get_list_suma(self) -> list[Union[None, int]]:
        """Funkcja zwraca listę 30 elementów zawierającą poszczególne rzuty z pełnych i zbieranych."""
        return self.list_pelne + self.list_zbierane
