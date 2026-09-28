# -*- coding: utf-8 -*-
"""Inject an error reporter into the built app and dump the DOM to find JS errors."""
import io, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SRC = os.path.join(ROOT, "英语分级播放器.html")
DBG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_debug.html")

with io.open(SRC, encoding="utf-8") as f:
    html = f.read()

probe = """
<script>
window.__errs = [];
window.onerror = function(m, s, l, c){ window.__errs.push(m + " @line " + l + ":" + c); };
window.addEventListener("unhandledrejection", function(e){
  window.__errs.push("promise: " + e.reason); });
window.addEventListener("load", function(){
  setTimeout(function(){
    var box = document.createElement("pre");
    box.id = "ERRBOX";
    box.textContent = "ERRORS(" + window.__errs.length + "): " + window.__errs.join(" || ")
      + "  ||| bands children=" + (document.getElementById("bands")||{children:[]}).children.length
      + "  ||| DATA levels=" + (typeof DATA !== "undefined" ? DATA.levels.length : "UNDEF")
      + "  ||| BANDS=" + (typeof BANDS !== "undefined" ? BANDS.length : "UNDEF");
    document.body.appendChild(box);
  }, 800);
});
</script>
"""

html = html.replace("<body>", "<body>" + probe, 1)
with io.open(DBG, "w", encoding="utf-8") as f:
    f.write(html)

out = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                      "--user-data-dir=" + os.path.join(os.path.dirname(DBG), "_cprof"),
                      "--virtual-time-budget=6000", "--dump-dom",
                      "file:///" + DBG.replace("\\", "/")],
                     capture_output=True, text=True, encoding="utf-8", errors="replace")
dom = out.stdout or ""
i = dom.find('id="ERRBOX"')
print(dom[max(0,i-30):i+900] if i >= 0 else "ERRBOX NOT FOUND")
print("\n--- stderr tail ---")
print((out.stderr or "")[-600:])
