"""Moduł odpowiedzialny za zapis wyników uzyskanych przez graczy w pliku csv."""

from storages_of_players_results import StorageOfAllPlayersScore, _StorageOfPlayerResults, _StorageOfAllTeamResults
from datetime import datetime
from informing import Informing


class ResultsToCsvFile:
    """Klasa odpowiedzialna za zapis wyników uzyskanych przez graczy w pliku csv"""

    def __init__(self, obj_with_results: StorageOfAllPlayersScore, path_to_dict: str = "results") -> None:
        """
        Metoda zapisuje uzyskane wyniki w pliku CSV.

        :param obj_with_results: obiekt zawierający wyniki wszystkich graczy
        :param path_to_dict: ścieżka ado katalogu gdzie ma ybć zapisany plik CSV z wynikami graczy

        __path_to_dict: ścieżka ado katalogu gdzie ma ybć zapisany plik CSV z wynikami graczy
        __obj_with_results: obiekt zawierający wyniki wszystkich graczy
        """
        self.__path_to_dict = path_to_dict
        self.__obj_with_results = obj_with_results

    def save_league_results_to_csv_file(self) -> bool:
        """
        Metoda zapisuje wyniki graczy w pliku w o nazwie "results_<aktualna_data>" w katalogu self.__path_to_dict.

        :return: True - udało się zapisać, False - wystąpił błąd
        """
        text = self.__get_two_team_head_txt() + self.__get_results_player() + self.__get_red_cards()
        return self.__save_txt_to_csv_file(text)

    def __get_two_team_head_txt(self) -> str:
        """
        Moduł odpowiedzialny za zwrócenie textu do pliku csv z głównymi informacjami o meczu ligowym.

        :return: str z informacjami jakie zespoły grały, kiedy i ilu było zawodników w drużynie
        """
        if self.__obj_with_results.number_of_teams != 2:
            return ""
        name_home_team = self.__obj_with_results.teams[0].team_results.name
        name_guest_team = self.__obj_with_results.teams[1].team_results.name
        date = datetime.now().strftime("%d.%m.%y")
        number_of_player_in_team = self.__obj_with_results.number_of_players_in_team

        head_data = "Szczegóły:\n-----\nGospodarz, Gość, Data, Liczba graczy w drużynie\n"
        head_data += f"{name_home_team}, {name_guest_team}, {date}, {number_of_player_in_team}\n------\n"
        return head_data

    def __get_results_player(self) -> str:
        """
        Moduł odpowiedzialny za zwrócenie textu do pliku csv z wynikami zawodników.

        :return: str z informacjami kto jakie miał wyniki w poszczególnych rzutach, jeżeli była zmiana, to przy
                zawodniku zapisywane są tylko jego rezultaty, a reszta jest pusta
        """
        text = "Wyniki\n-------\nName, Team_index, Player_index"
        for i in range(1, 121):
            text += f", rzut_{i}"
        text += "\n"
        for nr_team, team in enumerate(self.__obj_with_results.teams):
            for nr_player_in_team, player in enumerate(team.players_results):
                list_throw_start = player.list_when_changes
                list_throw_end = list_throw_start[1:]
                list_throw_end.append(120)
                list_results = player.get_list_suma()
                for nr_player_change, [throw_start, throw_end] in enumerate(zip(list_throw_start, list_throw_end)):
                    text += f"{player.list_name[nr_player_change]}, {nr_team}, {nr_player_in_team},"
                    for _ in range(0, throw_start):
                        text += ","
                    for i in range(throw_start, throw_end):
                        text += f"{list_results[i]},"
                    for _ in range(throw_end, 120):
                        text += ","
                    text += "\n"
        text += "--------\n"
        return text

    def __get_red_cards(self) -> str:
        """
        Moduł odpowiedzialny za zwrócenie textu do pliku csv z informacjami o czerwonych kartkach.

        :return: str z informacjami kto, kiedy  dostał czerwoną kartkę i ile zbił w tamtym rzucie kręgli
        """
        text = "Czerwone kartki\n---------\nTeam_index, Player_index, Rzut, Niezaliczony rezultat\n"
        for nr_team, team in enumerate(self.__obj_with_results.teams):
            for nr_player_in_team, player in enumerate(team.players_results):
                for [nr_throw, unrecognized_result] in player.list_red_cards:
                    text += f"{nr_team}, {nr_player_in_team}, {nr_throw}, {unrecognized_result}\n"
        text += "----------\n"
        return text

    def __save_txt_to_csv_file(self, text_to_save: str) -> bool:
        """
        Metoda zapisuje przekazany ciąg znaków do pliku csv.

        :param text_to_save: ciąg znaków który ma być zapisany w pliku CSV
        :return: True - udało się zapisać, False - wystąpił błąd
        """
        file_name = f"{self.__path_to_dict}/results_" + datetime.now().strftime("%y_%m_%d__%H_%M_%S") + ".csv"
        try:
            f = open(file_name, "w")
            f.write(text_to_save)
            f.close()
            return True
        except OSError:
            Informing().error(f"Nie można zapisać pliku z wynikami do: {file_name}")
            return False
