"""The front page's styles: inline, so the page fetches nothing."""

CSS = r"""
:root{--bg:#07070a;--bg2:#0c0c10;--panel:#111116;--panel2:#16161c;--line:#23232b;--line2:#30303a;
--text:#f5f5f0;--dim:#9b9ba4;--faint:#5d5d66;--lime:#c8ff3d;--red:#ff4d4d;--amber:#ffb020;--ink:#07070a;
--moved:#c8ff3d;--same:#3a3a43;--silent:#ff4d4d;--phantom:#ffb020;--ok:#c8ff3d;
--glow:rgba(200,255,61,.22);--rglow:rgba(255,77,77,.22);--shadow:0 1px 0 rgba(255,255,255,.04) inset,0 30px 80px -20px rgba(0,0,0,.7),0 10px 30px -10px rgba(0,0,0,.6);
--ease:cubic-bezier(.16,1,.3,1)}
@media (prefers-color-scheme:light){:root{--bg:#fafaf6;--bg2:#f2f2ec;--panel:#fff;--panel2:#f7f7f2;--line:#e4e4dc;
--line2:#d6d6ce;--text:#0b0b0d;--dim:#5f5f68;--faint:#9a9aa0;--lime:#467f00;--red:#d62828;--amber:#a35f00;--ink:#fff;
--moved:#467f00;--same:#cfcfc8;--silent:#d62828;--phantom:#a35f00;--ok:#467f00;--glow:rgba(110,180,0,.18);
--rglow:rgba(214,40,40,.14);--shadow:0 1px 0 rgba(255,255,255,.8) inset,0 30px 70px -24px rgba(20,20,10,.22),0 8px 24px -12px rgba(20,20,10,.16)}}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--text);overflow-x:hidden;
font:17px/1.6 Inter,-apple-system,BlinkMacSystemFont,"SF Pro Display","Segoe UI",system-ui,sans-serif;
-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
a{color:inherit}::selection{background:var(--lime);color:var(--ink)}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px;position:relative}
section{padding:120px 0;position:relative}
.band{background:linear-gradient(180deg,transparent,var(--bg2) 12%,var(--bg2) 88%,transparent)}
.eyebrow{display:inline-flex;align-items:center;gap:8px;font-size:13px!important;font-weight:900;letter-spacing:.04em;color:var(--lime)!important;margin:0 0 16px!important;text-transform:uppercase;line-height:1.4}
.eyebrow:before{content:"";width:18px;height:2px;border-radius:2px;background:currentColor}
h1,h2,h3{letter-spacing:-.035em;margin:0}
h2{font-size:clamp(34px,5vw,64px);font-weight:900;line-height:1.02;max-width:20ch;margin-bottom:36px}
h3{font-size:20px;font-weight:850;line-height:1.2}

/* ambient light, grid and grain */
.bg{position:fixed;inset:0;z-index:-1;pointer-events:none;overflow:hidden}
.bg:before{content:"";position:absolute;inset:0;
background-image:radial-gradient(color-mix(in srgb,var(--text) 14%,transparent) 1px,transparent 1.4px);background-size:28px 28px;
-webkit-mask-image:radial-gradient(ellipse 70% 55% at 50% 0%,#000 20%,transparent 75%);mask-image:radial-gradient(ellipse 70% 55% at 50% 0%,#000 20%,transparent 75%);opacity:.5}
.bg:after{content:"";position:absolute;inset:-50%;opacity:.06;
background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}
.aur{position:absolute;border-radius:50%;filter:blur(90px);opacity:.55;will-change:transform}
.a1{width:620px;height:620px;left:-140px;top:-220px;background:radial-gradient(closest-side,var(--glow),transparent);animation:drift1 18s ease-in-out infinite alternate}
.a2{width:560px;height:560px;right:-160px;top:40px;background:radial-gradient(closest-side,var(--rglow),transparent);animation:drift2 22s ease-in-out infinite alternate}
.a3{width:900px;height:500px;left:20%;top:560px;background:radial-gradient(closest-side,color-mix(in srgb,var(--lime) 9%,transparent),transparent);animation:drift1 26s ease-in-out infinite alternate-reverse}
@keyframes drift1{to{transform:translate(120px,80px) scale(1.15)}}
@keyframes drift2{to{transform:translate(-140px,120px) scale(.9)}}
.progress{position:fixed;left:0;top:0;height:2px;width:100%;z-index:20;background:var(--lime);transform-origin:0 50%;transform:scaleX(var(--p,0));box-shadow:0 0 12px var(--lime)}

/* nav */
.nav{position:fixed;top:14px;left:0;right:0;z-index:10;display:flex;justify-content:center;padding:0 12px;pointer-events:none}
.nav-in{pointer-events:auto;display:flex;align-items:center;gap:26px;padding:8px 8px 8px 18px;border-radius:999px;
background:color-mix(in srgb,var(--panel) 72%,transparent);backdrop-filter:saturate(1.6) blur(18px);-webkit-backdrop-filter:saturate(1.6) blur(18px);
border:1px solid var(--line);box-shadow:0 10px 40px -12px rgba(0,0,0,.5);transition:background .3s}
.logo{display:flex;align-items:center;gap:10px;font-weight:900;font-size:17px;letter-spacing:-.02em;text-decoration:none}
.mark{width:16px;height:16px;border-radius:4.5px;background:var(--lime);box-shadow:5px 5px 0 -1.5px var(--red)}
.nav nav{display:flex;gap:22px;font-size:14.5px;font-weight:750;color:var(--dim)}
.nav nav a{text-decoration:none;transition:color .2s}.nav nav a:hover{color:var(--text)}

/* buttons */
.btn{position:relative;display:inline-flex;align-items:center;gap:8px;border:0;cursor:pointer;font:inherit;font-size:16px;font-weight:900;
padding:14px 24px;border-radius:999px;background:var(--lime);color:var(--ink);text-decoration:none;white-space:nowrap;overflow:hidden;
transition:transform .25s var(--ease),box-shadow .25s var(--ease),filter .2s}
.btn:hover{transform:translateY(-2px)}
.btn.glow{box-shadow:0 0 0 1px color-mix(in srgb,var(--lime) 60%,transparent),0 8px 30px -6px var(--lime)}
.btn.glow:hover{box-shadow:0 0 0 1px var(--lime),0 12px 44px -6px var(--lime)}
.btn.glow:after{content:"";position:absolute;inset:0;background:linear-gradient(105deg,transparent 35%,rgba(255,255,255,.55) 50%,transparent 65%);transform:translateX(-120%);transition:transform .7s var(--ease)}
.btn.glow:hover:after{transform:translateX(120%)}
.btn.ghost{background:color-mix(in srgb,var(--panel) 60%,transparent);color:var(--text);box-shadow:inset 0 0 0 1px var(--line2);backdrop-filter:blur(8px)}
.btn.ghost:hover{box-shadow:inset 0 0 0 1px var(--dim)}
.btn.sm{font-size:14px;padding:9px 16px}
.btn:disabled{cursor:default;transform:none}
.ctas{display:flex;gap:12px;flex-wrap:wrap}

/* hero */
.hero{padding:170px 0 40px;text-align:center}
.badge{display:inline-flex;align-items:center;gap:10px;margin:0 0 30px;padding:7px 14px 7px 12px;border-radius:999px;font-size:13.5px;font-weight:800;
color:var(--dim);background:color-mix(in srgb,var(--panel) 70%,transparent);border:1px solid var(--line);backdrop-filter:blur(10px);animation:fadeUp .9s var(--ease) both}
.badge i{width:8px;height:8px;border-radius:50%;background:var(--lime);box-shadow:0 0 0 0 var(--lime);animation:pulse 2s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 color-mix(in srgb,var(--lime) 70%,transparent)}70%{box-shadow:0 0 0 10px transparent}100%{box-shadow:0 0 0 0 transparent}}
.hero h1{font-size:clamp(46px,8.4vw,112px);font-weight:900;line-height:.93;letter-spacing:-.05em;word-spacing:.06em;margin:0 auto 30px;max-width:13ch}
.hero h1 .l1,.hero h1 .l2{display:block}
.hero h1 .l2{position:relative;display:inline-block;color:var(--dim)}
.w{display:inline-block;overflow:hidden;vertical-align:top;padding-bottom:.08em;margin-bottom:-.08em}
.w>span{display:inline-block;animation:rise 1.1s var(--ease) both;animation-delay:calc(var(--i) * 70ms + 120ms)}
@keyframes rise{from{transform:translateY(105%) rotate(4deg);filter:blur(8px);opacity:0}to{transform:none;filter:none;opacity:1}}
@keyframes fadeUp{from{opacity:0;transform:translateY(16px);filter:blur(6px)}to{opacity:1;transform:none;filter:none}}
.scribble{position:absolute;left:-2%;right:-2%;bottom:-.12em;width:104%;height:.3em;overflow:visible}
.scribble path{fill:none;stroke:var(--red);stroke-width:7;stroke-linecap:round;stroke-dasharray:460;stroke-dashoffset:460;animation:draw 1.1s var(--ease) 1.25s forwards;filter:drop-shadow(0 0 10px var(--rglow))}
@keyframes draw{to{stroke-dashoffset:0}}
.sub{font-size:clamp(18px,1.7vw,21px);color:var(--dim);max-width:36em;margin:0 auto 38px;animation:fadeUp 1s var(--ease) .7s both}
.hero .ctas{justify-content:center;animation:fadeUp 1s var(--ease) .85s both}

/* the replay window */
.machine-wrap{perspective:1800px;max-width:1180px;margin:76px auto 0;padding:0 20px;animation:fadeUp 1.2s var(--ease) 1s both}
.machine{position:relative;text-align:left;border-radius:22px;background:color-mix(in srgb,var(--panel) 88%,transparent);
border:1px solid var(--line2);box-shadow:var(--shadow),0 0 120px -30px var(--glow);
transform:rotateX(var(--tilt,0deg)) scale(var(--sc,1));transform-origin:50% 0;transition:transform .1s linear;backdrop-filter:blur(20px)}
.machine:before{content:"";position:absolute;inset:-1px;border-radius:inherit;padding:1px;pointer-events:none;
background:linear-gradient(180deg,color-mix(in srgb,var(--lime) 45%,transparent),transparent 40%);
-webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask-composite:exclude}
.m-bar{display:flex;align-items:center;gap:14px;padding:13px 18px;border-bottom:1px solid var(--line);font-size:13.5px}
.dots{display:flex;gap:7px}.dots i{width:11px;height:11px;border-radius:50%;background:var(--line2)}
.dots i:nth-child(1){background:#ff5f57}.dots i:nth-child(2){background:#febc2e}.dots i:nth-child(3){background:#28c840}
.m-title{color:var(--dim);font-weight:700}.m-title b{color:var(--text)}
.m-live{margin-left:auto;display:flex;align-items:center;gap:8px;color:var(--dim);font-weight:750;font-size:12.5px}
.m-live i{width:7px;height:7px;border-radius:50%;background:var(--red);animation:pulse 2s infinite}
.m-body{display:grid;grid-template-columns:1.12fr 56px 1fr;padding:22px;gap:0}
.m-h{display:flex;justify-content:space-between;align-items:baseline;gap:10px;margin:0 0 12px;font-size:12.5px;font-weight:900;text-transform:uppercase;letter-spacing:.04em;color:var(--dim)}
.m-h span{text-transform:none;letter-spacing:0;font-weight:700;color:var(--faint)}
.rows{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:8px}
.row{position:relative;display:grid;grid-template-columns:104px minmax(0,1fr) auto auto;grid-template-areas:"f v t p";align-items:center;column-gap:12px;
padding:11px 14px;border-radius:13px;background:var(--panel2);border:1px solid var(--line);transition:border-color .35s,background .35s,box-shadow .35s,transform .35s var(--ease)}
.row .f{grid-area:f;font:800 13.5px ui-monospace,"SF Mono",Menlo,monospace;color:var(--text)}
.row .val{grid-area:v;font-size:14px;color:var(--dim);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;transition:color .25s}
.pips{grid-area:p;display:flex;gap:5px}
.pips i{width:10px;height:10px;border-radius:3px;border:1.5px solid var(--line2);transition:all .3s var(--ease)}
.pips i.s{background:var(--same);border-color:var(--same)}
.pips i.m{background:var(--moved);border-color:var(--moved);box-shadow:0 0 10px var(--glow)}
.row-tag{grid-area:t;font-size:11px;font-weight:900;text-transform:uppercase;letter-spacing:.03em;white-space:nowrap;padding:3px 9px;border-radius:999px;opacity:0;transform:scale(.8);transition:all .4s var(--ease)}
.row:not([data-verdict]) .row-tag{display:none}
.row[data-verdict] .row-tag{opacity:1;transform:none;background:var(--bg2);border:1px solid var(--line)}
.row[data-verdict="silent passthrough"] .row-tag{background:var(--red);border-color:var(--red);color:#fff!important}
.row[data-verdict="phantom sensitivity"] .row-tag{background:var(--amber);border-color:var(--amber);color:#111!important}
.row.fixed .row-tag{background:var(--lime);border-color:var(--lime);color:var(--ink)!important}
.row[data-verdict="inert"] .row-tag{color:var(--faint)}
.row[data-verdict="load-bearing"] .row-tag{color:var(--lime)}
.row[data-verdict="silent passthrough"] .row-tag{color:var(--red)}
.row[data-verdict="phantom sensitivity"] .row-tag{color:var(--amber)}
.row.active{border-color:var(--text);transform:translateX(6px);box-shadow:0 0 0 4px color-mix(in srgb,var(--text) 8%,transparent)}
.row[data-kind] .val{color:var(--text);font-weight:800}
.row[data-kind="destroy"] .val{color:var(--red);letter-spacing:.06em;animation:glitch .35s steps(2) 2}
.row[data-kind="drop"] .val{text-decoration:line-through;opacity:.7}
.row[data-kind="nudge"] .val{color:var(--amber)}
.row[data-kind]:after{content:attr(data-kind);position:absolute;right:12px;top:-9px;font-size:10.5px;font-weight:900;text-transform:uppercase;letter-spacing:.05em;
padding:2px 8px;border-radius:999px;background:var(--text);color:var(--bg)}
.row.bad{border-color:var(--red);background:color-mix(in srgb,var(--red) 9%,var(--panel2));box-shadow:0 0 0 4px color-mix(in srgb,var(--red) 14%,transparent),0 0 40px -6px var(--rglow);animation:shake .5s}
.row.fixed{border-color:var(--lime);background:color-mix(in srgb,var(--lime) 8%,var(--panel2));box-shadow:0 0 0 4px color-mix(in srgb,var(--lime) 12%,transparent),0 0 40px -6px var(--glow)}
@keyframes glitch{0%{transform:translateX(0);clip-path:inset(0 0 50% 0)}50%{transform:translateX(-3px);clip-path:inset(40% 0 0 0)}100%{transform:none;clip-path:none}}
@keyframes shake{20%{transform:translateX(-6px)}40%{transform:translateX(5px)}60%{transform:translateX(-3px)}80%{transform:translateX(2px)}}
.m-link{position:relative;display:flex;align-items:center}
.m-link span{position:relative;display:block;width:100%;height:2px;margin:0 8px;background:var(--line2);overflow:hidden;border-radius:2px}
.m-link span:after{content:"";position:absolute;inset:0;width:40%;background:linear-gradient(90deg,transparent,var(--lime),transparent);animation:flow 1.4s linear infinite}
@keyframes flow{from{transform:translateX(-100%)}to{transform:translateX(250%)}}
.answer{position:relative;border-radius:16px;padding:16px 18px;background:var(--panel2);border:1px solid var(--line);min-height:150px;transition:border-color .4s,box-shadow .4s,background .4s}
.a-badge{display:inline-block;font-size:11px;font-weight:900;text-transform:uppercase;letter-spacing:.04em;padding:3px 10px;border-radius:999px;background:var(--line);color:var(--dim);margin-bottom:10px;transition:all .3s}
.a-text{margin:0 0 12px;font-size:16px;line-height:1.5}
.a-keys{display:flex;flex-wrap:wrap;gap:8px}
.a-keys span{display:inline-flex;align-items:baseline;gap:7px;font-size:14px;font-weight:850;padding:5px 11px;border-radius:10px;background:var(--bg2);border:1px solid var(--line)}
.a-keys small{font-size:11.5px;font-weight:800;color:var(--faint);text-transform:uppercase;letter-spacing:.03em}
.answer.flash{animation:pop .5s var(--ease)}
@keyframes pop{0%{transform:scale(.985)}100%{transform:none}}
.answer[data-state="moved"]{border-color:var(--lime);box-shadow:0 0 0 3px color-mix(in srgb,var(--lime) 10%,transparent)}
.answer[data-state="moved"] .a-badge,.answer[data-state="right"] .a-badge{background:var(--lime);color:var(--ink)}
.answer[data-state="same"] .a-badge{background:var(--line2);color:var(--text)}
.answer[data-state="wrong"]{border-color:var(--red);box-shadow:0 0 50px -12px var(--rglow)}
.answer[data-state="wrong"] .a-badge{background:var(--red);color:#fff}
.answer[data-state="right"]{border-color:var(--lime);box-shadow:0 0 60px -12px var(--glow)}
.fixcard{margin-top:12px;border-radius:14px;border:1px solid var(--line);background:var(--bg2);padding:12px 14px;opacity:0;transform:translateY(10px);max-height:0;overflow:hidden;
transition:all .6s var(--ease)}
.fixcard.on{opacity:1;transform:none;max-height:200px}
.fixcard pre{margin:0;font:13px/1.7 ui-monospace,"SF Mono",Menlo,monospace;white-space:pre-wrap;word-break:break-word}
.fixcard .del,.fixcard .add{display:block;padding:1px 8px;border-radius:6px}
.fixcard .del{color:var(--red);background:color-mix(in srgb,var(--red) 10%,transparent);text-decoration:line-through;text-decoration-color:color-mix(in srgb,var(--red) 50%,transparent)}
.fixcard .add{color:var(--lime);background:color-mix(in srgb,var(--lime) 10%,transparent);margin-top:4px}
.fixcard.typing .add{animation:type 1.2s steps(40) .5s both}
@keyframes type{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 0 0 0)}}
.m-foot{display:flex;align-items:center;gap:18px;padding:14px 22px 18px;border-top:1px solid var(--line)}
.strip{display:flex;gap:4px;flex-shrink:0}
.strip i{width:14px;height:22px;border-radius:4px;background:var(--bg2);border:1px solid var(--line);transition:all .3s var(--ease)}
.strip i.on{border-color:var(--text);transform:translateY(-3px)}
.strip i.s{background:var(--same);border-color:var(--same)}
.strip i.m{background:var(--moved);border-color:var(--moved);box-shadow:0 0 12px var(--glow)}
.narr{margin:0;flex:1;font-size:15.5px;font-weight:650;color:var(--dim);min-height:2.6em;line-height:1.35;display:block;padding-top:.15em}
.narr b{color:var(--text);font-family:ui-monospace,"SF Mono",Menlo,monospace;font-size:.95em}
.narr em{font-style:normal;font-weight:900;color:var(--text);margin-left:.3em}
.narr em.m{color:var(--lime)}.narr em.r{color:var(--red)}
.replay{font:inherit;font-size:13px;font-weight:850;padding:7px 14px;border-radius:999px;background:transparent;color:var(--dim);border:1px solid var(--line2);cursor:pointer}
.replay:hover{color:var(--text);border-color:var(--dim)}

/* stats */
.stats-s{padding:80px 0 40px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:0;border-block:1px solid var(--line)}
.stats div{padding:30px 24px;border-left:1px solid var(--line)}.stats div:first-child{border-left:0}
.stats b{display:block;font-size:clamp(40px,4.6vw,60px);font-weight:900;letter-spacing:-.05em;line-height:1}
.stats b small{font-size:.42em;letter-spacing:-.02em;color:var(--dim);margin-left:2px}
.stats p{margin:10px 0 0;color:var(--dim);font-size:15px;max-width:22ch}

/* spotlight surfaces */
.spot{position:relative;isolation:isolate}
.spot:after{content:"";position:absolute;inset:0;border-radius:inherit;pointer-events:none;z-index:-1;opacity:0;transition:opacity .3s;
background:radial-gradient(420px circle at var(--mx,50%) var(--my,50%),color-mix(in srgb,var(--lime) 9%,transparent),transparent 45%)}
.spot:hover:after{opacity:1}
.spot:before{content:"";position:absolute;inset:-1px;border-radius:inherit;padding:1px;pointer-events:none;opacity:0;transition:opacity .3s;
background:radial-gradient(260px circle at var(--mx,50%) var(--my,50%),color-mix(in srgb,var(--lime) 70%,transparent),transparent 60%);
-webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask-composite:exclude}
.spot:hover:before{opacity:1}

/* story */
.story{display:grid;grid-template-columns:1fr 1fr;gap:72px;align-items:center}
.story-copy p{color:var(--dim);font-size:18.5px;margin:0 0 18px;max-width:34em}
.story h2{font-size:clamp(32px,4.2vw,54px)}
.quote{margin:30px 0 0;padding:20px 22px;border-radius:18px;background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--red)}
.quote p{margin:0 0 10px!important;color:var(--text)!important;font-size:17px!important;font-weight:700}
.quote a{font-size:14.5px;font-weight:800;color:var(--dim);text-decoration:none}.quote a:hover{color:var(--text)}
.chat{display:flex;flex-direction:column;gap:12px;background:var(--panel);border:1px solid var(--line2);border-radius:24px;padding:18px 20px 22px;box-shadow:var(--shadow)}
.chat-top{display:flex;align-items:center;gap:10px;padding-bottom:12px;border-bottom:1px solid var(--line);margin-bottom:4px;font-size:14px}
.chat-top span:last-child{color:var(--faint);font-weight:700;margin-left:auto;font-size:12.5px}
.av{width:30px;height:30px;border-radius:9px;display:grid;place-items:center;background:var(--text);color:var(--bg);font-weight:900}
.msg,.policy{border-radius:16px;padding:12px 16px;font-size:15.5px;line-height:1.5;max-width:90%}
.who{display:flex;align-items:center;font-size:11.5px;font-weight:900;letter-spacing:.04em;color:var(--dim);margin-bottom:4px;text-transform:uppercase}
.who i{font-style:normal;margin-left:8px;padding:1px 8px;border-radius:999px;font-size:10.5px}
.user{align-self:flex-end;background:var(--text);color:var(--bg);border-bottom-right-radius:5px}.user .who{color:color-mix(in srgb,var(--bg) 60%,transparent)}
.policy{align-self:center;max-width:100%;border:1.5px dashed var(--line2);color:var(--dim);font-size:14px}
.bot{background:var(--panel2);border:1px solid var(--line);border-bottom-left-radius:5px}
.bot.bad{border-color:color-mix(in srgb,var(--red) 60%,var(--line))}.bot.bad i{background:var(--red);color:#fff}
.bot.good{border-color:color-mix(in srgb,var(--lime) 60%,var(--line));box-shadow:0 0 40px -14px var(--glow)}.bot.good i{background:var(--lime);color:var(--ink)}
.js .chat>*:not(.chat-top){opacity:0;transform:translateY(12px) scale(.98)}
.js .chat.in>*{animation:msg .6s var(--ease) both}
.js .chat.in>*:nth-child(2){animation-delay:.1s}.js .chat.in>*:nth-child(3){animation-delay:.7s}
.js .chat.in>*:nth-child(4){animation-delay:1.5s}.js .chat.in>*:nth-child(5){animation-delay:2.6s}
@keyframes msg{to{opacity:1;transform:none}}

/* how it works */
.how{display:grid;grid-template-columns:.8fr 1.2fr;gap:56px;align-items:start}
.steps{list-style:none;padding:0;margin:0}
.steps li{padding:28px 0 28px 26px;border-left:2px solid var(--line);transition:border-color .4s,opacity .4s;min-height:34vh}
.steps li.on{border-color:var(--lime)}
.js .how-on .steps li:not(.on){opacity:.38}
.steps .n{display:block;font:900 14px ui-monospace,"SF Mono",Menlo,monospace;color:var(--lime);margin-bottom:12px}
.steps h3{font-size:26px;margin-bottom:10px}.steps p{margin:0;color:var(--dim);font-size:17px;max-width:30em}
.steps b{color:var(--text)}
.how-side{position:sticky;top:110px}
.how-fig{margin:0;background:var(--panel);border:1px solid var(--line2);border-radius:24px;padding:20px 20px 14px;box-shadow:var(--shadow);overflow:hidden}
.trees{display:grid}.trees .tree{grid-area:1/1;transition:opacity .6s var(--ease),transform .6s var(--ease)}
.tree{overflow-x:auto;-webkit-overflow-scrolling:touch}
.tree svg{display:block;width:100%;height:auto;min-width:560px}.tree svg text{font-family:inherit}
.tree svg>*{transition:opacity .5s var(--ease),stroke .5s,fill .5s}
.t-after{opacity:0;pointer-events:none}
.how-fig[data-step="4"] .t-before{opacity:0}.how-fig[data-step="4"] .t-after{opacity:1}
.how-fig[data-step="1"] .t-before svg>:not(:nth-last-child(-n+2)){opacity:0}
.how-fig[data-step="2"] .t-before path{stroke:var(--same)}
.how-fig[data-step="2"] .t-before rect{fill:var(--panel);stroke:var(--same)}
.how-fig[data-step="2"] .t-before rect:nth-last-child(2){fill:var(--text)}
.how-fig[data-step="2"] .t-before text{fill:var(--dim)}
.how-fig[data-step="2"] .t-before text:last-child{fill:var(--bg)}
.how-fig[data-step="2"] .t-before text[font-size="13"]{opacity:0}
.how-fig figcaption{color:var(--dim);font-size:15px;font-weight:700;padding:12px 6px 4px;min-height:3.2em}
.how-fig figcaption span[data-for]{display:none}
.how-fig[data-step="1"] [data-for="1"],.how-fig[data-step="2"] [data-for="2"],.how-fig[data-step="3"] [data-for="3"],.how-fig[data-step="4"] [data-for="4"]{display:inline}
.swipe{display:none}

/* the two bugs */
.bugs{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.bug{background:var(--panel);border:1px solid var(--line);border-radius:24px;padding:30px;overflow:hidden}
.pill{display:inline-block;font-size:12px;font-weight:900;padding:5px 11px;border-radius:999px;background:var(--red);
color:#fff;margin-bottom:16px;text-transform:uppercase;letter-spacing:.03em;box-shadow:0 0 24px -4px var(--rglow)}
.bug.phantom .pill{background:var(--amber);color:#111;box-shadow:0 0 24px -4px rgba(255,176,32,.35)}
.bug h3{font-size:clamp(24px,2.4vw,30px);line-height:1.15;margin-bottom:18px;letter-spacing:-.03em}.bug p{color:var(--dim);margin:0}
.demo{display:flex;align-items:center;gap:14px;padding:18px;border-radius:16px;background:var(--bg2);border:1px solid var(--line);margin-bottom:18px}
.demo small{display:block;font-size:11px;font-weight:900;color:var(--faint);text-transform:uppercase;letter-spacing:.04em;margin-bottom:6px}
.d-in,.d-out{flex:1;min-width:0}
.d-arrow{color:var(--faint);font-weight:900;font-size:20px}
.d-bar{display:block;height:28px;border-radius:8px;background:var(--panel);border:1px solid var(--line);overflow:hidden}
.d-bar i{display:block;height:100%;width:100%;background:repeating-linear-gradient(90deg,color-mix(in srgb,var(--text) 22%,transparent) 0 6px,transparent 6px 9px);animation:wipe 3.2s var(--ease) infinite}
@keyframes wipe{0%,15%{width:100%}45%,70%{width:0}100%{width:100%}}
.d-out b{display:block;font-size:22px;font-weight:900;letter-spacing:-.03em}
.d-out em{font-style:normal;font-size:12.5px;font-weight:800;color:var(--red)}
.bug.phantom .d-out em{color:var(--amber)}
.d-flip{position:relative;display:block;height:30px;overflow:hidden}
.d-flip b{display:block;height:30px;line-height:30px;font-size:22px;font-weight:900;letter-spacing:-.03em;animation:flip 3.2s var(--ease) infinite}
.d-in .d-flip b{font:800 18px/30px ui-monospace,"SF Mono",Menlo,monospace}
@keyframes flip{0%,35%{transform:translateY(0)}50%,85%{transform:translateY(-100%)}100%{transform:translateY(0)}}

/* try it */
.lead{color:var(--dim);font-size:18.5px;max-width:44em;margin:-18px 0 40px}
.featured{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:72px}
.note{color:var(--dim);font-size:15.5px;max-width:52em;margin:0 0 20px}
.arena{display:grid;grid-template-columns:1fr auto;gap:40px;align-items:center;padding:34px;border-radius:26px;margin-bottom:28px;
background:linear-gradient(135deg,color-mix(in srgb,var(--lime) 7%,var(--panel)),var(--panel) 55%);border:1px solid var(--line2);box-shadow:var(--shadow)}
.arena h3{font-size:clamp(26px,3vw,38px);letter-spacing:-.04em;line-height:1.05;margin-bottom:12px;max-width:18ch}
.arena p{color:var(--dim);margin:0 0 24px;max-width:36em}
.score{position:relative;width:220px;text-align:center}
.ring{width:200px;height:200px;transform:rotate(-90deg);display:block;margin:0 auto}
.ring circle{fill:none;stroke-width:9;stroke-linecap:round}
.r-bg{stroke:var(--line)}
.score:not(.on) .r-ok,.score:not(.on) .r-miss{opacity:0}
.r-ok{stroke:var(--lime);stroke-dasharray:0 327;transition:stroke-dasharray .35s var(--ease);filter:drop-shadow(0 0 6px var(--glow))}
.r-miss{stroke:var(--amber);stroke-dasharray:0 327;transition:stroke-dasharray .35s var(--ease),stroke-dashoffset .35s var(--ease)}
.ring-num{position:absolute;top:0;left:0;right:0;height:200px;display:flex;flex-wrap:wrap;align-content:center;justify-content:center;align-items:baseline}
.ring-num b{font-size:58px;font-weight:900;letter-spacing:-.05em;line-height:1}
.ring-num small{font-size:20px;color:var(--dim);font-weight:800}
.ring-num span{flex-basis:100%;font-size:12.5px;font-weight:850;color:var(--dim);text-transform:uppercase;letter-spacing:.04em;margin-top:6px}
.score-text{margin:10px 0 0;font-weight:800;font-size:13.5px;color:var(--dim);min-height:1.4em}
.score-text small{color:var(--dim);font-weight:700}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:18px}
.chip{font:inherit;font-size:14px;font-weight:800;padding:8px 15px;border-radius:999px;cursor:pointer;
background:transparent;color:var(--dim);border:1px solid var(--line2);transition:all .2s}
.chip:hover{color:var(--text);border-color:var(--dim)}
.chip.on{background:var(--text);color:var(--bg);border-color:var(--text)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}
.card{display:flex;flex-direction:column;background:var(--panel);border:1px solid var(--line);border-radius:18px;
padding:18px 18px 16px;min-width:0;overflow:hidden;transition:border-color .3s,transform .3s var(--ease),box-shadow .3s}
.card:hover{transform:translateY(-3px)}
.card.feat{padding:28px;border-radius:24px}.card.feat h3{font-size:26px}
.card.feat .planted{font-size:16px}
.card.hit{border-color:color-mix(in srgb,var(--lime) 65%,var(--line));box-shadow:0 0 40px -16px var(--glow)}
.card.hit.just{animation:hit .7s var(--ease)}
@keyframes hit{0%{transform:scale(.97)}60%{transform:scale(1.015)}100%{transform:none}}
.card.missed{border-color:color-mix(in srgb,var(--amber) 70%,var(--line))}
.card.running{border-color:var(--line2)}
.card.running .result{position:relative}
.card.running:after{opacity:1!important;background:linear-gradient(100deg,transparent 30%,color-mix(in srgb,var(--lime) 16%,transparent) 50%,transparent 70%)!important;
background-size:250% 100%!important;animation:scan 1s linear infinite}
@keyframes scan{from{background-position:120% 0}to{background-position:-120% 0}}
.card-top{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:8px}
.kicker{font-size:11.5px;font-weight:900;color:var(--dim);text-transform:uppercase;letter-spacing:.04em}
.tag{font-size:11px;font-weight:900;color:var(--dim);border:1px solid var(--line2);border-radius:999px;padding:2px 9px;white-space:nowrap}
.card h3{font-size:18.5px;margin-bottom:3px;line-height:1.25}.card h3 a{text-decoration:none}
.slug{margin:0 0 10px;font:12.5px ui-monospace,"SF Mono",Menlo,monospace;color:var(--faint);word-break:break-all}
.planted{font-size:14.5px;color:var(--dim);margin:0 0 12px}.planted span{font-weight:900;color:var(--text)}
.planted b{color:var(--text)}
.result{font-size:14px;margin-bottom:12px}
.result .ok{color:var(--lime);font-weight:900}.result .miss{color:var(--amber);font-weight:900}
.count{margin:8px 0 0;font-weight:800}.found{list-style:none;margin:6px 0 0;padding:0}.found li{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:4px 0;font-size:13.5px}
.v{font-size:10.5px;font-weight:900;padding:2px 8px;border-radius:999px;text-transform:uppercase;letter-spacing:.02em}
.v.silent{background:var(--red);color:#fff}.v.phantom{background:var(--amber);color:#111}
.card-foot{margin-top:auto;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.card-foot form{margin:0}.muted{color:var(--dim);font-size:14px}
.card.running .btn{opacity:.6;pointer-events:none}
.card.running .result:before{content:"Breaking every input…";color:var(--dim);font-weight:800}
.grid.folded .card:nth-child(n+9){display:none}.more{margin:20px auto 0;display:flex}

/* benchmark */
.bars{display:flex;flex-direction:column;gap:14px;margin-bottom:28px}
.bar{display:grid;grid-template-columns:270px 1fr 130px;gap:22px;align-items:center;background:var(--panel);
border:1px solid var(--line);border-radius:20px;padding:20px 24px}
.bar-label b{display:block;font-size:18px}.bar-label span{font-size:13.5px;color:var(--dim)}
.track{position:relative;height:16px;border-radius:999px;background:var(--bg2);overflow:hidden;border:1px solid var(--line)}
.fill{position:relative;height:100%;width:var(--w);border-radius:999px;background:var(--faint);transition:width 1.6s var(--ease)}
.fill.spread{position:absolute;inset:0 auto 0 0;height:auto;opacity:.4}
.js .bars:not(.in) .fill{width:0}
.bar.us .fill{background:linear-gradient(90deg,color-mix(in srgb,var(--lime) 60%,transparent),var(--lime));box-shadow:0 0 20px var(--glow)}
.bar.us{border-color:color-mix(in srgb,var(--lime) 50%,var(--line));box-shadow:0 0 60px -24px var(--glow)}
.bar-num{text-align:right;font-size:36px;font-weight:900;letter-spacing:-.04em;line-height:1}
.bar-num small{font-size:16px;color:var(--dim)}.bar-num em{display:block;font-style:normal;font-size:12.5px;color:var(--dim);font-weight:750;margin-top:6px;letter-spacing:0}

/* stack */
.bento{display:grid;grid-template-columns:repeat(4,1fr);grid-auto-rows:minmax(190px,auto);gap:14px}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:22px;padding:24px;overflow:hidden;display:flex;flex-direction:column}
.tile.big{grid-column:span 2;grid-row:span 2;background:linear-gradient(160deg,color-mix(in srgb,var(--lime) 8%,var(--panel)),var(--panel) 60%)}
.t-k{font-size:11.5px;font-weight:900;color:var(--lime);text-transform:uppercase;letter-spacing:.05em;padding-bottom:22px}
.tile h3{font-size:22px;margin-bottom:8px}.tile.big h3{font-size:34px;letter-spacing:-.04em}
.tile p{margin:0;color:var(--dim);font-size:15px}.tile.big p{font-size:17px;max-width:30em}
.forkviz{margin-top:auto!important;display:grid;grid-template-columns:auto repeat(7,1fr);grid-template-rows:1fr 1fr;gap:8px;align-items:center;margin-top:28px}
.forkviz b{grid-row:span 2;padding:10px 14px;border-radius:999px;background:var(--text);color:var(--bg);font-size:13px;font-weight:900;margin-right:8px}
.forkviz i{height:26px;border-radius:7px;background:var(--bg2);border:1px solid var(--line2);animation:fk 4s var(--ease) infinite;animation-delay:calc(var(--d) * 110ms)}
@keyframes fk{0%,10%{background:var(--bg2);transform:scale(.85);opacity:.4}25%,80%{background:var(--same);transform:none;opacity:1}100%{opacity:.4;transform:scale(.85)}}
.forkviz i:nth-of-type(10),.forkviz i:nth-of-type(11){animation-name:fkm}
@keyframes fkm{0%,10%{background:var(--bg2);transform:scale(.85);opacity:.4}25%,80%{background:var(--lime);border-color:var(--lime);transform:none;opacity:1;box-shadow:0 0 14px var(--glow)}100%{opacity:.4;transform:scale(.85)}}

/* use it */
.use{display:grid;grid-template-columns:.9fr 1.1fr;gap:56px;align-items:center}.use>div>p{color:var(--dim);margin:0 0 24px;font-size:18px}
.live-note{display:flex;gap:10px;align-items:center;font-size:15px!important;font-weight:750}
.live-note i{width:8px;height:8px;border-radius:50%;background:var(--lime);animation:pulse 2s infinite;flex-shrink:0}
.terms{display:flex;flex-direction:column;gap:14px}
.term{background:#0a0a0d;color:#eaeae4;border:1px solid #26262e;border-radius:18px;box-shadow:var(--shadow);overflow:hidden}
.term .m-bar{border-color:#1f1f26}.term .m-title{color:#8b8b94}
.t-body{margin:0;padding:18px 20px 20px;font:14px/1.75 ui-monospace,"SF Mono",Menlo,Consolas,monospace;white-space:pre-wrap;word-break:break-word;min-height:5.6em}
.t-cmd{display:block}.t-cmd:before{content:"$ ";color:#c8ff3d;font-weight:800}
.t-out{display:block;color:#9b9ba4}.t-out b{color:#f5f5f0}
.t-out .silent{color:#ff4d4d;font-weight:800}.t-out .phantom{color:#ffb020;font-weight:800}.t-out .inert{color:#5d5d66}.t-out .lb{color:#c8ff3d;font-weight:800}
.t-ok{display:block;color:#c8ff3d;font-weight:800}
.caret{display:inline-block;width:8px;height:1.1em;background:#c8ff3d;vertical-align:-3px;animation:blink 1s steps(1) infinite}
@keyframes blink{50%{opacity:0}}

/* closing */
.cta-s{padding:140px 0}
.cta{text-align:center;display:flex;flex-direction:column;align-items:center}
.cta h2{max-width:18ch;font-size:clamp(36px,5.6vw,76px);margin-bottom:40px;letter-spacing:-.05em}
.cta .ctas{justify-content:center}
.cta-s:before{content:"";position:absolute;left:50%;top:50%;width:900px;height:500px;transform:translate(-50%,-50%);pointer-events:none;
background:radial-gradient(closest-side,var(--glow),transparent);filter:blur(40px);opacity:.8}
.foot{padding:32px 0;border-top:1px solid var(--line);color:var(--dim);font-size:14px}
.foot-in{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}

/* scroll reveal */
.js .reveal{opacity:0;transform:translateY(28px);filter:blur(8px);transition:opacity .9s var(--ease),transform .9s var(--ease),filter .9s var(--ease)}
.js .reveal.in{opacity:1;transform:none;filter:none}

@media (max-width:980px){
.m-body{grid-template-columns:1fr;gap:18px}.m-link{display:none}
.story,.use,.bugs,.featured,.how{grid-template-columns:1fr}.how-side{position:static}.steps li{min-height:0;padding:18px 0 18px 22px}
.js .how-on .steps li:not(.on){opacity:1}
.stats{grid-template-columns:1fr 1fr}.stats div:nth-child(3){border-left:0}.stats div:nth-child(n+3){border-top:1px solid var(--line)}
.bento{grid-template-columns:1fr 1fr}.arena{grid-template-columns:1fr}.score{margin:0 auto}
.bar{grid-template-columns:1fr auto}.track{grid-column:1/-1;order:3}section{padding:88px 0}
.nav nav{display:none}}
@media (max-width:620px){
.hero{padding-top:130px}.machine-wrap{padding:0 12px;margin-top:56px}
.m-body{padding:14px}.row{grid-template-columns:84px minmax(0,1fr) auto;grid-template-areas:"f v p" "t t t";padding:10px 12px;row-gap:6px}.row[data-verdict] .row-tag{justify-self:start}
.m-foot{flex-direction:column;align-items:stretch;gap:10px;padding:12px 14px 14px}
.strip{justify-content:space-between}.strip i{flex:1;width:auto}
.m-live{display:none}.bento{grid-template-columns:1fr}.tile.big{grid-column:auto;grid-row:auto}
.stats{grid-template-columns:1fr 1fr}.stats div{padding:22px 14px}
.swipe{display:inline}.bug,.arena{padding:22px}.card.feat{padding:22px}
.nav-in{gap:14px}.forkviz{grid-template-columns:auto repeat(7,1fr);gap:5px}}
@media (prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important}
.js .reveal{opacity:1;transform:none;filter:none}html{scroll-behavior:auto}.scribble path{stroke-dashoffset:0}
.js .chat>*:not(.chat-top){opacity:1;transform:none}.machine{transform:none}}
"""
