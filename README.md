# Hackathons

This is a mono-repo with the code from all the hackathons that I've attended so far.

Each folder strives to be self contained using modern tooling (`uv`, `pixi`, `marimo`)

This allows me to have centralised tooling (if needed) as well as useful context for agents when working on new projects. "Successful" projects might get promoted to single repos. 

## Tools & Agents

(For myself) I recommend using as many agents as I can have access to. I personally really like claude code but there are 4-5 hour quotas which mean I'll be offline after a few hours in a hackathon so I am recommending having `gemini-cli` and `codex` handy! 

You will likely need node>=18 or node >=20 (gemini). I try to avoid `npm` where
possible install because of [all the hacks](https://tane.dev/2025/09/oh-no-not-again...-a-meditation-on-npm-supply-chain-attacks/)

```sh
curl -fsSL https://claude.ai/install.sh | bash
brew install gemini-cli
npm i -g @openai/codex
```

for `uv` and `marimo` I like global install and then drilling down with per-project tooling if required. 

```sh
brew install uv
uv tool install marimo
```

upgrade all with 

```sh
brew update && brew upgrade
uv tool upgrade --all
```

## ways of working

I'm excited about the possibilities that modern tooling open up, such as `uv` and `claude code`. Apparently `git worktree` can help loads with that too. [^1][^2][^3]

[^1]: https://fbruzzesi.github.io/blog/2025/07/20/stop-context-switching-how-git-worktree--uv-revolutionized-my-python-workflow/
[^2]: https://docs.claude.com/en/docs/claude-code/common-workflows#run-parallel-claude-code-sessions-with-git-worktrees
[^3: https://x.com/kieranklaassen/status/1930032748951154966
