#!/usr/bin/env bash
# Instala o ambiente: venv com MuJoCo + modelo do Franka Panda (MuJoCo Menagerie, Apache-2.0).
set -euo pipefail
cd "$(dirname "$0")"

python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt

if [ ! -f vendor/menagerie/franka_emika_panda/panda.xml ]; then
  git clone -q --depth 1 --filter=blob:none --sparse \
    https://github.com/google-deepmind/mujoco_menagerie.git vendor/menagerie
  git -C vendor/menagerie sparse-checkout set franka_emika_panda
fi

# sem monitor (servidor, WSL): renderiza pela GPU com EGL; troque por osmesa se não houver GPU
export MUJOCO_GL="${MUJOCO_GL:-egl}"
.venv/bin/python -c "import mujoco; print('MuJoCo', mujoco.__version__, 'ok')"
.venv/bin/python testes/rodar.py
