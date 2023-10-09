# Test cases

## 'do' flow is never call because of fallback

- The match statement 'user said something' will always match an therefore never trigger the LLM that would match it to the 'do' flow

## Since we don't have yet an NLU matching for generated flows the correct answer is not guaranteed

- user: "do something: Ask user to choose from two offered colors: red and blue then give a answer depending on the user choice"
- bot: "What color would you like? Red or blue?"
- user: "I like blue"
- bot: "I don't like blue, but it's a nice color!'

## issue: Bot does not react because LLM generates continuation based on dialog history rather than example flows

- user: "do something: Ask user to choose from two offered colors: red and blue then give a answer depending on the user choice"
- bot: "What color would you like? Red or blue?"
- user: "blue"
- bot: "I don't like blue!'
- user: "do something: Ask user to choose from two offered colors: red and blue then give a answer depending on the user choice"
- bot: "What color would you like? Red or blue?"
- user: "blue"
- bot: ...

Generated flow continuation:

```
bot say "What color would you like? Red or blue?"
user said "red"
user provided color choice
bot say "I like red!"
```
