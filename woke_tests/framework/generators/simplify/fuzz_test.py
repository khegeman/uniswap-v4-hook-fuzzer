"""

Attempts to simplify one sequence of a recorded fuzz test. 
"""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Callable, DefaultDict, List, Optional, Type, Dict, get_type_hints

from typing_extensions import get_type_hints, get_args, get_origin
from dataclasses import fields

from woke.testing.core import get_connected_chains
from woke.testing import fuzzing

import jsons
import copy


class FuzzTest(fuzzing.FuzzTest):
    def __get_methods_dict(self, attr: str) -> Dict[Callable]:
        ret = {}
        for x in dir(self):
            if hasattr(self.__class__, x):
                m = getattr(self.__class__, x)
                if hasattr(m, attr) and getattr(m, attr):
                    ret[x] = m
        return ret

    def get_param(self, param: str, sequence_num: int, flow_num: int, t: Type):
        params = self.sequences[str(sequence_num)][str(flow_num)]
        data = params["params"]
        value = data[param]
        if get_origin(t) is list:
            return [get_args(t)[0](v) for v in value]
        if type(value) is dict:
            # assuming this type is a dataclass that defines fields for now
            # for field in fields(t):
            #    print(field,field.type)
            resolved_hints = get_type_hints(t)
            field_names = [field.name for field in fields(t)]
            resolved_field_types = {name: resolved_hints[name] for name in field_names}
            args = {
                field.name: resolved_field_types[field.name](value[field.name])
                for field in fields(t)
            }
            # print("type",type(t), "args", args)
            return t(**args)
        return t(value)

    def load(self, filename: str):
        self.sequences = {}
        # load json lines recorded file to a dict for now
        with open(filename, "r") as f:
            for line in f.readlines():
                try:
                    flow = jsons.loads(line)
                    seqnum = list(flow)[0]
                    s = self.sequences.get(seqnum, {})
                    s.update(flow[seqnum])
                    self.sequences[seqnum] = s
                except Exception as e:
                    print(line, e)

    def run(
        self,
        sequences_count: int,
        flows_count: int,
        *,
        dry_run: bool = False,
        record: bool = False,
        filename: str,
        sequence: int,
        simplified: str,
        **kwargs,
    ):
        chains = get_connected_chains()

        flows: Dict[Callable] = self.__get_methods_dict("flow")
        invariants: List[Callable] = self.__get_methods("invariant")
        self.load(filename)
        sequences_count = len(list(self.sequences))

        open(simplified, "w").close()

        i = int(sequence)
        print("Simplifying sequence", i)
        flows_counter: DefaultDict[Callable, int] = defaultdict(int)
        invariant_periods: DefaultDict[Callable[[None], None], int] = defaultdict(int)

        # minimize each sequence
        flows_count = len(list(self.sequences.get(str(i))))
        removed = []
        baseline = None
        final = flows_count - 1
        for r in range(flows_count - 1, -1, -1):
            print("minimizer pass", r)
            snapshots = [chain.snapshot() for chain in chains]

            # in the first pass, we want to save the exception we get on the final flow
            # if there is no failure, skip minimize for the sequence

            self._flow_num = 0
            self._sequence_num = i
            self.pre_sequence()

            for j in range(flows_count):
                flow_name = self.sequences.get(str(i)).get(str(j)).get("name")
                print("processing flow", flow_name)
                if j == r or (j in removed):
                    if baseline is not None:
                        print("skipping flow", flow_name, j, r)
                        continue

                flow = flows.get(flow_name)

                fp = {
                    k: self.get_param(k, i, j, v)
                    for k, v in get_type_hints(flow, include_extras=True).items()
                    if k != "return"
                }

                self._flow_num = j
                try:
                    self.pre_flow(flow)
                    flow(self, **fp)
                    flows_counter[flow] += 1
                    self.post_flow(flow)

                    if not dry_run:
                        self.pre_invariants()
                        for inv in invariants:
                            if invariant_periods[inv] == 0:
                                self.pre_invariant(inv)
                                inv(self)
                                self.post_invariant(inv)

                            invariant_periods[inv] += 1
                            if invariant_periods[inv] == getattr(inv, "period"):
                                invariant_periods[inv] = 0
                        self.post_invariants()

                except AssertionError as e:
                    print("error", e, "pass ", j, final)
                    if baseline is None:
                        print("found baseline error", e)
                        baseline = e
                    elif j == final:
                        if type(e) is type(baseline) and e.args == baseline.args:
                            removed.append(r)
                            print("found valid sequence", removed)
                    break
                except Exception as e:
                    print("Exception", e, "pass ", j, final)
                    if baseline is None:
                        print("found baseline exception", e)
                        baseline = e
                    elif j == final:
                        if type(e) is type(baseline) and e.args == baseline.args:
                            removed.append(r)
                            print("found valid sequence", removed)
                    break

            print("ending ", r)
            self.post_sequence()

            for snapshot, chain in zip(snapshots, chains):
                chain.revert(snapshot)
            if baseline is None:
                print("sequence succeeded, skip optimization")
                break

        next = 0
        for r in range(flows_count):
            if r not in removed:
                print(i, "add", r, " to final")
                save_row = {0: {next: self.sequences[str(i)][str(r)]}}
                with open(simplified, "a") as fp:
                    jr = jsons.dumps(save_row, strip_privates=True, strip_nulls=True)
                    print(jr, file=fp)

                next = next + 1
