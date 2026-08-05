from config import DUMMY_LAT, DUMMY_LON


def get_position():
    """Liefert die aktuelle Position als (lat, lon).

    Aktuell eine Dummy-Implementierung mit fester Test-Position. Das Interface
    ist so gehalten, dass es spaeter 1:1 durch eine echte gpsd-Anbindung
    ersetzt werden kann, ohne dass detector.py angepasst werden muss.
    """
    return DUMMY_LAT, DUMMY_LON
