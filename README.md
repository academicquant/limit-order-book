# A limit order book in Python with price-time priority, tested against a brute-force model

You'll very likely be asked to build a limit order book in a quant developer interview, and I'd say it's one of those tasks that's easy to get nearly right. I've kept this one small enough that you can read it in a few minutes. Prices are integer ticks (so you never compare floats), and each side keeps a dict of price levels where every level is a queue of resting orders, oldest first. A heap gives you the best price, and an id map lets you cancel an order without searching for it.

```python
from book import Book

b = Book()
b.submit(1, "S", 101, 5)
b.submit(2, "S", 100, 5)
b.submit(3, "S", 100, 5)
b.submit(4, "B", 101, 12)   # [(2, 4, 100, 5), (3, 4, 100, 5), (1, 4, 101, 2)]
b.depth("S")                # [(101, 3)]
```

When you send an order in, it trades against the best price on the other side first and, within that price, against the oldest order sitting there. You always trade at the resting order's price, and whatever's left of your order rests at its own limit. `submit` hands you back the fills as (resting id, incoming id, price, quantity), in the order they happened.

The tests caught a bug while I was writing this, and I think it's worth knowing about because it's an easy one to make in an interview. When a fill empties a price level, you have to delete that level straight away. If you don't, the heap may drop the price later while the empty level stays behind, and a new order at that same price then rests where the heap can't see it (so your best bid quietly goes missing). Also, cancelling from the middle of a level is linear in the level's size here. A production book would probably use an intrusive linked list to make it constant time, and the lesson linked below goes through that.

## Tests

Running `python3 -m unittest test_book` checks price priority and then time priority, along with partial fills and the remainder resting at its limit (plus cancels, and a book that shouldn't cross). The main test replays 3,000 random orders and cancels against both this book and a slow list-based model, and after every single step it checks that the fills and the best bid and ask agree between the two and that the book never ends up crossed. You'll only need the Python standard library to run them.

## More practice

If you'd like to go further, I've written up how I'd design the order book for a real trading system (the data structures and the API around them) at https://academicquant.co.uk/qd-order-book?utm_source=github&utm_medium=post&utm_campaign=github-limit-order-book

MIT licence.
