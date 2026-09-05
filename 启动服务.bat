@echo off
rem ===== 电智学伴 Phase 2 一键启动 (Windows) =====
chcp 65001 >nul
cd /d "%~dp0backend"

rem ---- 选 Python：优先 3.12（Phase2 依赖已装），退回默认 python ----
set PYCMD=python
py -3.12 -c "import sys; sys.exit(0)" >nul 2>&1
if %errorlevel%==0 set PYCMD=py -3.12
echo [0/4] 使用解释器: %PYCMD%

echo [1/4] 安装/校验依赖...
%PYCMD% -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo [2/4] 检查知识库...
%PYCMD% -c "import sys; sys.path.insert(0,'.'); from kb.retriever import get_retriever; n=get_retriever().count(); print('当前知识库片段数:', n); sys.exit(0 if n>0 else 3)"
if %errorlevel%==3 (
  echo 知识库为空。若 textbooks 目录已有教材 PDF，请先构建索引：
  echo   cd backend
  echo   %PYCMD% -m kb.build_kb --dir ..\textbooks --offset 0
  echo 其中 --offset 用于校准印刷页码：PDF 第 1 页印着第 N 页则 offset=N-1。
)

echo [3/4] 启动服务 (http://localhost:8000)...
start "" http://localhost:8000

%PYCMD% main.py
pause
