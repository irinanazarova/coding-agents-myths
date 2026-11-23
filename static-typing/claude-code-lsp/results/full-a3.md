# Claude Code with and without typescript-lsp: full-a3

| Condition | Group | Tasks | Solved | Median minutes | Median cost | Runs with an Edit/Write | Runs shown type errors | Runs that ran tsc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lsp | plain | 12 | 8 (67%) | 1.5 | $0.07 | 0 | 0 | 0 |
| lsp | ts | 13 | 11 (85%) | 3.3 | $0.09 | 1 | 0 | 2 |
| lsp-edit | plain | 12 | 9 (75%) | 2.6 | $0.12 | 12 | 1 | 0 |
| lsp-edit | ts | 13 | 11 (85%) | 1.7 | $0.15 | 13 | 7 | 1 |
| nolsp | plain | 12 | 8 (67%) | 2.2 | $0.07 | 0 | 0 | 0 |
| nolsp | ts | 13 | 12 (92%) | 2.1 | $0.1 | 2 | 0 | 3 |
| nolsp-edit | plain | 12 | 8 (67%) | 3.1 | $0.11 | 12 | 0 | 0 |
| nolsp-edit | ts | 13 | 12 (92%) | 2.1 | $0.16 | 13 | 0 | 4 |

| Instance | Condition | Group | Resolved | Minutes | Cost | Edit/Write calls | Hook blocks | Type errors shown | LSP sets reported / delivered | tsc runs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| axios__axios-4731 | lsp | plain | false | 0.5 | $0.07 | 0 | 0 | 0 | 0 / 0 | 0 |
| axios__axios-4731 | lsp-edit | plain | false | 1.1 | $0.1 | 3 | 2 | 0 | 2 / 0 | 0 |
| axios__axios-4731 | nolsp | plain | false | 0.4 | $0.05 | 0 | 0 | 0 | 0 / 0 | 0 |
| axios__axios-4731 | nolsp-edit | plain | false | 3.7 | $0.18 | 3 | 2 | 0 | 0 / 0 | 0 |
| axios__axios-4738 | lsp | plain | false | 0.4 | $0.05 | 0 | 0 | 0 | 0 / 0 | 0 |
| axios__axios-4738 | lsp-edit | plain | false | 7.3 | $0.2 | 3 | 2 | 0 | 12 / 2 | 0 |
| axios__axios-4738 | nolsp | plain | false | 13.4 | $0.15 | 0 | 0 | 0 | 0 / 0 | 0 |
| axios__axios-4738 | nolsp-edit | plain | false | 2.7 | $0.11 | 1 | 1 | 0 | 0 / 0 | 0 |
| axios__axios-5085 | lsp | plain | true | 12.6 | $0.13 | 0 | 0 | 0 | 0 / 0 | 0 |
| axios__axios-5085 | lsp-edit | plain | true | 13.2 | $0.23 | 7 | 2 | 0 | 10 / 1 | 0 |
| axios__axios-5085 | nolsp | plain | true | 3.9 | $0.16 | 0 | 0 | 0 | 0 / 0 | 0 |
| axios__axios-5085 | nolsp-edit | plain | true | 12.6 | $0.13 | 2 | 1 | 0 | 0 / 0 | 0 |
| axios__axios-5316 | lsp | plain | false | 13.1 | $0.29 | 0 | 0 | 0 | 0 / 0 | 0 |
| axios__axios-5316 | lsp-edit | plain | false | 13.4 | $0.33 | 6 | 2 | 0 | 6 / 1 | 0 |
| axios__axios-5316 | nolsp | plain | false | 6.0 | $0.29 | 0 | 0 | 0 | 0 / 0 | 0 |
| axios__axios-5316 | nolsp-edit | plain | false | 21.8 | $0.41 | 6 | 1 | 0 | 0 / 0 | 0 |
| axios__axios-5892 | lsp | plain | true | 0.2 | $0.03 | 0 | 0 | 0 | 0 / 0 | 0 |
| axios__axios-5892 | lsp-edit | plain | true | 0.3 | $0.07 | 1 | 1 | 0 | 0 / 0 | 0 |
| axios__axios-5892 | nolsp | plain | true | 0.2 | $0.02 | 0 | 0 | 0 | 0 / 0 | 0 |
| axios__axios-5892 | nolsp-edit | plain | true | 0.4 | $0.04 | 1 | 1 | 0 | 0 / 0 | 0 |
| axios__axios-6539 | lsp | plain | false | 2.4 | $0.1 | 0 | 0 | 0 | 0 / 0 | 0 |
| axios__axios-6539 | lsp-edit | plain | true | 1.9 | $0.12 | 3 | 2 | 0 | 0 / 0 | 0 |
| axios__axios-6539 | nolsp | plain | false | 1.8 | $0.06 | 0 | 0 | 0 | 0 / 0 | 0 |
| axios__axios-6539 | nolsp-edit | plain | false | 1.8 | $0.11 | 2 | 1 | 0 | 0 / 0 | 0 |
| babel__babel-13928 | lsp | plain | true | 8.5 | $0.2 | 0 | 0 | 0 | 0 / 0 | 0 |
| babel__babel-13928 | lsp-edit | plain | true | 4.5 | $0.15 | 2 | 3 | 10 | 10 / 1 | 0 |
| babel__babel-13928 | nolsp | plain | true | 5.3 | $0.15 | 0 | 0 | 0 | 0 / 0 | 0 |
| babel__babel-13928 | nolsp-edit | plain | true | 11.5 | $0.18 | 3 | 3 | 0 | 0 / 0 | 0 |
| babel__babel-14532 | lsp | ts | true | 4.5 | $0.09 | 0 | 0 | 0 | 0 / 0 | 0 |
| babel__babel-14532 | lsp-edit | ts | true | 1.7 | $0.1 | 2 | 1 | 7 | 1 / 1 | 0 |
| babel__babel-14532 | nolsp | ts | true | 3.2 | $0.23 | 0 | 0 | 0 | 0 / 0 | 0 |
| babel__babel-14532 | nolsp-edit | ts | true | 3.5 | $0.23 | 3 | 2 | 0 | 0 / 0 | 0 |
| babel__babel-15445 | lsp | ts | false | 3.9 | $0.06 | 0 | 0 | 0 | 0 / 0 | 0 |
| babel__babel-15445 | lsp-edit | ts | false | 0.5 | $0.11 | 1 | 1 | 0 | 0 / 0 | 0 |
| babel__babel-15445 | nolsp | ts | true | 2.1 | $0.05 | 0 | 0 | 0 | 0 / 0 | 0 |
| babel__babel-15445 | nolsp-edit | ts | true | 2.1 | $0.09 | 1 | 1 | 0 | 0 / 0 | 0 |
| babel__babel-15649 | lsp | ts | true | 3.4 | $0.07 | 0 | 0 | 0 | 0 / 0 | 0 |
| babel__babel-15649 | lsp-edit | ts | true | 4.0 | $0.22 | 2 | 1 | 9 | 3 / 1 | 0 |
| babel__babel-15649 | nolsp | ts | true | 2.6 | $0.07 | 1 | 0 | 0 | 0 / 0 | 0 |
| babel__babel-15649 | nolsp-edit | ts | true | 3.7 | $0.15 | 1 | 1 | 0 | 0 / 0 | 0 |
| babel__babel-16130 | lsp | ts | true | 3.3 | $0.14 | 0 | 0 | 0 | 0 / 0 | 0 |
| babel__babel-16130 | lsp-edit | ts | true | 3.6 | $0.2 | 1 | 1 | 10 | 3 / 1 | 0 |
| babel__babel-16130 | nolsp | ts | true | 3.6 | $0.16 | 1 | 0 | 0 | 0 / 0 | 0 |
| babel__babel-16130 | nolsp-edit | ts | true | 1.6 | $0.21 | 2 | 1 | 0 | 0 / 0 | 0 |
| facebook__docusaurus-10130 | lsp | ts | true | 0.9 | $0.07 | 0 | 0 | 0 | 0 / 0 | 0 |
| facebook__docusaurus-10130 | lsp-edit | ts | true | 1.0 | $0.12 | 1 | 1 | 0 | 0 / 0 | 0 |
| facebook__docusaurus-10130 | nolsp | ts | true | 0.9 | $0.12 | 0 | 0 | 0 | 0 / 0 | 0 |
| facebook__docusaurus-10130 | nolsp-edit | ts | true | 0.7 | $0.13 | 1 | 1 | 0 | 0 / 0 | 0 |
| facebook__docusaurus-10309 | lsp | ts | true | 0.8 | $0.05 | 0 | 0 | 0 | 0 / 0 | 0 |
| facebook__docusaurus-10309 | lsp-edit | ts | true | 1.0 | $0.08 | 1 | 1 | 0 | 0 / 0 | 0 |
| facebook__docusaurus-10309 | nolsp | ts | true | 1.3 | $0.08 | 0 | 0 | 0 | 0 / 0 | 1 |
| facebook__docusaurus-10309 | nolsp-edit | ts | true | 1.2 | $0.14 | 2 | 1 | 0 | 0 / 0 | 0 |
| facebook__docusaurus-8927 | lsp | ts | false | 4.4 | $0.18 | 0 | 0 | 0 | 0 / 0 | 0 |
| facebook__docusaurus-8927 | lsp-edit | ts | false | 1.6 | $0.14 | 2 | 2 | 0 | 0 / 0 | 0 |
| facebook__docusaurus-8927 | nolsp | ts | false | 1.9 | $0.09 | 0 | 0 | 0 | 0 / 0 | 0 |
| facebook__docusaurus-8927 | nolsp-edit | ts | false | 1.0 | $0.14 | 1 | 1 | 0 | 0 / 0 | 0 |
| facebook__docusaurus-9897 | lsp | ts | true | 1.0 | $0.1 | 0 | 0 | 0 | 0 / 0 | 0 |
| facebook__docusaurus-9897 | lsp-edit | ts | true | 1.4 | $0.17 | 1 | 3 | 0 | 1 / 1 | 0 |
| facebook__docusaurus-9897 | nolsp | ts | true | 1.1 | $0.13 | 0 | 0 | 0 | 0 / 0 | 0 |
| facebook__docusaurus-9897 | nolsp-edit | ts | true | 1.8 | $0.21 | 3 | 2 | 0 | 0 / 0 | 3 |
| immutable-js__immutable-js-2005 | lsp | plain | true | 2.6 | $0.12 | 0 | 0 | 0 | 0 / 0 | 0 |
| immutable-js__immutable-js-2005 | lsp-edit | plain | true | 3.2 | $0.17 | 2 | 1 | 0 | 0 / 0 | 0 |
| immutable-js__immutable-js-2005 | nolsp | plain | true | 3.1 | $0.11 | 0 | 0 | 0 | 0 / 0 | 0 |
| immutable-js__immutable-js-2005 | nolsp-edit | plain | true | 3.4 | $0.13 | 2 | 1 | 0 | 0 / 0 | 0 |
| immutable-js__immutable-js-2006 | lsp | plain | true | 2.4 | $0.06 | 0 | 0 | 0 | 0 / 0 | 0 |
| immutable-js__immutable-js-2006 | lsp-edit | plain | true | 3.6 | $0.11 | 2 | 3 | 0 | 3 / 1 | 0 |
| immutable-js__immutable-js-2006 | nolsp | plain | true | 2.5 | $0.07 | 0 | 0 | 0 | 0 / 0 | 0 |
| immutable-js__immutable-js-2006 | nolsp-edit | plain | true | 3.4 | $0.11 | 2 | 2 | 0 | 0 / 0 | 0 |
| mrdoob__three.js-25687 | lsp | plain | true | 0.7 | $0.05 | 0 | 0 | 0 | 0 / 0 | 0 |
| mrdoob__three.js-25687 | lsp-edit | plain | true | 0.7 | $0.07 | 2 | 1 | 0 | 0 / 0 | 0 |
| mrdoob__three.js-25687 | nolsp | plain | true | 0.6 | $0.03 | 0 | 0 | 0 | 0 / 0 | 0 |
| mrdoob__three.js-25687 | nolsp-edit | plain | true | 0.8 | $0.06 | 2 | 1 | 0 | 0 / 0 | 0 |
| mrdoob__three.js-26589 | lsp | plain | true | 0.5 | $0.03 | 0 | 0 | 0 | 0 / 0 | 0 |
| mrdoob__three.js-26589 | lsp-edit | plain | true | 0.6 | $0.06 | 3 | 1 | 0 | 0 / 0 | 0 |
| mrdoob__three.js-26589 | nolsp | plain | true | 0.6 | $0.03 | 0 | 0 | 0 | 0 / 0 | 0 |
| mrdoob__three.js-26589 | nolsp-edit | plain | true | 0.5 | $0.07 | 3 | 1 | 0 | 0 / 0 | 0 |
| mrdoob__three.js-27395 | lsp | plain | true | 0.3 | $0.02 | 0 | 0 | 0 | 0 / 0 | 0 |
| mrdoob__three.js-27395 | lsp-edit | plain | true | 0.4 | $0.03 | 1 | 1 | 0 | 0 / 0 | 0 |
| mrdoob__three.js-27395 | nolsp | plain | true | 0.3 | $0.02 | 0 | 0 | 0 | 0 / 0 | 0 |
| mrdoob__three.js-27395 | nolsp-edit | plain | true | 0.3 | $0.04 | 1 | 1 | 0 | 0 / 0 | 0 |
| vuejs__core-11589 | lsp | ts | true | 22.1 | $0.25 | 0 | 0 | 0 | 0 / 0 | 2 |
| vuejs__core-11589 | lsp-edit | ts | true | 23.4 | $0.42 | 6 | 1 | 0 | 0 / 0 | 0 |
| vuejs__core-11589 | nolsp | ts | true | 8.7 | $0.21 | 0 | 0 | 0 | 0 / 0 | 3 |
| vuejs__core-11589 | nolsp-edit | ts | true | 16.4 | $0.39 | 5 | 1 | 0 | 0 / 0 | 1 |
| vuejs__core-11739 | lsp | ts | true | 4.2 | $0.38 | 0 | 0 | 0 | 0 / 0 | 1 |
| vuejs__core-11739 | lsp-edit | ts | true | 6.2 | $0.39 | 9 | 2 | 4 | 2 / 2 | 2 |
| vuejs__core-11739 | nolsp | ts | true | 4.9 | $0.45 | 0 | 0 | 0 | 0 / 0 | 1 |
| vuejs__core-11739 | nolsp-edit | ts | true | 5.5 | $0.53 | 9 | 4 | 0 | 0 / 0 | 1 |
| vuejs__core-11870 | lsp | ts | true | 0.7 | $0.06 | 0 | 0 | 0 | 0 / 0 | 0 |
| vuejs__core-11870 | lsp-edit | ts | true | 0.8 | $0.09 | 3 | 1 | 3 | 1 / 1 | 0 |
| vuejs__core-11870 | nolsp | ts | true | 0.6 | $0.05 | 0 | 0 | 0 | 0 / 0 | 0 |
| vuejs__core-11870 | nolsp-edit | ts | true | 2.4 | $0.16 | 6 | 2 | 0 | 0 / 0 | 1 |
| vuejs__core-11899 | lsp | ts | true | 1.1 | $0.12 | 0 | 0 | 0 | 0 / 0 | 0 |
| vuejs__core-11899 | lsp-edit | ts | true | 3.6 | $0.21 | 4 | 1 | 5 | 3 / 1 | 0 |
| vuejs__core-11899 | nolsp | ts | true | 0.9 | $0.1 | 0 | 0 | 0 | 0 / 0 | 0 |
| vuejs__core-11899 | nolsp-edit | ts | true | 0.9 | $0.14 | 3 | 1 | 0 | 0 / 0 | 0 |
| vuejs__core-11915 | lsp | ts | true | 2.8 | $0.08 | 1 | 0 | 0 | 0 / 0 | 0 |
| vuejs__core-11915 | lsp-edit | ts | true | 3.6 | $0.15 | 4 | 1 | 1 | 1 / 1 | 0 |
| vuejs__core-11915 | nolsp | ts | true | 3.4 | $0.07 | 0 | 0 | 0 | 0 / 0 | 0 |
| vuejs__core-11915 | nolsp-edit | ts | true | 7.9 | $0.16 | 3 | 2 | 0 | 0 / 0 | 0 |
