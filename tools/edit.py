#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/edit.py —— 编辑器本地伴随服务（零第三方依赖，仅标准库）

用途：纯静态的 editor.html 无法执行 git。本服务托管工作目录静态文件，
并暴露最小 API，让编辑器获得"每次保存一个 git 版本 + 回滚"的能力。
编辑器探测不到本服务时自动退化为 FSAA/下载路径，两者互不依赖。

用法：
    python3 tools/edit.py            # 以当前目录为工作目录
    python3 tools/edit.py deck/      # 指定工作目录（deck 所在目录）
    python3 tools/edit.py deck/ --port 8930 --no-browser

红线（docs/design/editor-v2.md §3）：
- 所有 API 只操作工作目录内文件，拒绝路径穿越；
- git add 只加 deck 文件与其同级 assets/，绝不 git add -A；
- 回滚前若工作区有未提交改动，先自动做一次 pre-rollback 提交（永不丢数据）；
- 目录不是 git 仓库时不擅自 init：/api/save 需调用方显式带 init:true
  （编辑器 UI 弹过一次确认后才带）。

转换触发（opt-in，--convert）：/api/convert 只做一件事——以子进程调用
技能脚本 skills/html-pptx/scripts/export-pptx.py（转换逻辑全部在技能侧，
本服务不含任何转换实现，只是"代为按下技能按钮"）。默认关闭，显式加
--convert 才开启；/api/health 的 convert 字段向外宣告该能力。
"""
import argparse
import functools
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIT = shutil.which('git')

HASH_RE = re.compile(r'^[0-9a-f]{4,40}$')


def timestamp():
    return time.strftime('%Y-%m-%d %H:%M:%S')


class ApiError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def git(workdir, args, text=True):
    """统一 git 调用：逐命令注入身份配置，避免依赖用户全局 git config。"""
    if not GIT:
        raise ApiError(500, 'git 不可用（未找到 git 命令）')
    cmd = [GIT, '-c', 'user.name=pptx-editor', '-c', 'user.email=pptx-editor@localhost'] + args
    return subprocess.run(cmd, cwd=workdir, capture_output=True, text=text)


def is_repo(workdir):
    if not GIT:
        return False
    r = git(workdir, ['rev-parse', '--is-inside-work-tree'])
    return r.returncode == 0 and r.stdout.strip() == 'true'


def safe_path(workdir, rel):
    """路径穿越防线：拒绝绝对路径与逃逸出工作目录的相对路径。"""
    if not rel or not isinstance(rel, str):
        raise ApiError(400, '缺少 path')
    if os.path.isabs(rel) or '\x00' in rel:
        raise ApiError(400, '非法路径')
    root = os.path.realpath(workdir)
    full = os.path.realpath(os.path.join(root, rel))
    if full != root and not full.startswith(root + os.sep):
        raise ApiError(400, '路径越界：只允许工作目录内的文件')
    rel_norm = os.path.relpath(full, root)
    return full, rel_norm


def atomic_write(full, data):
    """同目录临时文件 + os.replace，避免半写状态损坏 deck。"""
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(full) or '.',
                               prefix='.edit-', suffix='.tmp')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
        os.replace(tmp, full)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def deck_and_assets(workdir, rel):
    """git add 白名单：deck 文件 + 其同级 assets/ 目录（存在才加）。"""
    paths = [rel]
    assets = os.path.join(os.path.dirname(rel), 'assets')
    if os.path.isdir(os.path.join(workdir, assets)):
        paths.append(assets)
    return paths


def git_commit(workdir, rel, message):
    """只提交 deck 文件与同级 assets/；无改动时返回 None（不算错误）。"""
    paths = deck_and_assets(workdir, rel)
    r = git(workdir, ['add', '--'] + paths)
    if r.returncode != 0:
        raise ApiError(500, 'git add 失败：' + r.stderr.strip())
    r = git(workdir, ['commit', '-m', message, '--'] + paths)
    if r.returncode != 0:
        if 'nothing to commit' in (r.stdout + r.stderr):
            return None
        raise ApiError(500, 'git commit 失败：' + (r.stderr.strip() or r.stdout.strip()))
    h = git(workdir, ['rev-parse', '--short', 'HEAD'])
    return h.stdout.strip() if h.returncode == 0 else None


class Handler(SimpleHTTPRequestHandler):
    server_version = 'PptxEdit/1.0'

    def log_message(self, fmt, *args):   # 静默访问日志，保持终端干净
        pass

    # ---------- 基础 ----------

    def _send_json(self, obj, status=200):
        data = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self):
        n = int(self.headers.get('Content-Length') or 0)
        if n <= 0 or n > 64 * 1024 * 1024:
            raise ApiError(400, '请求体为空或过大')
        try:
            return json.loads(self.rfile.read(n).decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            raise ApiError(400, '请求体不是合法 JSON')

    # ---------- 路由 ----------

    def do_GET(self):
        path = urlparse(self.path).path
        try:
            if path == '/api/health':
                return self._send_json({
                    'ok': True,
                    'git': GIT is not None,
                    'gitReady': is_repo(self.server.workdir),
                    'convert': bool(getattr(self.server, 'allow_convert', False)),
                })
            if path == '/api/convert-status':
                return self._send_json(dict(self.server.convert_state))
            if path == '/api/versions':
                return self.api_versions(parse_qs(urlparse(self.path).query))
            if path.startswith('/api/'):
                raise ApiError(404, '未知 API')
            return self.serve_static(path)
        except ApiError as e:
            self._send_json({'ok': False, 'error': e.message}, e.status)
        except Exception as e:   # 兜底：API 不裸抛堆栈给浏览器
            self._send_json({'ok': False, 'error': str(e)}, 500)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            if path == '/api/save':
                return self.api_save(self._read_json())
            if path == '/api/rollback':
                return self.api_rollback(self._read_json())
            if path == '/api/convert':
                return self.api_convert(self._read_json())
            raise ApiError(404, '未知 API')
        except ApiError as e:
            self._send_json({'ok': False, 'error': e.message}, e.status)
        except Exception as e:
            self._send_json({'ok': False, 'error': str(e)}, 500)

    def serve_static(self, path):
        # 工作目录里没有 editor.html 时回落到项目根的副本——
        # 这样 `python3 tools/edit.py some/deck/` 也能直接用编辑器。
        if path in ('/', '/editor.html') and \
                not os.path.isfile(os.path.join(self.server.workdir, 'editor.html')):
            if path == '/':
                self.path = '/editor.html'
            with open(os.path.join(PROJECT_ROOT, 'editor.html'), 'rb') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if path == '/':
            self.path = '/editor.html'
        super().do_GET()

    # ---------- API ----------

    def api_save(self, body):
        workdir = self.server.workdir
        html = body.get('html')
        if not isinstance(html, str):
            raise ApiError(400, '缺少 html')
        full, rel = safe_path(workdir, body.get('path'))
        if not os.path.isdir(os.path.dirname(full) or workdir):
            raise ApiError(400, '目标目录不存在')

        atomic_write(full, html.encode('utf-8'))

        committed, commit_hash = False, None
        repo = is_repo(workdir)
        if not repo and body.get('init') is True:
            # 编辑器 UI 已弹过一次性确认，这里才允许 init
            r = git(workdir, ['init'])
            if r.returncode != 0:
                raise ApiError(500, 'git init 失败：' + r.stderr.strip())
            repo = True
        if repo:
            commit_hash = git_commit(workdir, rel, 'edit: ' + timestamp())
            committed = commit_hash is not None
        self._send_json({'ok': True, 'path': rel, 'committed': committed,
                         'hash': commit_hash, 'gitReady': repo})

    def api_versions(self, query):
        workdir = self.server.workdir
        full, rel = safe_path(workdir, (query.get('path') or [''])[0])
        if not is_repo(workdir):
            return self._send_json({'ok': True, 'gitReady': False, 'versions': []})
        r = git(workdir, ['log', '--format=%H%x1f%cI%x1f%s', '--', rel])
        if r.returncode != 0:
            return self._send_json({'ok': True, 'gitReady': True, 'versions': []})
        versions = []
        for line in r.stdout.splitlines():
            parts = line.split('\x1f')
            if len(parts) == 3:
                versions.append({'hash': parts[0], 'time': parts[1], 'message': parts[2]})
        self._send_json({'ok': True, 'gitReady': True, 'versions': versions})

    def api_rollback(self, body):
        workdir = self.server.workdir
        full, rel = safe_path(workdir, body.get('path'))
        target = body.get('hash') or ''
        if not HASH_RE.match(target):
            raise ApiError(400, '非法提交哈希')
        if not is_repo(workdir):
            raise ApiError(400, '工作目录不是 git 仓库，无版本可回滚')
        r = git(workdir, ['cat-file', '-e', '%s^{commit}' % target])
        if r.returncode != 0:
            raise ApiError(400, '目标版本不存在：' + target)

        # 红线：回滚前若工作区有未提交改动，先自动提交保护（可反悔的回滚）
        dirty = git(workdir, ['status', '--porcelain', '--', rel])
        pre = None
        if dirty.returncode == 0 and dirty.stdout.strip():
            pre = git_commit(workdir, rel, 'pre-rollback: ' + timestamp())

        r = git(workdir, ['show', '%s:%s' % (target, rel)], text=False)
        if r.returncode != 0:
            raise ApiError(400, '该版本中不存在此文件')
        atomic_write(full, r.stdout)
        self._send_json({'ok': True, 'path': rel, 'preRollback': pre})

    def api_convert(self, body):
        """代为触发技能导出管线（opt-in，异步任务制）。转换实现 100% 在技能脚本里，
        本端点只是触发器：启动后台线程跑 export-pptx.py，状态经 /api/convert-status 查询。
        重复触发幂等：管线运行中直接返回 running，不并发重跑。"""
        if not getattr(self.server, 'allow_convert', False):
            raise ApiError(403, '伴随服务未启用转换（以 --convert 启动可开启）')
        full, rel = safe_path(self.server.workdir, body.get('path'))
        if not rel.lower().endswith('.html') or not os.path.isfile(full):
            raise ApiError(400, '目标必须是工作目录内已存在的 .html deck 文件')
        started = start_convert(self.server, full)
        st = dict(self.server.convert_state)
        st.update({'ok': True, 'started': started})
        self._send_json(st)


def start_convert(server, deck_html):
    """启动（或复用）后台转换线程。返回是否本次新启动。
    状态机：idle → running → done/failed（tail 存末 30 行日志）。"""
    st = server.convert_state
    if st['status'] == 'running':
        return False
    script = os.path.join(PROJECT_ROOT, 'skills/html-pptx/scripts/export-pptx.py')
    if not os.path.isfile(script):
        st.update({'status': 'failed', 'tail': '未找到技能导出脚本：' + script,
                   'path': deck_html, 'started': timestamp()})
        return False
    st.update({'status': 'running', 'path': deck_html, 'started': timestamp(), 'tail': ''})

    def work():
        try:
            r = subprocess.run([sys.executable, script, deck_html, '--force'],
                               capture_output=True, text=True, timeout=1800)
            tail = (r.stdout + '\n' + r.stderr).strip().splitlines()[-30:]
            server.convert_state.update({'status': 'done' if r.returncode == 0 else 'failed',
                                         'code': r.returncode, 'tail': '\n'.join(tail)})
        except subprocess.TimeoutExpired:
            server.convert_state.update({'status': 'failed', 'tail': '转换超时（30 分钟上限）'})
        except Exception as e:
            server.convert_state.update({'status': 'failed', 'tail': str(e)})

    threading.Thread(target=work, daemon=True).start()
    return True


def main():
    ap = argparse.ArgumentParser(description='editor.html 本地伴随服务（静态托管 + git 版本 API）')
    ap.add_argument('workdir', nargs='?', default='.', help='工作目录（deck 所在目录），默认当前目录')
    ap.add_argument('--port', type=int, default=8926)
    ap.add_argument('--no-browser', action='store_true', help='不自动打开浏览器')
    ap.add_argument('--convert', action='store_true',
                    help='允许 /api/convert 以子进程触发技能导出管线（export-pptx.py），默认关闭')
    args = ap.parse_args()

    workdir = os.path.realpath(args.workdir)
    if not os.path.isdir(workdir):
        print('工作目录不存在：%s' % workdir, file=sys.stderr)
        sys.exit(2)

    handler = functools.partial(Handler, directory=workdir)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), handler)
    server.daemon_threads = True
    server.workdir = workdir
    server.allow_convert = args.convert
    server.convert_state = {'status': 'idle', 'path': None, 'started': None, 'tail': ''}

    url = 'http://127.0.0.1:%d/editor.html' % args.port
    if os.path.isfile(os.path.join(workdir, 'index.html')):
        url += '?deck=index.html'
    print('工作目录：%s' % workdir)
    print('编辑器：  %s' % url)
    print('git 版本：%s' % ('已就绪' if is_repo(workdir)
                            else '目录非 git 仓库（首次保存时编辑器会询问是否 init）'))
    print('一键转换：%s' % ('已启用（/api/convert → 技能 export-pptx.py）' if args.convert
                            else '未启用（加 --convert 后编辑器可一键触发导出管线）'))
    # --convert 启动即转：工作目录有 index.html 就后台开跑管线，编辑器打开时转换已在进行
    if args.convert:
        deck = os.path.join(workdir, 'index.html')
        if os.path.isfile(deck):
            start_convert(server, deck)
            print('启动即转：已开始后台转换 %s（编辑器里可看进度）' % deck)
        else:
            print('启动即转：工作目录无 index.html，跳过（在编辑器里打开 deck 后可一键转换）')
    print('Ctrl+C 停止')
    if not args.no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
