"""Moduł zawiera klasę z głównymi metodami do wstawiania tekstu i modyfikacji obrazu."""
from PIL import ImageFont, ImageDraw, Image


class MethodsToDrawOnImage:
    """
    Klasa z głównymi metodami do wypełniania  tabel.

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
        :param text: napis, który ma być dodany do komórki
        :param font_size: maksymalny rozmiar czcionki, jak się nie zmieści napis to rozmiar zostanie zmniejszony
        :param font_path: ścieżka do czcionki
        :param color: kolor czcionki zapisany w postaci (B, G, R)
        :param width: szerokość komórki
        :param height: wysokość komórki
        :return: komórka z dodanym wyśrodkowanym napisem
        """
        text = str(text)
        if text == "":
            return img_cell
        color = tuple(color)
        font_size = int(font_size)

        draw = ImageDraw.Draw(img_cell)
        while True:
            try:
                font = self.__get_font(font_path, font_size)
            except OSError:
                return img_cell
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

    def draw_center_text_by_coord(self, img: Image.Image, text: str | int | float, font_size: int,
                                  font_path: str, color: tuple | list,
                                  coords: list[int, int, int, int] | tuple[int, int, int, int]) -> Image.Image:
        """
        Zwraca obraz komórki z dodanym wyśrodkowanym w pionie i poziomi napisem.

        :param img: obraz komórki
        :param text: napis, który ma być dodany do komórki
        :param font_size: maksymalny rozmiar czcionki, jak się nie zmieści napis to rozmiar zostanie zmniejszony
        :param font_path: ścieżka do czcionki
        :param color: kolor czcionki zapisany w postaci (B, G, R)
        :param coords: współrzędne, kolejno lewa, prawa, górna, dolna
        :return: komórka z dodanym wyśrodkowanym napisem
        """
        return self.__draw_text_by_coord("center", img, text, font_size, font_path, color, coords)

    def draw_left_text_by_coord(self, img: Image.Image, text: str | int | float, font_size: int,
                                  font_path: str, color: tuple | list,
                                  coords: list[int, int, int, int] | tuple[int, int, int, int]) -> Image.Image:
        """
        Zwraca obraz komórki z dodanym wyjustowany do lewej krawędzi i wypoziomowany napisem.

        :param img: obraz komórki
        :param text: napis, który ma być dodany do komórki
        :param font_size: maksymalny rozmiar czcionki, jak się nie zmieści napis to rozmiar zostanie zmniejszony
        :param font_path: ścieżka do czcionki
        :param color: kolor czcionki zapisany w postaci (B, G, R)
        :param coords: współrzędne, kolejno lewa, prawa, górna, dolna
        :return: komórka z dodanym wyśrodkowanym napisem
        """
        return self.__draw_text_by_coord("left", img, text, font_size, font_path, color, coords)

    def draw_right_text_by_coord(self, img: Image.Image, text: str | int | float, font_size: int,
                                 font_path: str, color: tuple | list,
                                 coords: list[int, int, int, int] | tuple[int, int, int, int]) -> Image.Image:
        """
        Zwraca obraz komórki z dodanym wyjustowany do lewej krawędzi i wypoziomowany napisem.

        :param img: obraz komórki
        :param text: napis, który ma być dodany do komórki
        :param font_size: maksymalny rozmiar czcionki, jak się nie zmieści napis to rozmiar zostanie zmniejszony
        :param font_path: ścieżka do czcionki
        :param color: kolor czcionki zapisany w postaci (B, G, R)
        :param coords: współrzędne, kolejno lewa, prawa, górna, dolna
        :return: komórka z dodanym wyśrodkowanym napisem
        """
        return self.__draw_text_by_coord("right", img, text, font_size, font_path, color, coords)

    def __draw_text_by_coord(self, kind_position: str, img: Image.Image, text: str | int | float, font_size: int,
                             font_path: str, color: tuple | list,
                             coords: list[int, int, int, int] | tuple[int, int, int, int]) -> Image.Image:
        """
        Zwraca obraz komórki z dodanym wyjustowany do lewej krawędzi i wypoziomowany napisem.

        :param kind_position: jak ma być ułożony tekst: right/center/left
        :param img: obraz komórki
        :param text: napis, który ma być dodany do komórki
        :param font_size: maksymalny rozmiar czcionki, jak się nie zmieści napis to rozmiar zostanie zmniejszony
        :param font_path: ścieżka do czcionki
        :param color: kolor czcionki zapisany w postaci (B, G, R)
        :param coords: współrzędne, kolejno lewa, prawa, górna, dolna
        :return: komórka z dodanym wyśrodkowanym napisem
        """
        text = str(text)
        if text == "":
            return img
        color = tuple(color)
        font_size = int(font_size)

        width = coords[1] - coords[0]
        height = coords[3] - coords[2]

        draw = ImageDraw.Draw(img)
        while True:
            try:
                font = self.__get_font(font_path, font_size)
            except OSError:
                return img_cell
            w, h = draw.textsize(text, font=font)
            if w <= width and h <= height:
                break
            font_size -= 1
            if font_size <= 0:
                break
        if kind_position == "right":
            x = coords[1] - w
        elif kind_position == "center":
            x = (width - w) // 2 + coords[0]
        else:
            x = coords[0]
        y = (height - h) // 2 + coords[2]
        draw.text((x, y), text, font=font, fill=color)
        return img
