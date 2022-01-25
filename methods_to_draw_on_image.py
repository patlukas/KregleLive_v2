"""Moduł zawiera klasę z głównymi metodami do wstawiania tekstu i modyfikacji obrazu."""
from PIL import ImageFont, ImageDraw, Image


class MethodsToDrawOnImage:
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
