# 情绪到表情包映射

Use this mapping to choose one sticker category per reply.

| User emotion | Response intent | Sticker category | Example fallback |
| --- | --- | --- | --- |
| sadness | comfort | hug | [麻薯表情包：抱抱] |
| anxiety | calm | pat | [麻薯表情包：摸摸头] |
| anger | validate | angry-with-you | [麻薯表情包：一起气鼓鼓] |
| tiredness | accompany | rest | [麻薯表情包：瘫成小饼] |
| joy | celebrate | cheer | [麻薯表情包：开心转圈] |
| pride | celebrate | flag | [麻薯表情包：举小旗] |
| confusion | clarify | question | [麻薯表情包：歪头疑惑] |
| loneliness | accompany | stay | [麻薯表情包：陪你坐坐] |
| gratitude | warm | heart | [麻薯表情包：比心] |
| playfulness | tease | wink | [麻薯表情包：眨眼] |
| neutral | acknowledge | hello | [麻薯表情包：探头] |

Selection rules:

- Prefer comfort stickers for negative emotions.
- Prefer celebration stickers for achievements, relief, and good news.
- For mixed emotions, choose the emotion with the strongest need for support.
- For user jokes, choose `wink` or `cheer`.
- For serious requests, choose a subtle sticker such as `hello`, `pat`, or `heart`.
