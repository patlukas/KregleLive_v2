"""Moduł do tworzenia podstawowych tabel z wynikami. (Do wizualizacji wyników)"""

import copy
import numpy as np
import cv2
import json
from storages_of_players_results import StorageOfAllPlayersScore, _StorageOfPlayerResults
from PIL import ImageFont, ImageDraw, Image, ImageTk


class _MainMethodsToCreateTable:
    """
    Klasa z głównymi metodami do tworzenia tabel.

    draw_center_text_in_cell(Image.Image, str|int|float, int, str, tuple|list, int, int) -> Image.Image - zwraca obraz
                                                                                        komórki z wyśrodkowanym napisem
    """
    def __init__(self):
        """
        __used_fonts - {<path_font>: {<size_font>: <object font PIL>}} - słownik z załadowanymi już czcionkami
        __get_font(str, int) -> PIL.ImageFont.FreeTypeFont - zwraca potrzebną czcionkę
        """
        self.__used_fonts: dict = {}

    def __get_font(self, font_path: str, font_size: int) -> ImageFont.FreeTypeFont:
        """
        Metoda odpowiedzialna za zwrócenie potrzebnej czcionki.

        Jeżeli potrzebna czcionka nie była jeszcze używana to pobranie jej i zapisanie w __used_fonts, a jak już była
        używana to zwrócenie czcionki z __used_fonts.

        :param font_path: ścieżka do czcionki
        :param font_size: rozmiar czcionki
        :return: obiekt czcionki
        """
        if font_path in self.__used_fonts and font_size in self.__used_fonts[font_path]:
            return self.__used_fonts[font_path][font_size]
        else:
            font = ImageFont.truetype(font_path, font_size)
            if font_path not in self.__used_fonts:
                self.__used_fonts[font_path] = {}
            self.__used_fonts[font_path][font_size] = font
            return font

    def draw_center_text_in_cell(self, img_cell: Image.Image, text: str | int | float, font_size: int,
                                 font_path: str, color: tuple | list, width: int, height: int) -> Image.Image:
        """
        Zwraca obraz komórki z dodanym wyśrodkowanym w pionie i poziomi napisem.

        :param img_cell: obraz komórki
        :param text: napis który ma być dodany
        :param font_size: maksymalny rozmiar czcionki, jak się nie zmieści napis to rozmiar zostanie zmniejszony
        :param font_path: ścieżka do czcionki
        :param color: kolor czcionki zapisany w postaci (B, G, R)
        :param width: szerokość komórki
        :param height: wysokość komórki
        :return: komórka z dodanym wyśrodkowanym napisem
        """
        if type(text) != str:
            text = str(text)
        if text == "":
            return img_cell
        if type(color) == list:
            color = tuple(color)
        if type(font_size) != int:
            font_size = int(font_size)

        draw = ImageDraw.Draw(img_cell)
        while True:
            font = self.__get_font(font_path, font_size)
            w, h = draw.textsize(text, font=font)
            if w <= width and h <= height:
                break
            font_size -= 1
            if font_size <= 0:
                break
        x = (width - w) // 2
        y = (height - h) // 2
        draw.text((x, y), text, font=font, fill=color)
        return img_cell


class _CreatingMainTableDrawResults(_MainMethodsToCreateTable):
    """
    Klasa odpowiedzialna za tworzenie głównej tabeli z wynikami.

    make_table() -> None : tworzy i wyświetla tabelę
    set_obj_with_results(StorageOfAllPlayersScore) -> None : uaktualnienie obiektu przechowującego wyniki
    """
    def __init__(self, obj_with_results: StorageOfAllPlayersScore, table_settings: dict | None) -> None:
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
        self.__obj_with_results: StorageOfAllPlayersScore = obj_with_results
        self.__table_settings: dict | None = table_settings
        clear_image = cv2.imread(self.__table_settings["path_to_table"])
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
                result = self.__get_result_player(index_team, index_player, name_result)
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
                result = self.__get_result_team(index_team, name_result)
                if name_result in saved_data.keys() and result == saved_data[name_result]:
                    continue
                else:
                    saved_data[name_result] = result
                settings = self.__get_settings(team_settings, settings)
                self.__draw_text(result, settings)

            self.__saved_data["teams"][index_team] = saved_data

    def __draw_subtitles(self) -> None:
        """Metoda wypisuje napisy ktore zostały zapisane do wypisania w pliku json."""
        subtitles_settings = self.__table_settings["teams"]["settings"]
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

    def __get_result_player(self, index_team: int, index_player: int, name_result: str) -> str:
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
                        number_of_rzut, pelne, zbierane, dziur, suma, PS
                    - zaminiast Z (jak nie spełnione to ""):
                        - win - gracz wygrywa/wygrał tor
                        - draw - gracz remisuje/zremisował tor
                        - lose - gracz przegrywa/przegrał tor
            4. Inna nazwa statystyki wtedy ""
        """
        player_results = self.__obj_with_results.teams[index_team].players_results[index_player]
        player_lanes_results = player_results.result_tory
        if name_result == "name":
            return player_results.get_all_name_to_string()
        try:
            if name_result[:3] == "tor":
                index_tor = int(name_result[3]) - 1
                list_word = name_result.split("_")
                kind = list_word[1]
                if player_lanes_results[index_tor].number_of_rzut == 0:
                    return ""
                if len(list_word) == 2:
                    return player_lanes_results[index_tor].__getattribute__(kind)
                if player_lanes_results[index_tor].PS == {"win": 1, "draw": 0.5, "lose": 0}[list_word[2]]:
                    return player_lanes_results[index_tor].__getattribute__(kind)
                return ""
            if player_results.result_main.number_of_rzut == 0:
                return ""
            return player_results.result_main.__getattribute__(name_result)
        except AttributeError:
            return ""

    def __get_result_team(self, index_team: int, name_result: str) -> str:
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
        team_results = self.__obj_with_results.teams[index_team].team_results
        if name_result == "sum_difference_non_negative":
            if team_results.sum_difference >= 0:
                return team_results.sum_difference
            else:
                return ""
        if name_result == "sum_difference_positive":
            if team_results.sum_difference > 0:
                return team_results.sum_difference
            else:
                return ""
        if name_result == "sum_difference_negative":
            if team_results.sum_difference < 0:
                return team_results.sum_difference
            else:
                return ""
        try:
            return team_results.__getattribute__(name_result)
        except AttributeError:
            return ""


class CreatingMainTable:
    """
    Główna klasa odpowiedzialna za tworzenie tablicy z wynikami.

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
        file = open(path_to_table_settings, encoding='utf8')
        return json.load(file)

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
