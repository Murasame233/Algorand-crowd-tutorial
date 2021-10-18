# Chapter I

This Chapter will do some ready job

## Pre requirements
- `Python @latest`
- `Node.js @LTS`
- `CMake`

You'd better have python experience for smart contract dev.

You'd better have nodejs experience for DApp dev.

## folder struct
```
.
├── Makefile // Some fast command
├── README.md
├── Tutorial.md
├── backend // Dapp's backend, use later the.
├── contract // Smart contract folder
│   ├── env // Python venv folder
│   └── requirements.txt // Python installed package
└── frontend // Dapp's frontend, use later the.

```

# Steps

## Create Dir
```
mkdir contract backend frontend
```

## Ready the Python virtual env

```
cd contract
python -m venv env // create the python virtual env
source env/bin/activate // activate the python virtual env

pip install --upgrade pip
pip install pyteal
```

This will create virtual env on the contract folder, and install the packages we need.

Needed python package.
- `pyteal`

From now, when you run the python script, make sure you are under the virtual env.

> when you under virtual env, your shell will be like this:
> ```bash
> (env) ~/workfolder/contract ➜ 
> ```
