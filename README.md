# tools

## sym.py

This is a small python script to symbolize macOS 12 and onwards crash reports. Needs python3 and argparse.

You can install argparse using pip.

Params:

```
usage: sym.py [-h] -c 'CrashFilePath' -d 'SymbolsDir' [-o 'Output File Path']
-c 'CrashFilePath', --crash-log 'CrashFilePath'
                        Crash log file path
-d 'SymbolsDir', --sym-dir 'SymbolsDir'
                        Path to directory containing the symbols
-o 'Output File Path', --out-file 'Output File Path'
                        Path to output file which will contain symbolized log, optional - prints to stdout if not provided
```
