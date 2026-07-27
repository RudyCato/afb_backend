TPL = """<!DOCTYPE html>
<html lang="en" data-mode="retail">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Karla:wght@400;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header data-masthead></header>

<main id="main">
{body}
</main>

<footer data-footer></footer>
<script src="assets/catalog.js"></script>
<script src="assets/app.js"></script>
{extra}
</body>
</html>
"""

def hero(eyebrow, h1, lede):
    return f"""  <section class="shell hero" style="padding-block:clamp(2.5rem,6vw,4.5rem) 1.5rem">
    <span class="eyebrow">{eyebrow}</span>
    <h1 style="font-size:clamp(2.2rem,5vw,3.6rem);max-width:18ch">{h1}</h1>
    <p class="lede">{lede}</p>
  </section>
"""

def band(inner, tint=False, narrow=True):
    cls = "band tint" if tint else "band"
    sh = "shell narrow" if narrow else "shell"
    return f'  <section class="{cls}"><div class="{sh}">\n{inner}\n  </div></section>\n'

def cols(items):
    out = '<div class="cols">'
    for h, p in items:
        out += f"<div><h3>{h}</h3><p>{p}</p></div>"
    return out + "</div>"

PAGES = {}

# ---------------------------------------------------------------- wholesale
PAGES["wholesale.html"] = dict(
 title="Wholesale program — American Food & Beverage",
 desc="How wholesale ordering works at American Food & Beverage: minimums, lead times, delivery footprint and account setup.",
 body=hero("Wholesale &amp; foodservice",
   "Open an account, get a price sheet, order off the item numbers.",
   "We supply supermarket chains, independent grocers, distributors, restaurants, hotels and airlines. "
   "The process is short on purpose.")
 + band(cols([
     ("1 &middot; Tell us what you buy",
      "Send the item numbers you're interested in, or export a list straight off the item sheet. "
      "If you're not sure what maps to what, send us your current spec and we'll match it."),
     ("2 &middot; We price it against your volume",
      "Case pricing depends on how much and how often. Expect a sheet back within one business day, "
      "with minimums and lead times per line."),
     ("3 &middot; Account setup",
      "Credit application, resale certificate, and your delivery windows. Once that's on file "
      "pricing shows up when you sign in and you can order by item number."),
     ("4 &middot; Standing orders",
      "Most accounts settle into a weekly or biweekly cadence. Tell us the day, we'll build the route around it."),
   ]), narrow=False)
 + band(
   "<span class='eyebrow'>The details buyers ask about</span>"
   "<h2>Minimums, lead times, delivery</h2>"
   "<dl class='spec' style='grid-template-columns:auto 1fr;font-size:.95rem;margin-top:1.5rem'>"
   "<dt>Order minimum</dt><dd style='font-family:Karla,sans-serif'>Case quantities per item; a delivery minimum applies by zone and is set at account setup.</dd>"
   "<dt>Lead time</dt><dd style='font-family:Karla,sans-serif'>Stock items 24&ndash;48 hours. Custom blends and private label run 5&ndash;10 business days on the first order.</dd>"
   "<dt>Delivery</dt><dd style='font-family:Karla,sans-serif'>Next-day on our own trucks across NJ, NY and CT. Contracted LTL and full truckload nationwide.</dd>"
   "<dt>Pack changes</dt><dd style='font-family:Karla,sans-serif'>Any item can move between our seven packaging formats. Ask before you assume it isn't available in the size you want.</dd>"
   "<dt>Shelf life</dt><dd style='font-family:Karla,sans-serif'>Lot-coded with production and best-by dates on every case. Specs and COAs on request.</dd>"
   "<dt>Samples</dt><dd style='font-family:Karla,sans-serif'>Yes, on qualified accounts. Tell us the items and where to send them.</dd>"
   "</dl>", tint=True)
 + band(
   "<h2>Ready to price a list?</h2>"
   "<p>Switch to wholesale mode, work through the item sheet, and send it over. "
   "Or just call and read us the numbers.</p>"
   "<p style='margin-top:1.5rem'><a class='btn' href='shop.html'>Open the item sheet</a>"
   "<a class='btn ghost' href='quote.html' style='margin-left:.5rem'>Request pricing access</a></p>"),
 extra="<script>AFB.setMode('wholesale');</script>")

# ------------------------------------------------------------- private label
PAGES["private-label.html"] = dict(
 title="Private label & custom packing — American Food & Beverage",
 desc="Private label, custom blends and contract packing in seven formats from our SQF certified Paterson, NJ facility.",
 body=hero("Private label &amp; custom packing",
   "Your label, your blend, your pack size.",
   "We already roast, flavor, blend and pack under three of our own brands. Running yours is the same line "
   "with a different film.")
 + band(cols([
     ("Custom blends",
      "Trail mixes and snack blends built to a formula you approve, scaled by weight percentage so the "
      "hundredth case matches the first. Bring a target cost and we'll work backwards to a recipe."),
     ("Your packaging",
      "Sixteen-ounce clear containers, screw-top jars, to-go cups, presentation trays, granola cups, "
      "or bulk cases from 14 to 50 lb. Film, sleeve, label and shrink band to your artwork."),
     ("Roasting and flavoring",
      "Dry roast, oil roast, honey roast, tamari, cajun, truffle, caramelized. Done here, which is why "
      "a flavor tweak is a scheduling question rather than a sourcing project."),
     ("Chocolate and yogurt panning",
      "Almonds, cashews, peanuts, raisins, cranberries, espresso beans, pretzels &mdash; panned in house "
      "to your shell thickness."),
   ]), narrow=False)
 + band(
   "<span class='eyebrow'>What we need from you</span>"
   "<h2>Starting a private label run</h2>"
   "<p>Send us three things and we can quote it: the product spec or a sample of what you're matching, "
   "your target pack size and case count, and your annual volume estimate. Artwork can come later &mdash; "
   "we'll send you the dielines once the format is settled.</p>"
   "<p>First runs are typically 5&ndash;10 business days after artwork approval. Repeat runs slot into "
   "the normal production schedule.</p>"
   "<p style='margin-top:1.5rem'><a class='btn' href='quote.html'>Start a private label conversation</a></p>", tint=True))

# ------------------------------------------------------------ certifications
PAGES["certifications.html"] = dict(
 title="Certifications & food safety — American Food & Beverage",
 desc="SQF certified facility, USDA Organic handler and OU Kosher certification at American Food & Beverage in Paterson, NJ.",
 body=hero("Certifications &amp; food safety",
   "The paperwork your QA team is going to ask for.",
   "We keep certificates current and on hand, because the first thing a new account requests is "
   "documentation and the second is a sample.")
 + band(cols([
     ("SQF certified facility",
      "Our 60,000 sq ft Paterson plant is certified to the SQF food safety code, with documented "
      "prerequisite programs, HACCP plans and internal audits. Certificate and audit score available on request."),
     ("USDA Organic",
      "Certified organic handler. Organic items run on scheduled lines with documented changeover and "
      "segregation, and carry their own item numbers so nothing gets substituted by accident."),
     ("OU Kosher",
      "Certified by the Orthodox Union across the catalog, with rabbinic supervision on site. "
      "The current letter of certification lists every approved item."),
     ("Traceability",
      "Every case is lot-coded to a production date and a raw material lot. One-up, one-back "
      "traceability, exercised in mock recalls, results documented."),
     ("Allergen control",
      "Peanuts, tree nuts, sesame, milk and soy are all present in the facility. Allergen handling is "
      "scheduled and validated; labels state it plainly rather than burying it."),
     ("Supplier approval",
      "Growers, processors and packers are approved before their first shipment and reviewed on a "
      "cycle. COAs held on file per lot."),
   ]), narrow=False)
 + band(
   "<h2>Need the certificates?</h2>"
   "<p>Ask and we'll send current copies of the SQF certificate, organic certificate, OU letter, "
   "insurance, and product specs or COAs for any item number.</p>"
   "<p style='margin-top:1.5rem'><a class='btn' href='contact.html'>Request documentation</a></p>", tint=True))

# -------------------------------------------------------------------- about
PAGES["about.html"] = dict(
 title="About & facility — American Food & Beverage",
 desc="American Food & Beverage is an importer, wholesaler, roaster and packer in Paterson, New Jersey, operating as Grassland and Premium Food.",
 body=hero("About the company",
   "Importer, wholesaler, roaster, packer. All four, on one floor.",
   "American Food &amp; Beverage sources direct from growers, processors and packers worldwide, then "
   "finishes and packs everything at our own facility in Paterson, New Jersey.")
 + band(
   "<span class='eyebrow'>The floor</span>"
   "<h2>60,000 square feet in Paterson</h2>"
   "<p>Receiving, cold and dry storage, roasting, flavoring, chocolate panning, blending, packing and "
   "shipping all happen in the same building. That's not a boast about size &mdash; it's why a recipe change "
   "or a pack-size change is something we can schedule rather than something we have to source.</p>"
   "<p>We run three brands out of it: <b>Grassland</b> for organic and natural, <b>Premium Food</b> for the "
   "gourmet line, and <b>Tasty</b> for the screw-top jars. Same floor, same standards.</p>"
   "<div class='stats'>"
   "<div class='stat'><b>60,000</b><span>Sq ft facility</span></div>"
   "<div class='stat'><b>370+</b><span>Active SKUs</span></div>"
   "<div class='stat'><b>10</b><span>Product categories</span></div>"
   "<div class='stat'><b>Own fleet</b><span>Tri-State next day</span></div>"
   "</div>", tint=True)
 + band(cols([
     ("What we source",
      "Dried fruits, nuts, grains, trail mixes, plantain chips, beans, seeds, peas and lentils, "
      "chocolate covered items, gummies and candies &mdash; direct from growers, processors and packers "
      "all over the world."),
     ("What we also stock",
      "Vinegars, honey, olives, sugar, oats, lemon juice and pancake syrups. If it belongs next to "
      "our categories on a grocery shelf, ask &mdash; we probably carry it."),
     ("Who we serve",
      "Corporate supermarkets, independent grocery stores, distributors, restaurants, hotels, airlines "
      "and the broader food service industry."),
     ("How it ships",
      "Our own trucks across the Tri-State area with next-day delivery, plus private trucking partners "
      "for deliveries across the rest of the country."),
   ]), narrow=False))

# -------------------------------------------------------------------- quote
PAGES["quote.html"] = dict(
 title="Request wholesale pricing — American Food & Beverage",
 desc="Request a wholesale account and pricing access from American Food & Beverage, Paterson NJ.",
 body=hero("Request pricing access",
   "Tell us what you buy and we'll send a price sheet.",
   "Wholesale pricing is set per account, so it lives behind a short form rather than on a public page. "
   "This usually comes back the same day.")
 + """  <section class="band"><div class="shell" style="max-width:760px">
    <div class="panel">
      <form id="access" novalidate>
        <div class="formgrid">
          <div class="field"><label for="company">Company</label><input id="company" type="text" required></div>
          <div class="field"><label for="name">Contact name</label><input id="name" type="text" required></div>
          <div class="field"><label for="email">Work email</label><input id="email" type="email" required></div>
          <div class="field"><label for="phone">Phone</label><input id="phone" type="tel" required></div>
          <div class="field"><label for="type">Business type</label>
            <select id="type">
              <option>Supermarket chain</option><option>Independent grocer</option>
              <option>Distributor</option><option>Restaurant / foodservice</option>
              <option>Hotel</option><option>Airline</option><option>Other</option>
            </select></div>
          <div class="field"><label for="volume">Monthly volume, roughly</label>
            <select id="volume">
              <option>Under 20 cases</option><option>20&ndash;100 cases</option>
              <option>100&ndash;500 cases</option><option>Pallet quantities</option>
              <option>Truckload</option><option>Not sure yet</option>
            </select></div>
          <div class="field full"><label for="cats">Categories you're interested in</label>
            <input id="cats" type="text" placeholder="Nuts, trail mixes, organic dried fruit&hellip;"></div>
          <div class="field full"><label for="notes">Anything else</label>
            <textarea id="notes" placeholder="Private label, specific item numbers, delivery windows, target price points"></textarea></div>
        </div>
        <button class="btn" type="submit">Request access</button>
        <p class="count" style="margin-top:.75rem" id="err" role="alert"></p>
      </form>
    </div>
    <p class="count" style="margin-top:1.25rem">Prefer to talk? Call <a href="tel:+19083456345">(908)&nbsp;345-6345</a>
    or email <a href="mailto:sales@americanfoodbeverage.com">sales@americanfoodbeverage.com</a>.</p>
  </div></section>
""",
 extra="""<script>
document.getElementById("access").addEventListener("submit", function(e){
  e.preventDefault();
  var form = this, err = document.getElementById("err");
  var bad = Array.prototype.filter.call(form.querySelectorAll("[required]"), function(i){
    return !i.value.trim() || (i.type === "email" && i.value.indexOf("@") < 1);
  });
  if (bad.length){
    err.style.color = "var(--terra-deep)";
    err.textContent = "Fill in " + bad[0].previousElementSibling.textContent.toLowerCase() + " to continue.";
    bad[0].focus(); return;
  }
  form.parentElement.innerHTML =
    '<h3 style="margin-bottom:.4em">Request received</h3>' +
    '<p>A rep will be in touch, usually the same business day. If it\\'s urgent, call (908) 345-6345.</p>' +
    '<a class="btn ghost" href="shop.html">Browse the item sheet</a>';
  window.scrollTo(0,0);
});
</script>""")

# ------------------------------------------------------------------ contact
PAGES["contact.html"] = dict(
 title="Contact — American Food & Beverage",
 desc="Contact American Food & Beverage in Paterson, New Jersey. Sales, orders, documentation requests.",
 body=hero("Contact",
   "Paterson, New Jersey. Someone picks up.",
   "Sales, orders, certificates, samples, or a question about an item number &mdash; here's where each goes.")
 + band(cols([
     ("Sales &amp; new accounts",
      "<a href='mailto:sales@americanfoodbeverage.com'>sales@americanfoodbeverage.com</a><br>"
      "<a href='tel:+19083456345'>(908) 345-6345</a>"),
     ("Orders",
      "<a href='mailto:orders@grasslandfoods.com'>orders@grasslandfoods.com</a><br>"
      "Existing accounts, reorders and delivery changes."),
     ("Mail",
      "PO Box 533<br>Paterson, NJ 07543<br>United States"),
     ("Documentation",
      "SQF and organic certificates, OU letters, specs and COAs &mdash; ask sales and we'll send current copies."),
   ]), narrow=False)
 + """  <section class="band tint"><div class="shell" style="max-width:760px">
    <span class="eyebrow">Send a message</span>
    <h2>What do you need?</h2>
    <div class="panel" style="margin-top:1.25rem">
      <form id="contact" novalidate>
        <div class="formgrid">
          <div class="field"><label for="name">Your name</label><input id="name" type="text" required></div>
          <div class="field"><label for="email">Email</label><input id="email" type="email" required></div>
          <div class="field"><label for="company">Company (optional)</label><input id="company" type="text"></div>
          <div class="field"><label for="topic">Topic</label>
            <select id="topic">
              <option>New wholesale account</option><option>Existing order</option>
              <option>Private label</option><option>Certificates &amp; documentation</option>
              <option>Samples</option><option>Something else</option>
            </select></div>
          <div class="field full"><label for="msg">Message</label>
            <textarea id="msg" required placeholder="Item numbers help if you have them"></textarea></div>
        </div>
        <button class="btn" type="submit">Send message</button>
        <p class="count" style="margin-top:.75rem" id="err" role="alert"></p>
      </form>
    </div>
  </div></section>
""",
 extra="""<script>
document.getElementById("contact").addEventListener("submit", function(e){
  e.preventDefault();
  var form = this, err = document.getElementById("err");
  var bad = Array.prototype.filter.call(form.querySelectorAll("[required]"), function(i){
    return !i.value.trim() || (i.type === "email" && i.value.indexOf("@") < 1);
  });
  if (bad.length){
    err.style.color = "var(--terra-deep)";
    err.textContent = "Fill in " + bad[0].previousElementSibling.textContent.toLowerCase() + " to continue.";
    bad[0].focus(); return;
  }
  form.parentElement.innerHTML =
    '<h3 style="margin-bottom:.4em">Message sent</h3>' +
    '<p>Thanks &mdash; we\\'ll get back to you shortly. For anything time-sensitive, call (908) 345-6345.</p>';
});
</script>""")

for name, cfg in PAGES.items():
    html = TPL.format(title=cfg["title"], desc=cfg["desc"], body=cfg["body"], extra=cfg.get("extra",""))
    open(name, "w").write(html)
    print("wrote", name, len(html))
