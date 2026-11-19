import random
import unittest

from book import Book


class TestBook(unittest.TestCase):
    def test_price_then_time_priority(self):
        b = Book()
        b.submit(1, "S", 101, 5)
        b.submit(2, "S", 100, 5)
        b.submit(3, "S", 100, 5)
        fills = b.submit(4, "B", 101, 12)
        self.assertEqual(fills, [(2, 4, 100, 5), (3, 4, 100, 5), (1, 4, 101, 2)])
        self.assertEqual(b.depth("S"), [(101, 3)])
        self.assertIsNone(b.best_bid())

    def test_rests_remainder_at_its_limit(self):
        b = Book()
        b.submit(1, "S", 100, 3)
        self.assertEqual(b.submit(2, "B", 100, 10), [(1, 2, 100, 3)])
        self.assertEqual(b.best_bid(), 100)
        self.assertEqual(b.depth("B"), [(100, 7)])

    def test_no_cross_no_trade(self):
        b = Book()
        b.submit(1, "B", 99, 5)
        self.assertEqual(b.submit(2, "S", 100, 5), [])
        self.assertEqual((b.best_bid(), b.best_ask()), (99, 100))

    def test_cancel(self):
        b = Book()
        b.submit(1, "B", 99, 5)
        b.submit(2, "B", 99, 5)
        self.assertTrue(b.cancel(1))
        self.assertFalse(b.cancel(1))
        self.assertEqual(b.submit(3, "S", 99, 10), [(2, 3, 99, 5)])
        self.assertEqual(b.best_ask(), 99)

    def test_random_against_a_slow_reference(self):
        # replay 3,000 random orders and cancels on the book and on a brute-force list model
        rng = random.Random(9)
        b, ref, live = Book(), [], []
        for oid in range(3000):
            if live and rng.random() < 0.2:
                victim = rng.choice(live)
                live.remove(victim)
                self.assertEqual(b.cancel(victim), any(o[0] == victim for o in ref))
                ref = [o for o in ref if o[0] != victim]
                continue
            side, price, qty = rng.choice("BS"), rng.randint(95, 105), rng.randint(1, 9)
            want = []
            left = qty
            while left:
                opp = [o for o in ref if o[1] != side and (o[2] <= price if side == "B" else o[2] >= price)]
                if not opp:
                    break
                best = min(opp, key=lambda o: (o[2] if side == "B" else -o[2], o[4]))
                q = min(left, best[3])
                want.append((best[0], oid, best[2], q))
                left -= q
                best[3] -= q
                if best[3] == 0:
                    ref.remove(best)
            if left:
                ref.append([oid, side, price, left, oid])
                live.append(oid)
            self.assertEqual(b.submit(oid, side, price, qty), want)
            bids = [o[2] for o in ref if o[1] == "B"]
            asks = [o[2] for o in ref if o[1] == "S"]
            self.assertEqual(b.best_bid(), max(bids) if bids else None)
            self.assertEqual(b.best_ask(), min(asks) if asks else None)
            if bids and asks:
                self.assertLess(max(bids), min(asks))


if __name__ == "__main__":
    unittest.main()
