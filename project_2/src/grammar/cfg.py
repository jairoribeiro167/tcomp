from itertools import chain, combinations


class CFG:
    def __init__(self, variables, terminals, productions, start_symbol, is_normalized=False):
        self._variables = frozenset(variables)
        self._terminals = frozenset(terminals)
        self._productions = frozenset(productions)
        self._start_symbol = start_symbol
        self._is_normalized = is_normalized

    def _replace_start_symbol(self):
        # Check if start symbol is on the right side of productions.
        start_symbol = self._start_symbol
        variables = self._variables
        productions = self._productions

        if len(tuple(filter(lambda p: start_symbol in p[1], productions))) > 0:
            start_symbol = '$0'
            variables = variables.union((start_symbol,))
            productions = self._productions.union(((start_symbol, (self._start_symbol,)),))

        return CFG(
            variables=variables,
            terminals=self._terminals,
            productions=productions,
            start_symbol=start_symbol
        )

    def _remove_epsilon(self):
        def tuple_subset(tuple1, tuple2):
            for t in tuple1:
                if t not in tuple2:
                    return False
            return True

        productions = self._productions
        removed_productions = frozenset()

        while True:
            curr = \
                next((p for p in productions if '' in p[1] and p[0] != self._start_symbol), None)

            if not curr:
                break

            removed_productions = removed_productions.union((curr,))
            productions = productions.difference((curr,))
            new_productions = frozenset()
            curr_right = frozenset(filter(lambda p: curr[0] in p[1], productions))

            for p in curr_right:
                diff = tuple(filter(lambda e: e != curr[0], p[1]))
                candidates = tuple(
                    chain.from_iterable(combinations(p[1], r) for r in range(len(p[1]) + 1)))
                candidates = tuple(filter(lambda c: tuple_subset(diff, c), candidates))

                for c in candidates:
                    new_productions = \
                        new_productions.union(((p[0], c if c != () else ('',)),))

            new_productions = new_productions.difference(removed_productions)
            productions = productions.union(new_productions)

        return CFG(
            variables=self._variables,
            terminals=self._terminals,
            productions=productions,
            start_symbol=self._start_symbol
        )

    def _remove_unit_rules(self):
        productions = self._productions
        removed_productions = frozenset()

        while True:
            curr = \
                next((p for p in productions if len(p[1]) == 1 and p[1][0] in self._variables),
                     None)

            if not curr:
                break

            removed_productions = removed_productions.union((curr,))
            productions = productions.difference((curr,))
            new_productions = frozenset()
            curr_left = frozenset(filter(lambda p: curr[1][0] == p[0], productions))

            for p in curr_left:
                new_productions = \
                    new_productions.union(((curr[0], p[1]),))

            new_productions = new_productions.difference(removed_productions)
            productions = productions.union(new_productions)

        return CFG(
            variables=self._variables,
            terminals=self._terminals,
            productions=productions,
            start_symbol=self._start_symbol
        )

    def _keep_rules_with_two_symbols(self):
        variables = self._variables
        productions = self._productions
        new_productions = frozenset()
        index = 0

        while True:
            curr = next((p for p in productions if len(p[1]) > 2), None)

            if not curr:
                break

            productions = productions.difference((curr,))
            slc = curr[1][1:]
            production = next((p for p in new_productions if slc == p[1]), None)

            if production:
                productions = \
                    productions.union(((curr[0], (curr[1][0], production[0])),))
            else:
                new_production = (f'#{index}', slc)
                variables = variables.union((new_production[0],))
                productions = \
                    productions.union(((curr[0], (curr[1][0], new_production[0])),))
                productions = productions.union((new_production,))
                new_productions = new_productions.union((new_production,))
                index = index + 1

        return CFG(
            variables=variables,
            terminals=self._terminals,
            productions=productions,
            start_symbol=self._start_symbol
        )

    def _remove_terminals_from_no_unit_rules(self):
        variables = self._variables
        productions = self._productions
        new_productions = frozenset()
        index = 0

        while True:
            curr = \
                next((p for p in productions if len(p[1] == 2 and (
                        p[1][0] in self._terminals or p[1][1] in self._terminals
                ))), None)

            if not curr:
                break

            productions = productions.difference((curr,))
            slc = curr[1][:1] if curr[1][0] in self._terminals else curr[1][1:]
            production = next((p for p in new_productions if slc == p[1]), None)

            if production:
                if curr[1][1] in self._terminals:
                    productions = \
                        productions.union(((curr[0], (curr[1][0], production[0])),))
                else:
                    productions = \
                        productions.union(((curr[0], (production[0], curr[1][1])),))
            else:
                new_production = (f'@{index}', slc)
                variables = variables.union((new_production[0],))
                if curr[1][1] in self._terminals:
                    productions = \
                        productions.union(((curr[0], (curr[1][0], new_production[0])),))
                else:
                    productions = \
                        productions.union(((curr[0], (new_production[0], curr[1][1])),))
                productions = productions.union((new_production,))
                new_productions = new_productions.union((new_production,))
                index = index + 1

        return CFG(
            variables=variables,
            terminals=self._terminals,
            productions=productions,
            start_symbol=self._start_symbol
        )

    def normalize(self):
        if self._is_normalized:
            return CFG(
                variables=self._variables,
                terminals=self._terminals,
                productions=self._productions,
                start_symbol=self._start_symbol,
                is_normalized=self._is_normalized
            )
        else:
            g = self \
                ._replace_start_symbol() \
                ._remove_epsilon() \
                ._remove_unit_rules() \
                ._keep_rules_with_two_symbols() \
                ._remove_terminals_from_no_unit_rules()
            return CFG(
                variables=g._variables,
                terminals=g._terminals,
                productions=g._productions,
                start_symbol=g._start_symbol,
                is_normalized=True
            )

    def accept(self, string):
        if self._is_normalized:
            return False
        else:
            return self.normalize().accept(string)
