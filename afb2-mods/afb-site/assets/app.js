/* =========================================================================
   American Food & Beverage — shared behaviour
   Loads the catalog, remembers the visitor's mode, runs both carts.
   NAV / footer schema: americanfoodbeverage.com (5-category product nav)
   ========================================================================= */
(function () {
  "use strict";

  /* ---------- storage (falls back to memory when blocked) ------------- */
  var mem = {};
  var store = {
    get: function (k) {
      try { var v = localStorage.getItem(k); return v === null ? mem[k] : v; }
      catch (e) { return mem[k]; }
    },
    set: function (k, v) {
      mem[k] = v;
      try { localStorage.setItem(k, v); } catch (e) { /* memory only */ }
    }
  };
  var getJSON = function (k, d) { try { return JSON.parse(store.get(k)) || d; } catch (e) { return d; } };
  var setJSON = function (k, v) { store.set(k, JSON.stringify(v)); };

  /* ---------- mode ---------------------------------------------------- */
  var MODE_KEY = "afb.mode";
  function getMode() { return store.get(MODE_KEY) === "wholesale" ? "wholesale" : "retail"; }
  function setMode(m) {
    store.set(MODE_KEY, m);
    document.documentElement.dataset.mode = m;
    document.dispatchEvent(new CustomEvent("afb:mode", { detail: m }));
    paintChrome();
  }

  /* ---------- carts --------------------------------------------------- */
  function cart() { return getJSON("afb.cart", []); }
  function quote() { return getJSON("afb.quote", []); }
  function saveCart(c) { setJSON("afb.cart", c); paintChrome(); }
  function saveQuote(q) { setJSON("afb.quote", q); paintChrome(); }

  function addToCart(item, qty) {
    var c = cart(), row = c.filter(function (r) { return r.item === item; })[0];
    if (row) { row.qty += qty; } else { c.push({ item: item, qty: qty }); }
    saveCart(c);
  }
  function addToQuote(item, cases) {
    var q = quote(), row = q.filter(function (r) { return r.item === item; })[0];
    if (row) { row.cases += cases; } else { q.push({ item: item, cases: cases }); }
    saveQuote(q);
  }
  function cartCount() { return cart().reduce(function (n, r) { return n + r.qty; }, 0); }
  function quoteCount() { return quote().length; }

  /* ---------- catalog -------------------------------------------------- */
  var MIN = null;
  function minimums() { return MIN; }

  var catalogPromise = null;
  function catalog() {
    if (catalogPromise) return catalogPromise;
    catalogPromise = fetch(base() + "catalog.json")
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (d) { MIN = d.minimums; return d; })
      .catch(function () {
        if (window.AFB_CATALOG) { MIN = window.AFB_CATALOG.minimums; return window.AFB_CATALOG; }
        throw new Error("Catalog unavailable");
      });
    return catalogPromise;
  }
  function base() { return ""; }

  /* ---------- fuzzy-ish search ----------------------------------------- */
  function matches(p, q) {
    if (!q) return true;
    var hay = (p.item + " " + p.name + " " + p.category + " " + p.format).toLowerCase();
    return q.toLowerCase().split(/\s+/).every(function (tok) {
      if (!tok) return true;
      if (hay.indexOf(tok) > -1) return true;
      var i = 0;
      for (var c = 0; c < hay.length && i < tok.length; c++) if (hay[c] === tok[i]) i++;
      return i === tok.length && tok.length > 3;
    });
  }

  /* ---------- formatting ----------------------------------------------- */
  function money(n) { return "$" + n.toFixed(2); }
  function oz(n) { return (Math.round(n * 100) / 100) + " oz"; }
  function glyph(cat) {
    return ({
      "Nuts": "N", "Flavored Gourmet Nuts": "G", "Seeds": "S", "Trail Mixes": "T",
      "Dried Fruits": "F", "Granolas & Crunches": "R", "Plantain Chips": "P",
      "Chocolate Covered": "C", "Candy & Gummies": "Y", "Grains, Beans & Lentils": "B"
    })[cat] || "•";
  }

  /* ---------- chrome (header + footer) ---------------------------------- */
  // Navigation schema from americanfoodbeverage.com: 5 product categories
  var NAV = [
    ["shop.html?cat=Nuts",                                  "Nuts &amp; Seeds"],
    ["shop.html?cat=Dried%20Fruits",                        "Dried Fruit"],
    ["shop.html?cat=Grains%2C%20Beans%20%26%20Lentils",    "Superfood Powders"],
    ["shop.html?cat=Chocolate%20Covered",                   "Chocolate &amp; Sweets"],
    ["shop.html?cat=Plantain%20Chips",                      "Snacks"],
    ["about.html",                                          "About Us"],
    ["contact.html",                                        "Contact"]
  ];

  // SVG leaf/plant icon for the brand mark
  var BRAND_SVG =
    '<svg viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
      '<path d="M10 3 C10 3 4 5 4 11 C4 14.3 6.7 17 10 17" stroke="#fff" stroke-width="1.6" stroke-linecap="round" fill="none"/>' +
      '<path d="M10 17 C10 17 16 14 16 9 C16 6 13.5 3.5 10 3" stroke="#fff" stroke-width="1.6" stroke-linecap="round" fill="none"/>' +
      '<line x1="10" y1="17" x2="10" y2="11" stroke="#fff" stroke-width="1.6" stroke-linecap="round"/>' +
    '</svg>';

  function renderChrome() {
    var here = location.pathname.split("/").pop() || "index.html";
    var head = document.querySelector("[data-masthead]");
    if (head) {
      head.className = "masthead";
      head.innerHTML =
        // utility top bar
        '<div class="topbar"><div class="shell topbar-in">' +
          '<a href="contact.html">Contact</a>' +
          '<a href="shop.html#faq">FAQ</a>' +
          '<span>Ship to United States</span>' +
        '</div></div>' +
        // main masthead
        '<div class="shell masthead-in">' +
          '<a class="brand" href="index.html" aria-label="American Food and Beverage — home">' +
            '<div class="brand-mark">' + BRAND_SVG + '</div>' +
            '<div class="brand-text">' +
              '<b>American Food &amp; Beverage</b>' +
              '<span>SINCE 1989 &middot; PATERSON, NJ</span>' +
            '</div>' +
          '</a>' +
          '<nav class="nav" aria-label="Main">' +
          NAV.map(function (n) {
            var pg = n[0].split("?")[0];
            return '<a href="' + n[0] + '"' +
              (pg === here ? ' aria-current="page"' : '') + '>' + n[1] + '</a>';
          }).join("") +
          '<span class="stamp" role="group" aria-label="Browsing mode">' +
            '<button type="button" data-set-mode="retail">Retail</button>' +
            '<button type="button" data-set-mode="wholesale">Wholesale</button>' +
          '</span>' +
          '<a class="cartlink" href="cart.html" data-cartlink></a>' +
        '</nav></div>';
      head.addEventListener("click", function (e) {
        var b = e.target.closest("[data-set-mode]");
        if (b) setMode(b.dataset.setMode);
      });
    }

    var foot = document.querySelector("[data-footer]");
    if (foot) {
      foot.className = "foot";
      // Footer: dark ink background, Corporate / Links / Support / Pages columns
      foot.innerHTML =
        '<div class="shell"><div class="foot-grid">' +
          '<div>' +
            '<a class="brand" href="index.html" style="margin-bottom:1rem;display:inline-flex">' +
              '<div class="brand-mark">' + BRAND_SVG + '</div>' +
              '<div class="brand-text"><b>American Food &amp; Beverage</b><span>SINCE 1989 &middot; PATERSON, NJ</span></div>' +
            '</a>' +
            '<p>Importer, roaster and packer with four manufacturing facilities on 10 acres in New Jersey.</p>' +
            '<div class="certs"><span>SQF Certified</span><span>USDA Organic</span><span>OU Kosher</span></div>' +
          '</div>' +
          '<div><h4>Corporate</h4><ul>' +
            '<li><a href="about.html">About Us</a></li>' +
            '<li><a href="returns.html">Orders &amp; Returns</a></li>' +
            '<li><a href="terms.html">Terms of Service</a></li>' +
          '</ul></div>' +
          '<div><h4>Links</h4><ul>' +
            '<li><a href="contact.html">Store Location</a></li>' +
            '<li><a href="privacy.html">Privacy Policy</a></li>' +
          '</ul></div>' +
          '<div><h4>Support</h4><ul>' +
            '<li><a href="shop.html#faq">FAQ</a></li>' +
            '<li><a href="contact.html">Contact Us</a></li>' +
            '<li><a href="mailto:sales@americanfoodbeverage.com">Email Support</a></li>' +
          '</ul></div>' +
          '<div><h4>Pages</h4><ul>' +
            '<li><a href="index.html">Home</a></li>' +
            '<li><a href="shop.html">Shop</a></li>' +
            '<li><a href="about.html">About</a></li>' +
            '<li><a href="cart.html">Checkout</a></li>' +
          '</ul></div>' +
        '</div>' +
        '<div class="legal">' +
          '&copy; 2023 American Food Beverage. All rights reserved. &nbsp;&middot;&nbsp; ' +
          '<a href="tel:+19083456345">(908) 345-6345</a> &nbsp;&middot;&nbsp; ' +
          '<a href="privacy.html">Privacy</a> &nbsp;&middot;&nbsp; ' +
          '<a href="terms.html">Terms</a>' +
        '</div></div>';
    }
    paintChrome();
  }

  function paintChrome() {
    var m = getMode();
    document.documentElement.dataset.mode = m;
    document.querySelectorAll("[data-set-mode]").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.dataset.setMode === m));
    });
    document.querySelectorAll("[data-cartlink]").forEach(function (a) {
      if (m === "wholesale") {
        var n = quoteCount();
        a.innerHTML = "Quote <b>" + n + "</b>";
        a.setAttribute("aria-label", n + " items on your quote request");
      } else {
        var c = cartCount();
        a.innerHTML = "Cart <b>" + c + "</b>";
        a.setAttribute("aria-label", c + " items in your cart");
      }
    });
  }

  /* ---------- minimum order checks ------------------------------------- */
  function retailCheck(subtotal) {
    var m = MIN.retail, ok = subtotal >= m.orderSubtotal;
    return {
      ok: ok,
      short: Math.max(0, m.orderSubtotal - subtotal),
      pct: Math.min(100, (subtotal / m.orderSubtotal) * 100),
      message: ok ? "" : "Add " + money(m.orderSubtotal - subtotal) +
        " to reach the " + money(m.orderSubtotal) + " order minimum."
    };
  }
  function shipping(subtotal) {
    var m = MIN.retail;
    return subtotal >= m.freeShippingAt ? 0 : m.shippingFlat;
  }
  function wholesaleCheck(cases, lb) {
    var m = MIN.wholesale;
    var byCase = cases >= m.orderCases, byWeight = lb >= m.orderWeightLb;
    var ok = m.rule === "both" ? (byCase && byWeight) : (byCase || byWeight);
    return {
      ok: ok, byCase: byCase, byWeight: byWeight,
      shortCases: Math.max(0, m.orderCases - cases),
      shortLb: Math.max(0, m.orderWeightLb - lb),
      pct: Math.min(100, Math.max(cases / m.orderCases, lb / m.orderWeightLb) * 100),
      message: ok ? "" : "Opening order minimum is " + m.orderCases + " cases or " +
        m.orderWeightLb + " lb. You're " + Math.max(0, m.orderCases - cases) +
        " cases short — or add " + Math.ceil(Math.max(0, m.orderWeightLb - lb)) + " lb."
    };
  }
  function lineShort(product, cases) { return Math.max(0, product.moq - cases); }

  /* ---------- CSV export ------------------------------------------------ */
  function toCSV(rows) {
    var head = ["Item #", "Description", "Category", "Packaging", "Case QTY", "Unit Wt (oz)", "Case Wt (oz)", "Min cases", "Organic"];
    var body = rows.map(function (p) {
      return [p.item, p.name, p.category, p.format, p.caseQty, p.unitOz, p.caseWeightOz, p.moq, p.organic ? "Yes" : ""];
    });
    return [head].concat(body).map(function (r) {
      return r.map(function (c) {
        c = String(c);
        return /[",\n]/.test(c) ? '"' + c.replace(/"/g, '""') + '"' : c;
      }).join(",");
    }).join("\r\n");
  }
  function download(name, text) {
    var b = new Blob([text], { type: "text/csv;charset=utf-8" });
    var u = URL.createObjectURL(b), a = document.createElement("a");
    a.href = u; a.download = name; document.body.appendChild(a); a.click();
    a.remove(); setTimeout(function () { URL.revokeObjectURL(u); }, 500);
  }

  /* ---------- expose ----------------------------------------------------- */
  window.AFB = {
    getMode: getMode, setMode: setMode, catalog: catalog, matches: matches,
    money: money, oz: oz, glyph: glyph,
    cart: cart, quote: quote, saveCart: saveCart, saveQuote: saveQuote,
    addToCart: addToCart, addToQuote: addToQuote, paintChrome: paintChrome,
    toCSV: toCSV, download: download,
    minimums: minimums, retailCheck: retailCheck, wholesaleCheck: wholesaleCheck,
    shipping: shipping, lineShort: lineShort
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderChrome);
  } else { renderChrome(); }
})();
