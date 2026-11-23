# Claude Code with and without typescript-lsp: attempts combined

Attempts: full, full-a2, full-a3. Each cell is the median of the per-attempt values ± its standard error.

| | No plugin | Plugin | Hook | Plugin and hook |
| --- | --- | --- | --- | --- |
| TypeScript solved (13 tasks) | 92% ± 0 | 85% ± 3 | 92% ± 0 | 77% ± 3 |
| Plain JavaScript solved (12 tasks) | 75% ± 3 | 75% ± 3 | 75% ± 3 | 75% ± 0 |
| TypeScript minus plain JavaScript, same fix-size mix | +29 ± 2 points | +24 ± 4 points | +29 ± 2 points | +14 ± 2 points |
| TypeScript runs shown type errors | 0 of 39 | 0 of 39 | 0 of 39 | 23 of 39 |
| Runs that edited with Edit or Write | 5 of 75 | 5 of 75 | 75 of 75 | 75 of 75 |

Per task, attempts solved (full, full-a2, full-a3):

| Task | Group | No plugin | Plugin | Hook | Plugin and hook |
| --- | --- | --- | --- | --- | --- |
| babel__babel-14532 | ts | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ |
| babel__babel-15445 | ts | 3/3 ✓✓✓ | 1/3 ✓✗✗ | 3/3 ✓✓✓ | 0/3 ✗✗✗ |
| babel__babel-15649 | ts | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ |
| babel__babel-16130 | ts | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ |
| facebook__docusaurus-10130 | ts | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ |
| facebook__docusaurus-10309 | ts | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ |
| facebook__docusaurus-8927 | ts | 0/3 ✗✗✗ | 0/3 ✗✗✗ | 0/3 ✗✗✗ | 0/3 ✗✗✗ |
| facebook__docusaurus-9897 | ts | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ |
| vuejs__core-11589 | ts | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ |
| vuejs__core-11739 | ts | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ |
| vuejs__core-11870 | ts | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ |
| vuejs__core-11899 | ts | 3/3 ✓✓✓ | 1/3 ✗✗✓ | 3/3 ✓✓✓ | 1/3 ✗✗✓ |
| vuejs__core-11915 | ts | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ |
| axios__axios-4731 | plain | 2/3 ✓✓✗ | 2/3 ✓✓✗ | 2/3 ✓✓✗ | 2/3 ✓✓✗ |
| axios__axios-4738 | plain | 0/3 ✗✗✗ | 0/3 ✗✗✗ | 0/3 ✗✗✗ | 0/3 ✗✗✗ |
| axios__axios-5085 | plain | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ |
| axios__axios-5316 | plain | 0/3 ✗✗✗ | 0/3 ✗✗✗ | 0/3 ✗✗✗ | 0/3 ✗✗✗ |
| axios__axios-5892 | plain | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ |
| axios__axios-6539 | plain | 0/3 ✗✗✗ | 0/3 ✗✗✗ | 0/3 ✗✗✗ | 1/3 ✗✗✓ |
| babel__babel-13928 | plain | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ |
| immutable-js__immutable-js-2005 | plain | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ |
| immutable-js__immutable-js-2006 | plain | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ |
| mrdoob__three.js-25687 | plain | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ |
| mrdoob__three.js-26589 | plain | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ |
| mrdoob__three.js-27395 | plain | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ | 3/3 ✓✓✓ |
