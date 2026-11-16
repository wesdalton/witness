import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, existsSync, statSync } from "node:fs";
import { dirname, join, normalize, sep } from "node:path";
import { fileURLToPath } from "node:url";

const dist = join(dirname(fileURLToPath(import.meta.url)), "..", "dist");
const html = readFileSync(join(dist, "index.html"), "utf8");
const css = readFileSync(join(dist, "style.css"), "utf8");

const tags = (name) => [...html.matchAll(new RegExp(`<${name}\\b[^>]*>`, "gi"))].map((m) => m[0]);
const attr = (tag, name) => {
  const m = tag.match(new RegExp(`\\s${name}\\s*=\\s*("([^"]*)"|'([^']*)'|([^\\s>]+))`, "i"));
  return m ? (m[2] ?? m[3] ?? m[4]) : null;
};
const isExternal = (url) => /^(?:[a-z][a-z0-9+.-]*:|\/\/)/i.test(url);
const visibleText = html
  .replace(/<head[\s\S]*?<\/head>/i, "")
  .replace(/<[^>]+>/g, " ")
  .replace(/&nbsp;/g, " ")
  .replace(/\s+/g, " ");

const localRefs = [];
for (const tag of tags("[a-z]+")) {
  for (const name of ["href", "src"]) {
    const value = attr(tag, name);
    if (value !== null && !isExternal(value) && !value.startsWith("#")) localRefs.push(value);
  }
}

test("every local href and src resolves to a file under dist", () => {
  assert.ok(localRefs.length >= 5, "expected stylesheet, icons and images to be referenced");
  for (const ref of localRefs) {
    const path = normalize(join(dist, decodeURIComponent(ref.split(/[?#]/)[0])));
    assert.ok(path.startsWith(dist + sep), `${ref} escapes dist`);
    assert.ok(existsSync(path) && statSync(path).isFile(), `${ref} does not exist under dist`);
  }
});

test("local url() references in the stylesheet resolve", () => {
  for (const [, raw] of css.matchAll(/url\(\s*['"]?([^'")]+)['"]?\s*\)/g)) {
    if (isExternal(raw) || raw.startsWith("#")) continue;
    assert.ok(existsSync(join(dist, raw)), `style.css references missing ${raw}`);
  }
});

test("in-page fragment links point at existing ids", () => {
  const ids = new Set([...html.matchAll(/\sid="([^"]+)"/g)].map((m) => m[1]));
  for (const tag of tags("a")) {
    const href = attr(tag, "href");
    if (href && href.startsWith("#") && href.length > 1) {
      assert.ok(ids.has(href.slice(1)), `no element with id ${href}`);
    }
  }
});

test("no external scripts, stylesheets or fonts", () => {
  for (const tag of tags("script")) {
    const src = attr(tag, "src");
    assert.ok(!src || !isExternal(src), `external script: ${tag}`);
  }
  for (const tag of tags("link")) {
    const rel = (attr(tag, "rel") || "").toLowerCase();
    if (["stylesheet", "preload", "preconnect", "dns-prefetch", "modulepreload"].includes(rel)) {
      assert.ok(!isExternal(attr(tag, "href") || ""), `external resource: ${tag}`);
    }
  }
  assert.doesNotMatch(css, /@import|url\(\s*['"]?(?:https?:)?\/\//i, "stylesheet loads a remote resource");
});

test("headline numbers appear on the page", () => {
  const required = [
    "Exit 0 is not a test run",
    "48/48", "14/48", "43/48", "0/48",
    "191 of 192", "172 of 192", "0/192",
    "0/96", "2,112", "$2.69",
    "8 held-out incidents with 6 independent samples",
  ];
  for (const s of required) assert.ok(visibleText.includes(s), `missing on page: ${s}`);
});

test("links to the GitHub repository", () => {
  const hrefs = tags("a").map((t) => attr(t, "href"));
  assert.ok(hrefs.includes("https://github.com/wesdalton/witness"), "no link to the repository");
});

test("keeps the social preview and icon metadata", () => {
  for (const s of [
    'property="og:title"', 'property="og:description"', 'property="og:image"',
    'name="twitter:card"', 'rel="apple-touch-icon"', 'href="favicon.ico"',
  ]) assert.ok(html.includes(s), `missing ${s}`);
});

test("images carry alt text and the document is labelled", () => {
  assert.match(html, /<html lang="en">/);
  for (const tag of tags("img")) assert.notEqual(attr(tag, "alt"), null, `img without alt: ${tag}`);
  assert.equal(tags("h1").length, 1);
});

test("copy uses no em dashes", () => {
  assert.ok(!html.includes("\u2014") && !html.includes("&mdash;"));
});
