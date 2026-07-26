import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const frontendRequire = createRequire(
  path.join(root, "frontend", "package.json"),
);
const Ajv = frontendRequire("ajv");

const schemaPath = path.join(
  root,
  "docs",
  "semantic_ir",
  "editorial_semantic_ir_v1.schema.json",
);
const instancePaths = [
  "docs/semantic_ir/accepted/development_cases.json",
  "docs/semantic_ir/accepted/held_out_cases.json",
  "docs/semantic_ir/held_out_inputs/held_out_cases.json",
];

function loadJson(relativeOrAbsolutePath) {
  const resolved = path.isAbsolute(relativeOrAbsolutePath)
    ? relativeOrAbsolutePath
    : path.join(root, relativeOrAbsolutePath);
  return JSON.parse(fs.readFileSync(resolved, "utf8"));
}

function errorsText(validator) {
  return JSON.stringify(validator.errors ?? [], null, 2);
}

const schema = loadJson(schemaPath);
const ajv = new Ajv({ allErrors: true, schemaId: "auto" });
const validateCorpus = ajv.compile(schema);

for (const instancePath of instancePaths) {
  const valid = validateCorpus(loadJson(instancePath));
  assert.equal(
    valid,
    true,
    `${instancePath} failed Draft-07 validation:\n${errorsText(validateCorpus)}`,
  );
}

const methodBoundary = loadJson(
  "docs/semantic_ir/accepted/development_cases.json",
).cases.flatMap((caseValue) => caseValue.composition.method_boundaries)[0];
assert.ok(methodBoundary, "expected an existing method boundary fixture");
const validateMethodBoundary = ajv.compile(schema.definitions.methodBoundary);
assert.equal(
  validateMethodBoundary(methodBoundary),
  true,
  `method boundary failed Draft-07 validation:\n${errorsText(validateMethodBoundary)}`,
);

const typedConstraint = loadJson(
  "docs/semantic_ir/accepted/held_out_cases.json",
).cases.flatMap(
  (caseValue) => caseValue.shared_semantics.source_render_constraints,
)[0];
assert.ok(typedConstraint, "expected an existing typed source constraint fixture");
const validateSourceConstraint = ajv.compile(
  schema.definitions.sourceRenderConstraint,
);
assert.equal(
  validateSourceConstraint(typedConstraint),
  true,
  `typed source constraint failed Draft-07 validation:\n${errorsText(validateSourceConstraint)}`,
);

const missingEffect = structuredClone(typedConstraint);
delete missingEffect.semantic_effect;
assert.equal(
  validateSourceConstraint(missingEffect),
  false,
  "source constraint without semantic_effect unexpectedly validated",
);
assert.ok(
  validateSourceConstraint.errors?.some(
    (error) =>
      error.keyword === "required" &&
      error.params?.missingProperty === "semantic_effect",
  ),
  `missing semantic_effect did not produce a required error:\n${errorsText(validateSourceConstraint)}`,
);

process.stdout.write(
  JSON.stringify({
    status: "pass",
    draft: "Draft-07",
    validated_instances: instancePaths,
    regressions: {
      method_boundary_without_semantic_effect: "pass",
      source_constraint_without_semantic_effect: "rejected",
      typed_source_constraint: "pass",
      accepted_corpora: "pass",
    },
  }) + "\n",
);
