# Sample data — ILLUSTRATIVE ONLY

Fictional company: **Kuih Mesra Sdn Bhd** (small biscuit & frozen-food maker, Selangor).
All names, quantities, prices (RM) and dates are made up for demo purposes.
Replace these files with real business data using the same columns.

## The demo situation (why the plan order matters)

Butter is scarce: 15 kg in stock. The cookie orders need 19.2 kg in total, so not all of them can be made.

- **ORD-001**, a big Raya hamper order (100 boxes, 12 kg butter), arrived **first** but is due **last** (27 Oct).
- **ORD-004** and **ORD-006**, two small shop/café orders (30 boxes each, 3.6 kg butter each), arrived later but are due **sooner** (23 and 24 Oct).

First come, first served (the baseline) makes the hamper first and runs out of butter for both small orders: **3 of 6 orders on time**.
Earliest due date first (Timed) makes the two urgent orders first: **4 of 6 on time**. The hamper is flagged,
and the purchase request shows the butter needed. With a 4-day supplier lead time, it could still arrive before 27 Oct if the owner approves quickly.

Chicken is also short (25 kg for 35 kg of curry puff orders), so one curry puff order cannot be made in either plan.
Egg stock is set high enough that eggs are not the bottleneck in this demo.
