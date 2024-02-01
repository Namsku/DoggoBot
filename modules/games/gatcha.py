@dataclass
class Game:
    id: int
    name: str
    type: str
    cost: int


@dataclass
class Gatcha:
    id: int
    game_id: int
    text: str
    rarity: int
    time: int