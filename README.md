# Mochirong Mashu Skill

A Codex skill that replies in a soft “麻薯” emotional-support style and attaches one matching Mochirong-style sticker reaction to each user-facing reply.

## Install

Install directly from this GitHub repository:

```bash
npx @openai/codex skills install github:yuauston-312/mochirong-skills/mashu
```

The skill lives in the `mashu/` subdirectory, so keep `/mashu` at the end of the install path.

## Use

After installing, start a Codex conversation and say one of:

```text
Use mashu skill.
```

```text
进入麻薯模式。
```

```text
接下来用麻薯的语气和我聊天，每次带一个表情包。
```

## What It Does

- Infers the user's emotional state.
- Replies in a warm, soft, lightly playful 麻薯 tone.
- Selects exactly one sticker reaction per reply.
- Uses bundled Mochirong-style sticker assets from `mashu/assets/stickers/candidates/`.
- Falls back to a compact text sticker label when no matching image is available.

## Repository Structure

```text
mashu/
  SKILL.md
  agents/openai.yaml
  assets/stickers/
    candidates/
    manifest.json
    mochirong-contact-sheet.jpg
  references/
    emotion-map.md
    mashu-voice.md
    sticker-style.md
  scripts/
    festival_greeting.py
    select_sticker.py
```

## Preview

See `mashu/assets/stickers/mochirong-contact-sheet.jpg` for the current sticker contact sheet.

## Validate

If you are developing the skill locally, validate it with Codex's skill validator:

```bash
python ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py ./mashu
```

On Windows, the validator is usually under:

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" .\mashu
```
