## Set OpenAI Env
```
Set the environment variable OPENAI_API_KEY before running.
```

## Create conda environment
```bash
$ conda create -n mp python=3.10
$ conda activate mp

// Run from MAVProxy folder.
$ pip3 install .
```

## Install Formula
```bash
$ dotnet tool install --global VUISIS.Formula.<x64|ARM64> 
```

## Battery Demo Commands
```bash
$ batdemo invalid
$ batdemo repair
```