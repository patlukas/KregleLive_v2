"""Moduł odpowiedzialny za zarządzanie licencjami graczy."""
import json
import gspread
import logging
import logging_config


class GetLicenses:
    """
    Klasa odpowiedzialna za zarządzanie licencjami.

    get_list_team(list[str], str) -> list[str] - metoda zwraca listę drużyn, w których są gracze spełniający warunki
    get_list_player_in_team(list[str], str, str) -> list[str] - metoda zwraca listę graczy spełniających warunki
    """
    def __init__(self, path_to_json: str, path_config_spreadsheets: str):
        """
        self.__settings - słownik z ustawieniami plików z licencjami (pobierany z json)
        self.__licenses_data - lista słowników z danymi graczy, każdy element listy jest następująy:
                                {
                                "name": <str: nazwa gracza>,
                                "team": <str: nazwa rodzimego klubu>,
                                "category": <str: nazwa kategorii, np Junior, Seniorka, ...>
                                <str: na jakie rozgrywki wypożyczony, np superliga kobiet>: <str: dzie wypożyczony>
                                }
                            Jeżeli __licenses_data jest None to znaczy że nie udało się pobrać danych graczy.
        """
        self.__settings: dict = self.__get_settings_from_json(path_to_json)
        self.__licenses_data: list[dict] | None = self.__get_data_from_google_sheet(path_config_spreadsheets)

    @staticmethod
    def __get_settings_from_json(path_to_json: str) -> dict | None:
        """
        Metoda pobiera ustawienia dotyczące pliku z licencjami.

        :param path_to_json: ścieżka do pliku json z ustawieniami
        :return: słownik z ustawieniami jak udało się pobrać, lub None w przypadku problemu
        """
        try:
            file = open(path_to_json, encoding='utf8')
            return json.load(file)
        except FileNotFoundError:
            logging.warning(f"Nie można odczytać ustawień licencji z pliku {path_settings_worksheet}")
            return None

    def __get_data_from_google_sheet(self, path_config_spreadsheets: str) -> list[dict] | None:
        """
        Metoda odczytuje dane licencje graczy z arkusza Google.

        :param path_config_spreadsheets: ścieżka do pliku json z konfiguracją klienta
        :return: lista słowników z danymi graczy lub None jak nie udało się odczytać
        """
        client: gspread.client.Client | None = self.__get_gspread_client(path_config_spreadsheets)
        if client is None or self.__settings is None:
            return None
        try:
            spreadsheet = client.open_by_url(self.__settings["google_sheet"]["path"])
            worksheet = spreadsheet.sheet1
            rows = worksheet.get_all_values()
            settings = self.__settings["google_sheet"]
            players = []
            for row in rows:
                if row[settings["valid_license_column"]] not in settings["license_is_valid_when_there_is_text"]:
                    continue
                player = {
                    "name": row[settings["name_column"]],
                    "team": row[settings["team_column"]],
                    "category": row[settings["category_column"]],
                }
                if row[settings["loan_for_what_column"]] != "":
                    player[row[settings["loan_for_what_column"]].lower()] = row[settings["where_loaned_column"]]
                players.append(player)
            return players
        except (
                gspread.exceptions.NoValidUrlKeyFound,
                gspread.exceptions.APIError,
                gspread.exceptions.WorksheetNotFound
        ):
            return None

    @staticmethod
    def __get_gspread_client(path_config_spreadsheets: str) -> gspread.Client | None:
        """
        Metoda próbuje pobrać ustawienia klienta połączenia i stworzyć jego obiekt, inaczej None

        :param path_config_spreadsheets: ścieżka do json z konfiguracją klienta
        :return: obiekt klienta - jak udało się połączć, None jak połączenie się nie udało
        """
        try:
            return gspread.service_account(filename=path_config_spreadsheets)
        except FileNotFoundError:
            logging.warning(f"Nie znaleziono pliku z konfiguracją klienta {path_config_spreadsheets}")
            return None

    def get_list_team(self, list_category: list, type_of_game: str = "") -> list[str]:
        """
        Metoda zwraca drużyn zawierających graczy (przynajmniej 1 gracza), którzy spełniają podane wymagania.

        :param list_category: lista kategorii, np ["Młodzik", "Senior", "Junior"]
        :param type_of_game: nazwa typu gry, np "superliga mężczyzn", jest to istotne w przypadku wypożyczeń.
                             Jeżeli nie zostanie podany napis to będą brane tylko pod uwagę kluby maicerzyste.
        :return: Lista drużyn. Pod 0 indexem jest pusty ciąg znaków
        """
        if self.__licenses_data is None:
            return [""]
        teams = {"": 1}
        for player in self.__licenses_data:
            if player["category"] not in list_category:
                continue
            team = player.get(type_of_game.lower(), player["team"])
            teams[team] = 1
        teams_list = [*teams]
        teams_list.sort()
        return teams_list

    def get_list_player_in_team(self, list_category: list[str], name_team: str, type_of_game: str = "") -> list[str]:
        """
        Metoda zwraca listę graczy należących spełniających podane wymagania.

        :param list_category: lista kategorii, gracz musi należeć do którejś z nich
        :param name_team: nazwa drużyny lub "". Jak "" to waunek pomiajny, jak nie to musi to być jego macierzysty klub
                          lub to musi być jego klub do którego został wypożyczony
        :param type_of_game: jeżeli gracz jest wypożyczony na te rozgrywki to musi, być wypożyczony do drużyny name_team
                             wtedy nie uwzględnia się macierzystego klubu
        :return: lista graczy. Pod 0 indexem jest pusty napis.
        """
        if self.__licenses_data is None:
            return [""]
        players = [""]
        for player in self.__licenses_data:
            if player["category"] not in list_category:
                continue
            if name_team != "" and player.get(type_of_game.lower(), player["team"]) != name_team:
                continue
            players.append(player["name"])
        players.sort()
        return players

