const CACHE_NAME = "fast_io-docs-v31.2"; // bump version here
const urlsToCache = [
  "/",
  "/style.css",
  "/script.js",
  "/sw-register.js",
  "/manifest.json",
  "/icons/logo.webp",
  "/docs/00.intro/",
  "/docs/00.intro/01.fastio/",
  // "/docs/api/",
  "/docs/01.compile/",
  "/docs/01.compile/01.pwastore/",
  "/docs/01.compile/01.pwastore/01.webp",
  "/docs/01.compile/01.pwastore/02.webp",
  "/docs/01.compile/01.pwastore/03.webp",
  "/docs/01.compile/02.vscode/",
  "/docs/01.compile/02.vscode/autosavedisable.webp",
  "/docs/01.compile/03.compilers/",
  "/docs/01.compile/04.clang/",
  "/docs/01.compile/05.testinstallation/",
  "/docs/01.compile/06.gcc/",
  "/docs/01.compile/07.msvc/",
  "/docs/01.compile/08.fastio/",
  "/docs/02.basics/",
  "/docs/02.basics/01.helloworld/",
  "/docs/02.basics/02.datatypes/",
  "/docs/02.basics/02.datatypes/01.ascii/",
  "/docs/02.basics/03.literals/",
  "/docs/02.basics/04.initialization/",
  "/docs/02.basics/05.assignment/",
  "/docs/02.basics/06.operators/",
  "/docs/02.basics/07.sizeof/",
  "/docs/02.basics/08.const/",
  "/docs/02.basics/09.reference/",
  "/docs/02.basics/10.auto/",
  "/docs/02.basics/11.decltype/",
  "/docs/02.basics/12.decltypeauto/",
  "/docs/02.basics/13.casting/",
  "/docs/02.basics/14.a+b/",
  "/docs/02.basics/15.limits/",
  "/docs/02.basics/16.enumclass/",
  "/docs/02.basics/17.bit/",
  "/docs/02.basics/18.endian/",
  "/docs/02.basics/19.usingtypedef/",
  "/docs/02.basics/20.byte/",
  "/docs/03.statements/",
  "/docs/03.statements/01.empty/",
  "/docs/03.statements/02.compound/",
  "/docs/03.statements/03.if/",
  "/docs/03.statements/04.while/",
  "/docs/03.statements/05.for/",
  "/docs/03.statements/06.break/",
  "/docs/03.statements/07.continue/",
  "/docs/03.statements/08.dowhile/",
  "/docs/03.statements/09.switch/",
  "/docs/03.statements/10.goto/",
  "/docs/03.statements/11.preprocessor/",
  "/docs/03.statements/12.ifdefifndef/",
  "/docs/03.statements/13.attribute/",
  "/docs/03.statements/14.stringify/",
  "/docs/03.statements/15.featuretesting/",
  "/docs/04.dsal/",
  "/docs/04.dsal/01.string/",
  "/docs/04.dsal/02.char_category/",
  "/docs/04.dsal/03.vector/",
  "/docs/04.dsal/04.array/",
  "/docs/04.dsal/05.multidcontainers/",
  "/docs/05.pointerscarray/",
  "/docs/05.pointerscarray/01.address/",
  "/docs/05.pointerscarray/02.pointerbasics/",
  "/docs/05.pointerscarray/03.dereference/",
  "/docs/05.pointerscarray/04.nullptr/",
  "/docs/05.pointerscarray/05.cstylearray/",
  "/docs/05.pointerscarray/06.pointerarithmetic/",
  "/docs/05.pointerscarray/07.carraydecay/",
  "/docs/05.pointerscarray/08.cstylestring/",
  "/docs/05.pointerscarray/09.multidim/",
  "/docs/05.pointerscarray/10.constpointer/",
  "/docs/05.pointerscarray/11.voidpointer/",
  "/docs/05.pointerscarray/12.pointersandcontainers/",
  "/docs/05.pointerscarray/13.strictaliasing/",
  "/docs/05.pointerscarray/14.memfunctions/",
  "/docs/05.pointerscarray/15.pointerpitfalls/",
  "/docs/05.pointerscarray/16.pointerbestpractices/",
];

// Install: pre-cache resources
self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
  self.skipWaiting(); // activate new worker immediately
});

// Activate: remove old caches
self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(key => key !== CACHE_NAME)
            .map(key => caches.delete(key))
      )
    )
  );
  self.clients.claim(); // take control of all pages
});

// Fetch: cache-first with network fallback
self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request);
    })
  );
});

// Listen for messages from the client
self.addEventListener("message", event => {
  if (event.data === "SKIP_WAITING") {
    self.skipWaiting();
  }
});
