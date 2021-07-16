# cEDH-DDB-Crawler

| Dependencies | Installation |
---|---
| Beautiful Soup 4 | ``` pip install bs4 ``` |
| Selenium | ``` pip install selenium ``` |
| Geckodriver | https://github.com/mozilla/geckodriver/releases |

#### Setup Guide

1. Install the dependencies.
2. Move `geckodriver` to `src/`. `parser.py` assumes a binary file, but you can edit it to match the appropriate file type for your system.
3. Update `database.py` to query whatever values you want.
4. Script and run `main.py`.
