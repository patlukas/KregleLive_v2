"""Moduł odpowiedzialny za zapis wyników uzyskanych przez graczy w pliku csv."""
from storages_of_players_results import StorageOfAllPlayersScore
from datetime import datetime


class ResultsToCsvFile:
    """Klasa odpowiedzialna za zapis wyników uzyskanych przez graczy w pliku csv"""

    def __init__(self, obj_with_results: StorageOfAllPlayersScore) -> None:
        """
        Metoda zapisuje uzyskane wyniki w pliku CSV.

        :param obj_with_results: obiekt zawierający wyniki wszystkich graczy
        """

        text = "nazwa"
        for i in range(1, 121):
            text += ",rzut " + str(i)
        text += "\n"

        for team in obj_with_results.teams:
            for player in team.players_results:
                text += player.get_all_name_to_string()
                for rzut in player.get_list_suma():
                    text += ","
                    if rzut is not None:
                        text += str(rzut)
                text += "\n"
        file_name = "results/results_"+datetime.now().strftime("%y_%m_%d__%H_%M_%S")+".csv"
        f = open(file_name, "w")
        f.write(text)
        f.close()
