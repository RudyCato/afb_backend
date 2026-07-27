import re, json, io

PAGES = ["index","shop","product","cart","wholesale","private-label",
         "certifications","about","careers","sops","quote","contact"]
NAMES = "|".join(p.replace("-", r"\-") for p in PAGES)

def rewrite(s):
    """Turn page-to-page links into hash routes."""
    s = re.sub(r'\b(' + NAMES + r')\.html', lambda m: "#/" + m.group(1), s)
    return s

def grab(fn):
    raw = open(fn, encoding="utf-8").read()
    main = re.search(r"<main[^>]*>(.*?)</main>", raw, re.S)
    body = main.group(1) if main else ""
    attrs = re.search(r"<main([^>]*)>", raw).group(1)
    scripts = re.findall(r'<script>(.*?)</script>', raw, re.S)
    pagecss = "\n".join(re.findall(r"<style>(.*?)</style>", raw, re.S))
    title = re.search(r"<title>(.*?)</title>", raw, re.S).group(1)
    # drop the ld+json block (it has no <script> bare tag match anyway)
    return dict(attrs=attrs.strip(), body=rewrite(body), pagecss=pagecss,
                scripts=[rewrite(s) for s in scripts], title=title)

routes = {p: grab(p + ".html") for p in PAGES}

css = open("assets/site.css", encoding="utf-8").read()
css += "\n".join(v["pagecss"] for v in routes.values() if v.get("pagecss"))
app = open("assets/app.js", encoding="utf-8").read()
cat = json.load(open("catalog.json", encoding="utf-8"))
jobs = json.load(open("jobs.json", encoding="utf-8"))
sops = json.load(open("sops.json", encoding="utf-8"))

# --- patch app.js for single-file / hash-route life ------------------------
app = rewrite(app)

# 1. catalog comes from the embedded global, never the network
_start = app.index("    catalogPromise = fetch(")
_end = app.index("});", app.index("throw new Error(\"Catalog unavailable\");")) + 3
app = (app[:_start]
       + "    MIN = window.AFB_CATALOG.minimums;\n"
         "    catalogPromise = Promise.resolve(window.AFB_CATALOG);"
       + app[_end:])
assert "fetch(" not in app.split("window.AFB_renderChrome")[0], "catalog fetch not fully removed"

# 2. current-page detection reads the hash, not the path
app = app.replace(
'    var here = location.pathname.split("/").pop() || "index.html";',
'    var here = "#/" + (AFBROUTE.name || "index");')

# 3. chrome is rendered once by the router, not on DOMContentLoaded
app = app.replace(
"""  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderChrome);
  } else { renderChrome(); }""",
"""  window.AFB_renderChrome = renderChrome;""")

app = app.replace("    toCSV: toCSV, download: download",
                  "    toCSV: toCSV, download: download, renderChrome: renderChrome")

# page scripts read location.search — give them the route's query instead
for k in routes:
    routes[k]["scripts"] = [
        s.replace("location.search", "AFBROUTE.search")
         .replace("document.addEventListener(", "AFBNAV.on(")
        for s in routes[k]["scripts"]
    ]

ROUTER = r"""
/* ---- single-file router -------------------------------------------------
   Each page's <main> markup and its inline script are stored below. On a
   hash change we swap the markup, abort any listeners the last page
   registered, and re-run the new page's script.
------------------------------------------------------------------------- */
var ROUTES = __ROUTES__;
var AFBROUTE = { name: "index", search: "" };

var AFBNAV = (function () {
  var ctrl = null;
  return {
    reset: function () { if (ctrl) ctrl.abort(); ctrl = new AbortController(); },
    on: function (type, fn) {
      try { document.addEventListener(type, fn, { signal: ctrl.signal }); }
      catch (e) { document.addEventListener(type, fn); }
    }
  };
})();

function parseHash() {
  var h = location.hash.replace(/^#\/?/, "") || "index";
  var i = h.indexOf("?");
  var name = i < 0 ? h : h.slice(0, i);
  var search = i < 0 ? "" : h.slice(i);
  if (!ROUTES[name]) { name = "index"; search = ""; }
  return { name: name, search: search };
}

function go() {
  AFBROUTE = parseHash();
  var r = ROUTES[AFBROUTE.name];
  AFBNAV.reset();

  document.title = r.title;

  // a fresh <main> drops every listener the previous page attached to it
  var old = document.getElementById("main");
  var fresh = document.createElement("main");
  fresh.id = "main";
  if (r.cls) fresh.className = r.cls;
  if (r.style) fresh.setAttribute("style", r.style);
  fresh.innerHTML = r.body;
  old.parentNode.replaceChild(fresh, old);

  AFB.renderChrome();

  r.scripts.forEach(function (src) {
    try { (0, eval)(src); }
    catch (e) { console.error("route script failed:", AFBROUTE.name, e); }
  });

  window.scrollTo(0, 0);
}

// intercept in-document links so the back button still works
document.addEventListener("click", function (e) {
  var a = e.target.closest && e.target.closest('a[href^="#/"]');
  if (!a) return;
  if (a.getAttribute("href") === location.hash) { e.preventDefault(); go(); }
});

window.addEventListener("hashchange", go);
"""

def main_attrs(a):
    cls = re.search(r'class="([^"]*)"', a)
    sty = re.search(r'style="([^"]*)"', a)
    return (cls.group(1) if cls else ""), (sty.group(1) if sty else "")

rdata = {}
for k, v in routes.items():
    cls, sty = main_attrs(v["attrs"])
    rdata[k] = dict(title=v["title"], body=v["body"], scripts=v["scripts"], cls=cls, style=sty)

router = ROUTER.replace("__ROUTES__", json.dumps(rdata))

HTML = """<!DOCTYPE html>
<html lang="en" data-mode="retail">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#F4EDE0">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="AFB">
<title>American Food &amp; Beverage</title>
<meta name="description" content="Wholesale importer, roaster and packer of dried fruits, nuts, seeds, trail mixes and granolas. Paterson, NJ.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Karla:wght@400;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
__CSS__

/* --- standalone-demo additions ------------------------------------------ */
body{ padding-bottom:env(safe-area-inset-bottom) }
.masthead-in{ padding-top:calc(.85rem + env(safe-area-inset-top)) }
@media (max-width:760px){
  .masthead-in{ flex-wrap:wrap; gap:.6rem .9rem }
  .brand{ flex:1 1 auto }
  .nav{ order:3; width:100%; margin-left:0; gap:.9rem;
        overflow-x:auto; -webkit-overflow-scrolling:touch; padding-bottom:.15rem }
  .nav::-webkit-scrollbar{ display:none }
  .nav a{ white-space:nowrap; font-size:.85rem }
  .stamp{ order:1 } .cartlink{ order:2 }
  .hero{ padding-block:2rem 1.5rem }
  .grid{ grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:.7rem }
  .card .body{ padding:.7rem }
  .tablewrap{ max-height:none }
  table.sheet{ font-size:.8rem }
  table.sheet th,table.sheet td{ padding:.45rem .55rem }
  input[type=text],input[type=search],input[type=email],input[type=tel],select,textarea{ font-size:16px }
}
.demoflag{
  background:var(--ink); color:var(--paper); text-align:center;
  font-family:"IBM Plex Mono",monospace; font-size:.62rem; letter-spacing:.14em;
  text-transform:uppercase; padding:.5rem .75rem;
}
.demoflag b{ color:var(--kraft); font-weight:500 }
</style>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="demoflag">Demo build &middot; <b>sample pricing, forms don't send</b></div>
<header data-masthead></header>
<main id="main"></main>
<footer data-footer></footer>

<script>window.AFB_CATALOG=__CATALOG__;window.AFB_JOBS=__JOBS__;window.AFB_SOPS=__SOPS__;window.AFB_DEMO=true;</script>
<script>
__ROUTER__
</script>
<script>
__APP__
</script>
<script>go();</script>
</body>
</html>
"""

out = (HTML
       .replace("__CSS__", css)
       .replace("__CATALOG__", json.dumps(cat, separators=(",", ":")))
       .replace("__JOBS__", json.dumps(jobs, separators=(",", ":")))
       .replace("__SOPS__", json.dumps(sops, separators=(",", ":")))
       .replace("__ROUTER__", router)
       .replace("__APP__", app))

open("afb-demo.html", "w", encoding="utf-8").write(out)
print("afb-demo.html:", round(len(out.encode())/1024), "KB")
