from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from functools import cached_property
from pathlib import Path
from random import choice, sample
from sys import path
from typing import Type


ROOT_DIR = Path(path[0]).parent.parent
DATA_DIR = ROOT_DIR / 'data'




class DictOfRanges(dict):
    def __init__(self, mappable: dict):
        for key in mappable:
            if (
                   not isinstance(key, tuple) 
                or len(key) != 2
                or not isinstance(key[0], int) 
                or not isinstance(key[1], int)
            ):
                raise ValueError('...')
        super().__init__(mappable)
    
    def __getitem__(self, key: int):
        if isinstance(key, int):
            for left, right in self:
                if left <= key <= right:
                    return super().__getitem__((left, right))
        else:
            return super().__getitem__(key)
    
    def get_range(self, key: int) -> tuple[int, int]:
        if isinstance(key, int):
            for left, right in self:
                if left <= key <= right:
                    return left, right
        else:
            raise TypeError


@dataclass
class KindParameter:
    name: str
    initial: float
    min: float
    max: float
    
    def __hash__(self):
        return hash(self.name)


class CreatureParameter(ABC):
    name: str
    
    def __init__(
            self,
            initial: float,
            left: float,
            right: float,
            creature: 'Creature',
    ):
        self.__value = initial
        self._min = left
        self._max = right
        self.creature = creature
    
    @property
    def value(self) -> float:
        return self.__value
    
    @cached_property
    def range(self) -> tuple[float, float]:
        return self._min, self._max
    
    @value.setter
    def value(self, new_value: float):
        if new_value <= self._min:
            self.__value = self._min
        elif self._max <= new_value:
            self.__value = self._max
        else:
            self.__value = new_value
    
    @abstractmethod
    def update(self) -> None:
        pass


class Health(CreatureParameter):
    name = 'здоровье'
    
    def update(self) -> None:
        satiety = self.creature.params[Satiety]
        critical = sum(satiety.range) / 4
        if 0 < satiety.value < critical:
            self.value -= 0.5
        elif satiety.value == 0:
            self.value -= 1
        else:
            self.value += 0.1


class Satiety(CreatureParameter):
    name = 'сытость'
    
    def update(self) -> None:
        self.value -= 1


Parameters = Enum(
    'Parameters',
    {
        cls.__name__: cls
        for cls in CreatureParameter.__subclasses__()
    }
)


class Action(ABC):
    name: str
    
    def __init__(self, creature: 'Creature' = None):
        self.creature = creature
    
    def __hash__(self):
        return hash(self.name)
    
    @abstractmethod
    def do(self) -> str:
        pass


class PlayerAction(Action):
    image: Path
    state = 'normal'


class Feed(PlayerAction):
    name = 'покормить'
    image = DATA_DIR / 'images/btn1.png'
    
    def __init__(
            self, 
            amount: float,
            creature: 'Creature' = None, 
    ):
        self.amount = amount
        super().__init__(creature)
    
    def do(self) -> str:
        self.creature.params[Satiety].value += self.amount
        return f'вы покормили питомца на {self.amount} ед.'


class TeaseHead(PlayerAction):
    name = 'почесать голову'
    image = DATA_DIR / 'images/btn3.png'
    
    def do(self) -> str:
        return 'вы почесали голову питомцу'


class CreatureAction(Action):
    def __init__(
            self,
            rand_coeff: float,
            creature: 'Creature' = None, 
    ):
        self.rand_coeff = rand_coeff
        super().__init__(creature)


class ChaseTail(CreatureAction):
    name = 'гоняться за своим хвостом'
    
    def do(self) -> None:
        print('бегает за своим хвостом')


class NoAction(PlayerAction):
    name = 'бездействие'
    image = DATA_DIR / 'images/no_action.png'
    state = 'disabled'
    
    def do(self) -> None:
        print('бездействует')



class MaturePhase:
    def __init__(
            self, 
            days: int,
            *parameters: KindParameter,
            player_actions: Iterable[PlayerAction],
            creature_actions: Iterable[CreatureAction],
    ):
        self.days = days
        self.params = set(parameters)
        self.player_actions = set(player_actions)
        self.creature_actions = set(creature_actions)


class Kind(DictOfRanges):
    def __init__(
            self, 
            name: str, 
            image: Path,
            *mature_phases: MaturePhase
    ):
        self.name = name
        self.image = image
        
        phases = {}
        left = 0
        for phase in mature_phases:
            key = left, left + phase.days - 1
            phases[key] = phase
            left = left + phase.days
        super().__init__(phases)
        
        self.max_age = left - 1


@dataclass
class State:
    age: int
    
    def __repr__(self):
        return '/'.join(v for v in self.__dict__.values())


class History(list):
    def get_param(self, param: Type) -> list[float]:
        return [
            getattr(state, param.__name__)
            for state in self
        ]


class Creature:
    def __init__(
            self, 
            kind: Kind,
            name: str,
    ):
        self.kind = kind
        self.name = name
        self.__age: int = 0
        self.params: dict[Type, CreatureParameter] = {}
        for param in kind[0].params:
            cls = Parameters[param.name].value
            self.params[cls] = cls(
                initial=param.initial,
                left=param.min,
                right=param.max,
                creature=self,
            )
        self.player_actions: set[PlayerAction]
        self.creature_actions: set[CreatureAction]
        self.__set_actions()
        self.history: History = History()
    
    def __repr__(self):
        # title = f'({self.kind.name}) {self.name}: {self.age} ИД'
        params = '\n'.join(
            f'{p.name}: {p.value:.1f}' 
            for p in self.params.values()
        )
        # return f'{title}\n{params}'
        return f'{params}'
    
    def __set_actions(self) -> None:
        self.player_actions = {
            action.__class__(**{**action.__dict__, 'creature': self})
            for action in self.kind[self.age].player_actions
        }
        self.creature_actions = {
            action.__class__(**{**action.__dict__, 'creature': self})
            for action in self.kind[self.age].creature_actions
        }
    
    def update(self) -> None:
        for param in self.params.values():
            param.update()
        self.save()
    
    @property
    def age(self) -> int:
        return self.__age
    
    @age.setter
    def age(self, new_value: int):
        old_phase = self.kind.get_range(self.__age)
        new_phase = self.kind.get_range(new_value)
        self.__age = new_value
        if old_phase != new_phase:
            self._grow_up()
    
    def _grow_up(self) -> None:
        for param in self.kind[self.age].params:
            cls = Parameters[param.name].value
            initial = param.initial or self.params[cls].value
            self.params[cls] = cls(
                initial=initial,
                left=param.min,
                right=param.max,
                creature=self,
            )
        self.__set_actions()
    
    def random_action(self) -> None:
        action = choice(tuple(self.creature_actions))
        no_action = NoAction()
        prob = int(action.rand_coeff * 100)
        choice(sample([action, no_action], counts=[prob, 100-prob], k=100)).do()
    
    def save(self) -> State:
        state = State(self.age)
        for cls, param in self.params.items():
            setattr(state, cls.__name__, param.value)
        self.history.append(state)
        return state


dog = Kind(
    'собака',
    DATA_DIR / 'images/dog.png',
    MaturePhase(
        5,
        KindParameter(Health.__name__, 10, 0, 25),
        KindParameter(Satiety.__name__, 2, 0, 15),
        player_actions=[
            Feed(10),
        ],
        creature_actions=[
            ChaseTail(0.9),
        ]
    ),
    MaturePhase(
        50,
        KindParameter(Health.__name__, 0, 0, 60),
        KindParameter(Satiety.__name__, 0, 0, 40),
        player_actions=[
            Feed(25),
            TeaseHead(),
        ],
        creature_actions=[
            ChaseTail(0.35),
        ]
    ),
    MaturePhase(
        20,
        KindParameter(Health.__name__, 0, 0, 45),
        KindParameter(Satiety.__name__, 0, 0, 25),
        player_actions=[
            Feed(20),
            TeaseHead(),
        ],
        creature_actions=[],
    ),
)

jack = Creature(dog, 'Джек')

buttons = [
    pa.do
    for pa in jack.player_actions
]
