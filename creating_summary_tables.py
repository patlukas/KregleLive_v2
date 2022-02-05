"""."""
import json

import cv2
import numpy as np
import logging
import logging_config
from storages_of_players_results import StorageOfAllPlayersScore
from methods_to_draw_on_image import MethodsToDrawOnImage


class CreatingSummaryTables(MethodsToDrawOnImage):
    """."""
    def __init__(self, path_to_summary_table_settings: str, obj_with_results: StorageOfAllPlayersScore | None):
        """."""
        super().__init__()
        self.__summary_tables_settings: dict | None = self.__get_summary_tables_settings(path_to_summary_table_settings)
        self.__obj_to_storage_results: StorageOfAllPlayersScore | None = obj_with_results

    @staticmethod
    def __get_summary_tables_settings(path_to_settings: str) -> dict | None:
        """."""
        try:
            file = open(path_to_settings, encoding='utf8')
            return json.load(file)
        except FileNotFoundError:
            logging.warning(f"Nie można odczytać ustawień  tabeli z podsuowaniem z pliku {path_to_settings}")
            return None

    @staticmethod
    def create_summary_tables():
        """."""
        img_return = np.full((30+40*10+5, 800, 3), 255, dtype=np.uint8)
        img_return[:, :] = (255, 0, 255)

        cv2.imshow("Tabela statystyk druzyn", img_return)
        cv2.waitKey(0)
