# -*- coding: utf-8 -*-
"""Report which elements are wider than the viewport, at a given width."""
import io, os, subprocess, sys, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
WIDTH = sys.argv[1] if len(sys.argv) > 1 else "420"

with io.open(os.path.join(ROOT, "index.html"), encoding="utf-8") as f:
    html = f.read()

probe = """
<script>
window.addEventListener("load", function(){
  setTimeout(function(){
    var vw = document.documentElement.clientWidth;
    var out = ["viewport=" + vw,
               "docScrollWidth=" + document.documentElement.scrollWidth,
               "bodyScrollWidth=" + document.body.scrollWidth];
    var bad = [];
    document.querySelectorAll("*").forEach(function(n){
      var r = n.getBoundingClientRect();
      if (r.right > vw + 1 || r.left < -1){
        bad.push(n.tagName + "." + (n.className || "") + "#" + (n.id || "")
          + " L=" + Math.round(r.left) + " R=" + Math.round(r.right)
          + " W=" + Math.round(r.width));
      }
    });
    out.push("OVERFLOWING(" + bad.length + "):");
    out = out.concat(bad.slice(0, 14));
    var pre = document.createElement("pre");
    pre.id = "OVF";
    pre.textContent = out.join("\\n");
    document.body.appendChild(pre);
  }, 700);
});
</script>
"""
html = html.replace("<body>", "<body>" + probe, 1)
tmp = os.path.join(HERE, "_ovf.html")
with io.open(tmp, "w", encoding="utf-8") as f:
    f.write(html)

r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--hide-scrollbars",
                    "--user-data-dir=" + os.path.join(HERE, "_cprof2"),
                    "--virtual-time-budget=6000",
                    "--window-size=%s,900" % WIDTH, "--dump-dom",
                    "file:///" + tmp.replace("\\", "/")],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
dom = r.stdout or ""
i = dom.find('id="OVF"')
if i < 0:
    print("probe did not run")
else:
    seg = dom[i:i + 2600]
    body = re.sub(r"</?pre[^>]*>", "", seg)
    print(body.split("</body>")[0])
