const { copyFileSync } = require("node:fs");
const { join } = require("node:path");
const source = require("swagger-ui-dist").getAbsoluteFSPath();
for (const file of ["swagger-ui-bundle.js", "swagger-ui.css", "LICENSE", "NOTICE"]) {
  copyFileSync(join(source, file), join(__dirname, "dist/docs", file));
}
