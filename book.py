"""A limit order book with price-time priority: add, cancel, match, best prices and depth.
Prices are integer ticks, so there is no floating-point comparison anywhere."""
import heapq
from collections import deque


class Order:
    __slots__ = ("oid", "side", "price", "qty")

    def __init__(self, oid, side, price, qty):
        self.oid, self.side, self.price, self.qty = oid, side, price, qty


class Book:
    def __init__(self):
        self.levels = {"B": {}, "S": {}}   # price -> deque of resting orders, oldest first
        self.heaps = {"B": [], "S": []}    # best-price heaps (bids stored negated); stale prices skipped lazily
        self.orders = {}                   # oid -> Order, for O(1) cancel

    def _best(self, side):
        h = self.heaps[side]
        while h:
            p = -h[0] if side == "B" else h[0]
            if self.levels[side].get(p):
                return p
            heapq.heappop(h)
        return None

    def best_bid(self):
        return self._best("B")

    def best_ask(self):
        return self._best("S")

    def submit(self, oid, side, price, qty):
        """Match a limit order against the other side, then rest what is left.
        Returns the fills as (resting oid, incoming oid, price, qty), in the order they happened."""
        if side not in ("B", "S") or qty <= 0 or oid in self.orders:
            raise ValueError("bad order")
        other = "S" if side == "B" else "B"
        fills = []
        while qty > 0:
            p = self._best(other)
            if p is None or (side == "B" and p > price) or (side == "S" and p < price):
                break
            queue = self.levels[other][p]
            rest = queue[0]
            q = min(qty, rest.qty)
            fills.append((rest.oid, oid, p, q))   # trades at the resting order's price
            qty -= q
            rest.qty -= q
            if rest.qty == 0:
                queue.popleft()
                del self.orders[rest.oid]
                if not queue:
                    del self.levels[other][p]   # an empty level must go, or its price could vanish from the heap
        if qty > 0:
            o = Order(oid, side, price, qty)
            lv = self.levels[side]
            if price not in lv:
                lv[price] = deque()
                heapq.heappush(self.heaps[side], -price if side == "B" else price)
            lv[price].append(o)
            self.orders[oid] = o
        return fills

    def cancel(self, oid):
        o = self.orders.pop(oid, None)
        if o is None:
            return False
        q = self.levels[o.side][o.price]
        q.remove(o)          # O(level size); an intrusive linked list makes this O(1)
        if not q:
            del self.levels[o.side][o.price]
        return True

    def depth(self, side, n=5):
        """Top n price levels on one side as (price, total quantity), best first."""
        lv = self.levels[side]
        prices = sorted(lv, reverse=(side == "B"))[:n]
        return [(p, sum(o.qty for o in lv[p])) for p in prices]
