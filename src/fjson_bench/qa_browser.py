from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import shutil,threading
from playwright.sync_api import sync_playwright
VIEWPORTS=(1600,768,480)
def run_browser_qa(source,out_dir,interactions=None):
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
                    overflow=page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
                    shot=out_dir/f"viewport-{width}.png"; page.screenshot(path=str(shot),full_page=True); rows.append({"width":width,"interaction_pass":ok,"horizontal_overflow":bool(overflow),"screenshot":str(shot)}); page.close()
            finally: browser.close()
    finally: server.shutdown(); thread.join()
    status="PASS" if all(x["interaction_pass"] and not x["horizontal_overflow"] for x in rows) and not errors and not blocked else "FAIL"
    return {"status":status,"viewports":rows,"console_errors":errors,"blocked_requests":blocked}
