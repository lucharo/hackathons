# Hackathons

This is a mono-repo with the code from all the hackathons that I've attended so far.

Each folder strives to be self contained using modern tooling (`uv`, `pixi`, `marimo`)

This allows me to have centralised tooling (if needed) as well as useful context for agents when working on new projects. "Successful" projects might get promoted to single repos. 

## Agents

(For myself) I recommend using as many agents as I can have access to. I personally really like claude code but there are 4-5 hour quotas which mean I'll be offline after a few hours in a hackathon so I am recommending having `gemini-cli` and `codex` handy! 

You will likely need node>=18 or node >=20 (gemini). I try to avoid `npm` where
possible install because of [all the hacks](https://tane.dev/2025/09/oh-no-not-again...-a-meditation-on-npm-supply-chain-attacks/)

```sh
curl -fsSL https://claude.ai/install.sh | bash
brew install gemini-cli
npm i -g @openai/codex
```
