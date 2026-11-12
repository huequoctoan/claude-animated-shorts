import fs from "node:fs";
import path from "node:path";
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";

const browserExecutable = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const [frameStr = "100", outFile = "out/test_frame.jpg", compId = "DancingPlague"] = process.argv.slice(2);
const frame = Number(frameStr);

console.log(`Bundling for frame ${frame}...`);
const serveUrl = await bundle({
  entryPoint: path.resolve("src/index.ts"),
  publicDir: path.resolve("public"),
});

console.log(`Selecting composition ${compId}...`);
const composition = await selectComposition({
  serveUrl,
  id: compId,
  browserExecutable,
  chromiumOptions: {
    enableMultiProcessOnLinux: true,
  },
});

console.log("Rendering still frame", frame, "to", outFile);
await renderStill({
  composition,
  serveUrl,
  frame,
  output: outFile,
  imageFormat: "jpeg",
  jpegQuality: 92,
  scale: 0.5,
  browserExecutable,
  onBrowserLog: (l) => {
    console.log(`[Browser ${l.type}]`, l.text);
  },
});

console.log("Render completed successfully:", outFile);
process.exit(0);

