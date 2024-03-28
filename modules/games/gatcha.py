@dataclass
class Gatcha:
    id: int
    name: str
    cost : int
    timer: int

@dataclass
class GatchaItem:
    id: int
    name: str
    rarity: int
    gatcha_id: int
    description: str

class GatchaCog:
    def __init__(self, bot):
        self.bot = bot
        self.gatcha = {}
        self.gatcha_items = {}
        self.load_gatcha()
        self.load_gatcha_items()

    def load_gatcha(self):
        query = "SELECT * FROM gatcha"
        gatcha = self.bot.db.fetch(query)
        for g in gatcha:
            self.gatcha[g[0]] = Gatcha(*g)
    
    def load_gatcha_items(self):
        query = "SELECT * FROM gatcha_items"
        gatcha_items = self.bot.db.fetch(query)
        for g in gatcha_items:
            self.gatcha_items[g[0]] = GatchaItem(*g)
    