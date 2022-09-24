"""."""
import json

import cv2
import numpy as np
from PIL import Image
import os

from storages_of_players_results import StorageOfAllPlayersScore, _StorageOfPlayerResults
from methods_to_draw_on_image import MethodsToDrawOnImage
from informing import Informing
from datetime import datetime
import copy


class CreatingSummaryTables(MethodsToDrawOnImage):
    """
    Klasa jest wykorzystywana do tworzenia plansz z wynikami

    create_images_with_summary_results() - tworzy plansze ze statystykami
    """

    def __init__(self, path_to_summary_table_settings: str, obj_with_results: StorageOfAllPlayersScore | None):
        """
        Metoda inicjuje klasę i odczytuje ustawienia.

        :param path_to_summary_table_settings: ścieżka do pliku z ustawieniami dotyczącymi plansz
        :param obj_with_results: obiekt z wynikami graczy i drużyn
        """
        super().__init__()
        self.__summary_tables_settings: dict | None = self.__get_summary_tables_settings(path_to_summary_table_settings)
        self.__obj_to_storage_results: StorageOfAllPlayersScore | None = obj_with_results
        self.__statistic_players: list[dict] = []

    def create_images_with_summary_results(self) -> None:
        """Metoda jest odpowiedzialna za stworzenie wszystkich plansz ze ststystykami."""
        self.__calculate_statistic()
        date = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        path_to_historical_statistics = f'{self.__summary_tables_settings["path_to_save_historical_statistics"]}{date}'
        if not os.path.exists(path_to_historical_statistics):
            os.mkdir(path_to_historical_statistics)
        path_to_historical_statistics += "/ "
        CreateSummaryTablesComparisonTeamsAndTheBestPlayers(self.__statistic_players,
                                                            self.__summary_tables_settings[
                                                                "path_to_save_current_statistics"],
                                                            path_to_historical_statistics,
                                                            self.__summary_tables_settings["path_to_font"])
        CreateSummaryTablesDistributionResult(self.__statistic_players,
                                              self.__summary_tables_settings["path_to_save_current_statistics"],
                                              path_to_historical_statistics,
                                              self.__summary_tables_settings["path_to_font"])

    def __calculate_statistic(self) -> None:
        """
        Metoda analizuje wyniki graczy i zapisuje statystyki drużyn i graczy w self.____statistic_players.

        retrun: list<dict{"team": <dict> ststystyki drużyny, "players: list<dict: statystyki gracza>>}>

        Każdy słownik ze statystykami zawiera:
            name: <string> nazwa gracza/drużyny
            PS: <float> ilość zdobytych punktów setowych,
                PD: <float> ilość zdobytych punktów drużynowych,
                suma: <int> wynik
                pelne: <int> wynik pełnych
                zbierane: <int> wynik zbieranych
                dziur: <int> ilość rzutów wadliwych
                rozklad_w_ile_uklad: <dict> słownik z kluczami od 1 do 15, w każdym kluczu jest zapisana ile układów
                                        gracz zebrał w ilość rzutów odpowiadającyhc kluczowi. Jeżeli gracz nie ukończył
                                        układu do końca zbieranych na danym torze to ten ukłąd nie jest uwzględniany
                                        w tej statystyce
                rozklad_co_po_9: <dict> słownik z kluczami od 0 do 9, w każdym kluczu jest zapisana ile razy gracz zbił
                                    daną ilość kręgli po rzucie kiedy strącił 9 kręgli
                rozklad_pelne: <dict> słownik z kluczami od 0 do 9, w każdym kluczu jest zapisana ile razy gracz zbił
                                    daną ilość kręgli w pełnych
                rozklad_pelne: <dict> słownik z kluczami od 0 do 9, w każdym kluczu jest zapisana ile razy gracz zbił
                                    daną ilość kręgli w rozbiciach zbieranych
                rozklad_pelne: <dict> słownik z kluczami od 0 do 9, w każdym kluczu jest zapisana ile razy gracz zbił
                                    daną ilość kręgli w pełnych i rezbiciach zbieranych
        """
        if self.__obj_to_storage_results is None:
            return
        self.__statistic_players = []
        for team in self.__obj_to_storage_results.teams:
            list_player_stat = []
            for player in team.players_results:
                list_player_stat.append(self.__get_player_stat(player))
            team_name = team.team_results.name
            self.__statistic_players.append(
                {
                    "team": self.__get_team_stat(team_name, list_player_stat, team.team_results.PD),
                    "players": list_player_stat
                }
            )
        return

    @staticmethod
    def __get_player_stat(player_results: _StorageOfPlayerResults) -> dict:
        """
        Metoda odpowiada za zwrócenie słownika z statystykami gracza.

        :param player_results: obiekt przechowujący wyniki gracza
        return: słownik z przeredagowanymi wynikami gracza, w słowniku są następujące dane:
            {
                name: <string> nazwa gracza
                PS: <float> ilość zdobytych punktów setowych,
                PD: <float> ilość zdobytych punktów drużynowych,
                suma: <int> wynik gracza
                pelne: <int> wynik pełnych gracza
                zbierane: <int> wynik zbieranych gracza
                dziur: <int> ilość rzutów wadliwych gracza
                tor_best_suma: <int> najlepszy wynik toru
                tor_best_pelne: <int> najlepszy wynik pelnych toru
                tor_best_zbierane: <int> najlepszy wynik zbieranych toru
                rozklad_w_ile_uklad: <dict> słownik z kluczami od 1 do 15, w każdym kluczu jest zapisana ile układów
                                        gracz zebrał w ilość rzutów odpowiadającyhc kluczowi. Jeżeli gracz nie ukończył
                                        układu do końca zbieranych na danym torze to ten ukłąd nie jest uwzględniany
                                        w tej statystyce
                rozklad_co_po_9: <dict> słownik z kluczami od 0 do 9, w każdym kluczu jest zapisana ile razy gracz zbił
                                    daną ilość kręgli po rzucie kiedy strącił 9 kręgli
                rozklad_pelne: <dict> słownik z kluczami od 0 do 9, w każdym kluczu jest zapisana ile razy gracz zbił
                                    daną ilość kręgli w pełnych
                rozklad_rozbicia: <dict> słownik z kluczami od 0 do 9, w każdym kluczu jest zapisana ile razy gracz zbił
                                    daną ilość kręgli w rozbiciach zbieranych
                rozklad_all: <dict> słownik z kluczami od 0 do 9, w każdym kluczu jest zapisana ile razy gracz zbił
                                    daną ilość kręgli w pełnych i rezbiciach zbieranych
            }
        UWAGA: Jeżeli chociaż raz zostało coś źle zapisane w wynikach zbieranych, np była nieuwzglądniona czerwona
                kartka i nie zgadza się ilość kręgli to funkcja nie uwzglądnia statystyk ze zbieranych
        """

        player_stat = {
            "name": player_results.get_all_name_to_string(),
            "PS": player_results.result_main.PS,
            "PD": player_results.result_main.PD,
            "suma": player_results.result_main.suma,
            "pelne": player_results.result_main.pelne,
            "zbierane": player_results.result_main.zbierane,
            "dziur": player_results.result_main.dziur,
            "tor_best_suma": 0,
            "tor_best_pelne": 0,
            "tor_best_zbierane": 0,
            "best_seria_9": 0,
            "rozklad_w_ile_uklad": {
                1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0, 15: 0
            },
            "rozklad_co_po_9": {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0},
            "rozklad_pelne": {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0},
            "rozklad_rozbicia": {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0},
            "rozklad_all": {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0}
        }

        for i in player_results.get_list_pelne():
            if i is None or i < 0 or i > 9:
                continue
            player_stat["rozklad_pelne"][i] += 1
            player_stat["rozklad_all"][i] += 1

        list_suma = player_results.get_list_suma()
        for i in range(len(list_suma) - 1):
            next_result = list_suma[i + 1]
            if list_suma[i] != 9 or next_result is None or next_result < 0 or next_result > 9:
                continue
            player_stat["rozklad_co_po_9"][next_result] += 1

        len_seria = 0
        for i in range(120):
            if list_suma[i] == 9:
                len_seria += 1
            if list_suma[i] != 9 or i == 119:
                if len_seria > player_stat["best_seria_9"]:
                    player_stat["best_seria_9"] = len_seria
                len_seria = 0

        all_ok = True
        for tor_zbierane in player_results.get_lists_zbierane_with_unrecognized_results_due_to_red_cards():
            zbite_kregle = 0
            w_ile_uklad = 0
            for result in tor_zbierane:
                if result is None:
                    continue
                if result < 0 or result > 9:
                    all_ok = False
                    break
                if zbite_kregle == 0:
                    player_stat["rozklad_rozbicia"][result] += 1
                zbite_kregle += result
                w_ile_uklad += 1
                if zbite_kregle > 9:
                    all_ok = False
                    break
                if zbite_kregle == 9:
                    player_stat["rozklad_w_ile_uklad"][w_ile_uklad] += 1
                    w_ile_uklad = 0
                    zbite_kregle = 0

        if all_ok:
            for key in player_stat["rozklad_rozbicia"].keys():
                player_stat["rozklad_all"][key] += player_stat["rozklad_rozbicia"][key]
        else:
            player_stat["rozklad_rozbicia"] = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0}
            player_stat["rozklad_w_ile_uklad"] = {
                1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0, 15: 0
            }

        for tor in player_results.result_tory:
            if tor.suma > player_stat["tor_best_suma"]:
                player_stat["tor_best_suma"] = tor.suma
            if tor.suma > player_stat["tor_best_pelne"]:
                player_stat["tor_best_pelne"] = tor.pelne
            if tor.suma > player_stat["tor_best_zbierane"]:
                player_stat["tor_best_zbierane"] = tor.zbierane
        return player_stat

    @staticmethod
    def __get_team_stat(team_name: str, list_player_stat: list[dict], team_pd: float) -> dict:
        """
        Metoda sumuje statystyki graczy drużyny i zwraca je w słowniku

        :param team_name: <string> nazwa drużyny
        :param list_player_stat: lista słowników ze statystykami graczy
        :param team_pd: ilość zdobytych punktów drużynowych przez drużynę
        retrun: słownik z sumaowanymi wynikami drużyny, w słowniku są następujące dane:
            {
                name: <string> nazwa drużyny
                PS: <float> ilość zdobytych punktów setowych,
                PD: <float> ilość zdobytych punktów drużynowych,
                suma: <int> wynik drużyny
                pelne: <int> wynik pełnych drużyny
                zbierane: <int> wynik zbieranych drużyny
                dziur: <int> ilość rzutów wadliwych drużyny
                rozklad_w_ile_uklad: <dict> słownik z kluczami od 1 do 15, w każdym kluczu jest zapisana ile układów
                                        gracze zebrlił w ilość rzutów odpowiadających kluczowi.
                rozklad_co_po_9: <dict> słownik z kluczami od 0 do 9, w każdym kluczu jest zapisana ile razy gracze
                                    zbili daną ilość kręgli po rzucie kiedy strącił 9 kręgli
                rozklad_pelne: <dict> słownik z kluczami od 0 do 9, w każdym kluczu jest zapisana ile razy gracze
                                    zbili daną ilość kręgli w pełnych
                rozklad_pelne: <dict> słownik z kluczami od 0 do 9, w każdym kluczu jest zapisana ile razy gracze
                                    zbili daną ilość kręgli w rozbiciach zbieranych
                rozklad_pelne: <dict> słownik z kluczami od 0 do 9, w każdym kluczu jest zapisana ile razy gracze
                                    zbili daną ilość kręgli w pełnych i rozbiciach zbieranych
            }
        """
        team_stat = {
            "name": team_name,
            "PS": 0,
            "PD": team_pd,
            "suma": 0,
            "pelne": 0,
            "zbierane": 0,
            "dziur": 0,
            "rozklad_w_ile_uklad": {
                1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0, 15: 0
            },
            "rozklad_co_po_9": {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0},
            "rozklad_pelne": {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0},
            "rozklad_rozbicia": {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0},
            "rozklad_all": {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0}
        }
        for player_stat in list_player_stat:
            for key in ["PS", "suma", "pelne", "zbierane", "dziur"]:
                team_stat[key] += player_stat[key]
            for key in ["rozklad_w_ile_uklad", "rozklad_co_po_9", "rozklad_pelne", "rozklad_rozbicia", "rozklad_all"]:
                for i in team_stat[key].keys():
                    team_stat[key][i] += player_stat[key][i]
        return team_stat

    @staticmethod
    def __get_summary_tables_settings(path_to_settings: str) -> dict | None:
        """."""
        try:
            file = open(path_to_settings, encoding='utf8')
            return json.load(file)
        except FileNotFoundError:
            Informing().warning(f"Nie można odczytać ustawień  tabeli z podsuowaniem z pliku {path_to_settings}")
            return None


class CreateSummaryTablesComparisonTeamsAndTheBestPlayers(MethodsToDrawOnImage):
    """Klasa odpowiedzialna za stworzenie planszy z porównaniem drużyn i wypisaniem najlepszych graczy."""

    def __init__(self, statistic_players: list[dict], path_to_save_current_stat: str,
                 path_to_save_historical_statistics: str, font_path: str):
        """
        Metoda tworzy planszę ze statystykami.

        :param statistic_players: lista słowników ze statystykami graczy
        :param path_to_save_current_stat: ścieżka do katalogu gdzie ma być zapisana plansza z porównaniem
        :param path_to_save_historical_statistics: ścieżka do katalogu gdzie ma być zapisana plansza z porównaniem
                                                    w nazwie będzie zawarta data i godzina zapisania obrazu
        :param font_path: ścieżka do pliku z czcionką

        __statistic_players: lista słowników ze statystykami graczy
        __clear_bar_two_team: nieywpełniony obraz używany do porównania drużyn
        __path_to_save_current_stat: ścieżka do katalogu gdzie ma być zapisana plansza z porównaniem
        __path_to_save_historical_statistics: ścieżka do katalogu gdzie ma być zapisana plansza z porównaniem
                                                    w nazwie będzie zawarta data i godzina zapisania obrazu
        """
        super().__init__()
        self.__statistic_players: list[dict] = statistic_players
        self.__clear_bar_two_team: np.ndarray = self.__create_clear_two_team_bar_chart()
        self.__path_to_save_current_stat: str = path_to_save_current_stat
        self.__path_to_save_historical_statistics: str = path_to_save_historical_statistics
        self.__font_path: str = font_path
        self.__create_img_stat()

    def __create_img_stat(self) -> None:
        """Metoda zarządza tworzneiem planszy ze statystykami oraz zapisuje je w systemi i pokazuje ją."""
        img = np.full((550, 1280, 3), 255, dtype=np.uint8)
        img[:, :] = (0, 255, 0)
        img_team_comparison = self.__create_two_team_comparison(self.__font_path)
        img_high_score_board = self.__create_high_score_board(self.__font_path)

        img = Image.fromarray(img, "RGB")
        img.paste(img_team_comparison, (0, 0))
        img.paste(img_high_score_board, (580, 0))
        img.save(self.__path_to_save_current_stat + "Stat_0.png", "PNG")
        img.save(f"{self.__path_to_save_historical_statistics}Stat_0.png", "PNG")
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        cv2.imshow("Statystyka: Porownanie druzyn i najlepsi zawodnicy", img)
        cv2.waitKey(1)

    def __create_two_team_comparison(self, font_path: str) -> Image:
        """
        Metoda tworzy kolumnę z porównaniami statystyk drużyn.

        :param font_path: <str> ścieżka do pliku z czcionką
        retrun: obraz kolumny z porównaniem statystyk drużyn. Porównywane są: PD, PS, suma, pełne, zbierane, dziury,
                ilość zbitych 9;8;7, ilość zbitych 9;8;7 w pełnych, ilość zbitych 9;8;7 w zbieranych, ilość ukłądów
                zbitych w 1;2;3;4;5; 6 lub wiięcej rzutach
        """
        if len(self.__statistic_players) != 2:
            return
        bar_chart = np.full((550, 580, 3), 255, dtype=np.uint8)
        bar_chart[:, :] = (0, 0, 0)
        bar_chart = Image.fromarray(bar_chart, "RGB")
        font_color = (255, 255, 0)
        bar_chart = self.draw_center_text_by_coord(bar_chart, self.__statistic_players[0]["team"]["name"], 18,
                                                   font_path, font_color, (2, 288, 0, 35))
        bar_chart = self.draw_center_text_by_coord(bar_chart, self.__statistic_players[1]["team"]["name"], 18,
                                                   font_path, font_color, (292, 578, 0, 35))

        stat = [
            [0, 0, "PD", None, "Ilość zdbobytych Punktów Drużynowych"],
            [0, 1, "PS", None, "Ilość zdbobytych Punktów Setowych"],
            [1, 2, "suma", None, "Suma drużyny"],
            [1, 3, "pelne", None, "Pełne"],
            [1, 4, "zbierane", None, "Zbierane"],
            [1, 5, "dziur", None, "Ilość rzutów wadliwych"],
            [2, 6, "rozklad_all", 9, "Ilość zbitych \"9\""],
            [2, 7, "rozklad_all", 8, "Ilość zbitych \"8\""],
            [2, 8, "rozklad_all", 7, "Ilość zbitych \"7\""],
            [3, 9, "rozklad_pelne", 9, "Ilość zbitych \"9\" w pełnych"],
            [3, 10, "rozklad_pelne", 8, "Ilość zbitych \"8\" w pełnych"],
            [3, 11, "rozklad_pelne", 7, "Ilość zbitych \"7\" w pełnych"],
            [4, 12, "rozklad_rozbicia", 9, "Ilość rozbitych \"9\" w zbieranych"],
            [4, 13, "rozklad_rozbicia", 8, "Ilość rozbitych \"8\" w zbieranych"],
            [4, 14, "rozklad_rozbicia", 7, "Ilość rozbitych \"7\" w zbieranych"],
            [5, 15, "rozklad_w_ile_uklad", 1, "Ilość układów zebranych w jednym rzucie"],
            [5, 16, "rozklad_w_ile_uklad", 2, "Ilość układów zebranych w dwóch rzutach"],
            [5, 17, "rozklad_w_ile_uklad", 3, "Ilość układów zebranych w trzech rzutach"],
            [5, 18, "rozklad_w_ile_uklad", 4, "Ilość układów zebranych w czterech rzutach"],
            [5, 19, "rozklad_w_ile_uklad", 5, "Ilość układów zebranych w pięcie rzutach"],
            [5, 20, "rozklad_w_ile_uklad", [6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
             "Ilość układów zebranych w sześciu lub więcej rzutach"],
        ]
        for nr_section, nr_stat, key_main_dict, key_second_dict, desc_stat in stat:
            if key_second_dict is None:
                home_stat_val = self.__statistic_players[0]["team"][key_main_dict]
                guest_stat_val = self.__statistic_players[1]["team"][key_main_dict]
            elif type(key_second_dict) == list:
                home_stat_val = 0
                guest_stat_val = 0
                for key in key_second_dict:
                    home_stat_val += self.__statistic_players[0]["team"][key_main_dict][key]
                    guest_stat_val += self.__statistic_players[1]["team"][key_main_dict][key]
            else:
                home_stat_val = self.__statistic_players[0]["team"][key_main_dict][key_second_dict]
                guest_stat_val = self.__statistic_players[1]["team"][key_main_dict][key_second_dict]
            one_chart = self.__create_two_team_bar_chart(desc_stat, home_stat_val, guest_stat_val,
                                                       font_path, (255, 255, 255))
            bar_chart.paste(Image.fromarray(one_chart, "RGB"), (0, 30 + nr_stat * 22 + nr_section * 10))
        return bar_chart

    def __create_high_score_board(self, font_path: str) -> Image:
        """
        Metoda tworzy kolumną ze statystykami pokazującymi kto jest w czym najlepszy.

        :param font_path: ścieżka do pliku z czcionką
        return: obraz ze stworzoną statystyką
        """
        if len(self.__statistic_players) != 2:
            return
        bar_chart = np.full((550, 700, 3), 255, dtype=np.uint8)
        bar_chart[:, :] = (0, 0, 0)
        bar_chart = Image.fromarray(bar_chart, "RGB")

        stat = [
            [0, 0, "suma", None, "Najlepszy wynik"],
            [0, 1, "pelne", None, "Najlepsze pełne"],
            [0, 2, "zbierane", None, "Najlepsze zbierane"],
            [1, 3, "tor_best_suma", None, "Najlepszy wynik jednego toru"],
            [1, 4, "tor_best_pelne", None, "Najlepsze pełnych na jednym torze"],
            [1, 5, "tor_best_zbierane", None, "Najlepsze zbieranych na jednym torze"],
            [2, 6, "best_seria_9", None, "Najdłuższa seria \"9\""],
            [3, 7, "rozklad_all", 9, "Najwięcej \"9\""],
            [3, 8, "rozklad_all", 8, "Najwięcej \"8\""],
            [3, 9, "rozklad_all", 7, "Najwięcej \"7\""],
            [3, 10, "rozklad_all", 6, "Najwięcej \"6\""],
            [4, 11, "rozklad_pelne", 9, "Najwięcej \"9\" w pełnych"],
            [4, 12, "rozklad_pelne", 8, "Najwięcej \"8\" w pełnych"],
            [4, 13, "rozklad_pelne", 7, "Najwięcej \"7\" w pełnych"],
            [4, 14, "rozklad_pelne", 6, "Najwięcej \"6\" w pełnych"],
            [5, 15, "rozklad_rozbicia", 9, "Najwięcej rozbitych \"9\" w zbieranych"],
            [5, 16, "rozklad_rozbicia", 8, "Najwięcej rozbitych \"8\" w zbieranych"],
            [5, 17, "rozklad_rozbicia", 7, "Najwięcej rozbitych \"7\" w zbieranych"],
            [5, 18, "rozklad_rozbicia", 6, "Najwięcej rozbitych \"6\" w zbieranych"],
            [6, 19, "rozklad_w_ile_uklad", 1, "Najwięcej zebranych układów w jednym rzucie"],
            [6, 20, "rozklad_w_ile_uklad", 2, "Najwięcej zebranych układów w dwóch rzutach"],
            [6, 21, "rozklad_w_ile_uklad", 3, "Najwięcej zebranych układów w trzech rzutach"],
            [6, 22, "rozklad_w_ile_uklad", 4, "Najwięcej zebranych układów w czterech rzutach"],
            [6, 23, "rozklad_w_ile_uklad", 5, "Najwięcej zebranych układów w pięciu rzutach"],
            [6, 24, "rozklad_w_ile_uklad", [6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
             "Najwięcej zebranych układów w 6 lub więcej rzutów"],
        ]

        bar_chart = self.draw_center_text_by_coord(bar_chart, "Najlepsi zawodnicy", 25, font_path,
                                                   (255, 255, 255), (10, 700, 0, 30))

        for nr_section, nr_stat, key_main_dict, key_second_dict, desc_stat in stat:
            number_of_player = 0
            players_name = ""
            best_result = 0
            for team_stat in self.__statistic_players:
                for player_stat in team_stat["players"]:
                    if key_second_dict is None:
                        val = player_stat[key_main_dict]
                    elif type(key_second_dict) == list:
                        val = 0
                        for key in key_second_dict:
                            val += player_stat[key_main_dict][key]
                    else:
                        val = player_stat[key_main_dict][key_second_dict]
                    if val > best_result:
                        number_of_player = 1
                        best_result = val
                        players_name = player_stat["name"]
                    elif val == best_result:
                        if number_of_player == 1:
                            players_name = self.__get_short_player_name(players_name)
                        players_name += ", " + self.__get_short_player_name(player_stat["name"])
                        number_of_player += 1
            if best_result == 0:
                players_name = "-----"
            bar_chart = self.draw_right_text_by_coord(bar_chart, desc_stat + f" ({best_result}): ", 14, font_path,
                                                      (255, 255, 0), (10, 360, 3 + nr_stat * 18 + nr_section * 10 + 30,
                                                                      22 + nr_stat * 18 + nr_section * 10 + 30))
            bar_chart = self.draw_left_text_by_coord(bar_chart, players_name, 14, font_path,
                                                     (255, 255, 255), (
                                                         360, 700, 3 + nr_stat * 18 + nr_section * 10 + 30,
                                                         22 + nr_stat * 18 + nr_section * 10 + 30))
        return bar_chart

    @staticmethod
    def __get_short_player_name(player_name: str) -> str:
        """
        Metoda skraca przekazaną nazwę gracza.

        :param player_name: nazwa gracza
        return: inicjał i nazwisko, lub niezmieniony str jeżeli jest już skrócone,
                np jak jest kilka skróconych nazw po zmianie
        """
        if "/" in player_name:
            return player_name
        split_name = player_name.split()
        if len(split_name) < 2:
            return player_name
        return split_name[0][0] + ". " + split_name[-1]

    def __create_two_team_bar_chart(self, stat_name: str, home_val: float | int, guest_val: float | int,
                                    font_path: str, font_color: tuple = (255, 255, 255)) -> np.ndarray:
        """
        Metoda tworzy obraz statystyki, gdzie są dwa słupki poziome oraz napis statystyki i rezultaty drużyn.

        :param stat_name: <str> nazwa statystyki, która będzie napisana na środku
        :param home_val: <float | int> wartość ststytyki którą osiągneli gospodarze
        :param guest_val: <float | int> wartość ststytyki którą osiągneli goście
        :param font_path: <str> ścieżka do pliku z czcionką, która ma być użyta
        :param font_color: <tuple> kolor czcionki
        :return: obraz ststytsyki o wymiarach 720x40
        """
        bar_chart = self.__clear_bar_two_team
        bar_chart = Image.fromarray(bar_chart, "RGB")
        bar_chart = self.draw_center_text_by_coord(bar_chart, stat_name, 13, font_path, font_color, (0, 580, 4, 20))
        bar_chart = self.draw_center_text_by_coord(bar_chart, home_val, 12, font_path, font_color, (15, 55, 5, 20))
        bar_chart = self.draw_center_text_by_coord(bar_chart, guest_val, 12, font_path, font_color, (525, 565, 5, 20))

        if home_val + guest_val > 0:
            width_bar_home = int(home_val / (home_val + guest_val) * 280)
            width_bar_guest = 280 - width_bar_home
        else:
            width_bar_home = 0
            width_bar_guest = 0
        bar_chart = np.array(bar_chart)
        color_home = (255, 0, 0) if home_val > guest_val else (150, 150, 150)
        color_guest = (255, 0, 0) if home_val < guest_val else (150, 150, 150)
        bar_chart = cv2.rectangle(bar_chart, (285 - width_bar_home, 20), (285, 22), color_home, -1)
        bar_chart = cv2.rectangle(bar_chart, (295, 20), (295 + width_bar_guest, 22), color_guest, -1)
        return bar_chart

    @staticmethod
    def __create_clear_two_team_bar_chart() -> np.ndarray:
        """
        Metoda tworzy pusty obraz wykorzystywany przez create_two_team_bar_chart i zwraca go.

        :return: pusty obraz statystyki
        """
        bar_chart = np.full((22, 580, 3), 255, dtype=np.uint8)
        bar_chart[:, :] = (0, 0, 0)
        bar_chart = cv2.rectangle(bar_chart, (5, 20), (285, 22), (50, 50, 50), -1)
        bar_chart = cv2.rectangle(bar_chart, (295, 20), (575, 22), (50, 50, 50), -1)
        return bar_chart


class CreateSummaryTablesDistributionResult(MethodsToDrawOnImage):
    """
    Klasa odpowiedzialna za stworzenie plansz ze statystykami, gdzie będzie pokazany:
        -   rozkład rzutów do pełnego układu (ilukrotnie gracz trafił określoną ilość kręgli)
        -   rozkład rzutów do pełnego układu w pełnych
        -   rozkład rozbić w zbieranych
        -   rozkład w ilu rzutach były kończone układy
        -   rozkłąd co było rozbijane w rzucie następującym po zbiciu 9
    """

    def __init__(self, statistic_players: list[dict], path_to_save_current_stat: str,
                 path_to_save_historical_statistics: str, font_path: str):
        """
        Metoda inicjuje klasę i tworzy plansze ze statystykami.

        :param statistic_players: list<team: ..., pleyers<list>> - zawiera statystyki graczy
        :param path_to_save_current_stat: ścieżka do katalogu gdzie mają być zapisane plamsze ze statystykami
        :param path_to_save_historical_statistics: ścieżka do katalogu gdzie mają być zapisane plamsze ze statystykami
                                                    w nazwie pliku będzie dodana data i godzina zapisania
        :param font_path: ścieżka do pliku z czcionką

        __statistic_players - zawiera statystyki graczy
        __path_to_save_current_stat - ścieżka do katalogu gdzie mają być zapisane plamsze ze statystykami
        __path_to_save_historical_statistics - ścieżka do katalogu gdzie mają być zapisane plamsze ze statystykami
                                                    w nazwie pliku będzie dodana data i godzina zapisania
        __font_path - ścieżka do pliku z czcionką
        """
        super().__init__()
        self.__font_path: str = font_path
        self.__statistic_players: list[dict] = statistic_players
        self.__path_to_save_current_stat: str = path_to_save_current_stat
        self.__path_to_save_historical_statistics: str = path_to_save_historical_statistics

        self.__create_all_stat_image()

    def __create_all_stat_image(self) -> None:
        """Metoda tworzy wszystkie plansze ze statsytsykami zawierające rozkłady wyników."""
        stat_all = [
            [9, [0], '"0"'],
            [8, [1], '"1"'],
            [7, [2], '"2"'],
            [6, [3], '"3"'],
            [5, [4], '"4"'],
            [4, [5], '"5"'],
            [3, [6], '"6"'],
            [2, [7], '"7"'],
            [1, [8], '"8"'],
            [0, [9], '"9"']
        ]
        stat_w_ile_uklad = [
            [9, [15, 14, 13, 12, 11, 10], 'w 10 lub więcej rzutach'],
            [8, [9], 'w 9 rzutach'],
            [7, [8], 'w 8 rzutach'],
            [6, [7], 'w 7 rzutach'],
            [5, [6], 'w 6 rzutach'],
            [4, [5], 'w 5 rzutach'],
            [3, [4], 'w 4 rzutach'],
            [2, [3], 'w 3 rzutach'],
            [1, [2], 'w 2 rzutach'],
            [0, [1], 'w 1 rzucie']
        ]
        self.__create_stat_distribution_table("Rozkład rzutów do pełnego układu", "rozklad_all",
                                              stat_all, "Statytyka: rozklad calej gry",
                                              "Stat_1.png", False, True, False)

        self.__create_stat_distribution_table("Rozkład pełnych", "rozklad_pelne",
                                              stat_all, "Statytyka: rozklad pelnych",
                                              "Stat_2.png", True, True, False)

        self.__create_stat_distribution_table("Rozkład rozbić w zbieranych", "rozklad_rozbicia",
                                              stat_all, "Statytyka: rozklad zbieranych",
                                              "Stat_3.png", False, True, False)

        self.__create_stat_distribution_table("W ilu rzutach były kończone układy", "rozklad_w_ile_uklad",
                                              stat_w_ile_uklad, "Statytyka: rozklad w ile zebrane uklady",
                                              "Stat_4.png", False, True, False)

        self.__create_stat_distribution_table("Rozkład wyników w rzutach następujących po zbiciu dzięwiątki",
                                              "rozklad_co_po_9", stat_all, "Statytyka: co po 9",
                                              "Stat_5.png", False, False, True)

    @staticmethod
    def __create_empty_image() -> np.ndarray:
        """
        Metoda tworzy i zwraca pusty obraz który będzie tłem wyników.

        return: <np.ndarray> czarny obraz o wymiarach 550x1280
        """
        img = np.full((550, 1280, 3), 255, dtype=np.uint8)
        img[:, :] = (0, 0, 0)
        return img

    def __create_stat_distribution_table(self, title_stat: str, name_stat: str, list_stat: list[list],
                                         name_window: str, name_save: str,
                                         show_sum: bool, show_mean: bool, show_the_longest_9: bool) -> None:
        """
        Metoda tworze planszę ze statystykami które zostały podane przy wywoływaniu, pokazuje i zapisuje tą planszę.

        :param title_stat: tekst który ma być zapisany w górnej części planszy
        :param name_stat: nazwa statystyki, która ma być odczytywana z self.__statistic_players
        :param list_stat: lista wartości statystyk, które mają być pokazywane u graczy
        :param name_window: nazwa okna które będzi otworzone z tą statystyką
        :param name_save: nazwa pod jaką ma być zapisywana plansza w systemie
        :param show_sum: czy ma być pokazana suma statystyk przy graczu
        :param show_mean: czy ma być pokazana średnia statystyki przy graczu
        :param show_the_longest_9: czy ma być poakzana najdłuższa seria 9 gracza
        """
        img = self.__create_empty_image()
        img = Image.fromarray(img, "RGB")

        max_number_of = self.__get_max_value_stat(name_stat, list_stat)
        img = self.draw_center_text_by_coord(img, title_stat, 20, self.__font_path, (255, 255, 255), (0, 1280, 4, 40))
        one_player_width = int(1280 / len(self.__statistic_players[0]["players"]))

        for nr_row, list_stat_players in enumerate(self.__statistic_players):
            for nr_player, stat_player in enumerate(list_stat_players["players"]):
                list_text_to_put_on_img = []
                img_player = np.full((250, one_player_width, 3), 0, dtype=np.uint8)
                list_text_to_put_on_img.append([stat_player["name"], 15, (255, 255, 0), (0, one_player_width, 4, 20)])
                number_of_all, sum_all = 0, 0
                for nr_stat, list_kind_stat, name_val in list_stat:
                    number_of = 0
                    for kind_stat in list_kind_stat:
                        number_of += stat_player[name_stat][kind_stat]
                        sum_all += kind_stat * stat_player[name_stat][kind_stat]
                    number_of_all += number_of
                    if number_of_all:
                        przyslowek = "raz" if number_of == 1 else "razy"
                        w = int((one_player_width - 16) * number_of / max_number_of)
                        img_player = cv2.rectangle(img_player, (5, 45 + nr_stat * 20 + 2),
                                                   (8 + w, 45 + nr_stat * 20 + 18),
                                                   (255, 0, 0), -1)
                        list_text_to_put_on_img.append([name_val + f" ({number_of} {przyslowek})", 13, (255, 255, 255),
                                                       (0, one_player_width, 45 + nr_stat * 20,
                                                        45 + (nr_stat + 1) * 20)])
                if number_of_all:
                    txt = self.__get_txt_main_stat(show_sum, show_mean, show_the_longest_9,
                                                   sum_all, number_of_all, stat_player["best_seria_9"])
                    list_text_to_put_on_img.append([txt, 13, (255, 255, 255), (0, one_player_width, 20, 45)])

                img_player = Image.fromarray(img_player, "RGB")
                for text, font_size, font_color, position in list_text_to_put_on_img:
                    img_player = self.draw_center_text_by_coord(img_player, text, font_size, self.__font_path,
                                                                font_color, position)

                img.paste(img_player, (nr_player * one_player_width, nr_row * 250 + 50))
        img.save(self.__path_to_save_current_stat + name_save, "PNG")
        img.save(self.__path_to_save_historical_statistics + name_save, "PNG")
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        cv2.imshow(name_window, img)
        cv2.waitKey(1)

    def __get_max_value_stat(self, name_stat: str, list_stat: list) -> int:
        """
        Metoda zwraca jaką największą pokazywana statystyka może osiągnąć.

        :param name_stat: nazwa sprawdzanej statystyki
        :param list_stat: lista z szczegółami jakie statystyki są pokazywane
        return: maksymalna wartość jaką może osiągnąć badana statystyka
        """
        max_number_of = 1
        for list_stat_players in self.__statistic_players:
            for stat_player in list_stat_players["players"]:
                for _, list_kind_stat, _ in list_stat:
                    number_of = 0
                    for kind_stat in list_kind_stat:
                        number_of += stat_player[name_stat][kind_stat]
                    if number_of > max_number_of:
                        max_number_of = number_of
        return max_number_of

    @staticmethod
    def __get_txt_main_stat(show_sum: bool, show_mean: bool, show_best_9_series: bool,
                            sum_all: int, number_of_all: int, best_9_series: int) -> str:
        """
        Metoda zwraca tekst który ma być wpisany pod nazwą gracza.

        :param show_sum: czy suma ma być pokazana
        :param show_mean: czy średnia ma być pokazana
        :param show_best_9_series: czy najdłuższa seria 9 ma być pokazana
        :param sum_all: suma gracza
        :param sum_all: suma
        :param number_of_all: w ilu rzutach była osiągnięta ta suma
        :param best_9_series: najdłuższa seria 9

        return: napis który ma być wpisany
        """
        txt = ""
        if show_sum:
            txt += f"Wynik: {sum_all}"
        if show_mean:
            if show_sum:
                txt += " | "
            txt += f"Średnia: {int(sum_all / number_of_all * 100) / 100}"
        if show_best_9_series:
            przyslowek = "rzut" if best_9_series == 1 else "rzuty"
            if show_sum or show_mean:
                txt += " | "
            txt += f'Najdłuższa seria "9":  {best_9_series} {przyslowek}'
        return txt
