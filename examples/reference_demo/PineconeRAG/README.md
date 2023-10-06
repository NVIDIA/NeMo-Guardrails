# User inputting multiple input variables in Guardrails

This repo is a work in progress part of the [Enterprise Nemo Guardrails reference demo](https://docs.google.com/presentation/d/1TVUulF0PztqPd7Ise8S_hDlocyqIQ2lDjB716zL8HBI/edit#slide=id.g281eca29250_0_358)

## How to run

Within the `MultiVariable` folder run: ` nemoguardrails chat --config=. --verbose`

[Documentation for Reference Demo](https://docs.google.com/document/d/1ZN_iQJU7stLLJJZM1RgCOb-HVWAUpirWAGD00eFHROk/edit)

## Todos: 
- [x] Control the order of when bot asks questions
- [x] Storing values in a Python dict or csv file locally

## Feedback

- Some compiling option to check syntax etc is needed in colang
- writing the function definitions and then giving the sample conversation seems redundant, maybe dynamically generate?
- helper functions to ensure that all the functions are defined in both place? i guess this can be done at compile time
- 

