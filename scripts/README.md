# Scripts

This directory consists of scripts that provide the following features:

## flake_lint.sh

This script helps in automating the flake and linting process.

### How to run the script

    ./scripts/flake_lint.sh [PATH] [OPERATION]

#### PATH:
Add the path to the folder or file you want to perform the OPERATION.
```js
./scripts/flake_lint.sh /home/redant/core/redant_main.py
```
Here both flake and lint operations will be performed on `redant_main.py` file.

```js
./scripts/flake_lint.sh /home/redant/core/ 
```
Here both flake and lint operations will be performed on `/home/redant/core/`.

If you want to run the OPERATION on the whole repo then pass '<b>.</b>' in the PATH
```js
./scripts/flake_lint.sh . [flake/lint]
```

#### OPERATION
1. flake : To perform flake
```js
./scripts/flake_lint.sh /home/redant/core/redant_main.py flake
```
2. lint : To perform linting
```js
./scripts/flake_lint.sh /home/redant/core/redant_main.py lint
```

If nothing is passed, both `flake` and `lint` operations will take place.

## NOTE
---
If you want to perform both linting and flake operations on the whole repo:
```js
./scripts/flake_lint.sh
```