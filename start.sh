#!/bin/bash
clear

export SCRIPT_DIR=$(realpath $(dirname $0))
export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=4096

cd $SCRIPT_DIR

export VENV_ACTIVATE="venv/bin/activate"
export SL_FILE="main.py"

echo "VENV_ACTIVATE $VENV_ACTIVATE"
source $VENV_ACTIVATE

echo "SL_FILE $SL_FILE"
streamlit run $SL_FILE