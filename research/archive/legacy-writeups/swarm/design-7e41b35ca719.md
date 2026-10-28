# How this page presents the work

The public page is written as a research note, not a product page. In October 2026 I
looked at how individual alignment researchers present empirical work and copied
their habits rather than any visual style:

- **A question as the title, then a summary of findings.** Anthropic's research posts
  ([alignment faking](https://www.anthropic.com/research/alignment-faking),
  [sleeper agents](https://www.anthropic.com/research/sleeper-agents-training-deceptive-llms-that-persist-through-safety-training))
  and METR's [task-length post](https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/)
  open with a plain question or claim and a short summary of what was found.
- **One to three concrete claims, with evidence and caveats attached.** Neel Nanda's
  [advice on writing ML papers](https://www.alignmentforum.org/posts/eJGptPbbFPZGLpjsp/highly-opinionated-advice-on-how-to-write-ml-papers):
  readers keep a few sentences, so choose them; resist overclaiming; say clearly
  what is and is not new.
- **A concrete example before the abstraction.** The
  [emergent misalignment](https://www.emergent-misalignment.com/) page and
  [TurnTrout's activation-steering post](https://www.lesswrong.com/posts/5spBue2z2tw4JuDCx/steering-gpt-2-xl-by-adding-an-activation-vector)
  lead with real model outputs. Here the opening figure is the two identical test runs.
- **First person, including surprises and failures.** LessWrong and Alignment Forum
  posts from Redwood and Ryan Greenblatt say what surprised the authors and what did
  not work. The page states that source tracking made the toy model worse and that
  the pilot did not test the hypothesis.
- **Numbered figures with captions, and interaction that serves the argument.**
  Distill ([Research Debt](https://distill.pub/2017/research-debt/)) and Nicky Case's
  [Wisdom and/or Madness of Crowds](https://ncase.me/crowds/) put interactive figures
  inside the prose. Here, buttons in the text load the exact settings a paragraph
  describes.

What was removed: marketing hero, cards, badges, status pills, hypothesis grids, and
section labels like "01 · The question". Every number in the prose is reproducible
from `website/dist/engine.js` at the default settings (seed 42) or from the recorded
pilot episodes.

The demo runs entirely in the browser. It needs no account or provider key, and
visitors cannot trigger paid model calls. Real-model experiments are a separate local
workflow with explicit model selection and spending limits.
