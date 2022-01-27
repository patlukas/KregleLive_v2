"""Moduł do tworzenia paska z tabelami z wynikami na bieżących torach."""

import copy
import numpy as np
import cv2
import json
import logging
import logging_config
from PIL import Image, ImageDraw
from storages_of_players_results import StorageOfAllPlayersScore, _StorageOfPlayerResults
import methods_to_draw_on_image


class _CreatingLaneTableDrawResults(methods_to_draw_on_image.MethodsToDrawOnImage):
    """
    Klasa odpowiedzialna za tworzenie obrazu z tabelami z wynikami poszczególnych rzutów i z wynikami na torze.

    make_table() -> None : tworzy i wyświetla tabelę
    set_obj_with_results(StorageOfAllPlayersScore) -> None : uaktualnienie obiektu przechowującego wyniki
    """
    def __init__(self, obj_with_results: StorageOfAllPlayersScore | None, table_settings: dict | None) -> None:
        """
        :param obj_with_results: obiekt z wynikami graczy i drużyn
        :param table_settings: odczytany z json dane w jaki sposób ma być uzupełniona tabela

        __obj_with_results: obiekt z wynikami graczy i drużyn
        __table_settings: odczytany z json dane w jaki sposób ma być uzupełniona tabela
        __clear_image: czysty obraz tabeli pojedyńczego toru
        __finished_image: obraz tabeli do wyświetlenia (nie pojdyńczego toru, ale wszystkie x tabel)
        __saved_data: zawiera informacje jakie dane są zapisane na __finished_image

            Struktura słownika __saved_data:
            {
                <numer_toru: int>: {
                    "table": Image.Image - aktualnie wyświetlana tabela danego toru,
                    "data": {<nazwa_statystyki: str>: wypisana wartość: str}
                }
            }
        """
        super().__init__()
        self.__obj_with_results: StorageOfAllPlayersScore | None = obj_with_results
        self.__table_settings: dict | None = table_settings
        if table_settings is None:
            return
        clear_table = cv2.imread(self.__table_settings["path_to_table"])
        if clear_table is None:
            logging.warning(f"Nie można otworzyć obrazu {self.__table_settings['path_to_table']}")
            self.__table_settings = None
            return
        self.__clear_image: Image.Image = Image.fromarray(clear_table)
        self.__finished_image: Image.Image = self.__crete_empty_image()
        self.__saved_data: dict = {}

    def __crete_empty_image(self) -> Image.Image:
        """
        Metoda jest odpowiedzialna za stworzenie pustego płótna do przechowywania tabel z wynikami.

        :return: jednokolorowy obraz o wymiarach i kolorze określony w json (szablon do wklejania tabel)
        """
        width, height = self.__table_settings["width"], self.__table_settings["height"]
        background_color = self.__table_settings["background_color"]
        if type(background_color) == list:
            background_color = tuple(background_color)
        return Image.new("RGB", (width, height), background_color)

    def __get_dict_players_now_playing(self) -> dict:
        """
        Metoda do zwrócenia słownika z obiektami wynikowymi graczy, którzy aktualnie grają.

        :return: {nr_toru<int>: obiekt_z_wynikami_gracza<_StorageOfPlayerResults>, ...}
        """
        dict_players = {}
        for teams in self.__obj_with_results.teams:
            for player in teams.players_results:
                if player.tor_number is not None:
                    dict_players[player.tor_number] = player
        return dict_players

    def make_table(self) -> None:
        """
        Metoda odpowiedzialna za stworzenie i wyświetlenie tabeli z aktualnymi danymi.
        """
        if self.__obj_with_results is None or self.__table_settings is None:
            return
        dict_players_now_playing = self.__get_dict_players_now_playing()
        self.__draw_players_results(dict_players_now_playing)
        cv2.imshow("KL_lane_table", np.array(self.__finished_image))
        cv2.waitKey(1)

    def set_obj_with_results(self, obj_with_results: StorageOfAllPlayersScore) -> None:
        """
        Metoda do uaktualnienia obiektu przechowującego wyniki.

        :param obj_with_results: nowy obiekt przechowujący wyniki
        """
        self.__obj_with_results = obj_with_results

    def __draw_players_results(self, dict_players_now_playing: dict) -> None:
        """
        Metoda wypisuje aktualne wyniki graczy, aktualizuje tylko te komórki gdzie wystąpiła zmiana.

        :param dict_players_now_playing: słownik w którym ma indexy int licząc od 1 i jeżeli istanieje index to
                                        oznacza że na danym torze ktoś gra i pod tym indexem jest obiekt z jego wynikami


        Uwagi: Podczas pobierania wyniku gracza jest zamianiany X na numer bieżącego toru, ponieważ w json jest wpisane
                torX_rzut1 lub torX_suma, aby w prosty sposób można było odczytać aktualny wynik
        """
        for nr_lane, coords in self.__table_settings["table_coords"].items():
            nr_lane = int(nr_lane)
            saved_data: dict | None = self.__saved_data.get(nr_lane, None)
            player_obj_with_result: _StorageOfPlayerResults | None = dict_players_now_playing.get(nr_lane, None)
            if player_obj_with_result is None:
                if saved_data is not None:
                    self.__saved_data[nr_lane] = None
                    empty_img = Image.new("RGB", self.__clear_image.size,
                                          tuple(self.__table_settings["background_color"]))
                    self.__finished_image.paste(empty_img, (coords["left"], coords["top"]))
                continue
            if saved_data is None:
                saved_data = {
                    "table": copy.copy(self.__clear_image),
                    "data": {},
                }
            number_of_tor = str(player_obj_with_result.number_of_tor + 1)
            settings = self.__table_settings["cell_in_table"]["settings"]
            for name_result, new_settings in self.__table_settings["cell_in_table"]["cell"].items():
                settings = self.__get_settings(settings, new_settings)
                result = player_obj_with_result.get_data(name_result.replace("X", number_of_tor))
                saved_value = saved_data["data"].get(name_result, "")
                if result != saved_value:
                    saved_data["data"][name_result] = result
                    saved_data["table"] = self.__draw_text(saved_data["table"], result, settings)
            self.__saved_data[nr_lane] = saved_data
            self.__finished_image.paste(saved_data["table"], (coords["left"], coords["top"]))

    def __draw_text(self, img: Image.Image, text: str, settings: dict) -> Image.Image:
        """
        Metoda aktualizuje napis w komórce.

        Metoda wycina komórkę z czystego obrazu, zapisuje w niej tekst i wkleja do wynikowego obrazu.
        :param img: obraz tabeli gdzie ma być dodany tekst
        :param text: tekst do wpisania
        :param settings: ustawiania czcionki, rozmiaru komórki
        """
        img = copy.copy(img)
        font_size, font_path = settings["max_font_size"], settings["font_path"]
        font_color = settings["font_color"]
        left, top, width, height = settings["left"], settings["top"], settings["width"], settings["height"]

        cell = self.__clear_image.crop((left, top, left + width, top + height))
        cell = self.draw_center_text_in_cell(cell, text, font_size, font_path, font_color, width, height)
        img.paste(cell, (left, top))
        return img

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


class CreatingLaneTable:
    """
    Główna klasa odpowiedzialna za tworzenie tablicy z wynikami na poszczególnych torach.

    set_obj_to_storages_of_players_results(StorageOfAllPlayersScore) -> None - ustawienie nowego obiektu z wynikami
    set_table_settings(str) -> None - pobranie nowego pliku json z ustawieniami tabli
    make_table() -> None - tworzy i wyświetla tabelę
    """

    def __init__(self, path_to_table_settings: str, obj_with_results: StorageOfAllPlayersScore | None = None):
        """
        :param path_to_table_settings: ścieżka do ustawień tabeli
        :param obj_with_results: obiekt z wynikami

        __table_settings: ustawienia tabeli lub None jak nie podano ścieżki
        __obj_to_storage_results: obeikt z wynikami graczy i drużyn lub None
        __obj_to_create_table: obiekt do tworzenia tabeli
        """
        self.__table_settings: dict | None = self.__get_table_settings(path_to_table_settings)
        self.__obj_to_storage_results: None | StorageOfAllPlayersScore = obj_with_results
        self.__obj_to_create_table = _CreatingLaneTableDrawResults(self.__obj_to_storage_results, self.__table_settings)

    @staticmethod
    def __get_table_settings(path_to_table_settings: str) -> dict | None:
        """
        Metoda do pobrania słownika z pliku json lub zwrócenia None jak nie podano ścieżki.

        :param path_to_table_settings: ścieżka do pliku json
        :return: dict z json jak podano ścieżkę, w innym przypadku (podano błędną ścieżkę lub "") None
        """
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
        self.__obj_to_create_table = _CreatingLaneTableDrawResults(self.__obj_to_storage_results, self.__table_settings)

    def make_table(self) -> None:
        """Metoda tworzy tabelę z wynikami, wypełnia ją rezultatami osiagniętymi przez graczy i wyświetla ją."""
        self.__obj_to_create_table.make_table()
