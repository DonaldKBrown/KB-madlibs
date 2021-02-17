MadBot
==

This project is for a [Keybase](https://keybase.io) chat-bot that plays a silly word game with users. It's pretty simple and only responds to direct messages, so the bot running this service can be added to any [Keybase Team](https://keybase.io/popular-teams) without issue of it r
esponding/reacting out of context. This was based loosely off an old project of mine, but was improved to be a chat bot instead. Easy-peasy.

Set-Up
--
Set-up is pretty simple, depending on how you want to run it. You can turn it into a systemd service if you really want, or you can just run it in the background or in a `screen` or `tmux` session. However you want to run is best for you. However, as it is a Python project, I highly suggest you use a virtual environment. It's just better that way. This project requires:

1. A keybase account with a paper key
2. Access to that paper key
3. Python 3.7+
4. All requirements listed in `requirements.txt`.

Obviously, the easiest way to set this up is just to make a Python 3.7 virtual environment and run `pip install -r requirements.txt`. Theoretically, this will run on any system, but I wrote the paths in *nix style, so slight modifications will be need to be made for Windows users.

Contributing
--
Feel free to fork this repo and submit PRs as you wish, I don't even care. However, if you're going to submit stories through a PR, though, follow these rules I definitely did *not* copy/paste from my previous project:

Lib Format
--

Libs need to be formatted a specific way in order to be parsed correctly. Looking through `main.py` and its code should make it pretty obvious, but not everybody can read Python. As such, here are the rules:

- File must contain four (4) sections:
  - Title
  - Category List
  - Key list
    - Keys must contain only letters, numbers, and underscores and must start with a letter.
  - Body
- Sections must be separated by the string `###~~~###`
- Content cannot be overly offensive. I'm pretty lenient, but just keep in mind that kids/teenagers/your grandmother might be reading it.

Example Lib:
--

Here is an example Lib file, so that you know how to format it (basically just follow regular markdown rules for the actual content). More available within the `titles` directory.

```
A Hot Day
###~~~###
Funny
Life
Realistic
###~~~###
adj1=Adjective
name=Girl's Name
bvg1=Beverage
bvg2=Another Beverage
adj2=Adjective
ptverb=Past-Tense Verb
###~~~###
It was a {adj1} day, and {name} decided to set-up a stand to make some money. She decided on selling {bvg1} and {bvg2} to help people cool off.
However, {name} didn't know how to make {bvg1} *or* {bvg2}. As a result, it was **{adj2}**. Nobody {ptverb} any of it.
```
