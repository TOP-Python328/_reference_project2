from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from functools import cached_property
from typing import Type


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
    
    def __getitem__(self, key):
        if isinstance(key, int):
            for left, right in self:
                if left <= key <= right:
                    return super().__getitem__((left, right))
        else:
            return super().__getitem__(key)


@dataclass
class KindParameter:
    name: str
    initial: float
    min: float
    max: float


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
        self.origin = creature
    
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
    
    # @abstractmethod
    # def update(self) -> None:
        # pass


class Health(CreatureParameter):
    name = 'здоровье'


class Satiety(CreatureParameter):
    name = 'сытость'


Parameters = Enum(
    'Parameters',
    {
        cls.__name__: cls
        for cls in CreatureParameter.__subclasses__()
    }
)


class MaturePhase:
    def __init__(
            self, 
            days: int,
            *parameters: KindParameter
    ):
        self.days = days
        self.params = parameters


class Kind(DictOfRanges):
    def __init__(
            self, 
            name: str, 
            *mature_phases: MaturePhase
    ):
        self.name = name
        
        phases = {}
        left = 0
        for phase in mature_phases:
            key = left, left + phase.days - 1
            phases[key] = phase
            left = left + phase.days
        super().__init__(phases)


class Creature:
    def __init__(
            self, 
            kind: Kind,
            name: str,
    ):
        self.kind = kind
        self.name = name
        self.age: int = 0
        self.params: dict[Type, CreatureParameter] = {}
        for param in kind[0].params:
            cls = Parameters[param.name].value
            self.params[cls] = cls(
                param.initial,
                param.min,
                param.max,
                self
            )
    
    def __repr__(self):
        return f'({self.kind.name}) {self.name}: {self.age} ИД'


dog = Kind(
    'собака',
    MaturePhase(
        5,
        KindParameter(Health.__name__, 10, 0, 25),
        KindParameter(Satiety.__name__, 2, 0, 15),
    ),
    MaturePhase(
        50,
        KindParameter(Health.__name__, 0, 0, 60),
        KindParameter(Satiety.__name__, 0, 0, 40),
    ),
    MaturePhase(
        20,
        KindParameter(Health.__name__, 0, 0, 45),
        KindParameter(Satiety.__name__, 0, 0, 25),
    ),
)

jack = Creature(dog, 'Джек')

