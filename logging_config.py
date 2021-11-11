"""Po wywołaniu modułu podstawowe ustawienia logging są ustawiane"""

import logging

logging.basicConfig(
    format='%(asctime)s | %(levelname)s | %(message)s',
    filename='errors.log',
    encoding='utf-8',
    level=logging.DEBUG
)
