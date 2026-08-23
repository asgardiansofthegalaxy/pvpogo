from dataclasses import dataclass

# Dex
MAX_DEX = 865


# Regions
@dataclass
class Region:
    name: str
    dex_start: int
    dex_end: int


KANTO_REGION = Region("Kanto", 1, 151)
JOHTO_REGION = Region("Johto", 152, 251)
HOENN_REGION = Region("Hoenn", 252, 386)
SINNOH_REGION = Region("Sinnoh", 387, 493)
UNOVA_REGION = Region("Unova", 494, 649)
KALOS_REGION = Region("Kalos", 650, 718)
UNKNOWN_REGION = Region("Unknown", 808, 809)

REGIONS = {
    "kanto": KANTO_REGION,
    "johto": JOHTO_REGION,
    "hoenn": HOENN_REGION,
    "sinnoh": SINNOH_REGION,
    "unova": UNOVA_REGION,
    "kalos": KALOS_REGION,  # FIXME when legendaries are added
    "unknown": UNKNOWN_REGION,
}

NUM_REGIONS = 7  # Update this based on the actual number of regions defined

# Regional Dex numbers - # TODO: CAN PROBABLY BE DERIVED FROM POKEDEX DATA
REGIONAL_DEX_NUMBERS = [
    83,
    115,
    122,
    128,
    214,
    222,
    313,
    314,
    324,
    335,
    336,
    337,
    338,
    357,
    369,
    417,
    441,
    511,
    512,
    513,
    514,
    515,
    516,
    550,
    556,
    561,
    626,
    631,
    632,
]
