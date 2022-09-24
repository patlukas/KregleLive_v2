"""Moduł odpowiedzialny za zarządzanie rodzajami gry możliwymi do wyboru oraz ich szczegółami, np. Liga 6-osobowa."""

import json
from informing import Informing
from storages_of_players_results import StorageOfAllPlayersScore
from get_licenses import GetLicenses


class GameTypeManagement:
    """
    Klasa do zarządzania rodzajami gier do wyboru, np. liga 6-osobowa oraz klasa daje możliwość wyboru rodzaju.

    list_game_types - list<dict> - każdy element to szczegóły dotyczące jednego rodzaju gry
    list_name_of_game_types - list<str> - lista nazw rodzajów gry
    selected_game_type - dict z szczegółami wybranego rodzaju gry, ten dict jest wybrany z list_game_types
    name_of_the_selected_game_type - str - nazwa wybranego rodzaju gry

    choose_game_type(str) -> None - pozwala na zmienienie wybranego rodzaju gry poprzez podanie jego nazwy
    """
    def __init__(self, path_to_json_with_game_types: str, obj_to_storages_of_players_results: StorageOfAllPlayersScore,
                 obj_to_get_licenses: GetLicenses):
        """
        :param path_to_json_with_game_types - ścieżka do pliku json z rodzajami gier do wyboru oraz ich ustawieniami
        :param obj_to_storages_of_players_results - obiekt przechowujący wyniki graczy
        :param obj_to_get_licenses - obiekt przechowujący odczytane licencje

        __obj_to_storages_of_players_results - obiekt przechowujący wyniki graczy
        __obj_to_get_licenses - obiekt przechowujący odczytane licencje
        list_game_types - list<dict> - każdy element to szczegóły dotyczące jednego rodzaju gry
        list_name_of_game_types - list<str> - lista nazw rodzajów gry
        selected_game_type - dict z szczegółami wybranego rodzaju gry, ten dict jest wybrany z list_game_types
        name_of_the_selected_game_type - str - nazwa wybranego rodzaju gry
        """
        self.__obj_to_storages_of_players_results: StorageOfAllPlayersScore = obj_to_storages_of_players_results
        self.__obj_to_get_licenses: GetLicenses = obj_to_get_licenses
        self.selected_game_type: dict = {}
        self.name_of_the_selected_game_type: str = ""
        self.list_game_types: dict = {}
        self.list_name_of_game_types: list[str] = []
        self.__get_game_types(path_to_json_with_game_types)

    def __get_game_types(self, path_to_json: str) -> None:
        """
        Metoda pobiera rodzaje gier oraz ich ustawienia z json
        i zapisuje je w list_game_types oraz ich nazwy w list_name_of_game_types.

        :param path_to_json - ścieżka do pliku json z zapisanymi rodzajami gier
        """
        try:
            file = open(path_to_json, encoding='utf8')
            self.list_game_types = json.load(file)
            self.list_name_of_game_types = [*self.list_game_types.keys()]
            if len(self.list_name_of_game_types):
                self.choose_game_type(self.list_name_of_game_types[0])
        except FileNotFoundError:
            Informing().error(f"Nie można odczytać typów gier z pliku {path_to_json}")

    def choose_game_type(self, name_type: str) -> None:
        """
        Metoda umożliwia wybranie rodzaju gry przez podanie jego nazwy.

        Metoda zmiani wybrany rodzaj gry i modyfikuje ustawienia w
        obiekcie z licencami (dopuszczalne kategorie i nazwę rodzaju gry)
        i obiekcie z wynikami graczy (liczba drużyn i liczba graczy w drużynie).

        :param name_type - nazwa nowo wybranego rodzaju gry który ma być wybrany
        """
        self.selected_game_type = self.list_game_types.get(name_type, {})
        self.name_of_the_selected_game_type = name_type
        number_of_team = self.selected_game_type.get("number_of_team", 1)
        number_of_player_in_team = self.selected_game_type.get("number_of_player_in_team", 1)
        self.__obj_to_storages_of_players_results.on_data_initialization(number_of_team, number_of_player_in_team)
        list_category = self.selected_game_type.get("list_category", [])
        name_of_game = self.selected_game_type.get("name_of_game", "")
        self.__obj_to_get_licenses.set_list_category_and_name_of_game(list_category, name_of_game)
