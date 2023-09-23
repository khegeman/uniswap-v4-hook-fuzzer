"""

Fuzz test data collection classes and decorators
"""
from woke.development.core import Address, Account

from pathlib import Path
from typing import Dict
import time
import jsons
from dataclasses import dataclass, asdict, fields
from . import get_address


def address_serializer(obj: Address | Account, **kwargs) -> str:
    return str(get_address(obj))


jsons.set_serializer(address_serializer, Address)
jsons.set_serializer(address_serializer, Account)


def set_serializer(t: type) -> None:
    jsons.set_serializer(address_serializer, t)


@dataclass
class FlowMetaData:
    name: str
    params: Dict


class JsonCollector:
    def __init__(self, testName: str):
        datapath = Path.cwd().resolve() / ".replay"
        datapath.mkdir(parents=True, exist_ok=True)

        self._filename = datapath / f"{testName}-{time.strftime('%Y%m%d-%H%M%S')}.json"

        print("recording to", self._filename)

    def __repr__(self):
        return self._values.__repr__()

    @property
    def values(self):
        return self._values

    def collect(self, fuzz, fn, **kwargs):
        save_row = {
            fuzz._sequence_num: {fuzz._flow_num: FlowMetaData(fn.__name__, kwargs)}
        }
        with open(self._filename, "a") as fp:
            j = jsons.dumps(save_row, strip_privates=True, strip_nulls=True)
            print(j, file=fp)
