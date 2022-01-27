"""Moduł do tworzenia podstawowych tabel z wynikami. (Do wizualizacji wyników)"""

import copy
import numpy as np
import cv2
import json
import logging
import logging_config
from PIL import Image
from storages_of_players_results import StorageOfAllPlayersScore, _StorageOfPlayerResults
import methods_to_draw_on_image


class _CreatingMainTableDrawResults(methods_to_draw_on_image.MethodsToDrawOnImage):
    """
    Klasa odpowiedzialna za tworzenie głównej tabeli z wynikami.

    make_table() -> None : tworzy i wyświetla tabelę
    set_obj_with_results(StorageOfAllPlayersScore) -> None : uaktualnienie obiektu przechowującego wyniki
    """
    def __init__(self, obj_with_results: StorageOfAllPlayersScore | None, table_settings: dict | None) -> None:
        """
        :param obj_with_results: obiekt z wynikami graczy i drużyn
        :param table_settings: odczytany z json dane w jaki sposób ma być uzupełniona tabela

        __obj_with_results: obiekt z wynikami graczy i drużyn
        __table_settings: odczytany z json dane w jaki sposób ma być uzupełniona tabela
        __clear_image: czysty obraz tabeli
        __finished_image: obraz tabeli do wyświetlenia
        __saved_data: zawiera informacje jakie dane są zapisane na __finished_image
        """
        super().__init__()
        self.__obj_with_results: StorageOfAllPlayersScore | None = obj_with_results
        self.__table_settings: dict | None = table_settings
        if table_settings is None:
            return
        clear_image = cv2.imread(self.__table_settings["path_to_table"])
        if clear_image is None:
            logging.warning(f"Nie można otworzyć obrazu {self.__table_settings['path_to_table']}")
            self.__table_settings = None
            return
        self.__clear_image: Image.Image = Image.fromarray(clear_image)
        self.__finished_image: Image.Image = Image.fromarray(clear_image)
        self.__saved_data: dict = {"players": {}, "teams": {}}
        self.__draw_subtitles()

    def make_table(self) -> None:
        """
        Metoda odpowiedzialna za stworzenie i wyświetlenie tabeli z aktualnymi danymi.
        """
        if self.__obj_with_results is None or self.__table_settings is None:
            return
        self.__draw_players_results()
        self.__draw_team_results()
        cv2.imshow("KL_main_table", np.array(self.__finished_image))
        cv2.waitKey(1)

    def set_obj_with_results(self, obj_with_results: StorageOfAllPlayersScore) -> None:
        """
        Metoda do uaktualnienia obiektu przechowującego wyniki.

        :param obj_with_results: nowy obiekt przechowujący wyniki
        """
        self.__obj_with_results = obj_with_results

    def __draw_players_results(self) -> None:
        """Metoda wypisuje aktualne wyniki graczy, tylko te które uległy zmianie."""
        main_players_settings = self.__table_settings["players"]["settings"]
        main_players_settings = self.__get_settings(self.__table_settings["settings"], main_players_settings)

        for player_details in self.__table_settings["players"]["players"]:
            player_settings = self.__get_settings(main_players_settings, player_details["settings"])

            index_team, index_player = player_details["index_team"], player_details["index_player_in_team"]
            saved_data = {}
            player_id = str(index_team) + "|" + str(index_player)
            if player_id in self.__saved_data["players"].keys():
                saved_data = self.__saved_data["players"][player_id]

            for name_result, settings in player_details["cell"].items():
                result = self.__obj_with_results.get_data_from_player(index_team, index_player, name_result)
                if name_result in saved_data.keys() and result == saved_data[name_result]:
                    continue
                else:
                    saved_data[name_result] = result
                settings = self.__get_settings(player_settings, settings)
                self.__draw_text(result, settings)
            self.__saved_data["players"][player_id] = saved_data

    def __draw_team_results(self) -> None:
        """Metoda wypisuje aktualne wyniki drużyn."""
        main_teams_settings = self.__table_settings["teams"]["settings"]
        main_teams_settings = self.__get_settings(self.__table_settings["settings"], main_teams_settings)

        for team_details in self.__table_settings["teams"]["teams"]:
            team_settings = self.__get_settings(main_teams_settings, team_details["settings"])
            index_team = team_details["index_team"]

            saved_data = {}
            if index_team in self.__saved_data["teams"].keys():
                saved_data = self.__saved_data["teams"][index_team]

            for name_result, settings in team_details["cell"].items():
                result = self.__obj_with_results.get_data_from_team(index_team, name_result)
                if name_result in saved_data.keys() and result == saved_data[name_result]:
                    continue
                else:
                    saved_data[name_result] = result
                settings = self.__get_settings(team_settings, settings)
                self.__draw_text(result, settings)

            self.__saved_data["teams"][index_team] = saved_data

    def __draw_subtitles(self) -> None:
        """Metoda wypisuje napisy ktore zostały zapisane do wypisania w pliku json."""
        subtitles_settings = self.__table_settings["subtitles"]["settings"]
        subtitles_settings = self.__get_settings(self.__table_settings["settings"], subtitles_settings)
        for details in self.__table_settings["subtitles"]["cell"]:
            settings = self.__get_settings(subtitles_settings, details)
            self.__draw_text(details["text"], settings)

    def __draw_text(self, text: str, settings: dict) -> None:
        """
        Metoda aktualizuje napis w komórce.

        Metoda wycina komórkę z czystego obrazu, zapisuje w niej tekst i wkleja do wynikowego obrazu.
        :param text: tekst do wpisania
        :param settings: ustawiania czcionki, rozmiaru komórki
        """
        font_size, font_path = settings["max_font_size"], settings["font_path"]
        font_color = settings["font_color"]
        left, top, width, height = settings["left"], settings["top"], settings["width"], settings["height"]

        cell = self.__clear_image.crop((left, top, left + width, top + height))
        cell = self.draw_center_text_in_cell(cell, text, font_size, font_path, font_color, width, height)
        self.__finished_image.paste(cell, (left, top))

    @staticmethod
    def __get_settings(main_default_values: dict, new_default_values: dict) -> dict:
        """
        Metoda zwraca zaaktualizowany słownik z ustawieniami.

        Zapisuje z głównych ustawieniach te ustawiania które są w new_default_values i zwraca słownik.

        :param main_default_values: słownik z wszystkimi ustawianiami (niżej w hierarchi ważności)
        :param new_default_values: słownik ze zmienami w ustawieniach (ważniejszy w hierarchii)
        :return: zmodyfikowany słownik main_default_values o wartości z new_default_values
        """
        values = copy.deepcopy(main_default_values)
        for key, value in new_default_values.items():
            if key in values.keys():
                values[key] = value
        return values


class CreatingMainTable:
    """
    Główna klasa odpowiedzialna za tworzenie tablicy z wynikami.

    set_obj_to_storages_of_players_results(StorageOfAllPlayersScore) -> None - ustawienie nowego obiektu z wynikami
    set_table_settings(str) -> None - pobranie nowego pliku json z ustawieniami tabli
    make_table() -> None - tworzy i wyświetla tabelę
    """

    def __init__(self, path_to_table_settings: str, obj_with_results: StorageOfAllPlayersScore | None = None):
        """
        :param path_to_table_settings: ścieżka do ustawień tabeli
        :param obj_with_results: obiekt z wynikami

        __table_settings: ustawienia tabeli lub None jaknie podano ścieżki
        __obj_to_storage_results: obeikt z wynikami graczy i drużyn lub None
        __obj_to_create_table: oniekt do tworzenia tabeli
        """
        self.__table_settings: dict | None = self.__get_table_settings(path_to_table_settings)
        self.__obj_to_storage_results: None | StorageOfAllPlayersScore = obj_with_results
        self.__obj_to_create_table = _CreatingMainTableDrawResults(self.__obj_to_storage_results, self.__table_settings)

    @staticmethod
    def __get_table_settings(path_to_table_settings: str) -> dict | None:
        """
        Metoda do pobrania słownika z pliku json lub zwrócenia None jak nie podano ścieżki.

        :param path_to_table_settings: ścieżka do pliku json
        """
        if path_to_table_settings == "":
            return None
        try:
            file = open(path_to_table_settings, encoding='utf8')
            return json.load(file)
        except FileNotFoundError:
            logging.warning(f"Nie można odczytać ustawień tabeli z pliku {path_to_table_settings}")
            return None

    def set_obj_to_storages_of_players_results(self, obj_with_results: StorageOfAllPlayersScore) -> None:
        """
        Metoda aktualizuje obiekt z przechowujący wyniki graczy i drużyn.

        :param obj_with_results: nowy obiekt z wynikami
        """
        self.__obj_to_storage_results = obj_with_results
        self.__obj_to_create_table.set_obj_with_results(obj_with_results)

    def set_table_settings(self, path_to_table_settings: str) -> None:
        """
        Metoda aktualizuje ustawienia tabeli.

        :param path_to_table_settings: ścieżka do nowego pliku json z ustawieniami tabei
        """
        self.__table_settings = self.__get_table_settings(path_to_table_settings)
        self.__obj_to_create_table = _CreatingMainTableDrawResults(self.__obj_to_storage_results, self.__table_settings)

    def make_table(self) -> None:
        """Metoda tworzy tabelę z wynikami, wypełnia ją rezultatami osiagniętymi przez graczy i wyświetla ją."""
        self.__obj_to_create_table.make_table()
