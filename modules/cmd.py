from dataclasses import dataclass

@dataclass
class Cmd:
    name: str
    description: str
    usage: str
    used: int
    cost: int
    status: bool
    aliases: list
    category: str
    run: callable