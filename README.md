# osu! Skills

这个仓库用来放和 osu! 相关的 agent skill。

目前包含：

- `osu-beatmap-preview`
  根据 beatmap id 获取 `.osu` 谱面，解析谱面内容，并输出预览图和 JSON 结果。

## 使用

进入项目目录后运行：

```bash
cd 
python osu-beatmap-preview/scripts/run.py --bid="5199917"
```