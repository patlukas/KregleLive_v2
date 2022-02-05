"""Moduł odpowiedzialny za zarządzanie błędami i informajami jakie ma dostać użytkownik."""
from datetime import datetime


class Informing:
    """
    Klasa zarządzająca błędami i informacjami dla użytkownika.

    clear_log_file() -> None - czyści plik log i przenosi jego zawartość do archiwum
    get_list_message() -> list[dict] -> zwraca listę komunikatów i ich szczegóły
    info(str) -> None - dodaje komunikat o priorytecie "info"
    warning(str) -> None - dodaje komunikat o priorytecie "warning"
    error(str) -> None - dodaje komunikat o priorytecie "error"
    """
    def __init__(self):
        """
        __path - ścieżka do głównego pliku z bieżącymi logami
        __path_to_arch - ścieżka do pliku z historycznymi logami
        """
        self.__path: str = "info.log"
        self.__path_to_arch: str = "info_arch.log"

    @staticmethod
    def __get_time() -> str:
        """Metoda zwraca napis zawierający bieżącą datę z dokłądnością do sekundy."""
        return datetime.now().strftime("%H:%M:%S %d.%m.%y")

    def __write(self, new_line: str) -> None:
        """
        Metoda zapisuje przkazaną linię na końcu pliku z logami.

        :param new_line: tekst który ma zotać zapisany
        """
        with open(self.__path, "a") as file:
            file.write(new_line)
            file.close()

    def info(self, text: str) -> None:
        """
        Metoda do zapisywania wiadomości o priorytecie "info".

        :param text: wiadomość jaka ma zostać zapisana
        """
        self.__write(self.__get_time()+"|info|"+text.replace("|", " ")+"\n")

    def warning(self, text: str) -> None:
        """
        Metoda do zapisywania wiadomości o priorytecie "warning".

        :param text: wiadomość jaka ma zostać zapisana
        """
        self.__write(self.__get_time()+"|warning|"+text.replace("|", " ")+"\n")

    def error(self, text: str) -> None:
        """
        Metoda do zapisywania wiadomości o priorytecie "error".

        :param text: wiadomość jaka ma zostać zapisana
        """
        self.__write(self.__get_time()+"|error|"+text.replace("|", " ")+"\n")

    def clear_log_file(self):
        """Metoda przenosi zawartość głównego log do archiwum log oraz czyści plik z głównymi log."""
        with open(self.__path_to_arch, "a") as arch_file, open(self.__path, "r") as file:
            arch_file.write(file.read())
            file.close()
            open(self.__path, "w").close()
            arch_file.close()

    def get_list_message(self) -> list[dict]:
        """
        Metoda zwraca listę wszystkich wiadomości jakie są w pliku log.

        :return: lista słowników. Każdy słownik ma taką strukturę:
                    {
                        "data": <str: data dodania komunikatu, np: 01:12:00 05.02.22>,
                        "type": <str: rodzaj komunikatu, np info, warning, error>,
                        "text": <str: treść komunikatu>
                    }
        """
        list_message = []
        with open(self.__path, "r") as file:
            rows = file.read()
            for row in rows.split("\n"):
                details = row.split("|")
                if len(details) != 3:
                    continue
                message = {
                    "data": details[0],
                    "type": details[1],
                    "text": details[2]
                }
                list_message.append(message)
            file.close()
        return list_message
