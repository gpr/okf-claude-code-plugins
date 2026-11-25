# Vendored upstream content

Some files in this plugin are copied **verbatim** from the Open Knowledge
Format repository. Do not edit them here: put local overrides in
`skills/okf-spec/SKILL.md` (house rules) instead, so a re-sync stays a plain
copy. `tests/test_vendored.py` fails if a vendored file no longer matches the
hash below.

- Repository: https://github.com/open-knowledge-format/open-knowledge-format
- Commit: `527e81aff55992be21507e97004286789126f88c`
- OKF version: 0.3
- License: Apache License 2.0 — full text in
  [`LICENSE-okf-upstream.md`](LICENSE-okf-upstream.md). The rest of this
  repository is MIT; the vendored files keep their upstream license.

## Files

Each row is `<sha256>  <path in this plugin>  <path upstream>`.

<!-- vendored:begin -->
ac0b0105b71b300c2c2a75d36846b0aeeb14630d5c4a2db98cec3563ee98d0af  skills/okf-generate/SKILL.md  skills/okf-generate/SKILL.md
f5b850051dd162605f07efed162adcbd1e203a65105e16a65e94011d10d3a238  skills/okf-generate/references/attested-computations.md  skills/okf-generate/references/attested-computations.md
09cf7e1c93faa98d4acb99101758b0f5c75a629706810be15e682e68dab187b1  skills/okf-generate/references/frontmatter.md  skills/okf-generate/references/frontmatter.md
3892182f93cfbf0457b3234ee09ed07c06fb2defc6360a1a4b1c84a913b09179  skills/okf-generate/references/migration.md  skills/okf-generate/references/migration.md
55ef992ec10fad7760131c7c6cdd5f9aa4d8c7d1eaea25b6f639f98807ca8f04  skills/okf-generate/references/templates.md  skills/okf-generate/references/templates.md
7f92df7d6a2118a5b7e5c388aa97de48f6ad31b942abc9e2fc7d344830661f49  skills/okf-generate/scripts/validate.py  skills/okf-generate/scripts/validate.py
52c247fb545ce0a5441afd6cd45d72410c7a71a0bd12372c9d2c2c23351eba7e  skills/okf-consume/SKILL.md  skills/okf-consume/SKILL.md
a98fdcd29f6255c497fa17f353e743fda8baea08b7b4a6538da27b32c815c12f  skills/okf-consume/references/trust.md  skills/okf-consume/references/trust.md
18b3d9914faa0248ad6d3dff255cd9c27959c819228ed099b5ffb41be7057e6d  skills/okf-consume/scripts/scan.py  skills/okf-consume/scripts/scan.py
a1fcc51be23fce5c1e4e198f0a71af6046a5286503959caa4009311f74fac3f1  skills/okf-spec/references/SPEC.md  SPEC.md
8c6db340475136df3c1201d458fa5755698eace76e510471ecc9d857d6083dac  LICENSE-okf-upstream.md  LICENSE.md
<!-- vendored:end -->

## Re-sync

From the repository root:

```bash
git clone --depth 1 https://github.com/open-knowledge-format/open-knowledge-format /tmp/okf
cd plugins/okf-core
cp -r /tmp/okf/skills/okf-generate/. skills/okf-generate/
cp -r /tmp/okf/skills/okf-consume/.  skills/okf-consume/
cp /tmp/okf/SPEC.md    skills/okf-spec/references/SPEC.md
cp /tmp/okf/LICENSE.md LICENSE-okf-upstream.md
```

Then:

1. Update the commit above and every hash in the table
   (`sha256sum <path>`); add rows for new upstream files.
2. If `SPEC.md` changed, update the section → line index in
   `skills/okf-spec/SKILL.md`, and re-check its house rules and the
   `okf-search` agent against the new text.
3. If the OKF version changed, follow the version-bump checklist in the
   repository `CLAUDE.md`.
4. Run `python3 -m unittest discover -s plugins/okf-core/tests`.
