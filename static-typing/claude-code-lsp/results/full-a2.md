# Claude Code with and without typescript-lsp: full-a2

| Condition | Group | Tasks | Solved | Median minutes | Median cost | Runs with an Edit/Write | Runs shown type errors | Runs that ran tsc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lsp | plain | 12 | 9 (75%) | 1.6 | $0.09 | 1 | 0 | 0 |
| lsp | ts | 13 | 10 (77%) | 1.4 | $0.1 | 1 | 0 | 2 |
| lsp-edit | plain | 12 | 9 (75%) | 1.2 | $0.14 | 12 | 1 | 0 |
| lsp-edit | ts | 13 | 10 (77%) | 2.0 | $0.16 | 13 | 8 | 0 |
| nolsp | plain | 12 | 9 (75%) | 0.9 | $0.06 | 1 | 0 | 0 |
| nolsp | ts | 13 | 12 (92%) | 1.2 | $0.09 | 1 | 0 | 1 |
| nolsp-edit | plain | 12 | 9 (75%) | 1.1 | $0.13 | 12 | 0 | 0 |
| nolsp-edit | ts | 13 | 12 (92%) | 2.2 | $0.14 | 13 | 0 | 2 |

| Instance | Condition | Group | Resolved | Minutes | Cost | Edit/Write calls | Hook blocks | Type errors shown | LSP sets reported / delivered | tsc runs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| axios__axios-4731 | lsp | plain | true | 0.6 | $0.06 | 0 | 0 | 0 | 0 / 0 | 0 |
| axios__axios-4731 | lsp-edit | plain | true | 1.0 | $0.09 | 2 | 2 | 0 | 0 / 0 | 0 |
| axios__axios-4731 | nolsp | plain | true | 0.3 | $0.05 | 1 | 0 | 0 | 0 / 0 | 0 |
| axios__axios-4731 | nolsp-edit | plain | true | 0.5 | $0.1 | 1 | 1 | 0 | 0 / 0 | 0 |
| axios__axios-4738 | lsp | plain | false | 3.1 | $0.11 | 0 | 0 | 0 | 0 / 0 | 0 |
| axios__axios-4738 | lsp-edit | plain | false | 0.8 | $0.17 | 2 | 3 | 0 | 3 / 2 | 0 |
| axios__axios-4738 | nolsp | plain | false | 0.4 | $0.04 | 0 | 0 | 0 | 0 / 0 | 0 |
| axios__axios-4738 | nolsp-edit | plain | false | 0.6 | $0.1 | 2 | 2 | 0 | 0 / 0 | 0 |
| axios__axios-5085 | lsp | plain | true | 4.5 | $0.15 | 0 | 0 | 0 | 0 / 0 | 0 |
| axios__axios-5085 | lsp-edit | plain | true | 4.2 | $0.25 | 6 | 1 | 0 | 11 / 2 | 0 |
| axios__axios-5085 | nolsp | plain | true | 4.4 | $0.16 | 0 | 0 | 0 | 0 / 0 | 0 |
| axios__axios-5085 | nolsp-edit | plain | true | 12.8 | $0.26 | 5 | 1 | 0 | 0 / 0 | 0 |
| axios__axios-5316 | lsp | plain | false | 5.4 | $0.37 | 0 | 0 | 0 | 0 / 0 | 0 |
| axios__axios-5316 | lsp-edit | plain | false | 5.7 | $0.46 | 7 | 2 | 0 | 11 / 2 | 0 |
| axios__axios-5316 | nolsp | plain | false | 5.8 | $0.32 | 0 | 0 | 0 | 0 / 0 | 0 |
| axios__axios-5316 | nolsp-edit | plain | false | 15.5 | $0.42 | 6 | 2 | 0 | 0 / 0 | 0 |
| axios__axios-5892 | lsp | plain | true | 0.3 | $0.03 | 0 | 0 | 0 | 0 / 0 | 0 |
| axios__axios-5892 | lsp-edit | plain | true | 0.3 | $0.08 | 1 | 1 | 0 | 0 / 0 | 0 |
| axios__axios-5892 | nolsp | plain | true | 0.3 | $0.03 | 0 | 0 | 0 | 0 / 0 | 0 |
| axios__axios-5892 | nolsp-edit | plain | true | 0.3 | $0.04 | 1 | 1 | 0 | 0 / 0 | 0 |
| axios__axios-6539 | lsp | plain | false | 1.8 | $0.11 | 0 | 0 | 0 | 0 / 0 | 0 |
| axios__axios-6539 | lsp-edit | plain | false | 1.8 | $0.15 | 1 | 1 | 0 | 4 / 1 | 0 |
| axios__axios-6539 | nolsp | plain | false | 3.0 | $0.08 | 0 | 0 | 0 | 0 / 0 | 0 |
| axios__axios-6539 | nolsp-edit | plain | false | 3.1 | $0.15 | 2 | 1 | 0 | 0 / 0 | 0 |
| babel__babel-13928 | lsp | plain | true | 3.4 | $0.12 | 0 | 0 | 0 | 0 / 0 | 0 |
| babel__babel-13928 | lsp-edit | plain | true | 1.4 | $0.2 | 2 | 4 | 20 | 10 / 2 | 0 |
| babel__babel-13928 | nolsp | plain | true | 3.3 | $0.09 | 0 | 0 | 0 | 0 / 0 | 0 |
| babel__babel-13928 | nolsp-edit | plain | true | 1.4 | $0.15 | 2 | 3 | 0 | 0 / 0 | 0 |
| babel__babel-14532 | lsp | ts | true | 3.4 | $0.09 | 0 | 0 | 0 | 0 / 0 | 0 |
| babel__babel-14532 | lsp-edit | ts | true | 3.3 | $0.14 | 2 | 1 | 7 | 1 / 1 | 0 |
| babel__babel-14532 | nolsp | ts | true | 6.3 | $0.18 | 0 | 0 | 0 | 0 / 0 | 0 |
| babel__babel-14532 | nolsp-edit | ts | true | 2.2 | $0.21 | 5 | 2 | 0 | 0 / 0 | 0 |
| babel__babel-15445 | lsp | ts | false | 5.7 | $0.09 | 0 | 0 | 0 | 0 / 0 | 0 |
| babel__babel-15445 | lsp-edit | ts | false | 1.9 | $0.11 | 3 | 2 | 0 | 4 / 1 | 0 |
| babel__babel-15445 | nolsp | ts | true | 0.4 | $0.04 | 0 | 0 | 0 | 0 / 0 | 0 |
| babel__babel-15445 | nolsp-edit | ts | true | 2.3 | $0.05 | 1 | 1 | 0 | 0 / 0 | 0 |
| babel__babel-15649 | lsp | ts | true | 3.2 | $0.11 | 0 | 0 | 0 | 0 / 0 | 0 |
| babel__babel-15649 | lsp-edit | ts | true | 3.5 | $0.16 | 1 | 1 | 9 | 4 / 1 | 0 |
| babel__babel-15649 | nolsp | ts | true | 4.4 | $0.12 | 0 | 0 | 0 | 0 / 0 | 0 |
| babel__babel-15649 | nolsp-edit | ts | true | 3.7 | $0.11 | 1 | 1 | 0 | 0 / 0 | 0 |
| babel__babel-16130 | lsp | ts | true | 3.4 | $0.15 | 0 | 0 | 0 | 0 / 0 | 0 |
| babel__babel-16130 | lsp-edit | ts | true | 2.3 | $0.18 | 1 | 1 | 0 | 0 / 0 | 0 |
| babel__babel-16130 | nolsp | ts | true | 2.0 | $0.14 | 0 | 0 | 0 | 0 / 0 | 0 |
| babel__babel-16130 | nolsp-edit | ts | true | 3.8 | $0.19 | 1 | 1 | 0 | 0 / 0 | 0 |
| facebook__docusaurus-10130 | lsp | ts | true | 1.4 | $0.14 | 0 | 0 | 0 | 0 / 0 | 1 |
| facebook__docusaurus-10130 | lsp-edit | ts | true | 1.1 | $0.08 | 1 | 1 | 1 | 1 / 1 | 0 |
| facebook__docusaurus-10130 | nolsp | ts | true | 0.6 | $0.05 | 1 | 0 | 0 | 0 / 0 | 0 |
| facebook__docusaurus-10130 | nolsp-edit | ts | true | 0.5 | $0.07 | 1 | 1 | 0 | 0 / 0 | 0 |
| facebook__docusaurus-10309 | lsp | ts | true | 0.9 | $0.07 | 0 | 0 | 0 | 0 / 0 | 0 |
| facebook__docusaurus-10309 | lsp-edit | ts | true | 0.7 | $0.1 | 1 | 1 | 0 | 0 / 0 | 0 |
| facebook__docusaurus-10309 | nolsp | ts | true | 1.0 | $0.07 | 0 | 0 | 0 | 0 / 0 | 0 |
| facebook__docusaurus-10309 | nolsp-edit | ts | true | 0.7 | $0.08 | 1 | 1 | 0 | 0 / 0 | 0 |
| facebook__docusaurus-8927 | lsp | ts | false | 0.9 | $0.08 | 0 | 0 | 0 | 0 / 0 | 0 |
| facebook__docusaurus-8927 | lsp-edit | ts | false | 2.8 | $0.21 | 4 | 2 | 0 | 0 / 0 | 0 |
| facebook__docusaurus-8927 | nolsp | ts | false | 1.0 | $0.08 | 0 | 0 | 0 | 0 / 0 | 0 |
| facebook__docusaurus-8927 | nolsp-edit | ts | false | 2.3 | $0.14 | 2 | 2 | 0 | 0 / 0 | 0 |
| facebook__docusaurus-9897 | lsp | ts | true | 0.7 | $0.1 | 0 | 0 | 0 | 0 / 0 | 0 |
| facebook__docusaurus-9897 | lsp-edit | ts | true | 1.0 | $0.15 | 2 | 2 | 5 | 1 / 1 | 0 |
| facebook__docusaurus-9897 | nolsp | ts | true | 0.7 | $0.09 | 0 | 0 | 0 | 0 / 0 | 0 |
| facebook__docusaurus-9897 | nolsp-edit | ts | true | 1.2 | $0.17 | 2 | 3 | 0 | 0 / 0 | 0 |
| immutable-js__immutable-js-2005 | lsp | plain | true | 2.4 | $0.12 | 0 | 0 | 0 | 0 / 0 | 0 |
| immutable-js__immutable-js-2005 | lsp-edit | plain | true | 3.2 | $0.17 | 2 | 1 | 0 | 11 / 1 | 0 |
| immutable-js__immutable-js-2005 | nolsp | plain | true | 2.7 | $0.12 | 0 | 0 | 0 | 0 / 0 | 0 |
| immutable-js__immutable-js-2005 | nolsp-edit | plain | true | 2.8 | $0.14 | 2 | 1 | 0 | 0 / 0 | 0 |
| immutable-js__immutable-js-2006 | lsp | plain | true | 1.5 | $0.07 | 0 | 0 | 0 | 0 / 0 | 0 |
| immutable-js__immutable-js-2006 | lsp-edit | plain | true | 1.7 | $0.14 | 2 | 3 | 0 | 3 / 1 | 0 |
| immutable-js__immutable-js-2006 | nolsp | plain | true | 1.2 | $0.07 | 0 | 0 | 0 | 0 / 0 | 0 |
| immutable-js__immutable-js-2006 | nolsp-edit | plain | true | 1.6 | $0.17 | 2 | 4 | 0 | 0 / 0 | 0 |
| mrdoob__three.js-25687 | lsp | plain | true | 0.6 | $0.08 | 0 | 0 | 0 | 0 / 0 | 0 |
| mrdoob__three.js-25687 | lsp-edit | plain | true | 1.0 | $0.1 | 2 | 1 | 0 | 0 / 0 | 0 |
| mrdoob__three.js-25687 | nolsp | plain | true | 0.6 | $0.05 | 0 | 0 | 0 | 0 / 0 | 0 |
| mrdoob__three.js-25687 | nolsp-edit | plain | true | 0.7 | $0.12 | 2 | 1 | 0 | 0 / 0 | 0 |
| mrdoob__three.js-26589 | lsp | plain | true | 0.3 | $0.04 | 0 | 0 | 0 | 0 / 0 | 0 |
| mrdoob__three.js-26589 | lsp-edit | plain | true | 0.5 | $0.1 | 3 | 1 | 0 | 0 / 0 | 0 |
| mrdoob__three.js-26589 | nolsp | plain | true | 0.5 | $0.05 | 0 | 0 | 0 | 0 / 0 | 0 |
| mrdoob__three.js-26589 | nolsp-edit | plain | true | 0.5 | $0.11 | 4 | 1 | 0 | 0 / 0 | 0 |
| mrdoob__three.js-27395 | lsp | plain | true | 0.4 | $0.04 | 1 | 0 | 0 | 0 / 0 | 0 |
| mrdoob__three.js-27395 | lsp-edit | plain | true | 0.4 | $0.07 | 1 | 1 | 0 | 0 / 0 | 0 |
| mrdoob__three.js-27395 | nolsp | plain | true | 0.3 | $0.02 | 0 | 0 | 0 | 0 / 0 | 0 |
| mrdoob__three.js-27395 | nolsp-edit | plain | true | 0.4 | $0.07 | 1 | 1 | 0 | 0 / 0 | 0 |
| vuejs__core-11589 | lsp | ts | true | 7.0 | $0.34 | 1 | 0 | 0 | 0 / 0 | 0 |
| vuejs__core-11589 | lsp-edit | ts | true | 23.5 | $0.5 | 5 | 1 | 1 | 2 / 1 | 0 |
| vuejs__core-11589 | nolsp | ts | true | 7.0 | $0.25 | 0 | 0 | 0 | 0 / 0 | 0 |
| vuejs__core-11589 | nolsp-edit | ts | true | 7.7 | $0.31 | 7 | 1 | 0 | 0 / 0 | 1 |
| vuejs__core-11739 | lsp | ts | true | 6.0 | $0.31 | 0 | 0 | 0 | 0 / 0 | 1 |
| vuejs__core-11739 | lsp-edit | ts | true | 2.8 | $0.42 | 7 | 3 | 3 | 1 / 1 | 0 |
| vuejs__core-11739 | nolsp | ts | true | 14.2 | $0.43 | 0 | 0 | 0 | 0 / 0 | 1 |
| vuejs__core-11739 | nolsp-edit | ts | true | 7.6 | $0.6 | 10 | 5 | 0 | 0 / 0 | 1 |
| vuejs__core-11870 | lsp | ts | true | 1.2 | $0.06 | 0 | 0 | 0 | 0 / 0 | 0 |
| vuejs__core-11870 | lsp-edit | ts | true | 1.1 | $0.13 | 3 | 1 | 3 | 1 / 1 | 0 |
| vuejs__core-11870 | nolsp | ts | true | 0.7 | $0.05 | 0 | 0 | 0 | 0 / 0 | 0 |
| vuejs__core-11870 | nolsp-edit | ts | true | 1.3 | $0.11 | 3 | 1 | 0 | 0 / 0 | 0 |
| vuejs__core-11899 | lsp | ts | false | 1.2 | $0.13 | 0 | 0 | 0 | 0 / 0 | 0 |
| vuejs__core-11899 | lsp-edit | ts | false | 2.0 | $0.2 | 3 | 2 | 0 | 0 / 0 | 0 |
| vuejs__core-11899 | nolsp | ts | true | 1.2 | $0.09 | 0 | 0 | 0 | 0 / 0 | 0 |
| vuejs__core-11899 | nolsp-edit | ts | true | 1.0 | $0.17 | 3 | 1 | 0 | 0 / 0 | 0 |
| vuejs__core-11915 | lsp | ts | true | 1.3 | $0.1 | 0 | 0 | 0 | 0 / 0 | 0 |
| vuejs__core-11915 | lsp-edit | ts | true | 1.8 | $0.18 | 3 | 3 | 21 | 4 / 2 | 0 |
| vuejs__core-11915 | nolsp | ts | true | 1.6 | $0.11 | 0 | 0 | 0 | 0 / 0 | 0 |
| vuejs__core-11915 | nolsp-edit | ts | true | 1.3 | $0.09 | 3 | 1 | 0 | 0 / 0 | 0 |
