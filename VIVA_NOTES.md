# Viva Notes – E-Commerce Order Processing (Roman Urdu)

## Files ka kaam
| File | Kaam |
|---|---|
| `main.py` | Program yahan se shuru hota hai. `python main.py` demo chalata hai, `--test` tests |
| `config.py` | Saare rule numbers (discount tiers, shipping, low stock limit) ek `SETTINGS` dictionary mein |
| `data.py` | Starter products aur orders (functions se fresh copy milti hai, global variable nahi) |
| `helpers.py` | `add_up(*values)` (*args), `round_money` (half up), `money()` formatting |
| `pricing.py` | `calculate_order_subtotal`, `make_discount_calculator` (closure), `calculate_discount`, `calculate_shipping` (sab Decimal mein) |
| `validation.py` | `validate_order` – order, customer, product price/stock sab check, reason ke sath |
| `orders.py` | `process_order(order, products, **options)`, `process_all_orders` (duplicate ID check), `check_options` |
| `reports.py` | Customer/product report, `build_sales_summary` (dictionary) aur `format_sales_report` (text) |
| `test_orders.py` | Chhote chhote `test_` functions (har assert ke sath message), pytest ke sath bhi chalte hain. `main.py` isay sirf `--test` par import karta hai |

## Program ka flow (1 minute mein)
1. `main.py` -> `process_all_orders` har order ko `process_order` ko deta hai.
2. `process_order` pehle `validate_order` chalata hai. Galat ho to status = "rejected" (reason ke sath), stock nahi badalta.
3. Valid ho to subtotal -> discount -> shipping -> total nikalta hai (`pricing.py`).
4. "paid" ho to stock kam hota hai. "pending" ho to stock nahi ghatta aur revenue mein nahi ginta.
5. `generate_sales_report` (`reports.py`) sab results se report banata hai.

## Mumkin sawal aur jawab

**Q: Code multiple files mein kyun hai?**
Taake har kaam alag ho: data, pricing, validation, processing, reports. Padhna aur test karna aasan hota hai. Files ek dusri ko `import` se use karti hain (jaise `from pricing import calculate_discount`).

**Q: Classes kyun nahi use ki?**
Assessment mein mana tha. Sab kuch functions se kiya hai, data dictionaries aur lists mein hai.

**Q: Rejected, pending aur paid mein kya farq hai?**
Rejected = order invalid (stock kam, galat ID, qty <= 0 waghera). Pending = valid hai lekin payment nahi hui. Paid = valid + payment ho gayi. Sirf paid revenue aur stock par asar dalta hai.

**Q: Discount aur shipping subtotal par kyun lagi?**
Assignment ke mutabiq: discount slab subtotal se chunta hai, shipping bhi subtotal >= 500 par free. Total = subtotal - discount + shipping.

**Q: Revenue mein shipping shamil hai?**
Haan, revenue = customer ne jitna total pay kiya (discount ke baad + shipping). Agar sir shipping alag chahein to `reports.py` ke `generate_sales_report` mein `total_revenue` ki line mein `r["total"]` ki jagah `r["subtotal"] - r["discount"]` kar dein.

**Q: Ek hi product do baar order mein ho to stock check kaise hota hai?**
`validate_order` mein `requested` dictionary same product ki quantities jama karti hai, phir total ko stock se compare karta hai.

**Q: Ek order ne stock khatam kar diya to agla order?**
Orders ek ek karke chalte hain aur paid order ke baad stock update ho jata hai, to agla order bacha hua stock dekhta hai.

**Q: `**kwargs` kahan use hua?**
`orders.py` mein `process_order(order, products, **options)`. `options.get("include_shipping", True)` aur `options.get("apply_discount", True)`.

**Q: `*args` kahan use hua?**
`helpers.py` mein `add_up(*values)`. Kitni bhi values de sakte hain, jaise `add_up(*line_totals)`.

**Q: Lambda kahan use hua?**
`reports.py` mein sorting: `sorted(spend.items(), key=lambda pair: (-pair[1], pair[0]))` (zyada spend pehle, barabar ho to naam alphabetical). Low stock sorting mein bhi.

**Q: Comprehension aur sets kahan hain?**
List comprehension: `line_totals` (`pricing.py`). Set comprehension: `unique_customers` aur `sold_categories` (`reports.py`).

**Q: LEGB kahan dikhaya?**
Do closures hain: `reports.py` mein `make_low_stock_checker(threshold)` aur `pricing.py` mein `make_discount_calculator(tiers)`. Andar wala function apne bahar wale function ka `threshold` / `tiers` use karta hai (Enclosing scope). Local = function ke andar ke variables. Global = file level functions (koi global variable use nahi kiya). Built-in = `len`, `max`, `sorted` waghera.

**Q: Tie ho to kya hota hai?**
Top product/customer ki list banti hai, sab barabar wale dikhte hain. Starter data mein Mouse aur Keyboard dono 2 units, to "Keyboard, Mouse (tie...)" aata hai.

**Q: Low stock ka matlab?**
Stock <= 10. `generate_sales_report(..., low_stock_threshold=10)` se badal sakte hain. Koi na ho to "- None".

**Q: Program crash kyun nahi hota?**
`validate_order` type, missing keys, galat qty, galat price/stock sab check karta hai aur crash ki jagah reason deta hai. `process_all_orders` mein try/except safety net bhi hai, aur wahan bhi order ID record mein rehta hai taake pata chale kaun sa order fail hua.

**Q: Edge cases kahan test hue?**
`test_orders.py` mein 54 tests: unknown product, zero/negative qty, qty > stock, no items, invalid payment, empty products, empty orders, tie, no low stock, duplicate order ID, missing ID/customer, galat price/stock, galat options. Chalane ke liye `python main.py --test` (ya `python -m pytest`). Agar koi test fail ho to uska naam aur message dikhta hai aur baqi tests phir bhi chalte hain.

## Review ke baad kiye gaye fixes (sir ne ye galtiyan pakdi thin)

**Q: Same order do dafa aaye to?**
Ab ye rule `process_order(order, products, seen_ids=None, ...)` ke andar hai (ek hi jagah). `process_all_orders` ek set bana kar har call ko deta hai. Jo order ID pehle accept ho chuki (paid ya pending), wo dobara aaye to "Duplicate order ID ORD001" ke sath reject hoti hai. Isse double charge aur double stock kam hona band hua. Agar pehla order rejected tha to wahi ID theek karke dobara bhej sakte hain.

**Q: Order ID ya customer na ho to?**
`validate_order` dono ko non-empty string maangta hai (khali, spaces, None, number sab reject). Isse report mein `None` ya number wali customer type error bhi khatam hui.

**Q: Product ka price ya stock galat ho to?**
`validation.py` mein `is_valid_price` (number, >= 0, NaN/infinity nahi, bool nahi) aur `is_valid_stock` (whole number, >= 0). Galat ho to order "Invalid price for product P001" jaisi reason ke sath reject hota hai, TypeError se crash nahi.

**Q: Safety net mein order ID kyun gum hoti thi?**
Pehle except block "UNKNOWN" likhta tha. Ab `build_record(order, ...)` order se ID aur customer le leta hai, to crash ke baad bhi pata chalta hai kaun sa order fail hua.

**Q: `**options` mein typo ho to?**
`check_options` unknown naam (jaise `include_shiping`) aur galat type (jaise `apply_discount="no"`) par `TypeError` deta hai. Pehle typo chup chaap ignore ho jata tha. `**kwargs` assessment ki requirement hai, isliye rakha hai, bas ab check hota hai.

**Q: "Ali" aur "ali " alag customer?**
Nahi. Naam `.strip()` hota hai aur `.casefold()` se compare hota hai, to ek hi customer ginta hai.

**Q: unique_customers mein rejected orders?**
Nahi. Sirf valid (paid ya pending) orders wale customers ginte hain, aur report mein "Customers With A Valid Order: N" print hota hai.

**Q: `process_all_orders(None, ...)` par kya hota hai?**
Saaf `TypeError` ("orders must be a list ...") aata hai, ajeeb error nahi.

**Q: Tests ek lambe function mein kyun nahi?**
Ab har cheez ka alag `test_...` function hai (`test_discount_slabs`, `test_duplicate_order_id_rejected`, ...). Ek fail ho to baqi chalte rehte hain aur message batata hai kaunsa check toota.

## Doosre review ke fixes (Decimal, IDs, pending, seen_ids)

**Q: Float se paisay galat kyun round hote the?**
Float computer mein 150.675 ko bilkul 150.675 nahi rakhta, aur Python ka `round()` "half to even" use karta hai. Is liye 1004.50 par 15% ka discount 150.67 aata tha, jabke sahi 150.68 hai. Ab sab paisay `Decimal` hain (`helpers.py`), `quantize(Decimal("0.01"), ROUND_HALF_UP)` se round hotay hain, aur `add_up` har step par nahi, sirf aakhir mein ek dafa round karta hai. Floats pehle `str()` se guzar kar Decimal bante hain, taake 19.99 bilkul 19.99 rahe. `decimal` bhi standard library hai.

**Q: "ORD009" aur "ord009" ka kya?**
Order ID `.strip().upper()` se normalise hoti hai (`get_order_key` in `orders.py`) aur record mein bhi isi shakal mein save hoti hai. Dono same order hain, doosra reject hota hai, stock sirf ek dafa kam hota hai.

**Q: Pending orders stock reserve kyun nahi karte?**
Assessment ka rule hai ke pending order stock kam nahi karta. Is liye pending order sirf "provisional" hai: valid hai lekin na stock rokta hai na revenue banata hai. Do pending orders 10 laptop ke liye dono accept ho sakte hain, lekin jab payment hogi to stock dobara check hota hai aur sirf pehla fill hoga. Ye README aur `orders.py` ke docstring mein likha hai aur `test_pending_orders_are_provisional` mein test hota hai.

**Q: Shipping discount se pehle ke subtotal par kyun?**
Rule yahi hai: 520 ka subtotal -> 52 discount, shipping free (kyunke 520 >= 500), total 468. Agar discount ke baad (468) dekhte to shipping lagti. Ye `test_shipping_uses_subtotal_before_discount` mein lock hai.

**Q: Stock ka type har jagah same kyun?**
`reports.py` ka low-stock checker ab `validation.py` ka `is_valid_stock` use karta hai (whole number, >= 0), is liye float stock dono jagah ek jaisa treat hota hai.

**Q: "Customers With A Valid Order" ka matlab?**
Wo customers jin ka koi paid ya pending order valid tha. Is mein sirf pay karne walay nahi, pending walay bhi shamil hain. Rejected orders kabhi nahi ginte.

## Teesre review ke points (stock, crash, constants, report)

**Q: Stock do dafa kam ho kar valid order reject to nahi hota?**
Nahi. Stock sirf `process_order` mein ek dafa kam hota hai (koi `reserved_stock` nahi). `test_stock_is_subtracted_only_once`: 10 laptops mein 6 + 3 dono paid, stock 1; aur 5 + 5 dono paid, stock 0.

**Q: Kharab order (None, string, galat product) se crash?**
Nahi. `validate_order` har cheez type ke sath check karta hai (order dict hai? product dict hai? product ID string hai? list to nahi?) aur sirf reject karta hai. `test_malformed_orders_do_not_crash`.

**Q: Pending order 999 laptops ka accept hota hai?**
Nahi. Stock check pending orders par bhi lagta hai, to 999 laptops reject. Lekin pending stock reserve nahi karta (assessment ka rule), is liye payment par stock dobara check hota hai.

**Q: Magic numbers kahan gaye?**
`config.py` ke `SETTINGS` dictionary mein: discount tiers, free shipping limit (500), shipping cost (20), low stock limit (10). Code mein koi number inline nahi.

**Q: Report test kaise hoti hai?**
`build_sales_summary` sirf dictionary return karta hai (print nahi), `format_sales_report` usay text banata hai, aur print sirf `main.py` karta hai. `test_sales_summary_is_a_testable_dictionary`.

**Q: Categories ka set kahan use hua?**
`sold_categories` (set comprehension) ab report mein "Categories Sold: Accessories, Electronics" ke taur par print hota hai.

**Q: Products dictionary badalti hai?**
Haan, paid order stock kam karta hai (in place). Docstring aur README mein likha hai; original rakhna ho to `copy.deepcopy(products)` do.

**Q: NaN price?**
`is_valid_price` NaN aur infinity reject karta hai, to total kabhi `nan` nahi banta.

## Sir ke last review ke points (minor)

**Q: `calculate_discount` har baar function kyun nahi banata?**
Pehle har call par `make_discount_calculator(...)` dobara chalta tha: tiers dobara sort hotay aur andar wala function dobara banta tha. Ab `pricing.py` mein file load hotay hi ek dafa bana liya jata hai: `calculate_discount = make_discount_calculator(SETTINGS["discount_tiers"])`. Ye ab bhi closure hai (andar wala function apne bahar wale function ke `tiers_high_first` ko yaad rakhta hai), is liye LEGB ka "Enclosing" demo wahi rehta hai. `test_discount_calculator_is_built_only_once` check karta hai ke call ke dauran naya calculator nahi banta.

**Q: Order record mein har item ki price kyun save ki?**
Pehle item mein sirf `product_id` aur `quantity` thi. Total save tha, lekin ek line kis rate par bikki ye pata nahi chalta tha, aur agar baad mein product ki price badal jaye to record adhoora rehta. Ab har item mein `unit_price` aur `line_total` (= unit_price x quantity) bhi hain, to order record apne aap mein mukammal hai. `test_item_records_keep_unit_price_and_line_total` check karta hai ke line totals ka jama subtotal ke barabar hai aur price badalne ke baad bhi record mein purani price rehti hai.

## Starter data ka expected result
- ORD001: subtotal 1250, discount 187.50 (15%), shipping 0, total 1062.50 (paid)
- ORD002: subtotal 450, discount 22.50 (5%), shipping 20, total 447.50 (paid)
- ORD003: pending (revenue mein nahi, stock nahi ghata)
- Revenue $1,510.00, Discount $210.00, Shipping $20.00
- Customers With A Valid Order: 2, top customer Ali, top product tie Keyboard/Mouse, low stock: Laptop (9 left)
