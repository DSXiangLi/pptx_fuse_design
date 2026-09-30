#!/usr/bin/env bash
# 一键启动编辑器 WebUI：伴随服务（git 版本 + 转换能力）+ 自动开浏览器 +
# 启动即后台跑导出管线（工作目录有 index.html 时）。
#
# 用法：
#   tools/start-webui.sh [deck目录]      # 默认当前目录
#   tools/start-webui.sh tests/decks/cmb-retail-v2
#
# 等价命令：python3 tools/edit.py <deck目录> --convert
cd "$(dirname "$0")/.." || exit 1
exec python3 tools/edit.py "${1:-.}" --convert
