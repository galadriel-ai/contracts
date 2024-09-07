# Oracle Machine

## Prerequisites

- <b>Python 3.10</b>

## Overview

- This is the oracle machine that will executed all the instructions that can't be executed in the blockchain such as calling llm apis

- This is supposed to be run in teeML in production environment

## Setup

### Download dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Setup environment variables

- Copy `template.env` into `.env` file in the root directory
- Fill in all the variables as required

### Start oracle

_<b>Note</b>: Start after `oracle contract` is started_

```bash
python oracle.py
```
