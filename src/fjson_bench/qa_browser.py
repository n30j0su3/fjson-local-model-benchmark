from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import shutil,threading
from PIL import Image,ImageStat
from playwright.sync_api import sync_playwright
VIEWPORTS=(1600,768,480)
def run_browser_qa(source,out_dir,interactions=None,min_mean_luminance=None):
    source=Path(source).resolve(); out_dir=Path(out_dir); out_dir.mkdir(parents=True,exist_ok=True); serve=out_dir/"serve"; serve.mkdir(exist_ok=True); shutil.copy2(source,serve/"index.html")
    handler=partial(SimpleHTTPRequestHandler,directory=str(serve)); server=ThreadingHTTPServer(("127.0.0.1",0),handler); thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start(); rows=[]; errors=[]; blocked=[]
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            try:
                for width in VIEWPORTS:
                    page=browser.new_page(viewport={"width":width,"height":900}); page.on("console",lambda m: errors.append(m.text) if m.type=="error" else None); page.on("pageerror",lambda e: errors.append(str(e)))
                    def route(rt):
                        if rt.request.url.startswith(f"http://127.0.0.1:{server.server_port}"): rt.continue_()
                        else: blocked.append(rt.request.url); rt.abort()
                    page.route("**/*",route); page.goto(f"http://127.0.0.1:{server.server_port}/index.html",wait_until="domcontentloaded")
                    ok=True
                    for a in interactions or []:
                        control=page.locator(a["selector"])
                        select_state=control.evaluate("el => el.tagName === 'SELECT' ? {index: el.selectedIndex, count: el.options.length} : null")
                        if select_state and select_state["count"] > 1:
                            control.select_option(index=(select_state["index"]+1)%select_state["count"])
                        else:
                            control.click()
                        ok=ok and page.locator(a["expect"]).text_content()==a["value"]
                    page.wait_for_timeout(350)
                    page.evaluate("""async () => {
                      const root = document.documentElement;
                      const priorScrollBehavior = root.style.scrollBehavior;
                      root.style.scrollBehavior = 'auto';
                      const step = Math.min(240, Math.max(120, Math.floor(window.innerHeight * 0.25)));
                      const pause = () => new Promise(resolve => setTimeout(resolve, 90));
                      for (let y = 0; y <= root.scrollHeight - window.innerHeight; y += step) {
                        window.scrollTo(0, y);
                        await pause();
                      }
                      window.scrollTo(0, root.scrollHeight);
                      await pause();
                      window.scrollTo(0, 0);
                      root.style.scrollBehavior = priorScrollBehavior;
                    }""")
                    page.wait_for_timeout(700)
                    reveal_state=page.evaluate("""() => {
                      const nodes = [...document.querySelectorAll('.reveal')];
                      const visible = nodes.filter(el => {
                        const style = getComputedStyle(el);
                        return style.display !== 'none' && style.visibility !== 'hidden' && Number(style.opacity) >= 0.5;
                      });
                      return {total: nodes.length, visible: visible.length};
                    }""")
                    overflow=page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
                    shot=out_dir/f"viewport-{width}.png"; page.screenshot(path=str(shot),full_page=True)
                    mean_luminance=round(ImageStat.Stat(Image.open(shot).convert("L")).mean[0],2)
                    visual_pass=min_mean_luminance is None or mean_luminance>=min_mean_luminance
                    failures=[] if visual_pass else [{"code":"LOW_MEAN_LUMINANCE","actual":mean_luminance,"minimum":min_mean_luminance,"width":width}]
                    if reveal_state["total"] and reveal_state["visible"] < reveal_state["total"]:
                        failures.append({"code":"UNREVEALED_CONTENT","actual":reveal_state["visible"],"expected":reveal_state["total"],"width":width})
                        visual_pass=False
                    rows.append({"width":width,"interaction_pass":ok,"horizontal_overflow":bool(overflow),"mean_luminance":mean_luminance,"visual_pass":visual_pass,"reveal_total":reveal_state["total"],"reveal_visible":reveal_state["visible"],"failures":failures,"screenshot":str(shot)}); page.close()
            finally: browser.close()
    finally: server.shutdown(); thread.join()
    status="PASS" if all(x["interaction_pass"] and x["visual_pass"] and not x["horizontal_overflow"] for x in rows) and not errors and not blocked else "FAIL"
    return {"status":status,"minimum_mean_luminance":min_mean_luminance,"viewports":rows,"console_errors":errors,"blocked_requests":blocked}
